"""
Comprehensive DTC Database Completeness Audit

Analyzes the entire obd_codes database to determine:
- Field completion rates
- Record completeness distribution
- Priority codes for enrichment
- Severity rating accuracy
"""

import asyncio
from supabase import create_client
from app.core.config import settings
from collections import defaultdict
import json


def is_populated(value) -> bool:
    """Check if a field has meaningful data"""
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return len(value) > 0
    return bool(value)


def calculate_completeness_score(record: dict) -> tuple[int, dict]:
    """
    Calculate completeness score for a record (0-100).
    Returns (score, field_status)
    """
    fields = {
        'description': is_populated(record.get('description')),
        'system': is_populated(record.get('system')),
        'symptoms': is_populated(record.get('symptoms')),
        'common_causes': is_populated(record.get('common_causes')),
        'generic_fixes': is_populated(record.get('generic_fixes')),
        'severity': is_populated(record.get('severity')),
        'severity_explanation': is_populated(record.get('severity_explanation')),
        'technician_tip': is_populated(record.get('technician_tip')),
        'pre_replacement_checks': is_populated(record.get('pre_replacement_checks'))
    }

    score = int((sum(fields.values()) / len(fields)) * 100)
    return score, fields


def categorize_severity(code: str, description: str, current_severity: str) -> tuple[str, str, bool]:
    """
    Validate and categorize severity based on automotive knowledge.
    Returns (recommended_severity, reason, needs_correction)
    """
    code_upper = code.upper()
    desc_lower = description.lower() if description else ""

    # Critical patterns (safety-critical, immediate danger)
    critical_patterns = [
        'brake', 'airbag', 'srs', 'restraint', 'abs', 'traction control',
        'stability control', 'steering', 'transmission fail', 'oil pressure low',
        'engine overheating', 'coolant temperature high'
    ]

    # High severity patterns (engine damage risk, significant performance loss)
    high_patterns = [
        'misfire', 'knock sensor', 'detonation', 'timing', 'valve timing',
        'turbo', 'supercharger', 'fuel pressure low', 'catalyst damage',
        'oil leak', 'coolant leak', 'head gasket'
    ]

    # Low severity patterns (minor issues, informational)
    low_patterns = [
        'evap', 'purge', 'vent', 'canister', 'fuel cap', 'readiness',
        'monitor', 'incomplete', 'sensor circuit', 'pressure sensor circuit',
        'switch circuit', 'sensor range', 'sensor performance'
    ]

    # Check for critical
    if any(pattern in desc_lower for pattern in critical_patterns):
        recommended = "Critical"
        reason = "Safety-critical system"
    # Check for low
    elif any(pattern in desc_lower for pattern in low_patterns):
        recommended = "Low" if 'evap' in desc_lower or 'fuel cap' in desc_lower else "Moderate"
        reason = "Emissions/monitoring system (non-critical)"
    # Check for high
    elif any(pattern in desc_lower for pattern in high_patterns):
        recommended = "High"
        reason = "Engine damage risk or significant performance loss"
    else:
        # Default to Moderate for unknown codes
        recommended = "Moderate"
        reason = "Standard diagnostic code"

    # Specific code overrides
    evap_codes = ['P0440', 'P0441', 'P0442', 'P0443', 'P0446', 'P0450', 'P0451', 'P0452', 'P0453', 'P0455', 'P0456', 'P0457']
    if code_upper in evap_codes:
        recommended = "Moderate"
        reason = "EVAP system - emissions only, rarely causes drivability issues"

    needs_correction = (current_severity != recommended) if current_severity else False

    return recommended, reason, needs_correction


async def audit_database():
    """Perform comprehensive database audit"""

    if not settings.supabase_enabled:
        print("ERROR: Supabase is disabled in config")
        return

    print("=" * 80)
    print("DTC DATABASE COMPLETENESS AUDIT")
    print("=" * 80)
    print()

    client = create_client(settings.supabase_url, settings.supabase_service_key)

    # Fetch all records
    print("Fetching all DTC records from database...")
    result = client.table('obd_codes').select('*').execute()

    if not result.data:
        print("ERROR: No data found in database")
        return

    all_codes = result.data
    total_count = len(all_codes)

    print(f"Total DTCs in database: {total_count}")
    print()

    # Track statistics
    field_population = defaultdict(int)
    completeness_distribution = {
        'complete': [],           # 100% complete
        'mostly_complete': [],    # 70-99% complete
        'partial': [],            # 30-69% complete
        'minimal': [],            # 1-29% complete
        'empty': []              # 0% complete
    }

    severity_corrections = []
    codes_without_enrichment = []

    # Analyze each record
    for record in all_codes:
        code = record.get('code')
        score, fields = calculate_completeness_score(record)

        # Track field population
        for field_name, is_populated in fields.items():
            if is_populated:
                field_population[field_name] += 1

        # Categorize completeness
        if score == 100:
            completeness_distribution['complete'].append(code)
        elif score >= 70:
            completeness_distribution['mostly_complete'].append(code)
        elif score >= 30:
            completeness_distribution['partial'].append(code)
        elif score > 0:
            completeness_distribution['minimal'].append(code)
        else:
            completeness_distribution['empty'].append(code)

        # Check severity accuracy
        current_severity = record.get('severity')
        description = record.get('description', '')
        recommended_severity, reason, needs_correction = categorize_severity(
            code, description, current_severity
        )

        if needs_correction:
            severity_corrections.append({
                'code': code,
                'description': description,
                'current': current_severity,
                'recommended': recommended_severity,
                'reason': reason
            })

        # Track enrichment status
        enrichment_status = record.get('enrichment_status')
        if not enrichment_status or enrichment_status == 'not_enriched':
            if score < 100:
                codes_without_enrichment.append({
                    'code': code,
                    'score': score,
                    'missing': [k for k, v in fields.items() if not v]
                })

    # Print Field Completion Statistics
    print("=" * 80)
    print("FIELD COMPLETION RATES")
    print("=" * 80)
    print()

    field_order = [
        'description',
        'system',
        'common_causes',
        'generic_fixes',
        'symptoms',
        'severity',
        'severity_explanation',
        'technician_tip',
        'pre_replacement_checks'
    ]

    for field in field_order:
        count = field_population[field]
        percentage = (count / total_count) * 100
        bar_length = int(percentage / 2)
        bar = '#' * bar_length + '-' * (50 - bar_length)
        print(f"{field:30} {bar} {percentage:6.2f}% ({count}/{total_count})")

    print()

    # Print Completeness Distribution
    print("=" * 80)
    print("RECORD COMPLETENESS DISTRIBUTION")
    print("=" * 80)
    print()

    complete_count = len(completeness_distribution['complete'])
    mostly_complete_count = len(completeness_distribution['mostly_complete'])
    partial_count = len(completeness_distribution['partial'])
    minimal_count = len(completeness_distribution['minimal'])
    empty_count = len(completeness_distribution['empty'])

    print(f"Complete (100%):           {complete_count:5} codes ({(complete_count/total_count)*100:.1f}%)")
    print(f"Mostly Complete (70-99%):  {mostly_complete_count:5} codes ({(mostly_complete_count/total_count)*100:.1f}%)")
    print(f"Partial (30-69%):          {partial_count:5} codes ({(partial_count/total_count)*100:.1f}%)")
    print(f"Minimal (1-29%):           {minimal_count:5} codes ({(minimal_count/total_count)*100:.1f}%)")
    print(f"Empty (0%):                {empty_count:5} codes ({(empty_count/total_count)*100:.1f}%)")
    print()

    # Show sample incomplete codes
    print("=" * 80)
    print("SAMPLE INCOMPLETE CODES (showing first 20)")
    print("=" * 80)
    print()

    incomplete_codes = (
        completeness_distribution['minimal'] +
        completeness_distribution['partial'] +
        completeness_distribution['mostly_complete']
    )

    for code_name in incomplete_codes[:20]:
        record = next(r for r in all_codes if r.get('code') == code_name)
        score, fields = calculate_completeness_score(record)
        missing = [k for k, v in fields.items() if not v]
        print(f"{code_name:8} - {score:3}% complete - Missing: {', '.join(missing)}")

    if len(incomplete_codes) > 20:
        print(f"\n... and {len(incomplete_codes) - 20} more incomplete codes")

    print()

    # Severity Corrections
    print("=" * 80)
    print("SEVERITY RATING CORRECTIONS NEEDED")
    print("=" * 80)
    print()

    if severity_corrections:
        print(f"Found {len(severity_corrections)} codes with questionable severity ratings:")
        print()

        for correction in severity_corrections[:20]:
            print(f"Code: {correction['code']}")
            print(f"  Description: {correction['description'][:60]}...")
            print(f"  Current: {correction['current'] or 'None'} -> Recommended: {correction['recommended']}")
            print(f"  Reason: {correction['reason']}")
            print()

        if len(severity_corrections) > 20:
            print(f"... and {len(severity_corrections) - 20} more corrections needed")
    else:
        print("OK - All severity ratings appear reasonable")

    print()

    # Priority Codes for Enrichment
    print("=" * 80)
    print("TOP 20 PRIORITY CODES FOR ENRICHMENT")
    print("=" * 80)
    print()

    # Common/important codes that should be enriched first
    priority_codes = [
        'P0300', 'P0301', 'P0302', 'P0303', 'P0304',  # Misfires
        'P0420', 'P0430',  # Catalyst
        'P0171', 'P0174',  # Fuel trim
        'P0440', 'P0442', 'P0455', 'P0456',  # EVAP
        'P0128',  # Coolant temp
        'P0401',  # EGR
        'P0506', 'P0507',  # Idle control
        'P0010', 'P0011',  # VVT
        'P0031', 'P0037'   # O2 heater
    ]

    priority_incomplete = []
    for code in priority_codes:
        record = next((r for r in all_codes if r.get('code') == code), None)
        if record:
            score, fields = calculate_completeness_score(record)
            if score < 100:
                missing = [k for k, v in fields.items() if not v]
                priority_incomplete.append({
                    'code': code,
                    'score': score,
                    'description': record.get('description', 'N/A'),
                    'missing': missing
                })

    if priority_incomplete:
        print("High-priority codes needing enrichment:")
        print()
        for item in priority_incomplete:
            print(f"{item['code']:8} - {item['score']:3}% complete")
            print(f"  {item['description'][:70]}")
            print(f"  Missing: {', '.join(item['missing'])}")
            print()
    else:
        print("OK - All priority codes are fully enriched")

    print()

    # RECOMMENDATION
    print("=" * 80)
    print("RECOMMENDATION")
    print("=" * 80)
    print()

    # Calculate key metrics
    incomplete_percentage = ((total_count - complete_count) / total_count) * 100
    critical_fields_avg = (
        field_population['symptoms'] +
        field_population['common_causes'] +
        field_population['generic_fixes'] +
        field_population['severity_explanation'] +
        field_population['technician_tip']
    ) / (5 * total_count) * 100

    print(f"Database Completeness: {(complete_count/total_count)*100:.1f}%")
    print(f"Incomplete Records: {incomplete_percentage:.1f}% ({total_count - complete_count} codes)")
    print(f"Critical Fields Average: {critical_fields_avg:.1f}%")
    print(f"Priority Codes Incomplete: {len(priority_incomplete)}/{len(priority_codes)}")
    print()

    # Make recommendation
    if complete_count / total_count >= 0.90:
        print("RECOMMENDATION: OPTION A - Enable AUTO_LEARN_CODES")
        print()
        print("The database is mostly complete (>90%). Auto-learn can handle the")
        print("remaining gaps on-demand as codes are requested.")
        print()
        print("Pros:")
        print("  - Immediate solution for user requests")
        print("  - Only enriches codes that are actually used")
        print("  - No bulk processing required")
        print()
        print("Cons:")
        print("  - First user requesting an incomplete code experiences delay")
        print("  - AI enrichment costs incurred during user requests")

    elif critical_fields_avg < 30:
        print("RECOMMENDATION: OPTION B - Run Bulk Enrichment Job")
        print()
        print("The database has significant gaps (<30% critical field completion).")
        print("A bulk enrichment job should run before enabling auto-learn.")
        print()
        print("Recommended approach:")
        print(f"  1. Bulk enrich {len(priority_incomplete)} high-priority codes")
        print(f"  2. Bulk enrich remaining {len(incomplete_codes)} incomplete codes")
        print("  3. Enable AUTO_LEARN_CODES for future gaps")
        print()
        print("Pros:")
        print("  - Consistent user experience (no first-request delays)")
        print("  - Batch processing is more cost-efficient")
        print("  - Quality control before deployment")
        print()
        print("Cons:")
        print("  - Requires upfront time and API costs")
        print(f"  - Estimated enrichment time: {len(incomplete_codes) * 3 / 60:.0f} minutes")

    else:
        print("RECOMMENDATION: HYBRID APPROACH")
        print()
        print("The database is partially complete. Recommended strategy:")
        print()
        print(f"  1. Bulk enrich {len(priority_incomplete)} high-priority codes now")
        print("  2. Enable AUTO_LEARN_CODES for remaining gaps")
        print("  3. Monitor enrichment quality and costs")
        print()
        print("This balances immediate completeness for common codes with")
        print("on-demand enrichment for rare codes.")

    print()

    # Severity corrections
    if severity_corrections:
        print("WARNING: SEVERITY CORRECTIONS NEEDED")
        print()
        print(f"Found {len(severity_corrections)} codes with potentially incorrect severity ratings.")
        print("Run the severity correction script to fix these issues.")
        print()

    # Export detailed report
    report = {
        'summary': {
            'total_codes': total_count,
            'complete': complete_count,
            'incomplete': total_count - complete_count,
            'incomplete_percentage': incomplete_percentage
        },
        'field_completion': {
            field: {
                'count': field_population[field],
                'percentage': (field_population[field] / total_count) * 100
            }
            for field in field_order
        },
        'completeness_distribution': {
            'complete': len(completeness_distribution['complete']),
            'mostly_complete': len(completeness_distribution['mostly_complete']),
            'partial': len(completeness_distribution['partial']),
            'minimal': len(completeness_distribution['minimal']),
            'empty': len(completeness_distribution['empty'])
        },
        'priority_incomplete': priority_incomplete,
        'severity_corrections': severity_corrections[:50],  # Limit to first 50
        'incomplete_codes': codes_without_enrichment[:100]  # Limit to first 100
    }

    with open('database_audit_report.json', 'w') as f:
        json.dump(report, f, indent=2)

    print("=" * 80)
    print()
    print("Detailed report exported to: database_audit_report.json")
    print()


if __name__ == "__main__":
    asyncio.run(audit_database())
