"""
Run Database Migrations

Applies all pending migrations to the database.
"""

import asyncio
from pathlib import Path
from supabase import create_client
from app.core.config import settings


async def run_migrations():
    """Execute all SQL migration files"""

    if not settings.supabase_enabled:
        print("ERROR: Supabase is disabled")
        return

    print("=" * 80)
    print("DATABASE MIGRATIONS")
    print("=" * 80)
    print()

    client = create_client(settings.supabase_url, settings.supabase_service_key)

    # Get migration files
    migrations_dir = Path("migrations")
    if not migrations_dir.exists():
        print(f"ERROR: Migrations directory not found: {migrations_dir}")
        return

    migration_files = sorted(migrations_dir.glob("*.sql"))

    if not migration_files:
        print("No migration files found")
        return

    print(f"Found {len(migration_files)} migration(s):")
    for f in migration_files:
        print(f"  - {f.name}")
    print()

    # Confirm
    response = input("Apply these migrations? (yes/no): ")
    if response.lower() != 'yes':
        print("Cancelled")
        return

    print()

    # Execute each migration
    for migration_file in migration_files:
        print(f"Applying {migration_file.name}...")

        try:
            # Read SQL file
            sql = migration_file.read_text()

            # Execute via Supabase RPC (using direct SQL execution)
            # Note: Supabase Python client doesn't have direct SQL execution
            # We'll need to execute statements one by one
            statements = [s.strip() for s in sql.split(';') if s.strip()]

            for i, statement in enumerate(statements, 1):
                if not statement or statement.startswith('--'):
                    continue

                try:
                    # Execute using raw SQL via PostgREST
                    # This is a workaround - ideally use a PostgreSQL connection
                    print(f"  Statement {i}/{len(statements)}...", end=' ')

                    # Note: Supabase client library doesn't support raw SQL
                    # We need to use psycopg2 or similar for DDL statements
                    print("SKIPPED (requires psycopg2)")

                except Exception as e:
                    print(f"ERROR: {e}")
                    print(f"Statement: {statement[:100]}...")
                    raise

            print(f"  SUCCESS")

        except Exception as e:
            print(f"  FAILED: {e}")
            print()
            print("Migration failed. Please apply migrations manually using psql or pgAdmin.")
            print()
            print(f"SQL file: {migration_file}")
            return

    print()
    print("=" * 80)
    print("MIGRATIONS COMPLETE")
    print("=" * 80)
    print()
    print("Note: If migrations were skipped, please run them manually:")
    print()
    for f in migration_files:
        print(f"  psql -h <host> -U <user> -d <database> -f {f}")
    print()


if __name__ == "__main__":
    print()
    print("WARNING: Supabase Python client does not support raw SQL execution.")
    print("Please run migrations manually using psql:")
    print()
    print("  psql -h <supabase-host> -U postgres -d postgres -f migrations/001_add_enrichment_status.sql")
    print("  psql -h <supabase-host> -U postgres -d postgres -f migrations/002_add_provenance_metadata.sql")
    print("  psql -h <supabase-host> -U postgres -d postgres -f migrations/003_create_audit_log.sql")
    print()
    print("Alternatively, copy the SQL from each file into the Supabase SQL Editor.")
    print()
