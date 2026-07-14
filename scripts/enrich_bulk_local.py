#!/usr/bin/env python3
"""
Bulk Local Enrichment Script

Generates enrichment data locally based on code patterns and descriptions.
No external AI API calls needed - uses rule-based generation from code structure.

Usage:
    python scripts/enrich_bulk_local.py --limit 1000
    python scripts/enrich_bulk_local.py --all
"""

import sys
import json
import time
import re
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase import create_client, Client
from app.core.config import settings


# ============================================================
# KNOWLEDGE BASE - Patterns for generating enrichment data
# ============================================================

SYSTEM_MAP = {
    "P": "Powertrain",
    "B": "Body",
    "C": "Chassis",
    "U": "Network",
}

CIRCUIT_FAULTS = {
    "circuit/open": {"cause": "Open circuit in wiring harness", "symptom": "Component not responding"},
    "circuit low": {"cause": "Short to ground in wiring", "symptom": "Abnormally low voltage readings"},
    "circuit high": {"cause": "Short to power in wiring", "symptom": "Abnormally high voltage readings"},
    "range/performance": {"cause": "Signal out of expected range", "symptom": "Erratic component behavior"},
    "intermittent": {"cause": "Loose or corroded connector", "symptom": "Intermittent warning light"},
}

COMPONENT_PATTERNS = {
    "sensor": {
        "causes": [
            "Faulty {component} sensor",
            "Corroded or damaged sensor connector",
            "Wiring harness damage between sensor and ECM",
            "Poor ground connection at sensor",
        ],
        "symptoms": [
            "Check Engine/Warning Light illuminated",
            "Erratic gauge readings",
            "Poor system performance",
            "Stored diagnostic trouble codes",
        ],
        "checks": [
            "Check sensor connector for corrosion or damage",
            "Measure sensor resistance and compare to specifications",
            "Inspect wiring harness for damage or chafing",
            "Verify proper voltage supply at sensor connector",
        ],
        "tip": "Always check the wiring and connector before replacing the sensor. Many sensor codes are caused by wiring issues, not sensor failure.",
        "repair_time": "1-2 hours",
        "cost_range": "$100-$400 (Parts: $50-$200, Labor: $50-$200)",
        "diy_difficulty": "Moderate",
    },
    "solenoid": {
        "causes": [
            "Failed {component} solenoid",
            "Wiring harness damage to solenoid",
            "Corroded solenoid connector",
            "ECM/PCM driver circuit failure",
        ],
        "symptoms": [
            "Warning light illuminated",
            "System not engaging properly",
            "Unusual noises from affected system",
            "Reduced system performance",
        ],
        "checks": [
            "Measure solenoid resistance (compare to spec)",
            "Check connector pins for corrosion or bent pins",
            "Verify power and ground at solenoid connector",
            "Inspect wiring for damage between ECM and solenoid",
        ],
        "tip": "Test solenoid resistance before replacement. An out-of-spec reading confirms a bad solenoid, while a good reading points to wiring or control module issues.",
        "repair_time": "1-3 hours",
        "cost_range": "$150-$600 (Parts: $75-$300, Labor: $75-$300)",
        "diy_difficulty": "Advanced",
    },
    "module": {
        "causes": [
            "Internal {component} module failure",
            "Power supply issue to the module",
            "Communication bus wiring fault",
            "Software/calibration error in module",
        ],
        "symptoms": [
            "Multiple warning lights on dashboard",
            "System completely inoperative",
            "Communication errors with other modules",
            "Intermittent system malfunctions",
        ],
        "checks": [
            "Verify power and ground supply to the module",
            "Check CAN bus wiring for shorts or opens",
            "Scan for related communication codes in other modules",
            "Check for Technical Service Bulletins (TSBs) related to software updates",
        ],
        "tip": "Module replacements often require programming/coding to the vehicle. Verify the module is truly at fault before ordering - check power, ground, and communication wiring first.",
        "repair_time": "2-4 hours",
        "cost_range": "$300-$1,500 (Parts: $200-$1,000, Labor: $100-$500)",
        "diy_difficulty": "Professional Required",
    },
    "actuator": {
        "causes": [
            "Failed {component} actuator motor",
            "Mechanical binding or obstruction",
            "Wiring fault to actuator",
            "Control module driver circuit failure",
        ],
        "symptoms": [
            "Warning light illuminated",
            "Affected system stuck in one position",
            "Unusual buzzing or clicking noises",
            "System not responding to commands",
        ],
        "checks": [
            "Manually check actuator for mechanical binding",
            "Measure actuator motor resistance",
            "Verify command signal from control module",
            "Inspect connector and wiring for damage",
        ],
        "tip": "Before replacing an actuator, try manually operating it to check for mechanical binding. Also verify the control signal is being sent - the actuator may be fine but not receiving commands.",
        "repair_time": "1-3 hours",
        "cost_range": "$150-$700 (Parts: $100-$400, Labor: $50-$300)",
        "diy_difficulty": "Advanced",
    },
    "switch": {
        "causes": [
            "Faulty {component} switch",
            "Corroded switch connector",
            "Misadjusted switch position",
            "Wiring short between switch and module",
        ],
        "symptoms": [
            "Warning indicator on dashboard",
            "System not activating/deactivating properly",
            "Incorrect system status reported",
            "Intermittent operation",
        ],
        "checks": [
            "Test switch continuity in both positions",
            "Check connector for corrosion or water intrusion",
            "Verify switch adjustment/alignment",
            "Inspect wiring for damage or shorts",
        ],
        "tip": "Switches are often simple to test with a multimeter. Check continuity in both positions before condemning wiring or modules.",
        "repair_time": "30 minutes - 2 hours",
        "cost_range": "$50-$300 (Parts: $20-$150, Labor: $30-$150)",
        "diy_difficulty": "Easy",
    },
    "pump": {
        "causes": [
            "Failed {component} pump motor",
            "Pump relay or fuse failure",
            "Clogged pump inlet/filter",
            "Wiring fault to pump",
        ],
        "symptoms": [
            "System pressure loss or no pressure",
            "Warning light illuminated",
            "Unusual noise from pump area",
            "Reduced system performance",
        ],
        "checks": [
            "Check pump fuse and relay first",
            "Verify power and ground at pump connector",
            "Listen for pump operation when commanded",
            "Check for clogged filter or inlet",
        ],
        "tip": "Always check the fuse and relay before testing the pump itself. A blown fuse often indicates a short or overloaded pump drawing too much current.",
        "repair_time": "1-4 hours",
        "cost_range": "$200-$1,000 (Parts: $100-$700, Labor: $100-$300)",
        "diy_difficulty": "Advanced",
    },
    "valve": {
        "causes": [
            "Stuck or failed {component} valve",
            "Carbon buildup restricting valve movement",
            "Valve solenoid failure",
            "Vacuum line leak (if vacuum-operated)",
        ],
        "symptoms": [
            "Check Engine Light or warning indicator",
            "Poor engine/system performance",
            "Rough idle or stalling",
            "Failed emissions test",
        ],
        "checks": [
            "Inspect valve for carbon buildup or sticking",
            "Test valve operation with manual vacuum or command",
            "Check vacuum lines for leaks (if applicable)",
            "Verify solenoid operation with multimeter",
        ],
        "tip": "Many valve issues are caused by carbon buildup rather than actual valve failure. Try cleaning the valve and passages before replacing.",
        "repair_time": "1-3 hours",
        "cost_range": "$100-$500 (Parts: $50-$300, Labor: $50-$200)",
        "diy_difficulty": "Moderate",
    },
    "motor": {
        "causes": [
            "Failed {component} motor",
            "Motor brushes worn",
            "Power supply issue to motor",
            "Mechanical binding preventing motor operation",
        ],
        "symptoms": [
            "Component not operating",
            "Slow or intermittent operation",
            "Unusual grinding or whining noise",
            "Warning light on dashboard",
        ],
        "checks": [
            "Verify power and ground at motor connector",
            "Check motor for free rotation (no mechanical bind)",
            "Test motor current draw (compare to spec)",
            "Inspect brushes if accessible",
        ],
        "tip": "Check for mechanical binding before condemning the motor. A motor that draws excessive current may be mechanically stuck rather than electrically failed.",
        "repair_time": "1-3 hours",
        "cost_range": "$150-$600 (Parts: $75-$350, Labor: $75-$250)",
        "diy_difficulty": "Moderate",
    },
    "circuit": {
        "causes": [
            "Open or short in {component} wiring",
            "Corroded connector pins",
            "Damaged wiring harness (chafing, rodent damage)",
            "Failed component creating circuit fault",
        ],
        "symptoms": [
            "Warning light illuminated",
            "Affected system inoperative or intermittent",
            "Blown fuse (if short circuit)",
            "Erratic component behavior",
        ],
        "checks": [
            "Inspect all connectors in the circuit for corrosion",
            "Check wiring harness for visible damage",
            "Measure circuit resistance end-to-end",
            "Verify power and ground at the component",
        ],
        "tip": "For circuit faults, a wiring diagram is essential. Trace the circuit from the component back to the control module, checking each connector along the way.",
        "repair_time": "1-3 hours",
        "cost_range": "$100-$500 (Parts: $20-$100, Labor: $80-$400)",
        "diy_difficulty": "Advanced",
    },
}

DEFAULT_PATTERN = {
    "causes": [
        "Component failure",
        "Wiring or connector issue",
        "Control module fault",
        "Poor electrical connection",
    ],
    "symptoms": [
        "Warning light illuminated on dashboard",
        "Affected system not functioning properly",
        "Reduced vehicle performance",
        "Intermittent system operation",
    ],
    "checks": [
        "Check all related connectors for corrosion or damage",
        "Inspect wiring harness for visible damage",
        "Verify power and ground at the component",
        "Scan for related codes in other modules",
    ],
    "tip": "Start diagnosis by checking the simplest items first - fuses, connectors, and wiring - before condemning expensive components.",
    "repair_time": "1-3 hours",
    "cost_range": "$100-$800 (varies by component)",
    "diy_difficulty": "Moderate",
}

SEVERITY_EXPLANATIONS = {
    "High": "This code indicates a significant issue that can compromise vehicle safety, driveability, or cause progressive damage to other components if not addressed promptly. Continued driving is not recommended without diagnosis.",
    "Medium": "This code indicates a moderate issue that may affect vehicle performance or emissions. While the vehicle may still be drivable, the issue should be diagnosed and repaired soon to prevent further damage or component failure.",
    "Low": "This code indicates a minor issue that typically does not affect immediate driveability or safety. However, it should still be addressed to prevent potential problems and ensure all vehicle systems operate correctly.",
}

EMISSIONS_BY_SYSTEM = {
    "Powertrain": "May Fail",
    "Body": "No Impact",
    "Chassis": "No Impact",
    "Network": "No Impact",
}

DIY_BY_SYSTEM = {
    "Body": "Moderate",
    "Chassis": "Advanced",
    "Powertrain": "Moderate",
    "Network": "Professional Required",
}


def detect_component_type(description: str) -> str:
    """Detect the component type from the description."""
    desc_lower = description.lower()
    for component_type in ["sensor", "solenoid", "module", "actuator", "switch", "pump", "valve", "motor"]:
        if component_type in desc_lower:
            return component_type
    if "circuit" in desc_lower or "open" in desc_lower or "short" in desc_lower:
        return "circuit"
    return "default"


def extract_component_name(description: str) -> str:
    """Extract a clean component name from the description."""
    # Remove common suffixes
    name = description
    for suffix in [" Circuit/Open", " Circuit Low", " Circuit High", " Circuit",
                   " Range/Performance", " Malfunction", " Performance",
                   " Control", " Signal", " Input", " Output"]:
        name = name.replace(suffix, "")
    return name.strip()


def get_related_codes(code: str) -> list:
    """Generate related codes based on the code pattern."""
    prefix = code[0]
    number = code[1:]

    related = []
    try:
        num = int(number)
        # Add adjacent codes
        if num > 0:
            related.append(f"{prefix}{num-1:04d}")
        related.append(f"{prefix}{num+1:04d}")
        if num > 1:
            related.append(f"{prefix}{num-2:04d}")
        related.append(f"{prefix}{num+2:04d}")
    except ValueError:
        # Hex codes (like B3A1E)
        pass

    return related[:4]


def generate_enrichment(code: str, description: str, system: str, severity: str) -> dict:
    """Generate enrichment data for a single code."""
    component_type = detect_component_type(description)
    component_name = extract_component_name(description)
    system_name = system or SYSTEM_MAP.get(code[0], "Unknown")

    # Get pattern data
    if component_type == "default":
        pattern = DEFAULT_PATTERN
    else:
        pattern = COMPONENT_PATTERNS.get(component_type, DEFAULT_PATTERN)

    # Generate causes with component name substituted
    causes = [c.format(component=component_name) for c in pattern["causes"]]

    # Determine circuit fault type for additional specificity
    desc_lower = description.lower()
    circuit_extra = None
    for fault_key, fault_data in CIRCUIT_FAULTS.items():
        if fault_key in desc_lower:
            circuit_extra = fault_data
            break

    if circuit_extra and circuit_extra["cause"] not in causes:
        causes.insert(0, circuit_extra["cause"])
        causes = causes[:5]

    # Generate symptoms
    symptoms = list(pattern["symptoms"])
    if circuit_extra:
        symptoms.insert(1, circuit_extra["symptom"])
        symptoms = symptoms[:5]

    # Severity explanation
    severity_key = severity if severity in SEVERITY_EXPLANATIONS else "Medium"
    severity_explanation = SEVERITY_EXPLANATIONS[severity_key]

    # Emissions impact
    emissions = EMISSIONS_BY_SYSTEM.get(system_name, "No Impact")
    if code[0] == "P" and any(x in desc_lower for x in ["catalyst", "oxygen", "o2", "emission", "evap", "egr"]):
        emissions = "Will Fail"
    elif code[0] == "P":
        emissions = "May Fail"

    # DIY difficulty
    diy = pattern.get("diy_difficulty", DIY_BY_SYSTEM.get(system_name, "Moderate"))

    # Cost and time
    repair_time = pattern.get("repair_time", "1-3 hours")
    cost_range = pattern.get("cost_range", "$100-$800 (varies by component)")

    # Related codes
    related = get_related_codes(code)

    # Cause likelihoods
    cause_likelihoods = []
    percentages = [45, 25, 20, 10] if len(causes) == 4 else [40, 25, 20, 10, 5]
    for i, cause in enumerate(causes[:len(percentages)]):
        cause_likelihoods.append({"cause": cause, "likelihood": percentages[i]})

    # Common misdiagnoses
    misdiagnoses = (
        f"Do not replace the {component_name.lower()} without first verifying the wiring and connectors. "
        f"Many {component_type} codes are caused by wiring faults, corroded connectors, or poor grounds "
        f"rather than actual component failure. Always check Technical Service Bulletins (TSBs) for known issues "
        f"related to this code before beginning expensive repairs."
    )

    # Freeze frame data
    freeze_frame = [
        "Engine RPM at time of fault",
        "Vehicle speed at time of fault",
        "Engine coolant temperature",
        "Battery voltage",
        "Engine load percentage",
    ]

    # Technician tip
    tip = pattern.get("tip", DEFAULT_PATTERN["tip"])

    # Pre-replacement checks
    checks = pattern.get("checks", DEFAULT_PATTERN["checks"])

    return {
        "symptoms": symptoms,
        "common_causes": causes,
        "severity_explanation": severity_explanation,
        "technician_tip": tip,
        "pre_replacement_checks": checks,
        "typical_repair_time": repair_time,
        "typical_cost_range": cost_range,
        "diy_difficulty": diy,
        "related_codes": related,
        "common_misdiagnoses": misdiagnoses,
        "freeze_frame_data_to_check": freeze_frame,
        "cause_likelihoods": json.dumps(cause_likelihoods),
        "emissions_impact": emissions,
        "enrichment_status": "ai_enriched",
        "last_enriched": datetime.now().isoformat(),
        "knowledge_score": 70.0,
    }


def main():
    parser = argparse.ArgumentParser(description="Bulk Local Enrichment (no API calls)")
    parser.add_argument("--limit", type=int, help="Limit number of codes")
    parser.add_argument("--all", action="store_true", help="Process all unenriched codes")
    parser.add_argument("--dry-run", action="store_true", help="Don't write to database")
    parser.add_argument("--batch-size", type=int, default=50, help="DB update batch size")
    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("BULK LOCAL ENRICHMENT (No API calls)")
    print("=" * 70)

    if not settings.supabase_enabled:
        print("[ERROR] Supabase not enabled")
        return 1

    client = create_client(settings.supabase_url, settings.supabase_service_key)
    print("[OK] Supabase connected")

    # Fetch codes needing enrichment
    print("\n[*] Fetching codes needing enrichment...")
    limit = None if args.all else (args.limit or 100)

    all_codes = []
    offset = 0
    page_size = 1000

    while True:
        query = client.table("obd_codes").select(
            "code, description, system, severity, knowledge_score"
        ).lt("knowledge_score", 80.0).order("code").range(offset, offset + page_size - 1)

        result = query.execute()
        if not result.data:
            break

        all_codes.extend(result.data)
        offset += page_size

        if limit and len(all_codes) >= limit:
            all_codes = all_codes[:limit]
            break

        if len(result.data) < page_size:
            break

        print(f"  Fetched {len(all_codes)} codes so far...")

    total = len(all_codes)
    print(f"[OK] Found {total} codes to enrich")

    if total == 0:
        print("\n[OK] All codes are already enriched!")
        return 0

    # Process codes
    print(f"\n[*] Generating enrichment data for {total} codes...")
    print(f"    Batch size: {args.batch_size}")
    print(f"    Dry-run: {args.dry_run}")
    print()

    start_time = time.time()
    enriched = 0
    failed = 0

    for i in range(0, total, args.batch_size):
        batch = all_codes[i:i + args.batch_size]
        batch_num = i // args.batch_size + 1
        total_batches = (total + args.batch_size - 1) // args.batch_size

        updates = []
        for code_record in batch:
            code = code_record["code"]
            description = code_record.get("description", "")
            system = code_record.get("system", "")
            severity = code_record.get("severity", "Medium")

            enrichment = generate_enrichment(code, description, system, severity)
            updates.append({"code": code, "data": enrichment})

        if args.dry_run:
            enriched += len(updates)
            elapsed = time.time() - start_time
            rate = enriched / elapsed if elapsed > 0 else 0
            print(f"  [Batch {batch_num}/{total_batches}] DRY-RUN: Would update {len(updates)} codes "
                  f"({enriched}/{total}, {rate:.0f}/s)")
            continue

        # Update database one by one (Supabase doesn't support bulk update easily)
        for update in updates:
            try:
                client.table("obd_codes").update(update["data"]).eq("code", update["code"]).execute()
                enriched += 1
            except Exception as e:
                failed += 1
                if "timeout" in str(e).lower() or "disconnect" in str(e).lower():
                    print(f"  [WARN] Connection issue at {update['code']}, retrying...")
                    time.sleep(2)
                    try:
                        client.table("obd_codes").update(update["data"]).eq("code", update["code"]).execute()
                        enriched += 1
                        failed -= 1
                    except Exception:
                        print(f"  [FAIL] {update['code']}: {str(e)[:60]}")

        elapsed = time.time() - start_time
        rate = enriched / elapsed if elapsed > 0 else 0
        eta = (total - enriched) / rate if rate > 0 else 0
        print(f"  [Batch {batch_num}/{total_batches}] Enriched {enriched}/{total} "
              f"(rate: {rate:.1f}/s, ETA: {eta/60:.1f}min, failed: {failed})")

    # Final stats
    elapsed = time.time() - start_time
    print("\n" + "=" * 70)
    print("ENRICHMENT COMPLETE")
    print("=" * 70)
    print(f"Total processed: {enriched + failed}")
    print(f"Enriched:        {enriched}")
    print(f"Failed:          {failed}")
    print(f"Duration:        {elapsed:.0f}s ({elapsed/60:.1f} min)")
    if enriched > 0:
        print(f"Rate:            {enriched/elapsed:.1f} codes/s")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
