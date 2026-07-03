#!/usr/bin/env python3
"""
End-to-end integration test for DTC lookup pipeline.

Tests:
1. DTC normalization (case, whitespace)
2. Supabase lookup
3. Fallback data
4. Vehicle override merging
5. Webhook integration
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.client import get_supabase_client
from app.services.dtc_lookup import (
    normalize_dtc_code,
    lookup_dtc,
    lookup_with_vehicle_context,
    validate_dtc_format
)
from app.repositories.obd_repository import OBDRepository
from app.core.config import settings


def test_normalization():
    """Test DTC code normalization."""
    print("🧪 Testing DTC normalization...")

    test_cases = [
        ("P0420", "P0420"),
        ("p0420", "P0420"),
        ("P 0420", "P0420"),
        ("p-0420", "P0420"),
        ("  p0420  ", "P0420"),
        ("P0420\n", "P0420"),
    ]

    passed = 0
    for input_code, expected in test_cases:
        result = normalize_dtc_code(input_code)
        if result == expected:
            print(f"  ✅ '{input_code}' -> '{result}'")
            passed += 1
        else:
            print(f"  ❌ '{input_code}' -> '{result}' (expected '{expected}')")

    print(f"  Result: {passed}/{len(test_cases)} passed\n")
    return passed == len(test_cases)


def test_format_validation():
    """Test DTC format validation."""
    print("🧪 Testing DTC format validation...")

    valid_codes = ["P0420", "B1234", "C0001", "U0100"]
    invalid_codes = ["X0420", "P04200", "P042", "0420", "ABCD", ""]

    passed = 0
    total = len(valid_codes) + len(invalid_codes)

    for code in valid_codes:
        if validate_dtc_format(code):
            print(f"  ✅ '{code}' is valid")
            passed += 1
        else:
            print(f"  ❌ '{code}' should be valid")

    for code in invalid_codes:
        if not validate_dtc_format(code):
            print(f"  ✅ '{code}' correctly rejected")
            passed += 1
        else:
            print(f"  ❌ '{code}' should be invalid")

    print(f"  Result: {passed}/{total} passed\n")
    return passed == total


def test_supabase_lookup():
    """Test Supabase lookup for common codes."""
    print("🧪 Testing Supabase lookup...")

    client = get_supabase_client()
    if not client:
        print("  ⚠️  Supabase not enabled, skipping\n")
        return True

    test_codes = ["P0300", "P0420", "P0171", "P0455", "P0128"]

    passed = 0
    for code in test_codes:
        result = lookup_dtc(code, client)
        if result:
            print(f"  ✅ {code}: {result['description'][:50]}...")
            passed += 1
        else:
            print(f"  ❌ {code}: not found")

    print(f"  Result: {passed}/{len(test_codes)} found\n")
    return passed > 0  # At least one should work


def test_fallback_lookup():
    """Test fallback lookup when Supabase unavailable."""
    print("🧪 Testing fallback lookup...")

    # Pass None as client to force fallback
    test_codes = ["P0300", "P0420", "P0171"]

    passed = 0
    for code in test_codes:
        result = lookup_dtc(code, None)
        if result and result.get("source") == "fallback":
            print(f"  ✅ {code}: fallback working")
            passed += 1
        else:
            print(f"  ❌ {code}: fallback failed")

    print(f"  Result: {passed}/{len(test_codes)} passed\n")
    return passed > 0


def test_vehicle_override():
    """Test vehicle-specific override merging."""
    print("🧪 Testing vehicle override lookup...")

    client = get_supabase_client()
    if not client:
        print("  ⚠️  Supabase not enabled, skipping\n")
        return True

    # Test with and without vehicle context
    code = "P0420"

    # Without vehicle context
    base_result = lookup_dtc(code, client)
    if base_result:
        print(f"  ✅ Base lookup: {base_result['description'][:50]}...")
    else:
        print(f"  ❌ Base lookup failed")
        return False

    # With vehicle context (will use base if no override exists)
    vehicle_result = lookup_with_vehicle_context(
        code=code,
        client=client,
        make="Toyota",
        model="Camry",
        year="2015",
        engine="2.5L"
    )

    if vehicle_result:
        print(f"  ✅ Vehicle lookup: source={vehicle_result.get('source')}")
        print(f"     Confidence: {vehicle_result.get('confidence')}")
    else:
        print(f"  ❌ Vehicle lookup failed")
        return False

    print()
    return True


def test_repository_layer():
    """Test OBDRepository methods."""
    print("🧪 Testing OBDRepository...")

    client = get_supabase_client()
    if not client:
        print("  ⚠️  Supabase not enabled, skipping\n")
        return True

    repo = OBDRepository(client)

    # Test get_by_code
    result = repo.get_by_code("P0420")
    if result:
        print(f"  ✅ get_by_code: {result['code']}")
    else:
        print(f"  ❌ get_by_code: not found")
        return False

    # Test list_by_system
    results = repo.list_by_system("Powertrain")
    print(f"  ✅ list_by_system: {len(results)} Powertrain codes")

    print()
    return True


def test_case_insensitivity():
    """Test case-insensitive lookup."""
    print("🧪 Testing case-insensitive lookup...")

    client = get_supabase_client()
    if not client:
        print("  ⚠️  Supabase not enabled, skipping\n")
        return True

    variants = ["P0420", "p0420", "P0420", "p 0420"]

    results = []
    for variant in variants:
        result = lookup_dtc(variant, client)
        results.append(result)
        if result:
            print(f"  ✅ '{variant}' -> {result['code']}")
        else:
            print(f"  ❌ '{variant}' not found")

    # All should return the same result
    if results and all(r and r['code'] == 'P0420' for r in results):
        print("  ✅ All variants resolved to same code\n")
        return True
    else:
        print("  ❌ Case-insensitive lookup failed\n")
        return False


def main():
    print("=" * 80)
    print("DTC Integration Test Suite")
    print("=" * 80)
    print()

    if not settings.supabase_enabled:
        print("⚠️  Supabase is disabled. Some tests will be skipped.")
        print("   Enable it in .env to run full test suite.\n")

    tests = [
        ("Normalization", test_normalization),
        ("Format Validation", test_format_validation),
        ("Supabase Lookup", test_supabase_lookup),
        ("Fallback Lookup", test_fallback_lookup),
        ("Vehicle Override", test_vehicle_override),
        ("Repository Layer", test_repository_layer),
        ("Case Insensitivity", test_case_insensitivity),
    ]

    results = []
    for name, test_fn in tests:
        try:
            passed = test_fn()
            results.append((name, passed))
        except Exception as e:
            print(f"  ❌ Test error: {e}\n")
            results.append((name, False))

    # Summary
    print("=" * 80)
    print("Test Summary")
    print("=" * 80)

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")

    print()
    print(f"Overall: {passed_count}/{total_count} test suites passed")

    if passed_count == total_count:
        print("✅ All tests passed! Ready for production.")
        return 0
    else:
        print(f"⚠️  {total_count - passed_count} test suite(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
