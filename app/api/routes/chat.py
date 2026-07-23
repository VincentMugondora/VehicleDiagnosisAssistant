"""
Web Chat API for OBD-II diagnostics.

Provides a REST endpoint that reuses the existing MessageRouter
to deliver the same diagnosis quality as the WhatsApp bot.
"""

import uuid
from datetime import datetime
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.models.diagnostic import DiagnosticResult, SymptomDiagnosisResult
from app.models.session import SessionState
from app.services.message_router import MessageRouter
from app.services.obd_service import OBDService
from app.services.ai_client import AIClient
from app.repositories.obd_repository import OBDRepository
from app.db.client import get_supabase_client
from app.core.config import settings
from app.core.logging import logger

router = APIRouter(prefix="/chat", tags=["chat"])

_sessions: dict[str, SessionState] = {}


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    code: str | None = None
    type: str  # "diagnosis" | "symptom" | "followup" | "error"


def get_chat_router():
    client = get_supabase_client()
    obd_repo = OBDRepository(client)

    ai_client = None
    try:
        ai_client = AIClient()
    except Exception:
        pass

    obd_service = OBDService(obd_repo, ai_client=ai_client, auto_learn=settings.auto_learn_codes)
    router_instance = MessageRouter(obd_service)
    if ai_client and not router_instance.ai_client:
        router_instance.ai_client = ai_client
    return router_instance


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest, message_router: MessageRouter = Depends(get_chat_router)):
    session_id = req.session_id or str(uuid.uuid4())

    if session_id not in _sessions:
        _sessions[session_id] = SessionState(phone_hash=session_id, last_active=datetime.utcnow())

    session = _sessions[session_id]
    request_id = str(uuid.uuid4())

    result = await message_router.route_message(
        raw_text=req.message,
        phone_hash=session_id,
        request_id=request_id,
        session=session
    )

    if isinstance(result, DiagnosticResult):
        from app.services.diagnostic_formatter import format_diagnostic_report
        reply = format_diagnostic_report(result)
        return ChatResponse(
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
        return ChatResponse(
            session_id=session_id,
            reply=reply,
            type="symptom"
        )

    elif isinstance(result, dict) and "reply" in result:
        return ChatResponse(
            session_id=session_id,
            reply=result["reply"],
            type="followup"
        )

    else:
        error_msg = result.get("error", "Unable to process your message.")
        return ChatResponse(
            session_id=session_id,
            reply=error_msg,
            type="error"
        )
