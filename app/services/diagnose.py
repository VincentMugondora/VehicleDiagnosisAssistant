import json
import os
from typing import List, Dict, Any

def diagnose(symptoms: List[str]) -> Dict[str, Any]:
    """
    Given a list of normalized symptom keys, return aggregated probable codes,
    systems, and general checks.
    """
    if not symptoms:
        return {"probable_codes": [], "likely_systems": [], "recommended_checks": []}

    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "symptoms.json")
    try:
        with open(data_path, "r", encoding="utf-8") as f:
            symptoms_db = json.load(f)
    except Exception:
        symptoms_db = {}

    probable_codes = []
    likely_systems = []
    
    for sym in symptoms:
        info = symptoms_db.get(sym)
        if not info:
            continue
        probable_codes.extend(info.get("related_codes", []))
        likely_systems.extend(info.get("likely_systems", []))
        
    # Deduplicate while preserving order
    def dedupe(items):
        seen = set()
        out = []
        for it in items:
            if it not in seen:
                seen.add(it)
                out.append(it)
        return out
        
    probable_codes = dedupe(probable_codes)
    likely_systems = dedupe(likely_systems)
    
    # Generate some simple recommended checks based on the likely systems
    checks_map = {
        "Ignition": "Inspect spark plugs and ignition coils",
        "Fuel": "Check fuel pressure and injectors",
        "Air Intake": "Inspect for vacuum leaks and clean MAF sensor",
        "Transmission": "Check transmission fluid level and condition",
        "Electrical": "Test battery voltage and alternator output",
        "EGR": "Inspect EGR valve for carbon buildup",
        "Crankshaft Sensor": "Test crankshaft position sensor"
    }
    
    recommended_checks = []
    for sys in likely_systems:
        if sys in checks_map:
            recommended_checks.append(checks_map[sys])
            
    if not recommended_checks:
        recommended_checks = ["Perform a complete visual inspection", "Scan for active or pending OBD-II codes"]
        
    return {
        "probable_codes": probable_codes,
        "likely_systems": likely_systems,
        "recommended_checks": recommended_checks
    }
