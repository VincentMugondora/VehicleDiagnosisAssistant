import hmac
import base64
import hashlib
from datetime import datetime   
from typing import Dict, Any
import httpx
from fastapi import APIRouter, Request, Response, status, Depends
from app.models.webhook import TwilioWebhookPayload, BaileysWebhookPayload
from app.models.diagnostic import DiagnosticResult, SymptomDiagnosisResult
from app.services.session_manager import SessionManager
from app.services.message_router import MessageRouter
from app.services.obd_service import OBDService
from app.services.ai_client import AIClient
from app.repositories.obd_repository import OBDRepository
from app.repositories.message_log_repository import MessageLogRepository
from app.repositories.session_repository import SessionRepository
from app.repositories.diagnostic_log_repository import DiagnosticLogRepository
from app.db.client import get_supabase_client
from app.utils.phone import hash_phone_number
from app.api.formatters import (
    format_diagnostic_response,
    format_symptom_response,
    format_error_response
)
from app.core.config import settings
from app.core.errors import MessageAlreadyProcessed
from app.core.logging import logger

router = APIRouter(prefix="/webhook", tags=["webhook"])


# Dependency injection
def get_repositories():
    """Get all repository instances"""
    client = get_supabase_client()
    return {
        "obd_repo": OBDRepository(client),
        "message_repo": MessageLogRepository(client),
        "session_repo": SessionRepository(client),
        "diagnostic_repo": DiagnosticLogRepository(client)
    }


def get_session_manager(repos: dict = Depends(get_repositories)):
    """Get SessionManager with dependencies"""
    return SessionManager(
        session_repo=repos["session_repo"],
        message_repo=repos["message_repo"]
    )


def get_message_router(repos: dict = Depends(get_repositories)):
    """Get MessageRouter with dependencies"""
    # Initialize OBDService with AI client for auto-learning
    ai_client = None
    if settings.auto_learn_codes:
        try:
            ai_client = AIClient()
        except:
            pass  # AI optional, will work without it

    obd_service = OBDService(
        repos["obd_repo"],
        ai_client=ai_client,
        auto_learn=settings.auto_learn_codes
    )
    return MessageRouter(obd_service)


def _compute_twilio_signature(
    url: str,
    form_params: Dict[str, Any],
    auth_token: str
) -> str:
    """
    Compute Twilio HMAC-SHA1 signature for webhook validation.

    Args:
        url: Full webhook URL
        form_params: Form data dict
        auth_token: Twilio auth token

    Returns:
        Base64-encoded signature
    """
    s = url + "".join([
        f"{k}{v}"
        for k, v in sorted((k, str(v)) for k, v in form_params.items())
    ])
    digest = hmac.new(
        auth_token.encode("utf-8"),
        s.encode("utf-8"),
        hashlib.sha1
    ).digest()
    return base64.b64encode(digest).decode("utf-8")


async def _check_usage_limit(
    message_repo: MessageLogRepository,
    phone_hash: str
) -> str | None:
    """
    Check if user has exceeded usage limit.

    Args:
        message_repo: MessageLogRepository instance
        phone_hash: SHA-256 hash of phone number

    Returns:
        Error message if limit exceeded, None otherwise
    """
    limit = settings.usage_limit_per_number
    if limit <= 0:
        return None

    # Check if number is whitelisted
    allowed = [
        n.strip()
        for n in settings.allowed_numbers.split(",")
        if n.strip()
    ]
    # Note: Can't check raw number since we only have hash
    # For whitelisting, need to hash allowed numbers and compare

    count = message_repo.count_recent(
        phone_hash,
        settings.usage_limit_window_days
    )

    if count >= limit:
        logger.warning(
            "usage_limit_exceeded",
            phone_hash=phone_hash,
            count=count,
            limit=limit
        )
        return "Limit reached. Reply later or contact support to upgrade."

    return None


async def _send_reply_via_twilio(to_number: str, body: str):
    """
    Send WhatsApp reply via Twilio API.

    Args:
        to_number: Recipient phone number
        body: Message body
    """
    if not settings.twilio_send_reply:
        return

    if not all([
        settings.twilio_account_sid,
        settings.twilio_auth_token,
        settings.twilio_whatsapp_from
    ]):
        logger.warning("twilio_credentials_missing")
        return

    url = (
        f"https://api.twilio.com/2010-04-01/"
        f"Accounts/{settings.twilio_account_sid}/Messages.json"
    )
    data = {
        "To": to_number,
        "From": settings.twilio_whatsapp_from,
        "Body": body
    }
    auth = (settings.twilio_account_sid, settings.twilio_auth_token)

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(url, data=data, auth=auth)
        logger.info("twilio_reply_sent", to=to_number)
    except Exception as e:
        logger.error("twilio_reply_failed", error=str(e))


@router.post("/twilio")
async def twilio_webhook(
    request: Request,
    session_manager: SessionManager = Depends(get_session_manager),
    message_router: MessageRouter = Depends(get_message_router),
    repos: dict = Depends(get_repositories)
):
    """
    Twilio WhatsApp webhook handler.

    Validates signature, checks idempotency, processes message.
    """
    # Parse form data
    form = await request.form()
    data = {k: v for k, v in form.items()}

    # Validate payload structure
    try:
        payload = TwilioWebhookPayload(**data)
    except Exception as e:
        logger.error("twilio_payload_invalid", error=str(e))
        return Response(status_code=status.HTTP_400_BAD_REQUEST)

    # Validate signature
    if settings.twilio_validate_signature:
        provided = request.headers.get("X-Twilio-Signature", "")
        expected = _compute_twilio_signature(
            str(request.url),
            data,
            settings.twilio_auth_token or ""
        )
        if not hmac.compare_digest(provided, expected):
            logger.warning("twilio_signature_invalid")
            return Response(status_code=status.HTTP_403_FORBIDDEN)

    # Hash phone number
    phone_hash = hash_phone_number(payload.From)

    logger.info(
        "twilio_webhook_received",
        phone_hash=phone_hash,
        message_id=payload.MessageSid
    )

    # Check idempotency
    try:
        session_manager.check_message_idempotency(payload.MessageSid)
    except MessageAlreadyProcessed:
        logger.info("duplicate_message_ignored")
        return {"ok": True, "status": "duplicate"}

    # Check usage limit
    limit_msg = await _check_usage_limit(repos["message_repo"], phone_hash)
    if limit_msg:
        # Log and return limit message
        repos["message_repo"].insert_audit(
            message_id=payload.MessageSid,
            phone_hash=phone_hash,
            request_id=request.state.request_id,
            session_id=None,
            request_text=payload.Body,
            response_text=limit_msg,
            code=None
        )
        await _send_reply_via_twilio(payload.From, limit_msg)
        return {"ok": True, "status": "rate_limited"}

    # Load session
    session = session_manager.load_session(phone_hash)

    # Route message
    result = await message_router.route_message(
        raw_text=payload.Body,
        phone_hash=phone_hash,
        request_id=request.state.request_id
    )

    # Format response
    if isinstance(result, DiagnosticResult):
        reply_parts = format_diagnostic_response(result)
        code = result.code

        # Log diagnostic
        vehicle_str = " ".join(filter(None, [
            session.vehicle.make if session.vehicle else None,
            session.vehicle.model if session.vehicle else None,
            session.vehicle.year if session.vehicle else None,
            session.vehicle.engine if session.vehicle else None
        ]))
        repos["diagnostic_repo"].insert_diagnostic(
            code=result.code,
            vehicle=vehicle_str,
            source=result.source,
            confidence=result.confidence
        )

    elif isinstance(result, SymptomDiagnosisResult):
        reply_parts = format_symptom_response(result)
        code = None
    else:
        # Error dict
        reply_parts = format_error_response(result.get("error", "Error"))
        code = None

    # Join all reply parts
    reply = "\n\n".join(reply_parts)

    # Save session
    session_manager.save_session(session)

    # Log message
    repos["message_repo"].insert_audit(
        message_id=payload.MessageSid,
        phone_hash=phone_hash,
        request_id=request.state.request_id,
        session_id=None,  # TODO: get session ID from session
        request_text=payload.Body,
        response_text=reply,
        code=code
    )

    # Send reply
    await _send_reply_via_twilio(payload.From, reply)

    return {"ok": True}


@router.get("/test")
async def test_webhook():
    """Simple test endpoint"""
    return {"status": "ok", "message": "Webhook route is working!"}


@router.post("/baileys/test")
async def test_baileys_post(data: dict):
    """Test POST endpoint without complex logic"""
    logger.info("test_post_received", data=data)
    return {"status": "ok", "received": data}


@router.post("/baileys")
async def baileys_webhook(
    payload: BaileysWebhookPayload,
    request: Request,
    session_manager: SessionManager = Depends(get_session_manager),
    message_router: MessageRouter = Depends(get_message_router),
    repos: dict = Depends(get_repositories)
):
    """
    Baileys WhatsApp webhook handler.

    Validates API key, checks idempotency, processes message.
    """
    logger.info("baileys_webhook_started", payload=payload.model_dump())

    # Validate API key
    if settings.baileys_api_key:
        auth_header = request.headers.get("X-API-Key", "")
        if auth_header != settings.baileys_api_key:
            logger.warning("baileys_auth_failed")
            return Response(status_code=status.HTTP_401_UNAUTHORIZED)

    # Extract sender and text
    logger.info("extracting_sender")
    from_number = payload.get_sender()
    logger.info("sender_extracted", from_number=from_number)

    raw_text = payload.get_text().strip()
    logger.info("text_extracted", text=raw_text)

    # Generate message_id if not provided
    message_id = payload.message_id or f"msg_{hash_phone_number(from_number)}_{int(datetime.now().timestamp() * 1000)}"

    # Hash phone number
    phone_hash = hash_phone_number(from_number)

    logger.info(
        "baileys_webhook_received",
        phone_hash=phone_hash,
        message_id=message_id
    )

    # Check idempotency
    try:
        session_manager.check_message_idempotency(message_id)
    except MessageAlreadyProcessed:
        logger.info("duplicate_message_ignored")
        return {"ok": True, "status": "duplicate"}

    # Check usage limit
    limit_msg = await _check_usage_limit(repos["message_repo"], phone_hash)
    if limit_msg:
        repos["message_repo"].insert_audit(
            message_id=message_id,
            phone_hash=phone_hash,
            request_id=request.state.request_id,
            session_id=None,
            request_text=raw_text,
            response_text=limit_msg,
            code=None
        )
        return {"reply": limit_msg, "status": "rate_limited"}

    # Load session
    session = session_manager.load_session(phone_hash)

    # Route message with session context for followups
    result = await message_router.route_message(
        raw_text=raw_text,
        phone_hash=phone_hash,
        request_id=request.state.request_id,
        session=session  # Pass session for conversation memory
    )

    # Format response
    if isinstance(result, DiagnosticResult):
        reply_parts = format_diagnostic_response(result)
        code = result.code

        # Log diagnostic
        vehicle_str = " ".join(filter(None, [
            session.vehicle.make if session.vehicle else None,
            session.vehicle.model if session.vehicle else None,
            session.vehicle.year if session.vehicle else None,
            session.vehicle.engine if session.vehicle else None
        ]))
        repos["diagnostic_repo"].insert_diagnostic(
            code=result.code,
            vehicle=vehicle_str,
            source=result.source,
            confidence=result.confidence
        )

    elif isinstance(result, SymptomDiagnosisResult):
        reply_parts = format_symptom_response(result)
        code = None
    else:
        reply_parts = format_error_response(result.get("error", "Error"))
        code = None

    # Join all reply parts
    reply = "\n\n".join(reply_parts)

    # Save session
    session_manager.save_session(session)

    # Log message
    repos["message_repo"].insert_audit(
        message_id=message_id,
        phone_hash=phone_hash,
        request_id=request.state.request_id,
        session_id=None,
        request_text=raw_text,
        response_text=reply,
        code=code
    )

    return {"reply": reply}
