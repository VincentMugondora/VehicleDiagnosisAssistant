#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Live Response - See actual enriched response format

Usage:
    python scripts/test_live_response.py P0171
    python scripts/test_live_response.py P0300
    python scripts/test_live_response.py P0420
"""

import sys
import asyncio
import codecs
from pathlib import Path

# Force UTF-8 output
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'replace')

sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase import create_client
from app.core.config import settings
from app.services.obd_service import OBDService
from app.repositories.obd_repository import OBDRepository
from app.services.diagnostic_formatter import format_diagnostic_report
from app.models.diagnostic import VehicleContext
from app.services.cohere_client import CohereClient


async def test_code(code: str):
    """Test a specific OBD code response"""

    print("\n" + "="*70)
    print(f"TESTING CODE: {code}")
    print("="*70)

    # Initialize services
    supabase_client = create_client(settings.supabase_url, settings.supabase_service_key)
    obd_repo = OBDRepository(supabase_client)
    ai_client = CohereClient()
    obd_service = OBDService(obd_repo, ai_client, auto_learn=False)  # Don't auto-learn during test

    # Create vehicle context (generic)
    vehicle = VehicleContext(
        make="Toyota",
        model="Camry",
        year="2015",
        engine="2.5L"
    )

    print(f"\n[*] Looking up code {code}...")

    # Get diagnostic result
    result = await obd_service.get_obd_info(code, vehicle)

    print(f"[OK] Code found!")
    print(f"     Source: {result.source}")
    print(f"     Confidence: {result.confidence}")

    # Format the response
    formatted = format_diagnostic_report(result)

    print("\n" + "="*70)
    print("FORMATTED RESPONSE (What user sees):")
    print("="*70)
    print()
    print(formatted)
    print()
    print("="*70)

    # Show enrichment details
    print("\nENRICHMENT DETAILS:")
    print("-"*70)
    print(f"Has Cost Estimate:        {'YES' if result.typical_cost_range else 'NO'}")
    print(f"Has Time Estimate:        {'YES' if result.typical_repair_time else 'NO'}")
    print(f"Has DIY Difficulty:       {'YES' if result.diy_difficulty else 'NO'}")
    print(f"Has Related Codes:        {'YES' if result.related_codes else 'NO'}")
    print(f"Has Misdiagnosis Warning: {'YES' if result.common_misdiagnoses else 'NO'}")
    print(f"Has Scanner Guidance:     {'YES' if result.freeze_frame_data_to_check else 'NO'}")
    print(f"Has Likelihood Ranking:   {'YES' if result.cause_likelihoods else 'NO'}")

    if result.typical_cost_range:
        print(f"\nCost: {result.typical_cost_range}")
    if result.typical_repair_time:
        print(f"Time: {result.typical_repair_time}")
    if result.diy_difficulty:
        print(f"DIY:  {result.diy_difficulty}")


async def main():
    if len(sys.argv) < 2:
        print("\nUsage: python scripts/test_live_response.py <CODE>")
        print("\nExample codes to test:")
        print("  P0171  (System Too Lean - ENRICHED)")
        print("  P0300  (Random Misfire - ENRICHED)")
        print("  P0132  (O2 Sensor - ENRICHED)")
        print("  P0301  (Cylinder 1 Misfire - ENRICHED)")
        print("  P0420  (Catalyst - check if enriched)")
        return 1

    code = sys.argv[1].upper()
    await test_code(code)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
