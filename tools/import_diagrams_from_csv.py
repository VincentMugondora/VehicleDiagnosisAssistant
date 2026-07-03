#!/usr/bin/env python3
"""
Import system diagrams from CSV file into Supabase.

Usage:
    python tools/import_diagrams_from_csv.py system_diagrams.csv

CSV Format:
    system,image_url,source,license,caption,attribution_text

Example:
    catalytic converter,https://...,Wikimedia Commons,CC BY-SA 4.0,How it works,"Diagram by John Doe"

Features:
- Validates all required fields
- Checks image URLs are HTTPS
- Detects duplicates
- Provides dry-run mode
- Shows preview before inserting
"""
import sys
import csv
from pathlib import Path
from urllib.parse import urlparse
from app.db.client import get_supabase_client
from app.core.logging import logger

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def validate_row(row: dict, line_num: int) -> list[str]:
    """
    Validate a CSV row.

    Args:
        row: CSV row as dict
        line_num: Line number for error reporting

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    # Required fields
    required = ['system', 'image_url', 'source', 'license']
    for field in required:
        if not row.get(field) or not row[field].strip():
            errors.append(f"Line {line_num}: Missing required field '{field}'")

    # Validate image URL
    if row.get('image_url'):
        url = row['image_url'].strip()
        parsed = urlparse(url)

        if not parsed.scheme:
            errors.append(f"Line {line_num}: image_url missing protocol (http/https)")
        elif parsed.scheme != 'https':
            errors.append(f"Line {line_num}: image_url must be HTTPS (WhatsApp requirement)")

        if not parsed.netloc:
            errors.append(f"Line {line_num}: image_url missing domain")

    # Validate caption length
    if row.get('caption') and len(row['caption']) > 60:
        errors.append(f"Line {line_num}: caption too long ({len(row['caption'])} chars, max 60)")

    return errors


def preview_import(records: list[dict]):
    """Show preview of what will be imported"""
    print("\n" + "="*70)
    print("IMPORT PREVIEW")
    print("="*70)

    for i, record in enumerate(records, 1):
        print(f"\n{i}. {record['system']}")
        print(f"   URL: {record['image_url'][:60]}...")
        print(f"   Source: {record['source']}")
        print(f"   License: {record['license']}")
        if record.get('caption'):
            print(f"   Caption: {record['caption']}")
        if record.get('attribution_text'):
            print(f"   Attribution: {record['attribution_text']}")

    print("\n" + "="*70)
    print(f"Total: {len(records)} diagrams")
    print("="*70)


def import_diagrams(csv_path: str, dry_run: bool = False):
    """
    Import diagrams from CSV file.

    Args:
        csv_path: Path to CSV file
        dry_run: If True, validate and preview only (no insert)
    """
    print(f"\n📂 Reading: {csv_path}")

    # Check file exists
    path = Path(csv_path)
    if not path.exists():
        print(f"❌ File not found: {csv_path}")
        sys.exit(1)

    # Read CSV
    records = []
    all_errors = []

    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        # Validate header
        required_cols = {'system', 'image_url', 'source', 'license', 'caption', 'attribution_text'}
        if not required_cols.issubset(set(reader.fieldnames)):
            missing = required_cols - set(reader.fieldnames)
            print(f"❌ Missing CSV columns: {missing}")
            sys.exit(1)

        # Validate rows
        for line_num, row in enumerate(reader, start=2):  # Start at 2 (header is line 1)
            # Skip empty rows
            if not any(row.values()):
                continue

            errors = validate_row(row, line_num)
            all_errors.extend(errors)

            if not errors:
                # Clean record
                record = {
                    'system': row['system'].strip(),
                    'image_url': row['image_url'].strip(),
                    'source': row['source'].strip(),
                    'license': row['license'].strip(),
                    'caption': row['caption'].strip() if row.get('caption') else None,
                    'attribution_text': row['attribution_text'].strip() if row.get('attribution_text') else None
                }
                records.append(record)

    # Report validation errors
    if all_errors:
        print("\n❌ VALIDATION ERRORS:")
        for error in all_errors:
            print(f"  • {error}")
        sys.exit(1)

    if not records:
        print("❌ No valid records found in CSV")
        sys.exit(1)

    print(f"✅ Validated {len(records)} records")

    # Preview
    preview_import(records)

    # Dry run?
    if dry_run:
        print("\n🔍 DRY RUN - No changes made")
        return

    # Confirm
    response = input("\n❓ Import these diagrams to database? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("❌ Import cancelled")
        sys.exit(0)

    # Connect to database
    print("\n📡 Connecting to Supabase...")
    supabase = get_supabase_client()
    if not supabase:
        print("❌ Failed to connect to Supabase")
        sys.exit(1)

    # Import records
    print("\n📥 Importing...")
    success_count = 0
    error_count = 0

    for i, record in enumerate(records, 1):
        try:
            # Check for existing system
            existing = supabase.table("system_diagrams")\
                .select("id")\
                .eq("system", record['system'])\
                .execute()

            if existing.data:
                print(f"⚠️  {i}/{len(records)}: '{record['system']}' already exists, skipping")
                continue

            # Insert
            supabase.table("system_diagrams").insert(record).execute()
            print(f"✅ {i}/{len(records)}: '{record['system']}' imported")
            success_count += 1

        except Exception as e:
            print(f"❌ {i}/{len(records)}: '{record['system']}' failed: {e}")
            error_count += 1

    # Summary
    print("\n" + "="*70)
    print("IMPORT COMPLETE")
    print("="*70)
    print(f"✅ Success: {success_count}")
    if error_count:
        print(f"❌ Errors: {error_count}")
    print("="*70)


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python import_diagrams_from_csv.py <csv_file> [--dry-run]")
        print("\nExample:")
        print("  python import_diagrams_from_csv.py system_diagrams.csv")
        print("  python import_diagrams_from_csv.py system_diagrams.csv --dry-run")
        sys.exit(1)

    csv_path = sys.argv[1]
    dry_run = '--dry-run' in sys.argv

    if dry_run:
        print("🔍 DRY RUN MODE - Will validate and preview only")

    import_diagrams(csv_path, dry_run)


if __name__ == "__main__":
    main()
