#!/usr/bin/env python3
"""
Import OBD codes from GitHub repository:
https://github.com/mytrile/obd-trouble-codes

This script downloads 3,071 OBD codes and imports them to Supabase.
"""

import sys
import csv
import requests
from pathlib import Path
from io import StringIO

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.client import get_supabase_client
from app.core.config import settings

# GitHub raw CSV URL
CSV_URL = "https://raw.githubusercontent.com/mytrile/obd-trouble-codes/master/obd-trouble-codes.csv"

def detect_system(code: str) -> str:
    """Detect system from OBD code prefix"""
    if not code:
        return "Unknown"

    prefix = code[0].upper()

    if prefix == 'P':
        # Powertrain codes - further classify by second digit
        if len(code) >= 2:
            second = code[1]
            if second in ['0', '2']:
                return "Powertrain (Generic)"
            elif second in ['1', '3']:
                return "Powertrain (Manufacturer)"
        return "Powertrain"
    elif prefix == 'C':
        return "Chassis"
    elif prefix == 'B':
        return "Body"
    elif prefix == 'U':
        return "Network"
    else:
        return "Unknown"

def detect_severity(description: str) -> str:
    """Detect severity from description keywords"""
    desc_lower = description.lower()

    # Critical keywords
    if any(word in desc_lower for word in ['fail', 'failure', 'malfunction', 'not functioning']):
        return "serious"

    # Moderate keywords
    if any(word in desc_lower for word in ['performance', 'range', 'efficiency', 'low', 'high']):
        return "moderate"

    # Minor keywords
    if any(word in desc_lower for word in ['intermittent', 'circuit', 'input', 'sensor']):
        return "minor"

    return "moderate"  # Default

def download_codes():
    """Download codes from GitHub"""
    print(f"Downloading codes from GitHub...")
    print(f"URL: {CSV_URL}")
    print()

    try:
        response = requests.get(CSV_URL, timeout=30)
        response.raise_for_status()

        # Parse CSV
        csv_text = response.text
        csv_file = StringIO(csv_text)
        reader = csv.reader(csv_file)

        codes = {}
        for row in reader:
            if len(row) >= 2:
                code = row[0].strip().upper()
                description = row[1].strip()

                if code and description:
                    codes[code] = {
                        'code': code,
                        'description': description,
                        'system': detect_system(code),
                        'severity': detect_severity(description),
                        'symptoms': None,
                        'common_causes': None,
                        'generic_fixes': None
                    }

        print(f"✅ Downloaded {len(codes)} codes from GitHub")
        return codes

    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to download: {e}")
        return {}
    except Exception as e:
        print(f"❌ Error parsing CSV: {e}")
        return {}

def import_to_supabase(codes: dict, batch_size: int = 100):
    """Import codes to Supabase"""
    print()
    print("=" * 60)
    print("Importing to Supabase...")
    print("=" * 60)
    print()

    client = get_supabase_client()
    if not client:
        print("❌ Cannot connect to Supabase (fallback mode)")
        return 0, 0

    records = list(codes.values())
    total = len(records)
    imported = 0
    errors = 0

    print(f"Total codes to import: {total}")
    print()

    for i in range(0, total, batch_size):
        batch = records[i:i+batch_size]
        batch_num = (i // batch_size) + 1

        try:
            # Use upsert to handle duplicates
            result = client.table("obd_codes").upsert(
                batch,
                on_conflict="code"
            ).execute()

            imported += len(batch)
            print(f"✅ Batch {batch_num}: {len(batch)} codes | Total: {imported}/{total} ({imported*100//total}%)")

        except Exception as e:
            errors += len(batch)
            print(f"❌ Batch {batch_num} failed: {str(e)[:100]}")

    return imported, errors

def main():
    print("=" * 60)
    print("OBD Codes Import from GitHub")
    print("=" * 60)
    print()
    print("Repository: mytrile/obd-trouble-codes")
    print("Expected codes: ~3,071")
    print()

    # Check Supabase connection
    print("Checking Supabase connection...")
    try:
        client = get_supabase_client()
        if not client:
            print("❌ Supabase is in fallback mode")
            print("Please fix Supabase connection first.")
            return 1

        # Test connection
        result = client.table("obd_codes").select("code").limit(1).execute()
        print(f"✅ Connected to Supabase: {settings.supabase_url}")
        print()

    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        print()
        print("Please ensure:")
        print("  1. Tables are created (run migration SQL)")
        print("  2. .env has correct SUPABASE_URL and SUPABASE_SERVICE_KEY")
        return 1

    # Download codes
    codes = download_codes()
    if not codes:
        print("❌ No codes downloaded. Exiting.")
        return 1

    # Show breakdown by system
    print()
    print("Breakdown by system:")
    systems = {}
    for code_data in codes.values():
        system = code_data['system']
        systems[system] = systems.get(system, 0) + 1

    for system, count in sorted(systems.items()):
        print(f"  {system}: {count} codes")

    # Import
    imported, errors = import_to_supabase(codes)

    # Summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Downloaded: {len(codes)} codes")
    print(f"Imported: {imported} codes")
    if errors > 0:
        print(f"Errors: {errors} codes")
    print()

    if imported > 0:
        print("✅ Database is now populated with OBD codes!")
        print()
        print("Verify in Supabase:")
        print("  1. Go to Table Editor")
        print("  2. Click 'obd_codes' table")
        print(f"  3. Should see {imported} rows")
    else:
        print("❌ Import failed. Check errors above.")

    print()
    return 0 if imported > 0 else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Import cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
