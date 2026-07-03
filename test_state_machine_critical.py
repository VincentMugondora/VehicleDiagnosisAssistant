"""
Critical State Machine Tests

Tests three critical scenarios:
1. Duplicate webhook idempotency
2. 15-minute pending timeout expiration
3. CANCEL preserving access until expiry (not immediate revocation)
"""
import sys
import asyncio
from datetime import datetime, timedelta
from app.core.config import settings
from app.repositories.payment_repository import PaymentRepository
from app.services.user_state_machine import UserStateMachine, UserState
from app.services.payment_command_handlers import PaymentCommandHandler
from app.services.payment_service import PaymentService
from app.db.client import get_supabase_client

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def print_test_header(test_name: str):
    """Print test section header"""
    print("\n" + "="*70)
    print(f"TEST: {test_name}")
    print("="*70)


def print_result(passed: bool, message: str):
    """Print test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {message}")


async def test_duplicate_webhook_idempotency():
    """
    Test that duplicate webhooks do not create duplicate subscriptions.

    Scenario:
    1. User subscribes, transaction created (status='pending')
    2. First webhook fires -> creates subscription
    3. Second webhook fires (network retry) -> should be ignored
    4. Verify: Only ONE subscription created, no double-extension
    """
    print_test_header("Duplicate Webhook Idempotency")

    supabase = get_supabase_client()
    payment_repo = PaymentRepository(supabase)
    state_machine = UserStateMachine(payment_repo)

    # Setup: Create test user with pending transaction
    test_phone_hash = "test_idempotency_user_hash"
    test_email = "idempotency@test.com"
    test_phone = "0771111111"
    order_ref = f"TEST-IDEMPOTENCY-{datetime.utcnow().timestamp()}"

    print(f"\n1. Creating pending transaction...")
    print(f"   Phone hash: {test_phone_hash}")
    print(f"   Order ref: {order_ref}")

    # Cleanup any leftover data first
    supabase.table("subscriptions").delete().eq("phone_hash", test_phone_hash).execute()
    supabase.table("transactions").delete().eq("phone_hash", test_phone_hash).execute()
    supabase.table("user_usage").delete().eq("phone_hash", test_phone_hash).execute()

    # Create transaction (pending)
    tx_record = payment_repo.create_transaction(
        phone_hash=test_phone_hash,
        amount=2.00,
        currency="USD",
        description="Test idempotency subscription",
        order_reference=order_ref,
        user_email=test_email,
        user_phone=test_phone,
        subscription_type="monthly"
    )

    tx_id = tx_record["id"]
    print(f"   Transaction ID: {tx_id}")

    # Verify initial state
    state = state_machine.resolve_state(test_phone_hash)
    assert state.state == UserState.PENDING_PAYMENT, \
        f"Expected PENDING_PAYMENT, got {state.state.value}"
    print_result(True, "Initial state is PENDING_PAYMENT")

    # First webhook (should succeed)
    print(f"\n2. First webhook fires...")
    success1, new_state1, reason1 = state_machine.transition_to_active_subscriber(
        phone_hash=test_phone_hash,
        transaction_id=tx_id,
        order_reference=order_ref
    )

    print(f"   Success: {success1}")
    print(f"   Reason: {reason1}")
    print(f"   New state: {new_state1.state.value}")

    assert success1, "First webhook should succeed"
    assert new_state1.state == UserState.ACTIVE_SUBSCRIBER, \
        f"Expected ACTIVE_SUBSCRIBER, got {new_state1.state.value}"
    print_result(True, "First webhook created subscription")

    # Get subscription count
    subscriptions_after_first = payment_repo.get_subscription_by_phone(test_phone_hash)
    assert subscriptions_after_first is not None, "Subscription should exist"
    first_sub_id = subscriptions_after_first["id"]
    first_end_date = subscriptions_after_first["end_date"]

    print(f"   Subscription ID: {first_sub_id}")
    print(f"   End date: {first_end_date}")

    # Second webhook (should be ignored due to idempotency)
    print(f"\n3. Second webhook fires (duplicate)...")
    success2, new_state2, reason2 = state_machine.transition_to_active_subscriber(
        phone_hash=test_phone_hash,
        transaction_id=tx_id,
        order_reference=order_ref
    )

    print(f"   Success: {success2}")
    print(f"   Reason: {reason2}")
    print(f"   New state: {new_state2.state.value}")

    assert not success2, "Second webhook should be rejected (idempotent)"
    assert "Already processed" in reason2, f"Expected 'Already processed' in reason, got: {reason2}"
    print_result(True, "Second webhook ignored (idempotent)")

    # Verify subscription unchanged
    subscriptions_after_second = payment_repo.get_subscription_by_phone(test_phone_hash)
    second_sub_id = subscriptions_after_second["id"]
    second_end_date = subscriptions_after_second["end_date"]

    assert first_sub_id == second_sub_id, "Subscription ID should not change"
    assert first_end_date == second_end_date, "End date should not be extended"
    print_result(True, "Subscription unchanged (no double-extension)")

    # Cleanup
    print(f"\n4. Cleanup...")
    supabase.table("subscriptions").delete().eq("phone_hash", test_phone_hash).execute()
    supabase.table("transactions").delete().eq("phone_hash", test_phone_hash).execute()
    print_result(True, "Test data cleaned up")

    print("\n✅ TEST PASSED: Duplicate webhook idempotency verified")


async def test_15_minute_timeout_expiration():
    """
    Test that pending transactions expire after 15 minutes.

    Scenario:
    1. User subscribes, transaction created (status='pending')
    2. Wait (or simulate wait by backdating created_at)
    3. Resolve state after 16 minutes
    4. Verify: Transaction auto-expired, state returns to FREE_TIER
    """
    print_test_header("15-Minute Pending Timeout Expiration")

    supabase = get_supabase_client()
    payment_repo = PaymentRepository(supabase)
    state_machine = UserStateMachine(payment_repo)

    # Setup: Create test user with pending transaction
    test_phone_hash = "test_timeout_user_hash"
    test_email = "timeout@test.com"
    test_phone = "0772222222"
    order_ref = f"TEST-TIMEOUT-{datetime.utcnow().timestamp()}"

    print(f"\n1. Creating pending transaction...")
    print(f"   Phone hash: {test_phone_hash}")
    print(f"   Order ref: {order_ref}")

    # Cleanup any leftover data first
    supabase.table("subscriptions").delete().eq("phone_hash", test_phone_hash).execute()
    supabase.table("transactions").delete().eq("phone_hash", test_phone_hash).execute()
    supabase.table("user_usage").delete().eq("phone_hash", test_phone_hash).execute()

    # Create transaction (pending)
    tx_record = payment_repo.create_transaction(
        phone_hash=test_phone_hash,
        amount=2.00,
        currency="USD",
        description="Test timeout subscription",
        order_reference=order_ref,
        user_email=test_email,
        user_phone=test_phone,
        subscription_type="monthly"
    )

    tx_id = tx_record["id"]
    print(f"   Transaction ID: {tx_id}")

    # Verify initial state
    state = state_machine.resolve_state(test_phone_hash)
    assert state.state == UserState.PENDING_PAYMENT, \
        f"Expected PENDING_PAYMENT, got {state.state.value}"
    print_result(True, "Initial state is PENDING_PAYMENT")

    # Backdate the transaction to 16 minutes ago
    print(f"\n2. Backdating transaction to 16 minutes ago...")
    old_timestamp = datetime.utcnow() - timedelta(minutes=16)

    supabase.table("transactions").update({
        "created_at": old_timestamp.isoformat()
    }).eq("id", tx_id).execute()

    print(f"   Old timestamp: {old_timestamp}")
    print_result(True, "Transaction backdated")

    # Resolve state (should detect timeout and expire transaction)
    print(f"\n3. Resolving state after timeout...")
    state_after_timeout = state_machine.resolve_state(test_phone_hash)

    print(f"   State: {state_after_timeout.state.value}")
    print(f"   Can access diagnostic: {state_after_timeout.can_access_diagnostic}")

    # Verify transaction was expired
    transaction = payment_repo.get_transaction_by_order_reference(order_ref)
    print(f"   Transaction status: {transaction['status']}")

    assert transaction["status"] == "expired", \
        f"Expected transaction status 'expired', got '{transaction['status']}'"
    print_result(True, "Transaction status updated to 'expired'")

    # Verify state returned to FREE_TIER (or NEW_USER if no prior usage)
    assert state_after_timeout.state in [UserState.FREE_TIER, UserState.NEW_USER], \
        f"Expected FREE_TIER or NEW_USER after timeout, got {state_after_timeout.state.value}"
    assert not state_after_timeout.has_pending_transaction, \
        "Should not have pending transaction after timeout"
    print_result(True, f"State returned to {state_after_timeout.state.value}")

    # Cleanup
    print(f"\n4. Cleanup...")
    supabase.table("transactions").delete().eq("phone_hash", test_phone_hash).execute()
    supabase.table("user_usage").delete().eq("phone_hash", test_phone_hash).execute()
    print_result(True, "Test data cleaned up")

    print("\n✅ TEST PASSED: 15-minute timeout expiration verified")


async def test_cancel_preserves_access_until_expiry():
    """
    Test that CANCEL preserves access until expiry, not immediate revocation.

    Scenario:
    1. User is ACTIVE_SUBSCRIBER with expiry in future
    2. User sends CANCEL command
    3. Verify: auto_renew set to false, but is_active still true
    4. Verify: State still ACTIVE_SUBSCRIBER, can still access diagnostics
    5. Verify: Expiry date unchanged
    """
    print_test_header("CANCEL Preserves Access Until Expiry")

    supabase = get_supabase_client()
    payment_repo = PaymentRepository(supabase)
    state_machine = UserStateMachine(payment_repo)
    payment_service = PaymentService(payment_repo)
    command_handler = PaymentCommandHandler(state_machine, payment_service)

    # Setup: Create test user with active subscription
    test_phone_hash = "test_cancel_user_hash"
    test_email = "cancel@test.com"
    test_phone = "0773333333"
    order_ref = f"TEST-CANCEL-{datetime.utcnow().timestamp()}"

    print(f"\n1. Creating active subscription...")
    print(f"   Phone hash: {test_phone_hash}")

    # Cleanup any leftover data first
    supabase.table("subscriptions").delete().eq("phone_hash", test_phone_hash).execute()
    supabase.table("transactions").delete().eq("phone_hash", test_phone_hash).execute()
    supabase.table("user_usage").delete().eq("phone_hash", test_phone_hash).execute()

    # Create transaction (paid)
    tx_record = payment_repo.create_transaction(
        phone_hash=test_phone_hash,
        amount=2.00,
        currency="USD",
        description="Test cancel subscription",
        order_reference=order_ref,
        user_email=test_email,
        user_phone=test_phone,
        subscription_type="monthly"
    )

    tx_id = tx_record["id"]

    # Mark transaction as paid
    payment_repo.update_transaction_status(
        order_reference=order_ref,
        status="paid"
    )

    # Create subscription (expires in 30 days)
    start_date = datetime.utcnow()
    end_date = start_date + timedelta(days=30)

    sub_record = payment_repo.create_subscription(
        phone_hash=test_phone_hash,
        amount=2.00,
        currency="USD",
        subscription_type="monthly",
        start_date=start_date,
        end_date=end_date,
        transaction_id=tx_id
    )

    sub_id = sub_record["id"]
    print(f"   Subscription ID: {sub_record}")
    print(f"   Expires: {end_date}")

    # Verify initial state (ACTIVE_SUBSCRIBER)
    state_before = state_machine.resolve_state(test_phone_hash)
    assert state_before.state == UserState.ACTIVE_SUBSCRIBER, \
        f"Expected ACTIVE_SUBSCRIBER, got {state_before.state.value}"
    assert state_before.can_access_diagnostic, "Should be able to access diagnostics"
    print_result(True, "Initial state is ACTIVE_SUBSCRIBER with access")

    # Get subscription details before cancel
    sub_before = payment_repo.get_active_subscription(test_phone_hash)
    end_date_before = sub_before["end_date"]
    is_active_before = sub_before["is_active"]
    auto_renew_before = sub_before.get("auto_renew", False)

    print(f"   Before CANCEL:")
    print(f"     is_active: {is_active_before}")
    print(f"     auto_renew: {auto_renew_before}")
    print(f"     end_date: {end_date_before}")

    # Execute CANCEL command
    print(f"\n2. Executing CANCEL command...")
    reply = await command_handler.handle_cancel(test_phone_hash)

    print(f"   Reply: {reply[:100]}...")
    assert "keep" in reply.lower() or "until" in reply.lower(), \
        "Reply should mention keeping access until expiry"
    print_result(True, "CANCEL command executed")

    # Verify state after cancel (should still be ACTIVE_SUBSCRIBER)
    state_after = state_machine.resolve_state(test_phone_hash)

    print(f"\n3. Verifying state after CANCEL...")
    print(f"   State: {state_after.state.value}")
    print(f"   Can access diagnostic: {state_after.can_access_diagnostic}")

    assert state_after.state == UserState.ACTIVE_SUBSCRIBER, \
        f"Expected ACTIVE_SUBSCRIBER after CANCEL, got {state_after.state.value}"
    assert state_after.can_access_diagnostic, \
        "Should STILL be able to access diagnostics after CANCEL"
    print_result(True, "State still ACTIVE_SUBSCRIBER with access")

    # Verify subscription details
    sub_after = payment_repo.get_active_subscription(test_phone_hash)
    end_date_after = sub_after["end_date"]
    is_active_after = sub_after["is_active"]
    auto_renew_after = sub_after.get("auto_renew", False)

    print(f"   After CANCEL:")
    print(f"     is_active: {is_active_after}")
    print(f"     auto_renew: {auto_renew_after}")
    print(f"     end_date: {end_date_after}")

    assert is_active_after, "is_active should still be True"
    assert not auto_renew_after, "auto_renew should be False"
    assert end_date_after == end_date_before, "Expiry date should be unchanged"

    print_result(True, "is_active=True, auto_renew=False, expiry unchanged")

    # Simulate expiry by backdating end_date
    print(f"\n4. Simulating expiry (backdating end_date)...")
    past_date = datetime.utcnow() - timedelta(days=1)

    supabase.table("subscriptions").update({
        "end_date": past_date.isoformat()
    }).eq("id", sub_id).execute()

    # Verify state after expiry (should be EXPIRED)
    state_after_expiry = state_machine.resolve_state(test_phone_hash)

    print(f"   State after expiry: {state_after_expiry.state.value}")

    # After expiry, state should be EXPIRED or FREE_TIER/NEW_USER (if no recent usage)
    # This is correct behavior - expired subs fall back to free tier
    assert state_after_expiry.state in [UserState.EXPIRED, UserState.FREE_TIER, UserState.NEW_USER], \
        f"Expected EXPIRED/FREE_TIER/NEW_USER after expiry date, got {state_after_expiry.state.value}"
    print_result(True, f"State becomes {state_after_expiry.state.value} after expiry date passes (expired subscription reverts to free tier)")

    # Cleanup
    print(f"\n5. Cleanup...")
    supabase.table("subscriptions").delete().eq("phone_hash", test_phone_hash).execute()
    supabase.table("transactions").delete().eq("phone_hash", test_phone_hash).execute()
    supabase.table("user_usage").delete().eq("phone_hash", test_phone_hash).execute()
    print_result(True, "Test data cleaned up")

    print("\n✅ TEST PASSED: CANCEL preserves access until expiry verified")


async def main():
    """Run all critical tests"""
    print("="*70)
    print("CRITICAL STATE MACHINE TESTS")
    print("="*70)
    print("\nThese tests verify:")
    print("1. Duplicate webhook idempotency (no double-subscriptions)")
    print("2. 15-minute pending timeout expiration")
    print("3. CANCEL preserves access until expiry (not immediate revocation)")

    try:
        await test_duplicate_webhook_idempotency()
        await test_15_minute_timeout_expiration()
        await test_cancel_preserves_access_until_expiry()

        print("\n" + "="*70)
        print("✅ ALL CRITICAL TESTS PASSED")
        print("="*70)
        print("\nState machine is ready for integration into webhook and diagnostic flow.")

    except AssertionError as e:
        print("\n" + "="*70)
        print("❌ TEST FAILED")
        print("="*70)
        print(f"\nAssertion Error: {e}")
        sys.exit(1)
    except Exception as e:
        print("\n" + "="*70)
        print("❌ TEST ERROR")
        print("="*70)
        print(f"\nUnexpected Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
