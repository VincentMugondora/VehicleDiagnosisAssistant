"""
Find codes that mention our covered components but aren't being extracted.

This identifies "free coverage" - codes where the description contains
a component name we have diagrams for, but our regex patterns miss it.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
logging.disable(logging.CRITICAL)

from app.db.client import get_supabase_client
from app.services.component_mapper import extract_component_from_description, extract_component_from_code_prefix
import re


# Our 13 components that have diagrams
COVERED_COMPONENTS = [
    'battery',
    'transmission',
    'oxygen sensor',
    'fuel injector',
    'egr valve',
    'evap system',
    'catalytic converter',
    'wheel speed sensor',
    'ignition coil',
    'camshaft position sensor',
    'throttle body',
    'mass air flow sensor',
    'crankshaft position sensor',
]

# Variations to check for each component
COMPONENT_SEARCH_TERMS = {
    'battery': ['battery', 'batteries'],
    'transmission': ['transmission', 'gearbox', 'trans ', 'transaxle'],
    'oxygen sensor': ['oxygen sensor', 'o2 sensor', 'o2sensor', 'lambda sensor', 'air fuel sensor', 'a/f sensor'],
    'fuel injector': ['fuel injector', 'injector', 'fuel injection'],
    'egr valve': ['egr', 'exhaust gas recirculation'],
    'evap system': ['evap', 'evaporative emission', 'fuel vapor', 'vapor canister', 'purge valve'],
    'catalytic converter': ['catalyst', 'catalytic converter', 'cat converter'],
    'wheel speed sensor': ['wheel speed', 'wheel-speed', 'abs sensor'],
    'ignition coil': ['ignition coil', 'coil pack', 'coil-on-plug'],
    'camshaft position sensor': ['camshaft position', 'camshaft sensor', 'cmp sensor', 'cam position'],
    'throttle body': ['throttle body', 'throttle actuator', 'throttle valve'],
    'mass air flow sensor': ['mass air flow', 'maf sensor', 'air flow sensor', 'airflow sensor'],
    'crankshaft position sensor': ['crankshaft position', 'crankshaft sensor', 'crank sensor', 'ckp sensor'],
}


def find_missed_matches():
    """Find codes mentioning covered components that extraction misses."""

    print("=" * 80)
    print("FINDING MISSED COMPONENT MATCHES")
    print("=" * 80)
    print()
    print("Checking if codes mention our 13 covered components in their")
    print("descriptions but aren't caught by the extraction logic...")
    print()

    # Fetch all codes
    client = get_supabase_client()
    all_codes = []
    offset = 0
    page_size = 1000

    while True:
        result = client.table("obd_codes").select("code, description").range(offset, offset + page_size - 1).execute()
        if not result.data:
            break
        all_codes.extend(result.data)
        offset += page_size
        if len(result.data) < page_size:
            break

    print(f"Analyzing {len(all_codes):,} codes...")
    print()

    # Find missed matches
    missed_by_component = {comp: [] for comp in COVERED_COMPONENTS}
    total_missed = 0

    for record in all_codes:
        code = record.get('code')
        description = record.get('description', '').lower()

        # Try current extraction logic
        component = extract_component_from_description(description, code=code)
        if not component:
            component = extract_component_from_code_prefix(code)

        # If no component extracted, check if description mentions any covered component
        if not component:
            for covered_comp, search_terms in COMPONENT_SEARCH_TERMS.items():
                for term in search_terms:
                    # Use word boundaries to avoid partial matches
                    pattern = r'\b' + re.escape(term.lower()) + r'\b'
                    if re.search(pattern, description):
                        missed_by_component[covered_comp].append({
                            'code': code,
                            'description': record.get('description'),
                            'matched_term': term
                        })
                        total_missed += 1
                        break  # Don't count same code twice for same component

                if missed_by_component[covered_comp] and missed_by_component[covered_comp][-1]['code'] == code:
                    break  # Already recorded this code

    # Report results
    print("=" * 80)
    print("RESULTS: MISSED MATCHES")
    print("=" * 80)
    print()

    if total_missed == 0:
        print("[EXCELLENT] No missed matches found!")
        print("Current extraction logic catches all codes that mention covered components.")
        print()
        return

    print(f"Found {total_missed} codes mentioning covered components that aren't caught")
    print("by the current extraction logic.")
    print()
    print("This represents FREE coverage - we already have images for these components!")
    print()

    # Show breakdown
    print("Breakdown by component:")
    print("-" * 80)

    for component, missed_codes in sorted(missed_by_component.items(), key=lambda x: len(x[1]), reverse=True):
        count = len(missed_codes)
        if count > 0:
            print(f"\n{component.upper()}: {count} missed codes")
            print("-" * 80)

            # Show first 10 examples
            for i, item in enumerate(missed_codes[:10], 1):
                desc_short = item['description'][:60]
                print(f"  {i}. {item['code']:<8} {desc_short}...")
                print(f"     -> Mentions: '{item['matched_term']}'")

            if count > 10:
                print(f"  ... and {count - 10} more")

    print()
    print("=" * 80)
    print("RECOMMENDATION")
    print("=" * 80)
    print()
    print(f"Update component_mapper.py patterns to catch these {total_missed} codes.")
    print("This will increase coverage WITHOUT sourcing any new images!")
    print()


if __name__ == "__main__":
    find_missed_matches()
