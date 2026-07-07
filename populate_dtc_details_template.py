#!/usr/bin/env python3
"""
DTC Details Population Script

Populates repair_steps, parts, common_symptoms, and related_codes tables
with curated data for priority OBD-II codes.

USAGE:
    python populate_dtc_details.py

This script will:
1. Load prepared data for each priority code
2. Insert into Supabase tables
3. Report success/failure for each code
4. Provide row count summary

IMPORTANT: Review all data before running!
"""
import os
from pathlib import Path
from supabase import create_client
from typing import Dict, List

# Load environment variables
env_file = Path(".env")
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

# Initialize Supabase client
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_KEY")

if not url or not key:
    raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env")

client = create_client(url, key)

# ============================================================================
# DATA DEFINITIONS
# ============================================================================
#
# Format for each code:
#
# {
#     'code': 'P0XXX',
#     'common_symptoms': [
#         {'code_id': 'P0XXX', 'symptom_text': 'Description', 'severity': 'high'},
#         ...
#     ],
#     'repair_steps': [
#         {'code_id': 'P0XXX', 'step_number': 1, 'description': 'Step', 'difficulty': 'easy'},
#         ...
#     ],
#     'parts': [
#         {'code_id': 'P0XXX', 'part_name': 'Part Name', 'part_number': None},
#         ...
#     ],
#     'related_codes': [
#         {'code_id': 'P0XXX', 'related_code_id': 'P0YYY', 'relationship_type': 'often_appears_with'},
#         ...
#     ]
# }
#
# ============================================================================

# DATA WILL BE INSERTED HERE BY AGENT RESEARCH
DTC_DATA: List[Dict] = [
    # Example structure (to be replaced with actual data):
    # {
    #     'code': 'P0420',
    #     'common_symptoms': [...],
    #     'repair_steps': [...],
    #     'parts': [...],
    #     'related_codes': [...]
    # },
]


def insert_code_data(code_data: Dict) -> Dict[str, int]:
    """
    Insert all data for a single code.

    Returns:
        Dict with counts per table
    """
    code = code_data['code']
    counts = {
        'symptoms': 0,
        'repair_steps': 0,
        'parts': 0,
        'related_codes': 0
    }

    print(f"\n📝 Inserting data for {code}...")

    # Insert symptoms
    if code_data.get('common_symptoms'):
        try:
            response = client.table('common_symptoms').insert(
                code_data['common_symptoms']
            ).execute()
            counts['symptoms'] = len(response.data) if response.data else 0
            print(f"  ✓ {counts['symptoms']} symptoms")
        except Exception as e:
            print(f"  ✗ Symptoms failed: {e}")

    # Insert repair steps
    if code_data.get('repair_steps'):
        try:
            response = client.table('repair_steps').insert(
                code_data['repair_steps']
            ).execute()
            counts['repair_steps'] = len(response.data) if response.data else 0
            print(f"  ✓ {counts['repair_steps']} repair steps")
        except Exception as e:
            print(f"  ✗ Repair steps failed: {e}")

    # Insert parts
    if code_data.get('parts'):
        try:
            response = client.table('parts').insert(
                code_data['parts']
            ).execute()
            counts['parts'] = len(response.data) if response.data else 0
            print(f"  ✓ {counts['parts']} parts")
        except Exception as e:
            print(f"  ✗ Parts failed: {e}")

    # Insert related codes
    if code_data.get('related_codes'):
        try:
            response = client.table('related_codes').insert(
                code_data['related_codes']
            ).execute()
            counts['related_codes'] = len(response.data) if response.data else 0
            print(f"  ✓ {counts['related_codes']} related codes")
        except Exception as e:
            print(f"  ✗ Related codes failed: {e}")

    return counts


def main():
    """Main population routine"""
    print("=" * 60)
    print("DTC DETAILS POPULATION")
    print("=" * 60)
    print(f"\nCodes to populate: {len(DTC_DATA)}")

    if not DTC_DATA:
        print("\n⚠️  No data to insert - DTC_DATA is empty")
        print("This is a template. Add actual data before running.")
        return

    # Confirm before proceeding
    response = input("\nProceed with insertion? (yes/no): ")
    if response.lower() != 'yes':
        print("Aborted.")
        return

    # Insert all codes
    total_counts = {
        'symptoms': 0,
        'repair_steps': 0,
        'parts': 0,
        'related_codes': 0
    }

    success_codes = []
    failed_codes = []

    for code_data in DTC_DATA:
        code = code_data['code']
        try:
            counts = insert_code_data(code_data)
            success_codes.append(code)

            # Add to totals
            for key, value in counts.items():
                total_counts[key] += value

        except Exception as e:
            print(f"\n✗ {code} FAILED: {e}")
            failed_codes.append(code)

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"\n✓ Successfully populated: {len(success_codes)} codes")
    if failed_codes:
        print(f"✗ Failed: {len(failed_codes)} codes - {', '.join(failed_codes)}")

    print(f"\nTotal rows inserted:")
    print(f"  - Common Symptoms: {total_counts['symptoms']}")
    print(f"  - Repair Steps: {total_counts['repair_steps']}")
    print(f"  - Parts: {total_counts['parts']}")
    print(f"  - Related Codes: {total_counts['related_codes']}")

    print(f"\nGrand Total: {sum(total_counts.values())} rows")
    print("\n✅ Population complete!")


if __name__ == '__main__':
    main()
