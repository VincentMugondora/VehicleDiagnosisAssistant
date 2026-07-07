"""
Update database to use local placeholder images.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.db.client import get_supabase_client
from app.core.config import settings

# Map system names to local image filenames
LOCAL_IMAGES = {
    "catalytic converter": "http://localhost:8000/static/images/catalytic-converter.svg",
    "oxygen sensor": "http://localhost:8000/static/images/oxygen-sensor.svg",
    "mass air flow sensor": "http://localhost:8000/static/images/maf-sensor.svg",
    "throttle body": "http://localhost:8000/static/images/throttle-body.svg",
    "evap system": "http://localhost:8000/static/images/evap-system.svg",
    "fuel injector": "http://localhost:8000/static/images/fuel-injector.svg",
    "egr valve": "http://localhost:8000/static/images/egr-valve.svg",
    "ignition coil": "http://localhost:8000/static/images/ignition-coil.svg",
    "camshaft position sensor": "http://localhost:8000/static/images/camshaft-sensor.svg",
    "crankshaft position sensor": "http://localhost:8000/static/images/crankshaft-sensor.svg",
}

def update_to_local_images():
    """Update all system diagram URLs to use local images."""
    client = get_supabase_client()

    print("Updating to local placeholder images...")
    print()

    for system, local_url in LOCAL_IMAGES.items():
        print(f"Updating: {system}")
        print(f"  New URL: {local_url}")

        try:
            client.table('system_diagrams').update({
                'image_url': local_url,
                'source': 'Local',
                'license': 'Placeholder',
                'attribution_text': None
            }).eq('system', system).execute()
            print(f"  [OK] Updated")
        except Exception as e:
            print(f"  [ERROR] {e}")
        print()

    print("=" * 70)
    print(f"Updated {len(LOCAL_IMAGES)} systems to use local images")
    print()
    print("Images available at:")
    print("  http://localhost:8000/static/images/")

if __name__ == '__main__':
    update_to_local_images()
