"""Test free tier limit enforcement"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.user_state_machine import UserStateMachine
from app.db.client import get_supabase_client
from app.repositories.payment_repository import PaymentRepository
from app.utils.phone import hash_phone_number

client = get_supabase_client()
repo = PaymentRepository(client)
state_machine = UserStateMachine(repo)

# Test phone that doesn't have subscription
test_phone = "whatsapp:0778888888"
phone_hash = hash_phone_number(test_phone)

print(f"Testing free tier limits for: {test_phone}")
print(f"Phone hash: {phone_hash[:20]}...")
print("=" * 80)

# Check state multiple times (simulating diagnostic requests)
for i in range(7):
    state = state_machine.resolve_state(phone_hash)
    print(f"\nRequest {i+1}:")
    print(f"  State: {state.state.value}")
    print(f"  Used: {state.diagnostics_used}")
    print(f"  Remaining: {state.diagnostics_remaining}")
    print(f"  Can Access: {state.can_access_diagnostic}")
    print(f"  Reason: {state.reason}")

    if state.can_access_diagnostic:
        # Simulate diagnostic by incrementing usage
        from app.services.user_state_machine import StateTransitionTrigger
        state_machine.transition_after_diagnostic(
            phone_hash=phone_hash,
            trigger=StateTransitionTrigger.DIAGNOSTIC_REQUEST
        )
        print(f"  ✅ Diagnostic served")
    else:
        print(f"  ❌ Access denied - {state.reason}")
