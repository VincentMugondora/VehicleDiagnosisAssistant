import os
import re
from typing import Dict, List, Optional

try:
    # Preferred: new official SDK
    from google import genai as genai_new  # type: ignore
    _GENAI_MODE = "new"
except Exception:
    try:
        # Fallback: deprecated SDK (kept for compatibility)
        import google.generativeai as genai_old  # type: ignore
        _GENAI_MODE = "old"
    except Exception:
        genai_new = None  # type: ignore
        genai_old = None  # type: ignore
        _GENAI_MODE = "none"

_GENAI_CLIENT = None


def _configure() -> None:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return
    global _GENAI_CLIENT
    if _GENAI_MODE == "new":
        # Lazily initialize client
        if _GENAI_CLIENT is None:
            _GENAI_CLIENT = genai_new.Client(api_key=api_key)  # type: ignore
    elif _GENAI_MODE == "old":
        genai_old.configure(api_key=api_key)  # type: ignore


def _normalize_items(lines: List[str]) -> List[str]:
    cleaned: List[str] = []
    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        s = re.sub(r"^[\-•\d\.)\s]+", "", s)
        s = s.strip()
        if s:
            cleaned.append(s)
    return cleaned


def rank_causes_with_gemini(base_info: Dict[str, str], vehicle: Dict[str, Optional[str]]) -> List[str]:
    _configure()
    model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

    base_causes_raw = base_info.get("common_causes") or ""
    base_causes = [c.strip() for c in base_causes_raw.split(",") if c.strip()]

    make = vehicle.get("make") or ""
    model_name_vehicle = vehicle.get("model") or ""
    year = vehicle.get("year") or ""
    engine = vehicle.get("engine") or ""

    prompt = (
        "You are an automotive diagnostics assistant for mechanics. "
        "Only rephrase and rank the provided list of causes. Do not invent any new items. "
        "Return only the top 5 causes as a plain list, one per line, no numbering if possible.\n\n"
        f"Code description: {base_info.get('description') or ''}\n"
        f"Vehicle: {make} {model_name_vehicle} {year} {engine}\n"
        f"Causes to rank: {', '.join(base_causes)}\n"
    )

    try:
        if _GENAI_MODE == "new":
            if _GENAI_CLIENT is None:
                # Safety check; configuration failed
                raise RuntimeError("Gemini client not initialized")
            resp = _GENAI_CLIENT.models.generate_content(model=model_name, contents=[prompt])  # type: ignore
        elif _GENAI_MODE == "old":
            model = genai_old.GenerativeModel(model_name)  # type: ignore
            resp = model.generate_content(prompt)
        else:
            # No AI available; return base causes
            return base_causes[:5]
        txt = resp.text or ""
        lines = txt.splitlines()
        ranked = _normalize_items(lines)
        # Keep only items that were in the original list, preserve order from model
        allowed_set = {x.lower(): x for x in base_causes}
        filtered: List[str] = []
        for item in ranked:
            key = item.lower()
            # try to match loosely against allowed items
            match = next((allowed_set[a.lower()] for a in allowed_set if key.startswith(a.lower()) or a.lower() in key), None)
            if match and match not in filtered:
                filtered.append(match)
        if not filtered:
            filtered = base_causes
        return filtered[:5]
    except Exception:
        return base_causes[:5]
