"""
Run database migration via Supabase SQL Editor.

Since PostgREST doesn't allow DDL via API, this script provides
instructions for running migrations manually.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings

def main():
    migration_file = Path(__file__).parent.parent / 'migrations' / 'add_system_diagrams_table.sql'

    print("="*80)
    print("DATABASE MIGRATION REQUIRED")
    print("="*80)
    print("\nThe 'system_diagrams' table does not exist yet.")
    print("\nTo create it, run the migration SQL via Supabase Dashboard:")
    print("\n1. Open Supabase Dashboard:")
    print(f"   {settings.supabase_url.replace('https://', 'https://app.supabase.com/project/')}")
    print("\n2. Navigate to: SQL Editor (left sidebar)")
    print("\n3. Click 'New Query'")
    print(f"\n4. Copy the contents of: {migration_file}")
    print("\n5. Paste into SQL Editor and click 'Run'")
    print("\n" + "="*80)
    print("\nMIGRATION SQL:")
    print("="*80)

    with open(migration_file, 'r') as f:
        print(f.read())

    print("\n" + "="*80)
    print("After running the migration, re-run the import script.")
    print("="*80)

if __name__ == "__main__":
    main()
