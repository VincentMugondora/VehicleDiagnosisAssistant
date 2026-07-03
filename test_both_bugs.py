#!/usr/bin/env python3
"""
Test both bugs after fixes are applied.
Run this AFTER restarting the FastAPI server.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.db.client import get_supabase_client
from app.repositories.obd_repository import OBDRepository
from app.services.obd_service import OBDService
from app.services.message_router import MessageRouter
from app.models.diagnostic import VehicleContext
from app.api.formatters import format_diagnostic_response


async def test_bug_1_empty_fields():
    """Test BUG 1: Previously blank causes/checks should now be populated."""
    print('='*80)
    print('BUG 1 TEST: Empty Fields (Should be FIXED)')
    print('='*80)

    client = get_supabase_client()
    repo = OBDRepository(client)
    service = OBDService(repo, auto_learn=False)

    test_codes = ['P0171', 'P3497', 'P0507']

    for code in test_codes:
        vehicle = VehicleContext(make=None, model=None, year=None, engine=None)
        result = await service.get_obd_info(code, vehicle)

        # Format as WhatsApp message
        messages = format_diagnostic_response(result)
        full_message = '\n\n'.join(messages)

        print(f'\n[{code}] Result:')
        print(f'  Causes: {len(result.causes)} items')
        print(f'  Checks: {len(result.checks)} items')

        if len(result.causes) == 0 or len(result.checks) == 0:
            print('  ❌ FAIL: Still has empty fields!')
        else:
            print('  ✅ PASS: Enrichment working!')

        # Check formatted message
        if '*Likely causes:*\n\n*Recommended' in full_message:
            print('  ❌ FAIL: Formatted message has blank section!')
        else:
            print('  ✅ PASS: Formatted message looks good!')


async def test_bug_2_mixed_input():
    """Test BUG 2: P0442 with symptoms + vehicle should not crash."""
    print('\n' + '='*80)
    print('BUG 2 TEST: Mixed Input (Should not crash)')
    print('='*80)

    client = get_supabase_client()
    repo = OBDRepository(client)
    service = OBDService(repo, auto_learn=False)
    router = MessageRouter(service)

    test_cases = [
        ("P0442, fuel odor, Kia Rio 2020", "Original failing case"),
        ("P0507, high idle, Chevrolet Cruze 2015", "Working case"),
        ("P3497", "Simple case"),
    ]

    for test_input, label in test_cases:
        print(f'\n[{label}]')
        print(f'  Input: "{test_input}"')

        try:
            result = await router.route_message(
                raw_text=test_input,
                phone_hash="test_hash",
                request_id="test_123",
                session=None
            )

            if hasattr(result, 'code'):
                print(f'  ✅ SUCCESS')
                print(f'    Code: {result.code}')
                print(f'    Causes: {len(result.causes)} items')
                print(f'    Checks: {len(result.checks)} items')

                # Format message
                messages = format_diagnostic_response(result)
                print(f'    Message parts: {len(messages)}')
            else:
                print(f'  ⚠️  Returned error dict: {result}')

        except Exception as e:
            print(f'  ❌ EXCEPTION: {type(e).__name__}: {str(e)}')


async def main():
    """Run all tests."""
    await test_bug_1_empty_fields()
    await test_bug_2_mixed_input()

    print('\n' + '='*80)
    print('TEST SUMMARY')
    print('='*80)
    print('If all tests passed:')
    print('  1. Restart your FastAPI server: .\\start_backend.bat')
    print('  2. Test via WhatsApp with: P0171, P0420, P0442')
    print('  3. All should show complete causes + checks')
    print('='*80)


if __name__ == "__main__":
    asyncio.run(main())
