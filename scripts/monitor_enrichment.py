#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Monitor Enrichment Progress

Displays real-time enrichment statistics and progress.

Usage:
    python scripts/monitor_enrichment.py
    python scripts/monitor_enrichment.py --watch  # Auto-refresh every 30s
"""

import sys
import time
import argparse
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase import create_client
from app.core.config import settings


def clear_screen():
    """Clear terminal screen"""
    import os
    os.system('cls' if os.name == 'nt' else 'clear')


def get_enrichment_stats(client):
    """Get enrichment statistics"""
    result = client.table('obd_enrichment_stats').select('*').execute()

    stats = {}
    total = 0

    for row in result.data:
        status = row['enrichment_status']
        count = row['count']
        avg_score = row.get('avg_knowledge_score', 0)

        stats[status] = {
            'count': count,
            'avg_score': avg_score
        }
        total += count

    return stats, total


def get_recent_enrichments(client, limit=10):
    """Get recently enriched codes"""
    result = client.table('obd_codes').select(
        'code, description, knowledge_score, last_enriched, enrichment_status'
    ).eq('enrichment_status', 'ai_enriched').order(
        'last_enriched', desc=True
    ).limit(limit).execute()

    return result.data


def format_timedelta(td):
    """Format timedelta nicely"""
    seconds = int(td.total_seconds())
    if seconds < 60:
        return f"{seconds}s ago"
    elif seconds < 3600:
        return f"{seconds // 60}m ago"
    elif seconds < 86400:
        return f"{seconds // 3600}h ago"
    else:
        return f"{seconds // 86400}d ago"


def display_stats(stats, total, recent):
    """Display enrichment statistics"""
    print("\n" + "="*70)
    print("ENRICHMENT PROGRESS MONITOR")
    print("="*70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Overall stats
    print("Overall Statistics:")
    print("-" * 70)
    enriched = stats.get('ai_enriched', {}).get('count', 0) + \
               stats.get('reviewed', {}).get('count', 0) + \
               stats.get('oem_verified', {}).get('count', 0)

    remaining = total - enriched
    progress = (enriched / total * 100) if total > 0 else 0

    print(f"Total Codes:      {total:,}")
    print(f"Enriched:         {enriched:,} ({progress:.1f}%)")
    print(f"Remaining:        {remaining:,}")
    print()

    # Progress bar
    bar_width = 50
    filled = int(bar_width * progress / 100)
    bar = "#" * filled + "-" * (bar_width - filled)
    print(f"Progress: [{bar}] {progress:.1f}%")
    print()

    # Breakdown by status
    print("Enrichment Status Breakdown:")
    print("-" * 70)
    print(f"{'Status':<25} {'Count':>10} {'Avg Score':>15}")
    print("-" * 70)

    for status, data in sorted(stats.items(), key=lambda x: x[1]['count'], reverse=True):
        count = data['count']
        avg_score = data['avg_score']
        print(f"{status:<25} {count:>10,} {avg_score:>14.1f}%")

    print("-" * 70)

    # Estimates
    if remaining > 0:
        est_time_minutes = remaining * 15 / 60  # 15 seconds per code
        est_cost = remaining * 0.0014  # $0.0014 per code

        print()
        print("Estimates (if enriching all remaining):")
        print("-" * 70)
        print(f"Time:  ~{est_time_minutes:.0f} minutes (~{est_time_minutes/60:.1f} hours)")
        print(f"Cost:  ~${est_cost:.2f}")

    # Recent enrichments
    if recent:
        print()
        print("Recently Enriched (last 10):")
        print("-" * 70)

        for i, code_rec in enumerate(recent[:10], 1):
            code = code_rec.get('code')
            score = code_rec.get('knowledge_score', 0)
            last_enriched = code_rec.get('last_enriched')

            # Calculate time ago
            if last_enriched:
                try:
                    enriched_time = datetime.fromisoformat(last_enriched.replace('Z', '+00:00'))
                    now = datetime.now(enriched_time.tzinfo)
                    time_ago = format_timedelta(now - enriched_time)
                except:
                    time_ago = "unknown"
            else:
                time_ago = "unknown"

            desc = code_rec.get('description', 'N/A')[:40]
            print(f"  {i:2}. {code}: {score:>5.1f}% - {time_ago:>10} - {desc}...")

    print()
    print("="*70)


def monitor(watch=False, interval=30):
    """Monitor enrichment progress"""
    client = create_client(settings.supabase_url, settings.supabase_service_key)

    try:
        while True:
            if watch:
                clear_screen()

            # Get stats
            stats, total = get_enrichment_stats(client)
            recent = get_recent_enrichments(client, limit=10)

            # Display
            display_stats(stats, total, recent)

            if not watch:
                break

            # Wait before refresh
            print(f"\nRefreshing in {interval} seconds... (Ctrl+C to stop)")
            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")


def main():
    parser = argparse.ArgumentParser(description="Monitor Enrichment Progress")
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Auto-refresh every 30 seconds"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Refresh interval in seconds (default: 30)"
    )

    args = parser.parse_args()

    monitor(watch=args.watch, interval=args.interval)


if __name__ == "__main__":
    main()
