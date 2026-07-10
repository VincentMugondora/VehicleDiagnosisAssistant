#!/usr/bin/env python3
"""
Finalize the remaining 4 codes from manual review queue.

Decisions per user review:
- P0506: Leave as High, needs more context
- P0507: Leave as High, needs more context
- P0520: Keep as High (NOT Critical), update explanation to clarify sensor circuit
- C0060: Change to Moderate (NOT Critical), update explanation about normal brakes
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(url, key)

ACTIONS = {
    'P0520': {
        'action': 'update_explanation',
        'severity': 'High',  # Keep current
        'explanation': (
            'Oil pressure sensor circuit fault detected. This is likely a sensor or wiring issue, '
            'not actual low oil pressure. However, you cannot rely on your oil pressure warning '
            'light until this is fixed. Have it diagnosed immediately to confirm actual oil pressure is normal. '
            'Drive to nearest repair facility only - max 50km.'
        )
    },
    'C0060': {
        'action': 'severity_and_explanation',
        'severity': 'Moderate',  # Change from Medium
        'explanation': (
            'Anti-lock brake system has a motor circuit fault. Your regular brakes still work normally, '
            'but ABS may not activate during hard braking. Drive cautiously, especially in wet conditions. '
            'Schedule repair within a week.'
        )
    }
}

def main():
    print("=" * 80)
    print("FINALIZE REVIEW QUEUE - REMAINING CODES")
    print("=" * 80)
    print()
    print("Actions to perform:")
    print("  P0520: Keep High, update explanation (sensor circuit vs actual pressure)")
    print("  C0060: Change Medium -> Moderate, update explanation (normal brakes work)")
    print("  P0506: No action (needs more context)")
    print("  P0507: No action (needs more context)")
    print()

    for code, config in ACTIONS.items():
        try:
            # Get current data
            current = supabase.table('obd_codes').select('*').eq('code', code).execute()
            if not current.data:
                print(f"X {code}: Code not found in database")
                continue

            old_severity = current.data[0].get('severity', 'Unknown')

            # Update
            supabase.table('obd_codes').update({
                'severity': config['severity'],
                'severity_explanation': config['explanation']
            }).eq('code', code).execute()

            # Log to audit
            supabase.table('enrichment_audit_log').insert({
                'code': code,
                'action': f'severity_review_{config["action"]}',
                'actor': 'manual_review_finalized',
                'previous_state': old_severity,
                'new_state': config['severity'],
                'notes': config['explanation'],
                'metadata': {
                    'review_date': '2026-07-10',
                    'decision': config['action']
                }
            }).execute()

            if config['action'] == 'severity_and_explanation':
                print(f"+ {code}: {old_severity} -> {config['severity']}")
            else:
                print(f"+ {code}: Updated explanation (severity unchanged)")

        except Exception as e:
            print(f"X {code}: ERROR - {str(e)}")

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("Completed: 2 codes updated (P0520, C0060)")
    print("Deferred: 2 codes (P0506, P0507) - need additional context")
    print()
    print("Next step: Implement enhanced severity metadata model")
    print()

if __name__ == '__main__':
    main()
