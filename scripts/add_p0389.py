"""
Add P0389 (Crankshaft Position Sensor B Circuit Intermittent) to database
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.client import get_supabase_client

client = get_supabase_client()

print("Adding P0389 to database...")

# Full details for P0389
code_data = {
    "code": "P0389",
    "description": "Crankshaft Position Sensor B Circuit Intermittent",
    "symptoms": "Engine may stall, hesitate, or have difficulty starting. Check Engine Light on. Rough idle. Loss of power.",
    "common_causes": "Faulty crankshaft position sensor, damaged wiring or connectors, sensor mounting issues, reluctor wheel damage, ECM malfunction",
    "generic_fixes": "Inspect wiring and connectors for damage. Check sensor air gap. Test sensor resistance. Replace crankshaft position sensor if faulty. Clear codes and test drive.",
    "system": "crankshaft position sensor",  # Links to diagram
    "severity": "High"
}

try:
    # Upsert (insert or update)
    result = client.table("obd_codes").upsert(code_data, on_conflict="code").execute()

    if result.data:
        print("[OK] P0389 added successfully!")
        print(f"    System: {code_data['system']}")
        print(f"    Severity: {code_data['severity']}")
        print(f"    Description: {code_data['description']}")

        # Check if diagram exists
        diagram = client.table("system_diagrams").select("system").eq("system", "crankshaft position sensor").execute()

        if diagram.data:
            print("\n[OK] Diagram exists for 'crankshaft position sensor'")
            print("    Image will be sent with this code!")
        else:
            print("\n[WARN] No diagram for 'crankshaft position sensor'")
            print("       Run: python scripts/populate_all_tables.py")
    else:
        print("[ERROR] Failed to add P0389")

except Exception as e:
    print(f"[ERROR] {e}")

print("\nTest now: Send 'P0389' via WhatsApp")
print("Expected: Crankshaft position sensor image + detailed diagnosis")
