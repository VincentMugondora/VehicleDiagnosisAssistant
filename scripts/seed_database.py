"""
Database seeding script - migrates OBD codes from JSON to PostgreSQL.

Usage:
    python scripts/seed_database.py
"""
import json
import os
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.client import get_supabase_client
from app.core.logging import setup_logging, logger


def load_obd_codes_from_json() -> list[dict]:
    """Load OBD codes from JSON file"""
    json_path = Path(__file__).parent.parent / "app" / "data" / "obd_codes.json"

    if not json_path.exists():
        logger.error("obd_codes_json_not_found", path=str(json_path))
        return []

    with open(json_path, "r", encoding="utf-8") as f:
        codes_dict = json.load(f)

    # Convert dict format to list format
    codes = []
    for code, data in codes_dict.items():
        codes.append({
            "code": code,
            "description": data.get("meaning", ""),
            "symptoms": "",  # Not in current JSON
            "common_causes": ", ".join(data.get("generic_causes", [])),
            "generic_fixes": ", ".join(data.get("generic_checks", [])),
            "system": data.get("system", ""),
            "severity": data.get("severity", "")
        })

    logger.info("obd_codes_loaded", count=len(codes))
    return codes


def seed_obd_codes(client, codes: list[dict]):
    """Seed obd_codes table"""
    if not codes:
        logger.warning("no_codes_to_seed")
        return

    # Batch insert
    inserted = 0
    failed = 0
    for code_data in codes:
        try:
            client.table("obd_codes").upsert(
                {
                    "code": code_data["code"].upper(),
                    "description": code_data["description"],
                    "symptoms": code_data["symptoms"],
                    "common_causes": code_data["common_causes"],
                    "generic_fixes": code_data["generic_fixes"],
                    "system": code_data["system"],
                    "severity": code_data["severity"]
                },
                on_conflict="code"
            ).execute()
            inserted += 1
            logger.debug(
                "code_seeded",
                code=code_data["code"]
            )
        except Exception as e:
            failed += 1
            logger.error(
                "seed_failed",
                code=code_data.get("code", "unknown"),
                error=str(e)
            )

    logger.info(
        "obd_codes_seeded",
        inserted=inserted,
        failed=failed,
        total=len(codes)
    )


def main():
    """Main seeding function"""
    setup_logging()

    logger.info("seed_database_start")

    # Get Supabase client
    try:
        client = get_supabase_client()
        logger.info("supabase_connected")
    except Exception as e:
        logger.error("supabase_connection_failed", error=str(e))
        return

    # Load and seed OBD codes
    codes = load_obd_codes_from_json()
    seed_obd_codes(client, codes)

    logger.info("seed_database_complete")


if __name__ == "__main__":
    main()
