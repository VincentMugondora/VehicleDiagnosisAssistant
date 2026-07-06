#!/usr/bin/env python3
"""
List all system diagrams in the database.
"""
import sys
from app.db.client import get_supabase_client

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def list_all_diagrams():
    """List all system diagrams"""
    supabase = get_supabase_client()
    if not supabase:
        print("Failed to connect to Supabase")
        sys.exit(1)

    result = supabase.table('system_diagrams').select('system', count='exact').order('system').execute()

    print(f'\nTotal diagrams in database: {len(result.data)}')
    print('\nSystems with diagrams:')
    print('='*70)
    for i, row in enumerate(result.data, 1):
        print(f'{i:2}. {row["system"]}')
    print('='*70)


if __name__ == "__main__":
    list_all_diagrams()
