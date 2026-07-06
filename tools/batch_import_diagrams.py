#!/usr/bin/env python3
"""
Batch import system diagrams from workflow search results.
"""
import sys
import json
from app.db.client import get_supabase_client
from app.repositories.system_diagram_repository import SystemDiagramRepository

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# System name mappings (search term -> canonical database name)
SYSTEM_NAME_MAP = {
    'oxygen sensor': 'oxygen sensor',
    'egr valve': 'egr valve',
    'evap system': 'evap system',
    'mass air flow sensor': 'mass air flow sensor',
    'throttle body': 'throttle body',
    'ignition coil': 'ignition coil',
    'spark plugs': 'spark plug',
    'fuel injector': 'fuel injector',
    'fuel pump': 'fuel pump',
    'map sensor': 'map sensor',
    'camshaft position sensor': 'camshaft position sensor',
    'crankshaft position sensor': 'crankshaft position sensor',
    'knock sensor': 'knock sensor',
    'coolant temperature sensor': 'coolant temperature sensor',
    'thermostat': 'thermostat',
    'pcv valve': 'pcv valve',
    'radiator': 'radiator',
    'timing belt': 'timing belt',
    'alternator': 'alternator',
    'battery': 'battery',
    'brake pads': 'brake pads',
    'wheel speed sensor': 'wheel speed sensor',
    'transmission': 'transmission',
    'air intake manifold': 'air intake manifold'
}

DIAGRAMS = [
    {
        'system': 'oxygen sensor',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/b/bd/ZirconiaSensor.svg',
        'source': 'Wikimedia Commons',
        'license': 'CC BY-SA 3.0',
        'caption': 'Zirconia oxygen sensor schematic showing functional components',
        'attribution': 'Zirconia Oxygen Sensor by Michael Handrich, via Wikimedia Commons (CC BY-SA 3.0)'
    },
    {
        'system': 'egr valve',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/d/d9/EGR_Cooler.JPG',
        'source': 'Wikimedia Commons',
        'license': 'CC BY-SA 3.0',
        'caption': 'Physical cutaway of EGR cooler showing internal cooling passages',
        'attribution': 'Image by Ton1-bot, licensed under CC BY-SA 3.0 via Wikimedia Commons'
    },
    {
        'system': 'evap system',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/9/98/Principe_de_fonctionnement_d%27un_canister_d%27automobile.png',
        'source': 'Wikimedia Commons',
        'license': 'CC BY-SA 4.0',
        'caption': 'EVAP system schematic showing canister and vapor flow path',
        'attribution': 'By Georges88, CC BY-SA 4.0, via Wikimedia Commons'
    },
    {
        'system': 'mass air flow sensor',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/d/df/Detail_Hei%C3%9Ffilm-Luftmassenmesser.jpg',
        'source': 'Wikimedia Commons',
        'license': 'CC BY 4.0',
        'caption': 'Close-up of hot-film mass air flow sensor internal construction',
        'attribution': 'Detail Heißfilm-Luftmassenmesser by FLOEP, licensed under CC BY 4.0, via Wikimedia Commons'
    },
    {
        'system': 'throttle body',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/3/3d/USPatent6646395.png',
        'source': 'Wikimedia Commons',
        'license': 'Public Domain',
        'caption': 'Cross-section of electronic throttle body from U.S. Patent 6,646,395',
        'attribution': 'Image from U.S. Patent 6,646,395, uploaded by Interiot to Wikimedia Commons. Public Domain.'
    },
    {
        'system': 'ignition coil',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/8/8f/Induction_coil_cutaway.jpg',
        'source': 'Wikimedia Commons',
        'license': 'Public Domain',
        'caption': 'Cutaway of induction coil showing internal windings and core',
        'attribution': 'Public domain image by Harry Winfield Secor from "Wireless Course in Twenty Lessons" (1920)'
    },
    {
        'system': 'spark plug',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/7/7c/Spark_Plug_%28PSF%29.png',
        'source': 'Wikimedia Commons',
        'license': 'Public Domain',
        'caption': 'Cutaway diagram of spark plug showing internal structure',
        'attribution': 'Image from Pearson Scott Foresman, donated to Wikimedia Foundation (Public Domain)'
    },
    {
        'system': 'fuel injector',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/8/8e/Fuelinjector.png',
        'source': 'Wikimedia Commons',
        'license': 'CC BY-SA 3.0',
        'caption': 'Fuel injector cross-section showing solenoid and spray tip',
        'attribution': 'Fuelinjector.png by WikipedianProlific, licensed under CC BY-SA 3.0'
    },
    {
        'system': 'fuel pump',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/c/cb/Automobile_Fuel_tank_cutaway.JPG',
        'source': 'Wikimedia Commons',
        'license': 'CC BY-SA 3.0',
        'caption': 'Cutaway of fuel tank showing submersible fuel pump location',
        'attribution': 'Image by Cschirp, licensed under CC BY-SA 3.0 via Wikimedia Commons'
    },
    {
        'system': 'map sensor',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/0/06/K-car_MAP_and_logic_module_location_%284217323585%29.jpg',
        'source': 'Wikimedia Commons',
        'license': 'CC BY 2.0',
        'caption': 'MAP sensor location diagram showing installation behind kick panel',
        'attribution': 'Photo by dave_7, licensed under CC BY 2.0, via Wikimedia Commons'
    },
    {
        'system': 'camshaft position sensor',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/7/7c/Crankshaft_sensor.png',
        'source': 'Wikimedia Commons',
        'license': 'CC BY-SA 3.0',
        'caption': 'Cross-section of inductive position sensor (same technology as camshaft sensor)',
        'attribution': 'Image by Tamasflex, CC BY-SA 3.0, via Wikimedia Commons'
    },
    {
        'system': 'crankshaft position sensor',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/7/7c/Crankshaft_sensor.png',
        'source': 'Wikimedia Commons',
        'license': 'CC BY-SA 3.0',
        'caption': 'Cross-section of inductive crankshaft position sensor',
        'attribution': 'Crankshaft_sensor.png by Tamasflex, CC BY-SA 3.0, via Wikimedia Commons'
    },
    {
        'system': 'knock sensor',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/3/33/Piezoelectric_sensor.jpg',
        'source': 'Wikimedia Commons',
        'license': 'CC BY-SA 4.0',
        'caption': 'Working principle of piezoelectric sensor used in knock sensors',
        'attribution': 'Piezoelectric_sensor.jpg by علی رجبی 98, licensed under CC BY-SA 4.0, via Wikimedia Commons'
    },
    {
        'system': 'thermostat',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/0/01/Double_valve_automotive_thermostat.jpg',
        'source': 'Wikimedia Commons',
        'license': 'CC BY-SA 3.0',
        'caption': 'Cross-section of double-valve automotive thermostat showing wax capsule',
        'attribution': 'Image by Dougsim, licensed under CC BY-SA 3.0, via Wikimedia Commons'
    },
    {
        'system': 'pcv valve',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/d/d9/Carterventilatie.JPG',
        'source': 'Wikimedia Commons',
        'license': 'Public Domain',
        'caption': 'Cutaway of crankcase ventilation system showing internal labyrinth',
        'attribution': 'Image by Piero, released into the Public Domain'
    },
    {
        'system': 'radiator',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/4/4c/Thermo-syphon_cooling_circulation_%28Manual_of_Driving_and_Maintenance%29.jpg',
        'source': 'Wikimedia Commons',
        'license': 'Public Domain',
        'caption': 'Cooling system diagram showing radiator location and circulation',
        'attribution': 'From Manual of Driving and Maintenance (1937), Her Majesty\'s Stationery Office. Public Domain.'
    },
    {
        'system': 'timing belt',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/e/e1/Timing_belt_RB30E.jpg',
        'source': 'Wikimedia Commons',
        'license': 'Public Domain',
        'caption': 'Timing belt location showing installation in Nissan RB30E engine',
        'attribution': 'Image is in the Public Domain, released by copyright holder RB30DE'
    },
    {
        'system': 'alternator',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/7/7a/Alternator_%28cut-away%29_%2801%29.JPG',
        'source': 'Wikimedia Commons',
        'license': 'CC BY 2.5',
        'caption': 'Cutaway view of claw-pole alternator showing internal construction',
        'attribution': 'Image by S.J. de Waard, licensed under CC BY 2.5'
    },
    {
        'system': 'battery',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/8/85/Car_battery_cross-section.jpeg',
        'source': 'Wikimedia Commons',
        'license': 'CC BY-SA 3.0',
        'caption': 'Car battery cutaway revealing internal cell compartments and lead plates',
        'attribution': 'Image by Ben Cossalter, licensed under CC BY-SA 3.0, via Wikimedia Commons'
    },
    {
        'system': 'brake pads',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/7/76/Hydraylic_disc_brake_diagram.jpg',
        'source': 'Wikimedia Commons',
        'license': 'Public Domain',
        'caption': 'Technical diagram of hydraulic disc brake system showing brake pads',
        'attribution': 'Image by KDS4444, released into the public domain'
    },
    {
        'system': 'wheel speed sensor',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/3/39/Anti-lock_braking_system_diagram.jpg',
        'source': 'Wikimedia Commons',
        'license': 'Public Domain',
        'caption': 'Anti-lock braking system diagram showing wheel speed sensor locations',
        'attribution': 'Anti-lock braking system diagram by Pemansi, released into the public domain.'
    },
    {
        'system': 'transmission',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/5/5d/Porsche-gearbox-cutaway.jpg',
        'source': 'Wikimedia Commons',
        'license': 'CC BY-SA 3.0',
        'caption': 'Physical cutaway of Porsche manual transmission showing internal gears',
        'attribution': 'Image by BerndB~commonswiki, licensed under CC BY-SA 3.0, via Wikimedia Commons'
    },
    {
        'system': 'air intake manifold',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/7/7f/Manly_1919_Fig_133_Fordson_intake.png',
        'source': 'Wikimedia Commons',
        'license': 'Public Domain',
        'caption': 'Cutaway diagram of Fordson tractor intake manifold system (1919)',
        'attribution': 'Harold P. Manly, "The Ford Motor Car and Truck; Fordson Tractor" (1919), Public Domain'
    }
]


def batch_import():
    """Import all diagrams to database"""
    print(f"\n📥 Batch importing {len(DIAGRAMS)} system diagrams...")

    # Connect to database
    print("\n📡 Connecting to Supabase...")
    supabase = get_supabase_client()
    if not supabase:
        print("❌ Failed to connect to Supabase")
        sys.exit(1)

    repo = SystemDiagramRepository(supabase)

    success_count = 0
    error_count = 0
    skipped_count = 0

    for i, diagram in enumerate(DIAGRAMS, 1):
        system = SYSTEM_NAME_MAP.get(diagram['system'], diagram['system'])

        try:
            # Check if exists
            existing = repo.get_by_system(system)

            if existing:
                print(f"⚠️  {i}/{len(DIAGRAMS)}: '{system}' already exists, skipping")
                skipped_count += 1
                continue

            # Insert
            result = repo.insert(
                system=system,
                image_url=diagram['image_url'],
                source=diagram['source'],
                license=diagram['license'],
                caption=diagram['caption'],
                attribution_text=diagram['attribution']
            )

            if result:
                print(f"✅ {i}/{len(DIAGRAMS)}: '{system}' imported")
                success_count += 1
            else:
                print(f"❌ {i}/{len(DIAGRAMS)}: '{system}' failed (no result returned)")
                error_count += 1

        except Exception as e:
            print(f"❌ {i}/{len(DIAGRAMS)}: '{system}' failed: {e}")
            error_count += 1

    # Summary
    print("\n" + "="*70)
    print("IMPORT COMPLETE")
    print("="*70)
    print(f"✅ Success: {success_count}")
    print(f"⚠️  Skipped: {skipped_count}")
    if error_count:
        print(f"❌ Errors: {error_count}")
    print("="*70)


if __name__ == "__main__":
    batch_import()
