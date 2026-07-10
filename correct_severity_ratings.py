"""
Severity Rating Correction Script

Corrects severity ratings in the database based on automotive knowledge.
- Replaces "Medium" with "Moderate" (standardization)
- Fixes incorrectly rated codes based on system and description analysis
"""

import asyncio
from supabase import create_client
from app.core.config import settings
import json


def determine_correct_severity(code: str, description: str, system: str, current_severity: str) -> tuple[str, str]:
    """
    Determine correct severity based on code, description, and system.
    Returns (correct_severity, reason)
    """
    code_upper = code.upper()
    desc_lower = description.lower() if description else ""
    system_lower = system.lower() if system else ""

    # Critical: Safety systems (immediate danger)
    critical_patterns = [
        ('brake', 'Brake system failure risk'),
        ('airbag', 'Safety restraint system'),
        ('srs', 'Safety restraint system'),
        ('abs', 'Anti-lock brake system'),
        ('stability control', 'Vehicle stability system'),
        ('traction control', 'Traction control system'),
        ('steering', 'Steering system failure risk'),
        ('oil pressure', 'Engine oil pressure critical')
    ]

    for pattern, reason in critical_patterns:
        if pattern in desc_lower or pattern in system_lower:
            return "Critical", reason

    # High: Engine damage risk, significant performance loss
    high_patterns = [
        ('misfire', 'Engine damage risk from misfires'),
        ('knock sensor', 'Detonation/engine damage risk'),
        ('detonation', 'Engine knock/damage risk'),
        ('timing', 'Timing system issue'),
        ('turbo', 'Turbocharger system'),
        ('supercharger', 'Supercharger system'),
        ('overheating', 'Engine overheating risk'),
        ('coolant temperature high', 'Overheating risk'),
        ('head gasket', 'Major engine leak'),
        ('transmission fail', 'Transmission failure')
    ]

    for pattern, reason in high_patterns:
        if pattern in desc_lower:
            # Exception: Misfire detection codes are High, but circuit codes are Moderate
            if 'misfire detected' in desc_lower:
                return "High", reason
            elif 'misfire' in pattern and 'circuit' in desc_lower:
                return "Moderate", "Sensor circuit issue (not actual misfire)"
            elif pattern != 'misfire':
                return "High", reason

    # Low: Informational, monitoring, minor issues
    low_patterns = [
        ('evap', 'EVAP system (emissions only)'),
        ('purge', 'EVAP purge system'),
        ('vent', 'EVAP vent system'),
        ('canister', 'EVAP canister system'),
        ('fuel cap', 'Fuel cap issue'),
        ('readiness', 'Monitor readiness'),
        ('monitor incomplete', 'Monitor not complete'),
        ('not ready', 'Monitor not ready')
    ]

    for pattern, reason in low_patterns:
        if pattern in desc_lower:
            # EVAP codes are Moderate (not Low) because they can affect drivability
            if 'evap' in pattern or 'purge' in pattern:
                return "Moderate", "EVAP system - emissions primarily, rarely drivability"
            return "Low", reason

    # Moderate: Sensor circuits, performance issues, standard diagnostic codes
    moderate_patterns = [
        ('sensor circuit', 'Sensor circuit issue'),
        ('sensor range', 'Sensor range/performance'),
        ('sensor performance', 'Sensor performance issue'),
        ('switch circuit', 'Switch circuit issue'),
        ('circuit', 'Electrical circuit issue'),
        ('voltage', 'Voltage issue'),
        ('sensor', 'Sensor issue'),
        ('o2 sensor', 'O2 sensor issue'),
        ('oxygen sensor', 'O2 sensor issue'),
        ('catalyst', 'Catalyst efficiency'),
        ('lean', 'Fuel trim issue'),
        ('rich', 'Fuel trim issue'),
        ('egr', 'EGR system'),
        ('idle', 'Idle control issue'),
        ('thermostat', 'Thermostat issue'),
        ('coolant temp below', 'Thermostat/cooling issue')
    ]

    for pattern, reason in moderate_patterns:
        if pattern in desc_lower:
            return "Moderate", reason

    # Specific code overrides
    evap_codes = [
        'P0440', 'P0441', 'P0442', 'P0443', 'P0446', 'P0450', 'P0451',
        'P0452', 'P0453', 'P0455', 'P0456', 'P0457', 'P0458', 'P0459'
    ]
    if code_upper in evap_codes:
        return "Moderate", "EVAP system - emissions primarily"

    # O2 sensor codes
    if code_upper.startswith('P01') and 'o2' in desc_lower:
        return "Moderate", "O2 sensor issue - emissions/fuel trim"

    # Default: Moderate for unknown codes
    return "Moderate", "Standard diagnostic code"


async def correct_severity_ratings():
    """Run severity correction on entire database"""

    if not settings.supabase_enabled:
        print("ERROR: Supabase is disabled")
        return

    print("=" * 80)
    print("SEVERITY RATING CORRECTION")
    print("=" * 80)
    print()

    client = create_client(settings.supabase_url, settings.supabase_service_key)

    # Fetch all records
    print("Fetching all DTC records...")
    result = client.table('obd_codes').select('*').execute()

    if not result.data:
        print("ERROR: No data found")
        return

    all_codes = result.data
    total = len(all_codes)
    print(f"Found {total} codes")
    print()

    # Analyze corrections needed
    corrections = []
    standardizations = []

    for record in all_codes:
        code = record.get('code')
        description = record.get('description', '')
        system = record.get('system', '')
        current = record.get('severity')

        if not current:
            continue

        # Determine correct severity
        correct, reason = determine_correct_severity(code, description, system, current)

        # Check if correction needed
        if current == "Medium":
            # Standardize "Medium" to "Moderate"
            standardizations.append({
                'code': code,
                'from': current,
                'to': "Moderate",
                'reason': "Standardization (Medium -> Moderate)"
            })
        elif current != correct:
            # Actual severity change
            corrections.append({
                'code': code,
                'description': description[:60],
                'from': current,
                'to': correct,
                'reason': reason
            })

    print(f"Corrections needed: {len(corrections)}")
    print(f"Standardizations needed: {len(standardizations)}")
    print()

    # Show sample corrections
    if corrections:
        print("Sample severity corrections (showing first 10):")
        print()
        for item in corrections[:10]:
            print(f"{item['code']:8} {item['from']:10} -> {item['to']:10}")
            print(f"  {item['description']}...")
            print(f"  Reason: {item['reason']}")
            print()

    if standardizations:
        print(f"\nStandardizing {len(standardizations)} codes from 'Medium' to 'Moderate'")
        print()

    # Ask for confirmation
    total_updates = len(corrections) + len(standardizations)
    print("=" * 80)
    response = input(f"Apply {total_updates} severity corrections? (yes/no): ")

    if response.lower() != 'yes':
        print("Cancelled")
        return

    print()
    print("Applying corrections...")

    # Apply corrections
    success_count = 0
    error_count = 0

    # Apply actual severity corrections
    for item in corrections:
        try:
            client.table('obd_codes').update({
                'severity': item['to']
            }).eq('code', item['code']).execute()
            success_count += 1
            if success_count % 100 == 0:
                print(f"  Updated {success_count}/{total_updates}...")
        except Exception as e:
            print(f"  ERROR updating {item['code']}: {e}")
            error_count += 1

    # Apply standardizations (Medium -> Moderate)
    for item in standardizations:
        try:
            client.table('obd_codes').update({
                'severity': 'Moderate'
            }).eq('code', item['code']).execute()
            success_count += 1
            if success_count % 100 == 0:
                print(f"  Updated {success_count}/{total_updates}...")
        except Exception as e:
            print(f"  ERROR updating {item['code']}: {e}")
            error_count += 1

    print()
    print("=" * 80)
    print("CORRECTION COMPLETE")
    print("=" * 80)
    print(f"Successfully updated: {success_count}")
    print(f"Errors: {error_count}")
    print()

    # Export correction log
    correction_log = {
        'timestamp': '2026-07-10',
        'total_codes': total,
        'corrections': len(corrections),
        'standardizations': len(standardizations),
        'success': success_count,
        'errors': error_count,
        'correction_details': corrections + standardizations
    }

    with open('severity_correction_log.json', 'w') as f:
        json.dump(correction_log, f, indent=2)

    print("Correction log exported to: severity_correction_log.json")
    print()


if __name__ == "__main__":
    asyncio.run(correct_severity_ratings())
