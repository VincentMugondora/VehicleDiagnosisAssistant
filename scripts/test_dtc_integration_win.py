#!/usr/bin/env python3
"""
End-to-end integration test for DTC lookup pipeline (Windows-compatible).
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
    print("[TEST] DTC normalization...")

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
            print(f"  [PASS] '{input_code}' -> '{result}'")
            passed += 1
        else:
            print(f"  [FAIL] '{input_code}' -> '{result}' (expected '{expected}')")

    print(f"  Result: {passed}/{len(test_cases)} passed\n")
    return passed == len(test_cases)


def test_format_validation():
    print("[TEST] DTC format validation...")

    valid_codes = ["P0420", "B1234", "C0001", "U0100"]
    invalid_codes = ["X0420", "P04200", "P042", "0420", "ABCD", ""]

    passed = 0
    total = len(valid_codes) + len(invalid_codes)

    for code in valid_codes:
        if validate_dtc_format(code):
            print(f"  [PASS] '{code}' is valid")
            passed += 1
        else:
            print(f"  [FAIL] '{code}' should be valid")

    for code in invalid_codes:
        if not validate_dtc_format(code):
            print(f"  [PASS] '{code}' correctly rejected")
            passed += 1
        else:
            print(f"  [FAIL] '{code}' should be invalid")

    print(f"  Result: {passed}/{total} passed\n")
    return passed == total


def test_supabase_lookup():
    print("[TEST] Supabase lookup...")

    client = get_supabase_client()
    if not client:
        print("  [SKIP] Supabase not enabled\n")
        return True

    test_codes = ["P0300", "P0420", "P0171", "P0455", "P0128"]

    passed = 0
    for code in test_codes:
        result = lookup_dtc(code, client)
        if result:
            print(f"  [PASS] {code}: {result['description'][:50]}...")
            passed += 1
        else:
            print(f"  [FAIL] {code}: not found")

    print(f"  Result: {passed}/{len(test_codes)} found\n")
    return passed > 0


def test_fallback_lookup():
    print("[TEST] Fallback lookup...")

    test_codes = ["P0300", "P0420", "P0171"]

    passed = 0
    for code in test_codes:
        result = lookup_dtc(code, None)
        if result and result.get("source") == "fallback":
            print(f"  [PASS] {code}: fallback working")
            passed += 1
        else:
            print(f"  [FAIL] {code}: fallback failed")

    print(f"  Result: {passed}/{len(test_codes)} passed\n")
    return passed > 0


def test_vehicle_override():
    print("[TEST] Vehicle override lookup...")

    client = get_supabase_client()
    if not client:
        print("  [SKIP] Supabase not enabled\n")
        return True

    code = "P0420"

    base_result = lookup_dtc(code, client)
    if base_result:
        print(f"  [PASS] Base lookup: {base_result['description'][:50]}...")
    else:
        print(f"  [FAIL] Base lookup failed")
        return False

    vehicle_result = lookup_with_vehicle_context(
        code=code,
        client=client,
        make="Toyota",
        model="Camry",
        year="2015",
        engine="2.5L"
    )

    if vehicle_result:
        print(f"  [PASS] Vehicle lookup: source={vehicle_result.get('source')}")
        print(f"     Confidence: {vehicle_result.get('confidence')}")
    else:
        print(f"  [FAIL] Vehicle lookup failed")
        return False

    print()
    return True


def test_repository_layer():
    print("[TEST] OBDRepository...")

    client = get_supabase_client()
    if not client:
        print("  [SKIP] Supabase not enabled\n")
        return True

    repo = OBDRepository(client)

    result = repo.get_by_code("P0420")
    if result:
        print(f"  [PASS] get_by_code: {result['code']}")
    else:
        print(f"  [FAIL] get_by_code: not found")
        return False

    results = repo.list_by_system("Powertrain")
    print(f"  [PASS] list_by_system: {len(results)} Powertrain codes")

    print()
    return True


def test_case_insensitivity():
    print("[TEST] Case-insensitive lookup...")

    client = get_supabase_client()
    if not client:
        print("  [SKIP] Supabase not enabled\n")
        return True

    variants = ["P0420", "p0420", "P0420", "p 0420"]

    results = []
    for variant in variants:
        result = lookup_dtc(variant, client)
        results.append(result)
        if result:
            print(f"  [PASS] '{variant}' -> {result['code']}")
        else:
            print(f"  [FAIL] '{variant}' not found")

    if results and all(r and r['code'] == 'P0420' for r in results):
        print("  [PASS] All variants resolved to same code\n")
        return True
    else:
        print("  [FAIL] Case-insensitive lookup failed\n")
        return False


def main():
    print("=" * 80)
    print("DTC Integration Test Suite")
    print("=" * 80)
    print()

    if not settings.supabase_enabled:
        print("[WARN] Supabase is disabled. Some tests will be skipped.\n")

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
            print(f"  [ERROR] Test error: {e}\n")
            results.append((name, False))

    print("=" * 80)
    print("Test Summary")
    print("=" * 80)

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status}: {name}")

    print()
    print(f"Overall: {passed_count}/{total_count} test suites passed")

    if passed_count == total_count:
        print("[SUCCESS] All tests passed! Ready for production.")
        return 0
    else:
        print(f"[WARNING] {total_count - passed_count} test suite(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
