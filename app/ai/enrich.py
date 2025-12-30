from typing import Dict, Any, List, Optional

system_prompt = (
    "You are an automotive diagnostics assistant for mechanics. Keep responses concise and actionable."
)


def build_user_prompt(code: str, description: str, vehicle: Dict[str, Optional[str]]) -> str:
    make = vehicle.get("make") or ""
    model = vehicle.get("model") or ""
    year = vehicle.get("year") or ""
    engine = vehicle.get("engine") or ""
    return (
        f"Code: {code}\nDescription: {description}\nVehicle: {make} {model} {year} {engine}\n"
        "Return top 5 likely causes and short checks."
    )


def enrich_causes(base_info: Dict[str, Any], vehicle: Dict[str, Optional[str]]) -> List[str]:
    base_causes = base_info.get("common_causes") or ""
    items = [c.strip() for c in base_causes.split(",") if c.strip()]
    seen = set()
    ranked: List[str] = []
    for c in items:
        if c.lower() not in seen:
            seen.add(c.lower())
            ranked.append(c)
    if not ranked:
        ranked = [
            "Vacuum leak",
            "Faulty sensor",
            "Wiring/connector issue",
            "Air/fuel imbalance",
            "Exhaust leak",
        ]
    return ranked[:5]
