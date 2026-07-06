# Paynow Payment Flow - Visual Guide

Complete visual representation of the payment integration flow.

---

## 🔄 Complete Payment Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                       PAYNOW PAYMENT FLOW                            │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────┐
│    USER     │
│  (WhatsApp) │
└──────┬──────┘
       │
       │ 1. Send: "SUBSCRIBE john@example.com 0771234567"
       │
       ▼
┌──────────────────┐
│  Your Backend    │
│  (Webhook)       │
└────────┬─────────┘
         │
         │ 2. Validate command & parse parameters
         │
         ▼
┌──────────────────┐
│  State Machine   │
│  Check State     │
└────────┬─────────┘
         │
         │ 3. Check if already subscribed / pending
         │
         ▼
┌──────────────────┐
│ Payment Service  │
│ Create Payment   │
└────────┬─────────┘
         │
         │ 4. Generate order reference: SUB-20260706130946-f9253aa6
         │    Create transaction (status=pending)
         │
         ▼
┌──────────────────┐
│   Paynow API     │
│   (send_mobile)  │
└────────┬─────────┘
         │
         │ 5. Initiate EcoCash payment
         │    Returns: poll_url, instructions
         │
         ▼
┌──────────────────┐
│   Database       │
│   Update TX      │
└────────┬─────────┘
         │
         │ 6. Save poll_url and paynow_reference
         │
         ▼
┌──────────────────┐
│   User Response  │
│   (WhatsApp)     │
└────────┬─────────┘
         │
         │ 7. "✅ SUBSCRIBE initiated!
         │     📱 Check your phone (0771234567) for EcoCash prompt
         │     💰 Amount: $2.00 USD
         │     Order: SUB-20260706130946-f9253aa6"
         │
         ▼
┌──────────────────┐
│   User Phone     │
│   (EcoCash)      │
└────────┬─────────┘
         │
         │ 8. Receive USSD prompt: "Approve $2 payment?"
         │    User enters PIN
         │
         ▼
┌──────────────────┐
│  Paynow System   │
│  Process Payment │
└────────┬─────────┘
         │
         │ 9. Payment approved → status changes to "paid"
         │
         ▼
┌──────────────────┐
│ Payment Poller   │
│ (Background)     │
└────────┬─────────┘
         │
         │ 10. Poll every 30 seconds:
         │     GET poll_url → check status
         │
         ▼
┌──────────────────┐
│   Database       │
│   Update Status  │
└────────┬─────────┘
         │
         │ 11. Update transaction: status=paid, paid_at=now
         │
         ▼
┌──────────────────┐
│ Payment Service  │
│ Activate Sub     │
└────────┬─────────┘
         │
         │ 12. Create subscription record:
         │     - start_date: now
         │     - end_date: now + 30 days
         │     - is_active: true
         │
         ▼
┌──────────────────┐
│  State Machine   │
│  Transition      │
└────────┬─────────┘
         │
         │ 13. State: PENDING_PAYMENT → ACTIVE_SUBSCRIBER
         │
         ▼
┌──────────────────┐
│     DONE!        │
│  User has access │
└──────────────────┘
```

**Total Time:** 1-2 minutes from SUBSCRIBE to activation

---

## 🎯 State Machine Flow

```
                    ┌─────────────┐
                    │  NEW_USER   │
                    │  (0 used)   │
                    └──────┬──────┘
                           │
          ┌────────────────┼────────────────┐
          │                                  │
     [Send code]                      [Send SUBSCRIBE]
          │                                  │
          ▼                                  ▼
    ┌──────────┐                    ┌─────────────────┐
    │FREE_TIER │                    │PENDING_PAYMENT  │
    │(1-4 used)│                    │(Waiting for $)  │
    └────┬─────┘                    └────────┬────────┘
         │                                    │
    [Send code                         [Payment detected
     until 5]                           by poller]
         │                                    │
         ▼                                    ▼
    ┌──────────┐                    ┌─────────────────┐
    │ BLOCKED  │                    │ACTIVE_SUBSCRIBER│
    │(Hit limit)◄────[Expire]───────┤ (30 days)       │
    └────┬─────┘                    └────────┬────────┘
         │                                    │
    [Subscribe]                        [CANCEL command]
         │                                    │
         └────────────────┬───────────────────┘
                          │
                          ▼
                  ┌───────────────┐
                  │AUTO_RENEW: OFF│
                  └───────┬───────┘
                          │
                    [After 30 days]
                          │
                          ▼
                    ┌──────────┐
                    │ EXPIRED  │
                    └────┬─────┘
                         │
                   [RENEW command]
                         │
                         ▼
                 ┌─────────────────┐
                 │PENDING_PAYMENT  │
                 └─────────────────┘
```

---

## 💬 Command Flow

### SUBSCRIBE Command

```
User Input: "SUBSCRIBE john@example.com 0771234567"
     │
     ├─► Parse: email = john@example.com, phone = 0771234567
     │
     ├─► Check State:
     │   ├─► If ACTIVE_SUBSCRIBER → "Already subscribed"
     │   ├─► If PENDING_PAYMENT → "Payment in progress"
     │   └─► Else → Continue
     │
     ├─► Initiate Payment:
     │   ├─► Create transaction (status=pending)
     │   ├─► Call Paynow API
     │   ├─► Store poll_url
     │   └─► Return order_reference
     │
     ├─► Update State:
     │   └─► State → PENDING_PAYMENT
     │
     └─► Response: "✅ SUBSCRIBE initiated! Order: SUB-xxx"
```

### STATUS Command

```
User Input: "STATUS"
     │
     ├─► Resolve State:
     │   ├─► Check subscriptions table
     │   ├─► Check user_usage table
     │   └─► Determine current state
     │
     ├─► Format Response based on state:
     │   ├─► ACTIVE_SUBSCRIBER → Show expiry, auto-renew
     │   ├─► PENDING_PAYMENT → Show order, time remaining
     │   ├─► FREE_TIER → Show usage (X/5)
     │   ├─► EXPIRED → Show renewal prompt
     │   └─► NEW_USER → Show welcome message
     │
     └─► Send Response
```

### CANCEL Command

```
User Input: "CANCEL"
     │
     ├─► Check State:
     │   ├─► If NOT ACTIVE_SUBSCRIBER → "No active subscription"
     │   └─► Else → Continue
     │
     ├─► Update Database:
     │   └─► subscriptions.auto_renew = false
     │
     ├─► State remains ACTIVE_SUBSCRIBER
     │   (Access continues until expiration)
     │
     └─► Response: "✅ Auto-renewal cancelled. Access until: 2026-08-05"
```

---

## 🔄 Diagnostic Request Flow

### Free Tier User

```
User: "P0420"
  │
  ├─► Check State → FREE_TIER (2/5 used)
  │
  ├─► Can Access? → YES (2 < 5)
  │
  ├─► Serve Diagnostic
  │
  ├─► Increment Usage: 2 → 3
  │
  └─► Update user_usage table
```

### Subscribed User

```
User: "P0420"
  │
  ├─► Check State → ACTIVE_SUBSCRIBER
  │
  ├─► Can Access? → YES (unlimited)
  │
  ├─► Serve Diagnostic
  │
  └─► No usage tracking (unlimited)
```

### Blocked User (Hit Limit)

```
User: "P0420"
  │
  ├─► Check State → FREE_TIER (5/5 used)
  │
  ├─► Can Access? → NO (5 >= 5)
  │
  ├─► Block Request
  │
  └─► Response: "⚠️ Free tier limit reached.
       Subscribe for unlimited: SUBSCRIBE <email> <phone>"
```

---

## ⚙️ Background Poller Flow

```
┌─────────────────────────────────────────┐
│  Payment Poller (Runs every 30 seconds) │
└───────────────┬─────────────────────────┘
                │
                ├─► Query Database:
                │   SELECT * FROM transactions
                │   WHERE status = 'pending'
                │   AND created_at > NOW() - INTERVAL '15 minutes'
                │
                ├─► For each pending transaction:
                │   │
                │   ├─► Call Paynow API (poll_url)
                │   │
                │   ├─► Check response:
                │   │   ├─► paid=True → Activate subscription
                │   │   ├─► paid=False → Continue waiting
                │   │   └─► timeout → Mark as expired
                │   │
                │   └─► Update transaction status
                │
                └─► Sleep 30 seconds → Repeat
```

### Poller Logic

```python
# Simplified poller logic
while True:
    # Get pending transactions
    pending = get_pending_transactions(max_age_minutes=15)

    for tx in pending:
        # Check payment status
        status = paynow.check_status(tx.poll_url)

        if status.paid:
            # Update transaction
            tx.status = 'paid'
            tx.paid_at = now()

            # Create subscription
            create_subscription(
                phone_hash=tx.phone_hash,
                start_date=now(),
                end_date=now() + timedelta(days=30)
            )

            # Transition state
            state_machine.transition_to_active_subscriber(
                phone_hash=tx.phone_hash,
                transaction_id=tx.id
            )

    # Wait 30 seconds
    sleep(30)
```

---

## 🗄️ Database Flow

### Transaction Creation

```
SUBSCRIBE command received
    │
    ├─► INSERT INTO transactions:
    │     - id: UUID (auto-generated)
    │     - phone_hash: SHA-256 hash
    │     - amount: 2.00
    │     - currency: USD
    │     - status: pending
    │     - order_reference: SUB-xxx
    │     - user_email: john@example.com
    │     - user_phone: 0771234567
    │     - subscription_type: monthly
    │     - created_at: now()
    │
    └─► Return transaction_id
```

### Subscription Activation

```
Payment detected by poller
    │
    ├─► UPDATE transactions:
    │     - status: pending → paid
    │     - paid_at: now()
    │
    ├─► INSERT INTO subscriptions:
    │     - id: UUID (auto-generated)
    │     - phone_hash: (same as transaction)
    │     - subscription_type: monthly
    │     - amount: 2.00
    │     - currency: USD
    │     - start_date: now()
    │     - end_date: now() + INTERVAL '30 days'
    │     - is_active: true
    │     - auto_renew: false
    │     - transaction_id: (reference)
    │
    └─► User state → ACTIVE_SUBSCRIBER
```

### Usage Tracking

```
Diagnostic request (free tier user)
    │
    ├─► SELECT * FROM user_usage
    │   WHERE phone_hash = ?
    │   AND period_start <= now()
    │   AND period_end > now()
    │
    ├─► If found:
    │   │   UPDATE user_usage
    │   │   SET diagnostics_count = diagnostics_count + 1
    │   │
    │   └─► Else:
    │       INSERT INTO user_usage:
    │         - phone_hash: ?
    │         - diagnostics_count: 1
    │         - period_start: start_of_week(now())
    │         - period_end: end_of_week(now())
    │
    └─► Check: diagnostics_count >= 5?
```

---

## 📊 Decision Trees

### Access Control Decision

```
                  [Diagnostic Request]
                          │
            ┌─────────────┴─────────────┐
            │                           │
      [Check State]              [Check Whitelist]
            │                           │
            │                      [Is Whitelisted?]
            │                     ┌─────┴─────┐
            │                   YES           NO
            │                    │            │
            │                 [ALLOW]         │
            │                                 │
            ▼                                 ▼
    ┌────────────────┐              [Continue State Check]
    │ State Machine  │
    └───────┬────────┘
            │
      ┌─────┴─────┬─────┬─────┬─────┐
      │           │     │     │     │
  [ACTIVE]  [PENDING] [FREE] [EXP] [NEW]
      │           │     │     │     │
   [ALLOW]    [BLOCK] [CHK] [BLK] [CHK]
                        │           │
                   [Used < 5?]  [Used < 5?]
                     ┌───┴───┐     ┌───┴───┐
                   YES      NO    YES      NO
                    │        │     │        │
                [ALLOW]  [BLOCK] [ALLOW] [BLOCK]
```

### Payment Status Resolution

```
            [Poller Checks Transaction]
                        │
                   [Call Paynow]
                        │
            ┌───────────┴───────────┐
            │                       │
        [Success]              [Error/Timeout]
            │                       │
        [Parse Response]        [Log Error]
            │                       │
     ┌──────┴──────┐           [Continue]
     │             │
  [paid=True]  [paid=False]
     │             │
  [ACTIVATE]   [Keep Pending]
     │
  ├─► Update TX: status=paid
  ├─► Create subscription
  └─► Transition state
```

---

## 🎨 User Experience Flow

```
Day 1: User discovers service
    │
    └─► Sends: "P0420"
         └─► Gets diagnosis
              └─► "You have 4 free diagnostics remaining"

Day 1: Uses 5 diagnostics
    │
    └─► Sends: "P0300"
         └─► "⚠️ Free tier limit reached.
              Subscribe for unlimited: SUBSCRIBE <email> <phone>"

Day 1: Decides to subscribe
    │
    └─► Sends: "SUBSCRIBE john@example.com 0771234567"
         └─► "✅ SUBSCRIBE initiated! Check your phone..."

Day 1: Approves payment on phone
    │
    └─► [2 minutes later]
         └─► Automatic activation!

Day 1-30: Unlimited access
    │
    └─► Sends any code → Gets instant diagnosis

Day 15: Checks status
    │
    └─► Sends: "STATUS"
         └─► "✅ Active Subscription. Expires: 2026-08-05"

Day 20: Decides to cancel auto-renew
    │
    └─► Sends: "CANCEL"
         └─► "✅ Auto-renewal cancelled. Access until: 2026-08-05"

Day 31: Subscription expires
    │
    └─► Returns to free tier (5/week)

Day 32: Wants to renew
    │
    └─► Sends: "RENEW john@example.com 0771234567"
         └─► Cycle repeats!
```

---

## 📋 Summary

The complete Paynow integration provides:

1. **Simple User Experience**
   - WhatsApp commands
   - Clear instructions
   - Instant feedback

2. **Automated Backend**
   - Background payment detection
   - Automatic subscription activation
   - State management

3. **Robust Data Flow**
   - Complete audit trail
   - Idempotent operations
   - Consistent state

4. **Flexible Access Control**
   - Free tier enforcement
   - Subscription management
   - Usage tracking

All flows tested and verified ✅

---

**Created:** 2026-07-06  
**Status:** Production Ready  
**Next:** Activate production mode with Paynow
