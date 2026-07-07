#!/usr/bin/env python3
"""
Direct database state check - get actual row counts from Supabase
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=" * 60)
print("LIVE DATABASE STATE CHECK")
print("=" * 60)

# Get total count of obd_codes
result = supabase.table("obd_codes").select("code", count="exact").execute()
total_count = result.count
print(f"\n[OK] Total rows in obd_codes table: {total_count}")

# Get sample of codes to see what's there
sample = supabase.table("obd_codes").select("code, description").limit(10).execute()
print(f"\n[SAMPLE] First 10 codes:")
for row in sample.data:
    print(f"  - {row['code']}: {row['description'][:60]}...")

# Check for specific markers to identify which import ran
# wal33d_dtc.py imports ~24k codes, load_obd_codes.py imports ~250
print("\n[CHECK] Identifying which import ran...")

# Check for some codes that would only be in the large dataset
test_codes = ["P0001", "P0002", "P0003", "P1000", "P2000", "U0001", "B0001", "C0001"]
found = []
for code in test_codes:
    result = supabase.table("obd_codes").select("code").eq("code", code).execute()
    if result.data:
        found.append(code)

print(f"  Marker codes found: {found} ({len(found)}/{len(test_codes)})")

if len(found) >= 6:
    print("\n[VERDICT] Full wal33d_dtc.py import (~24k codes) appears to have run")
elif len(found) >= 2:
    print("\n[VERDICT] Partial import - unclear which script ran")
else:
    print("\n[VERDICT] Only small seed import ran (load_obd_codes.py, ~250 codes)")

# Check for the 4 "missing" codes from the document
print("\n[CHECK] Verifying the 4 allegedly missing codes...")
missing_codes = ["P0016", "P0301", "P0455", "P0456"]
for code in missing_codes:
    result = supabase.table("obd_codes").select("code, description").eq("code", code).execute()
    if result.data:
        print(f"  [FOUND] {code}: {result.data[0]['description'][:60]}...")
    else:
        print(f"  [MISSING] {code}: NOT FOUND in database")

print("\n" + "=" * 60)
