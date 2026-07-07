#!/usr/bin/env python3
"""
Simple Database Overview
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

print("=" * 70)
print("DATABASE OVERVIEW")
print("=" * 70)

# Main obd_codes table
result = supabase.table("obd_codes").select("code", count="exact").execute()
total = result.count

print(f"\n[OBD CODES TABLE]")
print(f"  Total codes: {total}")
print()

# By system
for system in ["Powertrain", "Body", "Chassis", "Network"]:
    result = supabase.table("obd_codes").select("code", count="exact").eq("system", system).execute()
    print(f"  {system:15} {result.count:5} codes")

# Enriched codes
print()
result = supabase.table("obd_codes").select("code", count="exact").not_.is_("symptoms", "null").execute()
print(f"  With symptoms:  {result.count:5} codes ({result.count/total*100:.1f}%)")

result = supabase.table("obd_codes").select("code", count="exact").is_("symptoms", "null").execute()
print(f"  Basic only:     {result.count:5} codes ({result.count/total*100:.1f}%)")

# Detail tables
print(f"\n[DETAIL TABLES]")
for table in ["common_symptoms", "repair_steps", "parts", "related_codes"]:
    result = supabase.table(table).select("id", count="exact").execute()
    print(f"  {table:20} {result.count:5} rows")

print("\n" + "=" * 70)
