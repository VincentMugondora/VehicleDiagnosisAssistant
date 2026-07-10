#!/usr/bin/env python3
"""
Apply only the 4 manually approved severity corrections from review queue.

APPROVED:
- P0420: High → Moderate (catalyst efficiency - emissions issue, not immediate danger)
- P0430: High → Moderate (catalyst efficiency bank 2 - same reasoning)
- P0217: High → Critical (engine coolant over-temp - stop immediately)
- P0218: High → Critical (transmission fluid over-temp - stop immediately)

REJECTED (left in review queue):
- P0506: High → Moderate (low idle - needs context)
- P0507: High → Moderate (high idle - needs context)
- P0520: High → Critical (oil pressure SENSOR circuit - sensor may be faulty, not actual pressure)
- C0060: Medium → Critical (ABS motor circuit - loses ABS assist, not total braking)
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(url, key)

# Only the 4 approved corrections
APPROVED_CORRECTIONS = {
    'P0420': {
        'from': 'High',
        'to': 'Moderate',
        'reason': 'Catalyst efficiency below threshold - affects emissions and fuel economy, not immediate engine safety'
    },
    'P0430': {
        'from': 'High',
        'to': 'Moderate',
        'reason': 'Catalyst efficiency below threshold Bank 2 - affects emissions and fuel economy, not immediate engine safety'
    },
    'P0217': {
        'from': 'High',
        'to': 'Critical',
        'reason': 'Engine coolant over-temperature - can rapidly cause severe engine damage, stop driving immediately'
    },
    'P0218': {
        'from': 'High',
        'to': 'Critical',
        'reason': 'Transmission fluid over-temperature - can quickly damage transmission, stop driving immediately'
    }
}

def main():
    print("=" * 80)
    print("APPLYING APPROVED SEVERITY CORRECTIONS")
    print("=" * 80)
    print()
    print("Applying 4 manually approved corrections:")
    for code, correction in APPROVED_CORRECTIONS.items():
        print(f"  {code}: {correction['from']} -> {correction['to']}")
    print()
    print("Leaving in review queue: P0506, P0507, P0520, C0060")
    print()

    applied = 0
    errors = []

    for code, correction in APPROVED_CORRECTIONS.items():
        try:
            # Update the severity
            result = supabase.table('obd_codes').update({
                'severity': correction['to'],
                'severity_explanation': correction['reason']
            }).eq('code', code).execute()

            # Log to audit trail
            supabase.table('enrichment_audit_log').insert({
                'code': code,
                'action': 'severity_correction',
                'actor': 'manual_review_approved',
                'previous_state': correction['from'],
                'new_state': correction['to'],
                'notes': correction['reason'],
                'metadata': {
                    'field': 'severity',
                    'approval_type': 'manual_review'
                }
            }).execute()

            applied += 1
            print(f"+ {code}: {correction['from']} -> {correction['to']}")

        except Exception as e:
            errors.append(f"{code}: {str(e)}")
            print(f"X {code}: ERROR - {str(e)}")

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Applied: {applied}/4")
    print(f"Errors: {len(errors)}")

    if errors:
        print("\nErrors:")
        for error in errors:
            print(f"  - {error}")

    print()
    print("Next steps:")
    print("1. Review remaining 4 codes (P0506, P0507, P0520, C0060) with more context")
    print("2. Implement enhanced severity model with drivability/safety flags")
    print()

if __name__ == '__main__':
    main()
