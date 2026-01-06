import re
from typing import Dict, Any

_OBD_REGEX = re.compile(r"^[PBCU][0-9]{4}$", re.IGNORECASE)


def validate_obd_code(code: str) -> bool:
    return bool(_OBD_REGEX.match(code or ""))


async def get_obd_info(db, code: str) -> Dict[str, Any]:
    doc = await db["obd_codes"].find_one({"code": code.upper()})
    if doc:
        base = {
            "code": doc.get("code", code.upper()),
            "description": doc.get("description") or "",
            "symptoms": doc.get("symptoms") or "",
            "common_causes": doc.get("common_causes") or "",
            "generic_fixes": doc.get("generic_fixes") or "",
        }
        # If DB is generic or lacks causes, try external fallback (no vehicle context here)
        try:
            from app.providers.search import get_external_obd  # local import to avoid cycles
            desc_low = (base.get("description") or "").strip().lower()
            has_causes = bool((base.get("common_causes") or "").strip())
            is_generic = (not desc_low) or ("generic obd-ii dtc" in desc_low)
            if is_generic or not has_causes:
                external = await get_external_obd(db, code.upper(), {})
                if external:
                    ext_desc = str(external.get("description") or "").strip()
                    ext_causes = [str(x).strip() for x in (external.get("causes") or []) if str(x).strip()]
                    ext_checks = [str(x).strip() for x in (external.get("checks") or []) if str(x).strip()]
                    if ext_desc and is_generic:
                        base["description"] = ext_desc
                    if ext_causes:
                        base["common_causes"] = ", ".join(ext_causes)
                    if ext_checks:
                        base["generic_fixes"] = ", ".join(ext_checks)
        except Exception:
            pass
        return base
    return {
        "code": code.upper(),
        "description": "Generic OBD-II DTC.",
        "symptoms": "",
        "common_causes": "Vacuum leak, faulty sensor, wiring issue",
        "generic_fixes": "Inspect vacuum lines, check connectors, verify sensor readings",
    }
