"""Fallback OBD code data when Supabase is unavailable"""

FALLBACK_OBD_CODES = {
    "P0420": {
        "code": "P0420",
        "name": "Catalyst System Efficiency Below Threshold (Bank 1)",
        "system": "Emissions",
        "description": "The powertrain control module (PCM) has detected that the catalytic converter is not working as efficiently as it should be.",
        "severity": "moderate",
        "causes": [
            "Faulty catalytic converter",
            "Damaged oxygen sensors (pre-cat or post-cat)",
            "Exhaust leak near the converter",
            "Engine misfire causing unburned fuel in exhaust",
            "Fuel system issues (running too rich or too lean)"
        ],
        "symptoms": [
            "Check engine light illuminated",
            "Reduced fuel efficiency",
            "Possible sulfur smell from exhaust",
            "May fail emissions test"
        ]
    },
    "P0300": {
        "code": "P0300",
        "name": "Random/Multiple Cylinder Misfire Detected",
        "system": "Ignition",
        "description": "The engine is misfiring on multiple cylinders. This can be caused by various issues affecting combustion.",
        "severity": "serious",
        "causes": [
            "Worn or fouled spark plugs",
            "Faulty ignition coils",
            "Vacuum leaks",
            "Low fuel pressure",
            "Clogged fuel injectors",
            "Engine mechanical problems (worn valves, rings)"
        ],
        "symptoms": [
            "Engine runs rough",
            "Loss of power",
            "Check engine light flashing",
            "Poor fuel economy",
            "Engine hesitation or stumbling"
        ]
    },
    "P0171": {
        "code": "P0171",
        "name": "System Too Lean (Bank 1)",
        "system": "Fuel System",
        "description": "The fuel system is delivering too little fuel or too much air, causing a lean condition.",
        "severity": "moderate",
        "causes": [
            "Vacuum leak in intake manifold",
            "Dirty or faulty mass air flow (MAF) sensor",
            "Weak fuel pump",
            "Clogged fuel filter",
            "Faulty oxygen sensor",
            "Exhaust leak before the O2 sensor"
        ],
        "symptoms": [
            "Check engine light on",
            "Engine hesitation",
            "Rough idle",
            "Lack of power",
            "Hard starting"
        ]
    },
    "P0128": {
        "code": "P0128",
        "name": "Coolant Thermostat (Coolant Temperature Below Thermostat Regulating Temperature)",
        "system": "Cooling System",
        "description": "The engine is not reaching proper operating temperature within the expected time.",
        "severity": "minor",
        "causes": [
            "Faulty thermostat stuck open",
            "Low coolant level",
            "Faulty engine coolant temperature sensor",
            "Faulty cooling fan running continuously"
        ],
        "symptoms": [
            "Check engine light on",
            "Poor fuel economy",
            "Heater may not work properly",
            "Engine takes longer to warm up"
        ]
    },
    "P0442": {
        "code": "P0442",
        "name": "Evaporative Emission Control System Leak Detected (Small Leak)",
        "system": "EVAP",
        "description": "A small leak has been detected in the evaporative emission control system.",
        "severity": "minor",
        "causes": [
            "Loose or damaged gas cap",
            "Cracked EVAP hoses",
            "Faulty purge or vent valve",
            "Leaking fuel tank",
            "Damaged charcoal canister"
        ],
        "symptoms": [
            "Check engine light on",
            "Possible fuel smell",
            "May fail emissions test"
        ]
    },
    "P0301": {
        "code": "P0301",
        "name": "Cylinder 1 Misfire Detected",
        "system": "Ignition",
        "description": "The powertrain control module has detected a misfire in cylinder 1.",
        "severity": "serious",
        "causes": [
            "Faulty spark plug in cylinder 1",
            "Faulty ignition coil",
            "Clogged or faulty fuel injector",
            "Vacuum leak affecting cylinder 1",
            "Low compression in cylinder 1",
            "Worn or damaged spark plug wire"
        ],
        "symptoms": [
            "Check engine light flashing",
            "Engine running rough",
            "Loss of power",
            "Increased emissions",
            "Poor fuel economy"
        ]
    },
    "P0302": {
        "code": "P0302",
        "name": "Cylinder 2 Misfire Detected",
        "system": "Ignition",
        "description": "The powertrain control module has detected a misfire in cylinder 2.",
        "severity": "serious",
        "causes": [
            "Faulty spark plug in cylinder 2",
            "Faulty ignition coil",
            "Clogged or faulty fuel injector",
            "Vacuum leak affecting cylinder 2",
            "Low compression in cylinder 2",
            "Worn or damaged spark plug wire"
        ],
        "symptoms": [
            "Check engine light flashing",
            "Engine running rough",
            "Loss of power",
            "Increased emissions",
            "Poor fuel economy"
        ]
    },
    "P0303": {
        "code": "P0303",
        "name": "Cylinder 3 Misfire Detected",
        "system": "Ignition",
        "description": "The powertrain control module has detected a misfire in cylinder 3.",
        "severity": "serious",
        "causes": [
            "Faulty spark plug in cylinder 3",
            "Faulty ignition coil",
            "Clogged or faulty fuel injector",
            "Vacuum leak affecting cylinder 3",
            "Low compression in cylinder 3",
            "Worn or damaged spark plug wire"
        ],
        "symptoms": [
            "Check engine light flashing",
            "Engine running rough",
            "Loss of power",
            "Increased emissions",
            "Poor fuel economy"
        ]
    },
    "P0304": {
        "code": "P0304",
        "name": "Cylinder 4 Misfire Detected",
        "system": "Ignition",
        "description": "The powertrain control module has detected a misfire in cylinder 4.",
        "severity": "serious",
        "causes": [
            "Faulty spark plug in cylinder 4",
            "Faulty ignition coil",
            "Clogged or faulty fuel injector",
            "Vacuum leak affecting cylinder 4",
            "Low compression in cylinder 4",
            "Worn or damaged spark plug wire"
        ],
        "symptoms": [
            "Check engine light flashing",
            "Engine running rough",
            "Loss of power",
            "Increased emissions",
            "Poor fuel economy"
        ]
    },
    "P0172": {
        "code": "P0172",
        "name": "System Too Rich (Bank 1)",
        "system": "Fuel System",
        "description": "The fuel system is delivering too much fuel or too little air, causing a rich condition.",
        "severity": "moderate",
        "causes": [
            "Faulty oxygen sensor",
            "Dirty or faulty mass air flow (MAF) sensor",
            "Leaking fuel injectors",
            "High fuel pressure",
            "Faulty fuel pressure regulator",
            "Dirty air filter restricting airflow"
        ],
        "symptoms": [
            "Check engine light on",
            "Black smoke from exhaust",
            "Strong fuel smell",
            "Poor fuel economy",
            "Rough idle"
        ]
    },
    "P0401": {
        "code": "P0401",
        "name": "Exhaust Gas Recirculation (EGR) Flow Insufficient",
        "system": "Emissions",
        "description": "The EGR system is not recirculating enough exhaust gas back into the engine.",
        "severity": "moderate",
        "causes": [
            "Clogged EGR valve",
            "Carbon buildup in EGR passages",
            "Faulty EGR valve",
            "Vacuum leak in EGR system",
            "Faulty EGR position sensor"
        ],
        "symptoms": [
            "Check engine light on",
            "Engine knocking or pinging",
            "Increased NOx emissions",
            "May fail emissions test",
            "Slight loss of power"
        ]
    },
    "P0455": {
        "code": "P0455",
        "name": "Evaporative Emission Control System Leak Detected (Large Leak)",
        "system": "EVAP",
        "description": "A large leak has been detected in the evaporative emission control system.",
        "severity": "moderate",
        "causes": [
            "Missing or loose gas cap",
            "Cracked or disconnected EVAP hose",
            "Faulty purge valve stuck open",
            "Damaged fuel tank",
            "Faulty vent valve",
            "Cracked charcoal canister"
        ],
        "symptoms": [
            "Check engine light on",
            "Strong fuel smell",
            "Fuel vapor smell in cabin",
            "May fail emissions test"
        ]
    },
    "P0456": {
        "code": "P0456",
        "name": "Evaporative Emission Control System Leak Detected (Very Small Leak)",
        "system": "EVAP",
        "description": "A very small leak has been detected in the evaporative emission control system.",
        "severity": "minor",
        "causes": [
            "Loose gas cap",
            "Gas cap seal worn out",
            "Very small crack in EVAP hose",
            "Faulty purge or vent valve",
            "Small leak in fuel tank"
        ],
        "symptoms": [
            "Check engine light on",
            "No noticeable drivability issues",
            "May fail emissions test"
        ]
    },
    "P0507": {
        "code": "P0507",
        "name": "Idle Air Control System RPM Higher Than Expected",
        "system": "Air Intake",
        "description": "The engine idle speed is higher than expected.",
        "severity": "minor",
        "causes": [
            "Vacuum leak",
            "Faulty idle air control (IAC) valve",
            "Dirty throttle body",
            "Carbon buildup in intake",
            "Faulty throttle position sensor",
            "Air intake leak"
        ],
        "symptoms": [
            "High idle speed (over 1000 RPM)",
            "Check engine light on",
            "Engine revving on its own",
            "Poor fuel economy"
        ]
    },
    "P0606": {
        "code": "P0606",
        "name": "PCM/ECM Processor Malfunction",
        "system": "Computer",
        "description": "The engine control module (ECM) has detected an internal processor error.",
        "severity": "critical",
        "causes": [
            "Faulty ECM/PCM",
            "Software corruption",
            "Low voltage to ECM",
            "Water damage to ECM",
            "Internal ECM circuit failure"
        ],
        "symptoms": [
            "Check engine light on",
            "Engine won't start",
            "Stalling or rough running",
            "Multiple system failures",
            "Erratic behavior"
        ]
    },
    "P0700": {
        "code": "P0700",
        "name": "Transmission Control System Malfunction",
        "system": "Transmission",
        "description": "The transmission control module has detected a malfunction.",
        "severity": "serious",
        "causes": [
            "Faulty transmission control module",
            "Transmission sensor failure",
            "Wiring issues",
            "Low transmission fluid",
            "Internal transmission problems"
        ],
        "symptoms": [
            "Check engine light on",
            "Transmission warning light on",
            "Harsh shifting",
            "Transmission stuck in gear",
            "No shifting at all"
        ]
    },
    "P0740": {
        "code": "P0740",
        "name": "Torque Converter Clutch Circuit Malfunction",
        "system": "Transmission",
        "description": "The torque converter clutch is not engaging or disengaging properly.",
        "severity": "moderate",
        "causes": [
            "Faulty torque converter clutch solenoid",
            "Low transmission fluid",
            "Dirty transmission fluid",
            "Internal transmission problems",
            "Wiring issues"
        ],
        "symptoms": [
            "Check engine light on",
            "Poor fuel economy",
            "Engine stalling at stops",
            "Transmission slipping",
            "Overheating transmission"
        ]
    },
    "P1450": {
        "code": "P1450",
        "name": "Barometric Pressure Sensor Circuit Malfunction",
        "system": "Sensors",
        "description": "The barometric pressure sensor is not functioning properly.",
        "severity": "minor",
        "causes": [
            "Faulty barometric pressure sensor",
            "Wiring problems",
            "Vacuum leak",
            "Faulty ECM"
        ],
        "symptoms": [
            "Check engine light on",
            "Poor fuel economy",
            "Rough idle at altitude changes",
            "Hesitation during acceleration"
        ]
    },
    "C1201": {
        "code": "C1201",
        "name": "Engine Control System Malfunction",
        "system": "ABS/Chassis",
        "description": "The ABS/traction control system has detected an engine control system problem.",
        "severity": "moderate",
        "causes": [
            "Communication error with ECM",
            "Wiring issues",
            "Faulty ABS module",
            "Low battery voltage",
            "Other engine codes present"
        ],
        "symptoms": [
            "ABS light on",
            "Traction control light on",
            "Check engine light on",
            "ABS system disabled",
            "Traction control disabled"
        ]
    },
    "U0100": {
        "code": "U0100",
        "name": "Lost Communication with ECM/PCM",
        "system": "Network",
        "description": "The vehicle's communication network has lost communication with the engine control module.",
        "severity": "serious",
        "causes": [
            "Faulty ECM/PCM",
            "CAN bus wiring issues",
            "Corroded connectors",
            "Low battery voltage",
            "Blown fuse"
        ],
        "symptoms": [
            "Check engine light on",
            "Vehicle won't start",
            "Multiple warning lights",
            "Loss of power",
            "Erratic gauges"
        ]
    },
    "B0001": {
        "code": "B0001",
        "name": "Driver Airbag Circuit Malfunction",
        "system": "Airbag",
        "description": "A problem has been detected in the driver's airbag circuit.",
        "severity": "serious",
        "causes": [
            "Faulty airbag",
            "Damaged clock spring",
            "Corroded connectors",
            "Wiring damage",
            "Faulty airbag control module"
        ],
        "symptoms": [
            "Airbag warning light on",
            "Airbag system disabled",
            "Horn not working (clock spring)"
        ]
    }
}


def get_fallback_code(code: str) -> dict | None:
    """Get OBD code from fallback data"""
    return FALLBACK_OBD_CODES.get(code.upper())


def search_fallback_codes(query: str) -> list[dict]:
    """Search fallback codes by keyword"""
    query_lower = query.lower()
    results = []
    for code_data in FALLBACK_OBD_CODES.values():
        if (query_lower in code_data['code'].lower() or
            query_lower in code_data['name'].lower() or
            query_lower in code_data['description'].lower()):
            results.append(code_data)
    return results
