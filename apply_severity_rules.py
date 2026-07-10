"""
Apply Deterministic Severity Rules to Database

Replaces AI-inferred severity with expert-defined deterministic rules.
Fixes 989 incorrect severity ratings identified in audit.

Changes:
- Applies severity_rules.py classification to all codes
- Generates severity_explanation for all codes
- Standardizes "Medium" → "Moderate"
- Updates database with correct values
"""

import asyncio
from supabase import create_client
from app.core.config import settings
from severity_rules import classify_severity, get_severity_explanation
import json
from datetime import datetime


async def apply_severity_rules():
    """Apply deterministic severity rules to entire database"""

    if not settings.supabase_enabled:
        print("ERROR: Supabase is disabled")
        return

    print("=" * 80)
    print("APPLY DETERMINISTIC SEVERITY RULES")
    print("=" * 80)
    print()

    client = create_client(settings.supabase_url, settings.supabase_service_key)

    # Fetch all codes
    print("Fetching all codes from database...")
    result = client.table('obd_codes').select('*').execute()

    if not result.data:
        print("ERROR: No data found")
        return

    all_codes = result.data
    total = len(all_codes)
    print(f"Found {total} codes")
    print()

    # Analyze changes needed
    corrections = []
    no_change = []

    for record in all_codes:
        code = record.get('code')
        description = record.get('description', '')
        system = record.get('system', 'Powertrain')
        current_severity = record.get('severity')

        # Classify using deterministic rules
        correct_severity, reasoning = classify_severity(code, description, system)
        correct_explanation = get_severity_explanation(correct_severity, reasoning)

        # Check if change needed
        if current_severity != correct_severity:
            corrections.append({
                'code': code,
                'description': description[:60],
                'current': current_severity,
                'correct': correct_severity,
                'reasoning': reasoning,
                'explanation': correct_explanation
            })
        else:
            # Even if severity is correct, we may need to add explanation
            current_explanation = record.get('severity_explanation')
            if not current_explanation:
                corrections.append({
                    'code': code,
                    'description': description[:60],
                    'current': current_severity,
                    'correct': correct_severity,
                    'reasoning': reasoning,
                    'explanation': correct_explanation
                })
            else:
                no_change.append(code)

    print(f"Codes requiring updates: {len(corrections)}")
    print(f"Codes already correct: {len(no_change)}")
    print()

    if not corrections:
        print("All codes already have correct severity and explanations")
        return

    # Show sample changes
    print("Sample changes (first 15):")
    print()
    for item in corrections[:15]:
        if item['current'] != item['correct']:
            print(f"{item['code']:8} {item['current'] or 'None':10} -> {item['correct']:10}")
            print(f"  {item['description']}...")
            print(f"  Reason: {item['reasoning']}")
        else:
            print(f"{item['code']:8} {item['correct']:10} (adding explanation)")
            print(f"  {item['description']}...")
        print()

    if len(corrections) > 15:
        print(f"... and {len(corrections) - 15} more updates")
    print()

    # Confirm
    print("=" * 80)
    response = input(f"Apply {len(corrections)} severity updates? (yes/no): ")

    if response.lower() != 'yes':
        print("Cancelled")
        return

    print()
    print("Applying updates...")

    # Apply updates
    success_count = 0
    error_count = 0
    updates_log = []

    for i, item in enumerate(corrections, 1):
        try:
            client.table('obd_codes').update({
                'severity': item['correct'],
                'severity_explanation': item['explanation']
            }).eq('code', item['code']).execute()

            success_count += 1
            updates_log.append({
                'code': item['code'],
                'old_severity': item['current'],
                'new_severity': item['correct'],
                'reasoning': item['reasoning']
            })

            if success_count % 100 == 0:
                print(f"  Updated {success_count}/{len(corrections)}...")

        except Exception as e:
            print(f"  ERROR updating {item['code']}: {e}")
            error_count += 1

    print()
    print("=" * 80)
    print("UPDATE COMPLETE")
    print("=" * 80)
    print(f"Successfully updated: {success_count}")
    print(f"Errors: {error_count}")
    print()

    # Export log
    log_data = {
        'timestamp': datetime.now().isoformat(),
        'total_codes': total,
        'updates_applied': success_count,
        'errors': error_count,
        'no_change': len(no_change),
        'updates': updates_log
    }

    with open('severity_updates_log.json', 'w') as f:
        json.dump(log_data, f, indent=2)

    print("Update log exported to: severity_updates_log.json")
    print()

    # Show summary by severity
    print("=" * 80)
    print("SEVERITY DISTRIBUTION (AFTER UPDATE)")
    print("=" * 80)

    result = client.table('obd_codes').select('severity').execute()
    severity_counts = {}
    for record in result.data:
        sev = record.get('severity', 'Unknown')
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    for severity in ['Critical', 'High', 'Moderate', 'Low']:
        count = severity_counts.get(severity, 0)
        percentage = (count / total) * 100
        print(f"{severity:12} {count:5} codes ({percentage:5.1f}%)")

    print()


if __name__ == "__main__":
    asyncio.run(apply_severity_rules())
