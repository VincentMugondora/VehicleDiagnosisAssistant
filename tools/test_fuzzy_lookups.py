#!/usr/bin/env python3
"""
Test fuzzy matching for various system name variations.
"""
import sys
from app.db.client import get_supabase_client
from app.repositories.system_diagram_repository import SystemDiagramRepository

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

TEST_QUERIES = [
    # Exact matches
    'catalytic converter',
    'oxygen sensor',
    'egr valve',

    # Common abbreviations
    'cat',
    'o2 sensor',
    'egr',
    'maf',

    # Variations
    'fuel',
    'ignition',
    'evap',
    'throttle',

    # Partial matches
    'catalyst',
    'spark',
    'battery',
    'transmission'
]


def test_fuzzy_lookups():
    """Test fuzzy matching for various queries"""
    print("\n🔍 Testing fuzzy matching for system diagrams...")
    print("="*70)

    supabase = get_supabase_client()
    if not supabase:
        print("❌ Failed to connect to Supabase")
        sys.exit(1)

    repo = SystemDiagramRepository(supabase)

    found_count = 0
    not_found_count = 0

    for query in TEST_QUERIES:
        result = repo.get_by_system_fuzzy(query)

        if result:
            print(f"✅ '{query}' → '{result.system}'")
            found_count += 1
        else:
            print(f"❌ '{query}' → NOT FOUND")
            not_found_count += 1

    print("="*70)
    print(f"Found: {found_count}/{len(TEST_QUERIES)}")
    print(f"Not found: {not_found_count}/{len(TEST_QUERIES)}")
    print("="*70)


if __name__ == "__main__":
    test_fuzzy_lookups()
