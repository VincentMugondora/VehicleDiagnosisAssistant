"""
Database setup script - Creates missing payment tables in Supabase
"""
from supabase import create_client
from app.core.config import settings
import sys


def setup_payment_tables():
    """Create payment-related tables in Supabase"""

    print("="*60)
    print("DATABASE SETUP - Payment Tables")
    print("="*60)

    # Connect to Supabase
    print(f"\n[1/4] Connecting to Supabase...")
    print(f"   URL: {settings.supabase_url}")

    try:
        supabase = create_client(
            settings.supabase_url,
            settings.supabase_service_key
        )
        print("   [OK] Connected")
    except Exception as e:
        print(f"   [ERROR] Connection failed: {e}")
        return False

    # Read SQL migration
    print(f"\n[2/4] Reading migration file...")
    try:
        with open("migrations/add_payments_tables.sql", "r") as f:
            sql_content = f.read()
        print(f"   [OK] Read {len(sql_content)} characters")
    except Exception as e:
        print(f"   [ERROR] Failed to read migration: {e}")
        return False

    # Execute SQL
    print(f"\n[3/4] Creating tables...")
    print("   - transactions")
    print("   - subscriptions")
    print("   - user_usage")

    try:
        # Note: Supabase Python client doesn't support direct SQL execution
        # User must run this manually in SQL Editor
        print("\n   [INFO] Cannot execute SQL directly via Python client")
        print("   [ACTION REQUIRED] Please run the SQL manually:")
        print("\n" + "="*60)
        print("INSTRUCTIONS:")
        print("="*60)
        print("1. Open Supabase Dashboard:")
        print("   https://supabase.com/dashboard/project/yalpyodkymdkgkridtom")
        print("\n2. Go to SQL Editor (left sidebar)")
        print("\n3. Click 'New query'")
        print("\n4. Copy and paste the contents of:")
        print("   migrations/add_payments_tables.sql")
        print("\n5. Click 'Run'")
        print("\n6. Verify tables created:")
        print("   SELECT * FROM subscriptions LIMIT 1;")
        print("="*60)

    except Exception as e:
        print(f"   [ERROR] Failed to create tables: {e}")
        return False

    # Check if tables exist
    print(f"\n[4/4] Verifying tables...")
    try:
        # Try to query each table
        for table in ['transactions', 'subscriptions', 'user_usage']:
            try:
                result = supabase.table(table).select("*").limit(1).execute()
                print(f"   [OK] Table '{table}' exists")
            except Exception as e:
                print(f"   [MISSING] Table '{table}' not found")
                print(f"      Error: {e}")
    except Exception as e:
        print(f"   [ERROR] Verification failed: {e}")

    print("\n" + "="*60)
    print("SETUP INSTRUCTIONS DISPLAYED ABOVE")
    print("="*60)
    print("\nAfter running the SQL, restart your backend:")
    print("   .\\start_backend.bat")
    print("="*60 + "\n")

    return True


if __name__ == "__main__":
    success = setup_payment_tables()
    sys.exit(0 if success else 1)
