import os
import hmac
import base64
import hashlib
import re
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

import httpx
from fastapi import APIRouter, Request, Response, status, Depends

from app.db.mongo import get_db
from app.services.obd import validate_obd_code, get_obd_info
from app.ai.enrich import enrich_causes, system_prompt, build_user_prompt
from app.services.parser import parse_message

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
    meaning = base_info.get("description") or "Unknown description"
    # Determine causes list
    if causes_ranked and isinstance(causes_ranked, list) and len(causes_ranked) > 0:
        causes = [str(c).strip() for c in causes_ranked if str(c).strip()]
    else:
        raw = base_info.get("common_causes") or ""
        causes = [c.strip() for c in raw.split(",") if c and c.strip()]

    # Determine checks/fixes list
    fixes_raw = base_info.get("generic_fixes") or ""
    fix_items = [i.strip() for i in re.split(r"[\,\n;]+", fixes_raw) if i and i.strip()]
    if not fix_items:
        fix_items = [
            "Inspect intake hoses for cracks",
            "Clean MAF sensor",
            "Check fuel pressure",
        ]

    max_causes = _get_int_env("REPLY_MAX_CAUSES", 3)
    max_checks = _get_int_env("REPLY_MAX_CHECKS", 3)

    lines = []
    lines.append(f"🚗 Code: {code}")
    lines.append("")
    lines.append("Meaning:")
    lines.append(meaning)

    if causes:
        lines.append("")
        lines.append("Likely causes:")
        for idx, c in enumerate(causes[:max_causes], start=1):
            suffix = " (very common)" if idx == 1 else ""
            lines.append(f"{idx}. {c}{suffix}")

    if fix_items:
        lines.append("")
        lines.append("Recommended checks:")
        for f in fix_items[:max_checks]:
            lines.append(f"• {f}")

    lines.append("")
    lines.append("ℹ️ Generic guidance. Confirm with physical inspection.")
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


def _get_int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)).strip())
    except Exception:
        return default


async def _check_usage_limit(db, phone_number: str) -> Optional[str]:
    limit = _get_int_env("USAGE_LIMIT_PER_NUMBER", 0)
    if limit <= 0:
        return None
    window_days = _get_int_env("USAGE_LIMIT_WINDOW_DAYS", 30)
    window_start = datetime.utcnow() - timedelta(days=window_days)
    count = await db["message_logs"].count_documents({
        "phone_number": phone_number,
        "created_at": {"$gte": window_start},
    })
    if count >= limit:
        return (
            "Limit reached. Reply later or contact support to upgrade."
        )
    return None


def _is_allowed_number(phone_number: str) -> bool:
    raw = os.getenv("ALLOWED_NUMBERS", "")
    if not raw:
        return False
    allowed = [n.strip() for n in raw.split(",") if n.strip()]
    return phone_number in allowed


@router.post("/twilio")
async def twilio_webhook(request: Request, db = Depends(get_db)):
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

    # Enforce simple per-number usage limits if configured
    limit_msg = None if _is_allowed_number(from_number) else await _check_usage_limit(db, from_number)
    if limit_msg:
        await _maybe_send_reply_via_twilio(from_number, limit_msg)
        await db["message_logs"].insert_one({
            "phone_number": from_number,
            "request_text": raw_text,
            "response_text": limit_msg,
            "code": None,
            "created_at": datetime.utcnow(),
        })
        return {"ok": True}

    parsed = parse_message(raw_text)
    code = parsed.get("code")
    vehicle = {
        "make": parsed.get("make"),
        "model": parsed.get("model"),
        "year": parsed.get("year"),
        "engine": parsed.get("engine"),
    }

    if not code or not validate_obd_code(code):
        reply = "Send an OBD-II code like P0171. Optional: add vehicle (e.g., Corolla 2015 1.6L)."
        await _maybe_send_reply_via_twilio(from_number, reply)
        await db["message_logs"].insert_one({
            "phone_number": from_number,
            "request_text": raw_text,
            "response_text": reply,
            "code": None,
            "created_at": datetime.utcnow(),
        })
        return {"ok": True}

    base_info = await get_obd_info(db, code)
    use_ai = os.getenv("AI_ENRICH_ENABLED", "false").lower() == "true"
    causes_ranked = None
    if use_ai:
        try:
            causes_ranked = enrich_causes(base_info, vehicle)
        except Exception:
            causes_ranked = None
    reply = _format_reply(code, base_info, causes_ranked)

    await _maybe_send_reply_via_twilio(from_number, reply)

    await db["message_logs"].insert_one({
        "phone_number": from_number,
        "request_text": raw_text,
        "response_text": reply,
        "code": code,
        "created_at": datetime.utcnow(),
    })

    return {"ok": True}
