"""
Enhanced Schema Population Script
Populates the new V2 schema tables with sample data

Usage:
    python scripts/populate_enhanced_schema.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.client import get_supabase_client

# ============================================================================
# SAMPLE DATA FOR NEW TABLES
# ============================================================================

# Vehicles (normalized)
VEHICLES_DATA = [
    {
        "make": "Toyota",
        "model": "Camry",
        "year_from": 2007,
        "year_to": 2011,
        "engine": "2.5L I4",
        "fuel_type": "Gasoline",
        "transmission": "Automatic",
        "drive_type": "FWD",
        "market": "US"
    },
    {
        "make": "Toyota",
        "model": "Camry",
        "year_from": 2012,
        "year_to": 2017,
        "engine": "2.5L I4",
        "fuel_type": "Gasoline",
        "transmission": "Automatic",
        "drive_type": "FWD",
        "market": "US"
    },
    {
        "make": "Honda",
        "model": "Civic",
        "year_from": 2006,
        "year_to": 2011,
        "engine": "1.8L I4",
        "fuel_type": "Gasoline",
        "transmission": "Automatic",
        "drive_type": "FWD",
        "market": "US"
    },
    {
        "make": "Ford",
        "model": "F-150",
        "year_from": 2011,
        "year_to": 2014,
        "engine": "5.0L V8",
        "fuel_type": "Gasoline",
        "transmission": "Automatic",
        "drive_type": "RWD",
        "market": "US"
    },
]

# Possible causes (ranked by probability)
POSSIBLE_CAUSES_DATA = {
    "P0420": [
        {"cause": "Failed catalytic converter", "probability": 85, "difficulty": "Hard", "check_first": False},
        {"cause": "Faulty downstream O2 sensor", "probability": 75, "difficulty": "Easy", "check_first": True},
        {"cause": "Exhaust leak near sensors", "probability": 60, "difficulty": "Medium", "check_first": True},
        {"cause": "Contaminated O2 sensors from coolant/oil", "probability": 40, "difficulty": "Medium", "check_first": False},
        {"cause": "Faulty upstream O2 sensor", "probability": 30, "difficulty": "Easy", "check_first": False},
    ],
    "P0300": [
        {"cause": "Worn spark plugs", "probability": 90, "difficulty": "Easy", "check_first": True},
        {"cause": "Faulty ignition coils", "probability": 80, "difficulty": "Medium", "check_first": True},
        {"cause": "Vacuum leaks", "probability": 60, "difficulty": "Medium", "check_first": False},
        {"cause": "Low fuel pressure", "probability": 50, "difficulty": "Medium", "check_first": False},
        {"cause": "Clogged fuel injectors", "probability": 45, "difficulty": "Medium", "check_first": False},
        {"cause": "Low engine compression", "probability": 30, "difficulty": "Hard", "check_first": False},
    ],
    "P0171": [
        {"cause": "Vacuum leak (intake manifold, hoses)", "probability": 80, "difficulty": "Medium", "check_first": True},
        {"cause": "Dirty/faulty MAF sensor", "probability": 75, "difficulty": "Easy", "check_first": True},
        {"cause": "Weak fuel pump", "probability": 60, "difficulty": "Medium", "check_first": False},
        {"cause": "Clogged fuel filter", "probability": 50, "difficulty": "Easy", "check_first": False},
        {"cause": "Exhaust leak before O2 sensor", "probability": 40, "difficulty": "Medium", "check_first": False},
    ],
}

# Diagnostic tests
DIAGNOSTIC_TESTS_DATA = {
    "P0420": [
        {
            "test_name": "Visual Inspection of Exhaust System",
            "test_type": "Visual",
            "tools_required": "Flashlight, inspection mirror",
            "procedure": "Inspect exhaust system from manifold to tailpipe. Look for rust holes, damaged flex pipes, loose clamps. Pay special attention to areas before and after catalytic converter.",
            "expected_result": "No visible holes, cracks, or loose connections",
            "estimated_minutes": 10,
            "difficulty": "Easy",
            "order_number": 1
        },
        {
            "test_name": "O2 Sensor Voltage Test",
            "test_type": "Electrical",
            "tools_required": "Scan tool with live data",
            "procedure": "Monitor upstream and downstream O2 sensor voltages with engine at operating temperature. Upstream should fluctuate 0.1-0.9V, downstream should be stable around 0.45V.",
            "expected_result": "Upstream: fluctuating, Downstream: stable",
            "estimated_minutes": 15,
            "difficulty": "Medium",
            "order_number": 2
        },
        {
            "test_name": "Catalytic Converter Efficiency Test",
            "test_type": "Electrical",
            "tools_required": "Scan tool with graphing capability",
            "procedure": "Graph both O2 sensors simultaneously. Healthy converter shows downstream readings much less reactive than upstream. Failed converter shows both sensors mirroring each other.",
            "expected_result": "Downstream voltage should be flat, not following upstream",
            "estimated_minutes": 20,
            "difficulty": "Medium",
            "order_number": 3
        },
    ],
    "P0300": [
        {
            "test_name": "Spark Plug Inspection",
            "test_type": "Visual",
            "tools_required": "Spark plug socket, gap tool",
            "procedure": "Remove all spark plugs. Check gap, electrode wear, carbon buildup, oil fouling. Compare plugs from different cylinders.",
            "expected_result": "Correct gap (typically 0.028-0.060\"), minimal wear, no fouling",
            "estimated_minutes": 30,
            "difficulty": "Medium",
            "order_number": 1
        },
        {
            "test_name": "Ignition Coil Test",
            "test_type": "Electrical",
            "tools_required": "Multimeter, scan tool",
            "procedure": "Measure coil primary and secondary resistance. Typical primary: 0.4-2 ohms, secondary: 6,000-30,000 ohms. Check for spark using spark tester.",
            "expected_result": "Resistance within spec, strong blue spark",
            "estimated_minutes": 20,
            "difficulty": "Medium",
            "order_number": 2
        },
    ],
}

# Repair tips
REPAIR_TIPS_DATA = {
    "P0420": [
        {
            "tip": "Always replace both upstream and downstream O2 sensors when replacing catalytic converter. Old sensors can contaminate new converter.",
            "tip_type": "Best Practice",
            "importance": "Critical"
        },
        {
            "tip": "Never spray water on hot catalytic converter - it can crack the ceramic substrate.",
            "tip_type": "Safety",
            "importance": "Critical"
        },
        {
            "tip": "Use anti-seize on O2 sensor threads, but keep it away from sensor tip.",
            "tip_type": "Best Practice",
            "importance": "Important"
        },
        {
            "tip": "Check for exhaust leaks BEFORE replacing expensive catalytic converter.",
            "tip_type": "Cost Saving",
            "importance": "Critical"
        },
    ],
    "P0300": [
        {
            "tip": "Replace all spark plugs at once, even if only one cylinder is misfiring. Prevents repeat repairs.",
            "tip_type": "Best Practice",
            "importance": "Important"
        },
        {
            "tip": "When swapping ignition coils between cylinders, clear codes first, then see if misfire follows the coil to confirm diagnosis.",
            "tip_type": "Best Practice",
            "importance": "Important"
        },
        {
            "tip": "Use dielectric grease on coil boots to prevent moisture and improve connection.",
            "tip_type": "Best Practice",
            "importance": "Nice-to-Know"
        },
    ],
    "P0171": [
        {
            "tip": "Spray brake cleaner around intake manifold while engine idles. RPM increase indicates vacuum leak location.",
            "tip_type": "Best Practice",
            "importance": "Important"
        },
        {
            "tip": "Clean MAF sensor with MAF-specific cleaner only. Do NOT use carb cleaner or touch sensor element.",
            "tip_type": "Common Mistake",
            "importance": "Critical"
        },
    ],
}

# Maintenance recommendations
MAINTENANCE_RECOMMENDATIONS_DATA = {
    "P0420": [
        {
            "recommendation": "Replace O2 sensors every 100,000 km to maintain catalytic converter efficiency",
            "interval_km": 100000,
            "interval_months": None
        },
        {
            "recommendation": "Use top-tier gasoline to reduce carbon buildup on sensors and converter",
            "interval_km": None,
            "interval_months": None
        },
    ],
    "P0300": [
        {
            "recommendation": "Replace spark plugs according to manufacturer specification (typically 60,000-100,000 km)",
            "interval_km": 80000,
            "interval_months": None
        },
        {
            "recommendation": "Inspect ignition coils during tune-up, replace if cracks visible",
            "interval_km": 80000,
            "interval_months": None
        },
    ],
    "P0171": [
        {
            "recommendation": "Clean or replace air filter every 20,000-40,000 km",
            "interval_km": 30000,
            "interval_months": None
        },
        {
            "recommendation": "Clean MAF sensor every 50,000 km or when symptoms appear",
            "interval_km": 50000,
            "interval_months": None
        },
    ],
}

# Images (sample with placeholder URLs)
IMAGES_DATA = {
    "P0420": [
        {
            "image_url": "https://example.com/catalytic-converter-diagram.jpg",
            "thumbnail_url": "https://example.com/catalytic-converter-diagram-thumb.jpg",
            "caption": "Catalytic converter location and O2 sensor positions",
            "image_type": "diagram",
            "source": "Technical Manual",
            "license": "Fair Use",
            "alt_text": "Diagram showing catalytic converter between exhaust manifold and muffler with upstream and downstream O2 sensors"
        },
        {
            "image_url": "https://example.com/o2-sensor-location.jpg",
            "caption": "O2 sensor location on exhaust pipe",
            "image_type": "location",
            "source": "Service Manual",
            "license": "Fair Use",
            "alt_text": "Photo showing O2 sensor threaded into exhaust pipe"
        },
    ],
    "P0300": [
        {
            "image_url": "https://example.com/spark-plug-removal.jpg",
            "caption": "Spark plug removal procedure",
            "image_type": "repair",
            "source": "Repair Guide",
            "license": "Fair Use",
            "alt_text": "Photo showing spark plug being removed with socket wrench"
        },
    ],
}


# ============================================================================
# POPULATION FUNCTIONS
# ============================================================================

def populate_vehicles(client):
    """Populate vehicles table"""
    print("\n" + "=" * 60)
    print("🚗 Populating vehicles table")
    print("=" * 60)

    try:
        client.table("vehicles").upsert(
            VEHICLES_DATA,
            on_conflict="make,model,year_from,year_to,engine"
        ).execute()
        print(f"✅ Imported {len(VEHICLES_DATA)} vehicles")
        return len(VEHICLES_DATA)
    except Exception as e:
        print(f"❌ Failed: {e}")
        return 0


def populate_possible_causes(client):
    """Populate possible_causes table"""
    print("\n" + "=" * 60)
    print("🔍 Populating possible_causes table")
    print("=" * 60)

    records = []
    for code, causes in POSSIBLE_CAUSES_DATA.items():
        for cause_data in causes:
            records.append({
                "obd_code_id": code,
                **cause_data
            })

    try:
        # Delete existing for these codes
        for code in POSSIBLE_CAUSES_DATA.keys():
            client.table("possible_causes").delete().eq("obd_code_id", code).execute()

        client.table("possible_causes").insert(records).execute()
        print(f"✅ Imported {len(records)} possible causes")
        return len(records)
    except Exception as e:
        print(f"❌ Failed: {e}")
        return 0


def populate_diagnostic_tests(client):
    """Populate diagnostic_tests table"""
    print("\n" + "=" * 60)
    print("🧪 Populating diagnostic_tests table")
    print("=" * 60)

    records = []
    for code, tests in DIAGNOSTIC_TESTS_DATA.items():
        for test_data in tests:
            records.append({
                "obd_code_id": code,
                **test_data
            })

    try:
        for code in DIAGNOSTIC_TESTS_DATA.keys():
            client.table("diagnostic_tests").delete().eq("obd_code_id", code).execute()

        client.table("diagnostic_tests").insert(records).execute()
        print(f"✅ Imported {len(records)} diagnostic tests")
        return len(records)
    except Exception as e:
        print(f"❌ Failed: {e}")
        return 0


def populate_repair_tips(client):
    """Populate repair_tips table"""
    print("\n" + "=" * 60)
    print("💡 Populating repair_tips table")
    print("=" * 60)

    records = []
    for code, tips in REPAIR_TIPS_DATA.items():
        for tip_data in tips:
            records.append({
                "obd_code_id": code,
                **tip_data
            })

    try:
        for code in REPAIR_TIPS_DATA.keys():
            client.table("repair_tips").delete().eq("obd_code_id", code).execute()

        client.table("repair_tips").insert(records).execute()
        print(f"✅ Imported {len(records)} repair tips")
        return len(records)
    except Exception as e:
        print(f"❌ Failed: {e}")
        return 0


def populate_maintenance_recommendations(client):
    """Populate maintenance_recommendations table"""
    print("\n" + "=" * 60)
    print("🔧 Populating maintenance_recommendations table")
    print("=" * 60)

    records = []
    for code, recommendations in MAINTENANCE_RECOMMENDATIONS_DATA.items():
        for rec_data in recommendations:
            records.append({
                "obd_code_id": code,
                **rec_data
            })

    try:
        for code in MAINTENANCE_RECOMMENDATIONS_DATA.keys():
            client.table("maintenance_recommendations").delete().eq("obd_code_id", code).execute()

        client.table("maintenance_recommendations").insert(records).execute()
        print(f"✅ Imported {len(records)} maintenance recommendations")
        return len(records)
    except Exception as e:
        print(f"❌ Failed: {e}")
        return 0


def populate_images(client):
    """Populate images table"""
    print("\n" + "=" * 60)
    print("🖼️  Populating images table")
    print("=" * 60)

    records = []
    for code, images in IMAGES_DATA.items():
        for image_data in images:
            records.append({
                "obd_code_id": code,
                **image_data
            })

    try:
        for code in IMAGES_DATA.keys():
            client.table("images").delete().eq("obd_code_id", code).execute()

        client.table("images").insert(records).execute()
        print(f"✅ Imported {len(records)} images")
        return len(records)
    except Exception as e:
        print(f"❌ Failed: {e}")
        return 0


def main():
    """Main population script"""
    print("=" * 60)
    print("🚀 Enhanced Schema Population Script")
    print("=" * 60)

    # Connect
    print("\n🔌 Connecting to Supabase...")
    try:
        client = get_supabase_client()
        client.table("obd_codes").select("code").limit(1).execute()
        print("✅ Connected")
    except Exception as e:
        print(f"❌ Failed: {e}")
        return 1

    # Populate
    totals = {}
    totals['vehicles'] = populate_vehicles(client)
    totals['possible_causes'] = populate_possible_causes(client)
    totals['diagnostic_tests'] = populate_diagnostic_tests(client)
    totals['repair_tips'] = populate_repair_tips(client)
    totals['maintenance_recommendations'] = populate_maintenance_recommendations(client)
    totals['images'] = populate_images(client)

    # Summary
    print("\n" + "=" * 60)
    print("📊 POPULATION SUMMARY")
    print("=" * 60)
    for table, count in totals.items():
        print(f"  {table:35s}: {count:6d} records")
    print("=" * 60)
    print()
    print("✅ Enhanced schema population complete!")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
