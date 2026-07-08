"""
Search Openverse API for generic fallback images.

Uses license_type=commercial to pre-filter for suitable licenses.
"""
import requests
import json
from typing import List, Dict


OPENVERSE_API = "https://api.openverse.org/v1/images/"

# Search queries for each category
SEARCH_QUERIES = {
    'powertrain': [
        'engine bay car',
        'car engine compartment',
    ],
    'body': [
        'car dashboard warning lights',
        'vehicle dashboard indicators',
    ],
    'chassis': [
        'car brake system',
        'wheel brake assembly automotive',
    ],
    'network': [
        'automotive wiring harness',
        'car electrical connector',
    ]
}


def search_openverse(query: str, page_size: int = 5) -> List[Dict]:
    """
    Search Openverse API for images.

    Args:
        query: Search term
        page_size: Number of results to return (max 20)

    Returns:
        List of image results with metadata
    """
    params = {
        'q': query,
        'license_type': 'commercial',  # Only commercial-use licenses
        'page_size': page_size,
    }

    try:
        response = requests.get(OPENVERSE_API, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        return data.get('results', [])
    except Exception as e:
        print(f"Error searching Openverse: {e}")
        return []


def format_candidate(result: Dict, rank: int) -> Dict:
    """Extract and format relevant metadata from Openverse result."""

    return {
        'rank': rank,
        'title': result.get('title', 'Untitled'),
        'creator': result.get('creator', 'Unknown'),
        'license': result.get('license', 'Unknown'),
        'license_version': result.get('license_version', ''),
        'license_url': result.get('license_url', ''),
        'source': result.get('source', 'Unknown'),
        'provider': result.get('provider', 'Unknown'),
        'image_url': result.get('url', ''),
        'thumbnail': result.get('thumbnail', ''),
        'foreign_landing_url': result.get('foreign_landing_url', ''),  # Link to original
        'width': result.get('width'),
        'height': result.get('height'),
        'filesize': result.get('filesize'),
    }


def main():
    print("=" * 80)
    print("OPENVERSE API SEARCH - GENERIC FALLBACK IMAGES")
    print("=" * 80)
    print()
    print("Searching for 4 categories with license_type=commercial...")
    print()

    all_candidates = {}

    for category, queries in SEARCH_QUERIES.items():
        print(f"\n{'=' * 80}")
        print(f"CATEGORY: {category.upper()}")
        print('=' * 80)

        candidates = []

        for query in queries:
            print(f"\nSearching: '{query}'")
            results = search_openverse(query, page_size=3)

            if results:
                print(f"  Found {len(results)} results")
                for i, result in enumerate(results[:2], start=1):  # Take top 2 per query
                    candidate = format_candidate(result, len(candidates) + 1)
                    candidates.append(candidate)
            else:
                print(f"  No results")

        all_candidates[category] = candidates

        # Display candidates for this category
        print()
        print(f"Candidates for {category}:")
        print("-" * 80)

        for candidate in candidates[:3]:  # Show top 3 per category
            print(f"\n#{candidate['rank']}: {candidate['title']}")
            print(f"  Creator: {candidate['creator']}")
            print(f"  License: {candidate['license']} {candidate['license_version']}")
            print(f"  Source: {candidate['source']}")
            print(f"  Provider: {candidate['provider']}")
            print(f"  Image URL: {candidate['image_url']}")
            print(f"  View original: {candidate['foreign_landing_url']}")
            if candidate['width'] and candidate['height']:
                print(f"  Dimensions: {candidate['width']}x{candidate['height']}")

    print("\n" + "=" * 80)
    print("SEARCH COMPLETE")
    print("=" * 80)
    print()
    print(f"Total candidates found:")
    for category, candidates in all_candidates.items():
        print(f"  {category}: {len(candidates)} candidates")

    # Save to JSON for reference
    with open('generic_fallback_candidates.json', 'w') as f:
        json.dump(all_candidates, f, indent=2)

    print()
    print("Candidates saved to: generic_fallback_candidates.json")
    print()
    print("Next steps:")
    print("1. Review candidates above")
    print("2. View actual images at the 'foreign_landing_url' links")
    print("3. Choose one per category")
    print("4. Verify license on original source")
    print("5. Download, optimize, and insert approved images")


if __name__ == '__main__':
    main()
