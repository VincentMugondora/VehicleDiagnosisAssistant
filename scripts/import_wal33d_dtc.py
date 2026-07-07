#!/usr/bin/env python3
"""
Import OBD-II DTC codes from Wal33D dtc-database into Supabase.

This script:
1. Downloads/clones the Wal33D dtc-database repository
2. Extracts generic SAE J2012 codes (is_generic=1, manufacturer='GENERIC')
3. Transforms them to match our obd_codes schema
4. Upserts them into Supabase

Source: https://github.com/Wal33D/dtc-database
License: MIT
"""

import os
import sys
import sqlite3
import tempfile
import subprocess
from pathlib import Path
from typing import Generator

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.client import get_supabase_client
from app.core.config import settings


# System mapping
SYSTEM_MAP = {
    "P": "Powertrain",
    "B": "Body",
    "C": "Chassis",
    "U": "Network"
}

# Severity heuristics (can be refined later)
SEVERITY_MAP = {
    "P0": "High",      # Powertrain generic
    "P1": "Medium",    # Powertrain manufacturer
    "B": "Low",        # Body
    "C": "Medium",     # Chassis
    "U": "Medium"      # Network
}


def get_severity(code: str) -> str:
    """Determine severity based on code prefix."""
    for prefix, severity in SEVERITY_MAP.items():
        if code.startswith(prefix):
            return severity
    return "Medium"


def clone_or_copy_dtc_database() -> Path:
    """
    Clone Wal33D dtc-database repo to temp directory.
    Returns path to dtc_codes.db file.
    """
    print("📥 Fetching Wal33D dtc-database...")

    # Check if we already have it locally
    local_path = Path(__file__).parent.parent / "data" / "dtc-database"
    if local_path.exists() and (local_path / "data" / "dtc_codes.db").exists():
        print(f"✅ Using existing local copy: {local_path}")
        return local_path / "data" / "dtc_codes.db"

    # Clone to temp directory
    temp_dir = Path(tempfile.gettempdir()) / "dtc-database"

    if temp_dir.exists():
        print(f"🔄 Updating existing clone at {temp_dir}...")
        try:
            subprocess.run(
                ["git", "-C", str(temp_dir), "pull"],
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError:
            print("⚠️  Git pull failed, using existing copy")
    else:
        print(f"📦 Cloning to {temp_dir}...")
        subprocess.run(
            ["git", "clone", "--depth", "1",
             "https://github.com/Wal33D/dtc-database.git",
             str(temp_dir)],
            check=True,
            capture_output=True
        )

    db_path = temp_dir / "data" / "dtc_codes.db"
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found at {db_path}")

    print(f"✅ Database ready: {db_path}")
    return db_path


def extract_generic_codes(db_path: Path) -> Generator[dict, None, None]:
    """
    Extract generic SAE J2012 codes from Wal33D database.

    Yields dict with: code, description, type, manufacturer, is_generic
    """
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = """
        SELECT code, description, type, manufacturer, is_generic
        FROM dtc_definitions
        WHERE is_generic = 1 AND manufacturer = 'GENERIC'
        ORDER BY code
    """

    cursor.execute(query)

    for row in cursor:
        yield dict(row)

    conn.close()


def transform_to_obd_codes_schema(raw_code: dict) -> dict:
    """
    Transform Wal33D code to our obd_codes schema.

    Input: {code, description, type, manufacturer, is_generic}
    Output: {code, description, system, severity, symptoms, common_causes, generic_fixes}
    """
    code = raw_code["code"].upper()

    return {
        "code": code,
        "description": raw_code["description"],
        "system": SYSTEM_MAP.get(raw_code["type"], "Unknown"),
        "severity": get_severity(code),
        "symptoms": None,          # To be enriched later
        "common_causes": None,     # To be enriched later
        "generic_fixes": None,     # To be enriched later
    }


def batch_upsert_to_supabase(codes: list[dict], batch_size: int = 100) -> int:
    """
    Upsert codes to Supabase in batches.
    Returns count of codes processed.
    """
    client = get_supabase_client()
    if not client:
        raise RuntimeError("Supabase client not available. Check SUPABASE_URL and SUPABASE_SERVICE_KEY.")

    total = len(codes)
    inserted = 0

    for i in range(0, total, batch_size):
        batch = codes[i:i + batch_size]

        try:
            result = client.table("obd_codes").upsert(
                batch,
                on_conflict="code"
            ).execute()

            inserted += len(batch)
            print(f"📝 Inserted batch {i // batch_size + 1}: {len(batch)} codes ({inserted}/{total})")

        except Exception as e:
            print(f"❌ Error inserting batch {i // batch_size + 1}: {e}")
            # Continue with next batch

    return inserted


def validate_sample_codes(codes: list[dict]) -> None:
    """
    Validate a sample of commonly-searched codes against expected definitions.
    """
    print("\n🔍 Validating sample codes...")

    expected = {
        "P0300": "Random/Multiple Cylinder Misfire Detected",
        "P0420": "Catalyst System Efficiency Below Threshold",
        "P0171": "System Too Lean",
        "P0455": "EVAP System Leak Detected",
        "P0128": "Coolant Thermostat",
    }

    code_map = {c["code"]: c for c in codes}

    for code, expected_desc_fragment in expected.items():
        if code in code_map:
            actual = code_map[code]["description"]
            if expected_desc_fragment.lower() in actual.lower():
                print(f"✅ {code}: {actual[:60]}...")
            else:
                print(f"⚠️  {code}: Expected '{expected_desc_fragment}', got '{actual}'")
        else:
            print(f"❌ {code}: NOT FOUND")


def main():
    """Main import workflow."""
    print("=" * 80)
    print("OBD-II DTC Database Import Script")
    print("Source: Wal33D/dtc-database (MIT License)")
    print("=" * 80)
    print()

    # Check for --yes flag to skip confirmation
    auto_confirm = "--yes" in sys.argv or "-y" in sys.argv

    # Check Supabase config
    if not settings.supabase_enabled:
        print("❌ Supabase is disabled. Enable it in .env:")
        print("   SUPABASE_ENABLED=true")
        print("   SUPABASE_URL=your-url")
        print("   SUPABASE_SERVICE_KEY=your-key")
        return 1

    print(f"🔗 Supabase URL: {settings.supabase_url}")
    print()

    try:
        # Step 1: Get database
        db_path = clone_or_copy_dtc_database()

        # Step 2: Extract generic codes
        print("\n📊 Extracting generic SAE J2012 codes...")
        raw_codes = list(extract_generic_codes(db_path))
        print(f"✅ Extracted {len(raw_codes)} generic codes")

        # Step 3: Transform
        print("\n🔄 Transforming to obd_codes schema...")
        transformed = [transform_to_obd_codes_schema(code) for code in raw_codes]

        # Step 4: Validate sample
        validate_sample_codes(transformed)

        # Step 5: Confirm before uploading
        print(f"\n📤 Ready to upload {len(transformed)} codes to Supabase.")

        if auto_confirm:
            print("✅ Auto-confirmed (--yes flag)")
            confirm = "y"
        else:
            confirm = input("Continue? [y/N]: ").strip().lower()

        if confirm != "y":
            print("❌ Import cancelled.")
            return 0

        # Step 6: Upsert to Supabase
        print("\n📥 Uploading to Supabase...")
        inserted = batch_upsert_to_supabase(transformed, batch_size=100)

        # Step 7: Summary
        print("\n" + "=" * 80)
        print("✅ Import Complete!")
        print("=" * 80)
        print(f"Total codes processed: {inserted}")
        print(f"Database: {settings.supabase_url}")
        print(f"Table: obd_codes")
        print()
        print("Next steps:")
        print("1. Verify codes in Supabase dashboard")
        print("2. Run validation tests: python scripts/validate_dtc_import.py")
        print("3. Test lookup in webhook: send 'P0420' via WhatsApp")
        print()

        return 0

    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
