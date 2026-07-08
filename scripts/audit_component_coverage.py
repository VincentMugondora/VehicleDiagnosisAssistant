"""
Audit component extraction coverage across all OBD codes.

Shows which components are most common and how many codes have no component match.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Suppress all logging during audit
import logging
logging.disable(logging.CRITICAL)

from app.db.client import get_supabase_client
from app.services.component_mapper import extract_component_from_description, extract_component_from_code_prefix
from collections import Counter


def audit_all_codes():
    """Audit component extraction across all codes in database."""

    print("=" * 80)
    print("COMPONENT EXTRACTION AUDIT")
    print("=" * 80)
    print()

    # Fetch all codes (no limit - get ALL codes)
    client = get_supabase_client()
    print("Fetching all OBD codes from database...")

    # Supabase has a 1000 row limit by default, need to paginate
    all_codes = []
    page_size = 1000
    offset = 0

    while True:
        result = client.table("obd_codes").select("code, description").range(offset, offset + page_size - 1).execute()
        if not result.data:
            break
        all_codes.extend(result.data)
        offset += page_size
        print(f"  Fetched {len(all_codes):,} codes...", end="\r")
        if len(result.data) < page_size:
            break

    print()  # Clear the progress line
    total_codes = len(all_codes)
    print(f"Total codes: {total_codes:,}")
    print()

    # Track components
    component_counts = Counter()
    no_component_codes = []

    print("Analyzing component extraction (this may take a moment)...")

    for i, record in enumerate(all_codes, start=1):
        if i % 1000 == 0:
            print(f"  Processed {i:,}/{total_codes:,} codes...", end="\r")
        code = record.get('code')
        description = record.get('description', '')

        # Use the SAME logic as webhook.py (after our fix)
        component = extract_component_from_description(description, code=code)

        # Fallback to code prefix if no match from description
        if not component:
            component = extract_component_from_code_prefix(code)

        if component:
            component_counts[component] += 1
        else:
            no_component_codes.append({
                'code': code,
                'description': description
            })

    print("Analysis complete!")
    print()
    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print()

    # 1. Distinct components
    distinct_components = len(component_counts)
    print(f"1. DISTINCT COMPONENTS FOUND: {distinct_components}")
    print()

    # 2. Codes with NO component match
    no_match_count = len(no_component_codes)
    no_match_percent = (no_match_count / total_codes) * 100
    print(f"2. CODES WITH NO COMPONENT MATCH: {no_match_count:,} ({no_match_percent:.1f}%)")
    print()

    # 3. Top components by code count
    print(f"3. TOP COMPONENTS BY CODE COUNT (Top 50)")
    print("-" * 80)
    print(f"{'Rank':<6} {'Component':<40} {'Codes':<10} {'% of Total'}")
    print("-" * 80)

    total_with_component = sum(component_counts.values())

    for rank, (component, count) in enumerate(component_counts.most_common(50), start=1):
        percent = (count / total_codes) * 100
        print(f"{rank:<6} {component:<40} {count:<10,} {percent:>5.1f}%")

    print("-" * 80)
    print(f"{'TOTAL':<6} {'(codes with component match)':<40} {total_with_component:<10,} {(total_with_component/total_codes)*100:>5.1f}%")
    print("=" * 80)
    print()

    # Sample of codes with NO match (first 20)
    print("SAMPLE: Codes with NO component match (first 20):")
    print("-" * 80)
    for i, item in enumerate(no_component_codes[:20], start=1):
        desc_short = item['description'][:60] + "..." if len(item['description']) > 60 else item['description']
        print(f"{i:>2}. {item['code']:<8} {desc_short}")

    if len(no_component_codes) > 20:
        print(f"... and {len(no_component_codes) - 20:,} more")

    print("=" * 80)
    print()

    # Sourcing priority analysis
    print("IMAGE SOURCING PRIORITY ANALYSIS")
    print("=" * 80)
    print()
    print("If you source images for the TOP 10 components, you'd cover:")

    cumulative = 0
    for rank, (component, count) in enumerate(component_counts.most_common(10), start=1):
        cumulative += count
        coverage = (cumulative / total_codes) * 100
        print(f"  Top {rank:>2}: {cumulative:>5,} codes ({coverage:>5.1f}% of all codes)")

    print()
    print("If you source images for the TOP 20 components, you'd cover:")

    cumulative = 0
    for rank, (component, count) in enumerate(component_counts.most_common(20), start=1):
        cumulative += count
        coverage = (cumulative / total_codes) * 100

    print(f"  Top 20: {cumulative:>5,} codes ({coverage:>5.1f}% of all codes)")

    print()
    print("If you source images for the TOP 50 components, you'd cover:")

    cumulative = 0
    for rank, (component, count) in enumerate(component_counts.most_common(50), start=1):
        cumulative += count
        coverage = (cumulative / total_codes) * 100

    print(f"  Top 50: {cumulative:>5,} codes ({coverage:>5.1f}% of all codes)")

    print()
    print("=" * 80)
    print()

    # Show which components we ALREADY HAVE diagrams for
    print("CURRENT DIAGRAM COVERAGE")
    print("=" * 80)
    existing_diagrams = client.table("system_diagrams").select("system").execute()
    existing_systems = {item['system'].lower() for item in existing_diagrams.data}

    print(f"Existing diagrams: {len(existing_systems)}")
    print()
    print("Top 20 components - diagram status:")
    print("-" * 80)

    for rank, (component, count) in enumerate(component_counts.most_common(20), start=1):
        has_diagram = component.lower() in existing_systems
        status = "[YES]" if has_diagram else "[NO] "
        percent = (count / total_codes) * 100
        print(f"{rank:>2}. {status} {component:<35} {count:>5,} codes ({percent:>4.1f}%)")

    print("=" * 80)


if __name__ == "__main__":
    audit_all_codes()
