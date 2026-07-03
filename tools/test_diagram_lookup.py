#!/usr/bin/env python3
"""
Test system diagram lookup and matching for specific DTC codes.

Usage:
    python tools/test_diagram_lookup.py P0420
    python tools/test_diagram_lookup.py "catalytic converter"

Shows:
- DTC system field
- Fuzzy matching process
- Final matched diagram
- What user would see
"""
import sys
from app.db.client import get_supabase_client
from app.repositories.obd_repository import OBDRepository
from app.repositories.system_diagram_repository import SystemDiagramRepository
from app.services.image_sender import format_attribution

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def test_dtc_lookup(code: str):
    """Test diagram lookup for a DTC code"""
    print("="*70)
    print(f"TEST: DTC Code {code}")
    print("="*70)

    # Connect to database
    supabase = get_supabase_client()
    obd_repo = OBDRepository(supabase)
    diagram_repo = SystemDiagramRepository(supabase)

    # Lookup DTC
    print(f"\n1. Looking up DTC: {code}")
    dtc = obd_repo.get_by_code(code)

    if not dtc:
        print(f"   ❌ DTC not found in database")
        return

    print(f"   ✅ Found: {dtc.get('description', 'N/A')}")

    system = dtc.get('system')
    if not system:
        print(f"   ⚠️  No system field in DTC record")
        return

    print(f"   📋 System: {system}")

    # Lookup diagram
    print(f"\n2. Looking up diagram for system: '{system}'")
    diagram = diagram_repo.get_by_system_fuzzy(system)

    if not diagram:
        print(f"   ❌ No diagram found for system '{system}'")
        print(f"\n   This is expected if you haven't added this system yet.")
        print(f"   Add a diagram with system matching '{system}' (or synonym)")
        return

    print(f"   ✅ Found diagram!")
    print(f"   📋 Matched system: {diagram.system}")
    print(f"   🔗 Image URL: {diagram.image_url}")
    print(f"   📄 Source: {diagram.source}")
    print(f"   ⚖️  License: {diagram.license}")

    if diagram.caption:
        print(f"   💬 Caption: {diagram.caption}")

    if diagram.attribution_text:
        print(f"   📷 Attribution: {diagram.attribution_text}")

    # Show what user sees
    print(f"\n3. What user would see:")
    print(f"   " + "─"*66)
    print(f"   [IMAGE MESSAGE]")
    if diagram.caption:
        print(f"   📷 {diagram.caption}")
    print(f"   🔗 {diagram.image_url[:60]}...")
    print(f"   " + "─"*66)
    print(f"   [TEXT MESSAGE - sent 1-2 seconds later]")
    print(f"   🔧 {code}: {dtc.get('description', 'N/A')}")
    print(f"   ...")
    if diagram.attribution_text:
        attribution = format_attribution(diagram)
        if attribution:
            print(f"   {attribution.strip()}")
    print(f"   " + "─"*66)

    print(f"\n✅ Complete flow verified!")


def test_system_lookup(system: str):
    """Test diagram lookup for a system name directly"""
    print("="*70)
    print(f"TEST: System Name '{system}'")
    print("="*70)

    # Connect to database
    supabase = get_supabase_client()
    diagram_repo = SystemDiagramRepository(supabase)

    # Lookup diagram
    print(f"\n1. Looking up diagram with fuzzy matching...")
    diagram = diagram_repo.get_by_system_fuzzy(system)

    if not diagram:
        print(f"   ❌ No diagram found for '{system}'")
        print(f"\n   Fuzzy matching tried:")
        print(f"   1. Exact match for '{system}'")
        print(f"   2. Synonym lookup")
        print(f"   3. Substring match (if >5 chars)")
        print(f"\n   No match found.")
        return

    print(f"   ✅ Found diagram!")
    print(f"   📋 Matched system: {diagram.system}")
    print(f"   🔗 Image URL: {diagram.image_url}")
    print(f"   📄 Source: {diagram.source}")
    print(f"   ⚖️  License: {diagram.license}")

    if diagram.caption:
        print(f"   💬 Caption: {diagram.caption}")
        print(f"   📏 Length: {len(diagram.caption)} chars {'✅' if len(diagram.caption) <= 60 else '⚠️ TOO LONG'}")

    if diagram.attribution_text:
        print(f"   📷 Attribution: {diagram.attribution_text}")

    print(f"\n✅ System lookup verified!")


def list_all_diagrams():
    """List all diagrams in database"""
    print("="*70)
    print("ALL SYSTEM DIAGRAMS")
    print("="*70)

    supabase = get_supabase_client()
    response = supabase.table("system_diagrams").select("*").order("system").execute()

    if not response.data:
        print("\n⚠️  No diagrams found in database")
        print("\nRun the migration first:")
        print("  migrations/add_system_diagrams_table.sql")
        print("\nThen import diagrams:")
        print("  python tools/import_diagrams_from_csv.py system_diagrams.csv")
        return

    print(f"\n📋 Found {len(response.data)} diagrams:\n")

    for i, diagram in enumerate(response.data, 1):
        print(f"{i}. {diagram['system']}")
        print(f"   URL: {diagram['image_url'][:60]}...")
        print(f"   License: {diagram['license']}")
        if diagram.get('caption'):
            print(f"   Caption: {diagram['caption']}")
        print()


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python test_diagram_lookup.py P0420")
        print("  python test_diagram_lookup.py 'catalytic converter'")
        print("  python test_diagram_lookup.py --list")
        print("\nTests diagram lookup and matching logic.")
        sys.exit(1)

    arg = sys.argv[1]

    if arg == '--list':
        list_all_diagrams()
    elif arg.startswith('P') and len(arg) == 5:
        # Looks like DTC code
        test_dtc_lookup(arg.upper())
    else:
        # Assume system name
        test_system_lookup(arg)


if __name__ == "__main__":
    main()
