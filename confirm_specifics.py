#!/usr/bin/env python3
"""
Confirm P3497 status and list the 7 enriched codes
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

print("=" * 70)
print("SPECIFIC CONFIRMATIONS")
print("=" * 70)

# 1. Check P3497 specifically
print("\n[1] P3497 Status")
print("-" * 70)
result = supabase.table("obd_codes").select("*").eq("code", "P3497").execute()

if result.data:
    p3497 = result.data[0]
    print("STATUS: FOUND in obd_codes table")
    print(f"  Code: {p3497['code']}")
    print(f"  Description: {p3497['description']}")
    print(f"  System: {p3497['system']}")
    print(f"  Severity: {p3497['severity']}")
    print(f"  Has symptoms: {p3497['symptoms'] is not None}")
    print(f"  Has causes: {p3497['common_causes'] is not None}")
    print(f"  Has fixes: {p3497['generic_fixes'] is not None}")
else:
    print("STATUS: NOT FOUND in obd_codes table")

# 2. List the 7 enriched codes
print("\n[2] The 7 Fully Enriched Codes")
print("-" * 70)

result = supabase.table("obd_codes").select("code, description, symptoms").not_.is_("symptoms", "null").execute()

print(f"Found {len(result.data)} codes with symptoms:\n")

for idx, row in enumerate(result.data, 1):
    symptoms_preview = row['symptoms'][:60] + "..." if len(row['symptoms']) > 60 else row['symptoms']
    print(f"{idx}. {row['code']}: {row['description']}")
    print(f"   Symptoms: {symptoms_preview}")
    print()

print("=" * 70)
