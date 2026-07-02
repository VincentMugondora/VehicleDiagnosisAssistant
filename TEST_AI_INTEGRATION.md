# 🧪 AI Integration Test Guide

## Current Status

✅ **Baileys Server**: Fully configured and ready  
⚠️ **Backend API**: Needs to be started  
✅ **Security**: All security features enabled  
✅ **API Key**: Generated and configured  

---

## Step 1: Start the Vehicle Diagnosis Backend

Open a **new terminal** and run:

```bash
cd C:\Users\vinmu\Desktop\VehicleDiagnosisAssistant

# Activate virtual environment
venv\Scripts\activate

# Start FastAPI backend on port 8001
uvicorn app.main:app --reload --port 8001
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8001
INFO:     Started server process
{"event": "app_starting", ...}
{"event": "supabase_connected", ...}
INFO:     Application startup complete.
```

✅ Leave this terminal running!

---

## Step 2: Start Baileys WhatsApp Server

Open **another terminal** and run:

```bash
cd C:\Users\vinmu\Desktop\VehicleDiagnosisAssistant\baileys-server

# Start Baileys server
npm start
```

**Expected output:**
```
🚀 Baileys WhatsApp Server v2.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📡 Server: http://localhost:3000
🔗 Backend: http://localhost:8001/webhook/baileys
🔒 Security: Enabled
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Then a QR code will appear. Scan it with WhatsApp!

---

## Step 3: Test AI Integration

Once connected, send this message to your WhatsApp number:

```
P0420 Toyota Camry 2015
```

### Expected Flow:
1. ✅ Message received by Baileys server
2. ✅ Forwarded to FastAPI backend (port 8001)
3. ✅ AI processes the OBD code
4. ✅ Response sent back to WhatsApp

### Sample Response:
```
🔧 P0420 - Catalyst System Efficiency Below Threshold (Bank 1)

📋 DESCRIPTION
The catalytic converter is not working efficiently...

⚠️ CAUSES
• Worn catalytic converter
• Oxygen sensor malfunction
• Exhaust leak
...

🔍 RECOMMENDED CHECKS
1. Check oxygen sensors
2. Inspect catalytic converter
3. Scan for additional codes
...
```

---

## Configuration Details

### Baileys Server (.env)
```
BACKEND_URL=http://localhost:8001/webhook/baileys
BAILEYS_API_KEY=a3bb4b6660552743096545286d5c6677d820b0326542bc8228d428c04bca0298
PORT=3000
REQUEST_TIMEOUT=60000
LOG_LEVEL=info
NODE_ENV=development
```

### Backend (.env)
```
BAILEYS_API_KEY=a3bb4b6660552743096545286d5c6677d820b0326542bc8228d428c04bca0298
SUPABASE_URL=https://your-project.supabase.co
AI_PROVIDER=cohere
COHERE_API_KEY=your-cohere-api-key-here
```

✅ Both use the **same API key** for authentication!

---

## Monitoring

### Check Baileys Server Health
```bash
curl http://localhost:3000/health
```

### Check Backend Health
```bash
curl http://localhost:8001/health
```

### View Metrics (with auth)
```bash
curl -H "X-API-Key: a3bb4b6660552743096545286d5c6677d820b0326542bc8228d428c04bca0298" \
  http://localhost:3000/metrics
```

### Watch Logs

**Baileys logs** (in baileys-server terminal):
```json
{"level":"info","requestId":"uuid","method":"POST","msg":"Incoming request"}
{"level":"info","from":"1234567890@s.whatsapp.net","msg":"Message received"}
{"level":"info","chunks":1,"msg":"Reply sent successfully"}
```

**Backend logs** (in backend terminal):
```json
{"event": "baileys_webhook_received", "phone_hash": "..."}
{"event": "message_routing", "type": "obd_code"}
{"event": "obd_diagnosis_complete", "code": "P0420"}
```

---

## Troubleshooting

### Backend Not Responding
**Check:**
```bash
# Is backend running?
curl http://localhost:8001/health

# Test webhook directly
curl -X POST http://localhost:8001/webhook/baileys \
  -H "Content-Type: application/json" \
  -H "X-API-Key: a3bb4b6660552743096545286d5c6677d820b0326542bc8228d428c04bca0298" \
  -d '{
    "from": "1234567890@s.whatsapp.net",
    "text": "P0420 Toyota Camry 2015",
    "message_id": "test_123"
  }'
```

### Timeout Errors
If AI takes too long, increase timeout in baileys-server/.env:
```
REQUEST_TIMEOUT=120000  # 2 minutes
```

### API Key Mismatch
Ensure BOTH .env files have the same `BAILEYS_API_KEY`:
- `VehicleDiagnosisAssistant/.env`
- `VehicleDiagnosisAssistant/baileys-server/.env`

### WhatsApp Not Connecting
```bash
# Delete session and re-scan QR
rm -rf auth_info_baileys
npm start
```

---

## Success Indicators

✅ **Baileys Server**
- "WhatsApp Connected!" message
- "Ready to receive messages"
- Connection status: "connected"

✅ **Backend**
- "app_starting" log
- "supabase_connected" log
- Health endpoint returns 200

✅ **Integration**
- Message received log in Baileys
- Request forwarded to backend
- AI response received
- Reply sent to WhatsApp

---

## Test Commands

### Manual Send (via Baileys API)
```bash
curl -X POST http://localhost:3000/send \
  -H "Content-Type: application/json" \
  -H "X-API-Key: a3bb4b6660552743096545286d5c6677d820b0326542bc8228d428c04bca0298" \
  -d '{
    "to": "YOUR_PHONE_NUMBER",
    "message": "Test message from API"
  }'
```

### Check Metrics
```bash
curl -H "X-API-Key: a3bb4b6660552743096545286d5c6677d820b0326542bc8228d428c04bca0298" \
  http://localhost:3000/metrics | python -m json.tool
```

---

## Architecture

```
WhatsApp User
    │
    ↓ (message)
Baileys Server (port 3000)
    │
    ↓ (HTTP POST with X-API-Key)
FastAPI Backend (port 8001)
    │
    ├→ Supabase (database)
    ├→ Cohere AI (diagnosis)
    └→ Returns JSON response
    │
    ↓ (response)
Baileys Server
    │
    ↓ (message)
WhatsApp User
```

---

## Next Steps

1. ✅ Start backend (Step 1)
2. ✅ Start Baileys server (Step 2)
3. ✅ Scan QR code
4. ✅ Send test message (Step 3)
5. ✅ Verify AI response
6. 🎉 **Success!**

---

**Pro Tip**: Keep both terminals visible side-by-side to watch the logs flow in real-time!

**Documentation**:
- Baileys Server: `baileys-server/README.md`
- Security: `baileys-server/SECURITY.md`
- Backend: `QUICKSTART.md`
