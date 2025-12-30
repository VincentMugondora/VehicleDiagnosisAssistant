import re
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.db.models import ObdCode

_OBD_REGEX = re.compile(r"^[PBCU][0-9]{4}$", re.IGNORECASE)


def validate_obd_code(code: str) -> bool:
    return bool(_OBD_REGEX.match(code or ""))


def get_obd_info(db: Session, code: str) -> Dict[str, Any]:
    rec = db.query(ObdCode).filter(ObdCode.code == code.upper()).first()
    if rec:
        return {
            "code": rec.code,
            "description": rec.description,
            "symptoms": rec.symptoms or "",
            "common_causes": rec.common_causes or "",
            "generic_fixes": rec.generic_fixes or "",
        }
    return {
        "code": code.upper(),
        "description": "Generic OBD-II DTC.",
        "symptoms": "",
        "common_causes": "Vacuum leak, faulty sensor, wiring issue",
        "generic_fixes": "Inspect vacuum lines, check connectors, verify sensor readings",
    }
