# Paynow Integration - System Architecture

## System Overview

```
┌─────────────┐
│   WhatsApp  │
│    User     │
└──────┬──────┘
       │ Message
       ▼
┌──────────────────────────────────────────────────┐
│           Baileys WhatsApp Bridge                │
└──────────────────┬───────────────────────────────┘
                   │ HTTP POST
                   ▼
┌──────────────────────────────────────────────────┐
│             FastAPI Backend                      │
│  ┌────────────────────────────────────────────┐  │
│  │ Webhook Handler (app/api/routes/webhook.py)│  │
│  │                                             │  │
│  │ 1. Check idempotency                        │  │
│  │ 2. Check rate limit                         │  │
│  │ 3. Check payment access ◄──────┐            │  │
│  │ 4. Handle payment commands      │            │  │
│  │ 5. Process diagnostic           │            │  │
│  │ 6. Increment usage counter ─────┘            │  │
│  └─────────────┬───────────────────────────────┘  │
│                │                                   │
│  ┌─────────────▼───────────────────────────────┐  │
│  │    Payment Service                          │  │
│  │    (app/services/payment_service.py)        │  │
│  │                                             │  │
│  │  • check_user_access()                      │  │
│  │  • initiate_subscription_payment() ─────┐   │  │
│  │  • check_payment_status() ◄────────┐    │   │  │
│  │  • increment_user_usage()          │    │   │  │
│  └─────────────┬───────────────────────┼────┼───┘  │
│                │                       │    │      │
│  ┌─────────────▼───────────────────────┼────┼───┐  │
│  │    Payment Repository               │    │   │  │
│  │    (app/repositories/payment_repo)  │    │   │  │
│  │                                     │    │   │  │
│  │  • create_transaction()             │    │   │  │
│  │  • get_pending_transactions() ──────┘    │   │  │
│  │  • create_subscription()                 │   │  │
│  │  • check_access()                        │   │  │
│  │  • increment_usage()                     │   │  │
│  └─────────────┬─────────────────────────────┼───┘  │
│                │                             │      │
│  ┌─────────────▼─────────────────────────────┼───┐  │
│  │    Background Payment Poller            │   │  │
│  │    (app/services/payment_poller.py)     │   │  │
│  │                                         │   │  │
│  │  • Runs every 30 seconds                │   │  │
│  │  • Checks pending transactions ─────────┘   │  │
│  │  • Polls Paynow for status                  │  │
│  └─────────────┬─────────────────────────────────┘  │
│                │                                     │
└────────────────┼─────────────────────────────────────┘
                 │
     ┌───────────┼───────────┐
     │           │           │
     ▼           ▼           ▼
┌─────────┐ ┌─────────┐ ┌──────────────┐
│Supabase │ │ Paynow  │ │   Paynow     │
│Database │ │   API   │ │   Webhook    │
│         │ │         │ │   (HTTPS)    │
│• trans  │ │• init   │ │• confirms    │
│• subs   │ │• poll   │ │  payments    │
│• usage  │ │         │ │              │
└─────────┘ └─────────┘ └──────────────┘
```

---

## Payment Flow Diagram

```
User                    Backend                 Paynow              User's Phone
 |                         |                      |                      |
 | 1. Diagnostic Request   |                      |                      |
 |──────────────────────►  |                      |                      |
 |                         |                      |                      |
 |                         | 2. Check access      |                      |
 |                         |    (free limit?)     |                      |
 |                         |                      |                      |
 |  3. "Subscribe $2/mo"   |                      |                      |
 | ◄──────────────────────  |                      |                      |
 |                         |                      |                      |
 | 4. SUBSCRIBE cmd        |                      |                      |
 |──────────────────────►  |                      |                      |
 |                         |                      |                      |
 |                         | 5. Create transaction |                     |
 |                         |    (status=pending)  |                      |
 |                         |                      |                      |
 |                         | 6. sendMobile()      |                      |
 |                         |───────────────────► |                      |
 |                         |                      |                      |
 |                         |                      | 7. EcoCash USSD      |
 |                         |                      |─────────────────────►|
 |                         |                      |                      |
 |                         | 8. poll_url          |                      |
 |                         | ◄─────────────────── |                      |
 |                         |                      |                      |
 |  9. "Check phone..."    |                      |                      |
 | ◄──────────────────────  |                      |                      |
 |                         |                      |                      |
 |                         |                      |                      | 10. User approves
 |                         |                      |                      |     payment
 |                         |                      |                      |
 |                         |                      | 11. Payment processed|
 |                         |                      | ◄────────────────────|
 |                         |                      |                      |
 |                         | 12. Poll status      |                      |
 |                         |───────────────────► |                      |
 |                         |                      |                      |
 |                         | 13. Status: paid     |                      |
 |                         | ◄─────────────────── |                      |
 |                         |                      |                      |
 |                         | 14. Webhook POST     |                      |
 |                         | ◄─────────────────── |                      |
 |                         |                      |                      |
 |                         | 15. Create subscription                     |
 |                         |     Update transaction                      |
 |                         |     status=paid      |                      |
 |                         |                      |                      |
 | 16. "Payment confirmed" |                      |                      |
 | ◄──────────────────────  |                      |                      |
 |                         |                      |                      |
 | 17. Diagnostic Request  |                      |                      |
 |──────────────────────►  |                      |                      |
 |                         |                      |                      |
 |                         | 18. Check access     |                      |
 |                         |     (subscribed!)    |                      |
 |                         |                      |                      |
 | 19. Diagnostic Result   |                      |                      |
 | ◄──────────────────────  |                      |                      |
```

---

## Database Schema Diagram

```
┌──────────────────────────────────────────────────┐
│                transactions                      │
├──────────────────────────────────────────────────┤
│ id (PK)               UUID                       │
│ phone_hash            TEXT                       │
│ amount                DECIMAL(10,2)              │
│ currency              TEXT (USD)                 │
│ status                TEXT (pending/paid/...)    │
│ order_reference       TEXT UNIQUE                │
│ paynow_reference      TEXT                       │
│ poll_url              TEXT                       │
│ user_email            TEXT                       │
│ user_phone            TEXT                       │
│ subscription_type     TEXT (monthly)             │
│ subscription_start    TIMESTAMPTZ                │
│ subscription_end      TIMESTAMPTZ                │
│ created_at            TIMESTAMPTZ                │
│ paid_at               TIMESTAMPTZ                │
└────────────┬─────────────────────────────────────┘
             │ 1:1
             │
             ▼
┌──────────────────────────────────────────────────┐
│                subscriptions                     │
├──────────────────────────────────────────────────┤
│ id (PK)               UUID                       │
│ phone_hash (UNIQUE)   TEXT                       │
│ subscription_type     TEXT (monthly)             │
│ amount                DECIMAL(10,2)              │
│ currency              TEXT (USD)                 │
│ start_date            TIMESTAMPTZ                │
│ end_date              TIMESTAMPTZ                │
│ is_active             BOOLEAN                    │
│ transaction_id (FK) ──┘                          │
│ auto_renew            BOOLEAN                    │
│ created_at            TIMESTAMPTZ                │
└──────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────┐
│                 user_usage                       │
├──────────────────────────────────────────────────┤
│ id (PK)               UUID                       │
│ phone_hash            TEXT                       │
│ diagnostics_count     INT                        │
│ period_start          TIMESTAMPTZ (Monday 00:00) │
│ period_end            TIMESTAMPTZ (Sunday 23:59) │
│ was_subscribed        BOOLEAN                    │
│ created_at            TIMESTAMPTZ                │
└──────────────────────────────────────────────────┘

Indexes:
  • transactions(phone_hash)
  • transactions(order_reference)
  • transactions(status)
  • subscriptions(phone_hash)
  • subscriptions(end_date)
  • user_usage(phone_hash, period_start)
```

---

## Access Control Logic

```
┌────────────────────────────────┐
│ User sends diagnostic request │
└───────────┬────────────────────┘
            │
            ▼
┌────────────────────────────────┐
│ Check active subscription?     │
└───┬─────────────────────┬──────┘
    │ YES                 │ NO
    │                     │
    ▼                     ▼
┌────────────┐     ┌──────────────────┐
│ ALLOW      │     │ Check weekly      │
│ (unlimited)│     │ usage count       │
└────────────┘     └─────────┬────────┘
                             │
                ┌────────────┼────────────┐
                │            │            │
              < 5          = 5          > 5
                │            │            │
                ▼            ▼            ▼
         ┌──────────┐  ┌─────────┐  ┌────────┐
         │ ALLOW    │  │ ALLOW   │  │ DENY   │
         │ (free)   │  │ (last)  │  │ (limit)│
         │          │  │         │  │        │
         │ Increment│  │ Increment│ │ Show   │
         │ counter  │  │ counter │  │ payment│
         └──────────┘  └─────────┘  │ prompt │
                                    └────────┘
```

---

## Component Responsibilities

### Frontend (WhatsApp)
```
User sends:
  • Diagnostic codes (P0420)
  • SUBSCRIBE <email> <phone>
  • STATUS

User receives:
  • Diagnostic results
  • Payment prompts
  • Subscription confirmations
  • Status updates
```

### Backend (FastAPI)
```
app/api/routes/webhook.py
  • Receives WhatsApp messages
  • Checks payment access
  • Handles payment commands
  • Routes diagnostic requests
  • Increments usage counters

app/services/payment_service.py
  • Initiates Paynow payments
  • Polls payment status
  • Creates subscriptions
  • Manages access control

app/services/payment_commands.py
  • Parses SUBSCRIBE command
  • Handles STATUS command
  • Formats responses

app/services/payment_poller.py
  • Background task (every 30s)
  • Checks pending transactions
  • Polls Paynow API
  • Updates transaction status
```

### Database (Supabase)
```
transactions table
  • Payment records
  • Status tracking
  • Paynow references

subscriptions table
  • Active subscriptions
  • Start/end dates
  • One per user

user_usage table
  • Weekly diagnostic counts
  • Free tier tracking
  • Auto-resets Monday 00:00 UTC
```

### External (Paynow)
```
Paynow API
  • sendMobile() - Initiate EcoCash payment
  • checkTransactionStatus() - Poll status
  • Webhook - Post payment confirmations

EcoCash
  • USSD prompt on user's phone
  • User enters PIN to approve
  • Payment processed
```

---

## Data Flow: Free Tier

```
1. First diagnostic (count=0):
   ├─> Check subscription: No
   ├─> Check usage: 0/5
   ├─> Allow: Yes
   ├─> Increment: 1
   └─> Return: Diagnostic result

2. Fifth diagnostic (count=4):
   ├─> Check subscription: No
   ├─> Check usage: 4/5
   ├─> Allow: Yes (last free)
   ├─> Increment: 5
   └─> Return: Diagnostic result

3. Sixth diagnostic (count=5):
   ├─> Check subscription: No
   ├─> Check usage: 5/5
   ├─> Allow: No (limit exceeded)
   └─> Return: Payment prompt

4. Monday 00:00 UTC:
   ├─> New week starts
   ├─> Usage counter: 0
   └─> User gets 5 more free
```

---

## Data Flow: Subscription

```
1. User subscribes:
   ├─> SUBSCRIBE command
   ├─> Create transaction (pending)
   ├─> Call Paynow sendMobile()
   ├─> Get poll_url
   ├─> Return: Instructions to user

2. User approves on phone:
   ├─> EcoCash USSD prompt
   ├─> User enters PIN
   ├─> Payment processed by EcoCash
   └─> Paynow receives confirmation

3. Backend polls (every 30s):
   ├─> Get pending transactions
   ├─> For each: Check status
   ├─> If paid: Create subscription
   └─> Update transaction status

4. Webhook receives confirmation:
   ├─> Paynow POSTs to /webhook/paynow
   ├─> Validate hash
   ├─> Process payment
   └─> Definitive confirmation

5. User gets unlimited access:
   ├─> Subscription active
   ├─> end_date = start + 30 days
   ├─> No usage limits
   └─> Can send unlimited diagnostics
```

---

## Error Handling

```
Payment Initiation Errors:
  ├─> Invalid phone/email format
  │   └─> Return: Validation error
  ├─> Paynow API error
  │   └─> Log error, retry, or fail gracefully
  └─> Database error
      └─> Rollback transaction, return error

Payment Confirmation Errors:
  ├─> Hash verification fails
  │   └─> Log security warning, reject
  ├─> Polling timeout
  │   └─> Mark as expired after 15 minutes
  └─> Webhook missed
      └─> Polling catches it anyway

Access Control Errors:
  ├─> Database unavailable
  │   └─> Log error, allow access (graceful degradation)
  ├─> Usage increment fails
  │   └─> Log warning, continue
  └─> Subscription query fails
      └─> Log error, check free tier
```

---

## Monitoring Points

```
Metrics to Track:
┌────────────────────────────────────┐
│ 1. Payment Success Rate            │
│    • Initiated / Confirmed         │
│    • Target: >90%                  │
├────────────────────────────────────┤
│ 2. Payment Confirmation Time       │
│    • p50, p95, p99                 │
│    • Target: <30s                  │
├────────────────────────────────────┤
│ 3. Free → Paid Conversion          │
│    • Hit limit / Subscribed        │
│    • Target: >10%                  │
├────────────────────────────────────┤
│ 4. Active Subscriptions            │
│    • Total count                   │
│    • Growth rate                   │
├────────────────────────────────────┤
│ 5. Churn Rate                      │
│    • Expired / Total               │
│    • Target: <50%                  │
└────────────────────────────────────┘

Alerts to Set Up:
  • Payment success rate <80%
  • Payment confirmation >2 minutes
  • Webhook not received >1 hour
  • Database errors
  • Paynow API errors
```

---

## Security Measures

```
1. Hash Verification (SHA512)
   ├─> All Paynow responses validated
   ├─> Concatenate: values + integration_key
   ├─> Compare: computed_hash == received_hash
   └─> Reject if mismatch

2. Phone Number Hashing (SHA-256)
   ├─> Hash before storage
   ├─> Never store plaintext
   └─> Consistent across tables

3. Integration Key Protection
   ├─> Never logged
   ├─> Never exposed in API
   ├─> Only in .env (not committed)
   └─> Only used for hash computation

4. Idempotency Checks
   ├─> Message IDs tracked
   ├─> Duplicate requests ignored
   └─> Prevents double-charging

5. HTTPS Required
   ├─> Webhook URL must be HTTPS
   ├─> Paynow enforces SSL
   └─> Prevents man-in-the-middle
```

---

**Architecture Status:** Complete ✅  
**Integration Pattern:** REST API + Webhook + Background Polling  
**Payment Provider:** Paynow Zimbabwe (EcoCash)  
**Deployment:** Ready for production
