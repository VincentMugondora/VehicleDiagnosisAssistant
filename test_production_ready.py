"""
Production readiness test for AI providers
Tests actual vehicle diagnosis scenario
"""
import asyncio
import sys
from app.services.ai_client import AIClient

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def test_production_scenario():
    """Test real-world vehicle diagnosis scenario"""
    print("\n" + "="*60)
    print("PRODUCTION READINESS TEST")
    print("="*60)

    # Initialize
    print("\n[1/3] Initializing AI Client...")
    client = AIClient()
    print(f"   Primary: {client.provider}")
    print(f"   Backup: {'Available' if client._backup_client else 'Not configured'}")

    # Test Case: P0420 - Catalytic Converter Issue
    print("\n[2/3] Testing OBD Code P0420 Diagnosis...")

    base_causes = [
        "Faulty oxygen sensor (bank 1, sensor 2)",
        "Catalytic converter efficiency below threshold",
        "Exhaust leak before catalytic converter",
        "Engine running too rich or lean",
        "Fuel injector issues",
        "Bad spark plugs",
        "Vacuum leak"
    ]

    vehicle = {
        "make": "Toyota",
        "model": "Camry",
        "year": "2015",
        "engine": "2.5L 4-cylinder"
    }

    print(f"   Vehicle: {vehicle['year']} {vehicle['make']} {vehicle['model']}")
    print(f"   Code: P0420 (Catalyst System Efficiency Below Threshold)")
    print(f"   Evaluating {len(base_causes)} possible causes...")

    try:
        ranked = client.rank_causes_with_retry(
            base_causes=base_causes,
            vehicle_context=vehicle,
            max_retries=3
        )

        print(f"\n   [SUCCESS] AI ranked {len(ranked)} most likely causes:")
        for i, cause in enumerate(ranked, 1):
            print(f"   {i}. {cause}")

    except Exception as e:
        print(f"\n   [ERROR] Ranking failed: {e}")
        return False

    # Test async completion
    print("\n[3/3] Testing Diagnostic Explanation...")

    async def test_explanation():
        try:
            response = await client.complete(
                prompt="Explain P0420 code to a mechanic in 2 sentences.",
                temperature=0.3,
                max_tokens=150
            )
            print(f"   [SUCCESS] Generated explanation:")
            print(f"   {response}")
            return True
        except Exception as e:
            print(f"   [ERROR] Explanation failed: {e}")
            return False

    result = asyncio.run(test_explanation())

    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print("[OK] AI Client initialized")
    print("[OK] Cause ranking working")
    print(f"[{'OK' if result else 'FAIL'}] Text generation working")
    print("\n[RESULT] System is PRODUCTION READY" if result else "[RESULT] Some tests failed")
    print("="*60 + "\n")

    return result


if __name__ == "__main__":
    success = test_production_scenario()
    sys.exit(0 if success else 1)
