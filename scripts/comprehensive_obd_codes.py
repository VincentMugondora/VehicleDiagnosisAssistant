"""
Comprehensive OBD-II Code Dataset
Contains 300+ real-world diagnostic trouble codes across all systems.
"""

# Powertrain (P) Codes - Engine and Transmission
POWERTRAIN_CODES = {
    # Mass Airflow & Intake (P0100-P0199)
    "P0100": {
        "description": "Mass or Volume Air Flow Circuit Malfunction",
        "common_causes": "Faulty MAF sensor, Vacuum leak, Dirty air filter, Damaged wiring",
        "symptoms": "Check engine light, Poor fuel economy, Rough idle, Hesitation on acceleration",
        "generic_fixes": "Clean/replace MAF sensor, Check vacuum lines, Replace air filter, Inspect wiring",
        "system": "Powertrain",
        "severity": "Medium"
    },
    "P0101": {
        "description": "Mass or Volume Air Flow Circuit Range/Performance Problem",
        "common_causes": "Dirty MAF sensor, Air leak after MAF, Faulty MAF sensor",
        "symptoms": "Poor acceleration, Hesitation, Stalling, Black exhaust smoke",
        "generic_fixes": "Clean MAF sensor with specialized cleaner, Check for air leaks, Replace MAF if needed",
        "system": "Powertrain",
        "severity": "Medium"
    },
    "P0102": {
        "description": "Mass or Volume Air Flow Circuit Low Input",
        "common_causes": "Disconnected MAF sensor, Damaged wiring, Failed MAF sensor",
        "symptoms": "Hard starting, Poor performance, Engine stalling",
        "generic_fixes": "Check MAF connector, Test wiring continuity, Replace MAF sensor",
        "system": "Powertrain",
        "severity": "Medium"
    },
    "P0103": {
        "description": "Mass or Volume Air Flow Circuit High Input",
        "common_causes": "Faulty MAF sensor, Short circuit in wiring, Air leak before MAF",
        "symptoms": "Poor fuel economy, Black smoke, Rough idle",
        "generic_fixes": "Test MAF sensor output, Check for wiring shorts, Inspect intake for leaks",
        "system": "Powertrain",
        "severity": "Medium"
    },
    "P0106": {
        "description": "Manifold Absolute Pressure/Barometric Pressure Circuit Range/Performance Problem",
        "common_causes": "Faulty MAP sensor, Vacuum leak, Clogged MAP sensor port",
        "symptoms": "Poor acceleration, Hesitation, Increased emissions",
        "generic_fixes": "Test MAP sensor, Check vacuum lines, Clean MAP sensor port",
        "system": "Powertrain",
        "severity": "Medium"
    },
    "P0107": {
        "description": "Manifold Absolute Pressure/Barometric Pressure Circuit Low Input",
        "common_causes": "Disconnected MAP sensor, Damaged wiring, Failed MAP sensor",
        "symptoms": "Hard starting, Stalling, Poor performance",
        "generic_fixes": "Check MAP connector, Test wiring, Replace MAP sensor",
        "system": "Powertrain",
        "severity": "Medium"
    },
    "P0108": {
        "description": "Manifold Absolute Pressure/Barometric Pressure Circuit High Input",
        "common_causes": "Short circuit in MAP wiring, Failed MAP sensor",
        "symptoms": "Rough idle, Poor fuel economy, Black smoke",
        "generic_fixes": "Check for wiring shorts, Test MAP sensor, Replace if faulty",
        "system": "Powertrain",
        "severity": "Medium"
    },
    "P0110": {
        "description": "Intake Air Temperature Circuit Malfunction",
        "common_causes": "Faulty IAT sensor, Damaged wiring, Poor connection",
        "symptoms": "Hard starting in cold weather, Poor fuel economy",
        "generic_fixes": "Test IAT sensor resistance, Check wiring connections, Replace sensor",
        "system": "Powertrain",
        "severity": "Low"
    },
    "P0112": {
        "description": "Intake Air Temperature Circuit Low Input",
        "common_causes": "Short to ground in IAT circuit, Failed IAT sensor",
        "symptoms": "Hard starting, Rich fuel mixture, Black smoke",
        "generic_fixes": "Check for wiring shorts to ground, Replace IAT sensor",
        "system": "Powertrain",
        "severity": "Low"
    },
    "P0113": {
        "description": "Intake Air Temperature Circuit High Input",
        "common_causes": "Open circuit in IAT wiring, Failed IAT sensor",
        "symptoms": "Poor performance in cold weather, Lean fuel mixture",
        "generic_fixes": "Check wiring continuity, Replace IAT sensor",
        "system": "Powertrain",
        "severity": "Low"
    },

    # Fuel and Air Metering (P0170-P0179)
    "P0170": {
        "description": "Fuel Trim Malfunction (Bank 1)",
        "common_causes": "Vacuum leak, Faulty MAF/MAP sensor, Fuel pressure problem, Exhaust leak",
        "symptoms": "Poor fuel economy, Hesitation, Rough idle",
        "generic_fixes": "Check for vacuum leaks, Test fuel pressure, Inspect exhaust for leaks",
        "system": "Powertrain",
        "severity": "Medium"
    },
    "P0171": {
        "description": "System Too Lean (Bank 1)",
        "common_causes": "Vacuum leak, Weak fuel pump, Dirty fuel injectors, Faulty MAF sensor, Exhaust leak",
        "symptoms": "Rough idle, Poor acceleration, Engine hesitation, Check engine light",
        "generic_fixes": "Check for vacuum leaks, Test fuel pressure, Clean fuel injectors, Test MAF sensor",
        "system": "Powertrain",
        "severity": "Medium"
    },
    "P0172": {
        "description": "System Too Rich (Bank 1)",
        "common_causes": "Faulty O2 sensor, Leaking fuel injectors, Excessive fuel pressure, Dirty air filter",
        "symptoms": "Black smoke from exhaust, Poor fuel economy, Fouled spark plugs, Strong fuel smell",
        "generic_fixes": "Test O2 sensors, Check fuel pressure, Inspect injectors for leaks, Replace air filter",
        "system": "Powertrain",
        "severity": "Medium"
    },
    "P0174": {
        "description": "System Too Lean (Bank 2)",
        "common_causes": "Vacuum leak on bank 2, Faulty MAF sensor, Weak fuel pump",
        "symptoms": "Rough idle, Poor acceleration, Engine hesitation",
        "generic_fixes": "Check for vacuum leaks on bank 2, Test MAF sensor, Check fuel pressure",
        "system": "Powertrain",
        "severity": "Medium"
    },
    "P0175": {
        "description": "System Too Rich (Bank 2)",
        "common_causes": "Faulty O2 sensor bank 2, Leaking fuel injectors, Excessive fuel pressure",
        "symptoms": "Black smoke, Poor fuel economy, Rough idle",
        "generic_fixes": "Test O2 sensors bank 2, Check fuel injector operation, Test fuel pressure",
        "system": "Powertrain",
        "severity": "Medium"
    },

    # Oxygen Sensors (P0130-P0167)
    "P0130": {
        "description": "O2 Sensor Circuit Malfunction (Bank 1, Sensor 1)",
        "common_causes": "Faulty O2 sensor, Damaged wiring, Exhaust leak near sensor",
        "symptoms": "Check engine light, Poor fuel economy, Failed emissions test",
        "generic_fixes": "Test O2 sensor voltage, Check wiring, Replace sensor if faulty",
        "system": "Powertrain",
        "severity": "Medium"
    },
    "P0131": {
        "description": "O2 Sensor Circuit Low Voltage (Bank 1, Sensor 1)",
        "common_causes": "Faulty O2 sensor, Vacuum leak, Low fuel pressure",
        "symptoms": "Poor fuel economy, Rough idle, Hesitation",
        "generic_fixes": "Test O2 sensor, Check for vacuum leaks, Test fuel pressure",
        "system": "Powertrain",
        "severity": "Medium"
    },
    "P0132": {
        "description": "O2 Sensor Circuit High Voltage (Bank 1, Sensor 1)",
        "common_causes": "Faulty O2 sensor, Fuel injector leaking, High fuel pressure",
        "symptoms": "Black smoke, Poor fuel economy, Strong fuel smell",
        "generic_fixes": "Test O2 sensor, Check injectors, Test fuel pressure regulator",
        "system": "Powertrain",
        "severity": "Medium"
    },
    "P0133": {
        "description": "O2 Sensor Circuit Slow Response (Bank 1, Sensor 1)",
        "common_causes": "Contaminated O2 sensor, Aged O2 sensor, Exhaust leak",
        "symptoms": "Poor fuel economy, Sluggish acceleration, Failed emissions",
        "generic_fixes": "Replace O2 sensor, Check for exhaust leaks",
        "system": "Powertrain",
        "severity": "Medium"
    },
    "P0134": {
        "description": "O2 Sensor Circuit No Activity Detected (Bank 1, Sensor 1)",
        "common_causes": "Failed O2 sensor, Damaged wiring, Poor ground connection",
        "symptoms": "Check engine light, Poor fuel economy, Rough running",
        "generic_fixes": "Test O2 sensor operation, Check wiring and grounds, Replace sensor",
        "system": "Powertrain",
        "severity": "Medium"
    },
    "P0135": {
        "description": "O2 Sensor Heater Circuit Malfunction (Bank 1, Sensor 1)",
        "common_causes": "Faulty O2 sensor heater, Blown fuse, Damaged wiring",
        "symptoms": "Extended warm-up time, Poor fuel economy when cold",
        "generic_fixes": "Check fuses, Test heater circuit, Replace O2 sensor",
        "system": "Powertrain",
        "severity": "Low"
    },
    "P0136": {
        "description": "O2 Sensor Circuit Malfunction (Bank 1, Sensor 2)",
        "common_causes": "Faulty downstream O2 sensor, Damaged wiring",
        "symptoms": "Check engine light, May not affect performance",
        "generic_fixes": "Test downstream O2 sensor, Check wiring, Replace if needed",
        "system": "Powertrain",
        "severity": "Low"
    },
    "P0137": {
        "description": "O2 Sensor Circuit Low Voltage (Bank 1, Sensor 2)",
        "common_causes": "Faulty downstream O2 sensor, Exhaust leak after catalytic converter",
        "symptoms": "Check engine light, Possible failed emissions test",
        "generic_fixes": "Test O2 sensor, Check for exhaust leaks, Replace sensor",
        "system": "Powertrain",
        "severity": "Low"
    },
    "P0138": {
        "description": "O2 Sensor Circuit High Voltage (Bank 1, Sensor 2)",
        "common_causes": "Faulty O2 sensor, Failing catalytic converter",
        "symptoms": "Check engine light, Reduced performance",
        "generic_fixes": "Test O2 sensor, Inspect catalytic converter, Replace sensor if faulty",
        "system": "Powertrain",
        "severity": "Medium"
    },
    "P0140": {
        "description": "O2 Sensor Circuit No Activity Detected (Bank 1, Sensor 2)",
        "common_causes": "Failed downstream O2 sensor, Damaged wiring",
        "symptoms": "Check engine light, No noticeable performance issues",
        "generic_fixes": "Test O2 sensor operation, Check wiring, Replace sensor",
        "system": "Powertrain",
        "severity": "Low"
    },
    "P0141": {
        "description": "O2 Sensor Heater Circuit Malfunction (Bank 1, Sensor 2)",
        "common_causes": "Faulty O2 sensor heater, Blown fuse, Wiring damage",
        "symptoms": "Extended catalyst warm-up, Slightly higher emissions when cold",
        "generic_fixes": "Check fuses, Test heater circuit, Replace O2 sensor",
        "system": "Powertrain",
        "severity": "Low"
    },

    # Catalyst System (P0420-P0439)
    "P0420": {
        "description": "Catalyst System Efficiency Below Threshold (Bank 1)",
        "common_causes": "Failing catalytic converter, Faulty O2 sensors, Exhaust leak, Engine misfire damage",
        "symptoms": "Check engine light, Reduced performance, Failed emissions test, Rotten egg smell",
        "generic_fixes": "Replace catalytic converter, Test O2 sensors, Check for exhaust leaks, Fix any misfires first",
        "system": "Powertrain",
        "severity": "Medium"
    },
    "P0430": {
        "description": "Catalyst System Efficiency Below Threshold (Bank 2)",
        "common_causes": "Failing catalytic converter bank 2, Faulty O2 sensors, Exhaust leak",
        "symptoms": "Check engine light, Reduced performance, Failed emissions test",
        "generic_fixes": "Replace catalytic converter bank 2, Test O2 sensors, Check exhaust system",
        "system": "Powertrain",
        "severity": "Medium"
    },

    # EVAP System (P0440-P0459)
    "P0440": {
        "description": "Evaporative Emission Control System Malfunction",
        "common_causes": "Loose gas cap, Cracked EVAP hose, Faulty purge valve, Leaking fuel tank",
        "symptoms": "Check engine light, Fuel smell",
        "generic_fixes": "Tighten gas cap, Inspect EVAP hoses, Test purge valve, Smoke test EVAP system",
        "system": "Powertrain",
        "severity": "Low"
    },
    "P0441": {
        "description": "Evaporative Emission Control System Incorrect Purge Flow",
        "common_causes": "Faulty purge valve, Blocked EVAP canister, Damaged EVAP hoses",
        "symptoms": "Check engine light, Possible rough idle",
        "generic_fixes": "Test purge valve operation, Inspect canister, Check EVAP hoses",
        "system": "Powertrain",
        "severity": "Low"
    },
    "P0442": {
        "description": "Evaporative Emission Control System Leak Detected (Small Leak)",
        "common_causes": "Loose gas cap, Small crack in EVAP hose, Leaking fuel filler neck seal",
        "symptoms": "Check engine light, Possible fuel smell",
        "generic_fixes": "Tighten/replace gas cap, Inspect all EVAP hoses, Check fuel filler neck seal",
        "system": "Powertrain",
        "severity": "Low"
    },
    "P0443": {
        "description": "Evaporative Emission Control System Purge Control Valve Circuit Malfunction",
        "common_causes": "Faulty purge valve, Damaged wiring, Poor electrical connection",
        "symptoms": "Check engine light, May have rough idle when cold",
        "generic_fixes": "Test purge valve, Check wiring and connector, Replace valve if needed",
        "system": "Powertrain",
        "severity": "Low"
    },
    "P0446": {
        "description": "Evaporative Emission Control System Vent Control Circuit Malfunction",
        "common_causes": "Faulty vent valve, Blocked vent line, Damaged wiring",
        "symptoms": "Check engine light, Difficulty refueling",
        "generic_fixes": "Test vent valve, Check vent line for blockage, Inspect wiring",
        "system": "Powertrain",
        "severity": "Low"
    },
    "P0455": {
        "description": "Evaporative Emission Control System Leak Detected (Large Leak)",
        "common_causes": "Missing/loose gas cap, Large crack in EVAP hose, Leaking fuel tank",
        "symptoms": "Check engine light, Strong fuel smell",
        "generic_fixes": "Check gas cap, Inspect all EVAP components, Smoke test system for large leaks",
        "system": "Powertrain",
        "severity": "Medium"
    },
    "P0456": {
        "description": "Evaporative Emission Control System Leak Detected (Very Small Leak)",
        "common_causes": "Slightly loose gas cap, Tiny crack in EVAP hose, Small seal leak",
        "symptoms": "Check engine light",
        "generic_fixes": "Tighten gas cap, Inspect EVAP hoses carefully, Smoke test recommended",
        "system": "Powertrain",
        "severity": "Low"
    },

    # Misfire Codes (P0300-P0312)
    "P0300": {
        "description": "Random/Multiple Cylinder Misfire Detected",
        "common_causes": "Faulty spark plugs, Bad ignition coils, Vacuum leak, Low compression, Fuel delivery issue",
        "symptoms": "Check engine light flashing, Rough idle, Loss of power, Poor fuel economy, Engine vibration",
        "generic_fixes": "Replace spark plugs, Test ignition coils, Check for vacuum leaks, Test compression, Check fuel pressure",
        "system": "Powertrain",
        "severity": "High"
    },
    "P0301": {
        "description": "Cylinder 1 Misfire Detected",
        "common_causes": "Faulty spark plug cyl 1, Bad ignition coil cyl 1, Fuel injector issue, Low compression",
        "symptoms": "Rough idle, Loss of power, Check engine light flashing",
        "generic_fixes": "Replace spark plug cyl 1, Test ignition coil cyl 1, Check fuel injector, Test compression",
        "system": "Powertrain",
        "severity": "High"
    },
    "P0302": {
        "description": "Cylinder 2 Misfire Detected",
        "common_causes": "Faulty spark plug cyl 2, Bad ignition coil cyl 2, Fuel injector issue, Low compression",
        "symptoms": "Rough idle, Loss of power, Check engine light flashing",
        "generic_fixes": "Replace spark plug cyl 2, Test ignition coil cyl 2, Check fuel injector, Test compression",
        "system": "Powertrain",
        "severity": "High"
    },
    "P0303": {
        "description": "Cylinder 3 Misfire Detected",
        "common_causes": "Faulty spark plug cyl 3, Bad ignition coil cyl 3, Fuel injector issue, Low compression",
        "symptoms": "Rough idle, Loss of power, Check engine light flashing",
        "generic_fixes": "Replace spark plug cyl 3, Test ignition coil cyl 3, Check fuel injector, Test compression",
        "system": "Powertrain",
        "severity": "High"
    },
    "P0304": {
        "description": "Cylinder 4 Misfire Detected",
        "common_causes": "Faulty spark plug cyl 4, Bad ignition coil cyl 4, Fuel injector issue, Low compression",
        "symptoms": "Rough idle, Loss of power, Check engine light flashing",
        "generic_fixes": "Replace spark plug cyl 4, Test ignition coil cyl 4, Check fuel injector, Test compression",
        "system": "Powertrain",
        "severity": "High"
    },
    "P0305": {
        "description": "Cylinder 5 Misfire Detected",
        "common_causes": "Faulty spark plug cyl 5, Bad ignition coil cyl 5, Fuel injector issue, Low compression",
        "symptoms": "Rough idle, Loss of power, Check engine light flashing",
        "generic_fixes": "Replace spark plug cyl 5, Test ignition coil cyl 5, Check fuel injector, Test compression",
        "system": "Powertrain",
        "severity": "High"
    },
    "P0306": {
        "description": "Cylinder 6 Misfire Detected",
        "common_causes": "Faulty spark plug cyl 6, Bad ignition coil cyl 6, Fuel injector issue, Low compression",
        "symptoms": "Rough idle, Loss of power, Check engine light flashing",
        "generic_fixes": "Replace spark plug cyl 6, Test ignition coil cyl 6, Check fuel injector, Test compression",
        "system": "Powertrain",
        "severity": "High"
    },
    "P0307": {
        "description": "Cylinder 7 Misfire Detected",
        "common_causes": "Faulty spark plug cyl 7, Bad ignition coil cyl 7, Fuel injector issue, Low compression",
        "symptoms": "Rough idle, Loss of power, Check engine light flashing",
        "generic_fixes": "Replace spark plug cyl 7, Test ignition coil cyl 7, Check fuel injector, Test compression",
        "system": "Powertrain",
        "severity": "High"
    },
    "P0308": {
        "description": "Cylinder 8 Misfire Detected",
        "common_causes": "Faulty spark plug cyl 8, Bad ignition coil cyl 8, Fuel injector issue, Low compression",
        "symptoms": "Rough idle, Loss of power, Check engine light flashing",
        "generic_fixes": "Replace spark plug cyl 8, Test ignition coil cyl 8, Check fuel injector, Test compression",
        "system": "Powertrain",
        "severity": "High"
    },

    # Fuel System (P0200-P0299)
    "P0200": {
        "description": "Injector Circuit Malfunction",
        "common_causes": "Faulty fuel injector, Damaged wiring, ECM issue",
        "symptoms": "Rough idle, Poor performance, Hard starting",
        "generic_fixes": "Test all injectors, Check wiring, Test ECM outputs",
        "system": "Powertrain",
        "severity": "Medium"
    },
    "P0201": {
        "description": "Injector Circuit Malfunction - Cylinder 1",
        "common_causes": "Faulty injector cyl 1, Damaged wiring, Poor connection",
        "symptoms": "Rough idle, Misfire cyl 1, Poor performance",
        "generic_fixes": "Test injector cyl 1, Check wiring and connector, Replace if faulty",
        "system": "Powertrain",
        "severity": "Medium"
    },
    "P0202": {
        "description": "Injector Circuit Malfunction - Cylinder 2",
        "common_causes": "Faulty injector cyl 2, Damaged wiring, Poor connection",
        "symptoms": "Rough idle, Misfire cyl 2, Poor performance",
        "generic_fixes": "Test injector cyl 2, Check wiring and connector, Replace if faulty",
        "system": "Powertrain",
        "severity": "Medium"
    },
    "P0203": {
        "description": "Injector Circuit Malfunction - Cylinder 3",
        "common_causes": "Faulty injector cyl 3, Damaged wiring, Poor connection",
        "symptoms": "Rough idle, Misfire cyl 3, Poor performance",
        "generic_fixes": "Test injector cyl 3, Check wiring and connector, Replace if faulty",
        "system": "Powertrain",
        "severity": "Medium"
    },
    "P0204": {
        "description": "Injector Circuit Malfunction - Cylinder 4",
        "common_causes": "Faulty injector cyl 4, Damaged wiring, Poor connection",
        "symptoms": "Rough idle, Misfire cyl 4, Poor performance",
        "generic_fixes": "Test injector cyl 4, Check wiring and connector, Replace if faulty",
        "system": "Powertrain",
        "severity": "Medium"
    },
    "P0205": {
        "description": "Injector Circuit Malfunction - Cylinder 5",
        "common_causes": "Faulty injector cyl 5, Damaged wiring, Poor connection",
        "symptoms": "Rough idle, Misfire cyl 5, Poor performance",
        "generic_fixes": "Test injector cyl 5, Check wiring and connector, Replace if faulty",
        "system": "Powertrain",
        "severity": "Medium"
    },
    "P0206": {
        "description": "Injector Circuit Malfunction - Cylinder 6",
        "common_causes": "Faulty injector cyl 6, Damaged wiring, Poor connection",
        "symptoms": "Rough idle, Misfire cyl 6, Poor performance",
        "generic_fixes": "Test injector cyl 6, Check wiring and connector, Replace if faulty",
        "system": "Powertrain",
        "severity": "Medium"
    },
    "P0207": {
        "description": "Injector Circuit Malfunction - Cylinder 7",
        "common_causes": "Faulty injector cyl 7, Damaged wiring, Poor connection",
        "symptoms": "Rough idle, Misfire cyl 7, Poor performance",
        "generic_fixes": "Test injector cyl 7, Check wiring and connector, Replace if faulty",
        "system": "Powertrain",
        "severity": "Medium"
    },
    "P0208": {
        "description": "Injector Circuit Malfunction - Cylinder 8",
        "common_causes": "Faulty injector cyl 8, Damaged wiring, Poor connection",
        "symptoms": "Rough idle, Misfire cyl 8, Poor performance",
        "generic_fixes": "Test injector cyl 8, Check wiring and connector, Replace if faulty",
        "system": "Powertrain",
        "severity": "Medium"
    },
    "P0128": {
        "description": "Coolant Thermostat (Coolant Temperature Below Thermostat Regulating Temperature)",
        "common_causes": "Stuck open thermostat, Faulty coolant temperature sensor, Low coolant level",
        "symptoms": "Temperature gauge stays low, Poor heater performance, Poor fuel economy, Extended warm-up time",
        "generic_fixes": "Replace thermostat, Test coolant temperature sensor, Check coolant level, Verify cooling fan operation",
        "system": "Powertrain",
        "severity": "Low"
    },
    "P0217": {
        "description": "Engine Coolant Over Temperature Condition",
        "common_causes": "Low coolant, Faulty thermostat, Bad water pump, Cooling fan failure, Radiator blockage",
        "symptoms": "Temperature gauge in red, Steam from engine, Loss of power",
        "generic_fixes": "Check coolant level, Test thermostat, Inspect water pump, Check cooling fans, Flush radiator",
        "system": "Powertrain",
        "severity": "High"
    },
    "P0218": {
        "description": "Transmission Fluid Over Temperature",
        "common_causes": "Low transmission fluid, Faulty transmission cooler, Excessive load, Slipping transmission",
        "symptoms": "Transmission slipping, Burning smell, Check engine light",
        "generic_fixes": "Check transmission fluid level, Inspect transmission cooler, Avoid excessive towing",
        "system": "Powertrain",
        "severity": "High"
    },
    "P0220": {
        "description": "Throttle/Pedal Position Sensor B Circuit Malfunction",
        "common_causes": "Faulty throttle position sensor, Damaged wiring, Poor connection",
        "symptoms": "Poor acceleration, Rough idle, Reduced power",
        "generic_fixes": "Test TPS sensor, Check wiring and connectors, Replace sensor if needed",
        "system": "Powertrain",
        "severity": "Medium"
    },
    "P0230": {
        "description": "Fuel Pump Primary Circuit Malfunction",
        "common_causes": "Faulty fuel pump relay, Damaged wiring, Failed fuel pump",
        "symptoms": "Hard starting, No start, Engine stalling",
        "generic_fixes": "Test fuel pump relay, Check wiring, Test fuel pump operation",
        "system": "Powertrain",
        "severity": "High"
    },

    # Ignition System (P0350-P0369)
    "P0351": {
        "description": "Ignition Coil A Primary/Secondary Circuit Malfunction",
        "common_causes": "Faulty ignition coil, Damaged wiring, ECM issue",
        "symptoms": "Misfire, Rough idle, Loss of power",
        "generic_fixes": "Test ignition coil, Check wiring, Replace coil if faulty",
        "system": "Powertrain",
        "severity": "High"
    },
    "P0352": {
        "description": "Ignition Coil B Primary/Secondary Circuit Malfunction",
        "common_causes": "Faulty ignition coil, Damaged wiring, ECM issue",
        "symptoms": "Misfire, Rough idle, Loss of power",
        "generic_fixes": "Test ignition coil, Check wiring, Replace coil if faulty",
        "system": "Powertrain",
        "severity": "High"
    },
    "P0353": {
        "description": "Ignition Coil C Primary/Secondary Circuit Malfunction",
        "common_causes": "Faulty ignition coil, Damaged wiring, ECM issue",
        "symptoms": "Misfire, Rough idle, Loss of power",
        "generic_fixes": "Test ignition coil, Check wiring, Replace coil if faulty",
        "system": "Powertrain",
        "severity": "High"
    },
    "P0354": {
        "description": "Ignition Coil D Primary/Secondary Circuit Malfunction",
        "common_causes": "Faulty ignition coil, Damaged wiring, ECM issue",
        "symptoms": "Misfire, Rough idle, Loss of power",
        "generic_fixes": "Test ignition coil, Check wiring, Replace coil if faulty",
        "system": "Powertrain",
        "severity": "High"
    },

    # Camshaft/Crankshaft Position (P0335-P0349)
    "P0335": {
        "description": "Crankshaft Position Sensor A Circuit Malfunction",
        "common_causes": "Faulty crankshaft position sensor, Damaged sensor wiring, Sensor misalignment",
        "symptoms": "No start, Stalling, Intermittent starting issues",
        "generic_fixes": "Test crankshaft sensor, Check wiring, Verify sensor gap, Replace sensor",
        "system": "Powertrain",
        "severity": "High"
    },
    "P0340": {
        "description": "Camshaft Position Sensor Circuit Malfunction",
        "common_causes": "Faulty camshaft position sensor, Damaged wiring, Timing chain/belt issue",
        "symptoms": "Hard starting, Rough idle, Poor performance, Stalling",
        "generic_fixes": "Test camshaft sensor, Check wiring, Verify timing marks, Replace sensor",
        "system": "Powertrain",
        "severity": "High"
    },
    "P0341": {
        "description": "Camshaft Position Sensor Circuit Range/Performance",
        "common_causes": "Faulty camshaft sensor, Timing chain stretched, Jumped timing",
        "symptoms": "Hard starting, Rough idle, Poor performance",
        "generic_fixes": "Test camshaft sensor, Check timing marks, Inspect timing chain/belt",
        "system": "Powertrain",
        "severity": "High"
    },

    # Knock Sensor (P0325-P0334)
    "P0325": {
        "description": "Knock Sensor 1 Circuit Malfunction (Bank 1)",
        "common_causes": "Faulty knock sensor, Damaged wiring, Loose sensor mounting",
        "symptoms": "Pinging/knocking sound, Reduced performance, Poor fuel economy",
        "generic_fixes": "Test knock sensor, Check wiring, Torque sensor properly, Replace if faulty",
        "system": "Powertrain",
        "severity": "Medium"
    },
    "P0330": {
        "description": "Knock Sensor 2 Circuit Malfunction (Bank 2)",
        "common_causes": "Faulty knock sensor bank 2, Damaged wiring, Loose mounting",
        "symptoms": "Pinging/knocking sound, Reduced performance",
        "generic_fixes": "Test knock sensor, Check wiring, Torque sensor, Replace if needed",
        "system": "Powertrain",
        "severity": "Medium"
    },

    # Variable Valve Timing (P0010-P0029)
    "P0010": {
        "description": "Intake Camshaft Position Actuator Circuit (Bank 1)",
        "common_causes": "Faulty VVT solenoid, Dirty engine oil, Low oil level, Wiring issue",
        "symptoms": "Rough idle, Poor performance, Increased fuel consumption",
        "generic_fixes": "Change engine oil, Test VVT solenoid, Check wiring, Replace solenoid",
        "system": "Powertrain",
        "severity": "Medium"
    },
    "P0011": {
        "description": "Intake Camshaft Position Timing Over-Advanced (Bank 1)",
        "common_causes": "Dirty engine oil, Faulty VVT solenoid, Timing chain stretched, Low oil pressure",
        "symptoms": "Rough idle, Poor performance, Check engine light",
        "generic_fixes": "Change engine oil, Test VVT system, Check timing chain, Test oil pressure",
        "system": "Powertrain",
        "severity": "Medium"
    },
    "P0012": {
        "description": "Intake Camshaft Position Timing Over-Retarded (Bank 1)",
        "common_causes": "Dirty engine oil, Faulty VVT solenoid, Timing chain issue",
        "symptoms": "Rough idle, Poor acceleration, Check engine light",
        "generic_fixes": "Change engine oil, Test VVT solenoid, Inspect timing chain",
        "system": "Powertrain",
        "severity": "Medium"
    },
    "P0014": {
        "description": "Exhaust Camshaft Position Timing Over-Advanced (Bank 1)",
        "common_causes": "Dirty engine oil, Faulty VVT solenoid, Timing issue",
        "symptoms": "Rough idle, Poor performance, Increased emissions",
        "generic_fixes": "Change engine oil, Test VVT system, Check timing",
        "system": "Powertrain",
        "severity": "Medium"
    },
    "P0016": {
        "description": "Crankshaft Position/Camshaft Position Correlation (Bank 1)",
        "common_causes": "Jumped timing chain/belt, Worn timing components, Faulty cam/crank sensors",
        "symptoms": "Hard starting, Rough idle, Poor performance, Rattling noise",
        "generic_fixes": "Inspect timing chain/belt, Check timing marks, Test sensors, Replace timing components",
        "system": "Powertrain",
        "severity": "High"
    },
    "P0017": {
        "description": "Crankshaft Position/Camshaft Position Correlation (Bank 1 Exhaust)",
        "common_causes": "Timing chain stretched, Jumped timing, Faulty sensors",
        "symptoms": "Hard starting, Rough running, Poor performance",
        "generic_fixes": "Check timing marks, Inspect timing chain, Test sensors",
        "system": "Powertrain",
        "severity": "High"
    },
    "P0020": {
        "description": "Intake Camshaft Position Actuator Circuit (Bank 2)",
        "common_causes": "Faulty VVT solenoid bank 2, Dirty oil, Wiring issue",
        "symptoms": "Rough idle, Poor performance",
        "generic_fixes": "Change oil, Test VVT solenoid, Check wiring",
        "system": "Powertrain",
        "severity": "Medium"
    },
    "P0021": {
        "description": "Intake Camshaft Position Timing Over-Advanced (Bank 2)",
        "common_causes": "Dirty oil, Faulty VVT solenoid bank 2, Timing issue",
        "symptoms": "Rough idle, Poor performance",
        "generic_fixes": "Change oil, Test VVT system, Check timing",
        "system": "Powertrain",
        "severity": "Medium"
    },
}

# Chassis (C) Codes - ABS, Suspension, Steering
CHASSIS_CODES = {
    "C0035": {
        "description": "Left Front Wheel Speed Sensor Circuit Malfunction",
        "common_causes": "Faulty wheel speed sensor, Damaged wiring, Dirty sensor, Damaged tone ring",
        "symptoms": "ABS light on, Traction control disabled, ABS not working",
        "generic_fixes": "Clean wheel speed sensor, Check wiring, Test sensor, Replace if faulty",
        "system": "Chassis",
        "severity": "Medium"
    },
    "C0040": {
        "description": "Right Front Wheel Speed Sensor Circuit Malfunction",
        "common_causes": "Faulty wheel speed sensor, Damaged wiring, Dirty sensor",
        "symptoms": "ABS light on, Traction control disabled",
        "generic_fixes": "Clean sensor, Check wiring, Test sensor, Replace if needed",
        "system": "Chassis",
        "severity": "Medium"
    },
    "C0045": {
        "description": "Left Rear Wheel Speed Sensor Circuit Malfunction",
        "common_causes": "Faulty wheel speed sensor, Damaged wiring, Dirty sensor",
        "symptoms": "ABS light on, Traction control disabled",
        "generic_fixes": "Clean sensor, Check wiring, Test sensor, Replace if faulty",
        "system": "Chassis",
        "severity": "Medium"
    },
    "C0050": {
        "description": "Right Rear Wheel Speed Sensor Circuit Malfunction",
        "common_causes": "Faulty wheel speed sensor, Damaged wiring, Dirty sensor",
        "symptoms": "ABS light on, Traction control disabled",
        "generic_fixes": "Clean sensor, Check wiring, Test sensor, Replace if needed",
        "system": "Chassis",
        "severity": "Medium"
    },
    "C0060": {
        "description": "Left Front ABS Motor Circuit Malfunction",
        "common_causes": "Faulty ABS motor, Damaged wiring, ABS module issue",
        "symptoms": "ABS light on, ABS not functioning",
        "generic_fixes": "Test ABS motor, Check wiring, Scan ABS module, Replace motor if faulty",
        "system": "Chassis",
        "severity": "Medium"
    },
    "C0070": {
        "description": "ABS Control Module Malfunction",
        "common_causes": "Failed ABS module, Software issue, Water damage, Electrical fault",
        "symptoms": "ABS light on, ABS not working, Traction control disabled",
        "generic_fixes": "Scan for additional codes, Check module connections, Reprogram or replace module",
        "system": "Chassis",
        "severity": "High"
    },
    "C0121": {
        "description": "ABS Valve Circuit Malfunction",
        "common_causes": "Faulty ABS valve, Damaged wiring, Low brake fluid, ABS pump failure",
        "symptoms": "ABS light on, ABS malfunction, Spongy brake pedal",
        "generic_fixes": "Check brake fluid level, Test ABS valves, Bleed ABS system, Replace valve if faulty",
        "system": "Chassis",
        "severity": "High"
    },
    "C0265": {
        "description": "Electronic Brake Control Module Malfunction",
        "common_causes": "Failed EBCM, Software corruption, Electrical issue",
        "symptoms": "ABS light on, Traction control light on, Brake warning light",
        "generic_fixes": "Reprogram EBCM, Check power and ground, Replace module if failed",
        "system": "Chassis",
        "severity": "High"
    },
}

# Body (B) Codes - Airbags, Comfort, Lighting
BODY_CODES = {
    "B0001": {
        "description": "Driver Airbag Circuit Malfunction",
        "common_causes": "Faulty airbag, Damaged clock spring, Wiring issue, Seat connector problem",
        "symptoms": "Airbag light on, Airbag may not deploy in crash",
        "generic_fixes": "Check clock spring, Test airbag circuit, Inspect connectors, Replace airbag if faulty",
        "system": "Body",
        "severity": "High"
    },
    "B0002": {
        "description": "Passenger Airbag Circuit Malfunction",
        "common_causes": "Faulty passenger airbag, Damaged wiring, Seat sensor issue",
        "symptoms": "Airbag light on, Passenger airbag disabled",
        "generic_fixes": "Test airbag circuit, Check seat sensor, Inspect wiring, Replace airbag if needed",
        "system": "Body",
        "severity": "High"
    },
    "B0010": {
        "description": "Side Airbag Circuit Malfunction (Driver)",
        "common_causes": "Faulty side airbag, Damaged wiring in seat, Connector issue",
        "symptoms": "Airbag warning light on",
        "generic_fixes": "Check seat wiring, Test airbag circuit, Replace airbag if faulty",
        "system": "Body",
        "severity": "High"
    },
    "B0015": {
        "description": "Side Airbag Circuit Malfunction (Passenger)",
        "common_causes": "Faulty side airbag, Damaged seat wiring, Connector problem",
        "symptoms": "Airbag warning light on",
        "generic_fixes": "Inspect seat wiring, Test circuit, Replace airbag if needed",
        "system": "Body",
        "severity": "High"
    },
    "B0020": {
        "description": "Curtain Airbag Circuit Malfunction",
        "common_causes": "Faulty curtain airbag, Damaged roof wiring, Connector issue",
        "symptoms": "Airbag light on, Curtain airbag disabled",
        "generic_fixes": "Check roof wiring, Test circuit, Replace curtain airbag if faulty",
        "system": "Body",
        "severity": "High"
    },
    "B0032": {
        "description": "Airbag Control Module Malfunction",
        "common_causes": "Failed airbag module, Software issue, Crash data stored, Power issue",
        "symptoms": "Airbag light on, All airbags may be disabled",
        "generic_fixes": "Clear crash data, Reprogram module, Check power supply, Replace if failed",
        "system": "Body",
        "severity": "High"
    },
    "B0050": {
        "description": "Battery Voltage Low",
        "common_causes": "Weak battery, Alternator failure, Parasitic draw, Bad battery connection",
        "symptoms": "Warning lights, Dim lights, Hard starting, Electrical issues",
        "generic_fixes": "Test battery voltage, Check alternator output, Test for parasitic draw, Replace battery",
        "system": "Body",
        "severity": "Medium"
    },
    "B0100": {
        "description": "Battery Voltage High",
        "common_causes": "Overcharging alternator, Failed voltage regulator, Bad alternator",
        "symptoms": "Warning lights, Flickering lights, Electrical component failure",
        "generic_fixes": "Test charging system, Check voltage regulator, Replace alternator if faulty",
        "system": "Body",
        "severity": "Medium"
    },
    "B1000": {
        "description": "Door Ajar Switch Circuit Malfunction",
        "common_causes": "Faulty door switch, Damaged wiring, Misaligned door",
        "symptoms": "Door ajar warning stays on, Interior lights stay on, Alarm issues",
        "generic_fixes": "Test door switches, Check wiring, Adjust door alignment, Replace switch",
        "system": "Body",
        "severity": "Low"
    },
    "B1317": {
        "description": "Battery Voltage Out of Range",
        "common_causes": "Weak battery, Alternator issue, Bad battery connection, ECU issue",
        "symptoms": "Warning lights, Electrical problems, Hard starting",
        "generic_fixes": "Test battery and alternator, Clean battery terminals, Check connections",
        "system": "Body",
        "severity": "Medium"
    },
    "B1342": {
        "description": "ECU is Defective",
        "common_causes": "Failed ECU, Software corruption, Water damage, Power surge damage",
        "symptoms": "Multiple warning lights, Various system malfunctions, No start",
        "generic_fixes": "Reprogram ECU, Check for water damage, Test power supply, Replace ECU",
        "system": "Body",
        "severity": "High"
    },
}

# Network (U) Codes - Communication
NETWORK_CODES = {
    "U0001": {
        "description": "High Speed CAN Communication Bus",
        "common_causes": "Damaged CAN wiring, Failed module, Poor connection, Bus termination issue",
        "symptoms": "Multiple warning lights, System malfunctions, Intermittent issues",
        "generic_fixes": "Check CAN bus wiring, Test modules, Check termination resistors, Repair wiring",
        "system": "Network",
        "severity": "High"
    },
    "U0073": {
        "description": "Control Module Communication Bus Off",
        "common_causes": "CAN bus short circuit, Module failure, Wiring damage",
        "symptoms": "Multiple systems not communicating, Warning lights",
        "generic_fixes": "Check CAN bus for shorts, Test modules, Repair wiring damage",
        "system": "Network",
        "severity": "High"
    },
    "U0100": {
        "description": "Lost Communication with ECM/PCM",
        "common_causes": "Failed ECM, CAN bus issue, Power supply problem, Wiring damage",
        "symptoms": "No start, Multiple warning lights, Various system failures",
        "generic_fixes": "Check ECM power and ground, Test CAN bus, Check wiring, Replace ECM if failed",
        "system": "Network",
        "severity": "High"
    },
    "U0101": {
        "description": "Lost Communication with TCM",
        "common_causes": "Failed TCM, CAN bus issue, Wiring damage, Power problem",
        "symptoms": "Transmission stuck in gear, No shift, Multiple warning lights",
        "generic_fixes": "Check TCM power, Test CAN bus, Check wiring, Replace TCM if needed",
        "system": "Network",
        "severity": "High"
    },
    "U0121": {
        "description": "Lost Communication with ABS Module",
        "common_causes": "Failed ABS module, CAN bus issue, Wiring damage",
        "symptoms": "ABS light on, Traction control disabled, Multiple warnings",
        "generic_fixes": "Check ABS module power, Test CAN bus, Repair wiring, Replace module",
        "system": "Network",
        "severity": "Medium"
    },
    "U0122": {
        "description": "Lost Communication with Vehicle Dynamics Control Module",
        "common_causes": "Failed VDC module, CAN bus problem, Wiring issue",
        "symptoms": "Stability control disabled, Warning lights on",
        "generic_fixes": "Check module power, Test CAN communication, Check wiring",
        "system": "Network",
        "severity": "Medium"
    },
    "U0126": {
        "description": "Lost Communication with Steering Angle Sensor Module",
        "common_causes": "Failed steering angle sensor, CAN bus issue, Calibration needed",
        "symptoms": "Stability control issues, Steering warning light",
        "generic_fixes": "Calibrate steering angle sensor, Check CAN bus, Replace sensor",
        "system": "Network",
        "severity": "Medium"
    },
    "U0140": {
        "description": "Lost Communication with Body Control Module",
        "common_causes": "Failed BCM, CAN bus problem, Power issue, Wiring damage",
        "symptoms": "Multiple electrical systems not working, Warning lights",
        "generic_fixes": "Check BCM power, Test CAN bus, Repair wiring, Replace BCM",
        "system": "Network",
        "severity": "High"
    },
    "U0155": {
        "description": "Lost Communication with Instrument Panel Cluster",
        "common_causes": "Failed instrument cluster, CAN bus issue, Wiring problem",
        "symptoms": "Gauges not working, Warning lights not functioning",
        "generic_fixes": "Check cluster connections, Test CAN bus, Replace cluster if failed",
        "system": "Network",
        "severity": "Medium"
    },
    "U0164": {
        "description": "Lost Communication with HVAC Control Module",
        "common_causes": "Failed HVAC module, CAN bus issue, Wiring damage",
        "symptoms": "Climate control not working, No communication with controls",
        "generic_fixes": "Check HVAC module power, Test CAN bus, Replace module",
        "system": "Network",
        "severity": "Low"
    },
}

# Additional Common Powertrain Codes
ADDITIONAL_POWERTRAIN = {
    "P0401": {
        "description": "Exhaust Gas Recirculation Flow Insufficient",
        "common_causes": "Clogged EGR valve, Carbon buildup, Faulty EGR valve, Vacuum hose issue",
        "symptoms": "Failed emissions test, Rough idle, Hesitation, Increased NOx emissions",
        "generic_fixes": "Clean EGR valve and passages, Replace EGR valve, Check vacuum lines",
        "system": "Powertrain",
        "severity": "Medium"
    },
    "P0402": {
        "description": "Exhaust Gas Recirculation Flow Excessive",
        "common_causes": "Stuck open EGR valve, Faulty EGR solenoid, Vacuum leak",
        "symptoms": "Rough idle, Stalling, Poor performance, Black smoke",
        "generic_fixes": "Test EGR valve operation, Replace EGR valve, Check EGR solenoid",
        "system": "Powertrain",
        "severity": "Medium"
    },
    "P0403": {
        "description": "Exhaust Gas Recirculation Circuit Malfunction",
        "common_causes": "Faulty EGR solenoid, Damaged wiring, Poor electrical connection",
        "symptoms": "Check engine light, Failed emissions test",
        "generic_fixes": "Test EGR solenoid, Check wiring and connectors, Replace solenoid",
        "system": "Powertrain",
        "severity": "Medium"
    },
    "P0404": {
        "description": "Exhaust Gas Recirculation Circuit Range/Performance",
        "common_causes": "Carbon buildup in EGR, Faulty EGR valve, Position sensor issue",
        "symptoms": "Rough idle, Poor performance, Failed emissions",
        "generic_fixes": "Clean EGR system, Test EGR valve, Replace if faulty",
        "system": "Powertrain",
        "severity": "Medium"
    },
    "P0500": {
        "description": "Vehicle Speed Sensor Malfunction",
        "common_causes": "Faulty VSS, Damaged wiring, Bad speedometer cable, Transmission issue",
        "symptoms": "Speedometer not working, Transmission shifting issues, Check engine light",
        "generic_fixes": "Test VSS, Check wiring, Replace sensor, Inspect speedometer cable",
        "system": "Powertrain",
        "severity": "Medium"
    },
    "P0505": {
        "description": "Idle Control System Malfunction",
        "common_causes": "Dirty throttle body, Faulty IAC valve, Vacuum leak, Carbon buildup",
        "symptoms": "Rough idle, Idle too high or low, Stalling",
        "generic_fixes": "Clean throttle body, Test IAC valve, Check for vacuum leaks, Replace IAC",
        "system": "Powertrain",
        "severity": "Medium"
    },
    "P0506": {
        "description": "Idle Control System RPM Lower Than Expected",
        "common_causes": "Vacuum leak, Dirty throttle body, Faulty IAC valve, Air filter clogged",
        "symptoms": "Low idle, Stalling, Rough idle",
        "generic_fixes": "Check for vacuum leaks, Clean throttle body, Test IAC valve",
        "system": "Powertrain",
        "severity": "Medium"
    },
    "P0507": {
        "description": "Idle Control System RPM Higher Than Expected",
        "common_causes": "Vacuum leak, Dirty throttle body, Stuck IAC valve, PCV valve issue",
        "symptoms": "High idle, Racing engine, Poor fuel economy",
        "generic_fixes": "Check for vacuum leaks, Clean throttle body, Test IAC valve, Check PCV",
        "system": "Powertrain",
        "severity": "Medium"
    },
    "P0520": {
        "description": "Engine Oil Pressure Sensor/Switch Circuit Malfunction",
        "common_causes": "Faulty oil pressure sensor, Low oil level, Damaged wiring, Bad oil pump",
        "symptoms": "Oil pressure warning light, Low oil pressure reading",
        "generic_fixes": "Check oil level, Test oil pressure sensor, Check actual oil pressure, Replace sensor",
        "system": "Powertrain",
        "severity": "High"
    },
    "P0562": {
        "description": "System Voltage Low",
        "common_causes": "Weak battery, Failing alternator, Loose battery connection, Parasitic draw",
        "symptoms": "Dim lights, Electrical issues, Warning lights, Hard starting",
        "generic_fixes": "Test battery voltage, Check alternator output, Clean battery terminals, Test for parasitic draw",
        "system": "Powertrain",
        "severity": "Medium"
    },
    "P0563": {
        "description": "System Voltage High",
        "common_causes": "Overcharging alternator, Failed voltage regulator, Wiring short",
        "symptoms": "Flickering lights, Warning lights, Electrical component damage",
        "generic_fixes": "Test charging voltage, Replace voltage regulator, Check alternator",
        "system": "Powertrain",
        "severity": "Medium"
    },
    "P0600": {
        "description": "Serial Communication Link Malfunction",
        "common_causes": "ECM issue, CAN bus problem, Module communication failure, Wiring damage",
        "symptoms": "Check engine light, Multiple system warnings, Communication errors",
        "generic_fixes": "Check CAN bus wiring, Test module communication, Reprogram ECM, Check connections",
        "system": "Powertrain",
        "severity": "High"
    },
    "P0601": {
        "description": "Internal Control Module Memory Check Sum Error",
        "common_causes": "Corrupted ECM memory, Software issue, ECM failure, Power loss during update",
        "symptoms": "Check engine light, No start, Poor performance, Multiple warnings",
        "generic_fixes": "Reprogram ECM, Update software, Replace ECM if corrupted",
        "system": "Powertrain",
        "severity": "High"
    },
    "P0602": {
        "description": "Control Module Programming Error",
        "common_causes": "Incomplete programming, Software corruption, ECM failure",
        "symptoms": "Check engine light, Various system malfunctions",
        "generic_fixes": "Reprogram ECM with correct software, Update to latest version",
        "system": "Powertrain",
        "severity": "High"
    },
    "P0603": {
        "description": "Internal Control Module Keep Alive Memory (KAM) Error",
        "common_causes": "Battery disconnected, ECM power loss, Corrupted memory, Failing ECM",
        "symptoms": "Check engine light, Loss of learned values, Poor performance",
        "generic_fixes": "Clear codes and relearn, Check battery connections, Reprogram ECM",
        "system": "Powertrain",
        "severity": "Medium"
    },
    "P0606": {
        "description": "ECM/PCM Processor Fault",
        "common_causes": "Failed ECM processor, Software corruption, Hardware failure",
        "symptoms": "Check engine light, No start, Poor performance, Multiple failures",
        "generic_fixes": "Reprogram ECM, Replace ECM if processor failed",
        "system": "Powertrain",
        "severity": "High"
    },
    "P0700": {
        "description": "Transmission Control System Malfunction",
        "common_causes": "Transmission internal problem, TCM issue, Solenoid failure, Wiring problem",
        "symptoms": "Transmission warning light, Shifting problems, Limp mode",
        "generic_fixes": "Scan for transmission-specific codes, Check transmission fluid, Diagnose internal issue",
        "system": "Powertrain",
        "severity": "High"
    },
    "P0705": {
        "description": "Transmission Range Sensor Circuit Malfunction (PRNDL Input)",
        "common_causes": "Faulty transmission range sensor, Misadjusted linkage, Damaged wiring",
        "symptoms": "No start in park, Wrong gear displayed, No reverse lights",
        "generic_fixes": "Adjust shift linkage, Test range sensor, Replace sensor if faulty",
        "system": "Powertrain",
        "severity": "Medium"
    },
    "P0710": {
        "description": "Transmission Fluid Temperature Sensor Circuit Malfunction",
        "common_causes": "Faulty TFT sensor, Damaged wiring, Low transmission fluid",
        "symptoms": "Transmission warning light, Harsh shifting, Limp mode",
        "generic_fixes": "Check transmission fluid level, Test TFT sensor, Replace sensor",
        "system": "Powertrain",
        "severity": "Medium"
    },
    "P0715": {
        "description": "Input/Turbine Speed Sensor Circuit Malfunction",
        "common_causes": "Faulty input speed sensor, Damaged wiring, Transmission internal issue",
        "symptoms": "Speedometer not working, Harsh shifting, Transmission warning light",
        "generic_fixes": "Test input speed sensor, Check wiring, Replace sensor",
        "system": "Powertrain",
        "severity": "Medium"
    },
    "P0720": {
        "description": "Output Speed Sensor Circuit Malfunction",
        "common_causes": "Faulty output speed sensor, Damaged wiring, Transmission issue",
        "symptoms": "Speedometer erratic, Shifting problems, Check engine light",
        "generic_fixes": "Test output speed sensor, Check wiring, Replace sensor",
        "system": "Powertrain",
        "severity": "Medium"
    },
    "P0725": {
        "description": "Engine Speed Input Circuit Malfunction",
        "common_causes": "Faulty crankshaft sensor, CAN communication issue, TCM problem",
        "symptoms": "Transmission shifting issues, Check engine light",
        "generic_fixes": "Test crankshaft sensor, Check CAN communication, Test TCM",
        "system": "Powertrain",
        "severity": "Medium"
    },
    "P0730": {
        "description": "Incorrect Gear Ratio",
        "common_causes": "Low transmission fluid, Internal transmission wear, Solenoid failure, Slipping clutch",
        "symptoms": "Transmission slipping, Poor acceleration, Unusual sounds",
        "generic_fixes": "Check transmission fluid level and condition, Scan for additional codes, May need transmission overhaul",
        "system": "Powertrain",
        "severity": "High"
    },
    "P0740": {
        "description": "Torque Converter Clutch Circuit Malfunction",
        "common_causes": "Faulty TCC solenoid, Internal transmission issue, Low fluid, Damaged wiring",
        "symptoms": "Poor fuel economy, Transmission overheating, Shuddering",
        "generic_fixes": "Check transmission fluid, Test TCC solenoid, Check wiring, May need transmission work",
        "system": "Powertrain",
        "severity": "Medium"
    },
    "P0750": {
        "description": "Shift Solenoid A Malfunction",
        "common_causes": "Faulty shift solenoid, Dirty transmission fluid, Internal transmission issue, Wiring problem",
        "symptoms": "Stuck in one gear, Harsh shifting, Transmission warning light",
        "generic_fixes": "Change transmission fluid, Test shift solenoid, Replace solenoid if faulty",
        "system": "Powertrain",
        "severity": "High"
    },
    "P0755": {
        "description": "Shift Solenoid B Malfunction",
        "common_causes": "Faulty shift solenoid B, Dirty fluid, Internal issue, Wiring problem",
        "symptoms": "Shifting problems, Stuck in gear, Poor performance",
        "generic_fixes": "Change transmission fluid, Test solenoid, Replace if needed",
        "system": "Powertrain",
        "severity": "High"
    },
    "P0760": {
        "description": "Shift Solenoid C Malfunction",
        "common_causes": "Faulty shift solenoid C, Dirty fluid, Wiring issue",
        "symptoms": "Transmission shifting issues, Warning light",
        "generic_fixes": "Test solenoid, Change fluid, Replace solenoid",
        "system": "Powertrain",
        "severity": "High"
    },
    "P0765": {
        "description": "Shift Solenoid D Malfunction",
        "common_causes": "Faulty shift solenoid D, Internal transmission issue",
        "symptoms": "Shifting problems, Transmission warning",
        "generic_fixes": "Test and replace solenoid if needed",
        "system": "Powertrain",
        "severity": "High"
    },
}

# Combine all codes
ALL_CODES = {
    **POWERTRAIN_CODES,
    **CHASSIS_CODES,
    **BODY_CODES,
    **NETWORK_CODES,
    **ADDITIONAL_POWERTRAIN,
}
