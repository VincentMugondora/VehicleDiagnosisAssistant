"""
Cache system diagram images from Wikimedia to Supabase Storage.

Downloads each diagram image once, uploads to Supabase Storage bucket,
and updates the database to point to the cached URL instead of the
external Wikimedia URL.

This eliminates the 18-53s delay caused by re-downloading from Wikimedia
on every diagnostic request.

Usage:
    python tools/cache_diagram_images.py
"""
import sys
import os
import time
import hashlib
from pathlib import Path

# Fix Windows encoding for Unicode emojis
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add app to path
root_path = Path(__file__).parent.parent
sys.path.insert(0, str(root_path))

import httpx
from app.db.client import get_supabase_client


def download_image(url: str, timeout: int = 30) -> bytes:
    """
    Download image from URL.

    Args:
        url: Image URL
        timeout: Request timeout in seconds

    Returns:
        Image bytes

    Raises:
        httpx.HTTPError: If download fails
    """
    print(f"  Downloading from: {url[:80]}...")

    # Add User-Agent header to avoid 403 from Wikimedia
    headers = {
        "User-Agent": "VehicleDiagnosisBot/1.0 (Educational diagnostic system; diagrams cached locally)"
    }

    with httpx.Client(timeout=timeout, follow_redirects=True, headers=headers) as client:
        response = client.get(url)
        response.raise_for_status()

        content_type = response.headers.get('content-type', '')
        if not content_type.startswith('image/'):
            raise ValueError(f"URL did not return an image (got {content_type})")

        print(f"  Downloaded {len(response.content)} bytes ({content_type})")
        return response.content


def get_file_extension(url: str, content_type: str = None) -> str:
    """
    Infer file extension from URL or content type.

    Args:
        url: Image URL
        content_type: MIME type (optional)

    Returns:
        File extension (e.g., ".jpg", ".png")
    """
    # Try content type first
    if content_type:
        if 'jpeg' in content_type or 'jpg' in content_type:
            return '.jpg'
        elif 'png' in content_type:
            return '.png'
        elif 'gif' in content_type:
            return '.gif'
        elif 'svg' in content_type:
            return '.svg'

    # Fallback to URL extension
    url_lower = url.lower()
    if '.jpg' in url_lower or '.jpeg' in url_lower:
        return '.jpg'
    elif '.png' in url_lower:
        return '.png'
    elif '.gif' in url_lower:
        return '.gif'
    elif '.svg' in url_lower:
        return '.svg'

    # Default to jpg
    return '.jpg'


def generate_storage_path(system_name: str, extension: str) -> str:
    """
    Generate storage path for diagram image.

    Args:
        system_name: System name (e.g., "catalytic converter")
        extension: File extension (e.g., ".jpg")

    Returns:
        Storage path (e.g., "diagrams/catalytic-converter.jpg")
    """
    # Sanitize system name for filename
    filename = system_name.lower().replace(' ', '-').replace('/', '-')
    return f"diagrams/{filename}{extension}"


def cache_all_diagrams(bucket_name: str = "system-diagrams", dry_run: bool = False):
    """
    Cache all system diagrams to Supabase Storage.

    Args:
        bucket_name: Supabase Storage bucket name
        dry_run: If True, don't actually upload or update database
    """
    client = get_supabase_client()

    # Fetch all diagrams
    print("Fetching diagrams from database...")
    result = client.table('system_diagrams').select('id, system, image_url, source').execute()
    diagrams = result.data

    print(f"Found {len(diagrams)} diagrams to cache\n")

    # Ensure bucket exists (if not dry run)
    if not dry_run:
        try:
            # Check if bucket exists
            buckets = client.storage.list_buckets()
            bucket_exists = any(b['name'] == bucket_name for b in buckets)

            if not bucket_exists:
                print(f"Creating storage bucket: {bucket_name}")
                client.storage.create_bucket(
                    bucket_name,
                    options={
                        "public": True,  # Make images publicly accessible
                        "fileSizeLimit": 5242880  # 5MB limit per file
                    }
                )
            else:
                print(f"Using existing bucket: {bucket_name}")
        except Exception as e:
            print(f"Warning: Could not check/create bucket: {e}")

    print()

    cached_count = 0
    skipped_count = 0
    error_count = 0

    for i, diagram in enumerate(diagrams, 1):
        system = diagram['system']
        image_url = diagram['image_url']
        diagram_id = diagram['id']
        source = diagram.get('source', '')

        print(f"[{i}/{len(diagrams)}] Processing: {system}")

        # Skip if already cached (URL doesn't point to wikimedia/external)
        if not any(domain in image_url for domain in ['wikimedia.org', 'wikipedia.org']):
            print(f"  ⏭️  Already cached (not a Wikimedia URL)")
            skipped_count += 1
            print()
            continue

        try:
            # Download image
            image_bytes = download_image(image_url)

            # Determine file extension
            extension = get_file_extension(image_url)
            storage_path = generate_storage_path(system, extension)

            print(f"  Storage path: {storage_path}")

            if dry_run:
                print(f"  [DRY RUN] Would upload {len(image_bytes)} bytes")
                print(f"  [DRY RUN] Would update database with cached URL")
            else:
                # Upload to Supabase Storage
                print(f"  Uploading to Supabase Storage...")
                upload_result = client.storage.from_(bucket_name).upload(
                    storage_path,
                    image_bytes,
                    file_options={
                        "content-type": f"image/{extension[1:]}",
                        "cache-control": "public, max-age=31536000"  # Cache for 1 year
                    }
                )

                # Get public URL
                public_url = client.storage.from_(bucket_name).get_public_url(storage_path)

                print(f"  ✅ Uploaded to: {public_url[:80]}...")

                # Update database
                client.table('system_diagrams').update({
                    'image_url': public_url,
                    'source': f"{source} (cached)"
                }).eq('id', diagram_id).execute()

                print(f"  ✅ Database updated")

                cached_count += 1

            # Rate limit to avoid hammering Wikimedia
            time.sleep(1)

        except Exception as e:
            print(f"  ❌ Error: {e}")
            error_count += 1

        print()

    # Summary
    print("=" * 60)
    print("Summary:")
    print(f"  Total diagrams: {len(diagrams)}")
    print(f"  ✅ Cached: {cached_count}")
    print(f"  ⏭️  Skipped (already cached): {skipped_count}")
    print(f"  ❌ Errors: {error_count}")

    if dry_run:
        print("\n[DRY RUN] No changes were made. Run without --dry-run to cache images.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Cache system diagram images to Supabase Storage")
    parser.add_argument(
        "--bucket",
        default="system-diagrams",
        help="Supabase Storage bucket name (default: system-diagrams)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Download images but don't upload or update database"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("System Diagram Image Caching Tool")
    print("=" * 60)
    print()

    try:
        cache_all_diagrams(bucket_name=args.bucket, dry_run=args.dry_run)
        print("\n✅ Done!")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
