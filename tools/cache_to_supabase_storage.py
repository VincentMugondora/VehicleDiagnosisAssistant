#!/usr/bin/env python3
"""
Cache system diagram images to Supabase Storage.

Downloads each diagram image from Wikimedia, uploads to Supabase Storage,
and updates the database to point to the Supabase Storage URL.

This eliminates the 18-53s delay caused by re-downloading from Wikimedia
on every diagnostic request.

Usage:
    python -m tools.cache_to_supabase_storage [--dry-run] [--bucket BUCKET_NAME]
"""
import sys
import time
import argparse
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from app.db.client import get_supabase_client

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def download_image(url: str, timeout: int = 30, retries: int = 3) -> tuple[bytes, str]:
    """
    Download image from URL with retry logic.

    Args:
        url: Image URL
        timeout: Request timeout in seconds
        retries: Number of retry attempts for rate limiting

    Returns:
        Tuple of (image_bytes, content_type)

    Raises:
        Exception: If download fails after all retries
    """
    headers = {
        "User-Agent": "VehicleDiagnosisBot/1.0 (Educational diagnostic system; caching to Supabase Storage)"
    }

    for attempt in range(retries + 1):
        try:
            with httpx.Client(timeout=timeout, follow_redirects=True) as client:
                response = client.get(url, headers=headers)

                # If rate limited, wait and retry
                if response.status_code == 429 and attempt < retries:
                    backoff = (2 ** attempt) * 5  # 5s, 10s, 20s
                    print(f"  ⏳ Rate limited (429), waiting {backoff}s before retry {attempt + 1}/{retries}...")
                    time.sleep(backoff)
                    continue

                response.raise_for_status()

                content_type = response.headers.get('content-type', 'image/jpeg')
                if not content_type.startswith('image/'):
                    raise ValueError(f"URL did not return an image (got {content_type})")

                return response.content, content_type

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429 and attempt < retries:
                continue
            raise
        except Exception as e:
            if attempt == retries:
                raise
            print(f"  ⚠️  Attempt {attempt + 1} failed: {e}, retrying...")
            time.sleep(2)

    raise Exception("Failed after all retry attempts")


def get_file_extension(url: str, content_type: str) -> str:
    """
    Infer file extension from URL or content type.

    Args:
        url: Image URL
        content_type: MIME type

    Returns:
        File extension (e.g., "jpg", "png")
    """
    # Try content type first
    if 'jpeg' in content_type or 'jpg' in content_type:
        return 'jpg'
    elif 'png' in content_type:
        return 'png'
    elif 'gif' in content_type:
        return 'gif'
    elif 'svg' in content_type:
        return 'svg'
    elif 'webp' in content_type:
        return 'webp'

    # Fallback to URL extension
    url_lower = url.lower()
    if '.jpg' in url_lower or '.jpeg' in url_lower:
        return 'jpg'
    elif '.png' in url_lower:
        return 'png'
    elif '.gif' in url_lower:
        return 'gif'
    elif '.svg' in url_lower:
        return 'svg'
    elif '.webp' in url_lower:
        return 'webp'

    # Default
    return 'jpg'


def sanitize_filename(system_name: str) -> str:
    """
    Sanitize system name for storage path.

    Args:
        system_name: System name (e.g., "catalytic converter")

    Returns:
        Sanitized filename (e.g., "catalytic-converter")
    """
    return system_name.lower().replace(' ', '-').replace('/', '-')


def cache_all_diagrams(bucket_name: str = "system-diagrams", dry_run: bool = False):
    """
    Cache all system diagrams to Supabase Storage.

    Args:
        bucket_name: Supabase Storage bucket name
        dry_run: If True, download but don't upload or update database
    """
    print('=' * 80)
    print('System Diagram Image Caching Tool (Supabase Storage)')
    print('=' * 80)
    print()

    client = get_supabase_client()
    if not client:
        raise Exception("Failed to initialize Supabase client")

    # Ensure bucket exists (if not dry run)
    if not dry_run:
        try:
            buckets = client.storage.list_buckets()
            bucket_exists = any(b['name'] == bucket_name for b in buckets)

            if not bucket_exists:
                print(f"Creating storage bucket: {bucket_name}")
                client.storage.create_bucket(
                    bucket_name,
                    options={
                        "public": True,  # Make images publicly accessible
                        "fileSizeLimit": 10485760,  # 10MB limit per file
                        "allowedMimeTypes": ["image/jpeg", "image/png", "image/gif", "image/svg+xml", "image/webp"]
                    }
                )
                print(f"✅ Bucket created\n")
            else:
                print(f"Using existing bucket: {bucket_name}\n")
        except Exception as e:
            print(f"⚠️  Warning: Could not check/create bucket: {e}\n")

    # Fetch all diagrams
    print("Fetching diagrams from database...")
    result = client.table('system_diagrams').select(
        'id, system, image_url, source'
    ).order('system').execute()

    diagrams = result.data
    print(f"Found {len(diagrams)} diagrams to cache\n")

    cached_count = 0
    skipped_count = 0
    error_count = 0

    for i, diagram in enumerate(diagrams, 1):
        system = diagram['system']
        image_url = diagram['image_url']
        diagram_id = diagram['id']
        source = diagram.get('source', '')

        print(f"[{i}/{len(diagrams)}] Processing: {system}")

        # Skip if already cached (not a wikimedia URL)
        if 'wikimedia.org' not in image_url and 'wikipedia.org' not in image_url:
            print(f"  ⏭️  Already cached (not a Wikimedia URL)\n")
            skipped_count += 1
            continue

        try:
            # Download image
            print(f"  Downloading from: {image_url[:80]}...")
            image_bytes, content_type = download_image(image_url)
            print(f"  ✅ Downloaded {len(image_bytes):,} bytes ({content_type})")

            # Determine storage path
            extension = get_file_extension(image_url, content_type)
            filename = f"{sanitize_filename(system)}.{extension}"
            storage_path = f"diagrams/{filename}"

            print(f"  Storage path: {storage_path}")

            if dry_run:
                print(f"  [DRY RUN] Would upload {len(image_bytes):,} bytes to {bucket_name}/{storage_path}")
                print(f"  [DRY RUN] Would update database with Supabase Storage URL")
            else:
                # Upload to Supabase Storage
                print(f"  Uploading to Supabase Storage...")

                # Check if file already exists and remove it
                try:
                    client.storage.from_(bucket_name).remove([storage_path])
                except:
                    pass  # File might not exist, that's fine

                # Upload new file
                upload_result = client.storage.from_(bucket_name).upload(
                    storage_path,
                    image_bytes,
                    file_options={
                        "content-type": content_type,
                        "cache-control": "public, max-age=31536000, immutable"  # Cache for 1 year
                    }
                )

                # Get public URL
                public_url = client.storage.from_(bucket_name).get_public_url(storage_path)

                print(f"  ✅ Uploaded: {public_url[:80]}...")

                # Update database
                update_result = client.table('system_diagrams').update({
                    'image_url': public_url,
                    'source': f"{source} (cached in Supabase Storage)"
                }).eq('id', diagram_id).execute()

                print(f"  ✅ Database updated")
                cached_count += 1

            # Rate limit to be nice to Wikimedia
            time.sleep(3)

        except Exception as e:
            print(f"  ❌ Error: {e}")
            error_count += 1

        print()

    # Summary
    print('=' * 80)
    print('Summary:')
    print(f"  Total diagrams: {len(diagrams)}")
    print(f"  ✅ Cached: {cached_count}")
    print(f"  ⏭️  Skipped (already cached): {skipped_count}")
    print(f"  ❌ Errors: {error_count}")

    if dry_run:
        print('\n[DRY RUN] No changes were made. Run without --dry-run to cache images.')


def main():
    parser = argparse.ArgumentParser(
        description="Cache system diagram images to Supabase Storage"
    )
    parser.add_argument(
        '--bucket',
        default='system-diagrams',
        help='Supabase Storage bucket name (default: system-diagrams)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Download images but don\'t upload or update database'
    )

    args = parser.parse_args()

    try:
        cache_all_diagrams(bucket_name=args.bucket, dry_run=args.dry_run)
        print('\n✅ Done!')
    except Exception as e:
        print(f'\n❌ Fatal error: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
