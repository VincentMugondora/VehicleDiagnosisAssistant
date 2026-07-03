"""
Test AI client fallback mechanism (Cohere -> Gemini)
"""
import asyncio
import sys
from app.services.ai_client import AIClient
from app.core.config import settings

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def test_rank_causes_fallback():
    """Test rank_causes_with_retry with Cohere primary and Gemini backup"""
    print(f"\n[TEST] Testing AI Client Fallback")
    print(f"Primary provider: {settings.ai_provider}")
    print(f"Gemini API key configured: {bool(settings.gemini_api_key)}")
    print(f"Cohere API key configured: {bool(settings.cohere_api_key)}")

    # Initialize client
    client = AIClient()
    print(f"\n[OK] Client initialized")
    print(f"   Primary: {client.provider}")
    print(f"   Backup available: {bool(client._backup_client)}")

    # Test data
    base_causes = [
        "Faulty oxygen sensor",
        "Catalytic converter efficiency below threshold",
        "Vacuum leak in intake manifold",
        "Fuel injector malfunction",
        "Mass airflow sensor dirty or faulty"
    ]

    vehicle_context = {
        "make": "Toyota",
        "model": "Camry",
        "year": "2015",
        "engine": "2.5L I4"
    }

    print(f"\n[VEHICLE] Testing with: {vehicle_context['year']} {vehicle_context['make']} {vehicle_context['model']}")
    print(f"   Base causes: {len(base_causes)}")

    # Test ranking
    try:
        ranked = client.rank_causes_with_retry(
            base_causes=base_causes,
            vehicle_context=vehicle_context,
            max_retries=2
        )

        print(f"\n[SUCCESS] Ranking successful!")
        print(f"   Returned causes: {len(ranked)}")
        print(f"\n   Ranked causes:")
        for i, cause in enumerate(ranked, 1):
            print(f"   {i}. {cause}")

    except Exception as e:
        print(f"\n[ERROR] Ranking failed: {e}")
        return False

    return True


async def test_complete_fallback():
    """Test async complete method with Cohere primary and Gemini backup"""
    print(f"\n[TEST] Testing AI Complete Fallback")

    client = AIClient()

    prompt = "Explain what P0420 means in one sentence."

    print(f"   Prompt: {prompt}")

    try:
        response = await client.complete(
            prompt=prompt,
            temperature=0.3,
            max_tokens=100
        )

        print(f"\n[SUCCESS] Complete successful!")
        print(f"   Response: {response[:150]}...")

    except Exception as e:
        print(f"\n[ERROR] Complete failed: {e}")
        return False

    return True


if __name__ == "__main__":
    print("=" * 60)
    print("AI CLIENT FALLBACK TEST")
    print("=" * 60)

    # Test 1: rank_causes
    result1 = test_rank_causes_fallback()

    # Test 2: async complete
    result2 = asyncio.run(test_complete_fallback())

    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Rank causes test: {'PASSED' if result1 else 'FAILED'}")
    print(f"Complete test: {'PASSED' if result2 else 'FAILED'}")

    if result1 and result2:
        print("\n[SUCCESS] All tests passed!")
    else:
        print("\n[WARNING] Some tests failed")
