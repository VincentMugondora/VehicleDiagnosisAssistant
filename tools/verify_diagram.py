#!/usr/bin/env python3
"""
Verify a system diagram was imported correctly.
"""
import sys
import json
from app.db.client import get_supabase_client
from app.repositories.system_diagram_repository import SystemDiagramRepository

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def verify_diagram(system_name: str):
    """
    Retrieve and display a system diagram.

    Args:
        system_name: System name to look up
    """
    print(f"\n🔍 Looking up diagram for: {system_name}")

    # Get Supabase client
    supabase = get_supabase_client()
    if not supabase:
        print("❌ Failed to connect to Supabase")
        return None

    # Use repository
    repo = SystemDiagramRepository(supabase)
    diagram = repo.get_by_system_fuzzy(system_name)

    if not diagram:
        print(f"\n❌ No diagram found for '{system_name}'")
        return None

    # Convert to dict for display
    result = {
        'id': diagram.id,
        'system': diagram.system,
        'image_url': diagram.image_url,
        'source': diagram.source,
        'license': diagram.license,
        'caption': diagram.caption,
        'attribution_text': diagram.attribution_text
    }

    if result:
        print("\n✅ DIAGRAM FOUND!")
        print("="*70)
        print(json.dumps(result, indent=2))
        print("="*70)

        # Verify key fields
        checks = {
            "Has ID": bool(result.get('id')),
            "Has system name": bool(result.get('system')),
            "Has image URL": bool(result.get('image_url')),
            "URL is HTTPS": result.get('image_url', '').startswith('https://') if result.get('image_url') else False,
            "Has license": bool(result.get('license')),
            "Has source": bool(result.get('source'))
        }

        print("\n📋 VERIFICATION CHECKS:")
        for check, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"   {status} {check}")

        all_passed = all(checks.values())
        if all_passed:
            print("\n🎉 All checks passed!")
        else:
            print("\n⚠️  Some checks failed")

        return result
    else:
        print(f"\n❌ No diagram found for '{system_name}'")
        return None


if __name__ == "__main__":
    verify_diagram("catalytic converter")
