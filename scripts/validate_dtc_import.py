#!/usr/bin/env python3
"""
Validate OBD-II DTC import against known SAE J2012 standards.

Spot-checks the top 15 commonly-searched codes to ensure accuracy.
Reference: https://www.obd-codes.com
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.client import get_supabase_client
from app.core.config import settings


# SAE J2012 reference definitions for validation
# Source: OBD-Codes.com (cross-referenced)
SAE_REFERENCE_CODES = {
    "P0300": {
        "desc_contains": ["random", "multiple", "misfire"],
        "system": "Powertrain",
    },
    "P0420": {
        "desc_contains": ["catalyst", "efficiency", "threshold"],
        "system": "Powertrain",
    },
    "P0171": {
        "desc_contains": ["system", "lean", "bank 1"],
        "system": "Powertrain",
    },
    "P0455": {
        "desc_contains": ["evap", "leak", "large"],
        "system": "Powertrain",
    },
    "P0128": {
        "desc_contains": ["coolant", "thermostat", "temperature"],
        "system": "Powertrain",
    },
    "P0401": {
        "desc_contains": ["egr", "flow"],
        "system": "Powertrain",
    },
    "P0442": {
        "desc_contains": ["evap", "leak", "small"],
        "system": "Powertrain",
    },
    "P0506": {
        "desc_contains": ["idle", "rpm", "lower"],
        "system": "Powertrain",
    },
    "P0700": {
        "desc_contains": ["transmission", "control"],
        "system": "Powertrain",
    },
    "P1404": {
        "desc_contains": ["exhaust", "gas", "recirculation"],  # EGR = Exhaust Gas Recirculation
        "system": "Powertrain",
    },
    "P0135": {
        "desc_contains": ["o2", "sensor", "heater", "bank 1", "sensor 1"],  # O2 is oxygen sensor
        "system": "Powertrain",
    },
    "P0174": {
        "desc_contains": ["system", "lean", "bank 2"],
        "system": "Powertrain",
    },
    "P0301": {
        "desc_contains": ["cylinder", "1", "misfire"],
        "system": "Powertrain",
    },
    "P0141": {
        "desc_contains": ["o2", "sensor", "heater", "bank 1", "sensor 2"],  # O2 is oxygen sensor
        "system": "Powertrain",
    },
    "P0161": {
        "desc_contains": ["o2", "sensor", "heater", "bank 2", "sensor 2"],  # O2 is oxygen sensor
        "system": "Powertrain",
    },
}


def validate_code(code: str, expected: dict) -> tuple[bool, str]:
    """
    Validate a single code against expected SAE J2012 definition.

    Returns: (success, message)
    """
    client = get_supabase_client()
    if not client:
        return False, "Supabase client not available"

    result = client.table("obd_codes").select("*").eq("code", code).execute()

    if not result.data:
        return False, f"Code {code} not found in database"

    record = result.data[0]
    description = record.get("description", "").lower()
    system = record.get("system", "")

    # Check system
    if system != expected["system"]:
        return False, f"System mismatch: expected {expected['system']}, got {system}"

    # Check description contains expected keywords
    missing_keywords = []
    for keyword in expected["desc_contains"]:
        if keyword.lower() not in description:
            missing_keywords.append(keyword)

    if missing_keywords:
        return False, f"Description missing keywords: {', '.join(missing_keywords)}"

    return True, f"{code}: {record['description'][:60]}..."


def main():
    print("=" * 80)
    print("OBD-II DTC Import Validation")
    print("=" * 80)
    print()

    if not settings.supabase_enabled:
        print("[ERROR] Supabase is disabled. Enable it in .env")
        return 1

    print(f"[INFO] Supabase URL: {settings.supabase_url}")
    print(f"[INFO] Validating {len(SAE_REFERENCE_CODES)} common codes...")
    print()

    passed = 0
    failed = 0

    for code, expected in SAE_REFERENCE_CODES.items():
        success, message = validate_code(code, expected)

        if success:
            print(f"[PASS] {message}")
            passed += 1
        else:
            print(f"[FAIL] {code}: {message}")
            failed += 1

    # Summary
    print()
    print("=" * 80)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 80)

    if failed == 0:
        print("[SUCCESS] All validation checks passed!")
        return 0
    else:
        print(f"[WARNING] {failed} validation checks failed. Review import data.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
