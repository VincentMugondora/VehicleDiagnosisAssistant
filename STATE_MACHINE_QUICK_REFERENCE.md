# State Machine Quick Reference 🚀

**TL;DR**: State machine is fully integrated and working. All tests pass.

---

## Run Tests

```bash
# Critical tests (idempotency, timeout, cancel)
python test_state_machine_critical.py

# Full integration test
python test_integration_flow.py
```

---

## State Flow

```
NEW_USER (first message)
    ↓ (diagnostic)
FREE_TIER (5/week)
    ↓ (SUBSCRIBE)
PENDING_PAYMENT (15min timeout)
    ↓ (webhook confirms)
ACTIVE_SUBSCRIBER (unlimited)
    ↓ (expiry_date passes)
EXPIRED (back to 5/week)
    ↓ (RENEW)
PENDING_PAYMENT
```

---

## Commands

```
SUBSCRIBE <email> <phone>  → Initiate payment
RENEW <email> <phone>      → Same as SUBSCRIBE (clearer for expired users)
STATUS                     → Show current state
CANCEL                     → Stop auto-renewal (keeps access until expiry)
HELP                       → Context-aware help
```

---

## Key Files

**Core**:
- `app/services/user_state_machine.py` - State resolution
- `app/services/payment_command_handlers.py` - Command handling

**Integration**:
- `app/api/routes/webhook.py` - Baileys webhook (lines 370-608)
- `app/api/routes/payments.py` - Paynow webhook (lines 117-191)

**Tests**:
- `test_state_machine_critical.py` - Critical scenarios
- `test_integration_flow.py` - Full flow

---

## Key Functions

### Resolve State (Single Source of Truth)
```python
from app.services.user_state_machine import UserStateMachine

state = state_machine.resolve_state(phone_hash)

# Check access
if state.can_access_diagnostic:
    # Allow diagnostic
else:
    # Show upgrade prompt
```

### Handle Commands
```python
from app.services.payment_command_handlers import PaymentCommandHandler

# Parse
if command_handler.parse_subscribe_or_renew(raw_text):
    email, phone, is_renew = command_handler.parse_subscribe_or_renew(raw_text)
    reply = await command_handler.handle_subscribe_or_renew(
        phone_hash, email, phone, is_renew
    )
```

### Confirm Payment (Idempotent)
```python
success, new_state, reason = state_machine.transition_to_active_subscriber(
    phone_hash=phone_hash,
    transaction_id=transaction_id,
    order_reference=order_reference
)

if success:
    # Subscription activated
else:
    # Already processed (idempotent)
```

---

## Priority Logic

**If user has both active subscription AND pending transaction:**

→ **Active subscription wins** (deterministic)

**Why**: User already has unlimited access, no need to wait for renewal payment.

---

## Critical Behaviors

### ✅ Idempotent Webhooks
- Duplicate webhooks automatically rejected
- Check: `transaction.status == 'pending'`
- No double-processing

### ✅ Timeout Handling
- Pending transactions expire after 15 minutes
- Check-on-access (every `resolve_state()` call)
- Auto-expires stale transactions

### ✅ CANCEL Preserves Access
- Sets `auto_renew=false`
- Keeps `is_active=true`, `end_date` unchanged
- User retains access until expiry

### ✅ Expired = Free Tier
- Expired users fall back to 5/week
- Not blocked completely
- Clear upgrade prompts

---

## Monitoring

**Key logs to watch:**
```
state_resolved                 - State resolution result
state_transition              - State changed
duplicate_webhook_ignored     - Idempotency working
payment_timeout_detected      - Transaction expired
subscription_expired_on_check - Subscription expired
```

---

## Troubleshooting

### User says payment confirmed but still limited
1. Check transaction status: `SELECT * FROM transactions WHERE order_reference = 'SUB-...'`
2. Check subscription: `SELECT * FROM subscriptions WHERE phone_hash = '...'`
3. Check logs: Look for `duplicate_webhook_ignored` or `payment_timeout_detected`

### Duplicate subscriptions
- **Should never happen** (idempotency prevents this)
- If it does: Check `transaction.status` guards in `transition_to_active_subscriber()`

### Free tier not resetting weekly
- Check `user_usage` table: `SELECT * FROM user_usage WHERE phone_hash = '...'`
- Week resets Sunday 00:00 UTC
- Verify timezone handling in `get_weekly_usage()`

---

## Database Tables

```sql
-- Core tables
transactions       -- Payment records (pending → paid)
subscriptions      -- Active/expired subscriptions
user_usage         -- Free tier tracking (weekly)

-- Key columns
transactions.status           -- 'pending', 'paid', 'expired', 'failed'
subscriptions.is_active       -- true/false
subscriptions.end_date        -- Expiry date (UTC)
subscriptions.auto_renew      -- true/false (CANCEL sets to false)
```

---

## Test Results

```
✅ test_state_machine_critical.py
   ✅ Duplicate webhook idempotency
   ✅ 15-minute timeout expiration
   ✅ CANCEL preserves access

✅ test_integration_flow.py
   ✅ New user → Free tier
   ✅ Limit reached → Upgrade prompt
   ✅ Subscribe → Pending payment
   ✅ Webhook → Active subscriber
   ✅ Unlimited access
   ✅ Duplicate webhook rejected
   ✅ STATUS command
   ✅ CANCEL command
```

---

## Production Checklist

- [x] All tests passing
- [x] Idempotency verified
- [x] Timeout handling verified
- [x] CANCEL behavior verified
- [x] Priority logic verified
- [x] Webhook integration complete
- [x] Diagnostic access control integrated
- [x] Timezone handling fixed

---

## Quick Deploy

```bash
# 1. Run tests
python test_state_machine_critical.py
python test_integration_flow.py

# 2. Verify environment
# - PAYNOW_INTEGRATION_ID
# - PAYNOW_INTEGRATION_KEY
# - SUPABASE_URL
# - SUPABASE_SERVICE_KEY

# 3. Deploy
# (Your deployment process here)

# 4. Monitor logs
# Watch for: state_transition, duplicate_webhook_ignored, payment_timeout_detected
```

---

## Need Help?

- **Full docs**: `STATE_MACHINE_INTEGRATION_COMPLETE.md`
- **Verification report**: `INTEGRATION_VERIFICATION_REPORT.md`
- **Test file**: `test_state_machine_critical.py`
- **Integration test**: `test_integration_flow.py`

---

**Status**: 🎉 Ready for production  
**Last Updated**: July 3, 2026
