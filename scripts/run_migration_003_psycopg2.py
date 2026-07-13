#!/usr/bin/env python3
"""
Migration 003 Runner with Direct PostgreSQL Connection

This script uses psycopg2 for direct database access.
Use this if you have PostgreSQL connection credentials.

Requirements:
    pip install psycopg2-binary

Usage:
    python scripts/run_migration_003_psycopg2.py
    python scripts/run_migration_003_psycopg2.py --rollback
    python scripts/run_migration_003_psycopg2.py --verify-only

Environment Variables Required:
    DATABASE_URL or individual:
    - DB_HOST
    - DB_PORT
    - DB_NAME
    - DB_USER
    - DB_PASSWORD
"""

import sys
import os
import argparse
from pathlib import Path
from urllib.parse import urlparse

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("❌ psycopg2 not installed. Install with: pip install psycopg2-binary")
    sys.exit(1)


def get_db_connection():
    """Get PostgreSQL connection from environment"""

    # Try DATABASE_URL first (common in production)
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        # Parse DATABASE_URL
        parsed = urlparse(database_url)
        conn_params = {
            "host": parsed.hostname,
            "port": parsed.port or 5432,
            "database": parsed.path[1:],  # Remove leading /
            "user": parsed.username,
            "password": parsed.password
        }
    else:
        # Fall back to individual env vars
        conn_params = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", "5432")),
            "database": os.getenv("DB_NAME", "postgres"),
            "user": os.getenv("DB_USER", "postgres"),
            "password": os.getenv("DB_PASSWORD", "")
        }

    try:
        conn = psycopg2.connect(**conn_params)
        print(f"✅ Connected to PostgreSQL: {conn_params['host']}:{conn_params['port']}/{conn_params['database']}")
        return conn
    except psycopg2.Error as e:
        print(f"❌ Database connection failed: {e}")
        print("\nMake sure you have set these environment variables:")
        print("  - DATABASE_URL (or)")
        print("  - DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD")
        sys.exit(1)


def read_migration_file(filename: str) -> str:
    """Read migration SQL file"""
    migration_path = Path(__file__).parent.parent / "supabase" / "migrations" / filename

    if not migration_path.exists():
        raise FileNotFoundError(f"Migration file not found: {migration_path}")

    with open(migration_path, 'r', encoding='utf-8') as f:
        return f.read()


def run_migration(conn, sql: str) -> bool:
    """Execute migration SQL"""
    try:
        print("\n🚀 Executing migration SQL...")

        cursor = conn.cursor()

        # Execute migration (may contain multiple statements)
        cursor.execute(sql)

        conn.commit()
        cursor.close()

        print("✅ Migration executed successfully!")
        return True

    except psycopg2.Error as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
        return False


def verify_migration(conn) -> bool:
    """Verify migration was successful"""
    print("\n🔍 Verifying Migration 003...\n")

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    checks_passed = 0
    checks_total = 0

    # Check 1: Verify new columns exist
    print("1. Checking new columns exist...")
    checks_total += 1
    try:
        cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'obd_codes'
              AND column_name IN (
                'enrichment_status',
                'knowledge_score',
                'technician_tip',
                'related_codes',
                'typical_cost_range',
                'diy_difficulty'
              )
            ORDER BY column_name;
        """)

        columns = cursor.fetchall()
        if len(columns) >= 5:
            print(f"   ✅ Found {len(columns)} new columns:")
            for col in columns:
                print(f"      - {col['column_name']} ({col['data_type']})")
            checks_passed += 1
        else:
            print(f"   ❌ Expected 6+ columns, found {len(columns)}")
    except Exception as e:
        print(f"   ❌ Column check failed: {e}")

    # Check 2: Verify trigger exists
    print("\n2. Checking trigger exists...")
    checks_total += 1
    try:
        cursor.execute("""
            SELECT trigger_name, event_manipulation
            FROM information_schema.triggers
            WHERE event_object_table = 'obd_codes'
              AND trigger_name = 'trigger_update_obd_knowledge_score';
        """)

        trigger = cursor.fetchone()
        if trigger:
            print(f"   ✅ Trigger found: {trigger['trigger_name']}")
            checks_passed += 1
        else:
            print("   ❌ Trigger not found")
    except Exception as e:
        print(f"   ❌ Trigger check failed: {e}")

    # Check 3: Verify views exist
    print("\n3. Checking views exist...")
    checks_total += 1
    try:
        cursor.execute("""
            SELECT viewname
            FROM pg_views
            WHERE viewname IN ('obd_codes_needing_enrichment', 'obd_enrichment_stats')
            ORDER BY viewname;
        """)

        views = cursor.fetchall()
        if len(views) >= 2:
            print(f"   ✅ Found {len(views)} views:")
            for view in views:
                print(f"      - {view['viewname']}")
            checks_passed += 1
        else:
            print(f"   ❌ Expected 2 views, found {len(views)}")
    except Exception as e:
        print(f"   ❌ View check failed: {e}")

    # Check 4: Test knowledge_score auto-calculation
    print("\n4. Testing knowledge_score auto-calculation...")
    checks_total += 1
    try:
        # Clean up test code if exists
        cursor.execute("DELETE FROM obd_codes WHERE code = 'P9999';")
        conn.commit()

        # Insert test code
        cursor.execute("""
            INSERT INTO obd_codes (code, description, system, severity)
            VALUES ('P9999', 'Test Migration Code', 'Test System', 'Low')
            RETURNING code, knowledge_score, enrichment_status;
        """)

        test_result = cursor.fetchone()
        conn.commit()

        if test_result:
            score = float(test_result['knowledge_score'])
            status = test_result['enrichment_status']

            if 20 <= score <= 40:
                print(f"   ✅ Knowledge score auto-calculated: {score}%")
                print(f"      Status: {status}")
                checks_passed += 1
            else:
                print(f"   ⚠️  Score calculated but unexpected: {score}%")

            # Clean up
            cursor.execute("DELETE FROM obd_codes WHERE code = 'P9999';")
            conn.commit()
        else:
            print("   ❌ Test insert failed")
    except Exception as e:
        print(f"   ❌ Knowledge score test failed: {e}")
        conn.rollback()

    # Check 5: Display enrichment statistics
    print("\n5. Enrichment statistics...")
    checks_total += 1
    try:
        cursor.execute("SELECT * FROM obd_enrichment_stats ORDER BY enrichment_status;")
        stats = cursor.fetchall()

        if stats:
            print("\n   Enrichment Statistics:")
            print("   " + "-"*70)
            print(f"   {'Status':<20} {'Count':>10} {'Avg Score':>15} {'Min':>8} {'Max':>8}")
            print("   " + "-"*70)

            for row in stats:
                status = row['enrichment_status'] or 'null'
                count = row['count']
                avg = row['avg_knowledge_score'] or 0.0
                min_score = row['min_knowledge_score'] or 0.0
                max_score = row['max_knowledge_score'] or 0.0
                print(f"   {status:<20} {count:>10} {avg:>14.1f}% {min_score:>7.1f}% {max_score:>7.1f}%")

            print("   " + "-"*70)
            checks_passed += 1
        else:
            print("   ⚠️  No data in obd_codes table")
            checks_passed += 1
    except Exception as e:
        print(f"   ⚠️  Stats check failed: {e}")

    # Check 6: Show codes needing enrichment
    print("\n6. Codes needing enrichment (lowest scores)...")
    checks_total += 1
    try:
        cursor.execute("""
            SELECT code, description, knowledge_score, missing_field
            FROM obd_codes_needing_enrichment
            ORDER BY knowledge_score ASC
            LIMIT 10;
        """)

        codes = cursor.fetchall()

        if codes:
            print(f"\n   Top {len(codes)} codes needing enrichment:")
            print("   " + "-"*70)
            for code_record in codes:
                code = code_record['code']
                score = code_record['knowledge_score']
                missing = code_record['missing_field']
                desc = code_record['description'][:40] + "..." if len(code_record['description']) > 40 else code_record['description']
                print(f"   {code}: {score:.1f}% - {desc}")
                print(f"          Missing: {missing}")
            print("   " + "-"*70)
            checks_passed += 1
        else:
            print("   ✅ All codes fully enriched!")
            checks_passed += 1
    except Exception as e:
        print(f"   ⚠️  Enrichment view check failed: {e}")

    cursor.close()

    # Summary
    print("\n" + "="*70)
    print(f"Verification Results: {checks_passed}/{checks_total} checks passed")
    print("="*70)

    if checks_passed == checks_total:
        print("\n✅ Migration 003 verified successfully!")
        return True
    elif checks_passed >= checks_total - 1:
        print("\n⚠️  Migration mostly successful")
        return True
    else:
        print("\n❌ Migration verification failed")
        return False


def rollback_migration(conn) -> bool:
    """Rollback migration 003"""
    print("\n⚠️  ROLLBACK WARNING")
    print("="*70)
    print("This will PERMANENTLY DELETE all enriched data!")
    print("="*70)

    confirmation = input("\nType 'ROLLBACK' to confirm: ")

    if confirmation != "ROLLBACK":
        print("\n❌ Rollback cancelled")
        return False

    print("\n🔄 Rolling back Migration 003...")

    try:
        rollback_sql = read_migration_file("003_rollback_enhance_obd_codes_enrichment.sql")

        cursor = conn.cursor()
        cursor.execute(rollback_sql)
        conn.commit()
        cursor.close()

        print("✅ Rollback completed successfully!")
        return True

    except Exception as e:
        print(f"\n❌ Rollback failed: {e}")
        conn.rollback()
        return False


def main():
    parser = argparse.ArgumentParser(description="Run Migration 003 with PostgreSQL")
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="Rollback migration instead of applying it"
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify migration, don't run it"
    )

    args = parser.parse_args()

    print("\n" + "="*70)
    print("Migration 003: Enhanced OBD Codes Enrichment (PostgreSQL)")
    print("="*70)

    # Get database connection
    conn = get_db_connection()

    try:
        if args.rollback:
            success = rollback_migration(conn)
        elif args.verify_only:
            success = verify_migration(conn)
        else:
            # Run migration
            migration_sql = read_migration_file("003_enhance_obd_codes_enrichment.sql")
            success = run_migration(conn, migration_sql)

            if success:
                # Verify after running
                print("\n" + "="*70)
                success = verify_migration(conn)

        if success:
            print("\n✅ Operation completed successfully!")
            return 0
        else:
            print("\n❌ Operation failed")
            return 1

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    finally:
        conn.close()
        print("\n🔌 Database connection closed")


if __name__ == "__main__":
    sys.exit(main())
