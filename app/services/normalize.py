import re
from typing import List


# Minimal keyword map; expandable
SYMPTOM_KEYWORDS = {
    "shaking": "rough_idle",
    "vibrating": "rough_idle",
    "rough idle": "rough_idle",
    "judder": "rough_idle",
    "low power": "low_power",
    "sluggish": "low_power",
    "no power": "low_power",
    "won't shift": "stuck_in_gear",
    "wont shift": "stuck_in_gear",
    "stuck in gear": "stuck_in_gear",
    "hard to start": "hard_start",
    "hard start": "hard_start",
    "cranking": "hard_start",
}


def normalize_symptoms(text: str) -> List[str]:
    t = (text or "").lower()
    # Normalize apostrophes
    t = t.replace("’", "'")
    found: List[str] = []
    for kw, key in SYMPTOM_KEYWORDS.items():
        if kw in t:
            found.append(key)
    # Also catch combined phrases split by spaces
    tokens = re.split(r"\W+", t)
    if "rough" in tokens and "idle" in tokens:
        found.append("rough_idle")
    if "low" in tokens and "power" in tokens:
        found.append("low_power")
    # Deduplicate while preserving order
    seen = set()
    out: List[str] = []
    for k in found:
        if k not in seen:
            seen.add(k)
            out.append(k)
    return out[:5]
