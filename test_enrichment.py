#!/usr/bin/env python3
"""Quick test for enriched OBD responses."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.db.client import get_supabase_client
from app.repositories.obd_repository import OBDRepository
from app.services.obd_service import OBDService
from app.models.diagnostic import VehicleContext


async def test_code(code: str, vehicle_info: str = ""):
    """Test a single code lookup with enrichment."""
    print(f"\n{'='*80}")
    print(f"Testing: {code} {vehicle_info}")
    print('='*80)

    client = get_supabase_client()
    repo = OBDRepository(client)
    service = OBDService(repo, auto_learn=False)

    # Parse vehicle if provided
    vehicle = VehicleContext(make=None, model=None, year=None, engine=None)
    if vehicle_info:
        parts = vehicle_info.split()
        if len(parts) >= 3:
            vehicle = VehicleContext(
                make=parts[0] if len(parts) > 0 else None,
                model=parts[1] if len(parts) > 1 else None,
                year=parts[2] if len(parts) > 2 else None,
                engine=parts[3] if len(parts) > 3 else None
            )

    result = await service.get_obd_info(code, vehicle)

    print(f"\nCode: {result.code}")
    print(f"Description: {result.description}")
    print(f"Source: {result.source}")
    print(f"Confidence: {result.confidence}")
    print(f"\nLikely Causes ({len(result.causes)}):")
    for i, cause in enumerate(result.causes, 1):
        print(f"  {i}. {cause}")
    print(f"\nRecommended Checks ({len(result.checks)}):")
    for i, check in enumerate(result.checks, 1):
        print(f"  {i}. {check}")


async def main():
    """Test various codes."""
    test_cases = [
        ("P0420", ""),  # Catalyst - should get cat-specific advice
        ("P0171", ""),  # Lean - should get fuel/air advice
        ("P0300", ""),  # Misfire - should get misfire advice
        ("P0442", "Kia Rio 2020"),  # EVAP with vehicle
        ("P0507", "Chevrolet Cruze 2015"),  # Idle with vehicle
    ]

    for code, vehicle in test_cases:
        await test_code(code, vehicle)

    print(f"\n{'='*80}")
    print("✅ All tests complete!")
    print('='*80)


if __name__ == "__main__":
    asyncio.run(main())
