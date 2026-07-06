# Paynow Payment Integration Setup

**Complete guide to activate Paynow payments for your VehicleDiagnosisAssistant**

Last Updated: 2026-07-06

---

## ✅ Your Paynow Credentials

```
Company: PaulNock inc
Type: 3rd Party Integration
Payment Link: NockDiagnostics Ai
Integration ID: 25487
Integration Key: f33ab311-0cdb-4302-a9a9-d2257170acdd
```

**Status:** ✅ Already added to `.env` file

---

## 🚀 Quick Setup (3 Steps)

### Step 1: Verify Credentials (Already Done!)

```bash
# Check .env file has Paynow credentials
grep "PAYNOW" .env
```

**Expected output:**
```
PAYNOW_INTEGRATION_ID=25487
PAYNOW_INTEGRATION_KEY=f33ab311-0cdb-4302-a9a9-d2257170acdd
PAYNOW_RETURN_URL=https://your-domain.com/payment/return
PAYNOW_RESULT_URL=https://your-domain.com/payment/callback
```

### Step 2: Test Paynow Connection

```bash
python scripts/test_paynow.py
```

**Expected:** Creates a $1 test payment and returns Paynow URL

### Step 3: Restart Backend

```bash
# Stop backend (Ctrl+C)
# Then restart:
uvicorn app.main:app --reload
```

**Check logs for:**
```
paynow_payment_service_initialized ✅
```

Instead of:
```
paynow_credentials_missing ⚠️
```

---

## 💰 How Payments Work

### Subscription Model

**Monthly Unlimited:**
- Price: $5 USD (or ZWL equivalent)
- Unlimited diagnostics for 30 days
- Auto-renews (if enabled)

**Free Tier:**
- 5 diagnostics per week
- No payment required
- Resets weekly (Monday)

### User Flow

1. **User sends message** → Backend checks usage
2. **Limit reached** → Sends subscription prompt
3. **User replies '/subscribe'** → Payment URL sent
4. **User pays via EcoCash** → Subscription activated
5. **User gets unlimited access** for 30 days

---

## 📱 Payment Commands

Users send these via WhatsApp:

```
/subscribe         - Start monthly subscription ($5/month)
/status            - Check subscription status
/usage             - View remaining free diagnostics
```

---

## 🧪 Testing Payments

### Test in Development

```bash
# 1. Run test script
python scripts/test_paynow.py

# Expected output:
#   [OK] Credentials configured
#   [OK] PaymentService initialized
#   [OK] Payment initiated successfully!
#   Payment URL: https://www.paynow.co.zw/Payment/...
```

### Test via WhatsApp

```
1. Send: /subscribe
2. You get: Payment URL with instructions
3. Click link or visit URL
4. Pay $5 USD via EcoCash
5. Status updates automatically
6. You get: "Subscription activated!" message
```

### Test with Real Payment

**Recommended test amount:** $1 USD

1. Modify test script amount to $1
2. Complete real EcoCash payment
3. Verify subscription activates
4. Refund if needed (contact Paynow)

---

## 🔧 Configuration

### Current Setup

**In `.env`:**
```env
PAYNOW_INTEGRATION_ID=25487
PAYNOW_INTEGRATION_KEY=f33ab311-0cdb-4302-a9a9-d2257170acdd
PAYNOW_RETURN_URL=https://your-domain.com/payment/return
PAYNOW_RESULT_URL=https://your-domain.com/payment/callback
```

### Callback URLs (Important!)

**Return URL:** Where users go after payment (optional)
- Can be your website or WhatsApp deep link
- Example: `https://wa.me/your-number?text=Payment%20completed`

**Result URL:** Where Paynow sends payment status (required)
- Must be publicly accessible HTTPS endpoint
- Example: `https://your-backend.com/webhook/paynow`
- Used for automated subscription activation

### For Production

You need to expose your backend to the internet for Paynow callbacks:

**Option 1: Ngrok (Quick Test)**
```bash
ngrok http 8000
# Copy URL: https://abc123.ngrok.io
# Update .env:
PAYNOW_RESULT_URL=https://abc123.ngrok.io/webhook/paynow
```

**Option 2: Deploy Backend (Production)**
- Deploy to Render, Railway, or Heroku
- Get public URL: `https://your-app.onrender.com`
- Update callback URL

**Option 3: Polling (No Webhook Needed)**
- Current implementation uses polling
- Checks payment status every 5 seconds
- No callback URL required for basic functionality

---

## 📊 Database Tables Used

### transactions
Stores all payment records:
```sql
- order_reference (unique)
- paynow_reference
- amount, currency
- status (pending, paid, failed, cancelled)
- user_phone, user_email
- created_at, paid_at
```

### subscriptions
Active user subscriptions:
```sql
- phone_hash (unique)
- subscription_type (monthly)
- start_date, end_date
- is_active
- transaction_id (FK)
```

### user_usage
Free tier usage tracking:
```sql
- phone_hash
- diagnostics_count
- period_start, period_end
- was_subscribed
```

---

## 🔍 Monitoring Payments

### Check Payment Status

**Via Database:**
```python
from app.db.client import get_supabase_client

client = get_supabase_client()

# Recent transactions
result = client.table('transactions').select('*').order('created_at', desc=True).limit(10).execute()
for t in result.data:
    print(f"{t['order_reference']}: {t['status']} - ${t['amount']}")

# Active subscriptions
result = client.table('subscriptions').select('*').eq('is_active', True).execute()
print(f"Active subscriptions: {len(result.data)}")
```

**Via Supabase Dashboard:**
1. Go to Table Editor
2. View `transactions` table
3. Filter by status, date, etc.

### Check User Subscription

```python
from app.repositories.payment_repository import PaymentRepository

repo = PaymentRepository(client)

# Check if user has active subscription
phone_hash = "user_phone_hash_here"
has_sub = repo.has_active_subscription(phone_hash)
print(f"Has subscription: {has_sub}")

# Get subscription details
sub = repo.get_active_subscription(phone_hash)
if sub:
    print(f"Expires: {sub.end_date}")
```

---

## 💡 Payment Flow Details

### 1. User Request

```
User: /subscribe
```

### 2. Backend Creates Payment

```python
payment_service.initiate_subscription_payment(
    phone_number="0771234567",
    email="user@example.com",
    amount=Decimal("5.00"),
    subscription_type="monthly"
)
```

### 3. Paynow Response

```json
{
  "success": true,
  "order_reference": "SUB-20260706-abc123",
  "paynow_reference": "1234567",
  "poll_url": "https://www.paynow.co.zw/Interface/CheckPayment/?guid=...",
  "redirect_url": "https://www.paynow.co.zw/Payment/..."
}
```

### 4. Send Payment URL to User

```
📱 To subscribe ($5/month):

👉 Pay here: https://www.paynow.co.zw/Payment/...

✅ Pay via EcoCash
⏱️ Payment usually confirms in 1-2 minutes
🔄 Checking status automatically...
```

### 5. Poll for Status

Backend checks every 5 seconds:
```python
status = payment_service.check_payment_status(poll_url)
# Returns: 'paid', 'pending', 'failed', etc.
```

### 6. Activate Subscription

When status = 'paid':
```python
payment_service.activate_subscription(
    transaction_id=transaction_id,
    duration_days=30
)
```

### 7. Notify User

```
✅ Payment confirmed!

Your monthly subscription is now active:
• Unlimited diagnostics for 30 days
• Expires: 2026-08-06

Thank you for subscribing! 🎉
```

---

## 🛠️ Troubleshooting

### Issue: Credentials Not Loaded

**Symptom:** Logs show `paynow_credentials_missing`

**Fix:**
1. Check `.env` file has Paynow credentials
2. Restart backend (credentials load at startup)
3. Verify with: `grep PAYNOW .env`

### Issue: Payment Fails to Initiate

**Symptom:** Error when creating payment

**Possible causes:**
- Invalid credentials
- Network connectivity
- Paynow API down

**Debug:**
```python
python scripts/test_paynow.py
# Check full error traceback
```

### Issue: Payment Stuck in 'Pending'

**Symptom:** User paid but subscription not activated

**Possible causes:**
- Paynow delay (normal, wait 1-5 minutes)
- Callback URL not reached
- Polling stopped

**Fix:**
1. Manually check payment status in Paynow dashboard
2. If paid, manually activate:
```python
from app.services.payment_service import PaymentService
from app.db.client import get_supabase_client

client = get_supabase_client()
service = PaymentService(client)

# Get transaction
result = client.table('transactions').select('*').eq('order_reference', 'SUB-xxx').execute()
transaction = result.data[0]

# Manually activate
service.activate_subscription(transaction['id'], duration_days=30)
```

### Issue: Webhook Not Receiving Callbacks

**Symptom:** Payments complete but no auto-activation

**Fix:**
1. Ensure `PAYNOW_RESULT_URL` is publicly accessible
2. Use Ngrok for testing: `ngrok http 8000`
3. Update URL in Paynow dashboard
4. Test webhook endpoint:
```bash
curl -X POST https://your-url.com/webhook/paynow \
  -H "Content-Type: application/json" \
  -d '{"reference": "test", "status": "Paid"}'
```

---

## 📈 Analytics & Reporting

### Revenue Report

```sql
-- Total revenue this month
SELECT 
    SUM(amount) as total_revenue,
    COUNT(*) as payment_count,
    currency
FROM transactions
WHERE status = 'paid'
  AND created_at >= date_trunc('month', CURRENT_DATE)
GROUP BY currency;
```

### Subscription Stats

```sql
-- Active subscribers
SELECT COUNT(*) FROM subscriptions WHERE is_active = true;

-- Expiring soon (next 7 days)
SELECT COUNT(*) FROM subscriptions 
WHERE is_active = true 
  AND end_date < CURRENT_DATE + INTERVAL '7 days';

-- Revenue by subscription type
SELECT 
    subscription_type,
    COUNT(*) as subscriber_count,
    SUM(amount) as total_revenue
FROM subscriptions s
JOIN transactions t ON s.transaction_id = t.id
WHERE s.is_active = true
GROUP BY subscription_type;
```

### Usage Stats

```sql
-- Free tier usage
SELECT 
    COUNT(*) as free_users,
    AVG(diagnostics_count) as avg_usage,
    SUM(CASE WHEN diagnostics_count >= 5 THEN 1 ELSE 0 END) as users_at_limit
FROM user_usage
WHERE period_start >= date_trunc('week', CURRENT_DATE)
  AND was_subscribed = false;
```

---

## 🎯 Next Steps

### Immediate (Test Now)

- [ ] Run `python scripts/test_paynow.py`
- [ ] Verify test payment creates
- [ ] Check transaction in database
- [ ] Restart backend and verify no credential warnings

### This Week

- [ ] Test `/subscribe` via WhatsApp
- [ ] Complete $1 test payment with real EcoCash
- [ ] Verify subscription activates
- [ ] Test expiration logic (set short duration for testing)

### Production

- [ ] Deploy backend to production server
- [ ] Configure public callback URL
- [ ] Update Paynow dashboard with callback URL
- [ ] Set up monitoring/alerts for failed payments
- [ ] Create admin dashboard for payment management

---

## 📞 Support

**Paynow Support:**
- Email: support@paynow.co.zw
- Phone: +263 (24) 2745-123
- Dashboard: https://www.paynow.co.zw

**Your Integration:**
- Integration ID: 25487
- Name: NockDiagnostics Ai
- Company: PaulNock inc

---

## ✅ Checklist

Setup:
- [x] Credentials added to `.env`
- [ ] Test script runs successfully
- [ ] Backend recognizes credentials (no warnings)
- [ ] Database tables exist (transactions, subscriptions, user_usage)

Testing:
- [ ] Test payment initiated successfully
- [ ] Payment URL generated
- [ ] Can access Paynow payment page
- [ ] Test EcoCash payment completes
- [ ] Subscription activates after payment
- [ ] Usage limits update correctly

Production:
- [ ] Backend deployed with public URL
- [ ] Callback URL configured
- [ ] Webhooks receiving notifications
- [ ] Monitoring set up
- [ ] Admin can manage subscriptions

---

**Status:** Ready to test!  
**Next:** Run `python scripts/test_paynow.py`
