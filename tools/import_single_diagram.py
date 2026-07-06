#!/usr/bin/env python3
"""
Import a single system diagram directly to Supabase.
Quick import without interactive prompts.
"""
import sys
from app.db.client import get_supabase_client
from app.core.logging import logger

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def import_diagram(system: str, image_url: str, source: str, license: str,
                   caption: str = None, attribution_text: str = None):
    """
    Import a single diagram to database.

    Args:
        system: System name (e.g., "catalytic converter")
        image_url: HTTPS URL to image
        source: Source name (e.g., "Wikimedia Commons")
        license: License type (e.g., "CC0 1.0")
        caption: Optional caption
        attribution_text: Optional attribution text
    """
    print(f"\n📥 Importing diagram for: {system}")
    print(f"   URL: {image_url}")
    print(f"   License: {license}")

    # Connect to database
    print("\n📡 Connecting to Supabase...")
    supabase = get_supabase_client()
    if not supabase:
        print("❌ Failed to connect to Supabase")
        sys.exit(1)

    try:
        # Check for existing system
        existing = supabase.table("system_diagrams")\
            .select("id")\
            .eq("system", system)\
            .execute()

        if existing.data:
            print(f"⚠️  System '{system}' already exists")
            print("   Updating existing record...")

            # Update existing
            record = {
                'image_url': image_url,
                'source': source,
                'license': license,
                'caption': caption,
                'attribution_text': attribution_text
            }

            result = supabase.table("system_diagrams")\
                .update(record)\
                .eq("system", system)\
                .execute()

            print(f"✅ Updated '{system}' diagram")
            return result.data[0]
        else:
            # Insert new
            record = {
                'system': system,
                'image_url': image_url,
                'source': source,
                'license': license,
                'caption': caption,
                'attribution_text': attribution_text
            }

            result = supabase.table("system_diagrams").insert(record).execute()
            print(f"✅ Inserted '{system}' diagram")
            return result.data[0]

    except Exception as e:
        print(f"❌ Import failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Import the catalytic converter diagram
    result = import_diagram(
        system="catalytic converter",
        image_url="https://upload.wikimedia.org/wikipedia/commons/8/85/Catalytic_Converter_Interior.jpg",
        source="Wikimedia Commons",
        license="CC0 1.0",
        caption="Cutaway view of catalytic converter internal structure",
        attribution_text="Cyrogigabyte, CC0, via Wikimedia Commons"
    )

    print(f"\n✨ Import complete!")
    print(f"   ID: {result.get('id')}")
    print(f"   System: {result.get('system')}")
