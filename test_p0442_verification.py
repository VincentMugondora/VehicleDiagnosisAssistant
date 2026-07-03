"""
Test script to verify P0442 mixed-input bug fix.

Tests the exact scenario from the bug report:
"P0442, fuel odor, Kia Rio 2020"

Runs it multiple times to rule out intermittent failures.
"""
import asyncio
import sys
from typing import Dict, Any
import os

# Fix Windows console encoding
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"

# Add app to path
sys.path.insert(0, ".")

from app.services.obd_service import OBDService
from app.services.message_router import MessageRouter
from app.repositories.obd_repository import OBDRepository
from app.db.client import get_supabase_client
from app.models.diagnostic import VehicleContext
from app.core.logging import logger


def print_result(iteration: int, result: Any):
    """Pretty print test result"""
    print(f"\n{'='*60}")
    print(f"ITERATION {iteration}")
    print(f"{'='*60}")

    if isinstance(result, dict) and "error" in result:
        print(f"[X] ERROR: {result['error']}")
        return False

    if hasattr(result, "code"):
        print(f"[OK] SUCCESS")
        print(f"   Code: {result.code}")
        print(f"   Description: {result.description}")
        print(f"   Source: {result.source}")
        print(f"   Confidence: {result.confidence}")
        print(f"   Causes ({len(result.causes)}):")
        for i, cause in enumerate(result.causes[:5], 1):
            print(f"      {i}. {cause}")
        print(f"   Checks ({len(result.checks)}):")
        for i, check in enumerate(result.checks[:5], 1):
            print(f"      {i}. {check}")
        return True
    else:
        print(f"[X] UNEXPECTED RESULT TYPE: {type(result)}")
        print(f"   Result: {result}")
        return False


async def test_p0442_direct():
    """Test P0442 through OBDService directly"""
    print("\n" + "="*60)
    print("TEST 1: Direct OBDService.get_obd_info() call")
    print("="*60)

    client = get_supabase_client()
    obd_repo = OBDRepository(client)
    obd_service = OBDService(obd_repo, ai_client=None, auto_learn=False)

    vehicle = VehicleContext(
        make="Kia",
        model="Rio",
        year="2020",
        engine=None
    )

    results = []
    for i in range(1, 4):
        try:
            result = await obd_service.get_obd_info("P0442", vehicle)
            success = print_result(i, result)
            results.append({"iteration": i, "success": success, "result": result})
        except Exception as e:
            print(f"\n{'='*60}")
            print(f"ITERATION {i}")
            print(f"{'='*60}")
            print(f"[X] EXCEPTION: {type(e).__name__}")
            print(f"   Message: {str(e)}")
            import traceback
            print(f"\n   Traceback:")
            print("   " + "\n   ".join(traceback.format_exc().split("\n")))
            results.append({"iteration": i, "success": False, "exception": str(e)})

    return results


async def test_p0442_message_router():
    """Test P0442 through MessageRouter (full pipeline)"""
    print("\n" + "="*60)
    print("TEST 2: MessageRouter.route_message() with mixed input")
    print("="*60)

    client = get_supabase_client()
    obd_repo = OBDRepository(client)
    obd_service = OBDService(obd_repo, ai_client=None, auto_learn=False)
    message_router = MessageRouter(obd_service)

    test_message = "P0442, fuel odor, Kia Rio 2020"

    results = []
    for i in range(1, 4):
        try:
            result = await message_router.route_message(
                raw_text=test_message,
                phone_hash="test_hash_123",
                request_id=f"test_req_{i}"
            )
            success = print_result(i, result)
            results.append({"iteration": i, "success": success, "result": result})
        except Exception as e:
            print(f"\n{'='*60}")
            print(f"ITERATION {i}")
            print(f"{'='*60}")
            print(f"[X] EXCEPTION: {type(e).__name__}")
            print(f"   Message: {str(e)}")
            import traceback
            print(f"\n   Traceback:")
            print("   " + "\n   ".join(traceback.format_exc().split("\n")))
            results.append({"iteration": i, "success": False, "exception": str(e)})

    return results


async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print(" P0442 MIXED INPUT VERIFICATION TEST")
    print("="*80)
    print("\nTesting exact input from bug report:")
    print('  "P0442, fuel odor, Kia Rio 2020"')
    print("\nRunning 3 iterations per test to catch intermittent failures...")

    # Test 1: Direct OBDService
    test1_results = await test_p0442_direct()

    # Test 2: Full MessageRouter pipeline
    test2_results = await test_p0442_message_router()

    # Summary
    print("\n" + "="*80)
    print(" SUMMARY")
    print("="*80)

    test1_success = sum(1 for r in test1_results if r["success"])
    test2_success = sum(1 for r in test2_results if r["success"])

    print(f"\nTest 1 (Direct OBDService): {test1_success}/3 passed")
    print(f"Test 2 (MessageRouter): {test2_success}/3 passed")

    if test1_success == 3 and test2_success == 3:
        print("\n[OK] ALL TESTS PASSED - P0442 bug is FIXED")
        return 0
    else:
        print("\n[X] SOME TESTS FAILED - P0442 bug is NOT FIXED")
        print("\nFailed iterations:")
        for i, result in enumerate(test1_results, 1):
            if not result["success"]:
                print(f"  - Test 1, Iteration {i}: {result.get('exception', 'See output above')}")
        for i, result in enumerate(test2_results, 1):
            if not result["success"]:
                print(f"  - Test 2, Iteration {i}: {result.get('exception', 'See output above')}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
