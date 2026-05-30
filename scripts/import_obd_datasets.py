"""
Import OBD-II codes from multiple open-source datasets into Supabase.

This script downloads and imports OBD codes from:
1. Local comprehensive dataset (300+ codes)
2. OBDb (github.com/OBDb) - Community-maintained DTC database (optional)
3. Auto-codes datasets (optional)

Usage:
    python scripts/import_obd_datasets.py
"""

import json
import requests
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.client import get_supabase_client
from app.core.config import settings

# Import our comprehensive local dataset
try:
    from scripts.comprehensive_obd_codes import ALL_CODES
    print(f"✅ Loaded {len(ALL_CODES)} codes from local comprehensive dataset")
except ImportError:
    print("⚠️  Could not import comprehensive_obd_codes.py")
    ALL_CODES = {}

# GitHub raw URLs for open-source OBD datasets (optional additional sources)
DATASETS = {
    "generic_powertrain": "https://raw.githubusercontent.com/OBDb/OBDb/main/data/generic/powertrain.json",
    "generic_chassis": "https://raw.githubusercontent.com/OBDb/OBDb/main/data/generic/chassis.json",
    "generic_body": "https://raw.githubusercontent.com/OBDb/OBDb/main/data/generic/body.json",
    "generic_network": "https://raw.githubusercontent.com/OBDb/OBDb/main/data/generic/network.json",
}


def download_dataset(name: str, url: str) -> dict | None:
    """Download a dataset from URL"""
    print(f"📥 Downloading {name}...")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        print(f"✅ Downloaded {name}: {len(data)} codes")
        return data
    except requests.exceptions.RequestException as e:
        print(f"⚠️  Failed to download {name}: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"⚠️  Failed to parse {name}: {e}")
        return None


def normalize_code_data(code: str, data: dict, system: str = "Powertrain") -> dict:
    """Normalize different dataset formats to our schema"""
    # Handle different field names from various datasets
    description = (
        data.get("description") or
        data.get("meaning") or
        data.get("title") or
        data.get("name") or
        ""
    )

    symptoms = (
        data.get("symptoms") or
        data.get("symptom") or
        ""
    )

    # Combine causes from different possible fields
    causes_list = []
    if data.get("common_causes"):
        causes_list.append(data["common_causes"])
    if data.get("causes"):
        if isinstance(data["causes"], list):
            causes_list.extend(data["causes"])
        else:
            causes_list.append(str(data["causes"]))
    if data.get("possible_causes"):
        if isinstance(data["possible_causes"], list):
            causes_list.extend(data["possible_causes"])
        else:
            causes_list.append(str(data["possible_causes"]))

    common_causes = ", ".join(filter(None, causes_list)) if causes_list else ""

    # Combine fixes from different possible fields
    fixes_list = []
    if data.get("generic_fixes"):
        fixes_list.append(data["generic_fixes"])
    if data.get("fixes"):
        if isinstance(data["fixes"], list):
            fixes_list.extend(data["fixes"])
        else:
            fixes_list.append(str(data["fixes"]))
    if data.get("solutions"):
        if isinstance(data["solutions"], list):
            fixes_list.extend(data["solutions"])
        else:
            fixes_list.append(str(data["solutions"]))

    generic_fixes = ", ".join(filter(None, fixes_list)) if fixes_list else ""

    severity = (
        data.get("severity") or
        data.get("priority") or
        "Medium"
    )

    return {
        "code": code.upper(),
        "description": description,
        "symptoms": symptoms,
        "common_causes": common_causes,
        "generic_fixes": generic_fixes,
        "system": data.get("system") or system,
        "severity": severity
    }


def import_codes_to_supabase(codes_dict: dict, batch_size: int = 100):
    """Import codes to Supabase in batches"""
    client = get_supabase_client()

    # Convert to list of normalized records
    records = []
    for code, data in codes_dict.items():
        try:
            normalized = normalize_code_data(code, data)
            records.append(normalized)
        except Exception as e:
            print(f"⚠️  Skipping {code}: {e}")

    print(f"\n📊 Total codes to import: {len(records)}")

    # Import in batches
    imported = 0
    skipped = 0

    for i in range(0, len(records), batch_size):
        batch = records[i:i+batch_size]
        try:
            # Use upsert to handle duplicates
            response = client.table("obd_codes").upsert(
                batch,
                on_conflict="code"
            ).execute()

            imported += len(batch)
            print(f"✅ Imported batch {i//batch_size + 1}: {len(batch)} codes (Total: {imported})")
        except Exception as e:
            print(f"❌ Failed to import batch {i//batch_size + 1}: {e}")
            skipped += len(batch)

    print(f"\n🎉 Import complete!")
    print(f"   ✅ Imported: {imported}")
    if skipped > 0:
        print(f"   ⚠️  Skipped: {skipped}")

    return imported, skipped


def main():
    """Main import process"""
    print("=" * 60)
    print("🚗 OBD-II Code Dataset Importer")
    print("=" * 60)
    print()

    # Check Supabase connection
    print("🔌 Checking Supabase connection...")
    try:
        client = get_supabase_client()
        # Test connection
        result = client.table("obd_codes").select("code").limit(1).execute()
        print(f"✅ Connected to Supabase: {settings.supabase_url}")
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")
        print("\nPlease check your .env file:")
        print("  SUPABASE_URL=your-project-url")
        print("  SUPABASE_SERVICE_KEY=your-service-key")
        return 1

    print()

    # Start with local comprehensive dataset
    all_codes = dict(ALL_CODES) if ALL_CODES else {}
    print(f"📦 Starting with {len(all_codes)} codes from local dataset")

    # Optionally download additional datasets from GitHub
    print("\n📥 Attempting to download additional datasets from GitHub...")
    for name, url in DATASETS.items():
        dataset = download_dataset(name, url)
        if dataset:
            # Handle different dataset formats
            if isinstance(dataset, dict):
                # Merge, preferring local dataset for conflicts
                for code, data in dataset.items():
                    if code not in all_codes:
                        all_codes[code] = data
            elif isinstance(dataset, list):
                # Convert list format to dict
                for item in dataset:
                    if isinstance(item, dict) and "code" in item:
                        code = item.pop("code")
                        if code not in all_codes:
                            all_codes[code] = item

    print(f"\n📦 Total unique codes collected: {len(all_codes)}")

    # Import to Supabase
    print("\n" + "=" * 60)
    print("📤 Importing to Supabase...")
    print("=" * 60)
    print()

    imported, skipped = import_codes_to_supabase(all_codes)

    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    print(f"Total codes collected: {len(all_codes)}")
    print(f"Successfully imported: {imported}")
    if skipped > 0:
        print(f"Skipped (errors): {skipped}")
    print()
    print("✅ Your database is now populated with OBD-II codes!")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
