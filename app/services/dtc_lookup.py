"""
Enhanced DTC lookup service with Supabase integration.

Provides case-insensitive, whitespace-tolerant lookup with fallback support.
"""

import re
from typing import Optional
from supabase import Client

from app.repositories.obd_repository import OBDRepository
from app.repositories.fallback_obd_data import get_fallback_code


def normalize_dtc_code(code: str) -> str:
    """
    Normalize DTC code for lookup.

    - Strip whitespace
    - Convert to uppercase
    - Remove non-alphanumeric characters

    Examples:
        'p0420' -> 'P0420'
        'P 0420' -> 'P0420'
        'p-0420' -> 'P0420'
    """
    return re.sub(r'[^A-Z0-9]', '', code.strip().upper())


def lookup_dtc(code: str, client: Client | None) -> Optional[dict]:
    """
    Lookup OBD-II DTC code in Supabase database.

    Features:
    - Case-insensitive
    - Whitespace-tolerant
    - Automatic normalization
    - Fallback to hardcoded data if Supabase unavailable

    Args:
        code: Raw DTC code (e.g., "P0420", "p 0420", "p-0420")
        client: Supabase client (None to use fallback)

    Returns:
        Dict with code info or None if not found
        {
            "code": str,
            "description": str,
            "system": str,
            "severity": str,
            "symptoms": str | None,
            "common_causes": str | None,
            "generic_fixes": str | None,
            "source": "supabase" | "fallback",
            "confidence": float
        }
    """
    normalized = normalize_dtc_code(code)

    if not normalized:
        return None

    # Use Supabase if available
    if client is not None:
        repo = OBDRepository(client)
        result = repo.get_by_code(normalized)

        if result:
            # Add metadata
            result["source"] = "supabase"
            result["confidence"] = 0.95
            return result

    # Fallback to hardcoded data
    fallback = get_fallback_code(normalized)
    if fallback:
        fallback["source"] = "fallback"
        fallback["confidence"] = 0.90
        return fallback

    return None


def lookup_with_vehicle_context(
    code: str,
    client: Client | None,
    make: Optional[str] = None,
    model: Optional[str] = None,
    year: Optional[str] = None,
    engine: Optional[str] = None
) -> Optional[dict]:
    """
    Lookup DTC code with vehicle-specific overrides.

    1. Lookup base code definition
    2. Check for vehicle-specific override
    3. Merge override data with base data

    Args:
        code: DTC code
        client: Supabase client
        make: Vehicle make (optional)
        model: Vehicle model (optional)
        year: Vehicle year (optional)
        engine: Engine type (optional)

    Returns:
        Enhanced code info with vehicle-specific context
    """
    # Get base definition
    base = lookup_dtc(code, client)

    if not base:
        return None

    # Check for vehicle override if vehicle details provided
    if client and all([make, model, year, engine]):
        repo = OBDRepository(client)
        override = repo.get_vehicle_override(
            code=normalize_dtc_code(code),
            make=make.lower().strip(),
            model=model.lower().strip(),
            year=year.strip(),
            engine=engine.lower().strip()
        )

        if override:
            # Merge override data
            base["source"] = "vehicle_override"
            base["confidence"] = 0.98

            # Merge known_issues into common_causes
            if override.get("known_issues"):
                existing_causes = base.get("common_causes") or ""
                known_issues = ", ".join(override["known_issues"])
                base["common_causes"] = f"{known_issues}, {existing_causes}".strip(", ")

            # Merge priority_checks into generic_fixes
            if override.get("priority_checks"):
                existing_fixes = base.get("generic_fixes") or ""
                priority_checks = ", ".join(override["priority_checks"])
                base["generic_fixes"] = f"{priority_checks}, {existing_fixes}".strip(", ")

    return base


def validate_dtc_format(code: str) -> bool:
    """
    Validate DTC code format.

    Valid formats:
    - Pxxxx (Powertrain)
    - Bxxxx (Body)
    - Cxxxx (Chassis)
    - Uxxxx (Network)

    Where xxxx is 4 digits.

    Args:
        code: Raw code string

    Returns:
        True if valid format, False otherwise
    """
    normalized = normalize_dtc_code(code)
    pattern = r'^[PBCU][0-9]{4}$'
    return bool(re.match(pattern, normalized))


# Backwards compatibility alias
get_dtc_info = lookup_dtc
