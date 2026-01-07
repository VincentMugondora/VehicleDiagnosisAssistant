import os
import re
from typing import Dict, Any, Optional

_OBD_REGEX = re.compile(r"^[PBCU][0-9]{4}$", re.IGNORECASE)


def validate_obd_code(code: str) -> bool:
    return bool(_OBD_REGEX.match(code or ""))


async def get_obd_info(db, code: str, vehicle: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    

    doc = await db["obd_codes"].find_one({"code": code.upper()})
    if doc:
        try:
            from app.providers.search import _sanitize_summary  # type: ignore
            causes_list = [c.strip() for c in (doc.get("common_causes") or "").split(",") if c.strip()]
            fixes_raw = doc.get("generic_fixes") or ""
            checks_list = [i.strip() for i in re.split(r"[,\n;]+", fixes_raw) if i and i.strip()]
            cleaned = _sanitize_summary(
                code,
                {
                    "description": doc.get("description") or "",
                    "causes": causes_list,
                    "checks": checks_list,
                },
            )
            if (
                cleaned.get("description") != (doc.get("description") or "")
                or ", ".join(cleaned.get("causes", []) or []) != (doc.get("common_causes") or "")
                or ", ".join(cleaned.get("checks", []) or []) != (doc.get("generic_fixes") or "")
            ):
                try:
                    await db["obd_codes"].update_one(
                        {"code": code.upper()},
                        {
                            "$set": {
                                "description": cleaned.get("description", "") or "",
                                "common_causes": ", ".join(cleaned.get("causes", []) or []),
                                "generic_fixes": ", ".join(cleaned.get("checks", []) or []),
                            }
                        },
                    )
                except Exception:
                    pass
            base = {
                "code": doc.get("code", code.upper()),
                "description": cleaned.get("description") or "",
                "symptoms": doc.get("symptoms") or "",
                "common_causes": ", ".join(cleaned.get("causes", []) or []),
                "generic_fixes": ", ".join(cleaned.get("checks", []) or []),
                "source": "local_db",
                "confidence": 0.95,
            }
        except Exception:
            base = {
                "code": doc.get("code", code.upper()),
                "description": doc.get("description") or "",
                "symptoms": doc.get("symptoms") or "",
                "common_causes": doc.get("common_causes") or "",
                "generic_fixes": doc.get("generic_fixes") or "",
                "source": "local_db",
                "confidence": 0.95,
            }
        if vehicle:
            try:
                v_norm = {
                    "make": str((vehicle.get("make") or "").strip().lower()),
                    "model": str((vehicle.get("model") or "").strip().lower()),
                    "year": str((vehicle.get("year") or "").strip().lower()),
                    "engine": str((vehicle.get("engine") or "").strip().lower()),
                }
                ov = await db["vehicle_overrides"].find_one({"code": code.upper(), **v_norm})
                if ov:
                    try:
                        from app.providers.search import _sanitize_summary  # type: ignore
                        ov_clean = _sanitize_summary(
                            code,
                            {
                                "description": base.get("description") or "",
                                "causes": ov.get("known_issues", []) or [],
                                "checks": ov.get("priority_checks", []) or [],
                            },
                        )
                        base_causes = [c.strip() for c in (base.get("common_causes") or "").split(",") if c.strip()]
                        merged_c = []
                        seen_c = set()
                        for citem in (ov_clean.get("causes", []) or []) + base_causes:
                            k = citem.lower()
                            if k not in seen_c:
                                seen_c.add(k)
                                merged_c.append(citem)
                        fixes_raw = base.get("generic_fixes") or ""
                        base_checks = [i.strip() for i in re.split(r"[,\n;]+", fixes_raw) if i and i.strip()]
                        merged_chk = []
                        seen_ch = set()
                        for it in (ov_clean.get("checks", []) or []) + base_checks:
                            k = it.lower()
                            if k not in seen_ch:
                                seen_ch.add(k)
                                merged_chk.append(it)
                        base["common_causes"] = ", ".join(merged_c)
                        base["generic_fixes"] = ", ".join(merged_chk)
                        base["source"] = "vehicle_override"
                        base["confidence"] = 0.98
                    except Exception:
                        pass
            except Exception:
                pass
        return base
    return {
        "code": code.upper(),
        "description": "Generic OBD-II diagnostic trouble code",
        "symptoms": "",
        "common_causes": "Faulty sensor, Wiring or connector issue, ECM software fault",
        "generic_fixes": "Inspect wiring, Check connectors, Clear code and retest",
        "source": "fallback",
        "confidence": 0.30,
    }
