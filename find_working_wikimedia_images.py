"""
Find and verify working Wikimedia Commons automotive component images.
"""
import httpx
import asyncio

# Potential Wikimedia Commons images to test
# Format: (system_name, list_of_potential_urls)
POTENTIAL_IMAGES = {
    "catalytic converter": [
        "https://upload.wikimedia.org/wikipedia/commons/4/44/Catalytic_converter_cut_open.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/44/Catalytic_converter_cut_open.jpg/800px-Catalytic_converter_cut_open.jpg",
        "https://commons.wikimedia.org/wiki/Special:FilePath/Catalytic_converter_cut_open.jpg",
    ],
    "oxygen sensor": [
        "https://upload.wikimedia.org/wikipedia/commons/e/e5/Lambda_sonde.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e5/Lambda_sonde.jpg/800px-Lambda_sonde.jpg",
    ],
    "mass air flow sensor": [
        "https://upload.wikimedia.org/wikipedia/commons/f/f8/MAF_sensor.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f8/MAF_sensor.jpg/800px-MAF_sensor.jpg",
    ],
    "throttle body": [
        "https://upload.wikimedia.org/wikipedia/commons/d/d0/Throttle_body.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d0/Throttle_body.jpg/800px-Throttle_body.jpg",
    ],
    "evap system": [
        "https://upload.wikimedia.org/wikipedia/commons/5/59/Evap_canister.jpg",
    ],
    "fuel injector": [
        "https://upload.wikimedia.org/wikipedia/commons/7/7f/Fuel_injector.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7f/Fuel_injector.jpg/800px-Fuel_injector.jpg",
    ],
    "egr valve": [
        "https://upload.wikimedia.org/wikipedia/commons/8/8f/EGR_valve.jpg",
    ],
    "ignition coil": [
        "https://upload.wikimedia.org/wikipedia/commons/1/1f/Ignition_coil.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a9/Ignition_coils.jpg/800px-Ignition_coils.jpg",
    ],
    "camshaft position sensor": [
        "https://upload.wikimedia.org/wikipedia/commons/0/04/Camshaft_sensor.jpg",
    ],
    "crankshaft position sensor": [
        "https://upload.wikimedia.org/wikipedia/commons/9/9e/Crankshaft_sensor.jpg",
    ],
}

async def test_url(url: str) -> tuple[str, int]:
    """Test if a URL returns 200 OK."""
    try:
        headers = {
            "User-Agent": "VehicleDiagnosisAssistant/2.0 (Educational Project)"
        }
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.head(url, headers=headers, follow_redirects=True)
            return (url, response.status_code)
    except Exception as e:
        return (url, 0)  # 0 = error

async def find_working_urls():
    """Find working URLs for all systems."""
    working_urls = {}

    print("Testing Wikimedia URLs...\n")

    for system, urls in POTENTIAL_IMAGES.items():
        print(f"Testing: {system}")

        # Test all URLs for this system
        results = await asyncio.gather(*[test_url(url) for url in urls])

        # Find first working URL
        working_url = None
        for url, status in results:
            print(f"  {status:3d} - {url[:80]}...")
            if status == 200 and not working_url:
                working_url = url

        if working_url:
            working_urls[system] = working_url
            print(f"  [OK] WORKING: {working_url}")
        else:
            print(f"  [FAIL] NO WORKING URL FOUND")
        print()

    print("=" * 80)
    print("SUMMARY - Working URLs:")
    print("=" * 80)
    for system, url in working_urls.items():
        print(f"{system:30s}: {url}")
    print()
    print(f"Found {len(working_urls)}/{len(POTENTIAL_IMAGES)} working URLs")

    return working_urls

if __name__ == "__main__":
    asyncio.run(find_working_urls())
