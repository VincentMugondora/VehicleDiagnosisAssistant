#!/usr/bin/env python3
"""
Check the specific codes that were causing FK constraint failures
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=" * 60)
print("FK Constraint Failure Codes Verification")
print("=" * 60)

# The 4 codes that were causing FK constraint failures
fk_failure_codes = ["P0609", "P0142", "P0271", "P3497"]

print("\n[CHECK] Verifying codes that caused FK failures...")
print()

found = []
missing = []

for code in fk_failure_codes:
    result = supabase.table("obd_codes").select("code, description").eq("code", code).execute()
    if result.data:
        found.append(code)
        print(f"  [FOUND] {code}: {result.data[0]['description']}")
    else:
        missing.append(code)
        print(f"  [MISSING] {code}: NOT FOUND in database")

print("\n" + "=" * 60)
print(f"Summary: {len(found)}/4 codes now present")
if missing:
    print(f"Still missing: {', '.join(missing)}")
else:
    print("All FK constraint codes are now in the database!")
print("=" * 60)
