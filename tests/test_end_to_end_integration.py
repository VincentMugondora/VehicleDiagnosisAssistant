"""
End-to-End Integration Tests

Tests the complete request flow from OBD code lookup through enrichment to formatted output.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.obd_service import OBDService
from app.repositories.obd_repository import OBDRepository
from app.models.diagnostic import DiagnosticResult, VehicleContext
from app.api.formatters import format_diagnostic_response


class TestCompleteRecordFlow:
    """Test flow for codes with complete data"""

    @pytest.mark.asyncio
    async def test_complete_code_lookup_no_enrichment(self):
        """Complete code should return immediately without AI enrichment"""
        # Setup mock repository with complete data
        mock_repo = MagicMock(spec=OBDRepository)
        mock_repo.get_by_code.return_value = {
            "code": "P0420",
            "description": "Catalyst System Efficiency Below Threshold (Bank 1)",
            "symptoms": "Check Engine Light, reduced fuel economy, sulfur smell",
            "common_causes": "Failed catalytic converter, exhaust leak, oxygen sensor failure",
            "generic_fixes": "Inspect exhaust system, test oxygen sensors, check for leaks",
            "system": "Emissions",
            "severity": "High",
            "severity_explanation": "Can cause emissions test failure and potential engine damage",
            "technician_tip": "Always test oxygen sensors before replacing expensive catalytic converter",
            "pre_replacement_checks": "Check for exhaust leaks, verify oxygen sensor readings, inspect wiring"
        }
        mock_repo.get_vehicle_override.return_value = None

        # No AI client needed for complete records
        service = OBDService(obd_repo=mock_repo, ai_client=None, auto_learn=False)

        # Execute lookup
        vehicle = VehicleContext(make="Toyota", model="Camry", year="2015", engine="2.5L")
        result = await service.get_obd_info("P0420", vehicle)

        # Verify no AI was called (no enrichment needed)
        assert result.code == "P0420"
        assert result.source == "local_db"
        assert result.confidence == 0.85
        assert len(result.causes) == 3
        assert len(result.checks) == 3
        assert result.symptoms is not None
        assert len(result.symptoms) == 3
        assert result.severity == "High"
        assert result.technician_tip is not None


class TestPartialRecordEnrichment:
    """Test flow for codes missing some fields that need enrichment"""

    @pytest.mark.asyncio
    async def test_partial_code_triggers_enrichment(self):
        """Partial code should trigger selective enrichment for missing fields"""
        # Setup mock repository with partial data (missing symptoms, severity, tip)
        mock_repo = MagicMock(spec=OBDRepository)
        mock_repo.get_by_code.return_value = {
            "code": "P0171",
            "description": "System Too Lean (Bank 1)",
            "symptoms": None,  # Missing
            "common_causes": "Vacuum leak, faulty MAF sensor, fuel pressure issue",
            "generic_fixes": "Check for vacuum leaks, test MAF sensor, verify fuel pressure",
            "system": "Fuel & Air",
            "severity": None,  # Missing
            "severity_explanation": None,
            "technician_tip": None,  # Missing
            "pre_replacement_checks": None
        }
        mock_repo.get_vehicle_override.return_value = None
        mock_repo.enrich_code.return_value = {
            "code": "P0171",
            "symptoms": "Poor acceleration, rough idle, hesitation, Check Engine Light",
            "severity": "Moderate",
            "severity_explanation": "Can lead to poor fuel economy and potential engine damage if ignored",
            "technician_tip": "Start with smoke test for vacuum leaks - cheapest and most common cause",
            "pre_replacement_checks": "Perform smoke test, check intake boots, inspect PCV valve"
        }

        # Mock AI client and enrichment
        mock_ai = AsyncMock()
        mock_ai.complete.return_value = """{
            "symptoms": ["Poor acceleration", "Rough idle", "Hesitation", "Check Engine Light illuminated"],
            "severity": "Moderate",
            "severity_explanation": "Can lead to poor fuel economy and potential engine damage if ignored",
            "technician_tip": "Start with smoke test for vacuum leaks - cheapest and most common cause",
            "pre_replacement_checks": ["Perform smoke test", "Check intake boots", "Inspect PCV valve"]
        }"""

        service = OBDService(obd_repo=mock_repo, ai_client=mock_ai, auto_learn=True)

        # Execute lookup
        vehicle = VehicleContext(make=None, model=None, year=None, engine=None)
        result = await service.get_obd_info("P0171", vehicle)

        # Verify enrichment was triggered
        assert result.code == "P0171"
        assert result.source == "enriched"
        assert result.confidence == 0.90
        assert result.symptoms is not None
        assert len(result.symptoms) == 4
        assert result.severity == "Moderate"
        assert result.technician_tip is not None
        assert "smoke test" in result.technician_tip.lower()

        # Verify repository enrichment was called
        mock_repo.enrich_code.assert_called_once()


class TestUnknownCodeGeneration:
    """Test flow for codes not in database that need full AI generation"""

    @pytest.mark.asyncio
    async def test_unknown_code_generates_with_ai(self):
        """Unknown code should trigger full AI generation and save to database"""
        # Setup mock repository - code not found
        mock_repo = MagicMock(spec=OBDRepository)
        mock_repo.get_by_code.return_value = None
        mock_repo.insert_code.return_value = {"code": "P2096"}

        # Mock AI client
        mock_ai = AsyncMock()
        mock_ai.complete.return_value = """{
            "code": "P2096",
            "description": "Post Catalyst Fuel Trim System Too Lean (Bank 1)",
            "symptoms": "Check Engine Light illuminated, reduced fuel economy, rough idle, hesitation during acceleration",
            "common_causes": "Exhaust leak after catalytic converter, faulty downstream oxygen sensor, damaged exhaust pipe",
            "generic_fixes": "Inspect exhaust system for leaks, test downstream O2 sensor, check exhaust manifold gaskets",
            "system": "Emissions",
            "severity": "Moderate",
            "severity_explanation": "Won't cause immediate damage but should be addressed to maintain emissions compliance",
            "technician_tip": "This is a downstream code - check exhaust leaks between catalytic converter and rear O2 sensor first",
            "pre_replacement_checks": "Visual exhaust inspection, downstream O2 sensor voltage test, check for exhaust leaks with smoke machine"
        }"""

        service = OBDService(obd_repo=mock_repo, ai_client=mock_ai, auto_learn=True)

        # Execute lookup
        vehicle = VehicleContext(make=None, model=None, year=None, engine=None)
        result = await service.get_obd_info("P2096", vehicle)

        # Verify AI generation was used
        assert result.code == "P2096"
        assert result.source == "ai_learned"
        assert result.confidence == 0.75
        assert "Post Catalyst" in result.description
        assert result.symptoms is not None
        assert result.severity == "Moderate"
        assert result.technician_tip is not None

        # Verify code was saved to database
        mock_repo.insert_code.assert_called_once()
        saved_data = mock_repo.insert_code.call_args[0][0]
        assert saved_data["code"] == "P2096"


class TestVehicleOverride:
    """Test vehicle-specific override handling"""

    @pytest.mark.asyncio
    async def test_vehicle_override_merges_with_base(self):
        """Vehicle override should merge with base code data"""
        mock_repo = MagicMock(spec=OBDRepository)
        mock_repo.get_by_code.return_value = {
            "code": "P0420",
            "description": "Catalyst System Efficiency Below Threshold (Bank 1)",
            "symptoms": "Check Engine Light, reduced fuel economy",
            "common_causes": "Failed catalytic converter, oxygen sensor failure",
            "generic_fixes": "Inspect exhaust system, test oxygen sensors",
            "system": "Emissions",
            "severity": "High",
            "severity_explanation": "Can cause emissions test failure",
            "technician_tip": "Test oxygen sensors first",
            "pre_replacement_checks": "Check for exhaust leaks"
        }
        mock_repo.get_vehicle_override.return_value = {
            "known_issues": ["Common in 2010-2015 Toyota Camry - often caused by heat shield rattling against converter"],
            "priority_checks": ["Inspect heat shield for damage before replacing converter - saves $800"]
        }

        service = OBDService(obd_repo=mock_repo, ai_client=None, auto_learn=False)

        # Execute with vehicle context
        vehicle = VehicleContext(make="Toyota", model="Camry", year="2015", engine="2.5L")
        result = await service.get_obd_info("P0420", vehicle)

        # Verify override was applied
        assert result.source == "vehicle_override"
        assert result.confidence == 0.98
        assert "heat shield" in str(result.causes).lower()
        assert any("heat shield" in check.lower() for check in result.checks)


class TestFormatterIntegration:
    """Test that diagnostic results format correctly for WhatsApp"""

    def test_complete_result_formats_correctly(self):
        """Complete diagnostic result should format into proper WhatsApp message"""
        result = DiagnosticResult(
            code="P0420",
            description="Catalyst System Efficiency Below Threshold (Bank 1)",
            causes=[
                "Failed catalytic converter",
                "Exhaust leak before catalytic converter",
                "Faulty oxygen sensor"
            ],
            checks=[
                "Inspect exhaust system for leaks",
                "Test upstream and downstream oxygen sensors",
                "Check catalytic converter efficiency",
                "Verify fuel trim values"
            ],
            confidence=0.90,
            source="enriched",
            system="Emissions",
            symptoms=[
                "Check Engine Light illuminated",
                "Reduced fuel economy",
                "Sulfur smell from exhaust"
            ],
            severity="High",
            severity_explanation="Can cause emissions test failure and potential engine damage if ignored",
            technician_tip="Always test oxygen sensors before replacing expensive catalytic converter",
            pre_replacement_checks=[
                "Check for exhaust leaks",
                "Verify oxygen sensor readings",
                "Inspect wiring and connectors"
            ]
        )

        messages = format_diagnostic_response(result)

        # Should return list of messages
        assert isinstance(messages, list)
        assert len(messages) >= 1

        # Combine all messages for content verification
        full_message = "\n".join(messages)

        # Verify key sections are present
        assert "P0420" in full_message
        assert "Catalyst System" in full_message
        assert "Emissions" in full_message
        assert "symptoms" in full_message.lower()
        assert "causes" in full_message.lower()
        assert "diagnostic" in full_message.lower() or "steps" in full_message.lower()
        assert "High" in full_message  # Severity
        assert "tip" in full_message.lower()
        assert "replace" in full_message.lower() or "before" in full_message.lower()

    def test_unknown_code_formats_safely(self):
        """Unknown code should format without errors"""
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

        messages = format_diagnostic_response(result)

        assert isinstance(messages, list)
        assert len(messages) == 1
        assert "P9999" in messages[0]
        assert "not in our database" in messages[0]


class TestMetadataPersistence:
    """Test that enrichment metadata is properly stored and retrieved"""

    @pytest.mark.asyncio
    async def test_enrichment_stores_metadata(self):
        """Enrichment should store provenance metadata for each field"""
        mock_repo = MagicMock(spec=OBDRepository)
        mock_repo.get_by_code.return_value = {
            "code": "P0300",
            "description": "Random/Multiple Cylinder Misfire Detected",
            "symptoms": None,  # Missing
            "common_causes": "Ignition coil failure, spark plug issues",
            "generic_fixes": "Replace spark plugs, test ignition coils",
            "system": "Ignition"
        }
        mock_repo.enrich_code.return_value = {"code": "P0300"}

        mock_ai = AsyncMock()
        mock_ai.complete.return_value = """{
            "symptoms": ["Rough idle", "Engine shaking", "Loss of power", "Check Engine Light flashing"]
        }"""

        service = OBDService(obd_repo=mock_repo, ai_client=mock_ai, auto_learn=True)

        vehicle = VehicleContext(make=None, model=None, year=None, engine=None)
        await service.get_obd_info("P0300", vehicle)

        # Verify enrich_code was called with metadata
        mock_repo.enrich_code.assert_called_once()
        args = mock_repo.enrich_code.call_args

        # Check that metadata fields were passed
        metadata_fields = args[0][2]  # Third argument is metadata_fields
        assert "symptoms_meta" in metadata_fields
        meta = metadata_fields["symptoms_meta"]
        assert meta["source"] == "ai_generated"
        assert meta["ai_model"] == "claude-sonnet-4"
        assert meta["prompt_version"] == "v6"
        assert "generated_at" in meta


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
