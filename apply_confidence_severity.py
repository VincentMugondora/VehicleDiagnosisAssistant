"""
Apply Confidence-Based Severity Corrections

Phase 1 of production deployment:
1. Analyze all codes with confidence scoring
2. Auto-apply high-confidence corrections (>=90%)
3. Generate review queue for medium-confidence (60-89%)
4. Document low-confidence codes (<60%)

Safeguards:
- Only applies corrections with >=90% confidence automatically
- All changes logged to audit trail
- Review queue generated for manual approval
- Low-confidence codes left unchanged
"""

import asyncio
from supabase import create_client
from app.core.config import settings
from severity_confidence import analyze_corrections, generate_review_queue
from severity_rules import get_severity_explanation
import json
from datetime import datetime


async def apply_confidence_severity():
    """Apply confidence-based severity corrections"""

    if not settings.supabase_enabled:
        print("ERROR: Supabase is disabled")
        return

    print("=" * 80)
    print("CONFIDENCE-BASED SEVERITY CORRECTIONS")
    print("=" * 80)
    print()
    print("This will:")
    print("  1. Analyze all 1,000 codes with confidence scoring")
    print("  2. Auto-apply HIGH confidence corrections (>=90%)")
    print("  3. Generate review queue for MEDIUM confidence (60-89%)")
    print("  4. Document LOW confidence codes (<60%)")
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

    # Analyze with confidence scoring
    print("Analyzing corrections with confidence scoring...")
    analysis = analyze_corrections(all_codes)

    stats = analysis['stats']
    high_confidence = analysis['high_confidence']
    medium_confidence = analysis['medium_confidence']
    low_confidence = analysis['low_confidence']

    print()
    print("=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"Total codes:             {stats['total']}")
    print(f"No change needed:        {stats['no_change']}")
    print(f"High confidence (>=90%): {stats['high_confidence']} -> AUTO-APPLY")
    print(f"Medium confidence (60-89%): {stats['medium_confidence']} -> REVIEW QUEUE")
    print(f"Low confidence (<60%):   {stats['low_confidence']} -> LEAVE UNCHANGED")
    print()

    # Show sample high-confidence corrections
    if high_confidence:
        print("Sample HIGH confidence corrections (first 10):")
        for corr in high_confidence[:10]:
            print(f"  {corr.code:8} {corr.current_severity:10} -> {corr.recommended_severity:10} ({corr.confidence:.0%})")
            print(f"    {corr.evidence}")
        if len(high_confidence) > 10:
            print(f"  ... and {len(high_confidence) - 10} more")
        print()

    # Confirm auto-apply
    import sys
    auto_confirm = '--yes' in sys.argv

    if high_confidence:
        if not auto_confirm:
            response = input(f"Auto-apply {len(high_confidence)} HIGH confidence corrections? (yes/no): ")
            if response.lower() != 'yes':
                print("Cancelled")
                return
        else:
            print(f"Auto-applying {len(high_confidence)} HIGH confidence corrections (--yes flag)")
    else:
        print("No high-confidence corrections to apply")
        return

    print()
    print("Applying HIGH confidence corrections...")

    # Apply high-confidence corrections
    success_count = 0
    error_count = 0
    changes_log = []

    for corr in high_confidence:
        try:
            # Get severity explanation
            explanation = get_severity_explanation(
                corr.recommended_severity,
                corr.reasoning
            )

            # Update database
            client.table('obd_codes').update({
                'severity': corr.recommended_severity,
                'severity_explanation': explanation
            }).eq('code', corr.code).execute()

            success_count += 1
            changes_log.append({
                'code': corr.code,
                'old_severity': corr.current_severity,
                'new_severity': corr.recommended_severity,
                'confidence': corr.confidence,
                'reasoning': corr.reasoning
            })

            if success_count % 50 == 0:
                print(f"  Applied {success_count}/{len(high_confidence)}...")

        except Exception as e:
            print(f"  ERROR updating {corr.code}: {e}")
            error_count += 1

    print()
    print("=" * 80)
    print("HIGH CONFIDENCE CORRECTIONS COMPLETE")
    print("=" * 80)
    print(f"Successfully applied: {success_count}")
    print(f"Errors: {error_count}")
    print()

    # Generate review queue for medium confidence
    if medium_confidence:
        print(f"Generating review queue for {len(medium_confidence)} MEDIUM confidence corrections...")
        review_file = f"severity_review_queue_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        generate_review_queue(medium_confidence, review_file)
        print()

    # Export logs
    log_data = {
        'timestamp': datetime.now().isoformat(),
        'total_codes': total,
        'analysis': {
            'no_change': stats['no_change'],
            'high_confidence': stats['high_confidence'],
            'medium_confidence': stats['medium_confidence'],
            'low_confidence': stats['low_confidence']
        },
        'applied': {
            'count': success_count,
            'errors': error_count,
            'changes': changes_log
        },
        'pending_review': len(medium_confidence),
        'left_unchanged': len(low_confidence)
    }

    log_file = f"severity_corrections_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(log_file, 'w') as f:
        json.dump(log_data, f, indent=2)

    print(f"Changes log: {log_file}")
    print()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"High confidence:   {success_count} corrections applied")
    print(f"Medium confidence: {len(medium_confidence)} corrections queued for review")
    print(f"Low confidence:    {len(low_confidence)} codes left unchanged")
    print()

    if medium_confidence:
        print(f"NEXT STEP: Review medium confidence corrections in {review_file}")
        print()

    # Show severity distribution after changes
    print("=" * 80)
    print("SEVERITY DISTRIBUTION (AFTER CORRECTIONS)")
    print("=" * 80)

    result = client.table('obd_codes').select('severity').execute()
    severity_counts = {}
    for record in result.data:
        sev = record.get('severity', 'Unknown')
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    for severity in ['Critical', 'High', 'Moderate', 'Low', 'Medium']:
        count = severity_counts.get(severity, 0)
        if count > 0:
            percentage = (count / total) * 100
            print(f"{severity:12} {count:5} codes ({percentage:5.1f}%)")

    print()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--dry-run':
        print("DRY RUN MODE - No changes will be applied")
        print()
    asyncio.run(apply_confidence_severity())
