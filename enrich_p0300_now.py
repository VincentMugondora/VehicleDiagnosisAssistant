#!/usr/bin/env python3
"""
Manually enrich P0300 using the AI enrichment system.

This will add symptoms, causes, diagnostic steps, technician tips, etc.
"""

import asyncio
import os
from dotenv import load_dotenv
from supabase import create_client
from app.repositories.obd_repository import OBDRepository
from app.services.obd_service import OBDService
from app.services.ai_client import AIClient
from app.models.diagnostic import VehicleContext

load_dotenv()

async def main():
    print("=" * 80)
    print("ENRICHING P0300 WITH AI")
    print("=" * 80)
    print()

    # Initialize clients
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_SERVICE_KEY")
    supabase = create_client(url, key)

    # Initialize AI client
    try:
        ai_client = AIClient()
        print(f"AI Client initialized: {ai_client.provider}")
    except Exception as e:
        print(f"ERROR: Failed to initialize AI client: {e}")
        return

    # Initialize OBD service with AI enrichment enabled
    obd_repo = OBDRepository(supabase)
    obd_service = OBDService(obd_repo, ai_client=ai_client, auto_learn=True)

    # Lookup P0300 - this will trigger enrichment if needed
    print("\nLooking up P0300...")
    vehicle = VehicleContext(make=None, model=None, year=None, engine=None)

    try:
        result = await obd_service.get_obd_info("P0300", vehicle)

        print("\n" + "=" * 80)
        print("ENRICHMENT COMPLETE")
        print("=" * 80)
        print(f"\nCode: {result.code}")
        print(f"Description: {result.description}")
        print(f"\nSymptoms: {len(result.symptoms) if result.symptoms else 0} items")
        if result.symptoms:
            for i, symptom in enumerate(result.symptoms[:3], 1):
                print(f"  {i}. {symptom}")
            if len(result.symptoms) > 3:
                print(f"  ... and {len(result.symptoms) - 3} more")

        print(f"\nCauses: {len(result.causes) if result.causes else 0} items")
        if result.causes:
            for i, cause in enumerate(result.causes[:3], 1):
                print(f"  {i}. {cause}")
            if len(result.causes) > 3:
                print(f"  ... and {len(result.causes) - 3} more")

        print(f"\nDiagnostic Steps: {len(result.checks) if result.checks else 0} items")
        if result.checks:
            for i, check in enumerate(result.checks[:3], 1):
                print(f"  {i}. {check}")
            if len(result.checks) > 3:
                print(f"  ... and {len(result.checks) - 3} more")

        print(f"\nTechnician Tip: {'YES' if result.technician_tip else 'NO'}")
        if result.technician_tip:
            print(f"  {result.technician_tip[:100]}...")

        print(f"\nPre-Replacement Checks: {'YES' if result.pre_replacement_checks else 'NO'}")

        print("\n" + "=" * 80)
        print("P0300 is now enriched in the database!")
        print("Test by querying P0300 via WhatsApp.")
        print("=" * 80)

    except Exception as e:
        print(f"\nERROR during enrichment: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
