#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multi-Source OBD Code Importer

Combines data from:
1. GitHub mytrile/obd-trouble-codes (3,071 codes - base)
2. python-OBD library codes (structured, community-vetted)
3. Existing fallback codes (detailed descriptions)

Creates the most comprehensive OBD code database possible.
"""

import sys
import io
import csv
import re
import requests
from pathlib import Path
from io import StringIO

# Fix Windows encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.client import get_supabase_client
from app.core.config import settings

# Data sources
GITHUB_CSV_URL = "https://raw.githubusercontent.com/mytrile/obd-trouble-codes/master/obd-trouble-codes.csv"
PYTHON_OBD_URL = "https://raw.githubusercontent.com/brendan-w/python-OBD/master/obd/codes.py"

def detect_system(code: str) -> str:
    """Detect system from OBD code"""
    if not code or len(code) < 2:
        return "Unknown"

    prefix = code[0].upper()
    second = code[1] if len(code) > 1 else '0'

    if prefix == 'P':
        if second in ['0', '2']:
            return "Powertrain"
        return "Powertrain (Manufacturer)"
    elif prefix == 'C':
        return "Chassis"
    elif prefix == 'B':
        return "Body"
    elif prefix == 'U':
        return "Network"
    return "Unknown"

def detect_severity(description: str) -> str:
    """Detect severity from description"""
    desc_lower = description.lower()

    critical_words = ['fail', 'failure', 'malfunction', 'not functioning', 'overspeed', 'overheat']
    serious_words = ['performance', 'range', 'efficiency', 'low', 'high', 'circuit']
    minor_words = ['intermittent', 'sensor', 'input', 'signal']

    if any(w in desc_lower for w in critical_words):
        return "serious"
    if any(w in desc_lower for w in serious_words):
        return "moderate"
    if any(w in desc_lower for w in minor_words):
        return "minor"

    return "moderate"

def extract_causes_symptoms(description: str) -> tuple:
    """Extract possible causes and symptoms from description"""
    # This is heuristic-based; improve as needed
    causes = []
    symptoms = []

    desc_lower = description.lower()

    # Common patterns
    if 'circuit' in desc_lower:
        if 'open' in desc_lower:
            causes.append("Open circuit (broken wire or connector)")
        if 'short' in desc_lower:
            causes.append("Short circuit (wire touching ground/power)")
        if 'low' in desc_lower:
            causes.append("Low voltage or weak signal")
        if 'high' in desc_lower:
            causes.append("High voltage or excessive signal")

    if 'sensor' in desc_lower or 'heater' in desc_lower:
        causes.append("Faulty sensor or component")
        causes.append("Wiring or connector issue")

    if 'performance' in desc_lower or 'range' in desc_lower:
        causes.append("Component operating outside normal range")
        symptoms.append("Performance issues")

    if 'malfunction' in desc_lower or 'failure' in desc_lower:
        symptoms.append("Check engine light on")
        causes.append("Component failure")

    return (", ".join(causes) if causes else None,
            ", ".join(symptoms) if symptoms else None)

def download_github_codes():
    """Download codes from mytrile GitHub repo"""
    print("1. Downloading from GitHub (mytrile/obd-trouble-codes)...")
    try:
        response = requests.get(GITHUB_CSV_URL, timeout=30)
        response.raise_for_status()

        csv_file = StringIO(response.text)
        reader = csv.reader(csv_file)

        codes = {}
        for row in reader:
            if len(row) >= 2:
                code = row[0].strip().upper()
                description = row[1].strip()

                if code and description:
                    causes, symptoms = extract_causes_symptoms(description)

                    codes[code] = {
                        'code': code,
                        'description': description,
                        'system': detect_system(code),
                        'severity': detect_severity(description),
                        'common_causes': causes,
                        'symptoms': symptoms,
                        'generic_fixes': None,
                        'source': 'github'
                    }

        print(f"   ✅ Downloaded {len(codes)} codes from GitHub")
        return codes
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return {}

def download_python_obd_codes():
    """Download codes from python-OBD library"""
    print("2. Downloading from python-OBD library...")
    try:
        response = requests.get(PYTHON_OBD_URL, timeout=30)
        response.raise_for_status()

        content = response.text

        # Parse Python dictionary from the file
        # Extract DTC = { ... } section
        dtc_match = re.search(r'DTC\s*=\s*\{([^}]+)\}', content, re.DOTALL)
        if not dtc_match:
            print("   ⚠️  Could not parse DTC dictionary")
            return {}

        dtc_content = dtc_match.group(1)

        # Parse entries like "P0001": "Description",
        codes = {}
        pattern = r'"([PCBU]\d{4})"\s*:\s*"([^"]+)"'
        matches = re.findall(pattern, dtc_content)

        for code, description in matches:
            causes, symptoms = extract_causes_symptoms(description)

            codes[code] = {
                'code': code,
                'description': description,
                'system': detect_system(code),
                'severity': detect_severity(description),
                'common_causes': causes,
                'symptoms': symptoms,
                'generic_fixes': None,
                'source': 'python-obd'
            }

        print(f"   ✅ Downloaded {len(codes)} codes from python-OBD")
        return codes
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return {}

def load_fallback_codes():
    """Load detailed codes from our fallback data"""
    print("3. Loading detailed fallback codes...")
    try:
        from app.repositories.fallback_obd_data import FALLBACK_OBD_CODES

        codes = {}
        for code, data in FALLBACK_OBD_CODES.items():
            # Convert our detailed format to import format
            causes = ", ".join(data.get('causes', []))
            symptoms = ", ".join(data.get('symptoms', []))

            codes[code] = {
                'code': code,
                'description': data.get('name') or data.get('description', ''),
                'system': data.get('system', detect_system(code)),
                'severity': data.get('severity', 'moderate'),
                'common_causes': causes if causes else None,
                'symptoms': symptoms if symptoms else None,
                'generic_fixes': None,
                'source': 'fallback'
            }

        print(f"   ✅ Loaded {len(codes)} detailed fallback codes")
        return codes
    except Exception as e:
        print(f"   ⚠️  Could not load fallback: {e}")
        return {}

def merge_sources(sources: list) -> dict:
    """Merge multiple code sources, preferring more detailed data"""
    print("\n4. Merging data sources...")

    merged = {}

    # Priority: fallback (most detailed) > python-obd > github
    for source_codes in reversed(sources):
        for code, data in source_codes.items():
            if code not in merged:
                merged[code] = data
            else:
                # Merge: prefer non-null values from more detailed source
                existing = merged[code]

                # Keep longer/better description
                if len(data['description']) > len(existing['description']):
                    existing['description'] = data['description']

                # Keep more detailed causes/symptoms
                if data['common_causes'] and not existing['common_causes']:
                    existing['common_causes'] = data['common_causes']
                if data['symptoms'] and not existing['symptoms']:
                    existing['symptoms'] = data['symptoms']

                # Track sources
                if 'sources' not in existing:
                    existing['sources'] = [existing.get('source', 'unknown')]
                existing['sources'].append(data['source'])

    # Clean up
    for code, data in merged.items():
        if 'sources' in data:
            data.pop('source', None)
            data['sources'] = ', '.join(set(data['sources']))
        else:
            data.pop('source', None)

    print(f"   ✅ Merged into {len(merged)} unique codes")
    return merged

def show_statistics(codes: dict):
    """Show statistics about the dataset"""
    print("\n" + "=" * 60)
    print("Dataset Statistics")
    print("=" * 60)

    systems = {}
    severities = {}

    for data in codes.values():
        system = data['system']
        severity = data['severity']

        systems[system] = systems.get(system, 0) + 1
        severities[severity] = severities.get(severity, 0) + 1

    print("\nBy System:")
    for system, count in sorted(systems.items(), key=lambda x: -x[1]):
        print(f"  {system:<30} {count:>5} codes")

    print("\nBy Severity:")
    for severity, count in sorted(severities.items(), key=lambda x: -x[1]):
        print(f"  {severity:<30} {count:>5} codes")

    # Count codes with detailed info
    with_causes = sum(1 for d in codes.values() if d['common_causes'])
    with_symptoms = sum(1 for d in codes.values() if d['symptoms'])

    print("\nDetail Coverage:")
    print(f"  With causes:    {with_causes:>5} ({with_causes*100//len(codes)}%)")
    print(f"  With symptoms:  {with_symptoms:>5} ({with_symptoms*100//len(codes)}%)")

    print(f"\nTotal unique codes: {len(codes)}")

def import_to_supabase(codes: dict, batch_size: int = 100):
    """Import merged codes to Supabase"""
    print("\n" + "=" * 60)
    print("Importing to Supabase")
    print("=" * 60)

    client = get_supabase_client()
    if not client:
        print("❌ Cannot connect to Supabase")
        return 0, 0

    records = list(codes.values())
    total = len(records)
    imported = 0
    errors = 0

    print(f"\nImporting {total} codes in batches of {batch_size}...")
    print()

    for i in range(0, total, batch_size):
        batch = records[i:i+batch_size]
        batch_num = (i // batch_size) + 1

        try:
            result = client.table("obd_codes").upsert(
                batch,
                on_conflict="code"
            ).execute()

            imported += len(batch)
            percentage = (imported * 100) // total
            print(f"✅ Batch {batch_num}: {len(batch)} codes | Total: {imported}/{total} ({percentage}%)")

        except Exception as e:
            errors += len(batch)
            print(f"❌ Batch {batch_num} failed: {str(e)[:100]}")

    return imported, errors

def main():
    print("=" * 60)
    print("Multi-Source OBD Code Importer")
    print("=" * 60)
    print()
    print("Sources:")
    print("  1. GitHub mytrile/obd-trouble-codes")
    print("  2. python-OBD library (community-vetted)")
    print("  3. Detailed fallback codes")
    print()

    # Check Supabase
    print("Checking Supabase connection...")
    try:
        client = get_supabase_client()
        if not client:
            print("❌ Supabase in fallback mode")
            return 1

        client.table("obd_codes").select("code").limit(1).execute()
        print(f"✅ Connected: {settings.supabase_url}")
        print()
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return 1

    # Download from all sources
    print("=" * 60)
    print("Downloading from Sources")
    print("=" * 60)
    print()

    github_codes = download_github_codes()
    python_obd_codes = download_python_obd_codes()
    fallback_codes = load_fallback_codes()

    # Merge
    merged_codes = merge_sources([github_codes, python_obd_codes, fallback_codes])

    if not merged_codes:
        print("\n❌ No codes to import")
        return 1

    # Statistics
    show_statistics(merged_codes)

    # Import
    imported, errors = import_to_supabase(merged_codes)

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total unique codes: {len(merged_codes)}")
    print(f"Imported:          {imported}")
    if errors > 0:
        print(f"Errors:            {errors}")
    print()

    if imported > 0:
        print("✅ Database populated with multi-source OBD codes!")
        print()
        print("Next: Restart backend and test via WhatsApp")
    else:
        print("❌ Import failed")

    return 0 if imported > 0 else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
