# 🚀 Launch Checklist - Vehicle Diagnosis Assistant

**Complete this checklist to launch your system**

---

## ✅ Pre-Launch Checklist

### 1. Network & Credentials

- [ ] **Internet connection** is working
  ```bash
  ping google.com
  ping supabase.com
  ```

- [ ] **Supabase credentials** are in `.env`
  ```bash
  # Check these are set:
  grep SUPABASE_URL .env
  grep SUPABASE_SERVICE_KEY .env
  ```

- [ ] **AI API key** is configured
  ```bash
  # For Cohere:
  grep COHERE_API_KEY .env
  
  # OR for Gemini:
  grep GEMINI_API_KEY .env
  ```

- [ ] **Baileys API key** matches backend
  ```bash
  # Both should have same key:
  grep BAILEYS_API_KEY .env
  grep BAILEYS_API_KEY baileys-server/.env
  ```

---

## 📦 Step 1: Load Database (One-Time)

**Important:** You need internet connection for this step.

```bash
# Activate virtual environment
venv\Scripts\activate

# Load 250 OBD codes into Supabase
python scripts/load_obd_codes.py
```

**Expected Output:**
```
============================================================
OBD-II Code Loader
============================================================

Loading OBD codes from: data/obd_codes_dataset.json
Found 250 codes to load
Dataset version: 1.0

Progress: 50/250 codes processed (20%)
Progress: 100/250 codes processed (40%)
Progress: 150/250 codes processed (60%)
Progress: 200/250 codes processed (80%)
Progress: 250/250 codes processed (100%)

============================================================
SUMMARY
============================================================
Total codes in dataset: 250
Successfully inserted/updated: 250
Errors: 0

[SUCCESS] All codes loaded successfully!

Database now contains 250 OBD codes
```

**If You Get Errors:**

❌ **Error: `[Errno 11001] getaddrinfo failed`**
- **Cause:** No internet connection or DNS issue
- **Fix:** 
  ```bash
  # Test internet
  ping 8.8.8.8
  ping supabase.com
  
  # Check Supabase URL
  python -c "from app.core.config import settings; print(settings.supabase_url)"
  ```

❌ **Error: `Authentication failed`**
- **Cause:** Invalid Supabase credentials
- **Fix:** 
  1. Go to https://app.supabase.com
  2. Select your project
  3. Settings → API
  4. Copy `URL` and `service_role key`
  5. Update `.env`

❌ **Error: `Table 'obd_codes' does not exist`**
- **Cause:** Database schema not initialized
- **Fix:**
  ```bash
  # Run migration SQL
  # Copy contents of: supabase/migrations/001_initial_schema.sql
  # Paste into: Supabase Dashboard → SQL Editor → Run
  ```

---

## 🧪 Step 2: Test Offline Components

```bash
# Run tests (no backend needed)
python test_system_e2e.py
```

**Expected Results:**
```
[PASS] - Configuration check
[PASS] - Code validation (11/11 tests)
[PASS] - Message parsing (4/5 tests)
[PASS] - Database connection
[PASS] - Database has codes (250 found)
```

---

## 🔧 Step 3: Start Backend

Open a **new terminal** (keep it running):

```bash
cd VehicleDiagnosisAssistant

# Activate virtual environment
venv\Scripts\activate

# Start FastAPI backend
uvicorn app.main:app --reload --port 8001
```

**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8001
INFO:     Started server process [12345]
{"event": "app_starting", "env": "development"}
{"event": "supabase_connected"}
INFO:     Application startup complete.
```

**Health Check:**
```bash
# In another terminal:
curl http://localhost:8001/health
```

Should return:
```json
{
  "status": "healthy",
  "timestamp": "2026-07-02T12:00:00Z",
  "database": "connected"
}
```

---

## 🧪 Step 4: Test Backend Integration

```bash
# Full test suite (requires backend running)
python test_system_e2e.py
```

**Expected: 7/7 tests passing!** ✅

---

## 📱 Step 5: Start Baileys WhatsApp Server

Open **another new terminal** (keep it running):

```bash
cd baileys-server

# Start Baileys
npm start
```

**Expected Output:**
```
========================================================================
  Baileys WhatsApp Server v2.0
========================================================================
📡 Server: http://localhost:3000
🔗 Backend: http://localhost:8001/webhook/baileys
🔒 Security: Enabled
========================================================================

[QR CODE APPEARS HERE]

Open WhatsApp → Settings → Linked Devices
Tap "Link a Device" and scan the code above
```

**Scan QR Code** with your phone, then you should see:
```
[SUCCESS] WhatsApp Connected!
📱 Ready to receive messages
```

---

## 🎯 Step 6: Test Via WhatsApp

Send these messages to your WhatsApp number:

### Test 1: Simple Code
```
P0420
```

**Expected Response:**
```
🔧 P0420 - Catalyst System Efficiency Below Threshold (Bank 1)

📋 DESCRIPTION
The catalytic converter is not working efficiently...

⚠️ CAUSES
• Worn catalytic converter
• Faulty oxygen sensor
• Exhaust leak
...

🔍 RECOMMENDED CHECKS
1. Inspect oxygen sensors
2. Check for exhaust leaks
3. Test catalytic converter efficiency
...
```

### Test 2: Code with Vehicle
```
P0420 Toyota Camry 2015
```

**Expected:** More specific response for Toyota Camry 2015!

### Test 3: Followup Question (NEW FEATURE!)
```
is this expensive to fix?
```

**Expected:** AI responds with context about P0420 you just diagnosed!

### Test 4: Another Code
```
P0171
```

### Test 5: Followup About New Code
```
what causes this?
```

**Expected:** AI responds about P0171 (not P0420)!

---

## 📊 Step 7: Monitor Logs

### Backend Logs (Terminal 1)
```json
{"event": "baileys_webhook_received", "phone_hash": "abc123...", "message_id": "..."}
{"event": "message_parsed", "code": "P0420", "vehicle_detected": true}
{"event": "obd_lookup_success", "code": "P0420", "source": "local_db"}
{"event": "last_diagnosis_stored", "code": "P0420"}
```

### Baileys Logs (Terminal 2)
```json
{"level":"info","from":"1234567890@s.whatsapp.net","msg":"Message received"}
{"level":"info","chunks":1,"msg":"Reply sent successfully"}
```

---

## ✅ Success Criteria

Your system is **fully operational** when:

- ✅ Database has 250 OBD codes
- ✅ Backend returns 200 on `/health`
- ✅ Baileys shows "WhatsApp Connected"
- ✅ Test messages get instant responses
- ✅ Followup questions use context
- ✅ Logs show successful processing

---

## 🐛 Troubleshooting

### Backend Won't Start

**Error:** `ModuleNotFoundError: No module named 'app'`
```bash
# Make sure you're in the right directory
cd VehicleDiagnosisAssistant
pwd  # Should show: .../VehicleDiagnosisAssistant

# Make sure venv is activated
venv\Scripts\activate
which python  # Should show venv path

# Reinstall if needed
pip install -r requirements.txt
```

### Database Empty After Loading

```bash
# Verify codes were loaded
python -c "
from app.db.client import get_supabase_client
client = get_supabase_client()
result = client.table('obd_codes').select('code', count='exact').execute()
print(f'Total codes: {result.count}')
"
```

### Baileys Won't Connect

```bash
# Delete session and retry
rm -rf baileys-server/auth_info_baileys
cd baileys-server
npm start
# Scan new QR code
```

### AI Not Working

```bash
# Test AI provider directly
python -c "
from app.services.ai_client import AIClient
import asyncio

async def test():
    client = AIClient()
    result = await client.complete('Hello', temperature=0.3, max_tokens=10)
    print(f'AI Response: {result}')

asyncio.run(test())
"
```

---

## 📈 Production Checklist

Before deploying to production:

- [ ] Set `NODE_ENV=production` in both `.env` files
- [ ] Use strong API keys (32+ characters)
- [ ] Set up reverse proxy (nginx) for HTTPS
- [ ] Configure firewall
- [ ] Set up process manager (PM2 for Node, systemd for Python)
- [ ] Enable monitoring (check `/health` endpoint)
- [ ] Set up log rotation
- [ ] Backup database regularly
- [ ] Test failover scenarios
- [ ] Document runbook for operations team

---

## 📚 Quick Reference

### Useful Commands

```bash
# Check backend health
curl http://localhost:8001/health

# Check Baileys health  
curl http://localhost:3000/health

# View database codes
python -c "from app.db.client import get_supabase_client; client = get_supabase_client(); print(client.table('obd_codes').select('code').limit(10).execute().data)"

# View recent messages
python -c "from app.db.client import get_supabase_client; client = get_supabase_client(); print(client.table('message_logs').select('request_text,created_at').order('created_at',desc=True).limit(5).execute().data)"

# Test webhook directly
curl -X POST http://localhost:8001/webhook/baileys \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_KEY_HERE" \
  -d '{"from":"test@s.whatsapp.net","text":"P0420","message_id":"test123"}'
```

### Key Files

- **Backend:** `app/main.py`, `app/services/message_router.py`
- **Config:** `.env`, `baileys-server/.env`
- **Data:** `data/obd_codes_dataset.json`
- **Tests:** `test_system_e2e.py`
- **Docs:** `docs/ARCHITECTURE.md`, `docs/DEVELOPER_GUIDE.md`

### Port Reference

- **8001** - FastAPI Backend
- **3000** - Baileys WhatsApp Server
- **5432** - PostgreSQL (Supabase, remote)

---

## 🎉 You're Live!

Once all steps pass, your Vehicle Diagnosis Assistant is **fully operational**!

**Key Features:**
- ✅ 250+ OBD codes in database
- ✅ Instant responses (<100ms)
- ✅ Context-aware followups
- ✅ Auto-learning unknown codes
- ✅ Vehicle-specific diagnostics
- ✅ Enterprise security
- ✅ Cost: <$5/month

**Need Help?**
- Check `docs/DEVELOPER_GUIDE.md` for debugging
- Check `docs/ARCHITECTURE.md` for system design
- Check `TEST_RESULTS.md` for test details

---

**Last Updated:** 2026-07-02  
**Version:** 2.0  
**Status:** Production Ready ✅
