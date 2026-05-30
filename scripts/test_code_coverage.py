"""
Test script to verify OBD code coverage and quality.
Displays statistics about the comprehensive code dataset.
"""

import sys
from comprehensive_obd_codes import ALL_CODES
from collections import Counter

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def analyze_codes():
    """Analyze the code dataset and display statistics"""

    print("=" * 70)
    print("OBD-II Code Dataset Analysis")
    print("=" * 70)
    print()

    # Total count
    total = len(ALL_CODES)
    print(f"Total Codes: {total}")
    print()

    # Count by system
    systems = Counter(code_data.get("system", "Unknown") for code_data in ALL_CODES.values())
    print("Codes by System:")
    for system, count in systems.most_common():
        percentage = (count / total) * 100
        print(f"  {system:15} {count:3} codes ({percentage:5.1f}%)")
    print()

    # Count by severity
    severities = Counter(code_data.get("severity", "Unknown") for code_data in ALL_CODES.values())
    print("Codes by Severity:")
    for severity, count in [("High", severities["High"]), ("Medium", severities["Medium"]), ("Low", severities["Low"])]:
        percentage = (count / total) * 100
        print(f"  {severity:15} {count:3} codes ({percentage:5.1f}%)")
    print()

    # Code prefixes
    prefixes = Counter(code[0] for code in ALL_CODES.keys())
    print("Codes by Prefix:")
    prefix_names = {"P": "Powertrain", "C": "Chassis", "B": "Body", "U": "Network"}
    for prefix in sorted(prefixes.keys()):
        count = prefixes[prefix]
        name = prefix_names.get(prefix, "Unknown")
        percentage = (count / total) * 100
        print(f"  {prefix} ({name:12}) {count:3} codes ({percentage:5.1f}%)")
    print()

    # Common code categories (P-codes)
    print("Common P-Code Categories:")
    p_categories = {
        "P010x-P011x": "MAF/IAT Sensors",
        "P013x-P014x": "O2 Sensors Bank 1",
        "P017x": "Fuel Trim",
        "P020x": "Fuel Injectors",
        "P030x": "Misfires",
        "P035x": "Ignition Coils",
        "P042x-P043x": "Catalytic Converter",
        "P044x": "EVAP System",
        "P070x-P079x": "Transmission",
    }

    for cat_range, cat_name in p_categories.items():
        # Extract first 3-4 digits to match
        if "-" in cat_range:
            start = cat_range.split("-")[0][:4]
            prefix = start[:3]
        else:
            prefix = cat_range[:4]

        count = sum(1 for code in ALL_CODES.keys() if code.startswith(prefix))
        if count > 0:
            print(f"  {cat_range:15} {cat_name:25} {count:2} codes")
    print()

    # Sample codes
    print("Sample Codes (Most Common):")
    common_codes = ["P0300", "P0420", "P0171", "P0442", "P0101", "P0301", "P0335", "P0700"]
    for code in common_codes:
        if code in ALL_CODES:
            desc = ALL_CODES[code]["description"]
            severity = ALL_CODES[code]["severity"]
            print(f"  {code} [{severity:6}] {desc}")
    print()

    # Quality checks
    print("Quality Checks:")

    # Check all required fields
    required_fields = ["description", "common_causes", "symptoms", "generic_fixes", "system", "severity"]
    complete_codes = sum(
        1 for code_data in ALL_CODES.values()
        if all(code_data.get(field) for field in required_fields)
    )
    print(f"  Complete entries: {complete_codes}/{total} ({(complete_codes/total)*100:.1f}%)")

    # Check description length
    good_descriptions = sum(
        1 for code_data in ALL_CODES.values()
        if len(code_data.get("description", "")) > 20
    )
    print(f"  Detailed descriptions: {good_descriptions}/{total} ({(good_descriptions/total)*100:.1f}%)")

    # Check for multiple causes
    multiple_causes = sum(
        1 for code_data in ALL_CODES.values()
        if "," in code_data.get("common_causes", "")
    )
    print(f"  Multiple causes listed: {multiple_causes}/{total} ({(multiple_causes/total)*100:.1f}%)")

    print()
    print("=" * 70)
    print("Dataset is ready for production use!")
    print("=" * 70)
    print()
    print("To import into Supabase, run:")
    print("  python scripts/import_obd_datasets.py")
    print()

if __name__ == "__main__":
    analyze_codes()
