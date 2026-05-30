# Quick Start Guide

Get the refactored Vehicle Diagnosis Assistant running in 5 minutes.

---

## 1. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 2. Setup Supabase

### Option A: Create New Project
1. Go to https://supabase.com
2. Create new project
3. Wait for database to initialize (~2 minutes)
4. Go to Settings → API
5. Copy `URL` and `service_role key`

### Option B: Use Existing Project
1. Go to your Supabase dashboard
2. Select project
3. Get URL and service key from Settings → API

---

## 3. Configure Environment

```bash
# Copy example
cp .env.example .env

# Edit .env and update:
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJxxxx...

# AI Provider (Cohere recommended)
AI_PROVIDER=cohere
COHERE_API_KEY=your-cohere-api-key-here
AI_ENRICH_ENABLED=true

# Or use Gemini (legacy)
# AI_PROVIDER=gemini
# GEMINI_API_KEY=AIzaSyxxx...
```

---

## 4. Initialize Database

### Run Migration SQL
```bash
# Copy contents of supabase/migrations/001_initial_schema.sql
# Paste into Supabase Dashboard → SQL Editor
# Click "Run"
```

Or if you have Supabase CLI:
```bash
supabase db push
```

### Seed OBD Codes
```bash
python scripts/seed_database.py
```

Expected output:
```
{"event": "seed_database_start", ...}
{"event": "supabase_connected", ...}
{"event": "obd_codes_loaded", "count": 1234}
{"event": "obd_codes_seeded", "count": 1234}
{"event": "seed_database_complete"}
```

---

## 5. Start Server

```bash
uvicorn app.main:app --reload --port 8000
```

Expected output:
```
INFO:     Started server process
INFO:     Waiting for application startup.
{"event": "app_starting", "env": "development", ...}
{"event": "supabase_connected", ...}
INFO:     Application startup complete.
```

---

## 6. Test It

### Health Check
```bash
curl http://localhost:8000/healthz
```

Expected:
```json
{
  "status": "ok",
  "version": "2.0.0",
  "env": "development"
}
```

### Test OBD Diagnosis
```bash
curl -X POST http://localhost:8000/webhook/baileys \
  -H "Content-Type: application/json" \
  -d '{
    "from": "whatsapp:+1234567890",
    "text": "P0420 Toyota Camry 2015",
    "message_id": "test123"
  }'
```

Expected response (formatted):
```json
{
  "reply": "*Fault code:* P0420\n*System:* local_db\n\n*What it means:*\nCatalyst System Efficiency Below Threshold (Bank 1)\n\n*Likely causes:*\n• Worn catalytic converter\n• Faulty rear O2 sensor\n• Exhaust leak before sensor\n...",
}
```

---

## 7. Verify Features

### Check Structured Logs
Look at terminal output - should see JSON logs:
```json
{"event": "baileys_webhook_received", "phone_hash": "a3f5b2...", "message_id": "test123", ...}
{"event": "message_parsed", "code": "P0420", ...}
{"event": "routing_to_code_diagnosis", "code": "P0420"}
{"event": "obd_lookup_success", "code": "P0420", "source": "local_db"}
{"event": "session_saved", ...}
```

### Check Phone Hashing
```sql
-- In Supabase Dashboard → SQL Editor
SELECT phone_hash, request_text FROM message_logs LIMIT 1;
```

Should see 64-character hex hash, NOT raw phone number.

### Test Idempotency
Send same message twice:
```bash
# First time - succeeds
curl -X POST http://localhost:8000/webhook/baileys \
  -d '{"message_id": "dup123", "from": "whatsapp:+1234567890", "text": "P0300"}'

# Second time - duplicate detected
curl -X POST http://localhost:8000/webhook/baileys \
  -d '{"message_id": "dup123", "from": "whatsapp:+1234567890", "text": "P0300"}'
```

Second response:
```json
{
  "ok": true,
  "status": "duplicate"
}
```

---

## 8. Connect to WhatsApp

### Option A: Twilio
1. Go to Twilio Console → WhatsApp
2. Set webhook URL: `https://your-domain.com/webhook/twilio`
3. Update `.env`:
   ```
   TWILIO_ACCOUNT_SID=ACxxx...
   TWILIO_AUTH_TOKEN=xxx...
   TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
   ```

### Option B: Baileys
1. Set webhook URL in your Baileys instance
2. Set API key in `.env`:
   ```
   BAILEYS_API_KEY=your-secret-key
   ```
3. Send `X-API-Key` header with requests

---

## Troubleshooting

### "Supabase connection failed"
- Check `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` in `.env`
- Verify project is active in Supabase dashboard

### "Table does not exist"
- Run migration SQL in Supabase dashboard
- Verify tables created: Settings → Database → Tables

### "OBD code not found"
- Run seed script: `python scripts/seed_database.py`
- Verify: `SELECT COUNT(*) FROM obd_codes;` in SQL Editor

### "Module not found"
- Install dependencies: `pip install -r requirements.txt`
- Check Python version: `python --version` (need 3.11+)

---

## Next Steps

1. **AI Provider Setup** (See COHERE_SETUP.md)
   - Cohere (recommended): Fast, reliable, cost-effective
   - Gemini (legacy): Alternative AI provider

2. **Configure Usage Limits**
   ```bash
   USAGE_LIMIT_PER_NUMBER=20
   USAGE_LIMIT_WINDOW_DAYS=30
   ```

3. **Enable External Search**
   ```bash
   INTERNET_FALLBACK_ENABLED=true
   BRAVE_API_KEY=your-key
   ```

4. **Deploy to Production**
   - See MIGRATION.md for full deployment guide
   - Create production Supabase project
   - Update production environment variables

---

## Development Tips

### Watch Logs
```bash
# JSON logs to file
uvicorn app.main:app --reload 2>&1 | tee app.log

# Pretty print JSON logs
uvicorn app.main:app --reload 2>&1 | jq
```

### Test with curl
```bash
# Save test payload
cat > test_payload.json <<EOF
{
  "from": "whatsapp:+1234567890",
  "text": "P0171 Honda Civic 2015 1.6L",
  "message_id": "test456"
}
EOF

# Send test
curl -X POST http://localhost:8000/webhook/baileys \
  -H "Content-Type: application/json" \
  -d @test_payload.json | jq
```

### Database Queries
```sql
-- Recent messages
SELECT * FROM message_logs ORDER BY created_at DESC LIMIT 10;

-- Active sessions
SELECT phone_hash, state->>'last_active' as last_active 
FROM conversation_sessions 
ORDER BY last_active DESC;

-- Popular OBD codes
SELECT code, COUNT(*) as count 
FROM diagnostic_logs 
GROUP BY code 
ORDER BY count DESC 
LIMIT 10;
```

---

## Support

- **Documentation**: See MIGRATION.md for detailed guide
- **Architecture**: See REFACTOR_SUMMARY.md for changes
- **Issues**: Check logs for structured error events
- **Supabase**: Dashboard → Logs for database errors

---

**Ready to go! 🚀**

Your Vehicle Diagnosis Assistant is now running with PostgreSQL/Supabase backend, structured logging, session management, and production-ready architecture.
