import re
from typing import Dict, Any

_OBD_REGEX = re.compile(r"^[PBCU][0-9]{4}$", re.IGNORECASE)


def validate_obd_code(code: str) -> bool:
    return bool(_OBD_REGEX.match(code or ""))


async def get_obd_info(db, code: str) -> Dict[str, Any]:
    doc = await db["obd_codes"].find_one({"code": code.upper()})
    if doc:
        return {
            "code": doc.get("code", code.upper()),
            "description": doc.get("description") or "",
            "symptoms": doc.get("symptoms") or "",
            "common_causes": doc.get("common_causes") or "",
            "generic_fixes": doc.get("generic_fixes") or "",
        }
    return {
        "code": code.upper(),
        "description": "Generic OBD-II DTC.",
        "symptoms": "",
        "common_causes": "Vacuum leak, faulty sensor, wiring issue",
        "generic_fixes": "Inspect vacuum lines, check connectors, verify sensor readings",
    }
