"""
Web Chat API for OBD-II diagnostics.

Provides a REST endpoint that reuses the existing MessageRouter
to deliver the same diagnosis quality as the WhatsApp bot.
"""

import uuid
from datetime import UTC, datetime
from fastapi import APIRouter, File, Form, UploadFile
from pydantic import BaseModel

from app.models.diagnostic import DiagnosticResult, SymptomDiagnosisResult
from app.models.session import SessionState
from app.services.message_router import MessageRouter
from app.services.obd_service import OBDService
from app.services.ai_client import AIClient
from app.repositories.obd_repository import OBDRepository
from app.repositories.session_repository import SessionRepository
from app.repositories.message_log_repository import MessageLogRepository
from app.db.client import get_supabase_client
from app.core.config import settings
from app.core.logging import logger

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    code: str | None = None
    type: str  # "diagnosis" | "symptom" | "followup" | "error"


def get_chat_dependencies():
    client = get_supabase_client()
    obd_repo = OBDRepository(client)
    session_repo = SessionRepository(client)
    message_repo = MessageLogRepository(client)

    ai_client = None
    try:
        ai_client = AIClient()
    except Exception:
        pass

    obd_service = OBDService(obd_repo, ai_client=ai_client, auto_learn=settings.auto_learn_codes)
    router_instance = MessageRouter(obd_service)
    if ai_client and not router_instance.ai_client:
        router_instance.ai_client = ai_client
    return router_instance, session_repo, message_repo


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest):
    message_router, session_repo, message_repo = get_chat_dependencies()
    session_id = req.session_id or str(uuid.uuid4())

    session = session_repo.get_by_phone_hash(session_id)
    if not session:
        session = SessionState(phone_hash=session_id, last_active=datetime.now(UTC))

    request_id = str(uuid.uuid4())

    result = await message_router.route_message(
        raw_text=req.message,
        phone_hash=session_id,
        request_id=request_id,
        session=session
    )

    session_repo.upsert_session(session)

    if isinstance(result, DiagnosticResult):
        from app.services.diagnostic_formatter import format_diagnostic_report
        reply = format_diagnostic_report(result)
        response = ChatResponse(
            session_id=session_id,
            reply=reply,
            code=result.code,
            type="diagnosis"
        )

    elif isinstance(result, SymptomDiagnosisResult):
        lines = []
        if result.likely_systems:
            lines.append("**Possible systems affected:**")
            lines.append(", ".join(result.likely_systems[:5]))
            lines.append("")
        if result.probable_codes:
            lines.append("**Common codes:**")
            lines.append(", ".join(result.probable_codes[:6]))
            lines.append("")
        if result.recommended_checks:
            lines.append("**Recommended checks:**")
            for c in result.recommended_checks[:6]:
                lines.append(f"- {c}")
        reply = "\n".join(lines)
        response = ChatResponse(
            session_id=session_id,
            reply=reply,
            type="symptom"
        )

    elif isinstance(result, dict) and "reply" in result:
        response = ChatResponse(
            session_id=session_id,
            reply=result["reply"],
            type="followup"
        )

    else:
        error_msg = result.get("error", "Unable to process your message.")
        if session.last_diagnosis and "Send an OBD-II code" in error_msg:
            last = session.last_diagnosis
            reply = (
                f"I can see your last diagnosis was {last.code} ({last.description}). "
                f"The AI followup service is temporarily unavailable. "
                f"Please try rephrasing your question or send another OBD code."
            )
            response = ChatResponse(session_id=session_id, reply=reply, type="followup")
        else:
            response = ChatResponse(
                session_id=session_id,
                reply=error_msg,
                type="error"
            )

    message_repo.insert_audit(
        message_id=request_id,
        phone_hash=session_id,
        request_id=request_id,
        session_id=session_id,
        request_text=req.message,
        response_text=response.reply,
        code=response.code,
    )

    return response


_ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic"}
_MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/image", response_model=ChatResponse)
async def chat_image(
    image: UploadFile = File(...),
    message: str = Form(default=""),
    session_id: str = Form(default=""),
):
    """Analyze an uploaded vehicle photo for visible issues."""
    from app.services.gemini_client import GeminiClient

    session_id = session_id or str(uuid.uuid4())

    if image.content_type not in _ALLOWED_IMAGE_TYPES:
        return ChatResponse(
            session_id=session_id,
            reply=f"Unsupported image type. Please upload JPEG, PNG, or WebP.",
            type="error",
        )

    image_bytes = await image.read()
    if len(image_bytes) > _MAX_IMAGE_SIZE:
        return ChatResponse(
            session_id=session_id,
            reply="Image too large. Please upload an image under 10 MB.",
            type="error",
        )

    try:
        gemini = GeminiClient()
    except Exception:
        return ChatResponse(
            session_id=session_id,
            reply="Image analysis is currently unavailable (AI service not configured).",
            type="error",
        )

    try:
        analysis = await gemini.analyze_image(
            image_bytes=image_bytes,
            mime_type=image.content_type,
            user_context=message,
        )
    except Exception as e:
        logger.error("image_analysis_failed", error=str(e))
        return ChatResponse(
            session_id=session_id,
            reply="Unable to analyze the image. Please try again or describe the issue in text.",
            type="error",
        )

    return ChatResponse(
        session_id=session_id,
        reply=analysis,
        type="followup",
    )
