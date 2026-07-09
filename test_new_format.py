"""
Test script to verify the new diagnostic report format.
"""

import sys
import io

# Fix Windows console encoding issues with emojis
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from app.models.diagnostic import DiagnosticResult
from app.services.diagnostic_formatter import format_diagnostic_report


def test_format_with_symptoms():
    """Test format with symptoms from database"""
    result = DiagnosticResult(
        code="P0420",
        description="Catalyst System Efficiency Below Threshold (Bank 1)",
        causes=[
            "Degraded catalytic converter",
            "Exhaust leak before catalytic converter",
            "Faulty oxygen sensors",
            "Engine running rich or lean",
            "Oil contamination in exhaust"
        ],
        checks=[
            "Check O2 sensor readings with scanner",
            "Inspect for exhaust leaks upstream of catalytic converter",
            "Test catalytic converter efficiency",
            "Check for engine misfires or running issues",
            "Clear code and road test"
        ],
        confidence=0.85,
        source="local_db",
        system="Emissions",
        symptoms=[
            "Check Engine Light illuminated",
            "Reduced engine performance",
            "Rattling noise from exhaust",
            "Sulfur smell from exhaust"
        ]
    )

    report = format_diagnostic_report(result)
    print("=" * 80)
    print("TEST 1: P0420 with symptoms from database")
    print("=" * 80)
    print(report)
    print("\n\n")


def test_format_without_symptoms():
    """Test format without symptoms (should generate them)"""
    result = DiagnosticResult(
        code="P0332",
        description="Knock Sensor 2 Circuit Low Input (Bank 2)",
        causes=[
            "Faulty knock sensor",
            "Damaged or corroded wiring",
            "Loose or improperly torqued sensor",
            "Short to ground in sensor circuit",
            "Faulty ECM"
        ],
        checks=[
            "Inspect knock sensor connector and wiring",
            "Test sensor resistance with multimeter",
            "Verify sensor mounting torque",
            "Check for shorts to ground",
            "View live scanner data"
        ],
        confidence=0.85,
        source="local_db",
        system="Powertrain",
        symptoms=None  # No symptoms - should generate
    )

    report = format_diagnostic_report(result)
    print("=" * 80)
    print("TEST 2: P0332 without symptoms (should generate)")
    print("=" * 80)
    print(report)
    print("\n\n")


def test_ai_generated_code():
    """Test format with AI-generated code"""
    result = DiagnosticResult(
        code="P3499",
        description="Cylinder Deactivation System Bank 2",
        causes=[
            "Faulty cylinder deactivation solenoid",
            "Low oil pressure",
            "Clogged oil passages",
            "Worn lifters or rocker arms",
            "ECM software issue"
        ],
        checks=[
            "Check engine oil level and pressure",
            "Inspect cylinder deactivation solenoid operation",
            "Test solenoid with scanner active tests",
            "Check for oil passage blockages",
            "Update ECM software if available"
        ],
        confidence=0.75,
        source="ai_learned",
        system="Powertrain",
        symptoms=[
            "Check Engine Light on",
            "Rough idle",
            "Reduced fuel economy",
            "Engine vibration"
        ]
    )

    report = format_diagnostic_report(result)
    print("=" * 80)
    print("TEST 3: P3499 (AI-generated)")
    print("=" * 80)
    print(report)
    print("\n\n")


def test_unknown_code():
    """Test format with unknown code"""
    result = DiagnosticResult(
        code="P9999",
        description="Code P9999 is not in our database yet.",
        causes=[
            "This code may be vehicle-specific",
            "Check your vehicle's service manual for details"
        ],
        checks=[
            "Search online: 'P9999 [your vehicle make/model]'",
            "Visit a qualified mechanic for professional diagnosis",
            "Clear code and monitor if problem recurs"
        ],
        confidence=0.10,
        source="unknown",
        system=None,
        symptoms=None
    )

    report = format_diagnostic_report(result)
    print("=" * 80)
    print("TEST 4: P9999 (unknown code)")
    print("=" * 80)
    print(report)
    print("\n\n")


def test_transmission_code():
    """Test format with transmission code"""
    result = DiagnosticResult(
        code="P0700",
        description="Transmission Control System Malfunction",
        causes=[
            "TCM fault codes present",
            "Transmission wiring issues",
            "Faulty transmission solenoid",
            "Low transmission fluid",
            "TCM software issue"
        ],
        checks=[
            "Scan for transmission-specific codes",
            "Check transmission fluid level and condition",
            "Inspect transmission wiring and connectors",
            "Test shift solenoids",
            "Check TCM power and ground"
        ],
        confidence=0.85,
        source="local_db",
        system="Transmission",
        symptoms=[
            "Check Engine Light on",
            "Harsh shifting",
            "Delayed engagement",
            "Slipping transmission",
            "Vehicle may enter limp mode"
        ]
    )

    report = format_diagnostic_report(result)
    print("=" * 80)
    print("TEST 5: P0700 (transmission code)")
    print("=" * 80)
    print(report)
    print("\n\n")


if __name__ == "__main__":
    print("\n")
    print("=" * 80)
    print("DIAGNOSTIC REPORT FORMAT TEST SUITE")
    print("=" * 80)
    print("\n")

    test_format_with_symptoms()
    test_format_without_symptoms()
    test_ai_generated_code()
    test_unknown_code()
    test_transmission_code()

    print("=" * 80)
    print("ALL TESTS COMPLETED")
    print("=" * 80)
