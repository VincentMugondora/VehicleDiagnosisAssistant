# ⚡ Quick Start - v2.0.0

Get your secure WhatsApp server running in 5 minutes!

---

## Step 1: Generate API Key (30 seconds)

```bash
# Copy this command and run it:
openssl rand -hex 32
```

**Save the output!** You'll need it in Step 2.

> 📋 Example output: `a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456`

---

## Step 2: Configure Environment (1 minute)

```bash
# Create your .env file
cp .env.example .env
```

Edit `.env` and set these TWO required variables:

```bash
# Paste the API key from Step 1
BAILEYS_API_KEY=paste-your-key-here

# Set your backend URL (adjust if needed)
BACKEND_URL=http://localhost:8000/webhook/baileys
```

**That's it!** All other settings have sensible defaults.

---

## Step 3: Install & Start (2 minutes)

```bash
# Install dependencies (first time only)
npm install

# Start the server
npm start
```

You should see:
```
🚀 Baileys WhatsApp Server v2.0
📡 Server: http://localhost:3000
🔗 Backend: http://localhost:8000/webhook/baileys
🔒 Security: Enabled
```

---

## Step 4: Scan QR Code (1 minute)

A QR code will appear in your terminal.

**On your phone:**
1. Open WhatsApp
2. Tap **⋮ Menu** (or **Settings** on iPhone)
3. Tap **Linked Devices**
4. Tap **Link a Device**
5. Scan the QR code

✅ When connected, you'll see:
```
✅ WhatsApp Connected!
📱 Ready to receive messages
```

---

## Step 5: Test It! (30 seconds)

Send a message to your WhatsApp number:

```
P0420 Toyota Camry 2015
```

You should receive a diagnosis response!

---

## ✅ You're Done!

Your server is now:
- 🔒 **Secure** - Enterprise-grade security
- 🚀 **Fast** - Optimized performance  
- 📊 **Monitored** - Health checks enabled
- 🛡️ **Protected** - Rate limiting active

---

## 🔍 Quick Health Check

```bash
# Check if server is healthy
curl http://localhost:3000/health
```

Expected response:
```json
{
  "status": "healthy",
  "connection": "connected",
  "uptime": 123,
  "timestamp": "2026-07-02T12:00:00.000Z"
}
```

---

## 📡 Send Messages via API

Now that it's running, you can send messages programmatically:

```bash
curl -X POST http://localhost:3000/send \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{
    "to": "1234567890",
    "message": "Hello from the API!"
  }'
```

**Remember:** Replace `your-api-key-here` with your actual key from `.env`

---

## 🐛 Troubleshooting

### Issue: "Missing required environment variables"
**Fix:**
```bash
# Make sure you created .env
cp .env.example .env

# Edit it with your API key
nano .env
```

### Issue: "Weak environment variable values"
**Fix:**
```bash
# Generate a new strong key
openssl rand -hex 32

# Paste it in .env as BAILEYS_API_KEY
```

### Issue: QR code not showing
**Fix:**
```bash
# Make sure you're in the right directory
cd baileys-server

# Try again
npm start
```

### Issue: Connection keeps dropping
**Fix:**
```bash
# Delete session and re-scan QR
rm -rf auth_info_baileys
npm start
# Scan the new QR code
```

### Issue: Backend not responding
**Fix:**
```bash
# Check if FastAPI is running
curl http://localhost:8000/healthz

# If not, start your FastAPI server first
```

---

## 📚 Next Steps

Now that you're running:

### Optional Configuration
Edit `.env` to customize:
- `PORT` - Change server port (default: 3000)
- `REQUEST_TIMEOUT` - Increase for slow AI models (default: 60000ms)
- `RATE_LIMIT_MAX` - Adjust rate limits (default: 20/min)
- `LOG_LEVEL` - Change logging verbosity (default: info)

### View Detailed Metrics
```bash
curl -H "X-API-Key: your-key" http://localhost:3000/metrics
```

### Run Security Tests
```bash
./test-security.sh
```

### Read Full Documentation
- `README.md` - Complete guide
- `SECURITY.md` - Security features
- `UPGRADE_SUMMARY.md` - What changed in v2.0

---

## 🚀 Production Deployment

Ready for production? Follow the checklist in `UPGRADE_SUMMARY.md`:

**Quick version:**
1. Set `NODE_ENV=production` in `.env`
2. Set up reverse proxy (nginx) for HTTPS
3. Use PM2 or systemd for process management
4. Configure firewall
5. Set up monitoring

**Example with PM2:**
```bash
npm install -g pm2
pm2 start index.js --name baileys-server
pm2 startup
pm2 save
```

---

## 🎉 Success!

You now have a **production-ready, enterprise-secure** WhatsApp integration!

**Key Features Enabled:**
- ✅ API Key Authentication
- ✅ Rate Limiting (20/min)
- ✅ Input Validation
- ✅ Security Headers
- ✅ Structured Logging
- ✅ Health Monitoring
- ✅ Graceful Shutdown
- ✅ Exponential Backoff
- ✅ Request Tracking
- ✅ Error Handling

---

## 🆘 Need Help?

1. Check logs: `npm start`
2. Test health: `curl http://localhost:3000/health`
3. Review `README.md` troubleshooting
4. Check `SECURITY.md` for best practices

---

**Version:** 2.0.0  
**Time to Deploy:** ~5 minutes  
**Security Level:** Enterprise-Grade ✅
