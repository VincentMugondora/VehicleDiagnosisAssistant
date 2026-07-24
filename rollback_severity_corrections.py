"""
Rollback Severity Corrections

Uses audit log to restore previous severity values for specified codes.
Supports:
- Rollback by code
- Rollback by date range
- Rollback by confidence threshold
- Dry-run mode
"""

import asyncio
from supabase import create_client
from app.core.config import settings
from datetime import UTC, datetime
import json


async def rollback_severity_corrections(
    codes: list[str] = None,
    after_timestamp: str = None,
    before_timestamp: str = None,
    below_confidence: float = None,
    dry_run: bool = True
):
    """
    Rollback severity corrections using audit log.

    Args:
        codes: Specific codes to rollback (None = all)
        after_timestamp: Only rollback changes after this time
        before_timestamp: Only rollback changes before this time
        below_confidence: Only rollback changes with confidence below this threshold
        dry_run: If True, show what would be rolled back without applying

    Returns:
        Statistics dict
    """
    if not settings.supabase_enabled:
        print("ERROR: Supabase is disabled")
        return

    print("=" * 80)
    print("ROLLBACK SEVERITY CORRECTIONS")
    print("=" * 80)
    print()

    if dry_run:
        print("DRY RUN MODE - No changes will be applied")
        print()

    client = create_client(settings.supabase_url, settings.supabase_service_key)

    # Query audit log for severity updates
    query = client.table('enrichment_audit_log').select('*').eq('action', 'severity_updated')

    if after_timestamp:
        query = query.gte('timestamp', after_timestamp)

    if before_timestamp:
        query = query.lte('timestamp', before_timestamp)

    if codes:
        query = query.in_('code', codes)

    result = query.execute()

    if not result.data:
        print("No severity corrections found in audit log")
        return

    # Filter by confidence if specified
    corrections = result.data
    if below_confidence is not None:
        corrections = [
            c for c in corrections
            if c.get('metadata', {}).get('confidence', 1.0) < below_confidence
        ]

    if not corrections:
        print(f"No corrections found matching criteria")
        return

    print(f"Found {len(corrections)} corrections to rollback:")
    print()

    # Group by code and get most recent correction per code
    corrections_by_code = {}
    for corr in corrections:
        code = corr['code']
        timestamp = corr['timestamp']

        if code not in corrections_by_code:
            corrections_by_code[code] = corr
        else:
            # Keep most recent
            if timestamp > corrections_by_code[code]['timestamp']:
                corrections_by_code[code] = corr

    rollback_list = []

    for code, corr in corrections_by_code.items():
        metadata = corr.get('metadata', {})
        previous = metadata.get('previous')
        current = metadata.get('new')
        confidence = metadata.get('confidence', 0)

        rollback_list.append({
            'code': code,
            'current_severity': current,
            'rollback_to': previous,
            'confidence': confidence,
            'timestamp': corr['timestamp']
        })

    # Show sample
    print("Sample rollbacks (first 10):")
    for item in rollback_list[:10]:
        print(f"  {item['code']:8} {item['current_severity']:10} -> {item['rollback_to']:10} (confidence: {item['confidence']:.0%})")

    if len(rollback_list) > 10:
        print(f"  ... and {len(rollback_list) - 10} more")

    print()

    if dry_run:
        print("DRY RUN - No changes applied")
        print()
        print(f"To execute rollback, run with dry_run=False")
        return {
            'dry_run': True,
            'would_rollback': len(rollback_list),
            'codes': [item['code'] for item in rollback_list]
        }

    # Confirm
    response = input(f"Rollback {len(rollback_list)} codes? (yes/no): ")
    if response.lower() != 'yes':
        print("Cancelled")
        return

    print()
    print("Executing rollback...")

    success_count = 0
    error_count = 0

    for item in rollback_list:
        try:
            client.table('obd_codes').update({
                'severity': item['rollback_to']
            }).eq('code', item['code']).execute()

            success_count += 1

            if success_count % 50 == 0:
                print(f"  Rolled back {success_count}/{len(rollback_list)}...")

        except Exception as e:
            print(f"  ERROR rolling back {item['code']}: {e}")
            error_count += 1

    print()
    print("=" * 80)
    print("ROLLBACK COMPLETE")
    print("=" * 80)
    print(f"Successfully rolled back: {success_count}")
    print(f"Errors: {error_count}")
    print()

    # Log rollback to audit
    for item in rollback_list:
        try:
            client.table('enrichment_audit_log').insert({
                'code': item['code'],
                'timestamp': datetime.utcnow().isoformat(),
                'action': 'severity_rollback',
                'actor': 'rollback_script',
                'previous_state': item['current_severity'],
                'new_state': item['rollback_to'],
                'notes': f"Rolled back severity correction (confidence: {item['confidence']:.0%})",
                'metadata': {'original_timestamp': item['timestamp']}
            }).execute()
        except Exception as e:
            print(f"  WARNING: Could not log rollback for {item['code']}: {e}")

    return {
        'success': success_count,
        'errors': error_count,
        'rolled_back': rollback_list
    }


if __name__ == "__main__":
    import sys

    # Parse command line args
    dry_run = '--execute' not in sys.argv
    codes = None
    after_timestamp = None
    below_confidence = None

    # Example usage:
    # python rollback_severity_corrections.py --execute
    # python rollback_severity_corrections.py --codes P0450,P0442 --execute
    # python rollback_severity_corrections.py --confidence 0.7 --execute

    for i, arg in enumerate(sys.argv):
        if arg == '--codes' and i + 1 < len(sys.argv):
            codes = sys.argv[i + 1].split(',')
        elif arg == '--after' and i + 1 < len(sys.argv):
            after_timestamp = sys.argv[i + 1]
        elif arg == '--confidence' and i + 1 < len(sys.argv):
            below_confidence = float(sys.argv[i + 1])

    print()
    print("Usage:")
    print("  python rollback_severity_corrections.py                    # Dry run (all)")
    print("  python rollback_severity_corrections.py --execute           # Execute rollback")
    print("  python rollback_severity_corrections.py --codes P0450,P0442 --execute")
    print("  python rollback_severity_corrections.py --confidence 0.7 --execute")
    print()

    asyncio.run(rollback_severity_corrections(
        codes=codes,
        after_timestamp=after_timestamp,
        below_confidence=below_confidence,
        dry_run=dry_run
    ))
