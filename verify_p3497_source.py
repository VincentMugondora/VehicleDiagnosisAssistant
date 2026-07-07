#!/usr/bin/env python3
"""
Verify where P3497 came from and check the import filtering strategy
"""
import os
import sqlite3
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

print("=" * 70)
print("P3497 Source Verification & Import Strategy Analysis")
print("=" * 70)

# Check Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("\n[1] Checking P3497 in Supabase...")
result = supabase.table("obd_codes").select("*").eq("code", "P3497").execute()
if result.data:
    print(f"  FOUND in Supabase:")
    for key, val in result.data[0].items():
        print(f"    {key}: {val}")
else:
    print("  NOT FOUND in Supabase")

# Check Wal33D source database
print("\n[2] Checking P3497 in Wal33D source database...")
db_path = Path(r"C:\Users\vinmu\AppData\Local\Temp\dtc-database\data\dtc_codes.db")

if db_path.exists():
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Check if P3497 exists and its attributes
    cursor.execute("""
        SELECT code, description, type, manufacturer, is_generic
        FROM dtc_definitions
        WHERE code = 'P3497'
    """)

    row = cursor.fetchone()
    if row:
        print(f"  FOUND in Wal33D database:")
        print(f"    code: {row['code']}")
        print(f"    description: {row['description']}")
        print(f"    type: {row['type']}")
        print(f"    manufacturer: {row['manufacturer']}")
        print(f"    is_generic: {row['is_generic']}")

        if row['is_generic'] == 1 and row['manufacturer'] == 'GENERIC':
            print("  [YES] Would be included in generic-only import")
        else:
            print("  [NO] Would be EXCLUDED from generic-only import")
    else:
        print("  NOT FOUND in Wal33D database")

    # Get stats on manufacturer-specific codes
    print("\n[3] Wal33D Database Statistics...")
    cursor.execute("SELECT COUNT(*) as total FROM dtc_definitions")
    total = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) as generic FROM dtc_definitions WHERE is_generic = 1 AND manufacturer = 'GENERIC'")
    generic = cursor.fetchone()['generic']

    cursor.execute("SELECT COUNT(*) as manufacturer FROM dtc_definitions WHERE is_generic = 0 OR manufacturer != 'GENERIC'")
    manufacturer = cursor.fetchone()['manufacturer']

    print(f"  Total codes: {total}")
    print(f"  Generic codes (imported): {generic}")
    print(f"  Manufacturer-specific codes (excluded): {manufacturer}")

    # Check for other P3xxx codes
    cursor.execute("""
        SELECT COUNT(*) as count,
               SUM(CASE WHEN is_generic = 1 AND manufacturer = 'GENERIC' THEN 1 ELSE 0 END) as generic_count
        FROM dtc_definitions
        WHERE code LIKE 'P3%'
    """)
    p3_stats = cursor.fetchone()
    print(f"\n  P3xxx range (typically manufacturer-specific):")
    print(f"    Total P3xxx codes: {p3_stats['count']}")
    print(f"    Generic P3xxx codes: {p3_stats['generic_count']}")
    print(f"    Manufacturer-specific P3xxx: {p3_stats['count'] - p3_stats['generic_count']}")

    conn.close()
else:
    print("  Wal33D database not found locally")

# Check import script filtering logic
print("\n[4] Import Script Filtering Strategy...")
print("  The import_wal33d_dtc.py script uses:")
print("    WHERE is_generic = 1 AND manufacturer = 'GENERIC'")
print("  This DELIBERATELY excludes manufacturer-specific codes.")

print("\n" + "=" * 70)
print("CONCLUSION:")
print("=" * 70)
print("If P3497 is in Supabase but excluded by the filter, it came from")
print("the original 133-code seed data, NOT the Wal33D import.")
print()
print("To import ALL codes (including manufacturer-specific):")
print("  - Modify the WHERE clause in import_wal33d_dtc.py")
print("  - Or manually add specific manufacturer codes as one-offs")
print("=" * 70)
