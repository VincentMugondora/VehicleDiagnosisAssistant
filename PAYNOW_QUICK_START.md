# Paynow Integration - Quick Start (5 Minutes)

## For Your Client

Your client needs to give you **2 credentials** from their Paynow account:

1. **Integration ID** (number like `12345`)
2. **Integration Key** (long secret string like `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)

**Where to find them:**
- Login to https://www.paynow.co.zw/
- Go to: Settings → Integration
- Copy both values

---

## Setup (5 Steps)

### 1. Add Credentials to `.env`

```bash
# Add these lines (use real values from client):
PAYNOW_INTEGRATION_ID=12345
PAYNOW_INTEGRATION_KEY=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
PAYNOW_RETURN_URL=https://your-domain.com/payments/return
PAYNOW_RESULT_URL=https://your-domain.com/webhook/paynow
```

### 2. Run Database Migration

Open Supabase SQL Editor and run:
```bash
migrations/add_payments_tables.sql
```

### 3. Configure Paynow Webhook

In Paynow dashboard:
- Settings → Integration
- Set **Result URL** to: `https://your-domain.com/webhook/paynow`
- (Must be public HTTPS, not localhost)

### 4. Start Backend

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 5. Test It

```bash
curl http://localhost:8000/payments/test
```

Expected: `{"status": "ok", "paynow_configured": true}`

---

## How Users Subscribe

**1. User hits free limit (5 diagnostics/week):**
```
You've used all 5 free diagnostics this week.

Subscribe for unlimited diagnostics!
Only $2/month

To subscribe, reply with:
SUBSCRIBE [your email] [your EcoCash number]
```

**2. User sends:**
```
SUBSCRIBE john@example.com 0771234567
```

**3. Bot responds:**
```
✅ Payment initiated!
📱 Check your phone for EcoCash prompt
💰 Amount: $2.00 USD
```

**4. User approves on phone** (EcoCash USSD)

**5. Payment confirmed** (5-30 seconds)

**6. Subscription active!** User gets unlimited diagnostics for 30 days

---

## User Commands

| Command | What It Does |
|---------|--------------|
| `SUBSCRIBE john@example.com 0771234567` | Start subscription payment |
| `STATUS` | Check subscription status |
| Any diagnostic code (e.g., `P0420`) | Uses diagnostic (free or subscribed) |

---

## Monitoring

### Check Payment Logs
```bash
# Payment initiated
grep "paynow_payment_initiating" app.log

# Payment confirmed
grep "payment_processed_subscription_created" app.log

# Errors
grep "paynow.*error" app.log
```

### Check Database
```sql
-- Active subscriptions
SELECT * FROM subscriptions WHERE is_active = true AND end_date > NOW();

-- Recent transactions
SELECT * FROM transactions ORDER BY created_at DESC LIMIT 10;

-- User usage
SELECT * FROM user_usage ORDER BY created_at DESC LIMIT 10;
```

---

## Troubleshooting

### "Payment system not configured"
→ Check `.env` has PAYNOW_INTEGRATION_ID and PAYNOW_INTEGRATION_KEY  
→ Restart backend

### "Payment initiation failed"
→ Check credentials are correct in Paynow dashboard  
→ Check logs for exact error

### Webhook not working
→ PAYNOW_RESULT_URL must be public HTTPS  
→ Configure in Paynow dashboard  
→ Test: `curl -X POST https://your-domain.com/webhook/paynow`

### Payment stuck "pending"
→ Background poller runs every 30 seconds  
→ Check: `GET /payments/status/{order_reference}`  
→ Typical confirmation: 5-30 seconds

---

## Testing Without Real Payments

### Simulate Free Tier
```python
# In Python console:
from app.db.client import get_supabase_client
from app.repositories.payment_repository import PaymentRepository
from app.utils.phone import hash_phone_number

client = get_supabase_client()
repo = PaymentRepository(client)

# Check user's usage
phone_hash = hash_phone_number("whatsapp:+263771234567")
usage = repo.get_weekly_usage(phone_hash)
print(f"Usage: {usage}/5")

# Increment manually
repo.increment_usage(phone_hash)
```

### Check Access
```bash
curl http://localhost:8000/payments/access-check/0771234567
```

---

## Next Steps

1. ✅ Get client's Paynow credentials
2. ✅ Add to `.env`
3. ✅ Run database migration
4. ✅ Configure webhook URL
5. ✅ Test with real EcoCash number
6. ✅ Monitor first few payments
7. ✅ Set up error alerts

---

**Full Documentation:** See `PAYNOW_INTEGRATION.md` for complete guide

**Support:** Check logs first, then Paynow developer docs
