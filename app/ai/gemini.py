import os
import re
from typing import Dict, List, Optional

import google.generativeai as genai


def _configure() -> None:
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        genai.configure(api_key=api_key)


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
    model = genai.GenerativeModel(model_name)

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
        resp = model.generate_content(prompt)
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
