"""Simple enrichment analysis without Unicode"""
import sys
sys.path.insert(0, ".")

from app.db.client import get_supabase_client
from app.repositories.obd_repository import OBDRepository

TOP_CODES = [
    "P0300", "P0420", "P0171", "P0455", "P0128", "P0442", "P0507",
    "P0101", "P0301", "P0440", "P0172", "P0430", "P0456", "P0174", "P0400"
]

GENERIC_CAUSES = [
    "component malfunction", "wiring or connector issue", "sensor failure",
    "ecm software issue", "ecm issue", "faulty sensor", "damaged wiring"
]

GENERIC_CHECKS = [
    "scan for additional codes", "inspect related components",
    "check wiring and connectors", "clear code and retest"
]

def is_generic(causes_str, checks_str):
    if not causes_str and not checks_str:
        return True
    causes_lower = (causes_str or "").lower()
    checks_lower = (checks_str or "").lower()
    has_generic_cause = any(g in causes_lower for g in GENERIC_CAUSES)
    has_generic_check = any(g in checks_lower for g in GENERIC_CHECKS)
    return has_generic_cause or has_generic_check

print("\nDTC ENRICHMENT QUALITY ANALYSIS")
print("="*70)

client = get_supabase_client()
repo = OBDRepository(client)

response = client.table("obd_codes").select("code, common_causes, generic_fixes").execute()
all_codes = response.data

generic_count = 0
specific_count = 0
empty_count = 0

for code_record in all_codes:
    causes = code_record.get("common_causes", "") or ""
    checks = code_record.get("generic_fixes", "") or ""
    if not causes and not checks:
        empty_count += 1
    elif is_generic(causes, checks):
        generic_count += 1
    else:
        specific_count += 1

print(f"\nTotal codes: {len(all_codes)}")
print(f"  - Specific enrichment: {specific_count} ({specific_count/len(all_codes)*100:.1f}%)")
print(f"  - Generic enrichment:  {generic_count} ({generic_count/len(all_codes)*100:.1f}%)")
print(f"  - Empty enrichment:    {empty_count} ({empty_count/len(all_codes)*100:.1f}%)")

print("\nTOP CODES ENRICHMENT STATUS")
print("="*70)

top_generic = []
top_specific = []

for code in TOP_CODES:
    code_data = repo.get_by_code(code)
    if code_data:
        causes = code_data.get("common_causes", "") or ""
        checks = code_data.get("generic_fixes", "") or ""
        if is_generic(causes, checks):
            status = "[GENERIC]"
            top_generic.append(code)
        else:
            status = "[SPECIFIC]"
            top_specific.append(code)
        desc = code_data.get('description', 'No description')[:55]
        print(f"{status} {code:6s} - {desc}")
    else:
        print(f"[MISSING]  {code:6s} - Not in database")

print(f"\nTop codes summary:")
print(f"  - {len(top_specific)}/{len(TOP_CODES)} have specific enrichment")
print(f"  - {len(top_generic)}/{len(TOP_CODES)} have generic enrichment")

if top_generic:
    print(f"\nPriority codes needing backfill:")
    for code in top_generic:
        print(f"  - {code}")

    print("\nBackfill plan:")
    print("  1. Check these datasets for better enrichment:")
    print("     - github.com/mytrile/obd-trouble-codes")
    print("     - github.com/todrobbins/dtcdb")
    print("     - github.com/fabiovila/OBDIICodes")
    print(f"  2. Estimated improvement: {len(top_generic)} codes upgraded to specific")
else:
    print("\nAll top codes have specific enrichment!")

print("\n" + "="*70)
