import re
from typing import Dict, Optional

_OBD_CODE_PATTERN = re.compile(r"\b([PpBbCcUu])\s*([0-9O]{4})\b")
_YEAR_PATTERN = re.compile(r"\b(19|20)\d{2}\b")
_ENGINE_PATTERN = re.compile(r"\b(\d\.\dL|[VvIi]\d)\b")


def _normalize_code(letter: str, digits: str) -> str:
    # Mechanics sometimes type 'O' instead of '0'
    normalized = digits.upper().replace("O", "0")
    return f"{letter.upper()}{normalized}"


def parse_message(text: str) -> Dict[str, Optional[str]]:
    """
    Extract OBD code and basic vehicle details from a free-form message.
    Returns a dict with keys: code, make, model, year, engine.
    """
    text = (text or "").strip()

    code = None
    m = _OBD_CODE_PATTERN.search(text)
    if m:
        code = _normalize_code(m.group(1), m.group(2))
        # Remove the matched portion from the text for vehicle parsing
        start, end = m.span()
        vehicle_text = (text[:start] + " " + text[end:]).strip()
    else:
        vehicle_text = text

    # Simple vehicle parsing heuristics
    year_match = _YEAR_PATTERN.search(vehicle_text)
    engine_match = _ENGINE_PATTERN.search(vehicle_text)

    year = year_match.group(0) if year_match else None
    engine = engine_match.group(0) if engine_match else None

    # Remove year and engine tokens for make/model selection
    cleaned = vehicle_text
    if year:
        cleaned = cleaned.replace(year, " ")
    if engine:
        cleaned = cleaned.replace(engine, " ")
    cleaned = re.sub(r"[\-_,.;]+", " ", cleaned)
    tokens = [t for t in re.split(r"\s+", cleaned) if t]

    make = tokens[0] if tokens else None
    model = tokens[1] if len(tokens) > 1 else None

    return {
        "code": code,
        "make": make,
        "model": model,
        "year": year,
        "engine": engine,
    }
