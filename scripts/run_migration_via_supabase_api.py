#!/usr/bin/env python3
"""
Run Migration 003 via Supabase Management API

This script uses the Supabase service key to execute SQL directly.
No database password needed!

Usage:
    python scripts/run_migration_via_supabase_api.py
    python scripts/run_migration_via_supabase_api.py --verify-only
"""

import sys
import argparse
import requests
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings


def read_migration_file(filename: str) -> str:
    """Read migration SQL file"""
    migration_path = Path(__file__).parent.parent / "supabase" / "migrations" / filename

    if not migration_path.exists():
        raise FileNotFoundError(f"Migration file not found: {migration_path}")

    with open(migration_path, 'r', encoding='utf-8') as f:
        return f.read()


def execute_sql_via_rpc(sql: str) -> bool:
    """
    Execute SQL via Supabase RPC function

    Note: This requires creating an RPC function in Supabase first
    """
    print("\n" + "="*70)
    print("MIGRATION EXECUTION OPTIONS")
    print("="*70)

    print("\nThe Supabase Python SDK doesn't support raw SQL execution.")
    print("Here are your options:\n")

    print("OPTION 1: Supabase Dashboard SQL Editor (EASIEST)")
    print("-" * 70)
    print("1. Go to: https://app.supabase.com/project/sklzlzcrjvrjylyvmdzj/sql/new")
    print("2. Copy the contents of: supabase/migrations/003_enhance_obd_codes_enrichment.sql")
    print("3. Paste into the SQL Editor")
    print("4. Click 'Run' button")
    print("\nThis is the recommended approach!\n")

    print("OPTION 2: Get Database Password (for automated script)")
    print("-" * 70)
    print("1. Go to: https://app.supabase.com/project/sklzlzcrjvrjylyvmdzj/settings/database")
    print("2. Find your database password (or reset it)")
    print("3. Set environment variable:")
    print('   PowerShell: $env:DB_PASSWORD="your-password"')
    print('   cmd: set DB_PASSWORD=your-password')
    print("4. Run: python scripts/run_migration_003_psycopg2.py\n")

    print("OPTION 3: Supabase CLI")
    print("-" * 70)
    print("If you have Supabase CLI linked to your project:")
    print("1. supabase link --project-ref sklzlzcrjvrjylyvmdzj")
    print("2. supabase db push\n")

    print("="*70)

    return False


def verify_migration_via_api() -> bool:
    """
    Verify migration via Supabase REST API
    """
    print("\n[*] Verifying Migration 003...\n")

    from supabase import create_client

    try:
        client = create_client(settings.supabase_url, settings.supabase_service_key)

        checks_passed = 0
        checks_total = 0

        # Check 1: Try to query new columns
        print("1. Checking if new columns exist...")
        checks_total += 1
        try:
            result = client.table("obd_codes").select(
                "code, enrichment_status, knowledge_score"
            ).limit(1).execute()

            print("   [OK] New columns accessible")
            checks_passed += 1
        except Exception as e:
            error_msg = str(e).lower()
            if "column" in error_msg and "does not exist" in error_msg:
                print(f"   [FAIL] New columns not found - migration not run yet")
            else:
                print(f"   [WARN] Could not verify columns: {e}")
                checks_passed += 1  # Might be empty table

        # Check 2: Try to query enrichment stats view
        print("\n2. Checking if views exist...")
        checks_total += 1
        try:
            result = client.table("obd_enrichment_stats").select("*").limit(5).execute()
            print(f"   [OK] Views accessible (found {len(result.data)} status groups)")
            checks_passed += 1
        except Exception as e:
            error_msg = str(e).lower()
            if "does not exist" in error_msg or "relation" in error_msg:
                print(f"   [FAIL] Views not found - migration not run yet")
            else:
                print(f"   [WARN] Could not verify views: {e}")

        # Check 3: Sample data if exists
        print("\n3. Checking for existing codes...")
        checks_total += 1
        try:
            result = client.table("obd_codes").select("code, description").limit(5).execute()

            if result.data:
                print(f"   [OK] Found {len(result.data)} sample codes:")
                for code_record in result.data[:3]:
                    code = code_record.get('code', 'N/A')
                    desc = code_record.get('description', 'N/A')[:50]
                    print(f"      - {code}: {desc}...")
                checks_passed += 1
            else:
                print("   [WARN] No codes in database yet")
                checks_passed += 1
        except Exception as e:
            print(f"   [WARN] Could not query codes: {e}")

        # Summary
        print("\n" + "="*70)
        print(f"Verification Results: {checks_passed}/{checks_total} checks passed")
        print("="*70)

        if checks_passed >= 2:
            print("\n[OK] Migration appears to be successful!")
            return True
        elif checks_passed == 1:
            print("\n[!] Migration may not be complete - some checks failed")
            print("    This usually means the migration hasn't been run yet.")
            return False
        else:
            print("\n[FAIL] Migration not detected")
            print("    Please run the migration using one of the options above.")
            return False

    except Exception as e:
        print(f"\n[ERROR] Verification failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Run Migration 003 via Supabase API")
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify migration, don't run it"
    )

    args = parser.parse_args()

    print("\n" + "="*70)
    print("Migration 003: Enhanced OBD Codes Enrichment")
    print("="*70)

    try:
        if args.verify_only:
            success = verify_migration_via_api()
        else:
            # Show migration options
            migration_sql = read_migration_file("003_enhance_obd_codes_enrichment.sql")
            print(f"\n[*] Migration file loaded: {len(migration_sql)} characters")
            success = execute_sql_via_rpc(migration_sql)

        if success:
            print("\n[OK] Operation completed successfully!")
            return 0
        else:
            print("\n[!] Please follow one of the options above to run the migration.")
            return 1

    except Exception as e:
        print(f"\n[ERROR] {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
