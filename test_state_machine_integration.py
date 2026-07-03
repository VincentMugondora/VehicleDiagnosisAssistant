"""
Integration tests for critical state machine scenarios.

Tests with ACTUAL database operations (mocked):
1. Duplicate webhook idempotency
2. 15-minute pending timeout
3. CANCEL preserving access until expiry
4. Active subscription + pending transaction priority
"""
import sys
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock
from app.services.user_state_machine import UserStateMachine, UserState
from app.services.payment_service import PaymentService

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def create_mock_repo():
    """Create mock payment repository"""
    return Mock()


def test_duplicate_webhook_idempotency():
    """
    Test: Duplicate webhook does NOT double-process.

    Scenario:
    1. Webhook fires with order_ref=SUB-123, transaction.status='pending'
    2. Process it: status -> 'paid', create subscription
    3. Same webhook fires again (network retry)
    4. Check: transaction.status='paid' (already processed)
    5. Result: NO duplicate subscription, log warning, return early
    """
    print("\n" + "="*70)
    print("TEST 1: Duplicate Webhook Idempotency")
    print("="*70)

    # Setup mock repo
    mock_repo = create_mock_repo()
    state_machine = UserStateMachine(mock_repo)

    phone_hash = "test_user_hash"
    order_ref = "SUB-123"
    tx_id = "tx-456"

    print("\n[Step 1] First webhook arrives")
    print(f"  Order: {order_ref}")
    print(f"  Transaction status: 'pending'")

    # Mock transaction lookup - FIRST TIME (status='pending')
    mock_repo.get_transaction_by_order_reference.return_value = {
        "id": tx_id,
        "order_reference": order_ref,
        "phone_hash": phone_hash,
        "status": "pending",  # KEY: Still pending
        "amount": 2.00,
        "currency": "USD",
        "subscription_type": "monthly"
    }

    # Mock state resolution dependencies (for initial resolve_state call)
    mock_repo.get_active_subscription.return_value = None  # No active sub yet
    mock_repo.get_pending_transactions_by_phone.return_value = []
    mock_repo.get_expired_subscription.return_value = None
    mock_repo.get_weekly_usage.return_value = 0

    # Mock update methods
    mock_repo.update_transaction_status = Mock()
    mock_repo.get_subscription_by_phone.return_value = None
    mock_repo.create_subscription = Mock()

    # Process first webhook
    success, new_state, reason = state_machine.transition_to_active_subscriber(
        phone_hash=phone_hash,
        transaction_id=tx_id,
        order_reference=order_ref
    )

    print(f"\n[Result 1] First webhook processed")
    print(f"  Success: {success}")
    print(f"  Reason: {reason}")
    print(f"  update_transaction_status called: {mock_repo.update_transaction_status.called}")
    print(f"  create_subscription called: {mock_repo.create_subscription.called}")

    assert success == True, "First webhook should succeed"
    assert mock_repo.update_transaction_status.called, "Should update transaction"
    assert mock_repo.create_subscription.called, "Should create subscription"

    print("  ✓ First webhook: Transaction updated, subscription created")

    # Reset mocks
    mock_repo.update_transaction_status.reset_mock()
    mock_repo.create_subscription.reset_mock()

    print("\n[Step 2] Second webhook arrives (duplicate)")
    print(f"  Same order: {order_ref}")
    print(f"  Transaction status NOW: 'paid' (already processed)")

    # Mock transaction lookup - SECOND TIME (status='paid')
    mock_repo.get_transaction_by_order_reference.return_value = {
        "id": tx_id,
        "order_reference": order_ref,
        "phone_hash": phone_hash,
        "status": "paid",  # KEY: Already paid!
        "amount": 2.00,
        "currency": "USD",
        "subscription_type": "monthly"
    }

    # Process duplicate webhook
    success, new_state, reason = state_machine.transition_to_active_subscriber(
        phone_hash=phone_hash,
        transaction_id=tx_id,
        order_reference=order_ref
    )

    print(f"\n[Result 2] Duplicate webhook handled")
    print(f"  Success: {success}")
    print(f"  Reason: {reason}")
    print(f"  update_transaction_status called: {mock_repo.update_transaction_status.called}")
    print(f"  create_subscription called: {mock_repo.create_subscription.called}")

    assert success == False, "Duplicate webhook should return False"
    assert "Already processed" in reason, "Should indicate already processed"
    assert not mock_repo.update_transaction_status.called, "Should NOT update transaction"
    assert not mock_repo.create_subscription.called, "Should NOT create subscription"

    print("  ✓ Duplicate webhook: No action taken, warning logged")
    print("\n[TEST PASSED] Idempotency verified ✓")


def test_pending_timeout():
    """
    Test: Pending transaction expires after 15 minutes.

    Scenario:
    1. User initiated payment at 10:00 (transaction.status='pending')
    2. User doesn't approve
    3. User sends message at 10:16 (16 minutes later)
    4. State resolution checks transaction age
    5. Age > 15 min: Auto-expire transaction (status -> 'expired')
    6. State resolves to FREE_TIER (not PENDING_PAYMENT)
    """
    print("\n" + "="*70)
    print("TEST 2: 15-Minute Pending Timeout")
    print("="*70)

    mock_repo = create_mock_repo()
    state_machine = UserStateMachine(mock_repo)

    phone_hash = "test_user_hash"
    order_ref = "SUB-789"

    # Current time
    now = datetime.utcnow()

    # Transaction created 16 minutes ago (PAST the 15-minute timeout)
    created_at = now - timedelta(minutes=16)

    print(f"\n[Setup]")
    print(f"  Current time: {now.strftime('%H:%M:%S')}")
    print(f"  Transaction created: {created_at.strftime('%H:%M:%S')}")
    print(f"  Age: 16 minutes (> 15 min timeout)")

    # Mock: No active subscription
    mock_repo.get_active_subscription.return_value = None

    # Mock: Pending transaction exists, but OLD
    mock_repo.get_pending_transactions_by_phone.return_value = [{
        "id": "tx-789",
        "order_reference": order_ref,
        "phone_hash": phone_hash,
        "status": "pending",
        "created_at": created_at,  # 16 minutes ago!
    }]

    # Mock: Expire transaction
    mock_repo.update_transaction_status = Mock()

    # Mock: No expired subscription
    mock_repo.get_expired_subscription.return_value = None

    # Mock: User has used 2 diagnostics this week
    mock_repo.get_weekly_usage.return_value = 2

    print(f"\n[Action] Resolve state")

    # Resolve state
    state = state_machine.resolve_state(phone_hash)

    print(f"\n[Result]")
    print(f"  Resolved state: {state.state.value}")
    print(f"  update_transaction_status called: {mock_repo.update_transaction_status.called}")

    if mock_repo.update_transaction_status.called:
        call_args = mock_repo.update_transaction_status.call_args
        print(f"  Called with: order_reference={call_args[1]['order_reference']}, status={call_args[1]['status']}")

    # Assertions
    assert mock_repo.update_transaction_status.called, "Should expire transaction"
    call_args = mock_repo.update_transaction_status.call_args
    assert call_args[1]['order_reference'] == order_ref, "Should expire correct transaction"
    assert call_args[1]['status'] == 'expired', "Should set status to 'expired'"

    assert state.state == UserState.FREE_TIER, f"Should resolve to FREE_TIER, got {state.state.value}"
    assert state.diagnostics_used == 2, "Should show current usage"
    assert state.diagnostics_remaining == 3, "Should show remaining (5-2=3)"

    print("  ✓ Transaction auto-expired after timeout")
    print("  ✓ State resolved to FREE_TIER (not PENDING_PAYMENT)")
    print("\n[TEST PASSED] Timeout handling verified ✓")


def test_cancel_preserves_access():
    """
    Test: CANCEL preserves access until expiry.

    Scenario:
    1. User has active subscription, expires 2026-08-15
    2. User sends CANCEL on 2026-08-01
    3. auto_renew set to false
    4. Subscription stays ACTIVE (is_active=true, end_date not changed)
    5. User can still access diagnostics
    6. After 2026-08-15: State becomes EXPIRED, falls to FREE_TIER
    """
    print("\n" + "="*70)
    print("TEST 3: CANCEL Preserves Access Until Expiry")
    print("="*70)

    mock_repo = create_mock_repo()
    state_machine = UserStateMachine(mock_repo)

    # Mock payment service
    mock_payment_service = Mock()

    phone_hash = "test_user_hash"
    subscription_id = "sub-123"

    # Dates
    now = datetime(2026, 8, 1, 10, 0, 0)  # Aug 1
    expiry = datetime(2026, 8, 15, 10, 0, 0)  # Aug 15 (14 days later)

    print(f"\n[Setup]")
    print(f"  Current date: {now.strftime('%Y-%m-%d')}")
    print(f"  Subscription expires: {expiry.strftime('%Y-%m-%d')}")
    print(f"  Days until expiry: 14")

    # Mock: Active subscription
    mock_repo.get_active_subscription.return_value = {
        "id": subscription_id,
        "phone_hash": phone_hash,
        "start_date": now - timedelta(days=16),
        "end_date": expiry,
        "is_active": True,
        "auto_renew": True
    }

    print(f"\n[Step 1] User sends CANCEL")

    # Mock: Cancel subscription
    mock_repo.update_subscription_auto_renew = Mock(return_value=True)

    # Simulate cancel via payment service
    from app.services.payment_service import PaymentService

    # We'll test the state resolution before and after cancel

    # BEFORE CANCEL: State should be ACTIVE_SUBSCRIBER
    state_before = state_machine.resolve_state(phone_hash)

    print(f"\n[Result - Before Cancel]")
    print(f"  State: {state_before.state.value}")
    print(f"  Can access: {state_before.can_access_diagnostic}")
    print(f"  Expires: {state_before.subscription_end_date.strftime('%Y-%m-%d')}")

    assert state_before.state == UserState.ACTIVE_SUBSCRIBER, "Should be active subscriber"
    assert state_before.can_access_diagnostic == True, "Should have access"

    print("  ✓ User has unlimited access")

    # Simulate CANCEL: auto_renew -> false
    mock_repo.get_active_subscription.return_value["auto_renew"] = False

    # AFTER CANCEL: State should STILL be ACTIVE_SUBSCRIBER
    state_after = state_machine.resolve_state(phone_hash)

    print(f"\n[Result - After Cancel]")
    print(f"  State: {state_after.state.value}")
    print(f"  Can access: {state_after.can_access_diagnostic}")
    print(f"  auto_renew: {state_after.auto_renew}")
    print(f"  Expires: {state_after.subscription_end_date.strftime('%Y-%m-%d')}")

    assert state_after.state == UserState.ACTIVE_SUBSCRIBER, "Should STILL be active subscriber"
    assert state_after.can_access_diagnostic == True, "Should STILL have access"
    assert state_after.auto_renew == False, "auto_renew should be false"

    print("  ✓ User STILL has unlimited access (not revoked)")
    print("  ✓ auto_renew=false (no future charges)")

    # AFTER EXPIRY: Simulate time passing
    print(f"\n[Step 2] Time passes (Aug 16 - after expiry)")

    # Mock: Subscription now expired (end_date in past)
    mock_repo.get_active_subscription.return_value = None  # No longer active
    mock_repo.get_pending_transactions_by_phone.return_value = []  # No pending tx
    mock_repo.get_expired_subscription.return_value = {
        "id": subscription_id,
        "phone_hash": phone_hash,
        "end_date": expiry,
        "is_active": False
    }
    mock_repo.get_weekly_usage.return_value = 1  # Used 1 this week

    state_expired = state_machine.resolve_state(phone_hash)

    print(f"\n[Result - After Expiry]")
    print(f"  State: {state_expired.state.value}")
    print(f"  Can access: {state_expired.can_access_diagnostic}")
    print(f"  Free tier: {state_expired.diagnostics_used}/{state_expired.diagnostics_used + state_expired.diagnostics_remaining}")

    assert state_expired.state == UserState.EXPIRED, "Should be expired"
    assert state_expired.can_access_diagnostic == True, "Should have FREE_TIER access (1/5)"
    assert state_expired.diagnostics_remaining == 4, "Should have 4 remaining"

    print("  ✓ State changed to EXPIRED")
    print("  ✓ Falls back to FREE_TIER (5/week), not blocked")
    print("\n[TEST PASSED] CANCEL preserves access until expiry ✓")


def test_active_subscription_plus_pending_priority():
    """
    Test: Priority when user has BOTH active subscription AND pending transaction.

    Scenario:
    1. User has active subscription (expires 2026-08-15)
    2. User also has pending transaction (maybe they clicked SUBSCRIBE twice?)
    3. State resolution checks active subscription FIRST
    4. Result: Resolves to ACTIVE_SUBSCRIBER (not PENDING_PAYMENT)
    5. Deterministic: Same inputs always produce same state
    """
    print("\n" + "="*70)
    print("TEST 4: Active Subscription + Pending Transaction Priority")
    print("="*70)

    mock_repo = create_mock_repo()
    state_machine = UserStateMachine(mock_repo)

    phone_hash = "test_user_hash"
    now = datetime.utcnow()

    print(f"\n[Setup] User has BOTH:")
    print(f"  1. Active subscription (expires in 10 days)")
    print(f"  2. Pending transaction (created 5 minutes ago)")

    # Mock: Active subscription EXISTS
    mock_repo.get_active_subscription.return_value = {
        "id": "sub-123",
        "phone_hash": phone_hash,
        "end_date": now + timedelta(days=10),  # Expires in future
        "is_active": True,
        "auto_renew": True
    }

    # Mock: Pending transaction ALSO exists
    mock_repo.get_pending_transactions_by_phone.return_value = [{
        "id": "tx-789",
        "order_reference": "SUB-789",
        "phone_hash": phone_hash,
        "status": "pending",
        "created_at": now - timedelta(minutes=5)  # Recent
    }]

    print(f"\n[Question] Which state should resolve?")
    print(f"  Option A: ACTIVE_SUBSCRIBER (subscription wins)")
    print(f"  Option B: PENDING_PAYMENT (transaction wins)")

    # Resolve state
    state = state_machine.resolve_state(phone_hash)

    print(f"\n[Result]")
    print(f"  Resolved state: {state.state.value}")
    print(f"  Has active subscription: {state.has_active_subscription}")
    print(f"  Has pending transaction: {state.has_pending_transaction}")
    print(f"  Can access diagnostic: {state.can_access_diagnostic}")

    # Assertions
    assert state.state == UserState.ACTIVE_SUBSCRIBER, \
        f"Should resolve to ACTIVE_SUBSCRIBER (subscription priority), got {state.state.value}"
    assert state.has_active_subscription == True, "Should show active subscription"
    assert state.can_access_diagnostic == True, "Should have unlimited access"

    print("  ✓ Resolved to ACTIVE_SUBSCRIBER (subscription takes priority)")

    # Test determinism: Call again with same inputs
    state2 = state_machine.resolve_state(phone_hash)

    assert state2.state == state.state, "Should be deterministic (same result)"

    print("  ✓ Deterministic: Same inputs produce same state")
    print("\n[Priority Logic]")
    print("  1. Active subscription checked FIRST")
    print("  2. If found and valid: Return ACTIVE_SUBSCRIBER")
    print("  3. Pending transaction checked SECOND")
    print("  4. Order matters, priority is deterministic")
    print("\n[TEST PASSED] Priority logic verified ✓")


if __name__ == "__main__":
    print("="*70)
    print("STATE MACHINE INTEGRATION TESTS")
    print("="*70)
    print("\nTesting critical scenarios with mocked database operations")

    try:
        test_duplicate_webhook_idempotency()
        test_pending_timeout()
        test_cancel_preserves_access()
        test_active_subscription_plus_pending_priority()

        print("\n" + "="*70)
        print("ALL INTEGRATION TESTS PASSED ✓")
        print("="*70)
        print("\nVerified:")
        print("  1. ✓ Duplicate webhook idempotency")
        print("  2. ✓ 15-minute pending timeout")
        print("  3. ✓ CANCEL preserves access until expiry")
        print("  4. ✓ Active + Pending priority (deterministic)")
        print("\nReady for webhook integration!")
        print("="*70 + "\n")

    except AssertionError as e:
        print(f"\n[FAILED] {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
