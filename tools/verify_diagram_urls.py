#!/usr/bin/env python3
"""
Verify system diagram URLs are accessible and valid.

Usage:
    python tools/verify_diagram_urls.py

Checks:
- URL is accessible (HTTP 200)
- Content-Type is image/*
- Image size is reasonable (<10MB)
- Response time is acceptable (<5s)

Reports broken/slow URLs for fixing.
"""
import sys
import asyncio
import httpx
from app.db.client import get_supabase_client
from app.repositories.system_diagram_repository import SystemDiagramRepository

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


async def verify_url(url: str, timeout: float = 5.0) -> dict:
    """
    Verify a single image URL.

    Args:
        url: Image URL to verify
        timeout: Max seconds to wait

    Returns:
        Dict with verification results
    """
    result = {
        'url': url,
        'accessible': False,
        'is_image': False,
        'size_mb': None,
        'response_time': None,
        'status_code': None,
        'error': None
    }

    try:
        import time
        start = time.time()

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.head(url, follow_redirects=True)
            result['response_time'] = time.time() - start
            result['status_code'] = response.status_code

            # Check status
            if response.status_code == 200:
                result['accessible'] = True

                # Check content type
                content_type = response.headers.get('content-type', '')
                result['is_image'] = content_type.startswith('image/')

                # Check size
                content_length = response.headers.get('content-length')
                if content_length:
                    size_bytes = int(content_length)
                    result['size_mb'] = size_bytes / (1024 * 1024)
            else:
                result['error'] = f"HTTP {response.status_code}"

    except asyncio.TimeoutError:
        result['error'] = f"Timeout (>{timeout}s)"
    except Exception as e:
        result['error'] = str(e)

    return result


async def verify_all_diagrams():
    """Verify all diagram URLs in database"""
    print("="*70)
    print("SYSTEM DIAGRAM URL VERIFICATION")
    print("="*70)

    # Connect to database
    print("\n📡 Connecting to Supabase...")
    supabase = get_supabase_client()
    if not supabase:
        print("❌ Failed to connect to Supabase")
        sys.exit(1)

    # Fetch all diagrams
    print("📥 Fetching diagrams...")
    response = supabase.table("system_diagrams").select("*").execute()

    if not response.data:
        print("⚠️  No diagrams found in database")
        print("\nRun the migration first:")
        print("  migrations/add_system_diagrams_table.sql")
        return

    diagrams = response.data
    print(f"✅ Found {len(diagrams)} diagrams\n")

    # Verify each URL
    print("🔍 Verifying URLs...\n")

    results = []
    for i, diagram in enumerate(diagrams, 1):
        system = diagram['system']
        url = diagram['image_url']

        print(f"[{i}/{len(diagrams)}] {system}...")
        result = await verify_url(url)
        results.append((diagram, result))

        # Status
        if result['accessible'] and result['is_image']:
            size = f"{result['size_mb']:.2f}MB" if result['size_mb'] else "unknown"
            time_str = f"{result['response_time']:.2f}s" if result['response_time'] else "N/A"
            print(f"  ✅ OK - {size}, {time_str}")
        elif result['accessible'] and not result['is_image']:
            print(f"  ⚠️  Not an image (content-type issue)")
        else:
            print(f"  ❌ Failed: {result['error']}")

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)

    ok_count = sum(1 for _, r in results if r['accessible'] and r['is_image'])
    failed_count = sum(1 for _, r in results if not r['accessible'])
    not_image_count = sum(1 for _, r in results if r['accessible'] and not r['is_image'])

    print(f"✅ Accessible images: {ok_count}/{len(diagrams)}")
    if failed_count:
        print(f"❌ Failed/timeout: {failed_count}")
    if not_image_count:
        print(f"⚠️  Not images: {not_image_count}")

    # Large files warning
    large_files = [(d, r) for d, r in results if r.get('size_mb') and r['size_mb'] > 5]
    if large_files:
        print(f"\n⚠️  Large files (>5MB): {len(large_files)}")
        for diagram, result in large_files:
            print(f"  • {diagram['system']}: {result['size_mb']:.2f}MB")
        print("  Consider optimizing these for faster WhatsApp delivery")

    # Slow responses warning
    slow_responses = [(d, r) for d, r in results if r.get('response_time') and r['response_time'] > 2]
    if slow_responses:
        print(f"\n⚠️  Slow responses (>2s): {len(slow_responses)}")
        for diagram, result in slow_responses:
            print(f"  • {diagram['system']}: {result['response_time']:.2f}s")
        print("  These may timeout in production (10s limit)")

    # Failed details
    failed = [(d, r) for d, r in results if not r['accessible']]
    if failed:
        print(f"\n❌ FAILED URLS ({len(failed)}):")
        for diagram, result in failed:
            print(f"\n  System: {diagram['system']}")
            print(f"  URL: {result['url']}")
            print(f"  Error: {result['error']}")

    print("\n" + "="*70)

    if ok_count == len(diagrams):
        print("✅ All diagrams verified successfully!")
    else:
        print(f"⚠️  {failed_count + not_image_count} issue(s) need fixing")

    print("="*70)


def main():
    """Main entry point"""
    asyncio.run(verify_all_diagrams())


if __name__ == "__main__":
    main()
