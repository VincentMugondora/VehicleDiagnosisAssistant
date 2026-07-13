#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 2 Enrichment Quick Start

This script helps you start Phase 2 enrichment with the right settings.

Usage:
    # Option 1: Single batch (all 500 codes)
    python scripts/start_phase2.py --all

    # Option 2: First batch of 100
    python scripts/start_phase2.py --batch 1

    # Option 3: Interactive mode
    python scripts/start_phase2.py
"""

import sys
import argparse
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase import create_client
from app.core.config import settings


def get_current_stats():
    """Get current enrichment statistics"""
    try:
        client = create_client(settings.supabase_url, settings.supabase_service_key)
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
    except Exception as e:
        print(f"Error getting stats: {e}")
        return None, None


def display_phase2_plan():
    """Display Phase 2 plan overview"""
    print("\n" + "="*70)
    print("PHASE 2 ENRICHMENT - QUICK START")
    print("="*70)

    total, enriched = get_current_stats()

    if total and enriched:
        remaining = total - enriched
        print(f"\nCurrent Status:")
        print(f"  Total Codes:     {total:,}")
        print(f"  Enriched:        {enriched:,}")
        print(f"  Remaining:       {remaining:,}")
        print(f"  Coverage:        ~{(enriched/total*100):.1f}%")
    else:
        print("\n(Could not fetch current stats)")

    print("\n" + "-"*70)
    print("Phase 2 Plan:")
    print("-"*70)
    print("  Target:          500 more codes")
    print("  Time:            ~2 hours (1.7 hours active)")
    print("  Cost:            ~$0.70")
    print("  After Phase 2:   ~600 total codes")
    print("  Coverage:        90%+ of user queries")
    print("="*70)


def start_batch(batch_num: int, size: int = 100):
    """Start a specific batch"""
    print(f"\n{'='*70}")
    print(f"Starting Phase 2 - Batch {batch_num} ({size} codes)")
    print("="*70)

    log_file = f"enrichment_phase2_batch{batch_num}.log"

    print(f"\nLog file: {log_file}")
    print(f"Batch size: 20 codes (pause 2s between batches)")
    print(f"Estimated time: ~{size * 12 / 60:.0f} minutes")
    print(f"Estimated cost: ~${size * 0.0014:.2f}")

    print("\n[*] Starting enrichment...")
    print("    (You can monitor progress in another terminal)")
    print("    python scripts/monitor_enrichment.py --watch")
    print()

    # Build command
    cmd = [
        sys.executable,
        "scripts/enrich_existing_codes.py",
        "--limit", str(size),
        "--batch-size", "20"
    ]

    # Run the enrichment
    try:
        result = subprocess.run(
            cmd,
            input="YES\n",
            text=True,
            capture_output=False
        )

        if result.returncode == 0:
            print(f"\n[OK] Batch {batch_num} completed successfully!")
            return True
        else:
            print(f"\n[ERROR] Batch {batch_num} failed with exit code {result.returncode}")
            return False

    except KeyboardInterrupt:
        print("\n\n[!] Interrupted by user")
        return False
    except Exception as e:
        print(f"\n[ERROR] Failed to start batch: {e}")
        return False


def start_all_batches():
    """Start all 5 batches sequentially"""
    print("\n" + "="*70)
    print("STARTING ALL PHASE 2 BATCHES (500 codes)")
    print("="*70)
    print("\nThis will run 5 batches of 100 codes each")
    print("Estimated total time: ~2 hours")
    print("You can stop between batches with Ctrl+C")
    print()

    confirm = input("Start all batches now? (yes/no): ")

    if confirm.lower() != "yes":
        print("\n[!] Cancelled")
        return

    for batch_num in range(1, 6):
        print(f"\n{'='*70}")
        print(f"BATCH {batch_num}/5")
        print("="*70)

        success = start_batch(batch_num, size=100)

        if not success:
            print(f"\n[!] Stopping after batch {batch_num} due to error")
            break

        if batch_num < 5:
            print(f"\n[*] Batch {batch_num} complete. Moving to batch {batch_num + 1}...")
            print("    (2 second pause)")
            import time
            time.sleep(2)

    print("\n" + "="*70)
    print("PHASE 2 COMPLETE!")
    print("="*70)
    print("\nVerify results:")
    print("  python scripts/monitor_enrichment.py")
    print("\nTest enriched codes:")
    print("  python scripts/test_live_response.py P0500")


def interactive_mode():
    """Interactive mode - ask user what they want to do"""
    display_phase2_plan()

    print("\n" + "="*70)
    print("PHASE 2 OPTIONS")
    print("="*70)
    print("\n1. Start all 500 codes now (~2 hours)")
    print("2. Start first batch of 100 (~20 minutes)")
    print("3. Start specific batch (1-5)")
    print("4. Show detailed plan")
    print("5. Cancel")

    choice = input("\nSelect option (1-5): ").strip()

    if choice == "1":
        start_all_batches()
    elif choice == "2":
        start_batch(1, size=100)
    elif choice == "3":
        batch = input("Which batch (1-5)? ").strip()
        try:
            batch_num = int(batch)
            if 1 <= batch_num <= 5:
                start_batch(batch_num, size=100)
            else:
                print("[ERROR] Batch must be 1-5")
        except ValueError:
            print("[ERROR] Invalid batch number")
    elif choice == "4":
        print("\nSee: PHASE_2_ENRICHMENT_PLAN.md for detailed plan")
    else:
        print("\n[!] Cancelled")


def main():
    parser = argparse.ArgumentParser(description="Phase 2 Enrichment Quick Start")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Start all 500 codes in sequence"
    )
    parser.add_argument(
        "--batch",
        type=int,
        choices=[1, 2, 3, 4, 5],
        help="Start specific batch (1-5)"
    )
    parser.add_argument(
        "--size",
        type=int,
        default=100,
        help="Batch size (default: 100)"
    )

    args = parser.parse_args()

    if args.all:
        start_all_batches()
    elif args.batch:
        start_batch(args.batch, size=args.size)
    else:
        interactive_mode()


if __name__ == "__main__":
    main()
