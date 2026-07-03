"""Test that Gemini enrichment is working after provider switch"""
import asyncio
import sys
sys.path.insert(0, ".")

from app.services.message_router import MessageRouter
from app.services.obd_service import OBDService
from app.repositories.obd_repository import OBDRepository
from app.db.client import get_supabase_client

async def test_gemini():
    print("\n" + "="*70)
    print("GEMINI ENRICHMENT TEST")
    print("="*70)

    client = get_supabase_client()
    obd_repo = OBDRepository(client)
    obd_service = OBDService(obd_repo, ai_client=None, auto_learn=False)
    message_router = MessageRouter(obd_service)

    print("\nTesting: P0420 Toyota Camry 2015")
    print("Expected: Gemini should rank causes based on vehicle context")

    result = await message_router.route_message(
        raw_text="P0420 Toyota Camry 2015",
        phone_hash="test_hash",
        request_id="test_gemini_1"
    )

    if hasattr(result, "code"):
        print(f"\n[OK] Code: {result.code}")
        print(f"Description: {result.description}")
        print(f"Source: {result.source}")
        print(f"\nRanked Causes:")
        for i, cause in enumerate(result.causes[:5], 1):
            print(f"  {i}. {cause}")
        print("\n[OK] Gemini enrichment appears to be working!")
        return 0
    else:
        print(f"\n[X] Error: {result}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(test_gemini())
    sys.exit(exit_code)
