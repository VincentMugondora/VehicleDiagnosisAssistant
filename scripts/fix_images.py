"""
Complete diagnostic and fix script for images not showing
Checks all potential issues and suggests fixes
"""
import sys
import requests
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.client import get_supabase_client
from app.core.config import settings

def main():
    print("=" * 70)
    print("IMAGE SYSTEM DIAGNOSTIC & FIX SCRIPT")
    print("=" * 70)

    client = get_supabase_client()
    issues = []

    # Check 1: Diagrams in database
    print("\n[1/6] Checking diagrams in database...")
    try:
        result = client.table("system_diagrams").select("system", count="exact").execute()
        count = result.count
        print(f"      Found: {count} diagrams")

        if count == 0:
            issues.append("No diagrams in database")
            print("      [ERROR] ISSUE: No diagrams found")
            print("      FIX: Run 'python scripts\\populate_all_tables.py'")
        else:
            print("      [OK] PASS")
    except Exception as e:
        issues.append(f"Database error: {e}")
        print(f"      [ERROR] {e}")

    # Check 2: Sample image URLs
    print("\n[2/6] Testing sample image URLs...")
    try:
        result = client.table("system_diagrams").select("system, image_url").limit(3).execute()
        broken = []
        working = []

        for d in result.data:
            try:
                r = requests.head(d["image_url"], timeout=5, allow_redirects=True)
                if r.status_code == 200:
                    working.append(d['system'])
                    print(f"      [OK] {d['system']}: {r.status_code}")
                else:
                    broken.append(d['system'])
                    print(f"      [ERROR] {d['system']}: {r.status_code}")
            except Exception as e:
                broken.append(d['system'])
                print(f"      [ERROR] {d['system']}: {str(e)[:50]}")

        if broken:
            issues.append(f"{len(broken)} broken image URLs")
            print(f"\n      [WARN]  {len(broken)}/{len(result.data)} URLs broken")
            print("      FIX: Update image_url in system_diagrams table")
        else:
            print(f"      [OK] PASS: All {len(working)} URLs working")

    except Exception as e:
        issues.append(f"URL test error: {e}")
        print(f"      [ERROR] ERROR: {e}")

    # Check 3: Code-to-diagram mapping
    print("\n[3/6] Checking code-to-diagram mappings...")
    try:
        # Check P0420 (common catalytic converter code)
        result = client.table("obd_codes").select("code, system").eq("code", "P0420").execute()

        if result.data:
            code_system = result.data[0]['system']
            print(f"      P0420 system field: '{code_system}'")

            # Check if diagram exists for this system
            diagram_result = client.table("system_diagrams").select("system").ilike("system", code_system).execute()

            if diagram_result.data:
                print(f"      [OK] Diagram found for '{code_system}'")
                print(f"         Matched: '{diagram_result.data[0]['system']}'")
            else:
                issues.append(f"No diagram for P0420 system '{code_system}'")
                print(f"      [ERROR] ISSUE: No diagram matches '{code_system}'")
                print("      FIX: Either:")
                print(f"           1. Add diagram for system '{code_system}'")
                print("           2. Update P0420 system to 'catalytic converter'")
        else:
            issues.append("P0420 code not found in database")
            print("      [ERROR] ISSUE: P0420 not in obd_codes table")
            print("      FIX: Run 'python scripts\\populate_all_tables.py'")

    except Exception as e:
        issues.append(f"Mapping check error: {e}")
        print(f"      [ERROR] ERROR: {e}")

    # Check 4: Baileys configuration
    print("\n[4/6] Checking Baileys configuration...")
    baileys_url = getattr(settings, 'baileys_outbound_url', None)

    if baileys_url:
        print(f"      BAILEYS_OUTBOUND_URL: {baileys_url}")
        print("      [OK] PASS: URL configured")
    else:
        issues.append("Baileys outbound URL not configured")
        print("      [ERROR] ISSUE: BAILEYS_OUTBOUND_URL not set in .env")
        print("      FIX: Add to .env:")
        print("           BAILEYS_OUTBOUND_URL=http://localhost:3000/send-image")

    # Check 5: Baileys server running
    print("\n[5/6] Checking Baileys server...")
    try:
        r = requests.get("http://localhost:3000", timeout=2)
        print(f"      Server responded: {r.status_code}")
        print("      [OK] PASS: Baileys server running")

        # Try send-image endpoint
        print("\n      Testing /send-image endpoint...")
        try:
            r2 = requests.post(
                "http://localhost:3000/send-image",
                json={"test": True},
                timeout=2
            )
            if r2.status_code in [200, 400]:  # 400 is OK (missing fields)
                print(f"      [OK] PASS: /send-image endpoint exists ({r2.status_code})")
            else:
                print(f"      [WARN]  /send-image returned {r2.status_code}")

        except requests.exceptions.ConnectionError:
            issues.append("/send-image endpoint not found")
            print("      [ERROR] ISSUE: /send-image endpoint not found (404)")
            print("      FIX: Add endpoint to Baileys server")
            print("           See: FIX_IMAGES_NOT_SHOWING.md")

    except requests.exceptions.ConnectionError:
        issues.append("Baileys server not running")
        print("      [ERROR] ISSUE: Cannot connect to Baileys server")
        print("      FIX: Start Baileys server:")
        print("           cd baileys")
        print("           npm start")
    except Exception as e:
        issues.append(f"Baileys check error: {e}")
        print(f"      [ERROR] ERROR: {e}")

    # Check 6: Sample query
    print("\n[6/6] Testing complete lookup flow...")
    try:
        # Simulate what happens when user sends P0420
        code_result = client.table("obd_codes").select("code, system").eq("code", "P0420").execute()

        if code_result.data:
            system = code_result.data[0]['system']
            print(f"      1. Code P0420 → system '{system}'")

            # Try fuzzy match (case-insensitive)
            diagram_result = client.table("system_diagrams").select("system, image_url").ilike("system", system).execute()

            if diagram_result.data:
                diagram_system = diagram_result.data[0]['system']
                diagram_url = diagram_result.data[0]['image_url']
                print(f"      2. Found diagram: '{diagram_system}'")
                print(f"      3. Image URL: {diagram_url[:60]}...")
                print("      [OK] PASS: Complete flow working")
            else:
                print(f"      2. [ERROR] No diagram found for '{system}'")
                issues.append("Complete flow broken: no diagram match")
        else:
            print("      [ERROR] P0420 not found")
            issues.append("Complete flow broken: code not in database")

    except Exception as e:
        issues.append(f"Flow test error: {e}")
        print(f"      [ERROR] ERROR: {e}")

    # Summary
    print("\n" + "=" * 70)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 70)

    if not issues:
        print("\n[OK] ALL CHECKS PASSED!")
        print("\nIf images still not showing:")
        print("  1. Check backend logs when sending P0420")
        print("  2. Look for 'system_diagram_sent' log entry")
        print("  3. Check WhatsApp for image before text response")
    else:
        print(f"\n[ERROR] FOUND {len(issues)} ISSUE(S):\n")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")

        print("\n[INFO] NEXT STEPS:")
        print("  1. Read: FIX_IMAGES_NOT_SHOWING.md")
        print("  2. Fix issues listed above")
        print("  3. Re-run this script to verify")

    print("\n" + "=" * 70)

    return 0 if not issues else 1


if __name__ == "__main__":
    sys.exit(main())
