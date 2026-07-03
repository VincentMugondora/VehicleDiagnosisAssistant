# Webhook Deployment Guide - Local vs Production

## Overview

Paynow's webhook (`/webhook/paynow`) **requires a public HTTPS URL** to receive payment confirmations. This guide explains the differences between local testing and production deployment.

---

## The Problem

```
┌─────────────┐                    ┌──────────────┐
│   Paynow    │  HTTPS POST        │   Your App   │
│   Servers   │ ─────────────────► │ (localhost)  │
│ (Zimbabwe)  │                    │              │
└─────────────┘                    └──────────────┘
                                          ❌
                  Can't reach localhost
```

**Why it doesn't work:**
- Your local machine (`localhost:8000`) is not accessible from the internet
- Paynow servers in Zimbabwe can't POST to `http://localhost:8000/webhook/paynow`
- Webhook confirmations will **never arrive** during local testing

---

## Solution Overview

| Environment | Webhook URL | How It Works |
|-------------|-------------|--------------|
| **Local Dev** | Use ngrok tunnel | Temporary public HTTPS URL → localhost |
| **Staging** | Real domain + HTTPS | Deploy to test server with SSL |
| **Production** | Real domain + HTTPS | Deploy to production server with SSL |

---

## Local Development Setup (Using ngrok)

### Step 1: Install ngrok

```bash
# Windows (using Chocolatey)
choco install ngrok

# Or download from: https://ngrok.com/download
```

### Step 2: Start Your Backend

```bash
# Terminal 1 - Start FastAPI
uvicorn app.main:app --reload --port 8000
```

### Step 3: Start ngrok Tunnel

```bash
# Terminal 2 - Start ngrok
ngrok http 8000
```

**Output:**
```
ngrok                                                           (Ctrl+C to quit)

Session Status                online
Account                       your-email@example.com (Plan: Free)
Version                       3.x.x
Region                        United States (us)
Latency                       -
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://abc123.ngrok.io -> http://localhost:8000

Connections                   ttl     opn     rt1     rt5     p50     p90
                              0       0       0.00    0.00    0.00    0.00
```

### Step 4: Update .env

```bash
# Use the ngrok HTTPS URL (changes every restart on free plan)
PAYNOW_RESULT_URL=https://abc123.ngrok.io/webhook/paynow
```

### Step 5: Configure Paynow Dashboard

1. Login to https://www.paynow.co.zw/
2. Go to: Settings → Integration
3. Set **Result URL** to: `https://abc123.ngrok.io/webhook/paynow`
4. Save

### Step 6: Restart Backend

```bash
# Restart to pick up new PAYNOW_RESULT_URL
# Press Ctrl+C, then:
uvicorn app.main:app --reload --port 8000
```

### Step 7: Test Webhook

```bash
# Test that ngrok is forwarding to your app
curl https://abc123.ngrok.io/webhook/paynow

# Should see FastAPI response (even if minimal)
```

### ngrok Web Interface

Visit `http://127.0.0.1:4040` to see:
- Live requests to your tunnel
- Request/response details
- Webhook POSTs from Paynow
- Very useful for debugging!

---

## ngrok Limitations & Workarounds

### Free Plan Limitations

| Limitation | Impact | Workaround |
|------------|--------|------------|
| URL changes on restart | Must update Paynow dashboard each time | Use paid plan ($8/month) for static URL |
| 40 requests/minute | May hit limit during testing | Upgrade to paid plan (120 req/min) |
| 1 online ngrok process | Can't run multiple apps | Use different ports or paid plan |

### Paid Plan Benefits ($8/month)

- **Static subdomain**: `https://yourname.ngrok.io` (never changes)
- **Higher limits**: 120 requests/minute
- **Multiple tunnels**: Run several apps simultaneously
- **Custom domains**: Use your own domain

**Recommendation for development:** Free plan is fine for initial testing, upgrade if webhook URL changes become annoying.

---

## Alternative: localtunnel (Free)

If ngrok's changing URLs are frustrating:

```bash
# Install
npm install -g localtunnel

# Start
lt --port 8000 --subdomain myapp

# Gets: https://myapp.loca.lt
```

**Pros:**
- Free
- Can request specific subdomain

**Cons:**
- Less reliable than ngrok
- May have downtime
- Requires npm/node

---

## Production Deployment

### Requirements

1. **Domain name** (e.g., `diagnostics.yourdomain.com`)
2. **HTTPS certificate** (Let's Encrypt, Cloudflare, etc.)
3. **Public server** (VPS, cloud provider, etc.)

### Deployment Options

#### Option A: Traditional VPS (DigitalOcean, Linode, etc.)

```bash
# 1. Deploy FastAPI app to VPS
ssh user@your-server.com
cd /opt/vehicle-diagnostics
git pull
pip install -r requirements.txt

# 2. Configure nginx as reverse proxy
sudo nano /etc/nginx/sites-available/diagnostics

server {
    listen 80;
    server_name diagnostics.yourdomain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name diagnostics.yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/diagnostics.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/diagnostics.yourdomain.com/privkey.pem;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# 3. Get SSL certificate
sudo certbot --nginx -d diagnostics.yourdomain.com

# 4. Run app with systemd
sudo nano /etc/systemd/system/diagnostics.service

[Unit]
Description=Vehicle Diagnostics API
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/vehicle-diagnostics
ExecStart=/opt/vehicle-diagnostics/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target

# 5. Start service
sudo systemctl enable diagnostics
sudo systemctl start diagnostics
```

**Update .env:**
```bash
PAYNOW_RESULT_URL=https://diagnostics.yourdomain.com/webhook/paynow
```

**Configure Paynow:**
- Set Result URL to: `https://diagnostics.yourdomain.com/webhook/paynow`

---

#### Option B: Railway.app (Easiest)

```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login
railway login

# 3. Initialize project
cd /path/to/VehicleDiagnosisAssistant
railway init

# 4. Add environment variables via Railway dashboard
# (PAYNOW_INTEGRATION_ID, PAYNOW_INTEGRATION_KEY, SUPABASE_URL, etc.)

# 5. Deploy
railway up

# Gets: https://yourapp.up.railway.app
```

**Automatic HTTPS** - Railway provides SSL automatically.

**Update webhook:**
```bash
PAYNOW_RESULT_URL=https://yourapp.up.railway.app/webhook/paynow
```

---

#### Option C: Vercel/Netlify (Serverless)

⚠️ **Not recommended** for this app because:
- Background polling task won't work in serverless
- Need persistent process for payment poller
- Better suited for traditional VPS or PaaS

---

#### Option D: Render.com (Recommended for Beginners)

```bash
# 1. Push code to GitHub
git push origin main

# 2. Go to: https://render.com
# 3. New Web Service → Connect GitHub repo
# 4. Configure:
#    - Build Command: pip install -r requirements.txt
#    - Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
#    - Environment: Add all .env variables
# 5. Deploy

# Gets: https://yourapp.onrender.com (with free SSL)
```

**Update webhook:**
```bash
PAYNOW_RESULT_URL=https://yourapp.onrender.com/webhook/paynow
```

---

## Configuration Changes Summary

### Local Development
```bash
# .env (changes every ngrok restart on free plan)
PAYNOW_RESULT_URL=https://abc123.ngrok.io/webhook/paynow

# Paynow Dashboard
Result URL: https://abc123.ngrok.io/webhook/paynow

# Notes:
- Must update dashboard when ngrok URL changes
- Use ngrok web interface to debug: http://127.0.0.1:4040
```

### Production
```bash
# .env (static - never changes)
PAYNOW_RESULT_URL=https://diagnostics.yourdomain.com/webhook/paynow

# Paynow Dashboard
Result URL: https://diagnostics.yourdomain.com/webhook/paynow

# Notes:
- Set once, forget
- Must have valid SSL certificate
- Monitor webhook delivery in logs
```

---

## Testing Webhook Delivery

### During Development (ngrok)

**Terminal 1 - Backend logs:**
```bash
uvicorn app.main:app --reload --port 8000
# Watch for: "paynow_webhook_received"
```

**Terminal 2 - ngrok:**
```bash
ngrok http 8000
# Note the HTTPS URL
```

**Browser - ngrok inspector:**
```
http://127.0.0.1:4040
# See all webhook POSTs from Paynow in real-time
```

**Manual test:**
```bash
curl -X POST https://abc123.ngrok.io/webhook/paynow \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "reference=TEST&amount=2.00&status=Paid"

# Should see request in:
# 1. Backend logs
# 2. ngrok inspector
```

### In Production

**Check logs:**
```bash
# Systemd service logs
sudo journalctl -u diagnostics -f

# Or app logs
tail -f /var/log/diagnostics/app.log

# Look for:
grep "paynow_webhook" app.log
```

**Monitor webhook delivery:**
```sql
-- Check recent transactions
SELECT 
    order_reference,
    status,
    created_at,
    paid_at,
    EXTRACT(EPOCH FROM (paid_at - created_at)) as seconds_to_confirm
FROM transactions
WHERE created_at > NOW() - INTERVAL '24 hours'
ORDER BY created_at DESC;
```

---

## Troubleshooting

### Webhook not being called

**Symptoms:**
- Payment initiated successfully
- User approves payment on phone
- Transaction stuck in "pending"
- No logs showing webhook received

**Causes & Fixes:**

1. **URL not reachable from internet**
   ```bash
   # Test from external service
   curl https://your-domain.com/webhook/paynow
   # Should return 200 or 405 (Method Not Allowed), not timeout
   ```

2. **Wrong URL in Paynow dashboard**
   - Login to Paynow dashboard
   - Check Settings → Integration → Result URL
   - Must exactly match PAYNOW_RESULT_URL in .env

3. **SSL certificate invalid**
   ```bash
   # Test SSL
   curl -v https://your-domain.com/webhook/paynow
   # Look for SSL handshake errors
   ```

4. **Firewall blocking Paynow**
   - Allow HTTPS (443) inbound
   - Check server firewall rules
   - Check cloud provider security groups

5. **ngrok session expired (local dev)**
   - Free plan tunnels expire after 8 hours
   - Restart ngrok
   - Update Paynow dashboard with new URL

### Webhook called but not processing

**Check logs for:**
```bash
grep "paynow_webhook_error" app.log
```

**Common issues:**
- Hash verification failed (wrong integration key)
- Missing required fields in POST data
- Database connection error
- Transaction not found in database

---

## Deployment Checklist

### Before Going Live

Local Development:
- [ ] Install ngrok
- [ ] Start ngrok tunnel
- [ ] Update .env with ngrok URL
- [ ] Update Paynow dashboard with ngrok URL
- [ ] Test webhook with manual curl
- [ ] Verify webhook appears in ngrok inspector
- [ ] Test full payment flow (if using real credentials)

Production Deployment:
- [ ] Domain name configured
- [ ] SSL certificate installed
- [ ] HTTPS working (test with browser)
- [ ] Update .env with production webhook URL
- [ ] Update Paynow dashboard with production URL
- [ ] Test webhook endpoint: `curl https://yourdomain.com/webhook/paynow`
- [ ] Monitor logs after first real payment
- [ ] Set up alerting for webhook failures

---

## Quick Reference

| Need | Local Dev | Production |
|------|-----------|------------|
| Tool | ngrok | nginx + SSL or PaaS |
| URL | `https://random.ngrok.io` | `https://yourdomain.com` |
| Changes | Every ngrok restart | Never |
| Update Paynow | Each time | Once |
| Cost | Free (with limits) | $5-20/month |
| SSL | Auto by ngrok | Certbot or provider |

---

**Key Takeaway:** Webhooks require public HTTPS. Use ngrok for local testing, real domain + SSL for production.
