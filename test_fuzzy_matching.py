"""
Test fuzzy matching edge cases for system diagram lookup.

Tests ambiguous cases and overlapping terms to verify match priority.
"""
import sys
from app.db.client import get_supabase_client
from app.repositories.system_diagram_repository import SystemDiagramRepository

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def setup_test_data(repo: SystemDiagramRepository):
    """
    Create test diagrams for edge case testing.

    Assumes these systems will be in your actual data.
    """
    # Note: This doesn't actually insert - just shows what we're testing against
    test_systems = [
        "catalytic converter",
        "oxygen sensor",
        "fuel system",
        "fuel injector",
        "egr valve",
        "ignition coil",
        "cooling system",
        "throttle body",
    ]

    print("="*70)
    print("TEST DATA SETUP")
    print("="*70)
    print("\nAssuming the following diagrams exist in system_diagrams table:")
    for i, system in enumerate(test_systems, 1):
        print(f"  {i}. {system}")
    print("\nIf these don't exist, add them manually first.")
    print("="*70)


def test_lookup(repo: SystemDiagramRepository, search_term: str, expected_match: str = None):
    """
    Test a single lookup and report which tier matched.

    Args:
        repo: Repository instance
        search_term: Term to search for
        expected_match: Expected system name (for verification)
    """
    print(f"\n{'─'*70}")
    print(f"🔍 Searching for: '{search_term}'")
    print(f"{'─'*70}")

    # Test exact match first
    exact = repo.get_by_system(search_term)
    if exact:
        print(f"✅ MATCH (Tier: EXACT)")
        print(f"   System: {exact.system}")
        print(f"   URL: {exact.image_url[:60]}...")
        if expected_match:
            assert exact.system.lower() == expected_match.lower(), \
                f"Expected '{expected_match}', got '{exact.system}'"
        return exact

    # If no exact match, try fuzzy
    print("   No exact match, trying fuzzy...")
    fuzzy = repo.get_by_system_fuzzy(search_term)

    if fuzzy:
        # Determine which tier matched by checking logs
        # We'll need to trace through the logic
        print(f"✅ MATCH (Tier: FUZZY - see details below)")
        print(f"   System: {fuzzy.system}")
        print(f"   URL: {fuzzy.image_url[:60]}...")

        # Try to determine match type
        search_lower = search_term.lower().strip()
        fuzzy_lower = fuzzy.system.lower()

        # Check synonym
        from app.repositories.system_diagram_repository import SYSTEM_SYNONYMS
        if search_lower in SYSTEM_SYNONYMS:
            synonyms = SYSTEM_SYNONYMS[search_lower]
            if any(syn.lower() == fuzzy_lower for syn in synonyms):
                print(f"   Match Type: SYNONYM")
                print(f"   Mapped: '{search_term}' → '{fuzzy.system}'")
        # Check substring
        elif search_lower in fuzzy_lower:
            print(f"   Match Type: SUBSTRING (search in system)")
            print(f"   Found: '{search_term}' inside '{fuzzy.system}'")
        elif fuzzy_lower in search_lower:
            print(f"   Match Type: CONTAINS (system in search)")
            print(f"   Found: '{fuzzy.system}' inside '{search_term}'")

        if expected_match:
            assert fuzzy.system.lower() == expected_match.lower(), \
                f"Expected '{expected_match}', got '{fuzzy.system}'"
        return fuzzy
    else:
        print("❌ NO MATCH FOUND")
        print("   This system has no diagram (expected for some systems)")
        return None


def test_ambiguous_cases():
    """
    Test potentially ambiguous search terms.

    Tests cases where multiple systems could match and verifies
    which one is actually returned.
    """
    print("\n" + "="*70)
    print("EDGE CASE TESTING: AMBIGUOUS TERMS")
    print("="*70)

    supabase = get_supabase_client()
    repo = SystemDiagramRepository(supabase)

    setup_test_data(repo)

    print("\n\n" + "="*70)
    print("TEST CASES")
    print("="*70)

    # Test Case 1: "fuel" - could match "fuel system" or "fuel injector"
    print("\n\n📋 TEST CASE 1: Ambiguous 'fuel'")
    print("Scenario: Search 'fuel' when both 'fuel system' and 'fuel injector' exist")
    print("Question: Which one gets returned?")
    result1 = test_lookup(repo, "fuel")

    # Test Case 2: "catalyst" - should map to "catalytic converter" via synonym
    print("\n\n📋 TEST CASE 2: Synonym 'catalyst'")
    print("Scenario: Search 'catalyst' (abbreviation)")
    print("Expected: Should find 'catalytic converter' via synonym map")
    result2 = test_lookup(repo, "catalyst", expected_match="catalytic converter")

    # Test Case 3: "o2 sensor" vs "oxygen sensor"
    print("\n\n📋 TEST CASE 3: Synonym 'o2 sensor'")
    print("Scenario: Search 'o2 sensor' when 'oxygen sensor' exists")
    print("Expected: Should find 'oxygen sensor' via synonym")
    result3 = test_lookup(repo, "o2 sensor", expected_match="oxygen sensor")

    # Test Case 4: "ignition" - could match "ignition coil" or "ignition system"
    print("\n\n📋 TEST CASE 4: Ambiguous 'ignition'")
    print("Scenario: Search 'ignition' (partial term)")
    print("Question: Does it find 'ignition coil' or 'ignition system'?")
    result4 = test_lookup(repo, "ignition")

    # Test Case 5: "cooling" - should find "cooling system"
    print("\n\n📋 TEST CASE 5: Partial 'cooling'")
    print("Scenario: Search 'cooling' when 'cooling system' exists")
    print("Expected: Should find 'cooling system' via substring or synonym")
    result5 = test_lookup(repo, "cooling", expected_match="cooling system")

    # Test Case 6: "egr" - abbreviation
    print("\n\n📋 TEST CASE 6: Abbreviation 'egr'")
    print("Scenario: Search 'egr' (common abbreviation)")
    print("Expected: Should find 'egr valve' via synonym")
    result6 = test_lookup(repo, "egr", expected_match="egr valve")

    # Test Case 7: Non-existent system
    print("\n\n📋 TEST CASE 7: Non-existent 'turbocharger'")
    print("Scenario: Search for system with no diagram")
    print("Expected: Should return None gracefully (not an error)")
    result7 = test_lookup(repo, "turbocharger")

    # Test Case 8: Very generic term "sensor"
    print("\n\n📋 TEST CASE 8: Very generic 'sensor'")
    print("Scenario: Search 'sensor' (could match many)")
    print("Question: Does it match anything? Which one?")
    result8 = test_lookup(repo, "sensor")

    # Summary
    print("\n\n" + "="*70)
    print("SUMMARY")
    print("="*70)

    results = {
        "fuel": result1,
        "catalyst": result2,
        "o2 sensor": result3,
        "ignition": result4,
        "cooling": result5,
        "egr": result6,
        "turbocharger": result7,
        "sensor": result8,
    }

    print("\nMatches found:")
    for term, result in results.items():
        if result:
            print(f"  ✅ '{term}' → '{result.system}'")
        else:
            print(f"  ❌ '{term}' → No match")

    print("\n" + "="*70)
    print("ANALYSIS")
    print("="*70)
    print("""
    POTENTIAL ISSUES IDENTIFIED:

    1. "fuel" ambiguity:
       - Could match "fuel system" OR "fuel injector" depending on which
         appears first in database iteration (substring match)
       - FIX: Add explicit synonym "fuel" → ["fuel system"] to prioritize

    2. "ignition" ambiguity:
       - Could match "ignition coil" OR "ignition system"
       - FIX: Add synonym "ignition" → ["ignition coil"] (more common)

    3. "sensor" is too generic:
       - Could match any system with "sensor" in name
       - Should NOT match anything specific
       - Current behavior: Matches first "sensor" system found
       - FIX: Don't add synonym for "sensor" alone - require specificity

    RECOMMENDATION:
    - Tighten substring matching to require minimum search term length (e.g., 4+ chars)
    - Add priority to synonym map (prefer more specific matches)
    - Consider exact-only mode for ambiguous terms
    """)


if __name__ == "__main__":
    try:
        test_ambiguous_cases()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
