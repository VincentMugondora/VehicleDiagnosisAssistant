# Pre-Production Checklist - Paynow Integration

## Quick Answers to Your 3 Questions

### 1. ❌ No Paynow Sandbox Available

**Finding:** Paynow Zimbabwe does not offer a sandbox/test environment.

**Testing Options:**
- **Recommended:** Use minimal real payments ($0.01 if supported, or $2 test transaction)
- **Alternative:** Build application-level test mode (mock Paynow responses)
- **For webhook testing:** Use ngrok to test locally without real payments

**See:** `WEBHOOK_DEPLOYMENT_GUIDE.md` for ngrok setup

---

### 2. ✅ Malformed Input Handling Verified

**All malformed inputs show this error:**
```
❌ Invalid SUBSCRIBE command format.

Correct format:
SUBSCRIBE <email> <phone>

Example:
SUBSCRIBE john@example.com 0771234567

Make sure:
• Email has @ and domain
• Phone is 10 digits starting with 0
• Phone supports EcoCash (071, 073, 077, 078)
```

**Validated edge cases:**
- ✅ Missing email or phone → Shows error
- ✅ Invalid email format → Shows error
- ✅ Invalid phone length → Shows error
- ✅ Wrong phone prefix (088) → Shows error (**Fixed!**)
- ✅ Country code format (+263) → Shows error
- ✅ Dashes in phone (077-123-4567) → Auto-cleaned, works
- ✅ Lowercase command → Works

**See:** `MALFORMED_INPUT_EXAMPLES.md` for all test cases

---

### 3. ✅ Webhook URL Requirements Confirmed

**Local Development:**
```bash
# Use ngrok to expose localhost
ngrok http 8000
# Gets: https://abc123.ngrok.io

# Update .env
PAYNOW_RESULT_URL=https://abc123.ngrok.io/webhook/paynow

# Update Paynow dashboard
Result URL: https://abc123.ngrok.io/webhook/paynow
```

**Production:**
```bash
# Need real domain + HTTPS
PAYNOW_RESULT_URL=https://diagnostics.yourdomain.com/webhook/paynow

# Update Paynow dashboard (once, never changes)
Result URL: https://diagnostics.yourdomain.com/webhook/paynow
```

**See:** `WEBHOOK_DEPLOYMENT_GUIDE.md` for complete guide

---

## Complete Pre-Production Checklist

### 1. Testing Strategy

#### Phase 1: Local Mock Testing (No Money)
- [ ] Run `python test_payment_integration.py`
- [ ] Verify database tables exist
- [ ] Test access control logic
- [ ] Test usage counting
- [ ] Simulate webhook with curl

#### Phase 2: ngrok Webhook Testing (No Money)
- [ ] Install ngrok: `choco install ngrok` or download
- [ ] Start backend: `uvicorn app.main:app --reload --port 8000`
- [ ] Start ngrok: `ngrok http 8000`
- [ ] Update `.env` with ngrok URL
- [ ] Test webhook reaches backend
- [ ] Check ngrok inspector: `http://127.0.0.1:4040`

#### Phase 3: Malformed Input Testing
- [ ] Run `python test_malformed_subscribe.py`
- [ ] Verify all invalid formats show error
- [ ] Verify valid formats are accepted
- [ ] Test via WhatsApp with real user

#### Phase 4: Real Payment Testing (Minimal Cost)
- [ ] Get client's real Paynow credentials
- [ ] Update `.env` with real credentials
- [ ] Consider: `SUBSCRIPTION_PRICE=0.01` for testing
- [ ] Test full flow with personal EcoCash account:
  - [ ] Send `SUBSCRIBE email@example.com 0771234567`
  - [ ] Verify EcoCash USSD prompt on phone
  - [ ] Approve payment
  - [ ] Check logs for polling
  - [ ] Check logs for webhook
  - [ ] Verify subscription created
  - [ ] Send diagnostic (should work unlimited)
  - [ ] Send `STATUS` (should show active)

---

### 2. Security Checklist

- [ ] PAYNOW_INTEGRATION_KEY never logged
- [ ] PAYNOW_INTEGRATION_KEY never committed to git
- [ ] Phone numbers hashed (SHA-256) before storage
- [ ] Hash verification enabled (SHA512 for Paynow responses)
- [ ] HTTPS required for webhook in production
- [ ] `.env` file in `.gitignore`
- [ ] `.env.example` has no real credentials

---

### 3. Database Setup

- [ ] Run migration: `migrations/add_payments_tables.sql`
- [ ] Verify tables created:
  ```sql
  SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename IN ('transactions', 'subscriptions', 'user_usage');
  ```
- [ ] Test helper functions:
  ```sql
  SELECT has_active_subscription('test_hash');
  SELECT get_weekly_usage('test_hash');
  ```

---

### 4. Configuration Validation

#### Local Development `.env`
```bash
# Supabase (keep same)
SUPABASE_URL=https://yourproject.supabase.co
SUPABASE_SERVICE_KEY=your-key

# Paynow (from client)
PAYNOW_INTEGRATION_ID=12345
PAYNOW_INTEGRATION_KEY=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

# Webhook (ngrok - changes each restart on free plan)
PAYNOW_RETURN_URL=https://abc123.ngrok.io/payments/return
PAYNOW_RESULT_URL=https://abc123.ngrok.io/webhook/paynow

# Payment config (can set low for testing)
SUBSCRIPTION_PRICE=0.01
FREE_DIAGNOSTICS_LIMIT=5
FREE_DIAGNOSTICS_WINDOW_DAYS=7

# Feature flags
AI_ENRICH_ENABLED=true
```

#### Production `.env`
```bash
# Supabase (production)
SUPABASE_URL=https://yourproject.supabase.co
SUPABASE_SERVICE_KEY=your-production-key

# Paynow (from client - REAL credentials)
PAYNOW_INTEGRATION_ID=12345
PAYNOW_INTEGRATION_KEY=real-key-xxxxx

# Webhook (production domain - NEVER CHANGES)
PAYNOW_RETURN_URL=https://diagnostics.yourdomain.com/payments/return
PAYNOW_RESULT_URL=https://diagnostics.yourdomain.com/webhook/paynow

# Payment config (production pricing)
SUBSCRIPTION_PRICE=2.00
FREE_DIAGNOSTICS_LIMIT=5
FREE_DIAGNOSTICS_WINDOW_DAYS=7

# Feature flags
AI_ENRICH_ENABLED=true
```

---

### 5. Paynow Dashboard Configuration

Login to https://www.paynow.co.zw/ and configure:

#### Development
- [ ] Settings → Integration
- [ ] Result URL: `https://abc123.ngrok.io/webhook/paynow`
- [ ] Save
- [ ] **Note:** Must update every time ngrok restarts (free plan)

#### Production
- [ ] Settings → Integration
- [ ] Result URL: `https://diagnostics.yourdomain.com/webhook/paynow`
- [ ] Save
- [ ] **Note:** Set once, never change

---

### 6. Deployment Checklist

#### Choose Deployment Method
- [ ] **Option A:** VPS (DigitalOcean, Linode) - Most control
- [ ] **Option B:** Railway.app - Easiest
- [ ] **Option C:** Render.com - Good balance

#### Setup Requirements
- [ ] Domain name registered
- [ ] SSL certificate (Let's Encrypt or provider)
- [ ] Server/hosting account created
- [ ] Database accessible from server
- [ ] Environment variables configured

#### Deploy Application
- [ ] Push code to GitHub
- [ ] Deploy to hosting
- [ ] Set environment variables
- [ ] Verify HTTPS working: `curl https://yourdomain.com/healthz`
- [ ] Test webhook endpoint: `curl https://yourdomain.com/webhook/paynow`
- [ ] Update Paynow dashboard with production URL

---

### 7. Monitoring Setup

#### Logs to Monitor
```bash
# Payment initiated
grep "paynow_payment_initiating" app.log

# Payment confirmed
grep "payment_processed_subscription_created" app.log

# Webhook received
grep "paynow_webhook_received" app.log

# Errors
grep "error" app.log | grep "paynow"
```

#### Key Metrics
- [ ] Set up logging aggregation (optional)
- [ ] Monitor payment success rate
- [ ] Monitor webhook delivery
- [ ] Monitor subscription churn
- [ ] Set alerts for payment failures

---

### 8. User Communication

#### Before Launch
- [ ] Test `SUBSCRIBE` command with real user
- [ ] Test `STATUS` command with real user
- [ ] Verify error messages are clear
- [ ] Test free tier (5 diagnostics)
- [ ] Test limit exceeded message

#### Documentation for Users
- [ ] How to subscribe (SUBSCRIBE command)
- [ ] How to check status (STATUS command)
- [ ] What happens after free limit
- [ ] Subscription price and duration
- [ ] Support contact for payment issues

---

### 9. Risk Mitigation

#### Payment Issues
- [ ] What if webhook never arrives?
  - Background poller checks every 30s
  - Max polling duration: 15 minutes
  - After 15 min: mark as expired
  
- [ ] What if user approves but subscription not created?
  - Check logs: `grep order_reference app.log`
  - Check database: `SELECT * FROM transactions WHERE order_reference = '...'`
  - Manually create subscription if payment confirmed
  
- [ ] What if user charged twice?
  - Idempotency checks prevent this
  - Check database for duplicate transactions
  - Refund via Paynow dashboard if needed

#### Access Control Issues
- [ ] What if database goes down?
  - Graceful degradation: allow access (log warning)
  - Don't block users due to system issues
  
- [ ] What if usage counter fails to increment?
  - Log warning, continue
  - User gets extra free diagnostic (acceptable)

---

### 10. Launch Readiness

#### Final Checks (Do These Last)
- [ ] All tests passing
- [ ] Webhook reachable from internet
- [ ] Paynow dashboard configured
- [ ] Real credentials in production `.env`
- [ ] SSL certificate valid
- [ ] Database migration run
- [ ] Background poller running
- [ ] Logs accessible
- [ ] Support contact ready

#### Soft Launch (Recommended)
- [ ] Enable for 5-10 test users first
- [ ] Monitor closely for 24 hours
- [ ] Check webhook delivery rate
- [ ] Check payment confirmation times
- [ ] Fix any issues before full launch

#### Full Launch
- [ ] Announce to all users
- [ ] Monitor payment volume
- [ ] Watch for edge cases
- [ ] Be ready to rollback if needed

---

## Common Issues & Solutions

### Issue: ngrok URL keeps changing

**Solution:** 
- Upgrade to ngrok paid plan ($8/month) for static URL
- Or use localtunnel (free, less reliable)
- Or deploy to production early

### Issue: Webhook not being called

**Check:**
1. URL reachable: `curl https://your-url.com/webhook/paynow`
2. Paynow dashboard configured correctly
3. SSL certificate valid
4. ngrok session not expired (local dev)

### Issue: Payment stuck in pending

**Typical causes:**
- Webhook not configured (check Paynow dashboard)
- Background poller not running (check logs)
- User didn't approve payment (check with user)

**Fix:**
- Check webhook logs: `grep paynow_webhook app.log`
- Check polling logs: `grep polling_pending app.log`
- Manually check status: `GET /payments/status/{order_reference}`

### Issue: User says they paid but still can't access

**Debug steps:**
1. Check transaction: `SELECT * FROM transactions WHERE user_phone = '...'`
2. Check subscription: `SELECT * FROM subscriptions WHERE phone_hash = '...'`
3. Check usage: `SELECT * FROM user_usage WHERE phone_hash = '...'`
4. Verify `end_date > NOW()` and `is_active = true`

---

## Testing Priority Order

1. **Highest:** Database tables, access control logic ✅
2. **High:** Webhook delivery (ngrok testing) ✅
3. **Medium:** Malformed input handling ✅
4. **Low:** Real payment flow (costs money) ⚠️

**Recommendation:** Do 1-3 thoroughly, then test #4 once with minimal amount before full production.

---

## Documentation Reference

| Document | Purpose | When to Read |
|----------|---------|--------------|
| `PRE_PRODUCTION_CHECKLIST.md` | This file - overview | Before launch |
| `PAYNOW_INTEGRATION.md` | Complete integration guide | Implementation |
| `PAYNOW_QUICK_START.md` | 5-minute setup | Quick reference |
| `PAYNOW_SUMMARY.md` | What was built | Overview |
| `PAYNOW_ARCHITECTURE.md` | System diagrams | Deep dive |
| `MALFORMED_INPUT_EXAMPLES.md` | Input validation tests | QA testing |
| `WEBHOOK_DEPLOYMENT_GUIDE.md` | Webhook setup details | Deployment |

---

## Ready to Launch?

✅ **You're ready when:**
- All Phase 1-3 tests pass
- Webhook reachable from internet
- Paynow dashboard configured
- Production `.env` set correctly
- Monitoring in place

⚠️ **Consider soft launch when:**
- Only Phase 1-2 tests done (skip real payment)
- Deploy to production
- Test with 5-10 real users
- Monitor closely for 24 hours

❌ **Don't launch yet if:**
- Database migration not run
- Webhook not configured
- No real Paynow credentials
- Can't monitor logs

---

**Status:** Ready for pre-production testing  
**Next Step:** Run `python test_payment_integration.py`  
**Then:** Set up ngrok for webhook testing  
**Finally:** One real payment test before launch
