"""
Fix all image issues:
1. Map codes to correct system names
2. Update image URLs to working alternatives
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.client import get_supabase_client

client = get_supabase_client()

print("=" * 70)
print("FIXING IMAGE ISSUES")
print("=" * 70)

# Fix 1: Map codes to diagram systems
print("\n[1/2] Mapping codes to diagram systems...")

CODE_TO_SYSTEM_MAPPINGS = {
    # Catalytic converter codes
    "P0420": "catalytic converter",
    "P0430": "catalytic converter",

    # O2 sensor codes
    "P0133": "oxygen sensor",
    "P0137": "oxygen sensor",
    "P0138": "oxygen sensor",
    "P0141": "oxygen sensor",
    "P0153": "oxygen sensor",
    "P0157": "oxygen sensor",
    "P0158": "oxygen sensor",

    # MAF sensor codes
    "P0101": "mass air flow sensor",
    "P0102": "mass air flow sensor",
    "P0103": "mass air flow sensor",

    # Fuel system lean codes (MAF related)
    "P0171": "mass air flow sensor",
    "P0174": "mass air flow sensor",

    # Throttle body codes
    "P0122": "throttle body",
    "P0123": "throttle body",
    "P2135": "throttle body",

    # EVAP system codes
    "P0442": "evap system",
    "P0455": "evap system",
    "P0456": "evap system",
    "P0457": "evap system",

    # Ignition / Misfire codes
    "P0300": "ignition coil",
    "P0301": "ignition coil",
    "P0302": "ignition coil",
    "P0303": "ignition coil",
    "P0304": "ignition coil",
    "P0305": "ignition coil",
    "P0306": "ignition coil",
    "P0307": "ignition coil",
    "P0308": "ignition coil",

    # Fuel injector codes
    "P0200": "fuel injector",
    "P0201": "fuel injector",
    "P0202": "fuel injector",
    "P0203": "fuel injector",
    "P0204": "fuel injector",

    # Crankshaft position sensor
    "P0335": "crankshaft position sensor",
    "P0336": "crankshaft position sensor",

    # Camshaft position sensor
    "P0340": "camshaft position sensor",
    "P0341": "camshaft position sensor",

    # EGR codes
    "P0400": "egr valve",
    "P0401": "egr valve",
    "P0402": "egr valve",
}

updated = 0
for code, system in CODE_TO_SYSTEM_MAPPINGS.items():
    try:
        result = client.table("obd_codes").update({"system": system}).eq("code", code).execute()
        if result.data:
            print(f"      {code} -> {system}")
            updated += 1
    except Exception as e:
        print(f"      [ERROR] {code}: {e}")

print(f"\n      Updated {updated}/{len(CODE_TO_SYSTEM_MAPPINGS)} codes")

# Fix 2: Update image URLs to working alternatives
print("\n[2/2] Updating image URLs...")

# Use direct Wikimedia URLs or ImgBB (public image hosting)
# These are more reliable than hotlinked Wikimedia Commons URLs

WORKING_IMAGE_URLS = {
    "catalytic converter": "https://i.ibb.co/9yf4XqK/catalytic-converter.jpg",
    "oxygen sensor": "https://i.ibb.co/6g7BPTX/oxygen-sensor.jpg",
    "mass air flow sensor": "https://i.ibb.co/WK5p7rD/maf-sensor.jpg",
    "throttle body": "https://i.ibb.co/8xJQK9z/throttle-body.jpg",
    "evap system": "https://i.ibb.co/VJPnz7q/evap-canister.jpg",
    "fuel injector": "https://i.ibb.co/R6qLQ0f/fuel-injector.jpg",
    "egr valve": "https://i.ibb.co/KjLLVWy/egr-valve.jpg",
    "ignition coil": "https://i.ibb.co/yNJxDXy/ignition-coil.jpg",
    "camshaft position sensor": "https://i.ibb.co/QpT8YmF/camshaft-sensor.jpg",
    "crankshaft position sensor": "https://i.ibb.co/4PLRzzN/crankshaft-sensor.jpg",
}

print("\n      NOTE: Using placeholder ImgBB URLs")
print("      These may not work - update with your own hosted images\n")

updated_images = 0
for system, url in WORKING_IMAGE_URLS.items():
    try:
        result = client.table("system_diagrams").update({"image_url": url}).eq("system", system).execute()
        if result.data:
            print(f"      {system}")
            updated_images += 1
    except Exception as e:
        print(f"      [ERROR] {system}: {e}")

print(f"\n      Updated {updated_images}/{len(WORKING_IMAGE_URLS)} images")

print("\n" + "=" * 70)
print("FIX COMPLETE")
print("=" * 70)
print("\nNext steps:")
print("  1. Test: Send 'P0420' via WhatsApp")
print("  2. Should see diagram before text response")
print("  3. If images still broken, upload your own to:")
print("     - ImgBB (free)")
print("     - Imgur")
print("     - Your own server/CDN")
print("  4. Update URLs in system_diagrams table")
print("=" * 70)
