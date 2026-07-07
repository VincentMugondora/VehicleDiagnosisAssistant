#!/usr/bin/env python3
import os
from pathlib import Path
from supabase import create_client

env_file = Path(".env")
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key] = value

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_KEY")
client = create_client(url, key)

# Simplified top codes only
data = {
    "P0171": {
        "symptoms": ["Check engine light on", "Rough idle or engine misfiring", "Loss of power", "Hard starting"],
        "steps": ["Inspect vacuum hoses for leaks", "Clean MAF sensor", "Check fuel pressure", "Test oxygen sensors"],
        "parts": ["MAF Sensor", "Oxygen Sensor", "Vacuum Hoses", "Fuel Filter"],
        "related": ["P0174", "P0170", "P0172"]
    },
    "P0100": {
        "symptoms": ["Check engine light on", "Engine running rough", "Hard starting", "Stalling"],
        "steps": ["Inspect MAF wiring", "Check air filter", "Clean MAF sensor", "Test sensor voltage"],
        "parts": ["MAF Sensor", "Air Filter", "Wiring Harness"],
        "related": ["P0101", "P0102", "P0103"]
    },
    "P0300": {
        "symptoms": ["Check engine light flashing", "Rough idle", "Poor acceleration", "Hard starting"],
        "steps": ["Check spark plugs", "Inspect ignition coils", "Look for vacuum leaks", "Test fuel pressure"],
        "parts": ["Spark Plugs", "Ignition Coils", "Spark Plug Wires", "Fuel Injectors"],
        "related": ["P0301", "P0302", "P0171"]
    },
    "P0420": {
        "symptoms": ["Check engine light on", "Failed emissions test", "Rotten egg smell", "Reduced power"],
        "steps": ["Repair other codes first", "Check for exhaust leaks", "Test oxygen sensors", "Monitor sensor voltages"],
        "parts": ["Catalytic Converter", "Upstream O2 Sensor", "Downstream O2 Sensor"],
        "related": ["P0430", "P0421", "P0171"]
    },
    "P0442": {
        "symptoms": ["Check engine light on", "Gasoline smell", "Loose gas cap message", "Fueling difficulty"],
        "steps": ["Check gas cap clicks 3 times", "Inspect cap seal", "Check filler neck", "Inspect EVAP hoses"],
        "parts": ["Gas Cap", "EVAP Vent Valve", "EVAP Purge Valve", "EVAP Hoses"],
        "related": ["P0455", "P0456", "P0446"]
    }
}

def ins(code, d):
    print(f"[*] {code}...")
    try:
        s = [{"code_id": code, "symptom": x} for x in d["symptoms"]]
        client.table("common_symptoms").insert(s).execute()
        print(f"  OK {len(s)} symptoms")
    except Exception as e:
        print(f"  FAIL symptoms: {e}")
    
    try:
        st = [{"code_id": code, "step_number": i+1, "instruction": x} for i, x in enumerate(d["steps"])]
        client.table("repair_steps").insert(st).execute()
        print(f"  OK {len(st)} steps")
    except Exception as e:
        print(f"  FAIL steps: {e}")
    
    try:
        p = [{"code_id": code, "part_name": x, "part_number": None} for x in d["parts"]]
        client.table("parts").insert(p).execute()
        print(f"  OK {len(p)} parts")
    except Exception as e:
        print(f"  FAIL parts: {e}")
    
    try:
        r = [{"code_id": code, "related_code": x} for x in d["related"]]
        client.table("related_codes").insert(r).execute()
        print(f"  OK {len(r)} related")
    except Exception as e:
        print(f"  FAIL related: {e}")

print("DTC Population (Top 5 Codes)")
print("=" * 40)
for code, info in data.items():
    ins(code, info)
print("
Done!")
