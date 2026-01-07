import os
import re
from typing import Dict, Any, Optional

_OBD_REGEX = re.compile(r"^[PBCU][0-9]{4}$", re.IGNORECASE)


def validate_obd_code(code: str) -> bool:
    return bool(_OBD_REGEX.match(code or ""))


async def get_obd_info(db, code: str, vehicle: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    # Prefer a per-vehicle summary if available
    try:
        save_per_vehicle = os.getenv("EXTERNAL_SAVE_PER_VEHICLE", "true").strip().lower() == "true"
        if vehicle and save_per_vehicle:
            v_norm = {
                "make": str((vehicle.get("make") or "").strip().lower()),
                "model": str((vehicle.get("model") or "").strip().lower()),
                "year": str((vehicle.get("year") or "").strip().lower()),
                "engine": str((vehicle.get("engine") or "").strip().lower()),
            }
            pv = await db["obd_summaries"].find_one({"code": code.upper(), **v_norm})
            if pv:
                # Sanitize legacy/older saved summaries to ensure clean reply
                try:
                    from app.providers.search import _sanitize_summary  # type: ignore
                    cleaned = _sanitize_summary(
                        code,
                        {
                            "description": pv.get("description") or "",
                            "causes": pv.get("causes", []) or [],
                            "checks": pv.get("checks", []) or [],
                        },
                    )
                    # If changed, persist sanitized version
                    if (
                        cleaned.get("description") != (pv.get("description") or "")
                        or cleaned.get("causes") != (pv.get("causes") or [])
                        or cleaned.get("checks") != (pv.get("checks") or [])
                    ):
                        try:
                            await db["obd_summaries"].update_one(
                                {"code": code.upper(), **v_norm},
                                {
                                    "$set": {
                                        "description": cleaned.get("description", "") or "",
                                        "causes": cleaned.get("causes", []) or [],
                                        "checks": cleaned.get("checks", []) or [],
                                    }
                                },
                            )
                        except Exception:
                            pass
                except Exception:
                    cleaned = {
                        "description": pv.get("description") or "",
                        "causes": pv.get("causes", []) or [],
                        "checks": pv.get("checks", []) or [],
                    }
                return {
                    "code": code.upper(),
                    "description": cleaned.get("description") or "",
                    "symptoms": "",
                    "common_causes": ", ".join(cleaned.get("causes", []) or []),
                    "generic_fixes": ", ".join(cleaned.get("checks", []) or []),
                }
    except Exception:
        pass

    doc = await db["obd_codes"].find_one({"code": code.upper()})
    if doc:
        # Sanitize primary record on read
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
            # persist if changed
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
            }
        except Exception:
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
            always_enrich = os.getenv("EXTERNAL_ENRICH_ALWAYS", "false").strip().lower() == "true"
            if is_generic or not has_causes or always_enrich:
                try:
                    print(f"[obd] enrich: is_generic={is_generic} has_causes={has_causes} always_enrich={always_enrich}")
                except Exception:
                    pass
                external = await get_external_obd(db, code.upper(), vehicle or {})
                try:
                    print(f"[obd] external_summary={'yes' if external else 'no'}")
                except Exception:
                    pass
                if external:
                    ext_desc = str(external.get("description") or "").strip()
                    ext_causes = [str(x).strip() for x in (external.get("causes") or []) if str(x).strip()]
                    ext_checks = [str(x).strip() for x in (external.get("checks") or []) if str(x).strip()]
                    # Only override description if generic
                    if ext_desc and is_generic:
                        base["description"] = ext_desc
                    if ext_causes or ext_checks:
                        if always_enrich:
                            # Replace to avoid stale/noisy data when enrichment is forced
                            if ext_causes:
                                base["common_causes"] = ", ".join(ext_causes)
                            if ext_checks:
                                base["generic_fixes"] = ", ".join(ext_checks)
                        else:
                            # Merge/dedupe
                            if ext_causes:
                                base_causes = [c.strip() for c in (base.get("common_causes") or "").split(",") if c.strip()]
                                merged = []
                                seen = set()
                                for c in base_causes + ext_causes:
                                    key = c.lower()
                                    if key not in seen:
                                        seen.add(key)
                                        merged.append(c)
                                base["common_causes"] = ", ".join(merged)
                            if ext_checks:
                                fixes_raw = base.get("generic_fixes") or ""
                                base_checks = [i.strip() for i in re.split(r"[,\n;]+", fixes_raw) if i and i.strip()]
                                merged_checks = []
                                seen2 = set()
                                for c in base_checks + ext_checks:
                                    key = c.lower()
                                    if key not in seen2:
                                        seen2.add(key)
                                        merged_checks.append(c)
                                base["generic_fixes"] = ", ".join(merged_checks)
        except Exception:
            pass
        return base
    # Not found in DB: attempt external before falling back to generic
    try:
        from app.providers.search import get_external_obd  # local import to avoid cycles
        try:
            print("[obd] not_found: attempting external")
        except Exception:
            pass
        external = await get_external_obd(db, code.upper(), vehicle or {})
        try:
            print(f"[obd] external_summary={'yes' if external else 'no'}")
        except Exception:
            pass
        if external:
            ext_desc = str(external.get("description") or "").strip()
            ext_causes = [str(x).strip() for x in (external.get("causes") or []) if str(x).strip()]
            ext_checks = [str(x).strip() for x in (external.get("checks") or []) if str(x).strip()]
            return {
                "code": code.upper(),
                "description": ext_desc or f"OBD-II code {code.upper()}",
                "symptoms": "",
                "common_causes": ", ".join(ext_causes) if ext_causes else "",
                "generic_fixes": ", ".join(ext_checks) if ext_checks else "",
            }
    except Exception:
        pass
    return {
        "code": code.upper(),
        "description": "Generic OBD-II DTC.",
        "symptoms": "",
        "common_causes": "Vacuum leak, faulty sensor, wiring issue",
        "generic_fixes": "Inspect vacuum lines, check connectors, verify sensor readings",
    }
