"""
Test script for web code fetcher.
Tests if we can successfully fetch codes from online sources.
"""

import asyncio
import sys
sys.path.insert(0, '.')

from app.services.web_code_fetcher import WebCodeFetcher


async def test_fetch():
    """Test fetching various codes"""

    fetcher = WebCodeFetcher()

    # Test codes - start with VERY common ones
    test_codes = [
        "P0420",  # Very common - catalytic converter
        "P0300",  # Very common - random misfire
        "P2177",  # Less common but should exist
        "P3499",  # Rare - cylinder deactivation
    ]

    print("=" * 70)
    print("Web Code Fetcher Test")
    print("=" * 70)
    print()

    for code in test_codes:
        print(f"\n{'='*70}")
        print(f"Testing: {code}")
        print(f"{'='*70}")

        try:
            result = await fetcher.fetch_code(code)

            if result:
                print(f"✅ SUCCESS")
                print(f"Description: {result.get('description', 'N/A')[:100]}...")
                print(f"Source: {result.get('source', 'N/A')}")
                print(f"Symptoms: {result.get('symptoms', 'N/A')[:100]}...")
                print(f"Causes: {result.get('common_causes', 'N/A')[:100]}...")
            else:
                print(f"❌ FAILED - No data returned")

        except Exception as e:
            print(f"❌ ERROR: {e}")

    print()
    print("=" * 70)
    print("Test Complete")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_fetch())
