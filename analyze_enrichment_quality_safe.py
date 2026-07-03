"""
Analyze enrichment data quality in the DTC database.

Reports:
1. Total codes in database
2. Codes with auto-generated (generic) enrichment vs. original enrichment
3. Most commonly searched codes and their enrichment status
4. Recommendations for backfilling from better sources
"""
import sys
sys.path.insert(0, ".")

from app.db.client import get_supabase_client
from app.repositories.obd_repository import OBDRepository

# Common codes from real-world usage stats
TOP_CODES = [
    "P0300",  # Random/Multiple Cylinder Misfire
    "P0420",  # Catalyst System Efficiency Below Threshold
    "P0171",  # System Too Lean Bank 1
    "P0455",  # EVAP System Leak Detected (Large Leak)
    "P0128",  # Coolant Thermostat (Coolant Temperature Below Thermostat)
    "P0442",  # EVAP System Leak Detected (Small Leak)
    "P0507",  # Idle Air Control System RPM Higher Than Expected
    "P0101",  # Mass Air Flow Circuit Range/Performance
    "P0301",  # Cylinder 1 Misfire Detected
    "P0440",  # EVAP System Malfunction
    "P0172",  # System Too Rich Bank 1
    "P0430",  # Catalyst System Efficiency Below Threshold Bank 2
    "P0456",  # EVAP System Leak Detected (Very Small Leak)
    "P0174",  # System Too Lean Bank 2
    "P0400",  # Exhaust Gas Recirculation Flow Malfunction
]

# Generic enrichment keywords (auto-generated)
GENERIC_CAUSES = [
    "component malfunction",
    "wiring or connector issue",
    "sensor failure",
    "ecm software issue",
    "ecm issue",
    "faulty sensor",
    "damaged wiring"
]

GENERIC_CHECKS = [
    "scan for additional codes",
    "inspect related components",
    "check wiring and connectors",
    "clear code and retest",
    "inspect wiring",
    "check connectors"
]


def is_generic_enrichment(causes_str: str, checks_str: str) -> bool:
    """Check if enrichment appears to be auto-generated"""
    if not causes_str and not checks_str:
        return True  # Empty = needs enrichment

    causes_lower = causes_str.lower() if causes_str else ""
    checks_lower = checks_str.lower() if checks_str else ""

    # Check if contains generic keywords
    has_generic_cause = any(g in causes_lower for g in GENERIC_CAUSES)
    has_generic_check = any(g in checks_lower for g in GENERIC_CHECKS)

    return has_generic_cause or has_generic_check


def main():
    print("\n" + "="*80)
    print(" DTC ENRICHMENT QUALITY ANALYSIS")
    print("="*80)

    client = get_supabase_client()
    repo = OBDRepository(client)

    # Get all codes from database
    print("\nFetching all DTC records from database...")
    try:
        # Query Supabase directly for all codes
        response = client.table("obd_codes").select("code, common_causes, generic_fixes").execute()
        all_codes = response.data
        print(f"[OK] Found {len(all_codes)} total codes")
    except Exception as e:
        print(f"[X] Error fetching codes: {e}")
        return 1

    # Analyze enrichment quality
    generic_count = 0
    specific_count = 0
    empty_count = 0

    for code_record in all_codes:
        causes = code_record.get("common_causes", "") or ""
        checks = code_record.get("generic_fixes", "") or ""

        if not causes and not checks:
            empty_count += 1
        elif is_generic_enrichment(causes, checks):
            generic_count += 1
        else:
            specific_count += 1

    # Report overall stats
    print("\n" + "="*80)
    print(" OVERALL ENRICHMENT STATUS")
    print("="*80)
    print(f"Total codes: {len(all_codes)}")
    print(f"  ├─ Specific enrichment: {specific_count} ({specific_count/len(all_codes)*100:.1f}%)")
    print(f"  ├─ Generic enrichment:  {generic_count} ({generic_count/len(all_codes)*100:.1f}%)")
    print(f"  └─ Empty enrichment:    {empty_count} ({empty_count/len(all_codes)*100:.1f}%)")

    print("\n[!]  Limitation: Generic enrichment is boilerplate fallback")
    print("    Example generic causes:")
    for cause in GENERIC_CAUSES[:3]:
        print(f"      - {cause}")
    print("    These work but lack code-specific detail.")

    # Check top codes
    print("\n" + "="*80)
    print(" TOP CODES ENRICHMENT STATUS")
    print("="*80)
    print(f"Checking {len(TOP_CODES)} most commonly searched codes:\n")

    top_codes_generic = []
    top_codes_specific = []

    for code in TOP_CODES:
        try:
            code_data = repo.get_by_code(code)
            if code_data:
                causes = code_data.get("common_causes", "") or ""
                checks = code_data.get("generic_fixes", "") or ""

                if is_generic_enrichment(causes, checks):
                    status = "[!]  GENERIC"
                    top_codes_generic.append(code)
                else:
                    status = "[OK] SPECIFIC"
                    top_codes_specific.append(code)

                print(f"{status}  {code:6s} - {code_data.get('description', 'No description')[:60]}")
            else:
                print(f"[X] MISSING  {code:6s} - Not in database")
        except Exception as e:
            print(f"[X] ERROR    {code:6s} - {e}")

    # Backfill recommendation
    print("\n" + "="*80)
    print(" BACKFILL RECOMMENDATION")
    print("="*80)

    if top_codes_generic:
        print(f"\n🎯 Priority: {len(top_codes_generic)}/{len(TOP_CODES)} top codes have generic enrichment")
        print("\nCodes to prioritize for backfill:")
        for code in top_codes_generic:
            print(f"  - {code}")

        print("\n📋 Proposed backfill plan:")
        print("  1. Check these alternative datasets for better enrichment:")
        print("     - https://github.com/mytrile/obd-trouble-codes")
        print("     - https://github.com/todrobbins/dtcdb")
        print("     - https://github.com/fabiovila/OBDIICodes")
        print("  2. For each top code, extract:")
        print("     - Specific causes (not generic)")
        print("     - Specific diagnostic steps (not generic)")
        print("  3. Update database with specific enrichment")
        print(f"\n  Estimated coverage improvement: {len(top_codes_generic)}/{len(TOP_CODES)} top codes")
        print(f"  (from {len(top_codes_specific)}/{len(TOP_CODES)} to {len(TOP_CODES)}/{len(TOP_CODES)} with specific data)")
    else:
        print("[OK] All top codes already have specific enrichment!")

    # Summary
    print("\n" + "="*80)
    print(" SUMMARY")
    print("="*80)
    print(f"\n📊 Database has {len(all_codes)} codes:")
    print(f"   - {specific_count} with specific enrichment ({specific_count/len(all_codes)*100:.1f}%)")
    print(f"   - {generic_count + empty_count} needing better enrichment ({(generic_count+empty_count)/len(all_codes)*100:.1f}%)")

    print(f"\n🎯 Top {len(TOP_CODES)} codes:")
    print(f"   - {len(top_codes_specific)} already specific")
    print(f"   - {len(top_codes_generic)} need backfill from better sources")

    print("\n💡 Next step: Review alternative datasets and backfill priority codes")
    print("   (Don't implement yet - report findings first)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
