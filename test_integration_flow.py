"""
Integration test for state machine in webhook flow.

Tests the full flow:
1. User sends diagnostic → uses free tier
2. User hits limit → gets upgrade prompt
3. User subscribes → payment initiated
4. Webhook confirms → subscription activated
5. User sends diagnostic → unlimited access
"""
import sys
import asyncio
from datetime import datetime
from app.db.client import get_supabase_client
from app.repositories.payment_repository import PaymentRepository
from app.services.user_state_machine import UserStateMachine, UserState
from app.services.payment_command_handlers import PaymentCommandHandler
from app.services.payment_service import PaymentService

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def print_section(title: str):
    """Print section header"""
    print("\n" + "="*70)
    print(f"{title}")
    print("="*70)


async def test_integration_flow():
    """Test full integration flow"""
    print_section("STATE MACHINE INTEGRATION TEST")

    supabase = get_supabase_client()
    payment_repo = PaymentRepository(supabase)
    state_machine = UserStateMachine(payment_repo)
    payment_service = PaymentService(payment_repo)
    command_handler = PaymentCommandHandler(state_machine, payment_service)

    # Test user
    test_phone_hash = "test_integration_user_hash"
    test_email = "integration@test.com"
    test_phone = "0774444444"

    # Cleanup
    print("\n🧹 Cleaning up any existing test data...")
    supabase.table("subscriptions").delete().eq("phone_hash", test_phone_hash).execute()
    supabase.table("transactions").delete().eq("phone_hash", test_phone_hash).execute()
    supabase.table("user_usage").delete().eq("phone_hash", test_phone_hash).execute()

    # Step 1: New user state
    print_section("STEP 1: New User → First Diagnostic")
    state = state_machine.resolve_state(test_phone_hash)
    print(f"State: {state.state.value}")
    print(f"Can access diagnostic: {state.can_access_diagnostic}")
    print(f"Diagnostics remaining: {state.diagnostics_remaining}")

    assert state.state == UserState.NEW_USER, f"Expected NEW_USER, got {state.state.value}"
    assert state.can_access_diagnostic, "New user should be able to access diagnostics"
    print("✅ New user can access diagnostics")

    # Simulate diagnostic usage
    print("\n📊 Simulating 5 diagnostic uses...")
    for i in range(5):
        payment_service.increment_user_usage(test_phone_hash)
        state = state_machine.resolve_state(test_phone_hash)
        print(f"   {i+1}/5 - State: {state.state.value}, Remaining: {state.diagnostics_remaining}")

    # Step 2: Free tier limit reached
    print_section("STEP 2: Free Tier Limit Reached")
    state = state_machine.resolve_state(test_phone_hash)
    print(f"State: {state.state.value}")
    print(f"Can access diagnostic: {state.can_access_diagnostic}")
    print(f"Diagnostics used: {state.diagnostics_used}")

    assert state.state == UserState.FREE_TIER, f"Expected FREE_TIER, got {state.state.value}"
    assert not state.can_access_diagnostic, "Should NOT be able to access after limit"
    print("✅ Free tier limit enforced")

    # Step 3: User subscribes
    print_section("STEP 3: User Subscribes")

    # Check if SUBSCRIBE command parses correctly
    test_command = f"SUBSCRIBE {test_email} {test_phone}"
    parsed = command_handler.parse_subscribe_or_renew(test_command)
    print(f"Command: {test_command}")
    print(f"Parsed: {parsed}")

    assert parsed is not None, "SUBSCRIBE command should parse"
    email, phone, is_renew = parsed
    assert email == test_email, f"Expected {test_email}, got {email}"
    assert phone == test_phone, f"Expected {test_phone}, got {phone}"
    assert not is_renew, "Should be subscribe, not renew"
    print("✅ SUBSCRIBE command parsed correctly")

    # Handle subscribe (would normally initiate Paynow payment)
    # For testing, we'll simulate the transaction creation
    print("\n💳 Simulating payment initiation...")
    order_ref = f"TEST-INTEGRATION-{datetime.utcnow().timestamp()}"

    tx_record = payment_repo.create_transaction(
        phone_hash=test_phone_hash,
        amount=2.00,
        currency="USD",
        description="Test integration subscription",
        order_reference=order_ref,
        user_email=test_email,
        user_phone=test_phone,
        subscription_type="monthly"
    )

    tx_id = tx_record["id"]
    print(f"Transaction created: {tx_id}")

    # Check state after subscription initiated
    state = state_machine.resolve_state(test_phone_hash)
    print(f"State: {state.state.value}")
    print(f"Has pending transaction: {state.has_pending_transaction}")

    assert state.state == UserState.PENDING_PAYMENT, f"Expected PENDING_PAYMENT, got {state.state.value}"
    assert state.has_pending_transaction, "Should have pending transaction"
    print("✅ State transitioned to PENDING_PAYMENT")

    # Step 4: Webhook confirms payment
    print_section("STEP 4: Paynow Webhook Confirms Payment")

    success, new_state, reason = state_machine.transition_to_active_subscriber(
        phone_hash=test_phone_hash,
        transaction_id=tx_id,
        order_reference=order_ref
    )

    print(f"Success: {success}")
    print(f"Reason: {reason}")
    print(f"New state: {new_state.state.value}")
    print(f"Subscription expires: {new_state.subscription_end_date}")

    assert success, "Payment confirmation should succeed"
    assert new_state.state == UserState.ACTIVE_SUBSCRIBER, f"Expected ACTIVE_SUBSCRIBER, got {new_state.state.value}"
    assert new_state.has_active_subscription, "Should have active subscription"
    print("✅ Payment confirmed, subscription activated")

    # Step 5: User sends diagnostic with unlimited access
    print_section("STEP 5: Unlimited Access for Subscriber")

    state = state_machine.resolve_state(test_phone_hash)
    print(f"State: {state.state.value}")
    print(f"Can access diagnostic: {state.can_access_diagnostic}")
    print(f"Diagnostics remaining: {state.diagnostics_remaining}")

    assert state.state == UserState.ACTIVE_SUBSCRIBER, f"Expected ACTIVE_SUBSCRIBER, got {state.state.value}"
    assert state.can_access_diagnostic, "Should have unlimited access"
    assert state.diagnostics_remaining == -1, "Should show unlimited (-1)"
    print("✅ Subscriber has unlimited access")

    # Step 6: Test duplicate webhook (idempotency)
    print_section("STEP 6: Test Duplicate Webhook (Idempotency)")

    success2, new_state2, reason2 = state_machine.transition_to_active_subscriber(
        phone_hash=test_phone_hash,
        transaction_id=tx_id,
        order_reference=order_ref
    )

    print(f"Success: {success2}")
    print(f"Reason: {reason2}")

    assert not success2, "Second webhook should be rejected"
    assert "Already processed" in reason2, f"Expected 'Already processed' in reason, got: {reason2}"
    print("✅ Duplicate webhook rejected (idempotent)")

    # Step 7: Test STATUS command
    print_section("STEP 7: Test STATUS Command")

    reply = await command_handler.handle_status(test_phone_hash)
    print(f"Reply:\n{reply}")

    assert "Active" in reply or "active" in reply, "Status should show active subscription"
    assert "Expires" in reply or "expires" in reply, "Status should show expiry date"
    print("✅ STATUS command working")

    # Step 8: Test CANCEL command
    print_section("STEP 8: Test CANCEL Command")

    reply = await command_handler.handle_cancel(test_phone_hash)
    print(f"Reply:\n{reply}")

    assert "keep" in reply.lower() or "until" in reply.lower(), "CANCEL should mention keeping access"

    # Verify state still ACTIVE_SUBSCRIBER
    state = state_machine.resolve_state(test_phone_hash)
    print(f"State after CANCEL: {state.state.value}")

    assert state.state == UserState.ACTIVE_SUBSCRIBER, f"Should still be ACTIVE_SUBSCRIBER after CANCEL"
    assert state.can_access_diagnostic, "Should still have access after CANCEL"
    print("✅ CANCEL preserves access until expiry")

    # Cleanup
    print_section("CLEANUP")
    supabase.table("subscriptions").delete().eq("phone_hash", test_phone_hash).execute()
    supabase.table("transactions").delete().eq("phone_hash", test_phone_hash).execute()
    supabase.table("user_usage").delete().eq("phone_hash", test_phone_hash).execute()
    print("✅ Test data cleaned up")

    print_section("✅ ALL INTEGRATION TESTS PASSED")
    print("\nState machine successfully integrated into:")
    print("  1. ✅ Diagnostic access control")
    print("  2. ✅ Payment command handling")
    print("  3. ✅ Webhook payment confirmation")
    print("  4. ✅ Idempotent duplicate webhook handling")
    print("  5. ✅ Free tier → Subscription flow")


if __name__ == "__main__":
    try:
        asyncio.run(test_integration_flow())
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
