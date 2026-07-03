#!/usr/bin/env python3
"""Test the database and enhanced OBD codes"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.db.client import get_supabase_client

def main():
    print("=" * 60)
    print("Database Test - Enhanced OBD Codes")
    print("=" * 60)
    print()

    client = get_supabase_client()
    if not client:
        print("ERROR: Cannot connect to database")
        return 1

    # Test 1: Total count
    print("Test 1: Total Code Count")
    result = client.table('obd_codes').select('code', count='exact').execute()
    total = result.count
    print(f"  Total codes: {total}")
    print()

    # Test 2: Detail coverage
    print("Test 2: Detail Coverage (sampling 500 codes)")
    result = client.table('obd_codes').select('*').limit(500).execute()
    codes = result.data

    with_causes = sum(1 for c in codes if c.get('common_causes'))
    with_symptoms = sum(1 for c in codes if c.get('symptoms'))

    print(f"  With causes: {with_causes}/{len(codes)} ({with_causes*100//len(codes)}%)")
    print(f"  With symptoms: {with_symptoms}/{len(codes)} ({with_symptoms*100//len(codes)}%)")
    print()

    # Test 3: System breakdown
    print("Test 3: System Breakdown")
    result = client.table('obd_codes').select('system').execute()
    systems = {}
    for code in result.data:
        system = code.get('system', 'Unknown')
        systems[system] = systems.get(system, 0) + 1

    for system, count in sorted(systems.items(), key=lambda x: -x[1])[:10]:
        print(f"  {system:<30} {count:>5} codes")
    print()

    # Test 4: Sample codes with details
    print("Test 4: Sample Codes with Detailed Information")
    result = client.table('obd_codes').select('*').not_.is_('common_causes', 'null').limit(5).execute()

    for i, code in enumerate(result.data, 1):
        print(f"\n  {i}. Code: {code['code']}")
        print(f"     Description: {code['description'][:60]}...")
        print(f"     System: {code['system']}")
        print(f"     Severity: {code['severity']}")
        if code.get('common_causes'):
            print(f"     Causes: {code['common_causes'][:60]}...")
        if code.get('symptoms'):
            print(f"     Symptoms: {code['symptoms'][:60]}...")
    print()

    # Test 5: Specific important codes
    print("Test 5: Testing Common Codes")
    test_codes = ['P0100', 'P0171', 'P0300', 'P0420', 'P0442', 'C1201', 'U0100', 'B0001']

    for code in test_codes:
        result = client.table('obd_codes').select('*').eq('code', code).execute()
        if result.data:
            data = result.data[0]
            status = "✅" if data.get('common_causes') or data.get('symptoms') else "⚠️ "
            print(f"  {status} {code}: {data['description'][:50]}...")
        else:
            print(f"  ❌ {code}: NOT FOUND")
    print()

    # Summary
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Database Size: {total} codes")
    print(f"Enhanced Codes: ~{with_causes*total//len(codes)} with causes")
    print(f"Status: {'✅ OPERATIONAL' if total > 1000 else '⚠️  CHECK DATABASE'}")
    print()

    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
