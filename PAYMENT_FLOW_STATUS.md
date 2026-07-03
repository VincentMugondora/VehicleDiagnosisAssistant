# Payment Flow Implementation Status

**Date**: July 3, 2026

## ✅ What's Already Implemented

### Database Tables
- ✅ `transactions` - Payment records with Paynow integration
- ✅ `subscriptions` - Active user subscriptions
- ✅ `user_usage` - Free tier tracking (5 diagnostics/week)

### Payment Service (`app/services/payment_service.py`)
- ✅ `initiate_subscription_payment()` - Start EcoCash payment
- ✅ `check_user_access()` - Check subscription status + free tier
- ✅ `increment_user_usage()` - Track diagnostic usage
- ✅ Paynow integration configured

### Commands (`app/services/payment_commands.py`)
- ✅ **SUBSCRIBE** - Initiate payment
  - Format: `SUBSCRIBE <email> <phone>`
  - Example: `SUBSCRIBE john@example.com 0771234567`
- ✅ **STATUS** - Check subscription/usage status

### Webhook Integration
- ✅ Payment command parsing
- ✅ Usage limit enforcement
- ✅ Upgrade prompts when limit hit

---

## ❌ What's Missing

### Commands Not Implemented
- ❌ **CANCEL** - Cancel auto-renewal
- ❌ **RENEW** - Renew expired subscription

### Features Not Implemented
- ❌ Expiry reminders (5 days before)
- ❌ Auto-expiry handling
- ❌ Payment timeout handling (5-10 min)

---

## 📋 Implementation Plan

### Phase 1: Add Missing Commands ✅ PRIORITY

#### 1.1 CANCEL Command
```python
# app/services/payment_commands.py

def parse_cancel_command(text: str) -> bool:
    """Check if message is CANCEL command"""
    return text.strip().upper() == 'CANCEL'

async def handle_cancel_command(
    phone_hash: str,
    payment_service: PaymentService
) -> str:
    """
    Handle CANCEL command - disable auto-renewal.
    
    Returns message for user.
    """
    # Check if user has active subscription
    access = payment_service.check_user_access(phone_hash)
    
    if not access["has_subscription"]:
        return (
            "❌ You don't have an active subscription.\n\n"
            "To subscribe:\n"
            "SUBSCRIBE <email> <phone>"
        )
    
    # Cancel auto-renewal
    result = payment_service.cancel_subscription(phone_hash)
    
    if result["success"]:
        expiry = result["expires_at"]
        return (
            f"✅ Auto-renewal cancelled.\n\n"
            f"Your subscription remains active until:\n"
            f"{expiry}\n\n"
            f"After that, you'll return to free tier (5 diagnostics/week).\n\n"
            f"To re-subscribe, send SUBSCRIBE."
        )
    else:
        return f"❌ Error: {result['error']}"
```

#### 1.2 RENEW Command
```python
# app/services/payment_commands.py

def parse_renew_command(text: str) -> Tuple[str, str] | None:
    """
    Parse RENEW command.
    
    Format: RENEW <email> <phone>
    Same as SUBSCRIBE but for expired users.
    """
    if not text.upper().startswith('RENEW'):
        return None
    
    # Same parsing logic as SUBSCRIBE
    parts = text.split()
    if len(parts) < 3:
        return None
    
    email = parts[1]
    phone = parts[2]
    
    # Validate
    if '@' not in email or '.' not in email:
        return None
    if not phone.startswith('0') or len(phone) != 10:
        return None
    
    return (email, phone)

async def handle_renew_command(
    raw_text: str,
    payment_service: PaymentService
) -> str:
    """
    Handle RENEW command - restart expired subscription.
    
    Essentially the same as SUBSCRIBE.
    """
    parsed = parse_renew_command(raw_text)
    
    if not parsed:
        return (
            "❌ Invalid RENEW command format.\n\n"
            "Correct format:\n"
            "RENEW <email> <phone>\n\n"
            "Example:\n"
            "RENEW john@example.com 0771234567"
        )
    
    email, phone = parsed
    
    # Initiate payment (same as SUBSCRIBE)
    result = await payment_service.initiate_subscription_payment(
        user_phone=phone,
        user_email=email,
        subscription_type='monthly'
    )
    
    if result.get("success"):
        return (
            f"💳 Renewing subscription...\n\n"
            f"✅ EcoCash payment request sent!\n\n"
            f"📱 Check your phone ({phone}) for EcoCash prompt.\n\n"
            f"💵 Amount: $2.00\n\n"
            f"⏱️ Payment expires in 10 minutes.\n\n"
            f"Reply STATUS to check payment progress."
        )
    else:
        error = result.get("error", "Unknown error")
        return (
            f"❌ Payment initiation failed: {error}\n\n"
            f"Please check:\n"
            f"• Phone number is correct ({phone})\n"
            f"• EcoCash account is active\n"
            f"• You have sufficient balance ($2)\n\n"
            f"Try again with RENEW command."
        )
```

### Phase 2: Add Payment Service Methods

#### 2.1 Cancel Subscription
```python
# app/services/payment_service.py

def cancel_subscription(self, phone_hash: str) -> dict:
    """
    Cancel auto-renewal for active subscription.
    
    Subscription stays active until expiry date.
    
    Returns:
        Dict with success, expires_at, or error
    """
    try:
        subscription = self.payment_repo.get_active_subscription(phone_hash)
        
        if not subscription:
            return {
                "success": False,
                "error": "No active subscription found"
            }
        
        # Set auto_renew = false
        self.payment_repo.update_subscription_auto_renew(
            phone_hash=phone_hash,
            auto_renew=False
        )
        
        logger.info(
            "subscription_cancelled",
            phone_hash=phone_hash,
            expires_at=subscription["end_date"]
        )
        
        return {
            "success": True,
            "expires_at": subscription["end_date"].strftime("%Y-%m-%d")
        }
    
    except Exception as e:
        logger.error("cancel_subscription_failed", error=str(e))
        return {
            "success": False,
            "error": str(e)
        }
```

#### 2.2 Check Expiring Subscriptions
```python
# app/services/payment_service.py

def get_expiring_subscriptions(self, days_before: int = 5) -> list[dict]:
    """
    Get subscriptions expiring within N days.
    
    Used for sending reminder messages.
    
    Returns:
        List of subscription dicts with phone_hash, end_date
    """
    return self.payment_repo.get_expiring_subscriptions(days_before)
```

### Phase 3: Background Tasks

#### 3.1 Expiry Reminder Job
```python
# app/jobs/expiry_reminders.py

import asyncio
from datetime import datetime
from app.services.payment_service import PaymentService
from app.core.logging import logger

async def send_expiry_reminders(payment_service: PaymentService):
    """
    Send reminders to users whose subscription expires in 5 days.
    
    Run daily via cron or scheduler.
    """
    expiring = payment_service.get_expiring_subscriptions(days_before=5)
    
    logger.info("expiry_reminders_check", count=len(expiring))
    
    for sub in expiring:
        phone_hash = sub["phone_hash"]
        expiry_date = sub["end_date"].strftime("%Y-%m-%d")
        
        message = (
            f"⏰ Subscription Reminder\n\n"
            f"Your unlimited diagnostics plan expires in 5 days:\n"
            f"{expiry_date}\n\n"
            f"To continue unlimited access, your subscription will auto-renew.\n\n"
            f"To cancel auto-renewal, send: CANCEL\n\n"
            f"Questions? Send: STATUS"
        )
        
        # Send via WhatsApp (Baileys/Twilio)
        try:
            await send_whatsapp_message(phone_hash, message)
            logger.info("expiry_reminder_sent", phone_hash=phone_hash)
        except Exception as e:
            logger.error("expiry_reminder_failed", phone_hash=phone_hash, error=str(e))
```

#### 3.2 Auto-Expire Job
```python
# app/jobs/auto_expire.py

from datetime import datetime
from app.services.payment_service import PaymentService
from app.core.logging import logger

def expire_subscriptions(payment_service: PaymentService):
    """
    Mark expired subscriptions as inactive.
    
    Run daily via cron.
    """
    expired_count = payment_service.payment_repo.expire_old_subscriptions()
    
    logger.info("subscriptions_expired", count=expired_count)
    
    return expired_count
```

### Phase 4: Webhook Updates

#### 4.1 Add CANCEL/RENEW to Webhook
```python
# app/api/routes/webhook.py (baileys_webhook function)

# After existing command checks
if parse_cancel_command(raw_text):
    reply = await handle_cancel_command(phone_hash, payment_service)
    # Send reply and return
    
if parse_renew_command(raw_text):
    reply = await handle_renew_command(raw_text, payment_service)
    # Send reply and return
```

---

## 🎯 User Flow Diagrams

### 1. New User → Free Tier
```
User sends: P0420
  ↓
Check access: has_subscription=False, usage=1/5
  ↓
Serve diagnosis ✅
  ↓
usage_count++
```

### 2. Free User Hits Limit
```
User sends: P0442 (6th diagnostic this week)
  ↓
Check access: usage=6, limit=5
  ↓
Return upgrade prompt:
"⚠️ Free tier limit reached (5/week)
 
To get unlimited diagnostics, subscribe:
SUBSCRIBE <email> <phone>

Only $2/month!"
```

### 3. User Subscribes
```
User sends: SUBSCRIBE john@example.com 0771234567
  ↓
Create transaction (status=pending)
  ↓
Call Paynow sendMobile()
  ↓
Reply: "📱 Check phone for EcoCash prompt"
  ↓
[User approves on phone]
  ↓
Paynow webhook fires → status=paid
  ↓
Create subscription record (expires in 30 days)
  ↓
Reply: "✅ Subscribed! Expires 2026-08-03"
```

### 4. Active Subscriber Usage
```
User sends: P0300
  ↓
Check access: has_subscription=True
  ↓
Serve diagnosis ✅ (no usage check)
```

### 5. User Cancels
```
User sends: CANCEL
  ↓
Set auto_renew=false
  ↓
Reply: "✅ Cancelled. Active until 2026-08-03"
```

### 6. Subscription Expires
```
Cron job runs daily
  ↓
Find subscriptions with end_date < NOW()
  ↓
Set is_active=false
  ↓
Next diagnosis:
  "⚠️ Subscription expired.
   To renew: RENEW <email> <phone>"
```

---

## 📊 Testing Checklist

### Command Tests
- [ ] SUBSCRIBE with valid format
- [ ] SUBSCRIBE with invalid email
- [ ] SUBSCRIBE with invalid phone
- [ ] STATUS (no subscription)
- [ ] STATUS (active subscription)
- [ ] STATUS (expired subscription)
- [ ] CANCEL (no subscription)
- [ ] CANCEL (active subscription)
- [ ] RENEW (expired subscription)

### Flow Tests
- [ ] New user gets 5 free diagnostics
- [ ] 6th diagnostic shows upgrade prompt
- [ ] Payment initiation creates transaction
- [ ] Webhook updates subscription
- [ ] Active subscriber gets unlimited
- [ ] Expired subscriber blocked + shown RENEW
- [ ] Reminder sent 5 days before expiry

---

## 🚀 Implementation Priority

### Must Have (Before Launch)
1. ✅ Database tables
2. ✅ SUBSCRIBE command
3. ✅ STATUS command
4. ✅ Payment initiation
5. ✅ Webhook integration
6. ✅ Free tier enforcement
7. ❌ **CANCEL command** ← **DO THIS NOW**
8. ❌ **RENEW command** ← **DO THIS NOW**

### Nice to Have
9. ❌ Expiry reminders (5-day warning)
10. ❌ Auto-expire cron job
11. ❌ Payment timeout handling

---

## 📝 Next Steps

1. Add `CANCEL` and `RENEW` commands to `payment_commands.py`
2. Add `cancel_subscription()` method to `payment_service.py`
3. Update webhook to handle CANCEL/RENEW
4. Test full payment flow
5. (Optional) Add expiry reminder job

---

**Status**: Core payment flow ✅ 90% complete  
**Missing**: CANCEL/RENEW commands ← **Priority fix**
