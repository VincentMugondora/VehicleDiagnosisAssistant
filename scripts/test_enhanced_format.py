#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Enhanced OBD Code Response Format (Migration 003)

This script tests the new response format with all Migration 003 fields.
"""

import sys
import codecs
from pathlib import Path

# Force UTF-8 encoding for output
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'replace')

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.diagnostic import DiagnosticResult
from app.services.diagnostic_formatter import format_diagnostic_report


def test_basic_format():
    """Test basic format (without Migration 003 fields)"""
    print("\n" + "="*70)
    print("TEST 1: BASIC FORMAT (Pre-Migration 003)")
    print("="*70 + "\n")

    result = DiagnosticResult(
        code="P0420",
        description="Catalyst System Efficiency Below Threshold (Bank 1)",
        causes=[
            "Worn catalytic converter",
            "Faulty downstream O2 sensor",
            "Engine running rich or lean"
        ],
        checks=[
            "Check for other codes first",
            "Inspect oxygen sensor readings",
            "Check fuel trim values"
        ],
        confidence=0.85,
        source="local_db",
        system="Emissions",
        symptoms=[
            "Check Engine Light on",
            "Decreased fuel economy",
            "Rotten egg smell from exhaust"
        ],
        severity="Moderate",
        severity_explanation="Can drive for now, but address soon",
        technician_tip="Always test the rear O2 sensor first!",
        pre_replacement_checks=[
            "Verify downstream O2 sensor is responding",
            "Check fuel trims are within spec"
        ]
    )

    formatted = format_diagnostic_report(result)
    print(formatted)


def test_enhanced_format():
    """Test enhanced format (with Migration 003 fields)"""
    print("\n\n" + "="*70)
    print("TEST 2: ENHANCED FORMAT (With Migration 003 Fields)")
    print("="*70 + "\n")

    result = DiagnosticResult(
        code="P0420",
        description="Catalyst System Efficiency Below Threshold (Bank 1)",
        causes=[
            "Worn catalytic converter",
            "Faulty downstream O2 sensor",
            "Engine running rich or lean",
            "Exhaust leak before catalytic converter"
        ],
        checks=[
            "Check for other codes first (P0171, P0174, P0300)",
            "View live O2 sensor data (before & after cat)",
            "Check fuel trim values (should be +/- 10%)",
            "Inspect exhaust for leaks upstream",
            "Test catalytic converter with infrared temp gun"
        ],
        confidence=0.90,
        source="ai_enriched",
        system="Emissions",
        symptoms=[
            "Check Engine Light illuminated",
            "Decreased fuel economy (2-4 MPG drop)",
            "Slight loss of power under acceleration",
            "Rotten egg smell from exhaust",
            "Failed emissions test"
        ],
        severity="Moderate",
        severity_explanation="Can drive for now, but address soon to prevent reduced fuel economy and failed emissions inspection.",
        technician_tip="80% of P0420 codes are misdiagnosed. Always test the rear O2 sensor first - it's cheaper ($200) and more likely faulty than the catalytic converter itself ($1,500).",
        pre_replacement_checks=[
            "Confirm no other codes present",
            "Verify downstream O2 sensor is responding",
            "Check fuel trims are within spec (-10% to +10%)",
            "Rule out exhaust leaks upstream of catalytic converter",
            "Confirm cat temperature rise (200F+ inlet to outlet)"
        ],
        # Migration 003 NEW fields
        typical_repair_time="1-3 hours",
        typical_cost_range="$200-$2,500 (O2 sensor: $200-$400, Catalytic converter: $1,000-$2,500)",
        diy_difficulty="Moderate",
        related_codes=["P0430", "P0300", "P0171", "P0174"],
        common_misdiagnoses="Do not immediately replace the catalytic converter! Test the downstream O2 sensor and check for engine problems (lean/rich conditions) first. Many mechanics replace $1,500 cats when a $200 sensor was the real issue.",
        freeze_frame_data_to_check=[
            "Short Term Fuel Trim (STFT): should be -10% to +10%",
            "Long Term Fuel Trim (LTFT): should be -10% to +10%",
            "O2 Sensor Voltage: Front should toggle 0.1-0.9V, Rear should be stable ~0.45V",
            "Catalyst Temperature: Outlet should be 200F+ hotter than inlet"
        ],
        cause_likelihoods='[{"cause": "Worn catalytic converter", "likelihood": 60}, {"cause": "Faulty downstream O2 sensor", "likelihood": 25}, {"cause": "Engine running rich or lean", "likelihood": 10}, {"cause": "Exhaust leak before catalytic converter", "likelihood": 5}]',
        emissions_impact="Will Fail"
    )

    formatted = format_diagnostic_report(result)
    print(formatted)


def main():
    print("\n" + "="*70)
    print("ENHANCED OBD CODE RESPONSE FORMAT TEST")
    print("Testing Migration 003 Improvements")
    print("="*70)

    # Test basic format
    test_basic_format()

    # Test enhanced format
    test_enhanced_format()

    print("\n\n" + "="*70)
    print("COMPARISON SUMMARY")
    print("="*70)
    print("\nBasic Format Sections:")
    print("  1. Header")
    print("  2. Description")
    print("  3. Symptoms")
    print("  4. Causes")
    print("  5. Diagnostic Steps")
    print("  6. Severity")
    print("  7. Pre-replacement Checks")
    print("  8. Technician Tip")
    print("  9. Footer")
    print("\nEnhanced Format Adds:")
    print("  10. Cost & Time Information (NEW)")
    print("  11. Related Codes (NEW)")
    print("  12. Common Misdiagnosis Warning (NEW)")
    print("  13. Freeze Frame Data Guidance (NEW)")
    print("  14. Likelihood Percentages in Causes (NEW)")
    print("\n" + "="*70)


if __name__ == "__main__":
    main()
