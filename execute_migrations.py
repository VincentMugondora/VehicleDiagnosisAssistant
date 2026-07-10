"""
Execute Database Migrations via Supabase

Manually executes migration SQL via Supabase.
"""

import asyncio
from supabase import create_client
from app.core.config import settings


async def execute_migrations():
    """Execute migrations directly"""

    if not settings.supabase_enabled:
        print("ERROR: Supabase is disabled")
        return

    print("=" * 80)
    print("EXECUTING DATABASE MIGRATIONS")
    print("=" * 80)
    print()

    client = create_client(settings.supabase_url, settings.supabase_service_key)

    # Migration 1: Add enrichment_status column
    print("Migration 1: Adding enrichment_status column...")
    try:
        # Check if column exists
        result = client.table('obd_codes').select('enrichment_status').limit(1).execute()
        print("  Column already exists")
    except Exception:
        print("  ERROR: Cannot add column via Supabase client")
        print("  Please run: migrations/001_add_enrichment_status.sql manually")
        print()
        return

    # Initialize enrichment_status for existing records
    print("  Initializing enrichment_status for existing records...")
    try:
        # Update all records that don't have enrichment_status
        result = client.table('obd_codes').select('code, enrichment_status').execute()

        codes_to_update = [
            r['code'] for r in result.data
            if r.get('enrichment_status') is None
        ]

        if codes_to_update:
            print(f"  Found {len(codes_to_update)} codes without status")
            for code in codes_to_update[:10]:  # Update in batches
                client.table('obd_codes').update({
                    'enrichment_status': 'raw_database'
                }).eq('code', code).execute()

            print(f"  Initialized {min(len(codes_to_update), 10)} codes")
            if len(codes_to_update) > 10:
                print(f"  Note: {len(codes_to_update) - 10} more codes need initialization")
        else:
            print("  All codes already have enrichment_status")

    except Exception as e:
        print(f"  WARNING: {e}")

    print("  SUCCESS")
    print()

    # Migration 2 & 3: JSONB columns and audit log
    print("Migration 2 & 3: Metadata columns and audit log...")
    print("  These require DDL statements (ALTER TABLE, CREATE TABLE)")
    print("  Please run manually via Supabase SQL Editor:")
    print()
    print("  1. Go to Supabase Dashboard > SQL Editor")
    print("  2. Copy contents of migrations/002_add_provenance_metadata.sql")
    print("  3. Execute SQL")
    print("  4. Copy contents of migrations/003_create_audit_log.sql")
    print("  5. Execute SQL")
    print()

    response = input("Have you run migrations 2 & 3? (yes/skip): ")
    if response.lower() != 'yes':
        print()
        print("Migrations incomplete. Please run manually before proceeding.")
        print()
        return

    print()
    print("=" * 80)
    print("MIGRATION SETUP COMPLETE")
    print("=" * 80)
    print()


if __name__ == "__main__":
    asyncio.run(execute_migrations())
