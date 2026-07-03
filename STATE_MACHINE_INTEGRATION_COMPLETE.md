# State Machine Integration Complete ✅

**Date**: July 3, 2026  
**Status**: State machine fully integrated into webhook and diagnostic access flow

---

## 🎯 What Was Verified

### 1. ✅ Critical Test Results

All three critical tests passing in `test_state_machine_critical.py`:

#### Test 1: Duplicate Webhook Idempotency
- **Scenario**: Webhook fires twice for same order (network retry)
- **Result**: Second webhook ignored, no duplicate subscription
- **Mechanism**: `transaction.status == 'pending'` check in `transition_to_active_subscriber()`
- **Outcome**: Only ONE subscription created, expiry date unchanged

#### Test 2: 15-Minute Pending Timeout
- **Scenario**: Pending transaction created 16 minutes ago
- **Result**: Auto-expired on next `resolve_state()` call
- **Mechanism**: Check `created_at < (now - 15 minutes)` in `resolve_state()`
- **Outcome**: Transaction status → 'expired', state → FREE_TIER/NEW_USER

#### Test 3: CANCEL Preserves Access
- **Scenario**: User cancels auto-renewal
- **Result**: Access preserved until expiry date
- **Mechanism**: Sets `auto_renew=false`, keeps `is_active=true`, `end_date` unchanged
- **Outcome**: User keeps unlimited access until expiry, not revoked immediately

---

### 2. ✅ Priority Logic Analysis

**Question**: What happens if user has BOTH active subscription AND pending transaction?

**Answer**: Active subscription ALWAYS wins (deterministic)

**Resolution Order** in `user_state_machine.py:resolve_state()`:
```
1. Active subscription (is_active=true, end_date > now)
   → RETURN ACTIVE_SUBSCRIBER (line 121-145)
   
2. Pending transaction (status='pending', created < 15min)
   → RETURN PENDING_PAYMENT (line 156-204)
   
3. Expired subscription (is_active=false)
   → RETURN EXPIRED
   
4. Free tier usage > 0
   → RETURN FREE_TIER
   
5. No records
   → RETURN NEW_USER
```

**Why deterministic:**
- Active subscription check comes FIRST
- If found, immediately RETURNS (line 136)
- Pending transaction check never executes
- Same inputs → same output (no race conditions)

**Why correct:**
- User already has unlimited access
- No need to wait for renewal payment
- Clear user experience

---

### 3. ✅ Integration Points

All three integration points now connected:

#### A. Baileys Message Webhook (`app/api/routes/webhook.py`)

**Changes:**
1. Added imports:
   ```python
   from app.services.user_state_machine import UserStateMachine
   from app.services.payment_command_handlers import PaymentCommandHandler
   ```

2. Added dependency injectors (lines 53-67):
   ```python
   def get_state_machine(repos: dict = Depends(get_repositories)):
       return UserStateMachine(repos["payment_repo"])
   
   def get_command_handler(...):
       state_machine = UserStateMachine(repos["payment_repo"])
       return PaymentCommandHandler(state_machine, payment_service)
   ```

3. Updated `_check_payment_access()` (lines 151-237):
   - Now uses `state_machine.resolve_state()` instead of old `payment_service.check_user_access()`
   - Returns tuple: `(error_message, user_state)`
   - State-aware error messages (different for PENDING_PAYMENT, EXPIRED, FREE_TIER)

4. Updated `baileys_webhook()` (lines 409-646):
   - Added `state_machine` and `command_handler` dependencies
   - Replaced old payment command imports with new command handler calls
   - All commands now use:
     - `command_handler.parse_subscribe_or_renew()`
     - `command_handler.handle_subscribe_or_renew()`
     - `command_handler.parse_status()` / `handle_status()`
     - `command_handler.parse_cancel()` / `handle_cancel()`
     - `command_handler.parse_help()` / `handle_help()`

#### B. Paynow Payment Webhook (`app/api/routes/payments.py`)

**Changes:**
1. Added import:
   ```python
   from app.services.user_state_machine import UserStateMachine
   ```

2. Updated `paynow_webhook()` (lines 117-191):
   - Added state machine initialization
   - When payment confirmed (`status_response.paid`):
     - Gets transaction and phone_hash
     - Calls `state_machine.transition_to_active_subscriber()`
     - **Idempotent**: duplicate webhooks automatically ignored
     - Logs success/already-processed appropriately

**Flow:**
```
Paynow webhook fires
  ↓
Validate with Paynow SDK
  ↓
If paid:
  - Get transaction by order_reference
  - Call state_machine.transition_to_active_subscriber()
  - Check: transaction.status == 'pending'?
    - YES: Update to 'paid', create subscription → ACTIVE_SUBSCRIBER
    - NO: Log warning, return early (already processed)
```

#### C. Diagnostic Access Check

**Flow in `baileys_webhook()`:**
```
1. Resolve state (line 469-472):
   payment_access_msg, user_state = await _check_payment_access(
       state_machine, phone_hash, raw_text
   )

2. Check access (line 473-485):
   if payment_access_msg:
       # Access denied - return upgrade prompt
       repos["message_repo"].insert_audit(...)
       return {"reply": payment_access_msg, "status": "payment_required"}

3. If allowed, continue to diagnostic routing (line 487+)
```

**Access Logic:**
- `state.can_access_diagnostic` determines access
  - ACTIVE_SUBSCRIBER: Always `True` (unlimited)
  - PENDING_PAYMENT: `True` if free tier remaining
  - EXPIRED: `True` if free tier remaining
  - FREE_TIER: `True` if `usage < 5`
  - NEW_USER: Always `True` (first 5 free)

---

## 📊 State Machine Summary

### States
- **NEW_USER**: First message, no usage yet
- **FREE_TIER**: Used 1-4 diagnostics this week
- **PENDING_PAYMENT**: Payment initiated, waiting for EcoCash approval (15min timeout)
- **ACTIVE_SUBSCRIBER**: Paid subscription, unlimited access
- **EXPIRED**: Subscription expired, falls back to FREE_TIER

### Transitions
```
NEW_USER → FREE_TIER
  (first diagnostic)

FREE_TIER → PENDING_PAYMENT
  (SUBSCRIBE command OR limit hit)

PENDING_PAYMENT → ACTIVE_SUBSCRIBER
  (Paynow webhook confirms payment)

PENDING_PAYMENT → FREE_TIER
  (15min timeout OR payment declined)

ACTIVE_SUBSCRIBER → EXPIRED
  (expiry_date passes)

EXPIRED → PENDING_PAYMENT
  (RENEW command)
```

### Key Design Decisions

1. **Derived State**: State calculated from database records, not stored separately
2. **Idempotent Webhooks**: `transaction.status` guards state transitions
3. **Expired = Free Tier**: Expired users fall back to 5/week, not blocked
4. **Timeout on Access**: Check transaction age on every `resolve_state()` call
5. **CANCEL Behavior**: Sets `auto_renew=false`, keeps access until expiry
6. **Timezone-Aware**: All datetime comparisons use `_utcnow()` (timezone-aware)

---

## 🔧 Commands Available

### SUBSCRIBE / RENEW
```
SUBSCRIBE <email> <phone>
RENEW <email> <phone>
```
- Validates email and Zimbabwe phone format
- Creates pending transaction
- Calls Paynow API (EcoCash prompt)
- Transitions to PENDING_PAYMENT

### STATUS
```
STATUS
```
- Shows current state
- State-aware response (different for each state)
- Shows expiry, usage, auto-renew status

### CANCEL
```
CANCEL
```
- Only works in ACTIVE_SUBSCRIBER state
- Sets `auto_renew=false`
- Keeps access until expiry
- Clear message about retention period

### HELP
```
HELP
```
- Context-aware help message
- Shows commands relevant to current state

---

## 🚀 Files Modified

### Core State Machine
- ✅ `app/services/user_state_machine.py` - State resolution and transitions
- ✅ `app/services/payment_command_handlers.py` - Command parsing and handling

### Integration Points
- ✅ `app/api/routes/webhook.py` - Baileys webhook (message handling)
- ✅ `app/api/routes/payments.py` - Paynow webhook (payment confirmation)

### Repository
- ✅ `app/repositories/payment_repository.py` - Added state machine queries

### Bug Fixes
- ✅ `app/services/payment_service.py` - Fixed datetime parsing in `cancel_subscription()`

### Tests
- ✅ `test_state_machine_critical.py` - All 3 critical tests passing

---

## ✅ Verification Checklist

- [x] Duplicate webhook idempotency verified
- [x] 15-minute pending timeout verified
- [x] CANCEL preserves access verified
- [x] Priority logic (active subscription wins) confirmed
- [x] State machine integrated into Baileys webhook
- [x] State machine integrated into Paynow webhook
- [x] Diagnostic access check uses state machine
- [x] Payment commands routed to command handler
- [x] Timezone-aware datetime comparisons
- [x] All tests passing

---

## 🎉 Ready for Production

The state machine is now fully integrated and verified:

1. **Single Source of Truth**: `resolve_state()` called at top of every message
2. **Idempotent**: Duplicate webhooks safe, no double-processing
3. **Deterministic**: Same inputs → same outputs
4. **Tested**: All critical scenarios verified
5. **Integrated**: Webhook, diagnostic access, and payment confirmation all connected

---

## 📝 Next Steps (Optional)

1. **Monitoring**: Add metrics for state transitions
2. **Background Job**: Optional poller for pending transactions (currently check-on-access)
3. **User Notifications**: Send WhatsApp message when payment confirmed
4. **Admin Dashboard**: View user states and transitions

---

## 🐛 Known Edge Cases (Handled)

1. **User has both active subscription and pending renewal**: Active subscription wins (deterministic)
2. **Webhook fires twice**: Second ignored (idempotent via status check)
3. **Payment times out**: Auto-expires after 15min on next access
4. **Subscription expires**: Auto-marks expired on next access, falls back to free tier
5. **User cancels**: Access preserved until expiry date
6. **Timezone mismatches**: All comparisons use timezone-aware UTC

---

**Status**: 🎉 **INTEGRATION COMPLETE AND VERIFIED**
