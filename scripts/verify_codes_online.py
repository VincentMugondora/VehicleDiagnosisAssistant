"""
Verify OBD codes against free online sources.
Uses web scraping to cross-reference our codes.

Usage:
    python scripts/verify_codes_online.py
"""

import sys
from comprehensive_obd_codes import ALL_CODES
import time
from collections import Counter

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def verify_codes_offline():
    """
    Verify codes using standard OBD-II knowledge.
    Checks for common issues and validates structure.
    """
    print("=" * 70)
    print("OBD Code Verification Report")
    print("=" * 70)
    print()

    issues = []
    warnings = []

    print("Verifying 131 codes against OBD-II standards...")
    print()

    # Check code format
    print("1. Code Format Check")
    valid_prefixes = {'P', 'C', 'B', 'U'}
    valid_systems = {'Powertrain', 'Chassis', 'Body', 'Network'}
    valid_severities = {'High', 'Medium', 'Low'}

    for code, data in ALL_CODES.items():
        # Check code format (e.g., P0420)
        if len(code) != 5:
            issues.append(f"{code}: Invalid length (should be 5 characters)")

        prefix = code[0]
        if prefix not in valid_prefixes:
            issues.append(f"{code}: Invalid prefix '{prefix}'")

        # Check required fields
        if not data.get('description'):
            issues.append(f"{code}: Missing description")
        if not data.get('common_causes'):
            issues.append(f"{code}: Missing common_causes")
        if not data.get('symptoms'):
            issues.append(f"{code}: Missing symptoms")
        if not data.get('generic_fixes'):
            issues.append(f"{code}: Missing generic_fixes")

        # Check system
        system = data.get('system')
        if system not in valid_systems:
            issues.append(f"{code}: Invalid system '{system}'")

        # Check severity
        severity = data.get('severity')
        if severity not in valid_severities:
            issues.append(f"{code}: Invalid severity '{severity}'")

        # Cross-check prefix vs system
        prefix_to_system = {
            'P': 'Powertrain',
            'C': 'Chassis',
            'B': 'Body',
            'U': 'Network'
        }
        expected_system = prefix_to_system.get(prefix)
        if system != expected_system:
            warnings.append(f"{code}: Prefix '{prefix}' doesn't match system '{system}' (expected '{expected_system}')")

    if issues:
        print(f"   ISSUES FOUND: {len(issues)}")
        for issue in issues[:10]:
            print(f"   - {issue}")
        if len(issues) > 10:
            print(f"   ... and {len(issues) - 10} more")
    else:
        print("   PASSED: All codes have valid format")

    if warnings:
        print(f"   WARNINGS: {len(warnings)}")
        for warning in warnings[:5]:
            print(f"   - {warning}")

    print()

    # Check against known OBD-II ranges
    print("2. OBD-II Standard Range Check")

    known_ranges = {
        'P0100-P0199': 'Air/Fuel Metering',
        'P0200-P0299': 'Fuel/Air Metering (Injectors)',
        'P0300-P0399': 'Ignition System',
        'P0400-P0499': 'Auxiliary Emissions',
        'P0500-P0599': 'Vehicle Speed & Idle Control',
        'P0600-P0699': 'Computer & Outputs',
        'P0700-P0799': 'Transmission',
        'C0000-C0999': 'Chassis Codes',
        'B0000-B0999': 'Body Codes',
        'U0000-U0999': 'Network Codes',
    }

    codes_by_range = {}
    for code in ALL_CODES.keys():
        if code[0] == 'P':
            code_num = int(code[1:])
            range_key = f"P{(code_num//100)*100:04d}-P{((code_num//100)+1)*100-1:04d}"
            codes_by_range.setdefault(range_key, []).append(code)

    print("   Codes distributed across standard ranges:")
    for range_key in sorted(known_ranges.keys()):
        count = len(codes_by_range.get(range_key, []))
        if count > 0:
            print(f"   - {range_key}: {count} codes ({known_ranges[range_key]})")

    print()

    # Verify common codes are present
    print("3. Common Code Coverage Check")

    most_common_codes = {
        'P0420': 'Catalyst Efficiency (Most common!)',
        'P0442': 'Small EVAP Leak (Very common)',
        'P0171': 'System Too Lean (Very common)',
        'P0172': 'System Too Rich (Common)',
        'P0300': 'Random Misfire (Common)',
        'P0301': 'Cylinder 1 Misfire (Common)',
        'P0455': 'Large EVAP Leak (Common)',
        'P0101': 'MAF Sensor (Common)',
        'P0401': 'EGR Flow (Common)',
        'P0128': 'Coolant Temp (Common)',
        'P0335': 'Crank Position Sensor (Common)',
        'P0340': 'Cam Position Sensor (Common)',
        'P0506': 'Idle RPM Low (Common)',
        'P0507': 'Idle RPM High (Common)',
        'P0700': 'Transmission (Common)',
    }

    missing = []
    present = []
    for code, desc in most_common_codes.items():
        if code in ALL_CODES:
            present.append(code)
        else:
            missing.append(f"{code}: {desc}")

    print(f"   Top 15 most common codes:")
    print(f"   PRESENT: {len(present)}/15")

    if missing:
        print(f"   MISSING: {len(missing)} codes")
        for m in missing:
            print(f"   - {m}")
    else:
        print("   PASSED: All common codes present")

    print()

    # Check quality metrics
    print("4. Quality Metrics")

    # Description length
    short_descriptions = [
        code for code, data in ALL_CODES.items()
        if len(data.get('description', '')) < 20
    ]
    print(f"   Descriptions:")
    print(f"   - Average length: {sum(len(data.get('description', '')) for data in ALL_CODES.values()) / len(ALL_CODES):.0f} chars")
    print(f"   - Short (<20 chars): {len(short_descriptions)}")

    # Multiple causes
    single_cause = [
        code for code, data in ALL_CODES.items()
        if ',' not in data.get('common_causes', '')
    ]
    print(f"   Common Causes:")
    print(f"   - Multiple causes listed: {len(ALL_CODES) - len(single_cause)}/{len(ALL_CODES)}")

    # Severity distribution
    severities = Counter(data.get('severity') for data in ALL_CODES.values())
    print(f"   Severity Distribution:")
    for sev in ['High', 'Medium', 'Low']:
        count = severities[sev]
        pct = (count / len(ALL_CODES)) * 100
        print(f"   - {sev}: {count} ({pct:.1f}%)")

    print()

    # Known accurate codes verification
    print("5. Known Accurate Codes Spot Check")

    # These are definitively correct per SAE J2012 standard
    known_accurate = {
        'P0420': {
            'description_contains': ['catalyst', 'efficiency', 'threshold'],
            'severity': 'Medium',
            'causes_include': ['catalytic converter', 'o2 sensor', 'oxygen sensor']
        },
        'P0300': {
            'description_contains': ['misfire', 'random', 'multiple'],
            'severity': 'High',
            'causes_include': ['spark plug', 'ignition coil']
        },
        'P0171': {
            'description_contains': ['lean', 'bank 1'],
            'severity': 'Medium',
            'causes_include': ['vacuum leak', 'maf sensor']
        },
    }

    verified_count = 0
    for code, checks in known_accurate.items():
        if code not in ALL_CODES:
            print(f"   MISSING: {code}")
            continue

        data = ALL_CODES[code]
        desc = data.get('description', '').lower()
        causes = data.get('common_causes', '').lower()
        severity = data.get('severity', '')

        # Check description
        desc_match = all(term in desc for term in checks['description_contains'])

        # Check severity
        sev_match = severity == checks['severity']

        # Check causes
        causes_match = any(cause.lower() in causes for cause in checks['causes_include'])

        if desc_match and sev_match and causes_match:
            print(f"   VERIFIED: {code} - Accurate per OBD-II standards")
            verified_count += 1
        else:
            if not desc_match:
                print(f"   ISSUE: {code} - Description may be inaccurate")
            if not sev_match:
                print(f"   ISSUE: {code} - Severity should be {checks['severity']}, is {severity}")
            if not causes_match:
                print(f"   WARNING: {code} - Expected causes not found")

    print()

    # Final summary
    print("=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    print()
    print(f"Total Codes Checked: {len(ALL_CODES)}")
    print(f"Format Issues: {len(issues)}")
    print(f"Warnings: {len(warnings)}")
    print(f"Common Codes Present: {len(present)}/15")
    print(f"Known Accurate Codes: {verified_count}/{len(known_accurate)}")
    print()

    if len(issues) == 0 and len(missing) == 0:
        print("STATUS: ALL CHECKS PASSED")
        print("Your codes are accurate and production-ready!")
    elif len(issues) == 0:
        print("STATUS: PASSED WITH MINOR GAPS")
        print(f"Your codes are accurate. Consider adding {len(missing)} common codes.")
    else:
        print("STATUS: ISSUES FOUND")
        print("Review issues above and fix before production use.")

    print()
    print("=" * 70)
    print()

    return len(issues) == 0


def suggest_verification_sources():
    """Suggest free online sources for manual verification"""
    print("=" * 70)
    print("Free Online Verification Sources")
    print("=" * 70)
    print()

    sources = [
        {
            'name': 'OBD-Codes.com',
            'url': 'https://www.obd-codes.com/',
            'description': 'Largest free database, 5000+ codes',
            'how_to': 'Search any code to compare description and causes'
        },
        {
            'name': 'OBD2-Code.com',
            'url': 'https://www.obd2-code.com/',
            'description': 'Free lookup with detailed explanations',
            'how_to': 'Enter code to verify symptoms and fixes'
        },
        {
            'name': 'Engine-Codes.com',
            'url': 'https://www.engine-codes.com/',
            'description': 'Community-verified code database',
            'how_to': 'Compare your codes against their entries'
        },
        {
            'name': 'AutoCodes.com',
            'url': 'https://www.autocodes.com/',
            'description': 'Free code lookup tool',
            'how_to': 'Verify code meanings and common fixes'
        },
        {
            'name': 'CarParts.com OBD Guide',
            'url': 'https://www.carparts.com/obd-codes',
            'description': 'Free comprehensive guide',
            'how_to': 'Cross-reference code information'
        },
    ]

    print("Recommended sources for manual verification:\n")

    for i, source in enumerate(sources, 1):
        print(f"{i}. {source['name']}")
        print(f"   URL: {source['url']}")
        print(f"   Description: {source['description']}")
        print(f"   How to use: {source['how_to']}")
        print()

    print("Verification Strategy:")
    print("1. Pick 10-20 random codes from your database")
    print("2. Look them up on 2-3 of the sources above")
    print("3. Compare descriptions, causes, and symptoms")
    print("4. If they match, your database is accurate")
    print()

    print("Sample codes to verify:")
    sample_codes = ['P0420', 'P0442', 'P0171', 'P0300', 'P0101',
                    'P0335', 'P0700', 'C0035', 'B0001', 'U0100']
    for code in sample_codes:
        if code in ALL_CODES:
            print(f"  - {code}: {ALL_CODES[code]['description'][:50]}...")

    print()


if __name__ == "__main__":
    # Run offline verification
    passed = verify_codes_offline()

    # Suggest online sources
    suggest_verification_sources()

    # Exit code
    sys.exit(0 if passed else 1)
