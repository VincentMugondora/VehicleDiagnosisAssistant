#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prioritized Enrichment Plan

Enriches OBD codes in priority order:
1. Most common P-codes (powertrain)
2. Codes with existing data that need enhancement
3. All remaining codes

Usage:
    # Phase 1: Top 100 most common P-codes
    python scripts/prioritized_enrichment_plan.py --phase 1

    # Phase 2: Next 500 codes
    python scripts/prioritized_enrichment_plan.py --phase 2

    # Phase 3: All remaining
    python scripts/prioritized_enrichment_plan.py --phase 3
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase import create_client
from app.core.config import settings


# Priority P-codes (most common issues users encounter)
PRIORITY_P_CODES = [
    # Catalytic Converter & Emissions
    "P0420", "P0430", "P0441", "P0442", "P0455", "P0456",

    # O2 Sensors
    "P0131", "P0132", "P0133", "P0134", "P0135", "P0136", "P0137", "P0138",
    "P0141", "P0151", "P0152", "P0153", "P0154", "P0155", "P0156", "P0157", "P0158", "P0161",

    # Fuel System
    "P0171", "P0172", "P0174", "P0175", "P0300", "P0301", "P0302", "P0303",
    "P0304", "P0305", "P0306", "P0307", "P0308",

    # Ignition System
    "P0351", "P0352", "P0353", "P0354", "P0355", "P0356", "P0357", "P0358",

    # MAF & MAP Sensors
    "P0100", "P0101", "P0102", "P0103", "P0106", "P0107", "P0108",

    # Transmission
    "P0700", "P0705", "P0715", "P0720", "P0730", "P0731", "P0732", "P0733",
    "P0734", "P0735", "P0740", "P0741", "P0750", "P0755", "P0760",

    # Engine & Sensors
    "P0010", "P0011", "P0016", "P0017", "P0030", "P0031", "P0036", "P0037",
    "P0068", "P0069", "P0070", "P0087", "P0088", "P0089", "P0090",

    # EGR
    "P0400", "P0401", "P0402", "P0403", "P0404", "P0405", "P0406", "P0407", "P0408",

    # Throttle
    "P0121", "P0122", "P0123", "P2101", "P2102", "P2103", "P2104", "P2105",

    # EVAP System
    "P0440", "P0443", "P0446", "P0447", "P0448", "P0449", "P0450", "P0451", "P0452", "P0453",
]


def get_enrichment_stats(client):
    """Get current enrichment statistics"""
    result = client.table('obd_enrichment_stats').select('*').execute()

    total = 0
    enriched = 0

    for row in result.data:
        count = row['count']
        status = row['enrichment_status']
        total += count

        if status in ['ai_enriched', 'reviewed', 'oem_verified']:
            enriched += count

    return total, enriched


def get_phase_1_codes(client):
    """Phase 1: Top 100 priority P-codes"""
    codes = []

    for code in PRIORITY_P_CODES[:100]:
        result = client.table('obd_codes').select('code, description, knowledge_score').eq('code', code).execute()

        if result.data and result.data[0]['knowledge_score'] < 80:
            codes.append(result.data[0])

    return codes


def get_phase_2_codes(client):
    """Phase 2: Next 500 P-codes (P0000-P0999)"""
    result = client.table('obd_codes').select(
        'code, description, knowledge_score'
    ).like('code', 'P0%').lt('knowledge_score', 80.0).order('code').limit(500).execute()

    return result.data


def get_phase_3_codes(client, batch_size=1000):
    """Phase 3: All remaining codes"""
    result = client.table('obd_codes').select(
        'code, description, knowledge_score'
    ).lt('knowledge_score', 80.0).order('code').limit(batch_size).execute()

    return result.data


def main():
    parser = argparse.ArgumentParser(description="Prioritized Enrichment Plan")
    parser.add_argument(
        "--phase",
        type=int,
        choices=[1, 2, 3],
        required=True,
        help="Enrichment phase: 1=Top 100 priority, 2=Next 500 P-codes, 3=All remaining"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show plan without executing"
    )

    args = parser.parse_args()

    print("\n" + "="*70)
    print("PRIORITIZED ENRICHMENT PLAN")
    print("="*70)

    # Connect to database
    client = create_client(settings.supabase_url, settings.supabase_service_key)

    # Get current stats
    total, enriched = get_enrichment_stats(client)
    remaining = total - enriched

    print(f"\nCurrent Status:")
    print(f"  Total Codes: {total}")
    print(f"  Enriched: {enriched}")
    print(f"  Remaining: {remaining}")
    print()

    # Get codes for selected phase
    if args.phase == 1:
        print("PHASE 1: Top 100 Priority P-Codes")
        print("-" * 70)
        print("Most common codes users encounter")
        print("Estimated time: ~25 minutes")
        print("Estimated cost: $0.14")
        print()
        codes = get_phase_1_codes(client)

    elif args.phase == 2:
        print("PHASE 2: Next 500 P-Codes (P0000-P0999)")
        print("-" * 70)
        print("Common powertrain codes")
        print("Estimated time: ~2 hours")
        print("Estimated cost: $0.70")
        print()
        codes = get_phase_2_codes(client)

    else:  # phase == 3
        print("PHASE 3: All Remaining Codes")
        print("-" * 70)
        print("WARNING: This will enrich ALL remaining codes")
        print(f"Estimated time: ~{remaining * 15 / 3600:.1f} hours")
        print(f"Estimated cost: ~${remaining * 0.0014:.2f}")
        print()
        codes = get_phase_3_codes(client, batch_size=1000)

    print(f"Found {len(codes)} codes to enrich")

    if len(codes) == 0:
        print("\n[OK] No codes need enrichment in this phase!")
        return 0

    # Show sample
    print("\nSample codes (first 10):")
    for i, code_record in enumerate(codes[:10], 1):
        code = code_record.get('code')
        desc = code_record.get('description', 'N/A')[:45]
        score = code_record.get('knowledge_score', 0)
        print(f"  {i:2}. {code}: {score:.0f}% - {desc}...")

    if len(codes) > 10:
        print(f"  ... and {len(codes) - 10} more")

    # Build command
    code_list = ','.join([c['code'] for c in codes[:100]])  # Max 100 at a time

    print("\n" + "="*70)
    print("RECOMMENDED COMMAND:")
    print("="*70)

    if args.phase == 1:
        print("\n# Enrich top 100 priority codes")
        print(f"python scripts/enrich_existing_codes.py --limit {len(codes)} --batch-size 20")

    elif args.phase == 2:
        print("\n# Enrich in batches of 100")
        for i in range(0, min(len(codes), 500), 100):
            batch_num = i // 100 + 1
            print(f"\n# Batch {batch_num}:")
            print(f"python scripts/enrich_existing_codes.py --limit 100 --batch-size 20")
            if i < 400:
                print("# Wait for completion, then run next batch")

    else:  # phase 3
        print("\n# WARNING: Phase 3 will take many hours")
        print("# Recommended: Run in batches")
        print("\n# Option 1: Enrich 1000 codes at a time")
        print("python scripts/enrich_existing_codes.py --limit 1000 --batch-size 50")
        print("\n# Option 2: Run continuously (requires monitoring)")
        print("python scripts/enrich_existing_codes.py --all --batch-size 50")

    print("\n" + "="*70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
