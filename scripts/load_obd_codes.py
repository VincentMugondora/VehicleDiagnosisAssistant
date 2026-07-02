#!/usr/bin/env python3
"""
Load OBD-II codes from JSON dataset into Supabase database.

Usage:
    python scripts/load_obd_codes.py
"""
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from app.db.client import get_supabase_client
from app.core.logging import logger


def load_obd_codes():
    """Load OBD codes from JSON file into database"""

    # Load JSON data
    json_path = Path(__file__).parent.parent / "data" / "obd_codes_dataset.json"

    print(f"Loading OBD codes from: {json_path}")

    with open(json_path, 'r') as f:
        data = json.load(f)

    codes = data['codes']
    total = len(codes)

    print(f"Found {total} codes to load")
    print(f"Dataset version: {data['metadata']['version']}")
    print()

    # Connect to Supabase
    client = get_supabase_client()

    # Insert codes in batches
    batch_size = 50
    inserted = 0
    updated = 0
    errors = 0

    for i in range(0, total, batch_size):
        batch = codes[i:i + batch_size]

        try:
            # Prepare batch for upsert
            batch_data = []
            for code_info in batch:
                batch_data.append({
                    "code": code_info["code"],
                    "description": code_info["description"],
                    "system": code_info["system"],
                    "severity": code_info["severity"],
                    "symptoms": code_info.get("symptoms", ""),
                    "common_causes": code_info.get("common_causes", ""),
                    "generic_fixes": code_info.get("generic_fixes", "")
                })

            # Use upsert to handle duplicates
            result = client.table("obd_codes").upsert(
                batch_data,
                on_conflict="code"
            ).execute()

            batch_count = len(result.data) if result.data else 0
            inserted += batch_count

            # Progress indicator
            progress = min(i + batch_size, total)
            print(f"Progress: {progress}/{total} codes processed ({progress*100//total}%)")

        except Exception as e:
            print(f"Error inserting batch {i//batch_size + 1}: {str(e)}")
            errors += 1
            continue

    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total codes in dataset: {total}")
    print(f"Successfully inserted/updated: {inserted}")
    print(f"Errors: {errors}")
    print()

    if errors == 0:
        print("[SUCCESS] All codes loaded successfully!")
    else:
        print(f"[WARNING] Completed with {errors} errors")

    # Verify count in database
    try:
        count_result = client.table("obd_codes").select("code", count="exact").execute()
        db_count = count_result.count
        print(f"\nDatabase now contains {db_count} OBD codes")
    except Exception as e:
        print(f"\n⚠️  Could not verify database count: {str(e)}")


def show_sample():
    """Show sample of loaded codes"""
    try:
        client = get_supabase_client()
        result = client.table("obd_codes").select("code, description").limit(10).execute()

        if result.data:
            print("\nSample codes in database:")
            print("-" * 60)
            for code in result.data:
                print(f"{code['code']}: {code['description'][:50]}...")

    except Exception as e:
        print(f"Error retrieving sample: {str(e)}")


if __name__ == "__main__":
    print("=" * 60)
    print("OBD-II Code Loader")
    print("=" * 60)
    print()

    try:
        load_obd_codes()
        show_sample()

        print("\n" + "=" * 60)
        print("[COMPLETE] Load successful!")
        print("=" * 60)
        print("\nYou can now test the system with:")
        print("  python test_system_e2e.py")
        print("\nOr test via WhatsApp:")
        print("  Send: P0420 Toyota Camry 2015")

    except KeyboardInterrupt:
        print("\n\n[WARNING] Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
