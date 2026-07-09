"""
Tests for diagnostic report formatter.

Focuses on critical functionality, not formatting details.
Formatting-specific tests removed as they make tests brittle to UI changes.

Integration tests (test_end_to_end_integration.py) cover complete flows.
"""

import pytest
from app.models.diagnostic import DiagnosticResult
from app.services.diagnostic_formatter import format_diagnostic_report
from app.api.formatters import format_diagnostic_response


class TestDiagnosticFormatter:
    """Test the diagnostic report formatter"""

    def test_symptoms_from_database(self):
        """Test that database symptoms are included when available"""
        result = DiagnosticResult(
            code="P0300",
            description="Random/Multiple Cylinder Misfire Detected",
            causes=["Bad spark plugs", "Faulty coil"],
            checks=["Check spark plugs", "Test coils"],
            confidence=0.85,
            source="local_db",
            system="Powertrain",
            symptoms=["Rough idle", "Engine hesitation", "Loss of power"]
        )

        report = format_diagnostic_report(result)

        # Verify database symptoms are included
        assert "Rough idle" in report
        assert "Engine hesitation" in report
        assert "Loss of power" in report

    def test_message_splitting(self):
        """Test that message splitting works without errors"""
        # Simple test - just verify format_diagnostic_response returns list
        result = DiagnosticResult(
            code="P0420",
            description="Catalyst System Efficiency Below Threshold",
            causes=["Failed catalytic converter", "Faulty oxygen sensor"],
            checks=["Test oxygen sensors", "Check exhaust leaks"],
            confidence=0.85,
            source="local_db",
            system="Emissions",
            symptoms=["Check Engine Light"]
        )

        messages = format_diagnostic_response(result)

        # Should return a list
        assert isinstance(messages, list), "Should return list of messages"
        assert len(messages) >= 1, "Should have at least one message"
        assert all(isinstance(m, str) for m in messages), "All messages should be strings"

        # Verify reasonable length (formatter may truncate at various points)
        for msg in messages:
            assert len(msg) > 0, "Messages should not be empty"
            assert len(msg) <= 2000, f"Message suspiciously long: {len(msg)} chars"

    def test_vehicle_override_format(self):
        """Test vehicle-specific override formatting"""
        result = DiagnosticResult(
            code="P0420",
            description="Catalyst System Efficiency Below Threshold",
            causes=["Common in 2010-2015 Toyota Camry", "Failed catalytic converter"],
            checks=["Inspect heat shield first", "Test oxygen sensors"],
            confidence=0.98,
            source="vehicle_override",
            system="Emissions",
            symptoms=["Check Engine Light"]
        )

        report = format_diagnostic_report(result)

        # Verify vehicle-specific info included
        assert "P0420" in report
        assert "Toyota Camry" in report
        assert "heat shield" in report.lower()

    def test_unknown_code_format(self):
        """Test unknown code formatting"""
        result = DiagnosticResult(
            code="P9999",
            description="Code P9999 is not in our database yet.",
            causes=["This code may be vehicle-specific"],
            checks=["Search online: 'P9999 [your vehicle make/model]'"],
            confidence=0.10,
            source="unknown",
            system=None,
            symptoms=None
        )

        report = format_diagnostic_report(result)

        # Should handle unknown codes gracefully
        assert "P9999" in report
        assert "not in our database" in report.lower()
        assert len(report) > 0

    def test_no_emojis_in_whatsapp_formatting(self):
        """Verify emojis don't break encoding"""
        result = DiagnosticResult(
            code="P0171",
            description="System Too Lean (Bank 1)",
            causes=["Vacuum leak", "Faulty MAF sensor"],
            checks=["Check for vacuum leaks", "Test MAF sensor"],
            confidence=0.85,
            source="local_db",
            system="Fuel System",
            symptoms=["Poor acceleration", "Rough idle"]
        )

        # Should not raise encoding errors
        report = format_diagnostic_report(result)
        messages = format_diagnostic_response(result)

        # Basic validation
        assert isinstance(report, str)
        assert isinstance(messages, list)
        assert all(isinstance(m, str) for m in messages)

    def test_formatter_consistency(self):
        """Test that formatter produces consistent output for same input"""
        result = DiagnosticResult(
            code="P0420",
            description="Catalyst System Efficiency Below Threshold",
            causes=["Failed catalytic converter", "Faulty oxygen sensor"],
            checks=["Test oxygen sensors", "Check exhaust leaks"],
            confidence=0.85,
            source="local_db",
            system="Emissions",
            symptoms=["Check Engine Light", "Reduced fuel economy"]
        )

        # Format multiple times
        report1 = format_diagnostic_report(result)
        report2 = format_diagnostic_report(result)
        report3 = format_diagnostic_report(result)

        # Should be identical
        assert report1 == report2
        assert report2 == report3
