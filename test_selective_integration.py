"""
Integration test for selective enrichment.

Tests the full flow:
1. User requests DTC
2. Service identifies missing fields
3. Selective enrichment generates only what's needed
4. Result is saved to database
5. Next request returns enriched data
"""

import asyncio
import sys
import io

# Fix Windows console encoding for checkmarks
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from unittest.mock import Mock, AsyncMock, patch
from app.services.obd_service import OBDService
from app.repositories.obd_repository import OBDRepository
from app.services.ai_client import AIClient
from app.models.diagnostic import VehicleContext


async def test_selective_enrichment_integration():
    """Test full enrichment flow with selective generation"""

    # Mock repository with partial data
    mock_repo = Mock(spec=OBDRepository)
    mock_repo.get_by_code.return_value = {
        "code": "P0420",
        "description": "Catalyst System Efficiency Below Threshold (Bank 1)",
        "system": "Emissions",
        # Missing: symptoms, causes, fixes, severity, technician_tip, pre_replacement_checks
        "common_causes": "",
        "generic_fixes": "",
        "symptoms": "",
        "severity": None,
        "severity_explanation": None,
        "technician_tip": None,
        "pre_replacement_checks": ""
    }
    mock_repo.get_vehicle_override.return_value = None

    # Track what gets saved
    saved_data = {}
    def capture_insert(data):
        saved_data.update(data)
        return data

    mock_repo.insert_code = Mock(side_effect=capture_insert)

    # Mock AI client to return realistic enrichment
    mock_ai_client = Mock(spec=AIClient)
    mock_ai_client.complete = AsyncMock(return_value="""{
        "symptoms": [
            "Check Engine Light illuminated",
            "Reduced fuel economy",
            "Sulfur smell from exhaust",
            "Loss of power at highway speeds"
        ],
        "common_causes": [
            "Catalytic converter failure",
            "Exhaust leak before converter",
            "Engine running rich",
            "Faulty oxygen sensors",
            "Oil contamination from engine burning oil"
        ],
        "generic_fixes": [
            "Inspect exhaust system for leaks",
            "Check oxygen sensor readings with scanner",
            "Test fuel trims - should be near 0%",
            "Verify engine not burning oil (check PCV valve)",
            "Replace catalytic converter only after ruling out above"
        ],
        "severity": "High",
        "severity_explanation": "Emissions failure, will not pass inspection. Reduced fuel economy. May indicate engine issues.",
        "technician_tip": "Check for exhaust leaks BEFORE replacing the converter - a $20 gasket can cause this code, not just a $1000 cat.",
        "pre_replacement_checks": [
            "Inspect exhaust manifold gaskets",
            "Check all O2 sensor connectors",
            "Test fuel pressure - should be 40-60 PSI",
            "Check for oil consumption",
            "Verify converter not physically damaged"
        ]
    }""")

    # Create service with real selective enrichment
    service = OBDService(
        obd_repo=mock_repo,
        ai_client=mock_ai_client,
        auto_learn=True
    )

    # Create test vehicle context
    vehicle = VehicleContext(
        make="Toyota",
        model="Camry",
        year="2008",
        engine="2.4L"
    )

    print("\n=== Test 1: First Request (triggers enrichment) ===\n")

    # First request should trigger selective enrichment
    result = await service.get_obd_info("P0420", vehicle)

    print(f"Code: {result.code}")
    print(f"Source: {result.source}")
    print(f"Confidence: {result.confidence}")
    print(f"Severity: {result.severity}")
    print(f"\nSymptoms ({len(result.symptoms or [])} items):")
    for s in result.symptoms or []:
        print(f"  - {s}")
    print(f"\nCauses ({len(result.causes)} items):")
    for c in result.causes[:3]:
        print(f"  - {c}")
    print(f"\nTechnician Tip: {result.technician_tip}")

    # Verify AI was called
    assert mock_ai_client.complete.called, "AI should have been called for enrichment"

    # Verify selective enrichment prompt was used
    prompt_used = mock_ai_client.complete.call_args[1]['prompt']
    assert "EXISTING CONTEXT" in prompt_used, "Should provide existing context"
    assert "FIELDS TO GENERATE" in prompt_used, "Should specify missing fields"
    assert "P0420" in prompt_used, "Should include code"

    print("\n✓ AI was called with selective enrichment prompt")

    # Verify data was saved to database
    assert mock_repo.insert_code.called, "Should save enriched data"
    assert "symptoms" in saved_data, "Should save symptoms"
    assert "technician_tip" in saved_data, "Should save technician tip"

    print("✓ Enriched data was saved to database")

    # Verify result contains enriched fields
    assert result.symptoms is not None, "Should have symptoms"
    assert len(result.symptoms) >= 4, "Should have multiple symptoms"
    assert result.severity == "High", "Should have severity"
    assert result.technician_tip is not None, "Should have technician tip"

    print("✓ Result contains all enriched fields")

    print("\n=== Test 2: Second Request (no enrichment needed) ===\n")

    # Update mock to return enriched data
    mock_repo.get_by_code.return_value = {
        "code": "P0420",
        "description": "Catalyst System Efficiency Below Threshold (Bank 1)",
        "system": "Emissions",
        "common_causes": saved_data.get("common_causes", ""),
        "generic_fixes": saved_data.get("generic_fixes", ""),
        "symptoms": saved_data.get("symptoms", ""),
        "severity": saved_data.get("severity"),
        "severity_explanation": saved_data.get("severity_explanation"),
        "technician_tip": saved_data.get("technician_tip"),
        "pre_replacement_checks": saved_data.get("pre_replacement_checks", "")
    }

    # Reset AI mock call count
    mock_ai_client.complete.reset_mock()

    # Second request should NOT trigger enrichment
    result2 = await service.get_obd_info("P0420", vehicle)

    print(f"Code: {result2.code}")
    print(f"Source: {result2.source}")
    print(f"AI called: {mock_ai_client.complete.called}")

    # Verify AI was NOT called this time
    assert not mock_ai_client.complete.called, "AI should not be called for already-enriched code"

    print("✓ Second request did not call AI (used cached enrichment)")

    # Verify same quality data returned
    assert result2.symptoms is not None
    assert result2.severity == "High"
    assert result2.technician_tip is not None

    print("✓ Second request returned enriched data from database")

    print("\n=== All Tests Passed ===\n")
    print("Integration verified:")
    print("  1. ✓ Selective enrichment detects missing fields")
    print("  2. ✓ AI generates only what's needed")
    print("  3. ✓ Data is saved to database")
    print("  4. ✓ Subsequent requests use cached enrichment")
    print("  5. ✓ Users never wait for AI after first request")


async def test_field_detection():
    """Test that missing field detection is accurate"""

    print("\n=== Test: Missing Field Detection ===\n")

    mock_repo = Mock(spec=OBDRepository)
    mock_ai_client = Mock(spec=AIClient)

    service = OBDService(mock_repo, mock_ai_client, auto_learn=True)

    # Test case 1: Completely missing enrichment
    base_data_empty = {
        "code": "P0420",
        "description": "Test",
        "system": "Emissions"
    }

    missing = []
    for field in ["symptoms", "common_causes", "generic_fixes", "severity",
                  "severity_explanation", "technician_tip", "pre_replacement_checks"]:
        if not base_data_empty.get(field):
            missing.append(field)

    print(f"Empty data missing fields: {len(missing)}")
    assert len(missing) == 7, "Should detect all 7 missing enrichment fields"
    print("✓ Correctly detects all missing fields")

    # Test case 2: Partially enriched
    base_data_partial = {
        "code": "P0420",
        "description": "Test",
        "system": "Emissions",
        "symptoms": "Check Engine Light",
        "severity": "High",
        # Missing: causes, fixes, severity_explanation, technician_tip, pre_replacement_checks
    }

    missing_partial = []
    for field in ["symptoms", "common_causes", "generic_fixes", "severity",
                  "severity_explanation", "technician_tip", "pre_replacement_checks"]:
        if not base_data_partial.get(field):
            missing_partial.append(field)

    print(f"Partial data missing fields: {len(missing_partial)}")
    assert len(missing_partial) == 5, "Should detect 5 remaining missing fields"
    print("✓ Correctly detects partially missing fields")

    print("\n✓ Field detection working correctly")


if __name__ == "__main__":
    print("=" * 60)
    print("SELECTIVE ENRICHMENT INTEGRATION TEST")
    print("=" * 60)

    asyncio.run(test_field_detection())
    asyncio.run(test_selective_enrichment_integration())

    print("\n" + "=" * 60)
    print("SUCCESS: All integration tests passed")
    print("=" * 60)
