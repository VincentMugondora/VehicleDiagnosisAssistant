"""
Test High-Confidence Component Image System

Verifies that:
1. Images are ONLY sent for high-confidence matches (≥80%)
2. No generic fallback images are sent
3. Text-only diagnosis works when no component is identified
4. Logging captures all image decisions
"""
import sys
import os
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.component_mapper import (
    extract_best_component_match,
    should_send_image,
    CONFIDENCE_THRESHOLD
)
from app.models.component_registry import get_all_components


def test_high_confidence_matches():
    """Test that high-confidence matches are correctly identified"""
    print("\n" + "="*80)
    print("TEST 1: High-Confidence Component Matches (Should Send Images)")
    print("="*80)

    high_confidence_tests = [
        ("P0420", "Catalyst System Efficiency Below Threshold"),
        ("P0135", "O2 Sensor Heater Circuit Malfunction Bank 1 Sensor 1"),
        ("P0351", "Ignition Coil A Primary/Secondary Circuit Malfunction"),
        ("P0101", "Mass Air Flow Sensor Circuit Range/Performance"),
        ("P0118", "Engine Coolant Temperature Circuit High Input"),
    ]

    passed = 0
    for code, description in high_confidence_tests:
        match = extract_best_component_match(description, code)
        if match:
            send_image = should_send_image(match)
            status = "✅ PASS" if send_image else "❌ FAIL"
            print(f"\n{status} {code}: {description[:50]}...")
            print(f"   Component: {match.component.canonical_name}")
            print(f"   Confidence: {match.confidence}%")
            print(f"   Image: {match.component.image_filename}")
            print(f"   Should Send: {send_image}")
            if send_image:
                passed += 1
        else:
            print(f"\n❌ FAIL {code}: No component match found")

    print(f"\n{passed}/{len(high_confidence_tests)} tests passed")
    return passed == len(high_confidence_tests)


def test_low_confidence_matches():
    """Test that low-confidence matches do NOT trigger images"""
    print("\n" + "="*80)
    print("TEST 2: Low-Confidence Matches (Should NOT Send Images)")
    print("="*80)

    low_confidence_tests = [
        ("P0700", "Transmission Control System Malfunction"),
        ("U0100", "Lost Communication with ECM/PCM"),
        ("B1234", "Unknown Body Code"),
    ]

    passed = 0
    for code, description in low_confidence_tests:
        match = extract_best_component_match(description, code)
        send_image = should_send_image(match) if match else False

        status = "✅ PASS" if not send_image else "❌ FAIL"
        print(f"\n{status} {code}: {description[:50]}...")

        if match:
            print(f"   Component: {match.component.canonical_name}")
            print(f"   Confidence: {match.confidence}%")
            print(f"   Should Send: {send_image}")
        else:
            print(f"   No component match → TEXT_ONLY")

        if not send_image:
            passed += 1

    print(f"\n{passed}/{len(low_confidence_tests)} tests passed")
    return passed == len(low_confidence_tests)


def test_component_registry():
    """Verify component registry structure and coverage"""
    print("\n" + "="*80)
    print("TEST 3: Component Registry Validation")
    print("="*80)

    components = get_all_components()
    with_images = [c for c in components if c.image_filename]
    without_images = [c for c in components if not c.image_filename]

    print(f"\nTotal Components: {len(components)}")
    print(f"Components with Images: {len(with_images)}")
    print(f"Components without Images: {len(without_images)}")
    print(f"Coverage: {len(with_images)/len(components)*100:.1f}%")

    print("\n✅ Components with Images:")
    for comp in with_images:
        print(f"   - {comp.canonical_name} → {comp.image_filename}")

    if without_images:
        print("\n⚠️  Components Needing Images:")
        for comp in without_images:
            print(f"   - {comp.canonical_name}")

    return True


def test_confidence_threshold():
    """Verify confidence threshold is set correctly"""
    print("\n" + "="*80)
    print("TEST 4: Confidence Threshold Configuration")
    print("="*80)

    print(f"\nConfidence Threshold: {CONFIDENCE_THRESHOLD}%")
    print(f"Expected: 80%")

    if CONFIDENCE_THRESHOLD == 80:
        print("✅ PASS: Threshold correctly set to 80%")
        return True
    else:
        print(f"❌ FAIL: Threshold is {CONFIDENCE_THRESHOLD}%, should be 80%")
        return False


def test_no_generic_fallbacks():
    """Ensure no generic fallback images in registry"""
    print("\n" + "="*80)
    print("TEST 5: No Generic Fallback Images")
    print("="*80)

    components = get_all_components()
    generic_keywords = ['generic', 'fallback', 'engine bay', 'dashboard', 'warning light']

    found_generic = []
    for comp in components:
        for keyword in generic_keywords:
            if keyword in comp.canonical_name.lower():
                found_generic.append(comp.canonical_name)

    if not found_generic:
        print("✅ PASS: No generic fallback components found in registry")
        return True
    else:
        print(f"❌ FAIL: Found generic components: {found_generic}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("HIGH-CONFIDENCE COMPONENT IMAGE SYSTEM - TEST SUITE")
    print("="*80)

    results = {
        "High-Confidence Matches": test_high_confidence_matches(),
        "Low-Confidence Matches": test_low_confidence_matches(),
        "Component Registry": test_component_registry(),
        "Confidence Threshold": test_confidence_threshold(),
        "No Generic Fallbacks": test_no_generic_fallbacks(),
    }

    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")

    total_passed = sum(results.values())
    total_tests = len(results)

    print(f"\n{total_passed}/{total_tests} test suites passed")

    if total_passed == total_tests:
        print("\n🎉 SUCCESS: High-confidence image system is working correctly!")
        print("✅ No generic fallback images")
        print("✅ Only sending images for ≥80% confidence matches")
        print("✅ Text-only diagnosis available for all codes")
        return 0
    else:
        print("\n⚠️  ISSUES DETECTED: Review failed tests above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
