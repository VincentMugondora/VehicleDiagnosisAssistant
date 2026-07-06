# Paynow Payment Commands - User Guide

Quick reference for all payment-related WhatsApp commands.

---

## 💳 Payment Commands

### SUBSCRIBE

**Purpose:** Start a monthly subscription for unlimited diagnostics

**Format:**
```
SUBSCRIBE <email> <phone>
```

**Example:**
```
SUBSCRIBE john@example.com 0771234567
```

**What happens:**
1. Payment request sent to Paynow
2. You receive EcoCash prompt on your phone
3. Approve payment with your EcoCash PIN
4. Subscription activates automatically (1-2 minutes)
5. You get 30 days unlimited diagnostics

**Response:**
```
✅ SUBSCRIBE initiated!

📱 Check your phone (0771234567) for EcoCash prompt
💰 Amount: $2.00 USD
🎯 Plan: Monthly Unlimited

Approve the payment on your phone

⏱️ You have 15 minutes to approve.

Order: SUB-20260706130946-f9253aa6

Reply STATUS to check payment progress.
```

---

### STATUS

**Purpose:** Check your subscription status or usage

**Format:**
```
STATUS
```

**Response (Active Subscriber):**
```
✅ Active Subscription

📱 Plan: Monthly Unlimited
🎯 Status: Active
📅 Expires: 2026-08-05 13:10 UTC
🔄 Renewal: ❌ Auto-renew cancelled

You have unlimited diagnostics until expiration.

To cancel auto-renewal: CANCEL
```

**Response (Free Tier):**
```
📊 Free Tier Status

✅ Used: 2/5 this week
🎯 Remaining: 3

Upgrade to unlimited:
SUBSCRIBE <email> <phone>

Only $2/month!
```

**Response (New User):**
```
👋 Welcome!

You have 5 free diagnostics per week.

Send an OBD code to get started:
Example: P0420

For unlimited diagnostics ($2/month):
SUBSCRIBE <email> <phone>

Need help? Send: HELP
```

---

### RENEW

**Purpose:** Renew an expired subscription

**Format:**
```
RENEW <email> <phone>
```

**Example:**
```
RENEW john@example.com 0771234567
```

**What happens:**
- Same as SUBSCRIBE
- Works even if previous subscription expired
- Cannot use if subscription is still active

**Response (Already Active):**
```
✅ You already have an active subscription!

📅 Expires: 2026-08-05

Your plan will auto-renew unless you send CANCEL.

Reply STATUS for details.
```

---

### CANCEL

**Purpose:** Cancel auto-renewal (keep current subscription until expiration)

**Format:**
```
CANCEL
```

**What happens:**
- Auto-renewal disabled
- You keep access until expiration date
- No refunds (keeps current period active)
- After expiration, you return to free tier

**Response:**
```
✅ Auto-renewal cancelled.

📅 You'll keep unlimited access until:
2026-08-05

After that, you'll return to free tier (5 diagnostics/week).

💳 No further charges will be made.

To re-subscribe anytime:
SUBSCRIBE <email> <phone>
```

**Important Notes:**
- Does NOT cancel immediately
- Does NOT refund current period
- You keep access until natural expiration
- Can re-subscribe anytime

---

### HELP

**Purpose:** Show available commands

**Format:**
```
HELP
```

**Response:**
```
🔧 Vehicle Diagnosis Assistant

📋 Available Commands:

🔍 Diagnostics:
  • Send OBD code: P0420
  • Follow-up: explain further

💳 Payment:
  • STATUS - Check subscription
  • CANCEL - Stop auto-renewal

ℹ️ Info:
  • HELP - Show this message

📧 Example:
  SUBSCRIBE john@example.com 0771234567
```

---

## 🔍 Diagnostic Commands

### Send OBD Code

**Purpose:** Get diagnosis for a fault code

**Format:**
```
<OBD-CODE>
```

**Examples:**
```
P0420
P0171
P0300
```

**Response Example:**
```
*Fault code:* P0420
*System:* Emissions

*What it means:*
Catalyst System Efficiency Below Threshold (Bank 1)

*Likely causes:*
• Failing catalytic converter
• Faulty O2 sensors
• Engine misfire damage
• Exhaust leak

*Recommended action:*
1. Replace catalytic converter
2. Test O2 sensors
3. Check for exhaust leaks
4. Fix any misfires first

_Always confirm with live scanner data before replacing parts._
```

**Access Control:**
- **Free tier:** 5 diagnostics per week
- **Subscribed:** Unlimited diagnostics

---

## 💰 Pricing

### Free Tier
- **Cost:** Free
- **Limit:** 5 diagnostics per week
- **Reset:** Every Monday at midnight
- **No payment required**

### Monthly Subscription
- **Cost:** $2.00 USD
- **Duration:** 30 days from payment
- **Access:** Unlimited diagnostics
- **Auto-renew:** No (default off)

---

## 📞 Payment Methods

### Supported
- ✅ **EcoCash** (Zimbabwe)
- ✅ **Mobile Money**

### Payment Flow
1. Send SUBSCRIBE command via WhatsApp
2. Receive EcoCash USSD prompt on your phone
3. Enter PIN to approve
4. Confirmation sent within 1-2 minutes
5. Access activated automatically

---

## ⚠️ Important Notes

### Test Mode (Current)
- Only works with test phone numbers
- No real money charged
- Test numbers: 0771111111, 0772222222, 0773333333
- Payments auto-approve for testing

### Production Mode (After Activation)
- Works with any Zimbabwe phone number
- Real EcoCash payments
- Actual money charged
- Manual approval required

---

## 🛟 Troubleshooting

### "Payment not detected"

**Problem:** Approved payment but subscription not activated

**Solution:**
1. Wait 2-3 minutes (poller runs every 30 seconds)
2. Send STATUS to check
3. If still pending after 5 minutes, contact support

---

### "Already have pending payment"

**Problem:** Previous payment still processing

**Solution:**
1. Check your phone for EcoCash prompt
2. Approve if still waiting
3. Send STATUS to check progress
4. Wait for timeout (15 minutes) if abandoned

---

### "Free tier limit reached"

**Problem:** Used all 5 free diagnostics this week

**Solution:**
1. Wait until Monday for reset, OR
2. Subscribe for unlimited:
   ```
   SUBSCRIBE your@email.com 0771234567
   ```

---

### "Subscription expired"

**Problem:** 30 days elapsed since last payment

**Solution:**
1. Renew subscription:
   ```
   RENEW your@email.com 0771234567
   ```
2. Or use free tier (5/week)

---

## 📧 Support

**Email:** support@paynow.co.zw  
**Phone:** +263 (24) 2745-123  

**Account Details:**
- Integration ID: 25487
- Integration Name: NockDiagnostics Ai
- Company: PaulNock inc

---

## 🔒 Privacy & Security

### Data Stored
- Phone number (hashed)
- Email address
- Payment transactions
- Usage statistics

### NOT Stored
- EcoCash PIN
- Full phone number (plain text)
- Payment card details

### Security Measures
- Phone numbers hashed with SHA-256
- HTTPS/TLS encryption
- Paynow secure payment gateway
- No direct handling of payment credentials

---

**Last Updated:** 2026-07-06  
**Version:** 1.0  
**Status:** Test Mode Active
