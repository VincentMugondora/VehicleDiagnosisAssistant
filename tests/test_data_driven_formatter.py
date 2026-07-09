"""
Tests for data-driven diagnostic formatter.

Validates that:
1. Formatter is presentation-only (no automotive knowledge)
2. All intelligence comes from DiagnosticResult model
3. Minimal fallback logic only when data unavailable
4. No keyword matching or heuristic inference
"""

import pytest
from app.models.diagnostic import DiagnosticResult
from app.services.diagnostic_formatter import format_diagnostic_report, DiagnosticReportFormatter
from app.api.formatters import format_diagnostic_response


class TestDataDrivenFormatter:
    """Test that formatter is pure presentation without automotive knowledge"""

    def test_fully_populated_result(self):
        """Test with all fields populated - formatter just presents"""
        result = DiagnosticResult(
            code="P0420",
            description="Catalyst System Efficiency Below Threshold",
            causes=["Degraded catalytic converter", "Faulty O2 sensor"],
            checks=["Check O2 sensors", "Test catalyst efficiency"],
            confidence=0.90,
            source="enriched",
            system="Emissions",
            symptoms=["Check Engine Light", "Poor performance"],
            severity="Moderate",
            severity_explanation="Should be fixed to prevent damage.",
            technician_tip="Check for exhaust leaks before replacing converter.",
            pre_replacement_checks=["O2 sensors verified", "Exhaust leaks ruled out"]
        )

        report = format_diagnostic_report(result)

        # Verify all sections present
        assert "🔧 *Fault Code: P0420*" in report
        assert "*System:* Emissions" in report
        assert "📖 *What it means*" in report
        assert "🚗 *Common symptoms*" in report
        assert "🔍 *Likely causes*" in report
        assert "🛠️ *Recommended diagnostic steps*" in report
        assert "⚠️ *Severity*" in report
        assert "*Moderate*" in report
        assert "Should be fixed to prevent damage." in report
        assert "❌ *Do NOT replace parts until*" in report
        assert "💡 *Technician Tip*" in report
        assert "Check for exhaust leaks" in report

    def test_missing_optional_fields(self):
        """Test that formatter gracefully handles missing fields"""
        result = DiagnosticResult(
            code="P9999",
            description="Unknown code",
            causes=["Unknown"],
            checks=["Consult manual"],
            confidence=0.10,
            source="unknown",
            system=None,
            symptoms=None,  # Missing
            severity=None,  # Missing
            severity_explanation=None,
            technician_tip=None,  # Missing
            pre_replacement_checks=None  # Missing
        )

        report = format_diagnostic_report(result)

        # Required sections present
        assert "P9999" in report
        assert "Unknown code" in report

        # Optional sections omitted gracefully
        assert "🚗 *Common symptoms*" not in report
        assert "⚠️ *Severity*" not in report
        assert "💡 *Technician Tip*" not in report
        assert "❌ *Do NOT replace parts until*" not in report

    def test_severity_fallback(self):
        """Test that formatter provides fallback explanation only when needed"""
        result = DiagnosticResult(
            code="P0300",
            description="Misfire",
            causes=["Spark plugs"],
            checks=["Check plugs"],
            confidence=0.85,
            source="local_db",
            system="Powertrain",
            symptoms=["Rough idle"],
            severity="High",
            severity_explanation=None,  # Missing - should use fallback
            technician_tip="Check freeze frame data",
            pre_replacement_checks=["Plugs inspected"]
        )

        report = format_diagnostic_report(result)

        # Verify fallback explanation is used
        assert "*High*" in report
        assert "engine damage" in report.lower()  # Fallback text

    def test_no_automotive_knowledge_in_formatter(self):
        """
        Critical test: Formatter should NOT infer anything from description.
        All intelligence must come from DiagnosticResult fields.
        """
        # Two codes with "sensor" in description but different data
        result1 = DiagnosticResult(
            code="P0100",
            description="MAF Sensor Circuit Malfunction",
            causes=["Dirty MAF sensor"],
            checks=["Clean MAF sensor"],
            confidence=0.85,
            source="enriched",
            system="Air Intake",
            symptoms=["Rough idle"],
            severity="Low",
            severity_explanation="Minor issue",
            technician_tip="Try cleaning before replacing",
            pre_replacement_checks=["Cleaned and retested"]
        )

        result2 = DiagnosticResult(
            code="P0200",
            description="Injector Sensor Circuit Malfunction",
            causes=["Bad injector"],
            checks=["Test injector"],
            confidence=0.85,
            source="enriched",
            system="Fuel",
            symptoms=["Misfire"],
            severity="High",
            severity_explanation="Can cause damage",
            technician_tip="Check wiring first",
            pre_replacement_checks=["Wiring verified"]
        )

        report1 = format_diagnostic_report(result1)
        report2 = format_diagnostic_report(result2)

        # Both have "sensor" in description, but formatter should present
        # the data exactly as provided, not infer based on "sensor"
        assert "Dirty MAF sensor" in report1
        assert "Bad injector" in report2
        assert "Try cleaning before replacing" in report1
        assert "Check wiring first" in report2
        assert "*Low*" in report1
        assert "*High*" in report2

    def test_formatter_consistency(self):
        """Test that formatter produces consistent output for same input"""
        result = DiagnosticResult(
            code="P0420",
            description="Test",
            causes=["Cause"],
            checks=["Check"],
            confidence=0.85,
            source="local_db",
            system="Test",
            symptoms=["Symptom"],
            severity="Moderate",
            severity_explanation="Explanation",
            technician_tip="Tip",
            pre_replacement_checks=["Check wiring"]
        )

        report1 = format_diagnostic_report(result)
        report2 = format_diagnostic_report(result)

        assert report1 == report2, "Formatter should produce consistent output"

    def test_message_splitting_with_new_format(self):
        """Test that message splitting still works with enriched data"""
        result = DiagnosticResult(
            code="P0300",
            description="Random/Multiple Cylinder Misfire Detected",
            causes=[
                "Worn spark plugs",
                "Faulty ignition coils",
                "Fuel injector issues",
                "Low compression",
                "Vacuum leaks",
                "Contaminated fuel"
            ],
            checks=[
                "Scan for specific cylinder misfire codes",
                "Inspect spark plugs and coils",
                "Test fuel injector operation",
                "Perform compression test",
                "Check for vacuum leaks",
                "Test fuel quality",
                "Check air filter",
                "Verify timing"
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
                "Engine vibration",
                "Stalling"
            ],
            severity="High",
            severity_explanation="Misfires can cause catalytic converter damage from unburned fuel entering the exhaust. A flashing check engine light indicates active misfires that require immediate attention.",
            technician_tip="Use freeze frame data to determine if the misfire occurs under specific conditions (cold start, load, RPM). This helps narrow down the cause quickly without replacing parts unnecessarily.",
            pre_replacement_checks=[
                "Specific cylinder codes identified",
                "Spark plugs and coils inspected",
                "Compression tested on affected cylinders",
                "Fuel delivery verified",
                "Timing verified"
            ]
        )

        messages = format_diagnostic_response(result)

        # Verify splitting works
        assert isinstance(messages, list)
        assert len(messages) >= 1

        # Verify each message is under limit
        for msg in messages:
            assert len(msg) <= 1600

        # Verify content preserved
        full_text = "\n\n".join(messages)
        assert "P0300" in full_text
        assert "Misfire" in full_text

    def test_all_severity_levels(self):
        """Test that all severity levels are handled correctly"""
        severities = [
            ("Critical", "safety"),
            ("High", "damage"),
            ("Moderate", "performance"),
            ("Low", "minor")
        ]

        for severity, keyword in severities:
            result = DiagnosticResult(
                code="P0001",
                description="Test",
                causes=["Test"],
                checks=["Test"],
                confidence=0.85,
                source="local_db",
                system="Test",
                symptoms=["Test"],
                severity=severity,
                severity_explanation=None,  # Force fallback
                technician_tip="Test",
                pre_replacement_checks=["Test"]
            )

            report = format_diagnostic_report(result)
            assert f"*{severity}*" in report
            assert keyword in report.lower()

    def test_no_keyword_matching(self):
        """
        Critical: Formatter should NOT match keywords in description
        to generate symptoms, tips, or checks.
        """
        # Code with "knock sensor" in description
        result = DiagnosticResult(
            code="P0332",
            description="Knock Sensor 2 Circuit Low Input",
            causes=["Faulty sensor"],
            checks=["Test sensor"],
            confidence=0.85,
            source="local_db",
            system="Powertrain",
            # Deliberately provide symptoms that don't match typical "knock sensor" symptoms
            symptoms=["Generic symptom 1", "Generic symptom 2"],
            severity="Low",
            severity_explanation="Not urgent",
            # Deliberately provide tip that doesn't mention wiring
            technician_tip="Check software version first",
            pre_replacement_checks=["Software checked"]
        )

        report = format_diagnostic_report(result)

        # Formatter should use what's provided, NOT infer from "knock sensor"
        assert "Generic symptom 1" in report
        assert "Check software version first" in report
        assert "*Low*" in report

        # Should NOT generate knock-sensor-specific content
        # (If it did, that means it's using keyword matching)
        # We verify this by confirming it uses the provided data

    def test_enriched_vs_local_db_source(self):
        """Test that both sources work identically in formatter"""
        data = {
            "code": "P0420",
            "description": "Cat Efficiency",
            "causes": ["Bad cat"],
            "checks": ["Test cat"],
            "confidence": 0.85,
            "system": "Emissions",
            "symptoms": ["Light on"],
            "severity": "Moderate",
            "severity_explanation": "Fix soon",
            "technician_tip": "Check O2 first",
            "pre_replacement_checks": ["O2 checked"]
        }

        result_enriched = DiagnosticResult(source="enriched", **data)
        result_local = DiagnosticResult(source="local_db", **data)

        report_enriched = format_diagnostic_report(result_enriched)
        report_local = format_diagnostic_report(result_local)

        # Format should be identical regardless of source
        # (only confidence might differ, but not tested here)
        assert "Cat Efficiency" in report_enriched
        assert "Cat Efficiency" in report_local
        assert "Check O2 first" in report_enriched
        assert "Check O2 first" in report_local


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
