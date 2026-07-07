"""
Complete Database Population Script
Populates ALL tables with initial data:
1. OBD Codes (obd_codes)
2. System Diagrams (system_diagrams)
3. DTC Details (vehicle_fitment, repair_steps, parts, symptoms, related_codes)

Usage:
    python scripts/populate_all_tables.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.client import get_supabase_client
from app.core.config import settings

# Import existing OBD codes
try:
    from scripts.comprehensive_obd_codes import ALL_CODES
    print(f"✅ Loaded {len(ALL_CODES)} codes from local dataset")
except ImportError:
    print("⚠️  Could not import comprehensive_obd_codes.py")
    ALL_CODES = {}


# ============================================================================
# SYSTEM DIAGRAMS DATA
# Free/public domain images from Wikimedia Commons
# ============================================================================

SYSTEM_DIAGRAMS = [
    {
        "system": "catalytic converter",
        "image_url": (
            "https://upload.wikimedia.org/wikipedia/commons/thumb/"
            "f/f5/Catalytic_converter_cut_open.jpg/"
            "800px-Catalytic_converter_cut_open.jpg"
        ),
        "source": "Wikimedia Commons",
        "license": "CC BY-SA 3.0",
        "caption": "Catalytic converter internal structure",
        "attribution_text": "Image: Wikimedia Commons, CC BY-SA 3.0"
    },
    {
        "system": "oxygen sensor",
        "image_url": (
            "https://upload.wikimedia.org/wikipedia/commons/thumb/"
            "2/2b/Lambda_sonde.jpg/800px-Lambda_sonde.jpg"
        ),
        "source": "Wikimedia Commons",
        "license": "CC BY-SA 3.0",
        "caption": "Oxygen (O2) sensor",
        "attribution_text": "Image: Wikimedia Commons, CC BY-SA 3.0"
    },
    {
        "system": "mass air flow sensor",
        "image_url": (
            "https://upload.wikimedia.org/wikipedia/commons/thumb/"
            "e/e0/MAF_sensor.jpg/800px-MAF_sensor.jpg"
        ),
        "source": "Wikimedia Commons",
        "license": "Public Domain",
        "caption": "Mass Air Flow (MAF) sensor",
        "attribution_text": None
    },
    {
        "system": "throttle body",
        "image_url": (
            "https://upload.wikimedia.org/wikipedia/commons/thumb/"
            "3/3e/Throttle_body.jpg/800px-Throttle_body.jpg"
        ),
        "source": "Wikimedia Commons",
        "license": "CC BY-SA 3.0",
        "caption": "Electronic throttle body",
        "attribution_text": "Image: Wikimedia Commons, CC BY-SA 3.0"
    },
    {
        "system": "evap system",
        "image_url": (
            "https://upload.wikimedia.org/wikipedia/commons/thumb/"
            "1/1f/Evap_canister.jpg/800px-Evap_canister.jpg"
        ),
        "source": "Wikimedia Commons",
        "license": "Public Domain",
        "caption": "EVAP charcoal canister",
        "attribution_text": None
    },
    {
        "system": "fuel injector",
        "image_url": (
            "https://upload.wikimedia.org/wikipedia/commons/thumb/"
            "c/c5/Fuel_injector.jpg/800px-Fuel_injector.jpg"
        ),
        "source": "Wikimedia Commons",
        "license": "CC BY-SA 3.0",
        "caption": "Fuel injector assembly",
        "attribution_text": "Image: Wikimedia Commons, CC BY-SA 3.0"
    },
    {
        "system": "egr valve",
        "image_url": (
            "https://upload.wikimedia.org/wikipedia/commons/thumb/"
            "7/70/EGR_valve.jpg/800px-EGR_valve.jpg"
        ),
        "source": "Wikimedia Commons",
        "license": "Public Domain",
        "caption": "Exhaust Gas Recirculation (EGR) valve",
        "attribution_text": None
    },
    {
        "system": "ignition coil",
        "image_url": (
            "https://upload.wikimedia.org/wikipedia/commons/thumb/"
            "9/9a/Ignition_coil.jpg/800px-Ignition_coil.jpg"
        ),
        "source": "Wikimedia Commons",
        "license": "CC BY-SA 3.0",
        "caption": "Ignition coil pack",
        "attribution_text": "Image: Wikimedia Commons, CC BY-SA 3.0"
    },
    {
        "system": "camshaft position sensor",
        "image_url": (
            "https://upload.wikimedia.org/wikipedia/commons/thumb/"
            "b/b1/Camshaft_sensor.jpg/800px-Camshaft_sensor.jpg"
        ),
        "source": "Wikimedia Commons",
        "license": "Public Domain",
        "caption": "Camshaft position sensor",
        "attribution_text": None
    },
    {
        "system": "crankshaft position sensor",
        "image_url": (
            "https://upload.wikimedia.org/wikipedia/commons/thumb/"
            "4/4c/Crankshaft_sensor.jpg/800px-Crankshaft_sensor.jpg"
        ),
        "source": "Wikimedia Commons",
        "license": "CC BY-SA 3.0",
        "caption": "Crankshaft position sensor",
        "attribution_text": "Image: Wikimedia Commons, CC BY-SA 3.0"
    }
]


# ============================================================================
# DTC DETAIL DATA (Sample for top 20 most common codes)
# ============================================================================

# Vehicle fitment for common codes
VEHICLE_FITMENT_DATA = {
    "P0420": [
        {
            "make": "Toyota", "model": "Camry",
            "year_start": 2007, "year_end": 2020, "engine": "2.5L"
        },
        {
            "make": "Honda", "model": "Civic",
            "year_start": 2006, "year_end": 2020, "engine": "1.8L"
        },
        {
            "make": "Ford", "model": "F-150",
            "year_start": 2009, "year_end": 2020, "engine": "5.0L V8"
        },
        {
            "make": "Chevrolet", "model": "Silverado",
            "year_start": 2007, "year_end": 2020, "engine": "5.3L V8"
        },
    ],
    "P0300": [
        {
            "make": "Toyota", "model": "Corolla",
            "year_start": 2005, "year_end": 2020, "engine": "1.8L"
        },
        {
            "make": "Honda", "model": "Accord",
            "year_start": 2008, "year_end": 2020, "engine": "2.4L"
        },
        {
            "make": "Ford", "model": "Focus",
            "year_start": 2012, "year_end": 2018, "engine": "2.0L"
        },
    ],
    "P0171": [
        {
            "make": "Toyota", "model": "Camry",
            "year_start": 2007, "year_end": 2020, "engine": "2.5L"
        },
        {
            "make": "Honda", "model": "CR-V",
            "year_start": 2007, "year_end": 2020, "engine": "2.4L"
        },
        {
            "make": "Ford", "model": "Explorer",
            "year_start": 2011, "year_end": 2019, "engine": "3.5L V6"
        },
    ],
    "P0128": [
        {
            "make": "Toyota", "model": "Prius",
            "year_start": 2010, "year_end": 2020, "engine": "1.8L Hybrid"
        },
        {
            "make": "Honda", "model": "Civic",
            "year_start": 2006, "year_end": 2015, "engine": "1.8L"
        },
    ],
}

# Repair steps for common codes
REPAIR_STEPS_DATA = {
    "P0420": [
        {
            "step_number": 1,
            "instruction": (
                "Scan for additional codes that may indicate root cause "
                "(O2 sensor codes)"
            )
        },
        {
            "step_number": 2,
            "instruction": (
                "Check exhaust system for leaks before and after "
                "catalytic converter"
            )
        },
        {
            "step_number": 3,
            "instruction": (
                "Inspect oxygen sensors (upstream and downstream) "
                "for damage or contamination"
            )
        },
        {
            "step_number": 4,
            "instruction": (
                "Test catalytic converter efficiency using scan tool live data"
            )
        },
        {
            "step_number": 5,
            "instruction": (
                "If converter is failed, replace catalytic converter "
                "and both O2 sensors"
            )
        },
        {
            "step_number": 6,
            "instruction": "Clear codes and complete drive cycle to verify repair"
        },
    ],
    "P0300": [
        {
            "step_number": 1,
            "instruction": (
                "Scan for cylinder-specific misfire codes (P0301-P0308)"
            )
        },
        {
            "step_number": 2,
            "instruction": (
                "Inspect spark plugs for wear, fouling, or incorrect gap"
            )
        },
        {
            "step_number": 3,
            "instruction": "Check ignition coils and spark plug wires for damage"
        },
        {
            "step_number": 4,
            "instruction": "Test fuel pressure and fuel injector operation"
        },
        {
            "step_number": 5,
            "instruction": "Check for vacuum leaks in intake manifold"
        },
        {
            "step_number": 6,
            "instruction": (
                "Inspect compression on all cylinders "
                "if above steps don't resolve"
            )
        },
    ],
    "P0171": [
        {
            "step_number": 1,
            "instruction": (
                "Inspect air intake system for leaks or loose connections"
            )
        },
        {
            "step_number": 2,
            "instruction": "Check MAF sensor for contamination, clean if necessary"
        },
        {
            "step_number": 3,
            "instruction": "Inspect vacuum hoses for cracks or disconnection"
        },
        {
            "step_number": 4,
            "instruction": (
                "Test fuel pressure - low pressure causes lean condition"
            )
        },
        {
            "step_number": 5,
            "instruction": "Check PCV valve operation"
        },
        {
            "step_number": 6,
            "instruction": "Inspect exhaust system for leaks before O2 sensor"
        },
    ],
}

# Parts for common codes
PARTS_DATA = {
    "P0420": [
        {"part_name": "Catalytic Converter", "part_number": None},
        {"part_name": "Upstream Oxygen Sensor (Bank 1 Sensor 1)", "part_number": None},
        {"part_name": "Downstream Oxygen Sensor (Bank 1 Sensor 2)", "part_number": None},
        {"part_name": "Exhaust Gaskets", "part_number": None},
    ],
    "P0300": [
        {"part_name": "Spark Plugs (set of 4-8)", "part_number": None},
        {"part_name": "Ignition Coils", "part_number": None},
        {"part_name": "Spark Plug Wires (if applicable)", "part_number": None},
        {"part_name": "Fuel Filter", "part_number": None},
    ],
    "P0171": [
        {"part_name": "MAF Sensor", "part_number": None},
        {"part_name": "Vacuum Hoses", "part_number": None},
        {"part_name": "Fuel Filter", "part_number": None},
        {"part_name": "Fuel Pump", "part_number": None},
        {"part_name": "Intake Manifold Gasket", "part_number": None},
    ],
}

# Common symptoms
SYMPTOMS_DATA = {
    "P0420": [
        "Check Engine Light on",
        "Reduced fuel economy",
        "Sulfur/rotten egg smell from exhaust",
        "Failed emissions test",
    ],
    "P0300": [
        "Check Engine Light flashing",
        "Engine rough idle",
        "Loss of power",
        "Engine hesitation or stumbling",
        "Poor fuel economy",
    ],
    "P0171": [
        "Check Engine Light on",
        "Rough idle",
        "Engine hesitation on acceleration",
        "Hard starting",
        "Lean exhaust smell",
    ],
    "P0128": [
        "Check Engine Light on",
        "Engine takes long to reach operating temperature",
        "Poor heater performance",
        "Reduced fuel economy in cold weather",
    ],
}

# Related codes
RELATED_CODES_DATA = {
    "P0420": ["P0430", "P0137", "P0138", "P0141"],
    "P0300": ["P0301", "P0302", "P0303", "P0304", "P0305", "P0306", "P0307", "P0308"],
    "P0171": ["P0174", "P0101", "P0106", "P0172"],
    "P0128": ["P0125", "P0126"],
}


# ============================================================================
# POPULATION FUNCTIONS
# ============================================================================

def populate_obd_codes(client):
    """Populate obd_codes table"""
    print("\n" + "=" * 60)
    print("📦 Populating obd_codes table")
    print("=" * 60)

    records = []
    for code, data in ALL_CODES.items():
        records.append({
            "code": code.upper(),
            "description": data.get("description", ""),
            "symptoms": data.get("symptoms", ""),
            "common_causes": data.get("common_causes", ""),
            "generic_fixes": data.get("generic_fixes", ""),
            "system": data.get("system", "Powertrain"),
            "severity": data.get("severity", "Medium"),
        })

    # Import in batches
    batch_size = 100
    imported = 0

    for i in range(0, len(records), batch_size):
        batch = records[i:i+batch_size]
        try:
            client.table("obd_codes").upsert(
                batch, on_conflict="code"
            ).execute()
            imported += len(batch)
            batch_num = i // batch_size + 1
            print(f"✅ Batch {batch_num}: {len(batch)} codes (Total: {imported})")
        except Exception as e:  # pylint: disable=broad-exception-caught
            batch_num = i // batch_size + 1
            print(f"❌ Batch {batch_num} failed: {e}")

    print(f"\n✅ Imported {imported} OBD codes")
    return imported


def populate_system_diagrams(client):
    """Populate system_diagrams table"""
    print("\n" + "=" * 60)
    print("🖼️  Populating system_diagrams table")
    print("=" * 60)

    try:
        client.table("system_diagrams").upsert(
            SYSTEM_DIAGRAMS,
            on_conflict="system"
        ).execute()
        print(f"✅ Imported {len(SYSTEM_DIAGRAMS)} system diagrams")
        return len(SYSTEM_DIAGRAMS)
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"❌ Failed to import system diagrams: {e}")
        return 0


def populate_vehicle_fitment(client):
    """Populate code_vehicle_fitment table"""
    print("\n" + "=" * 60)
    print("🚗 Populating code_vehicle_fitment table")
    print("=" * 60)

    records = []
    for code, vehicles in VEHICLE_FITMENT_DATA.items():
        for vehicle in vehicles:
            records.append({
                "code_id": code,
                **vehicle
            })

    try:
        # Delete existing for these codes first to avoid duplicates
        for code in VEHICLE_FITMENT_DATA:
            client.table("code_vehicle_fitment").delete().eq(
                "code_id", code
            ).execute()

        # Insert new data
        client.table("code_vehicle_fitment").insert(records).execute()
        print(f"✅ Imported {len(records)} vehicle fitment records")
        return len(records)
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"❌ Failed to import vehicle fitment: {e}")
        return 0


def populate_repair_steps(client):
    """Populate repair_steps table"""
    print("\n" + "=" * 60)
    print("🔧 Populating repair_steps table")
    print("=" * 60)

    records = []
    for code, steps in REPAIR_STEPS_DATA.items():
        for step in steps:
            records.append({
                "code_id": code,
                **step
            })

    try:
        # Delete existing for these codes
        for code in REPAIR_STEPS_DATA:
            client.table("repair_steps").delete().eq("code_id", code).execute()

        client.table("repair_steps").insert(records).execute()
        print(f"✅ Imported {len(records)} repair steps")
        return len(records)
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"❌ Failed to import repair steps: {e}")
        return 0


def populate_parts(client):
    """Populate parts table"""
    print("\n" + "=" * 60)
    print("🔩 Populating parts table")
    print("=" * 60)

    records = []
    for code, parts in PARTS_DATA.items():
        for part in parts:
            records.append({
                "code_id": code,
                **part
            })

    try:
        # Delete existing for these codes
        for code in PARTS_DATA:
            client.table("parts").delete().eq("code_id", code).execute()

        client.table("parts").insert(records).execute()
        print(f"✅ Imported {len(records)} parts")
        return len(records)
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"❌ Failed to import parts: {e}")
        return 0


def populate_symptoms(client):
    """Populate common_symptoms table"""
    print("\n" + "=" * 60)
    print("📋 Populating common_symptoms table")
    print("=" * 60)

    records = []
    for code, symptoms in SYMPTOMS_DATA.items():
        for symptom in symptoms:
            records.append({
                "code_id": code,
                "symptom": symptom
            })

    try:
        # Delete existing for these codes
        for code in SYMPTOMS_DATA:
            client.table("common_symptoms").delete().eq("code_id", code).execute()

        client.table("common_symptoms").insert(records).execute()
        print(f"✅ Imported {len(records)} symptoms")
        return len(records)
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"❌ Failed to import symptoms: {e}")
        return 0


def populate_related_codes(client):
    """Populate related_codes table"""
    print("\n" + "=" * 60)
    print("🔗 Populating related_codes table")
    print("=" * 60)

    records = []
    for code, related in RELATED_CODES_DATA.items():
        for related_code in related:
            records.append({
                "code_id": code,
                "related_code": related_code
            })

    try:
        # Delete existing for these codes
        for code in RELATED_CODES_DATA:
            client.table("related_codes").delete().eq("code_id", code).execute()

        client.table("related_codes").insert(records).execute()
        print(f"✅ Imported {len(records)} related code relationships")
        return len(records)
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"❌ Failed to import related codes: {e}")
        return 0


def main():
    """Main population script"""
    print("=" * 60)
    print("🚀 Complete Database Population Script")
    print("=" * 60)
    print()

    # Connect to Supabase
    print("🔌 Connecting to Supabase...")
    try:
        client = get_supabase_client()
        client.table("obd_codes").select("code").limit(1).execute()
        print(f"✅ Connected: {settings.supabase_url}")
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"❌ Connection failed: {e}")
        return 1

    # Track totals
    totals = {}

    # Populate all tables
    totals['obd_codes'] = populate_obd_codes(client)
    totals['system_diagrams'] = populate_system_diagrams(client)
    totals['vehicle_fitment'] = populate_vehicle_fitment(client)
    totals['repair_steps'] = populate_repair_steps(client)
    totals['parts'] = populate_parts(client)
    totals['symptoms'] = populate_symptoms(client)
    totals['related_codes'] = populate_related_codes(client)

    # Summary
    print("\n" + "=" * 60)
    print("📊 POPULATION SUMMARY")
    print("=" * 60)
    for table, count in totals.items():
        print(f"  {table:20s}: {count:6d} records")
    print("=" * 60)
    print()
    print("✅ Database population complete!")
    print()
    print("Next steps:")
    print("  1. Test OBD code lookup: P0420, P0300, P0171")
    print("  2. Verify system diagrams are accessible")
    print("  3. Query DTC details for populated codes")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
