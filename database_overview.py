#!/usr/bin/env python3
"""
Database Overview - Show current state and statistics
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=" * 70)
print("DATABASE OVERVIEW")
print("=" * 70)

# 1. Total OBD codes count
print("\n[1] OBD Codes Count by System")
print("-" * 70)

result = supabase.table("obd_codes").select("code", count="exact").execute()
total = result.count
print(f"  Total OBD Codes: {total}")

# Count by system
for system in ["Powertrain", "Body", "Chassis", "Network", "Unknown"]:
    result = supabase.table("obd_codes").select("code", count="exact").eq("system", system).execute()
    print(f"    {system}: {result.count}")

# 2. Sample codes from each system
print("\n[2] Sample Codes (5 per system)")
print("-" * 70)

for system in ["Powertrain", "Body", "Chassis", "Network"]:
    result = supabase.table("obd_codes").select("code, description").eq("system", system).limit(5).execute()
    print(f"\n  {system}:")
    for row in result.data:
        desc = row['description'][:50] + "..." if len(row['description']) > 50 else row['description']
        print(f"    {row['code']}: {desc}")

# 3. Codes with enriched data (symptoms, causes, fixes)
print("\n[3] Enriched Codes (with symptoms/causes/fixes)")
print("-" * 70)

result = supabase.table("obd_codes").select("code, description").not_.is_("symptoms", "null").execute()
enriched_count = len(result.data)
print(f"  Codes with symptoms: {enriched_count}")

if enriched_count > 0:
    print(f"\n  Sample enriched codes:")
    for row in result.data[:5]:
        print(f"    {row['code']}: {row['description'][:50]}...")

# 4. Detail tables
print("\n[4] DTC Detail Tables")
print("-" * 70)

detail_tables = ["common_symptoms", "repair_steps", "parts", "related_codes"]
for table in detail_tables:
    result = supabase.table(table).select("dtc_code", count="exact").execute()
    print(f"  {table}: {result.count} rows")

    # Get unique codes count
    unique_result = supabase.table(table).select("dtc_code").execute()
    unique_codes = len(set(row['dtc_code'] for row in unique_result.data)) if unique_result.data else 0
    print(f"    Unique codes: {unique_codes}")

# 5. Coverage summary
print("\n[5] Overall Coverage Summary")
print("-" * 70)
print(f"  Total OBD codes: {total}")
print(f"  Codes with enriched data: {enriched_count} ({enriched_count/total*100:.1f}%)")
print(f"  Codes needing enrichment: {total - enriched_count} ({(total-enriched_count)/total*100:.1f}%)")

print("\n" + "=" * 70)
