# Paynow Quick Reference Card

## ✅ Status: WORKING

Integration ID: `25487`  
Email: `nopausegroupofcompanies@gmail.com`  
Mode: **TEST MODE**

---

## 🧪 Test Mode

**Test Phone Numbers:**
- `0771111111` (Always succeeds)
- `0772222222` (Always succeeds)
- `0773333333` (Always succeeds)

**Email:** Must use `nopausegroupofcompanies@gmail.com`

**Payment:** Simulated (no real money)

---

## 💰 Pricing

**Free Tier:** 5 diagnostics/week  
**Monthly Sub:** $5 USD for 30 days unlimited

---

## 📱 WhatsApp Commands

```
/subscribe  - Start subscription
/status     - Check subscription
/usage      - View diagnostics remaining
```

---

## 🚀 Quick Test

1. Restart backend: `uvicorn app.main:app --reload`
2. Send via WhatsApp: `/subscribe`
3. Use test phone: `0771111111`
4. Verify subscription activates

---

## 🔧 Admin Check

```python
from app.db.client import get_supabase_client
c = get_supabase_client()

# Active subs
r = c.table('subscriptions').select('*').eq('is_active', True).execute()
print(f"Active: {len(r.data)}")

# Recent payments
r = c.table('transactions').select('*').order('created_at', desc=True).limit(5).execute()
for t in r.data:
    print(f"{t['order_reference']}: {t['status']}")
```

---

## 🎯 Production Activation

**Email:** support@paynow.co.zw  
**Request:** Activate integration 25487 for production  
**Benefit:** Accept real phones + real payments

---

**Files:** PAYNOW_SUCCESS.md (full guide)  
**Last Test:** 2026-07-06 ✅ SUCCESS
