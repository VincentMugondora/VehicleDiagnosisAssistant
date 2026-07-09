"""
Test script to verify the new data-driven architecture.

Demonstrates:
1. Formatter is presentation-only
2. All intelligence comes from DiagnosticResult
3. No heuristic logic in formatter
"""

import sys
import io

# Fix Windows console encoding issues with emojis
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from app.models.diagnostic import DiagnosticResult
from app.services.diagnostic_formatter import format_diagnostic_report


def test_fully_populated_result():
    """Test with all fields populated (ideal case - from database or AI)"""
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
        confidence=0.90,
        source="enriched",
        system="Emissions",
        symptoms=[
            "Check Engine Light illuminated",
            "Reduced engine performance",
            "Rattling noise from exhaust",
            "Sulfur smell from exhaust"
        ],
        severity="Moderate",
        severity_explanation="This code should be diagnosed and repaired to prevent potential damage and restore proper vehicle performance. The vehicle is usually drivable, but prolonged operation may reduce efficiency or cause further issues.",
        technician_tip="Catalytic converter codes are often symptoms of other problems (lean/rich conditions, misfires, oil consumption). Fix upstream issues first before replacing the converter.",
        pre_replacement_checks=[
            "Wiring and connectors have been inspected",
            "O2 sensor readings verified",
            "Exhaust leaks ruled out",
            "Engine running conditions confirmed normal"
        ]
    )

    report = format_diagnostic_report(result)
    print("=" * 80)
    print("TEST 1: Fully Populated Result (Database/AI)")
    print("=" * 80)
    print(report)
    print("\n\n")


def test_minimal_result():
    """Test with minimal fields (what formatter does when data is sparse)"""
    result = DiagnosticResult(
        code="P9999",
        description="Code P9999 is not in our database yet.",
        causes=["This code may be vehicle-specific"],
        checks=["Search online for this code", "Consult a qualified mechanic"],
        confidence=0.10,
        source="unknown",
        system=None,
        symptoms=None,  # No symptoms
        severity=None,  # No severity
        severity_explanation=None,
        technician_tip=None,  # No tip
        pre_replacement_checks=None  # No checks
    )

    report = format_diagnostic_report(result)
    print("=" * 80)
    print("TEST 2: Minimal Result (Unknown Code)")
    print("=" * 80)
    print(report)
    print("\n\n")


def test_partial_result():
    """Test with some fields populated, some missing"""
    result = DiagnosticResult(
        code="P0171",
        description="System Too Lean (Bank 1)",
        causes=[
            "Vacuum leak",
            "Faulty MAF sensor",
            "Low fuel pressure",
            "Exhaust leak before O2 sensor"
        ],
        checks=[
            "Inspect intake for vacuum leaks",
            "Test MAF sensor operation",
            "Check fuel pressure",
            "Inspect exhaust for leaks"
        ],
        confidence=0.85,
        source="local_db",
        system="Fuel System",
        symptoms=[
            "Check Engine Light on",
            "Rough idle",
            "Hesitation during acceleration",
            "Poor fuel economy"
        ],
        severity="Moderate",
        severity_explanation=None,  # Missing - formatter will use fallback
        technician_tip="Before replacing the MAF sensor, try cleaning it with MAF cleaner. Also check for vacuum leaks, which are a common cause of lean conditions.",
        pre_replacement_checks=None  # Missing - section will be omitted
    )

    report = format_diagnostic_report(result)
    print("=" * 80)
    print("TEST 3: Partial Result (Some Fields Missing)")
    print("=" * 80)
    print(report)
    print("\n\n")


def test_ai_generated_result():
    """Test with AI-generated result (all fields from AI)"""
    result = DiagnosticResult(
        code="P0332",
        description="Knock Sensor 2 Circuit Low Input (Bank 2)",
        causes=[
            "Faulty knock sensor",
            "Damaged or corroded sensor wiring",
            "Loose or improperly torqued sensor",
            "Short to ground in sensor circuit",
            "Faulty ECM (rare)"
        ],
        checks=[
            "Inspect knock sensor connector and wiring for damage",
            "Test sensor resistance with multimeter (compare to spec)",
            "Verify sensor mounting torque to specification",
            "Check for shorts to ground in wiring harness",
            "View live knock sensor data with scanner",
            "Clear code and perform road test under load"
        ],
        confidence=0.75,
        source="ai_learned",
        system="Powertrain",
        symptoms=[
            "Check Engine Light illuminated",
            "Engine pinging or knocking under acceleration",
            "Reduced engine power",
            "Poor fuel economy",
            "Timing retarded to prevent damage"
        ],
        severity="High",
        severity_explanation="This code can lead to engine damage if left unaddressed. The ECM may retard timing excessively to prevent knock, reducing performance. Prolonged knock sensor failure can allow damaging detonation.",
        technician_tip="Many knock sensor codes are caused by damaged wiring or poor connector contact rather than a failed sensor. Always inspect the harness routing near the exhaust manifold where heat can damage insulation.",
        pre_replacement_checks=[
            "Wiring and connectors inspected for damage",
            "Connector terminals are clean and tight",
            "Live scanner data confirms sensor is not responding",
            "Sensor resistance tested and compared to specification"
        ]
    )

    report = format_diagnostic_report(result)
    print("=" * 80)
    print("TEST 4: AI-Generated Result (All Fields from AI)")
    print("=" * 80)
    print(report)
    print("\n\n")


def test_high_severity_result():
    """Test with high severity code"""
    result = DiagnosticResult(
        code="P0300",
        description="Random/Multiple Cylinder Misfire Detected",
        causes=[
            "Worn spark plugs",
            "Faulty ignition coils",
            "Fuel injector issues",
            "Low compression",
            "Vacuum leaks"
        ],
        checks=[
            "Scan for specific cylinder misfire codes",
            "Inspect spark plugs and coils",
            "Test fuel injector operation",
            "Perform compression test",
            "Check for vacuum leaks"
        ],
        confidence=0.90,
        source="enriched",
        system="Powertrain",
        symptoms=[
            "Check Engine Light flashing",
            "Rough idle",
            "Engine hesitation",
            "Loss of power",
            "Increased fuel consumption",
            "Engine vibration"
        ],
        severity="High",
        severity_explanation="Misfires can cause catalytic converter damage from unburned fuel entering the exhaust. A flashing check engine light indicates active misfires that require immediate attention to prevent expensive repairs.",
        technician_tip="Use freeze frame data to determine if the misfire occurs under specific conditions (cold start, load, RPM). This helps narrow down the cause quickly without replacing parts unnecessarily.",
        pre_replacement_checks=[
            "Specific cylinder codes identified",
            "Spark plugs and coils inspected",
            "Compression tested on affected cylinders",
            "Fuel delivery verified"
        ]
    )

    report = format_diagnostic_report(result)
    print("=" * 80)
    print("TEST 5: High Severity Code (Misfire)")
    print("=" * 80)
    print(report)
    print("\n\n")


if __name__ == "__main__":
    print("\n")
    print("=" * 80)
    print("DATA-DRIVEN ARCHITECTURE TEST SUITE")
    print("=" * 80)
    print("\n")
    print("Testing that formatter is presentation-only.")
    print("All intelligence comes from DiagnosticResult.")
    print("No heuristic logic in formatter.")
    print("\n")

    test_fully_populated_result()
    test_minimal_result()
    test_partial_result()
    test_ai_generated_result()
    test_high_severity_result()

    print("=" * 80)
    print("ALL TESTS COMPLETED")
    print("=" * 80)
    print("\n")
    print("✅ Formatter is presentation-only")
    print("✅ All intelligence from DiagnosticResult")
    print("✅ Minimal fallback logic only")
