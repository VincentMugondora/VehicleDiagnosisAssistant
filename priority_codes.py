"""
Priority DTC List

Curated list of most common/important OBD-II codes to enrich first.
Based on diagnostic frequency data and real-world usage patterns.
"""

# Tier 1: Top 50 Most Common Codes (90% of diagnostic requests)
TIER_1_PRIORITY = [
    # Misfires (extremely common)
    "P0300",  # Random/Multiple Misfire
    "P0301",  # Cylinder 1 Misfire
    "P0302",  # Cylinder 2 Misfire
    "P0303",  # Cylinder 3 Misfire
    "P0304",  # Cylinder 4 Misfire
    "P0305",  # Cylinder 5 Misfire
    "P0306",  # Cylinder 6 Misfire

    # Catalyst (very common emissions failure)
    "P0420",  # Catalyst Efficiency Bank 1
    "P0430",  # Catalyst Efficiency Bank 2

    # Fuel trim (common lean/rich conditions)
    "P0171",  # System Too Lean Bank 1
    "P0172",  # System Too Rich Bank 1
    "P0174",  # System Too Lean Bank 2
    "P0175",  # System Too Rich Bank 2

    # EVAP (most common codes after catalyst)
    "P0440",  # EVAP System
    "P0442",  # EVAP Small Leak
    "P0443",  # EVAP Purge Control Valve
    "P0446",  # EVAP Vent Control
    "P0450",  # EVAP Pressure Sensor
    "P0455",  # EVAP Large Leak
    "P0456",  # EVAP Very Small Leak
    "P0457",  # EVAP Leak Detected

    # O2 Sensors (very common)
    "P0130",  # O2 Sensor Circuit Bank 1 Sensor 1
    "P0131",  # O2 Sensor Low Voltage Bank 1 Sensor 1
    "P0132",  # O2 Sensor High Voltage Bank 1 Sensor 1
    "P0133",  # O2 Sensor Slow Response Bank 1 Sensor 1
    "P0134",  # O2 Sensor No Activity Bank 1 Sensor 1
    "P0135",  # O2 Sensor Heater Bank 1 Sensor 1
    "P0136",  # O2 Sensor Circuit Bank 1 Sensor 2
    "P0137",  # O2 Sensor Low Voltage Bank 1 Sensor 2
    "P0138",  # O2 Sensor High Voltage Bank 1 Sensor 2

    # MAF/MAP Sensors (common airflow issues)
    "P0100",  # MAF Circuit
    "P0101",  # MAF Range/Performance
    "P0102",  # MAF Low Input
    "P0103",  # MAF High Input
    "P0106",  # MAP Range/Performance
    "P0107",  # MAP Low Input
    "P0108",  # MAP High Input

    # Coolant/Thermostat (common)
    "P0125",  # Insufficient Coolant Temperature
    "P0128",  # Coolant Thermostat

    # EGR (common emissions)
    "P0400",  # EGR Flow
    "P0401",  # EGR Insufficient Flow
    "P0402",  # EGR Excessive Flow

    # Idle Control (common)
    "P0505",  # Idle Control System
    "P0506",  # Idle RPM Lower Than Expected
    "P0507",  # Idle RPM Higher Than Expected

    # VVT/Cam Timing (increasingly common)
    "P0010",  # VVT Control Circuit Bank 1
    "P0011",  # VVT Timing Over-Advanced Bank 1
    "P0012",  # VVT Timing Over-Retarded Bank 1
]

# Tier 2: Common Codes (next 100 codes, ~8% of requests)
TIER_2_PRIORITY = [
    # Additional Misfires
    "P0307", "P0308",

    # Additional O2 Sensors
    "P0140", "P0141", "P0150", "P0151", "P0152", "P0153", "P0154", "P0155",
    "P0156", "P0157", "P0158", "P0159", "P0160", "P0161",

    # Crankshaft/Camshaft Position
    "P0335",  # Crankshaft Position Sensor
    "P0336",  # Crankshaft Position Range/Performance
    "P0340",  # Camshaft Position Sensor
    "P0341",  # Camshaft Position Range/Performance
    "P0344",  # Camshaft Position Intermittent

    # Throttle Position
    "P0120",  # TPS Circuit
    "P0121",  # TPS Range/Performance
    "P0122",  # TPS Low Input
    "P0123",  # TPS High Input

    # Coolant Temperature
    "P0115",  # ECT Sensor Circuit
    "P0116",  # ECT Range/Performance
    "P0117",  # ECT Low Input
    "P0118",  # ECT High Input

    # Intake Air Temperature
    "P0110",  # IAT Sensor Circuit
    "P0111",  # IAT Range/Performance
    "P0112",  # IAT Low Input
    "P0113",  # IAT High Input

    # Additional VVT
    "P0013", "P0014", "P0015", "P0016", "P0017", "P0018", "P0019",
    "P0020", "P0021", "P0022", "P0023", "P0024",

    # Fuel System
    "P0030",  # O2 Heater Bank 1 Sensor 1
    "P0031",  # O2 Heater Low Bank 1 Sensor 1
    "P0032",  # O2 Heater High Bank 1 Sensor 1
    "P0036",  # O2 Heater Bank 1 Sensor 2
    "P0037",  # O2 Heater Low Bank 1 Sensor 2
    "P0038",  # O2 Heater High Bank 1 Sensor 2

    # Knock Sensor
    "P0325",  # Knock Sensor 1 Bank 1
    "P0326",  # Knock Sensor 1 Range/Performance
    "P0327",  # Knock Sensor 1 Low Input
    "P0328",  # Knock Sensor 1 High Input
    "P0330",  # Knock Sensor 2 Bank 2

    # Vehicle Speed
    "P0500",  # Vehicle Speed Sensor
    "P0501",  # Vehicle Speed Sensor Range/Performance

    # Transmission
    "P0700",  # Transmission Control System
    "P0705",  # Transmission Range Sensor
    "P0715",  # Input/Turbine Speed Sensor
    "P0720",  # Output Speed Sensor

    # Additional EVAP
    "P0441",  # EVAP Incorrect Purge Flow
    "P0451",  # EVAP Pressure Sensor Range
    "P0452",  # EVAP Pressure Sensor Low
    "P0453",  # EVAP Pressure Sensor High
    "P0454",  # EVAP Pressure Sensor Intermittent

    # Secondary Air
    "P0410",  # Secondary Air System
    "P0411",  # Secondary Air Incorrect Flow

    # Random Common Codes
    "P0200",  # Injector Circuit
    "P0201",  # Injector 1 Circuit
    "P0202",  # Injector 2 Circuit
    "P0203",  # Injector 3 Circuit
    "P0204",  # Injector 4 Circuit

    "P0405",  # EGR Sensor Low
    "P0406",  # EGR Sensor High

    "P0460",  # Fuel Level Sensor
    "P0461",  # Fuel Level Sensor Range
]

# Tier 3: Less Common But Important (manufacturer-specific or rare)
TIER_3_PRIORITY = [
    # Additional Bank 2 codes
    "P0150", "P0151", "P0152", "P0153", "P0154", "P0155",
    "P0156", "P0157", "P0158", "P0159", "P0160", "P0161",

    # More advanced powertrain
    "P0219",  # Engine Overspeed
    "P0230",  # Fuel Pump Primary Circuit
    "P0231",  # Fuel Pump Low
    "P0232",  # Fuel Pump High

    # Turbo/Boost
    "P0234",  # Turbo Overboost
    "P0235",  # Turbo Boost Sensor
    "P0236",  # Turbo Boost Range/Performance
    "P0237",  # Turbo Boost Low
    "P0238",  # Turbo Boost High

    # Advanced emissions
    "P0420", "P0421", "P0422", "P0423", "P0424",
    "P0430", "P0431", "P0432", "P0433", "P0434",
]


def get_priority_tier(code: str) -> int:
    """
    Get priority tier for a code.

    Returns:
        1: Tier 1 (highest priority)
        2: Tier 2 (medium priority)
        3: Tier 3 (lower priority)
        0: Not in priority list
    """
    code_upper = code.upper()
    if code_upper in TIER_1_PRIORITY:
        return 1
    elif code_upper in TIER_2_PRIORITY:
        return 2
    elif code_upper in TIER_3_PRIORITY:
        return 3
    return 0


def get_priority_batch(batch_size: int = 50, tier: int = 1) -> list[str]:
    """
    Get next batch of codes to enrich.

    Args:
        batch_size: Number of codes to return
        tier: Priority tier (1, 2, or 3)

    Returns:
        List of codes
    """
    if tier == 1:
        return TIER_1_PRIORITY[:batch_size]
    elif tier == 2:
        return TIER_2_PRIORITY[:batch_size]
    elif tier == 3:
        return TIER_3_PRIORITY[:batch_size]
    return []


def get_all_priority_codes() -> list[str]:
    """Get all priority codes across all tiers."""
    return TIER_1_PRIORITY + TIER_2_PRIORITY + TIER_3_PRIORITY


if __name__ == "__main__":
    print("=" * 80)
    print("PRIORITY CODE STATISTICS")
    print("=" * 80)
    print()
    print(f"Tier 1 (Highest Priority): {len(TIER_1_PRIORITY)} codes")
    print(f"Tier 2 (Medium Priority):  {len(TIER_2_PRIORITY)} codes")
    print(f"Tier 3 (Lower Priority):   {len(TIER_3_PRIORITY)} codes")
    print(f"Total Priority Codes:      {len(get_all_priority_codes())} codes")
    print()
    print("NOTE: Coverage estimates (90-98% of requests) are planning assumptions")
    print("based on industry diagnostic patterns, NOT measured usage data.")
    print("Actual coverage TBD after deployment analytics.")
    print()
    print("Tier 1 Sample (first 10):")
    for code in TIER_1_PRIORITY[:10]:
        print(f"  {code}")
    print()
