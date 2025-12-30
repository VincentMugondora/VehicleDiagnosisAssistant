import os
import hmac
import base64
import hashlib
import re
from typing import Dict, Any, Optional

import httpx
from fastapi import APIRouter, Request, Response, status, Depends
from sqlalchemy.orm import Session

from app.db.models import get_session, MessageLog
from app.services.obd import validate_obd_code, get_obd_info
from app.ai.enrich import enrich_causes, system_prompt, build_user_prompt

router = APIRouter(prefix="/webhook", tags=["webhook"])


def _compute_twilio_signature(url: str, form_params: Dict[str, Any], auth_token: str) -> str:
    s = url + "".join([f"{k}{v}" for k, v in sorted((k, str(v)) for k, v in form_params.items())])
    digest = hmac.new(auth_token.encode("utf-8"), s.encode("utf-8"), hashlib.sha1).digest()
    return base64.b64encode(digest).decode("utf-8")


def _parse_vehicle_details(text: str) -> Dict[str, Optional[str]]:
    year_match = re.search(r"\b(19|20)\d{2}\b", text)
    engine_match = re.search(r"\b(\d\.\dL|V\d|I\d)\b", text, re.IGNORECASE)
    parts = re.sub(r"\s+", " ", text).strip().split(" ")
    make = parts[0] if parts else None
    model = None
    if len(parts) >= 2:
        model = parts[1]
    year = year_match.group(0) if year_match else None
    engine = engine_match.group(0) if engine_match else None
    return {"make": make, "model": model, "year": year, "engine": engine}


def _format_reply(code: str, base_info: Dict[str, Any], causes_ranked: Optional[list]) -> str:
    lines = []
    meaning = base_info.get("description") or "Unknown description"
    lines.append(f"Code: {code}")
    lines.append(f"Meaning: {meaning}")
    causes = causes_ranked or (base_info.get("common_causes") or "").split(",")
    causes = [c.strip() for c in causes if c and c.strip()]
    if causes:
        lines.append("Likely causes:")
        for c in causes[:5]:
            lines.append(f"- {c}")
    fixes = base_info.get("generic_fixes") or "Check basics: wiring, connectors, vacuum leaks, and sensor integrity."
    lines.append(f"Recommended checks: {fixes}")
    return "\n".join(lines)


async def _maybe_send_reply_via_twilio(to_number: str, body: str) -> None:
    send_flag = os.getenv("TWILIO_SEND_REPLY", "false").lower() == "true"
    if not send_flag:
        return
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_WHATSAPP_FROM")
    if not all([account_sid, auth_token, from_number]):
        return
    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
    data = {"To": to_number, "From": from_number, "Body": body}
    auth = (account_sid, auth_token)
    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(url, data=data, auth=auth)


@router.post("/twilio")
async def twilio_webhook(request: Request, db: Session = Depends(get_session)):
    form = await request.form()
    data = {k: v for k, v in form.items()}

    validate = os.getenv("TWILIO_VALIDATE_SIGNATURE", "true").lower() == "true"
    if validate:
        provided = request.headers.get("X-Twilio-Signature", "")
        expected = _compute_twilio_signature(str(request.url), data, os.getenv("TWILIO_AUTH_TOKEN", ""))
        if not hmac.compare_digest(provided, expected):
            return Response(status_code=status.HTTP_403_FORBIDDEN)

    from_number = data.get("From", "")
    raw_text = (data.get("Body") or "").strip()

    code_match = re.search(r"\b[PBCU][0-9]{4}\b", raw_text, re.IGNORECASE)
    code = code_match.group(0).upper() if code_match else None

    vehicle_text = raw_text.replace(code, "").strip() if code else raw_text
    vehicle = _parse_vehicle_details(vehicle_text)

    if not code or not validate_obd_code(code):
        reply = "Please send a valid OBD-II code (e.g., P0171) and optional vehicle details (make model year engine)."
        await _maybe_send_reply_via_twilio(from_number, reply)
        db.add(MessageLog(phone_number=from_number, request_text=raw_text, response_text=reply, code=None))
        db.commit()
        return {"ok": True}

    base_info = get_obd_info(db, code)
    causes_ranked = enrich_causes(base_info, vehicle)
    reply = _format_reply(code, base_info, causes_ranked)

    await _maybe_send_reply_via_twilio(from_number, reply)

    db.add(MessageLog(phone_number=from_number, request_text=raw_text, response_text=reply, code=code))
    db.commit()

    return {"ok": True}
