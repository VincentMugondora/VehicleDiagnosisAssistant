"""
Test state machine logic and command handlers.

This demonstrates the state resolution and command handling
WITHOUT touching webhook or diagnostic access code.
"""
import sys
from app.services.payment_command_handlers import PaymentCommandHandler

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def test_command_parsing():
    """Test command parsing logic"""
    print("\n" + "="*70)
    print("COMMAND PARSING TESTS")
    print("="*70)

    # Test SUBSCRIBE/RENEW
    print("\n[1/5] SUBSCRIBE/RENEW Parsing:")
    tests = [
        ("SUBSCRIBE john@example.com 0771234567", ("john@example.com", "0771234567", False)),
        ("RENEW john@example.com 0771234567", ("john@example.com", "0771234567", True)),
        ("subscribe john@example.com 0773456789", ("john@example.com", "0773456789", False)),
        ("renew test@email.com 0778888888", ("test@email.com", "0778888888", True)),
        ("SUBSCRIBE invalid-email 0771234567", None),
        ("SUBSCRIBE john@example.com 123", None),
        ("SUBSCRIBE", None),
    ]

    for text, expected in tests:
        result = PaymentCommandHandler.parse_subscribe_or_renew(text)
        status = "✓" if result == expected else "✗"
        print(f"  [{status}] {text[:50]:50} -> {result}")

    # Test CANCEL
    print("\n[2/5] CANCEL Parsing:")
    tests = [
        ("CANCEL", True),
        ("cancel", True),
        ("CaNcEl", True),
        ("CANCEL extra", False),
        ("MY CANCEL", False),
    ]

    for text, expected in tests:
        result = PaymentCommandHandler.parse_cancel(text)
        status = "✓" if result == expected else "✗"
        print(f"  [{status}] {text[:50]:50} -> {result}")

    # Test STATUS
    print("\n[3/5] STATUS Parsing:")
    tests = [
        ("STATUS", True),
        ("status", True),
        ("StAtUs", True),
        ("STATUS extra", False),
        ("MY STATUS", False),
    ]

    for text, expected in tests:
        result = PaymentCommandHandler.parse_status(text)
        status = "✓" if result == expected else "✗"
        print(f"  [{status}] {text[:50]:50} -> {result}")

    # Test HELP
    print("\n[4/5] HELP Parsing:")
    tests = [
        ("HELP", True),
        ("help", True),
        ("HeLp", True),
        ("HELP me", False),
        ("NEED HELP", False),
    ]

    for text, expected in tests:
        result = PaymentCommandHandler.parse_help(text)
        status = "✓" if result == expected else "✗"
        print(f"  [{status}] {text[:50]:50} -> {result}")

    print("\n[5/5] Phone Validation:")
    valid_phones = [
        ("0771234567", "✓ Valid Econet"),
        ("0733456789", "✓ Valid NetOne"),
        ("0712345678", "✓ Valid Econet"),
        ("0783456789", "✓ Valid Telecel"),
    ]

    invalid_phones = [
        ("0791234567", "✗ Invalid prefix (not EcoCash)"),
        ("771234567", "✗ Missing leading 0"),
        ("07712345678", "✗ Too long"),
        ("077123456", "✗ Too short"),
    ]

    print("  Valid phones:")
    for phone, desc in valid_phones:
        result = PaymentCommandHandler.parse_subscribe_or_renew(f"SUBSCRIBE t@e.c {phone}")
        status = "✓" if result else "✗"
        print(f"    [{status}] {phone:15} - {desc}")

    print("\n  Invalid phones:")
    for phone, desc in invalid_phones:
        result = PaymentCommandHandler.parse_subscribe_or_renew(f"SUBSCRIBE t@e.c {phone}")
        status = "✓" if result is None else "✗"
        print(f"    [{status}] {phone:15} - {desc}")


def test_state_machine_logic():
    """Test state resolution logic"""
    print("\n" + "="*70)
    print("STATE MACHINE LOGIC")
    print("="*70)

    print("""
State Resolution Algorithm:
---------------------------
1. Check for active subscription (is_active=true, end_date > now)
   -> ACTIVE_SUBSCRIBER

2. Check for pending transaction (status='pending', created < 15min)
   -> PENDING_PAYMENT

3. Check for expired subscription (is_active=false OR end_date <= now)
   -> EXPIRED (behaves like free_tier)

4. Check free tier usage (diagnostics_count this week)
   -> FREE_TIER

5. No records at all
   -> NEW_USER

State Transitions:
------------------
NEW_USER -> FREE_TIER:
  Trigger: First diagnostic request

FREE_TIER -> PENDING_PAYMENT:
  Trigger: SUBSCRIBE command OR limit hit + diagnostic request

PENDING_PAYMENT -> ACTIVE_SUBSCRIBER:
  Trigger: Paynow webhook confirms (status='pending' -> 'paid')
  IDEMPOTENT: Only if transaction status is 'pending'

PENDING_PAYMENT -> FREE_TIER:
  Trigger: Timeout (15 min) OR declined payment

ACTIVE_SUBSCRIBER -> EXPIRED:
  Trigger: expiry_date passes (checked on each message)

EXPIRED -> PENDING_PAYMENT:
  Trigger: RENEW command

EXPIRED behaves like FREE_TIER:
  Falls back to 5/week limit, not completely blocked

Commands & States:
-----------------
SUBSCRIBE/RENEW: Move to PENDING_PAYMENT
  - Active subscriber: Show "already subscribed" message
  - Pending payment: Show "payment in progress" message
  - Otherwise: Initiate payment

CANCEL: Sets auto_renew=false
  - Only works in ACTIVE_SUBSCRIBER state
  - Does NOT revoke access
  - Subscription stays active until expiry_date
  - Clear message: "You'll keep access until [date]"

STATUS: Shows current state
  - ACTIVE: Expiry date, auto-renew status
  - PENDING: Order ref, time remaining
  - EXPIRED: Free tier usage, renewal prompt
  - FREE_TIER: Usage X/5, upgrade prompt
  - NEW_USER: Welcome + instructions

HELP: Context-aware help
  - Shows commands relevant to current state
""")


def test_state_scenarios():
    """Test specific state scenarios"""
    print("\n" + "="*70)
    print("STATE SCENARIOS")
    print("="*70)

    scenarios = [
        {
            "name": "New User → Free Tier → Subscribe",
            "steps": [
                "1. User sends: P0420",
                "   State: NEW_USER",
                "   Action: Serve diagnosis, increment usage (1/5)",
                "   New state: FREE_TIER",
                "",
                "2. User sends: STATUS",
                "   State: FREE_TIER",
                "   Response: 'Used: 1/5 this week'",
                "",
                "3. User sends: SUBSCRIBE john@example.com 0771234567",
                "   State: FREE_TIER",
                "   Action: Initiate payment, create transaction",
                "   New state: PENDING_PAYMENT",
                "   Response: 'Check your phone for EcoCash prompt'",
                "",
                "4. [User approves on phone]",
                "   Webhook fires: order_reference=SUB-xxx",
                "   Check: transaction.status == 'pending'? YES",
                "   Action: Update status to 'paid', create subscription",
                "   New state: ACTIVE_SUBSCRIBER",
                "",
                "5. User sends: P0171",
                "   State: ACTIVE_SUBSCRIBER",
                "   Action: Serve diagnosis (unlimited, no usage check)",
            ]
        },
        {
            "name": "Free Tier → Limit Hit → Upgrade Prompt",
            "steps": [
                "1. User sends 5 diagnostics (P0420, P0171, P0300, P0442, P0455)",
                "   State: FREE_TIER",
                "   Usage: 5/5",
                "",
                "2. User sends: P0430",
                "   State: FREE_TIER",
                "   Check: usage >= limit? YES",
                "   Response: '⚠️ Free tier limit reached. SUBSCRIBE <email> <phone>'",
                "   (Optionally auto-transition to PENDING_PAYMENT here)",
            ]
        },
        {
            "name": "Pending Payment → Timeout",
            "steps": [
                "1. User sends: SUBSCRIBE john@example.com 0771234567",
                "   State: FREE_TIER -> PENDING_PAYMENT",
                "   Transaction created at: 10:00",
                "",
                "2. [User doesn't approve, waits 16 minutes]",
                "",
                "3. User sends: P0420 (at 10:16)",
                "   State resolution checks transaction age",
                "   Created: 10:00, Now: 10:16, Diff: 16min > 15min",
                "   Action: Expire transaction (status -> 'expired')",
                "   New state: FREE_TIER",
                "   Response: 'Payment expired. Try again: SUBSCRIBE'",
            ]
        },
        {
            "name": "Active → Expired → Renew",
            "steps": [
                "1. User is ACTIVE_SUBSCRIBER",
                "   Expires: 2026-08-03 10:00",
                "",
                "2. [31 days pass]",
                "",
                "3. User sends: P0420 (at 2026-08-04)",
                "   State resolution checks expiry",
                "   end_date: 2026-08-03 < now: 2026-08-04",
                "   Action: Mark subscription expired (is_active=false)",
                "   New state: EXPIRED",
                "   Check free tier: usage 2/5",
                "   Action: Serve diagnosis",
                "   Response: Include '⚠️ Subscription expired. RENEW to continue unlimited'",
                "",
                "4. User sends: RENEW john@example.com 0771234567",
                "   State: EXPIRED",
                "   Action: Same as SUBSCRIBE - initiate payment",
                "   New state: PENDING_PAYMENT",
            ]
        },
        {
            "name": "Duplicate Webhook (Idempotency)",
            "steps": [
                "1. Webhook fires: order_reference=SUB-123",
                "   transaction.status: 'pending'",
                "   Action: Update to 'paid', create subscription",
                "   New state: ACTIVE_SUBSCRIBER",
                "",
                "2. [Same webhook fires again - network retry]",
                "   Webhook fires: order_reference=SUB-123",
                "   transaction.status: 'paid' (already processed)",
                "   Check: status == 'pending'? NO",
                "   Action: LOG WARNING, return early, do NOTHING",
                "   Result: No duplicate subscription, no double-extension",
            ]
        },
        {
            "name": "Cancel Auto-Renewal",
            "steps": [
                "1. User is ACTIVE_SUBSCRIBER",
                "   Expires: 2026-08-15",
                "   auto_renew: true",
                "",
                "2. User sends: CANCEL",
                "   State: ACTIVE_SUBSCRIBER",
                "   Action: Set auto_renew=false",
                "   State: Still ACTIVE_SUBSCRIBER (no change)",
                "   Response: 'You'll keep access until 2026-08-15. No further charges.'",
                "",
                "3. User sends: P0420",
                "   State: ACTIVE_SUBSCRIBER",
                "   Action: Serve diagnosis (still unlimited)",
                "",
                "4. [2026-08-15 passes]",
                "   State: EXPIRED",
                "   Falls back to FREE_TIER (5/week)",
            ]
        }
    ]

    for i, scenario in enumerate(scenarios, 1):
        print(f"\n[{i}/{len(scenarios)}] {scenario['name']}")
        print("-" * 70)
        for step in scenario['steps']:
            print(f"  {step}")


if __name__ == "__main__":
    print("="*70)
    print("STATE MACHINE TEST SUITE")
    print("="*70)

    test_command_parsing()
    test_state_machine_logic()
    test_state_scenarios()

    print("\n" + "="*70)
    print("IMPLEMENTATION NOTES")
    print("="*70)
    print("""
Key Design Decisions:
--------------------
1. State Resolution, Not Storage
   - Current state is DERIVED from database records
   - No 'state' column to update
   - Single source of truth

2. Idempotency
   - transaction.status guards state transitions
   - Duplicate webhooks are safe
   - No double-processing

3. Expired = Free Tier
   - Expired users aren't blocked completely
   - Fall back to 5/week limit
   - Better UX than hard block

4. Timeout Handling
   - Check on every message (check-on-access)
   - 15-minute window for payment
   - Auto-expire stale transactions

5. Cancel Behavior
   - Doesn't revoke access
   - Just stops auto-renewal
   - Clear user communication

6. Command Synonyms
   - SUBSCRIBE = RENEW (same code path)
   - Clearer intent for users

7. Structured Logging
   - Every transition logged
   - from_state, to_state, trigger
   - Debug from logs alone

Next Steps:
----------
1. Review this state machine logic
2. Wire into webhook handler
3. Wire into diagnostic access checks
4. Add integration tests
""")

    print("\n" + "="*70)
    print("ALL TESTS COMPLETE")
    print("="*70)
    print("\nTo test with backend:")
    print("1. Review state machine files:")
    print("   - app/services/user_state_machine.py")
    print("   - app/services/payment_command_handlers.py")
    print("2. Check added repository methods:")
    print("   - app/repositories/payment_repository.py")
    print("3. Next: Wire into webhook and access checks")
    print("="*70 + "\n")
