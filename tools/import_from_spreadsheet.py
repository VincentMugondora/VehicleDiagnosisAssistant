"""
Import system diagrams from spreadsheet tracker.

Reads system_diagram_tracker.xlsx, downloads and validates images,
and prepares data for insertion into system_diagrams table.
"""
import os
import sys
from pathlib import Path
from typing import Optional
import requests
from io import BytesIO

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import openpyxl
except ImportError:
    print("ERROR: openpyxl not installed. Run: pip install openpyxl")
    sys.exit(1)

try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow not installed. Run: pip install Pillow")
    sys.exit(1)


# Configuration
SPREADSHEET_PATH = r"c:\Users\vinmu\Downloads\system_diagram_tracker.xlsx"
MAX_IMAGE_SIZE_MB = 2
ALLOWED_FORMATS = ['jpeg', 'jpg', 'png']
DOWNLOAD_TIMEOUT = 30  # seconds


class ImageValidationError(Exception):
    """Raised when image validation fails"""
    pass


def read_spreadsheet(path: str):
    """
    Read the spreadsheet and extract approved rows.

    Returns:
        List of dicts with columns: System, Image URL, Source, License,
        Attribution Text, Caption, Status, Notes
    """
    print(f"\n[*] Reading spreadsheet: {path}")

    if not os.path.exists(path):
        raise FileNotFoundError(f"Spreadsheet not found: {path}")

    workbook = openpyxl.load_workbook(path, data_only=True)
    sheet = workbook.active

    # Read header row
    headers = []
    for cell in sheet[1]:
        if cell.value:
            headers.append(str(cell.value).strip())

    print(f"   Headers: {headers}")

    # Read data rows
    rows = []
    for row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
        if not any(row):  # Skip empty rows
            continue

        row_data = {}
        for header, value in zip(headers, row):
            row_data[header] = value.strip() if isinstance(value, str) else value

        rows.append(row_data)

    print(f"   Total rows read: {len(rows)}")

    # Filter for approved rows
    approved = [r for r in rows if r.get('Status', '').lower() == 'approved']

    print(f"   [OK] Approved rows: {len(approved)}")
    print(f"   [>>]  Skipped (not approved): {len(rows) - len(approved)}")

    return approved


def download_and_validate_image(url: str, system: str) -> dict:
    """
    Download image from URL and validate.

    Returns:
        dict with keys: success (bool), image_data (bytes), format (str),
        size_mb (float), width (int), height (int), error (str)
    """
    result = {
        'success': False,
        'image_data': None,
        'format': None,
        'size_mb': 0,
        'width': 0,
        'height': 0,
        'error': None
    }

    try:
        # Download
        print(f"   [DL]  Downloading from {url[:60]}...")
        response = requests.get(url, timeout=DOWNLOAD_TIMEOUT, headers={
            'User-Agent': 'VehicleDiagnosisAssistant/1.0 (Educational Project)'
        })
        response.raise_for_status()

        image_data = response.content
        size_mb = len(image_data) / (1024 * 1024)

        # Validate it's an image
        try:
            img = Image.open(BytesIO(image_data))
            img.verify()  # Check if it's a valid image

            # Re-open after verify (verify closes the file)
            img = Image.open(BytesIO(image_data))
            img_format = img.format.lower()
            width, height = img.size

        except Exception as e:
            raise ImageValidationError(f"Not a valid image: {e}")

        # Check format
        if img_format not in ALLOWED_FORMATS:
            raise ImageValidationError(
                f"Format '{img_format}' not allowed. Must be: {ALLOWED_FORMATS}"
            )

        # Check size
        if size_mb > MAX_IMAGE_SIZE_MB:
            raise ImageValidationError(
                f"Image too large: {size_mb:.2f}MB (max {MAX_IMAGE_SIZE_MB}MB)"
            )

        # Success
        result.update({
            'success': True,
            'image_data': image_data,
            'format': img_format,
            'size_mb': size_mb,
            'width': width,
            'height': height
        })

        print(f"      [OK] Valid {img_format.upper()} - {width}x{height}px - {size_mb:.2f}MB")

    except requests.RequestException as e:
        result['error'] = f"Download failed: {e}"
        print(f"      [X] {result['error']}")
    except ImageValidationError as e:
        result['error'] = str(e)
        print(f"      [X] {result['error']}")
    except Exception as e:
        result['error'] = f"Unexpected error: {e}"
        print(f"      [X] {result['error']}")

    return result


def process_approved_rows(rows):
    """
    Process all approved rows: download and validate images.

    Returns:
        dict with keys: validated (list), failed (list)
    """
    validated = []
    failed = []

    print(f"\n[*] Processing {len(rows)} approved rows...\n")

    for idx, row in enumerate(rows, start=1):
        system = row.get('System', '').strip()
        image_url = row.get('Image URL', '').strip()

        print(f"{idx}. System: {system}")

        if not system:
            failed.append({
                'row': row,
                'reason': 'Missing system name'
            })
            print(f"   [X] Skipped: Missing system name\n")
            continue

        if not image_url:
            failed.append({
                'row': row,
                'system': system,
                'reason': 'Missing image URL'
            })
            print(f"   [X] Skipped: Missing image URL\n")
            continue

        # Download and validate
        validation = download_and_validate_image(image_url, system)

        if validation['success']:
            validated.append({
                'system': system.lower().strip(),  # Normalize
                'image_url': image_url,
                'source': row.get('Source', '').strip(),
                'license': row.get('License', '').strip(),
                'attribution_text': row.get('Attribution Text', '').strip(),
                'caption': row.get('Caption', '').strip(),
                'validation': validation,
                'original_row': row
            })
        else:
            failed.append({
                'row': row,
                'system': system,
                'reason': validation['error']
            })

        print()  # Blank line between rows

    return {
        'validated': validated,
        'failed': failed
    }


def print_summary(results):
    """Print a summary of validation results"""
    validated = results['validated']
    failed = results['failed']

    print("\n" + "="*80)
    print("[*] VALIDATION SUMMARY")
    print("="*80)

    print(f"\n[OK] Successfully validated: {len(validated)}")
    if validated:
        print("\nSystems ready to import:")
        for item in validated:
            val = item['validation']
            print(f"  • {item['system']}")
            print(f"    Format: {val['format'].upper()} | "
                  f"Size: {val['size_mb']:.2f}MB | "
                  f"Dimensions: {val['width']}x{val['height']}px")
            print(f"    License: {item['license']}")

    print(f"\n[X] Failed validation: {len(failed)}")
    if failed:
        print("\nSystems that failed:")
        for item in failed:
            system = item.get('system', 'Unknown')
            reason = item['reason']
            print(f"  • {system}: {reason}")

    print("\n" + "="*80)

    return len(validated), len(failed)


def main():
    """Main import workflow"""
    print("="*80)
    print("[*] SYSTEM DIAGRAM IMPORT TOOL")
    print("="*80)

    try:
        # Step 1: Read spreadsheet
        approved_rows = read_spreadsheet(SPREADSHEET_PATH)

        if not approved_rows:
            print("\n[WARN]  No approved rows found. Nothing to import.")
            return

        print(f"\nSystems to process:")
        for row in approved_rows:
            print(f"  • {row.get('System', 'Unknown')}")

        # Step 2: Download and validate all images
        results = process_approved_rows(approved_rows)

        # Step 3: Print summary
        num_valid, num_failed = print_summary(results)

        # Step 4: Save results for database insertion
        if num_valid > 0:
            import json
            output_file = "import_results.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                # Don't serialize image_data (too large)
                export_data = {
                    'validated': [
                        {k: v for k, v in item.items() if k != 'validation'}
                        for item in results['validated']
                    ],
                    'failed': results['failed'],
                    'summary': {
                        'validated': num_valid,
                        'failed': num_failed
                    }
                }
                json.dump(export_data, f, indent=2)

            print(f"\n[*] Results saved to: {output_file}")
            print(f"\n[PAUSE]  REVIEW THE RESULTS ABOVE BEFORE DATABASE INSERTION")
            print(f"    To insert into database, run: python tools/insert_system_diagrams.py")

    except FileNotFoundError as e:
        print(f"\n[X] ERROR: {e}")
        print(f"\n[*] Place your spreadsheet at: {SPREADSHEET_PATH}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[X] UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
