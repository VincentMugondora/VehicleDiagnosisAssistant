# Paynow Payment Integration Guide

## Overview

This WhatsApp diagnostic bot now includes **Paynow EcoCash mobile payments** for subscription management.

**Pricing Model:**
- 5 free diagnostics per week
- After free limit: $2/month subscription for unlimited diagnostics

**Payment Flow:**
1. User hits free limit
2. Bot prompts to subscribe via EcoCash
3. User sends SUBSCRIBE command with email + phone
4. Paynow initiates EcoCash USSD prompt on user's phone
5. User approves payment on phone
6. Backend polls Paynow + webhook confirms payment
7. Subscription activated, user gets unlimited access

---

## Setup Instructions

### 1. Get Paynow Credentials

Your client needs to provide these credentials from their Paynow merchant account:

1. **Go to:** https://www.paynow.co.zw/ (Paynow Zimbabwe)
2. **Login** to merchant account
3. **Navigate to:** Settings → Integration
4. **Copy:**
   - Integration ID (numeric, e.g., `12345`)
   - Integration Key (long secret string)

### 2. Configure Environment Variables

Add to your `.env` file (NOT `.env.example` - keep client credentials private):

```bash
# Paynow Payments (from client's Paynow account)
PAYNOW_INTEGRATION_ID=12345
PAYNOW_INTEGRATION_KEY=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
PAYNOW_RETURN_URL=https://your-domain.com/payments/return
PAYNOW_RESULT_URL=https://your-domain.com/webhook/paynow

# Payment Config (adjust if needed)
SUBSCRIPTION_PRICE=2.00
FREE_DIAGNOSTICS_LIMIT=5
FREE_DIAGNOSTICS_WINDOW_DAYS=7
```

**Important URLs:**
- `PAYNOW_RETURN_URL`: Where users are redirected after web payments (less relevant for mobile, but required by SDK)
- `PAYNOW_RESULT_URL`: Your webhook endpoint where Paynow sends payment confirmations - **MUST be public HTTPS URL**

### 3. Run Database Migration

Execute the SQL migration in your Supabase SQL Editor:

```bash
# File: migrations/add_payments_tables.sql
```

This creates:
- `transactions` table (payment records)
- `subscriptions` table (active subscriptions)
- `user_usage` table (free tier tracking)
- Helper functions for access control

### 4. Configure Paynow Webhook

In your Paynow merchant dashboard:

1. Go to Settings → Integration
2. Set **Result URL** to: `https://your-domain.com/webhook/paynow`
3. Make sure this URL is:
   - **Public** (not localhost)
   - **HTTPS** (Paynow requires SSL)
   - **Reachable** from internet

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs the `paynow` Python SDK.

### 6. Test the Integration

```bash
# Start backend
uvicorn app.main:app --reload --port 8000

# Test payment API
curl http://localhost:8000/payments/test

# Expected response:
# {"status": "ok", "message": "Payments API is running", "paynow_configured": true}
```

---

## How It Works

### For Users

**Free Tier:**
- New user gets 5 free diagnostics per week
- Counter resets every Monday at midnight UTC

**Hitting Limit:**
When user sends 6th diagnostic request in a week:
```
You've used all 5 free diagnostics this week.

📱 Subscribe for unlimited diagnostics!
💵 Only $2/month

To subscribe, reply with:
SUBSCRIBE [your email] [your EcoCash number]

Example:
SUBSCRIBE john@example.com 0771234567
```

**Subscribing:**
User sends:
```
SUBSCRIBE john@example.com 0771234567
```

Bot responds:
```
✅ Payment initiated!

📱 Check your phone for EcoCash prompt
💰 Amount: $2.00 USD
🎯 Plan: Monthly Unlimited

*124*4*3# - Dial to complete payment

⏱️ You have 5 minutes to approve the payment.

Order: SUB-20260703-abc123

Reply STATUS to check payment progress.
```

**Completing Payment:**
1. User's phone receives EcoCash USSD prompt (*124*4*3#)
2. User enters EcoCash PIN to approve
3. Payment processes (5-30 seconds typically)
4. Bot automatically detects payment
5. Subscription activated

**Checking Status:**
User sends:
```
STATUS
```

Bot responds:
```
✅ Active Subscription

📱 Plan: Monthly Unlimited
🎯 Status: Active
📅 Expires: 2026-08-03 10:30 UTC

You have unlimited diagnostics until expiration.
```

### Backend Flow

**1. Access Control:**
```python
# Before every diagnostic request
access_info = payment_service.check_user_access(phone_hash)

if not access_info["can_access"]:
    # User hit limit - show subscription prompt
    return payment_prompt_message
```

**2. Payment Initiation:**
```python
# User sends SUBSCRIBE command
result = await payment_service.initiate_subscription_payment(
    user_phone="0771234567",
    user_email="john@example.com",
    subscription_type="monthly"
)

# Creates:
# - Transaction record (status=pending)
# - Paynow API call (EcoCash USSD prompt)
# - Returns poll_url for status checking
```

**3. Payment Polling:**
```python
# Background task runs every 30 seconds
pending_transactions = payment_repo.get_pending_transactions()

for transaction in pending_transactions:
    status = await payment_service.check_payment_status(order_reference)

    if status["status"] == "paid":
        # Create subscription
        # Update transaction
        # User gets unlimited access
```

**4. Webhook Confirmation:**
```python
# Paynow posts to /webhook/paynow when payment completes
@router.post("/webhook/paynow")
async def paynow_webhook(request: Request):
    data = await request.form()
    status = paynow.process_status_update(data)

    if status.paid:
        # Definitive confirmation
        # Process payment
```

---

## API Endpoints

### Payment Initiation
```bash
POST /payments/initiate
Content-Type: application/json

{
  "user_phone": "0771234567",
  "user_email": "john@example.com",
  "subscription_type": "monthly"
}

Response:
{
  "success": true,
  "order_reference": "SUB-20260703-abc123",
  "poll_url": "https://www.paynow.co.zw/interface/querytransaction?guid=...",
  "instructions": "*124*4*3# - Dial to complete payment",
  "transaction_id": "uuid"
}
```

### Payment Status
```bash
GET /payments/status/{order_reference}

Response:
{
  "status": "paid",
  "amount": 2.00,
  "order_reference": "SUB-20260703-abc123",
  "paynow_reference": "123456",
  "paid_at": "2026-07-03T10:30:00Z",
  "subscription_end_date": "2026-08-03T10:30:00Z"
}
```

### Access Check
```bash
GET /payments/access-check/0771234567

Response:
{
  "can_access": true,
  "reason": "subscribed",
  "diagnostics_used": 0,
  "diagnostics_remaining": -1,
  "subscription_end_date": "2026-08-03T10:30:00Z"
}
```

### Paynow Webhook
```bash
POST /webhook/paynow
(Paynow sends form data automatically)
```

---

## WhatsApp Commands

Users can send these commands via WhatsApp:

### SUBSCRIBE
```
SUBSCRIBE john@example.com 0771234567
```
Initiates subscription payment via EcoCash.

### STATUS
```
STATUS
```
Shows current subscription status or free tier usage.

---

## Security Features

### 1. Hash Verification
All Paynow responses are validated using SHA512 hash:
```python
# SDK automatically validates
status = paynow.check_transaction_status(poll_url)
# Raises HashMismatchException if tampered
```

### 2. Credential Protection
- Integration key never logged or exposed
- Phone numbers hashed (SHA-256) before storage
- Sensitive payment data not logged in plaintext

### 3. Idempotency
- Duplicate messages ignored
- Transaction references unique
- Prevents double-charging

### 4. Rate Limiting
- Original USAGE_LIMIT still active (abuse prevention)
- Payment limits separate from free tier limits

---

## Database Schema

### transactions
```sql
id                   UUID PRIMARY KEY
phone_hash           TEXT (SHA-256 of user phone)
amount               DECIMAL(10, 2)
currency             TEXT DEFAULT 'USD'
status               TEXT CHECK (status IN ('pending', 'paid', 'failed', 'cancelled', 'expired'))
order_reference      TEXT UNIQUE (our reference)
paynow_reference     TEXT (Paynow's reference)
poll_url             TEXT (for status checking)
user_email           TEXT
user_phone           TEXT (Zimbabwe format)
subscription_type    TEXT
subscription_start   TIMESTAMPTZ
subscription_end     TIMESTAMPTZ
created_at           TIMESTAMPTZ
paid_at              TIMESTAMPTZ
```

### subscriptions
```sql
id                  UUID PRIMARY KEY
phone_hash          TEXT UNIQUE (one active sub per user)
subscription_type   TEXT
amount              DECIMAL(10, 2)
start_date          TIMESTAMPTZ
end_date            TIMESTAMPTZ
is_active           BOOLEAN
transaction_id      UUID (links to payment)
```

### user_usage
```sql
id                  UUID PRIMARY KEY
phone_hash          TEXT
diagnostics_count   INT
period_start        TIMESTAMPTZ (Monday 00:00 UTC)
period_end          TIMESTAMPTZ (Sunday 23:59 UTC)
was_subscribed      BOOLEAN
```

---

## Monitoring & Logs

### Key Events

```bash
# Payment initiated
{"event": "paynow_payment_initiating", "order_reference": "SUB-...", "amount": 2.00}

# Payment confirmed
{"event": "payment_processed_subscription_created", "subscription_end_date": "2026-08-03..."}

# User hit free limit
{"event": "payment_required", "phone_hash": "abc...", "diagnostics_used": 5}

# Usage incremented
{"event": "usage_incremented", "phone_hash": "abc...", "count": 3}
```

### Error Monitoring

```bash
# Paynow API errors
{"event": "paynow_payment_failed", "error": "..."}

# Webhook errors
{"event": "paynow_webhook_error", "error": "..."}

# Polling errors
{"event": "poll_transaction_error", "order_reference": "SUB-...", "error": "..."}
```

---

## Testing

### Test Scenarios

1. **Free Tier:**
   ```bash
   # Send 5 diagnostics (should work)
   # Send 6th diagnostic (should get payment prompt)
   ```

2. **Subscription:**
   ```bash
   # Send: SUBSCRIBE test@example.com 0771234567
   # Check phone for EcoCash prompt
   # Approve payment
   # Wait 30-60 seconds for polling
   # Send diagnostic (should work)
   ```

3. **Status Check:**
   ```bash
   # Send: STATUS
   # Should show subscription or free tier status
   ```

### Manual Testing (Development)

```bash
# 1. Initiate payment
curl -X POST http://localhost:8000/payments/initiate \
  -H "Content-Type: application/json" \
  -d '{
    "user_phone": "0771234567",
    "user_email": "test@example.com",
    "subscription_type": "monthly"
  }'

# 2. Check status
curl http://localhost:8000/payments/status/SUB-20260703-abc123

# 3. Check access
curl http://localhost:8000/payments/access-check/0771234567
```

---

## Troubleshooting

### "Payment system not configured"
- Check PAYNOW_INTEGRATION_ID and PAYNOW_INTEGRATION_KEY in `.env`
- Restart backend after adding credentials

### "Payment initiation failed"
- Check Paynow credentials are correct
- Verify integration is active in Paynow dashboard
- Check logs for exact error message

### Webhook not receiving updates
- Ensure PAYNOW_RESULT_URL is public HTTPS
- Check URL is configured in Paynow dashboard
- Test webhook with: `curl -X POST https://your-domain.com/webhook/paynow`

### Payment stuck in "pending"
- Background poller runs every 30 seconds
- Check logs: `grep "polling_pending_transactions" app.log`
- Manually check: `GET /payments/status/{order_reference}`
- Typical confirmation time: 5-30 seconds after approval

### User still sees payment prompt after subscribing
- Check subscription table: `SELECT * FROM subscriptions WHERE phone_hash = '...'`
- Verify end_date > now()
- Check is_active = true
- Try sending STATUS command to debug

---

## Production Deployment

### Pre-Launch Checklist

- [ ] Client provides real Paynow credentials
- [ ] Credentials added to production `.env`
- [ ] Database migration run on production Supabase
- [ ] PAYNOW_RESULT_URL set to public HTTPS endpoint
- [ ] Result URL configured in Paynow dashboard
- [ ] Test with real EcoCash number
- [ ] Verify webhook receives updates
- [ ] Monitor logs for errors
- [ ] Set up alerts for payment failures

### Monitoring

```bash
# Key metrics to track:
- Payment initiation success rate
- Payment confirmation time (p50, p95, p99)
- Webhook delivery success rate
- Active subscriptions count
- Churn rate (expired subscriptions)
- Free tier → paid conversion rate
```

---

## Cost Estimates

### Paynow Fees
(Check with Paynow for current rates)
- Transaction fee: ~2-5% + small fixed fee
- For $2 subscription: ~$0.10 fee = $1.90 net

### Infrastructure
- Supabase: Free tier or $25/month
- WhatsApp (Baileys): Free
- Hosting: Depends on deployment

---

## Support

### For Users
- WhatsApp support via bot (implement /help command)
- Send STATUS for subscription info
- Contact details for payment issues

### For Developers
- Paynow docs: https://developers.paynow.co.zw/
- SDK GitHub: https://github.com/paynow/Paynow-Python-SDK
- This codebase: Check logs, monitoring, database

---

## Future Enhancements

### Potential Improvements
1. **Auto-renewal** - Recurring payments before expiration
2. **Multiple tiers** - Weekly/monthly options
3. **Promo codes** - Discount codes for marketing
4. **Referral program** - Credits for referring users
5. **Payment history** - User can see past payments
6. **Cancel subscription** - User-initiated cancellation
7. **Grace period** - 24-48 hours after expiration
8. **SMS notifications** - Expiration reminders

---

## Files Created

```
migrations/add_payments_tables.sql          - Database schema
app/models/payment.py                       - Pydantic models
app/repositories/payment_repository.py      - Database operations
app/services/payment_service.py             - Paynow integration
app/services/payment_commands.py            - WhatsApp command handlers
app/services/payment_poller.py              - Background polling
app/api/routes/payments.py                  - Payment API endpoints
```

---

**Status:** Integration complete and ready for client credentials ✅
