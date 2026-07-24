import hmac
import base64
import hashlib
import traceback
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
from app.services.payment_service import PaymentService
from app.services.user_state_machine import UserStateMachine
from app.services.payment_command_handlers import PaymentCommandHandler
from app.services.image_sender import ImageSender, format_attribution
from app.repositories.obd_repository import OBDRepository
from app.repositories.message_log_repository import MessageLogRepository
from app.repositories.session_repository import SessionRepository
from app.repositories.diagnostic_log_repository import DiagnosticLogRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.system_diagram_repository import SystemDiagramRepository
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
        "diagnostic_repo": DiagnosticLogRepository(client),
        "payment_repo": PaymentRepository(client),
        "diagram_repo": SystemDiagramRepository(client)
    }


def get_payment_service(repos: dict = Depends(get_repositories)):
    """Get PaymentService with dependencies"""
    return PaymentService(repos["payment_repo"])


def get_state_machine(repos: dict = Depends(get_repositories)):
    """Get UserStateMachine with dependencies"""
    return UserStateMachine(repos["payment_repo"])


def get_command_handler(
    repos: dict = Depends(get_repositories),
    payment_service: PaymentService = Depends(get_payment_service)
):
    """Get PaymentCommandHandler with dependencies"""
    state_machine = UserStateMachine(repos["payment_repo"])
    return PaymentCommandHandler(state_machine, payment_service)


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

    # Check if number is whitelisted by hashing allowed numbers
    import hashlib
    allowed_numbers = [
        n.strip()
        for n in settings.allowed_numbers.split(",")
        if n.strip()
    ]

    # Hash each allowed number and check if phone_hash matches
    for allowed_num in allowed_numbers:
        allowed_hash = hashlib.sha256(allowed_num.encode()).hexdigest()
        if phone_hash == allowed_hash:
            logger.info(
                "whitelisted_number_bypassing_limit",
                phone_hash=phone_hash
            )
            return None  # Bypass limit check for whitelisted numbers

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


async def _check_payment_access(
    state_machine: UserStateMachine,
    phone_hash: str,
    raw_text: str
) -> tuple[str | None, Any]:
    """
    Check if user can access diagnostic service based on subscription/free tier.

    Uses state machine for single source of truth.

    Args:
        state_machine: UserStateMachine instance
        phone_hash: SHA-256 hash of phone number
        raw_text: User's message text

    Returns:
        Tuple of (error_message, state_info)
        - error_message: Error message if access denied, None if access allowed
        - state_info: UserStateInfo object for use in command handlers
    """
    # Check if number is whitelisted (same logic as usage limit check)
    import hashlib
    allowed_numbers = [
        n.strip()
        for n in settings.allowed_numbers.split(",")
        if n.strip()
    ]

    # Hash each allowed number and check if phone_hash matches
    for allowed_num in allowed_numbers:
        allowed_hash = hashlib.sha256(allowed_num.encode()).hexdigest()
        if phone_hash == allowed_hash:
            logger.info(
                "whitelisted_number_bypassing_payment_check",
                phone_hash=phone_hash
            )
            # Create a fake "subscribed" state for whitelisted numbers
            from app.services.user_state_machine import UserStateInfo, UserState
            return None, UserStateInfo(
                state=UserState.ACTIVE_SUBSCRIBER,
                phone_hash=phone_hash,
                diagnostics_used=0,
                diagnostics_remaining=999999,
                can_access_diagnostic=True,
                reason="whitelisted"
            )

    # Resolve current state
    state = state_machine.resolve_state(phone_hash)

    # Payment commands always allowed (checked separately)
    payment_keywords = ['subscribe', 'renew', 'cancel', 'status', 'help']
    if any(keyword in raw_text.lower() for keyword in payment_keywords):
        return None, state

    # Check if user can access diagnostics
    if state.can_access_diagnostic:
        return None, state  # Access allowed

    # Access denied - return payment prompt based on state
    if state.state.value == "pending_payment":
        return (
            f"⏳ Payment in progress\n\n"
            f"Order: {state.pending_order_reference}\n\n"
            f"📱 Check your phone for EcoCash prompt.\n\n"
            f"While you wait, you have {state.diagnostics_remaining} free diagnostics remaining this week."
        ), state
    elif state.state.value == "expired":
        return (
            f"⚠️ Subscription expired\n\n"
            f"You've used {state.diagnostics_used}/5 free diagnostics this week.\n\n"
            f"To renew unlimited access:\n"
            f"RENEW <email> <phone>\n\n"
            f"Example:\n"
            f"RENEW john@example.com 0771234567\n\n"
            f"💵 Only $2/month"
        ), state
    else:
        # FREE_TIER limit reached
        return (
            f"You've used all {state.diagnostics_used} free diagnostics this week.\n\n"
            f"📱 Subscribe for unlimited diagnostics!\n"
            f"💵 Only $2/month\n\n"
            f"To subscribe, reply with:\n"
            f"SUBSCRIBE <email> <phone>\n\n"
            f"Example:\n"
            f"SUBSCRIBE john@example.com 0771234567"
        ), state


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
        from app.core.http_clients import get_twilio_client
        client = get_twilio_client()
        await client.post(url, data=data, auth=auth)
        logger.info("twilio_reply_sent", to=to_number)
    except Exception as e:  # pylint: disable=broad-exception-caught
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
        session_id=phone_hash,
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
    repos: dict = Depends(get_repositories),
    payment_service: PaymentService = Depends(get_payment_service),
    state_machine: UserStateMachine = Depends(get_state_machine),
    command_handler: PaymentCommandHandler = Depends(get_command_handler)
):
    """
    Baileys WhatsApp webhook handler.

    Validates API key, checks idempotency, processes message.
    """
    # Don't log payload - can contain emojis that crash Windows console
    logger.info("baileys_webhook_started")

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

    # Ignore non-user senders (newsletters, status broadcasts, groups)
    if from_number and ("@newsletter" in from_number or "@broadcast" in from_number):
        logger.debug("ignoring_non_user_sender", from_number=from_number)
        return {"ok": True, "status": "ignored"}

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

    # Check usage limit (old rate limiting - keep for abuse prevention)
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

    # Check payment access using state machine (subscription/free tier)
    payment_access_msg, user_state = await _check_payment_access(
        state_machine, phone_hash, raw_text
    )
    if payment_access_msg:
        repos["message_repo"].insert_audit(
            message_id=message_id,
            phone_hash=phone_hash,
            request_id=request.state.request_id,
            session_id=None,
            request_text=raw_text,
            response_text=payment_access_msg,
            code=None
        )
        return {"reply": payment_access_msg, "status": "payment_required"}

    # Load session
    session = session_manager.load_session(phone_hash)

    # Check for payment commands first (SUBSCRIBE, RENEW, CANCEL, STATUS, HELP)
    logger.info("checking_payment_commands", raw_text=raw_text)

    # SUBSCRIBE or RENEW
    if command_handler.parse_subscribe_or_renew(raw_text):
        parsed = command_handler.parse_subscribe_or_renew(raw_text)
        email, phone, is_renew = parsed
        reply = await command_handler.handle_subscribe_or_renew(
            phone_hash, email, phone, is_renew
        )

        repos["message_repo"].insert_audit(
            message_id=message_id,
            phone_hash=phone_hash,
            request_id=request.state.request_id,
            session_id=None,
            request_text=raw_text,
            response_text=reply,
            code=None
        )

        return {"reply": reply}

    # STATUS
    logger.info("checking_status_command", raw_text=raw_text, parsed=command_handler.parse_status(raw_text))
    if command_handler.parse_status(raw_text):
        logger.info("status_command_matched")
        reply = await command_handler.handle_status(phone_hash)

        repos["message_repo"].insert_audit(
            message_id=message_id,
            phone_hash=phone_hash,
            request_id=request.state.request_id,
            session_id=None,
            request_text=raw_text,
            response_text=reply,
            code=None
        )

        return {"reply": reply}

    # CANCEL
    if command_handler.parse_cancel(raw_text):
        reply = await command_handler.handle_cancel(phone_hash)

        repos["message_repo"].insert_audit(
            message_id=message_id,
            phone_hash=phone_hash,
            request_id=request.state.request_id,
            session_id=None,
            request_text=raw_text,
            response_text=reply,
            code=None
        )

        return {"reply": reply}

    # HELP
    if command_handler.parse_help(raw_text):
        reply = await command_handler.handle_help(phone_hash)

        repos["message_repo"].insert_audit(
            message_id=message_id,
            phone_hash=phone_hash,
            request_id=request.state.request_id,
            session_id=None,
            request_text=raw_text,
            response_text=reply,
            code=None
        )

        return {"reply": reply}

    # Route message with session context for followups
    try:
        result = await message_router.route_message(
            raw_text=raw_text,
            phone_hash=phone_hash,
            request_id=request.state.request_id,
            session=session  # Pass session for conversation memory
        )
    except Exception as e:
        logger.error(
            "message_routing_failed",
            error=str(e),
            error_type=type(e).__name__,
            raw_text=raw_text,
            traceback=traceback.format_exc()
        )
        # Return fallback error response
        result = {
            "error": "Sorry, there was an error processing your request. Please try again later."
        }

    # Format response
    if isinstance(result, DiagnosticResult):
        # NEW CONFIDENCE-BASED IMAGE SYSTEM
        # Only send images for high-confidence component matches (≥80%)
        diagram = None
        component_match = None

        # Extract component with confidence scoring
        from app.services.component_mapper import extract_best_component_match, should_send_image

        component_match = extract_best_component_match(
            description=result.description,
            code=result.code
        )

        # Determine search term for diagram lookup
        if component_match:
            search_term = component_match.component.canonical_name
        else:
            search_term = result.system  # Fallback to system category

        # Log the image decision
        image_decision = {
            "code": result.code,
            "detected_component": component_match.component.canonical_name if component_match else None,
            "confidence": component_match.confidence if component_match else 0,
            "has_image": component_match.component.image_filename if component_match else None,
            "should_send": should_send_image(component_match) if component_match else False,
        }

        logger.info("image_decision", **image_decision)

        # Only attempt image send if confidence threshold met
        if component_match and should_send_image(component_match):
            try:
                diagram = repos["diagram_repo"].get_by_system_fuzzy(search_term)
                if diagram:
                    logger.info(
                        "high_confidence_component_match",
                        code=result.code,
                        component=component_match.component.canonical_name,
                        confidence=component_match.confidence,
                        diagram_system=diagram.system
                    )

                    # Send image FIRST (before text diagnosis)
                    image_sender = ImageSender(
                        baileys_webhook_url=getattr(settings, 'baileys_outbound_url', None),
                        timeout=15.0
                    )

                    image_sent = await image_sender.send_system_diagram(
                        to_number=from_number,
                        diagram=diagram
                    )

                    if image_sent:
                        logger.info(
                            "image_sent_successfully",
                            code=result.code,
                            component=component_match.component.canonical_name,
                            confidence=component_match.confidence
                        )
                    else:
                        logger.warning(
                            "image_send_failed_continuing",
                            code=result.code,
                            component=component_match.component.canonical_name
                        )
                else:
                    logger.info(
                        "high_confidence_match_but_no_diagram",
                        code=result.code,
                        component=component_match.component.canonical_name,
                        confidence=component_match.confidence
                    )

            except Exception as e:
                logger.error(
                    "image_send_error",
                    code=result.code,
                    error=str(e)
                )
                # Continue anyway - image errors never block text diagnosis
        else:
            # Log why image was not sent
            if component_match:
                if component_match.confidence < 80:
                    logger.info(
                        "image_not_sent_low_confidence",
                        code=result.code,
                        component=component_match.component.canonical_name,
                        confidence=component_match.confidence,
                        status="TEXT_ONLY"
                    )
                elif not component_match.component.image_filename:
                    logger.info(
                        "image_not_sent_no_file",
                        code=result.code,
                        component=component_match.component.canonical_name,
                        confidence=component_match.confidence,
                        status="TEXT_ONLY"
                    )
            else:
                logger.info(
                    "image_not_sent_no_component_match",
                    code=result.code,
                    description=result.description[:50],
                    status="TEXT_ONLY"
                )

        # Format text response
        reply_parts = format_diagnostic_response(result)
        code = result.code

        # Append attribution if diagram was found
        if diagram and diagram.attribution_text:
            attribution = format_attribution(diagram)
            if attribution:
                reply_parts.append(attribution)

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

        # Increment usage counter (for free tier tracking)
        try:
            usage_count = payment_service.increment_user_usage(phone_hash)
            logger.info("usage_incremented", phone_hash=phone_hash, count=usage_count)
        except Exception as e:
            logger.warning("usage_increment_failed", error=str(e))

    elif isinstance(result, SymptomDiagnosisResult):
        reply_parts = format_symptom_response(result)
        code = None

        # Increment usage for symptom diagnosis too
        try:
            payment_service.increment_user_usage(phone_hash)
        except Exception as e:
            logger.warning("usage_increment_failed", error=str(e))

    elif isinstance(result, dict) and "reply" in result:
        # Handle followup responses (AI-generated explanations)
        reply_parts = [result["reply"]]
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
