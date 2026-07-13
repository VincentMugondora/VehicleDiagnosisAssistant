#!/usr/bin/env python3
"""
Extract PostgreSQL connection string from Supabase URL

Usage: python scripts/get_supabase_connection.py
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings

def extract_db_connection():
    """Extract database connection info from Supabase URL"""

    if not settings.supabase_url:
        print("❌ SUPABASE_URL not found in .env")
        return None

    # Supabase URL format: https://PROJECT_ID.supabase.co
    # PostgreSQL connection format: postgresql://postgres:[PASSWORD]@db.PROJECT_ID.supabase.co:5432/postgres

    # Extract project ID from URL
    supabase_url = settings.supabase_url

    if "supabase.co" in supabase_url:
        project_id = supabase_url.replace("https://", "").replace(".supabase.co", "")

        print("\n" + "="*70)
        print("Supabase Connection Information")
        print("="*70)
        print(f"\nProject ID: {project_id}")
        print(f"Supabase URL: {supabase_url}")

        print("\n[!] To run the migration, you need the DATABASE PASSWORD")
        print("\nYou can find it in your Supabase Dashboard:")
        print("1. Go to: https://app.supabase.com/project/" + project_id + "/settings/database")
        print("2. Look for 'Database password' or 'Connection string'")
        print("3. Copy the password")

        print("\nOnce you have the password, set it as an environment variable:")
        print("\nWindows (PowerShell):")
        print('  $env:DB_PASSWORD="your-password-here"')
        print("\nWindows (cmd):")
        print('  set DB_PASSWORD=your-password-here')

        print("\nThen run:")
        print("  python scripts/run_migration_003_psycopg2.py")

        print("\n" + "="*70)

        # Try to construct connection string if password is available
        db_password = os.getenv("DB_PASSWORD") or os.getenv("SUPABASE_DB_PASSWORD")

        if db_password:
            db_host = f"db.{project_id}.supabase.co"
            db_port = "5432"
            db_name = "postgres"
            db_user = "postgres"

            connection_string = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

            print("\n[OK] Password found! Connection string ready.")
            print(f"\nDB_HOST: {db_host}")
            print(f"DB_PORT: {db_port}")
            print(f"DB_NAME: {db_name}")
            print(f"DB_USER: {db_user}")

            # Set environment variables for the migration script
            os.environ["DB_HOST"] = db_host
            os.environ["DB_PORT"] = db_port
            os.environ["DB_NAME"] = db_name
            os.environ["DB_USER"] = db_user
            os.environ["DB_PASSWORD"] = db_password

            return {
                "host": db_host,
                "port": db_port,
                "name": db_name,
                "user": db_user,
                "password": db_password,
                "connection_string": connection_string
            }
        else:
            print("\n[!] DB_PASSWORD not set in environment")
            return None
    else:
        print(f"❌ Unexpected Supabase URL format: {supabase_url}")
        return None

if __name__ == "__main__":
    extract_db_connection()
