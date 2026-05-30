# ✅ Setup Checklist

Quick checklist to get your Vehicle Diagnosis Assistant running.

---

## Prerequisites

- [x] Dependencies installed (`pip install -r requirements.txt`)
- [x] `.env` file created (exists now!)
- [ ] Supabase service_role key configured
- [ ] Database schema created
- [ ] OBD codes seeded

---

## Step-by-Step

### ✅ Step 1: Get Supabase Service Key

**Status:** ⚠️ NEEDS ATTENTION

**Current issue:** Your `.env` has a publishable key instead of service_role key.

**Fix:**
1. Go to: https://supabase.com/dashboard/project/your-supabase-project-id
2. Settings → API
3. Copy the **service_role** key (starts with `eyJ`)
4. Update line 3 in `.env`:
   ```bash
   SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

See: `GET_SUPABASE_KEY.md` for detailed instructions.

---

### ⬜ Step 2: Create Database Schema

**Status:** NOT STARTED

**Action:**
1. Go to Supabase Dashboard → SQL Editor
2. Copy entire contents of `supabase/migrations/001_initial_schema.sql`
3. Paste into SQL Editor
4. Click "Run"

**Verify:**
```sql
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public';
```

Should see: obd_codes, message_logs, diagnostic_logs, conversation_sessions, etc.

---

### ⬜ Step 3: Seed OBD Codes

**Status:** NOT STARTED (tried but failed due to missing service key)

**Action:**
```bash
python scripts/seed_database.py
```

**Expected output:**
```json
{"event": "seed_database_start", ...}
{"event": "supabase_connected", ...}
{"event": "obd_codes_loaded", "count": 1234}
{"event": "obd_codes_seeded", "count": 1234}
{"event": "seed_database_complete"}
```

**Verify:**
```sql
SELECT COUNT(*) FROM obd_codes;
```

Should return ~1000-5000 rows.

---

### ⬜ Step 4: Start Server

**Status:** NOT STARTED

**Action:**
```bash
uvicorn app.main:app --reload --port 8000
```

**Expected output:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
{"event": "app_starting", "env": "development", ...}
{"event": "supabase_connected", ...}
INFO:     Application startup complete.
```

---

### ⬜ Step 5: Test Health Endpoint

**Status:** NOT STARTED

**Action:**
```bash
curl http://localhost:8000/healthz
```

**Expected:**
```json
{
  "status": "ok",
  "version": "2.0.0",
  "env": "development"
}
```

---

### ⬜ Step 6: Test OBD Diagnosis

**Status:** NOT STARTED

**Action:**
```bash
curl -X POST http://localhost:8000/webhook/baileys \
  -H "Content-Type: application/json" \
  -d '{
    "from": "whatsapp:+1234567890",
    "text": "P0420 Toyota Camry 2015",
    "message_id": "test123"
  }'
```

**Expected:**
```json
{
  "reply": "*Fault code:* P0420\n*System:* local_db\n..."
}
```

---

### ⬜ Step 7: Verify AI Integration

**Status:** NOT STARTED

**Check logs for:**
```json
{"event": "ai_client_initialized", "provider": "cohere"}
{"event": "cohere_request", ...}
{"event": "cohere_success", "ranked_count": 5}
```

---

## Current Status

**Progress:** 1/7 steps complete (14%)

**Next Action:** Get Supabase service_role key → See `GET_SUPABASE_KEY.md`

---

## Quick Commands

```bash
# After fixing service key:

# 1. Seed database
python scripts/seed_database.py

# 2. Start server
uvicorn app.main:app --reload --port 8000

# 3. Test (in new terminal)
curl http://localhost:8000/healthz

# 4. Test diagnosis
curl -X POST http://localhost:8000/webhook/baileys \
  -H "Content-Type: application/json" \
  -d '{"from":"whatsapp:+1234567890","text":"P0420","message_id":"test1"}'
```

---

## Troubleshooting

### "ValidationError: Field required"
→ Get service_role key (see Step 1)

### "Table does not exist"
→ Run migration SQL (see Step 2)

### "OBD code not found"
→ Seed database (see Step 3)

### "Module not found: cohere"
→ Run `pip install -r requirements.txt`

---

## Documentation

- **Quick Start**: `START_HERE.md`
- **Supabase Key**: `GET_SUPABASE_KEY.md`
- **Cohere Setup**: `COHERE_SETUP.md`
- **Full Migration**: `MIGRATION.md`

---

**You're on step 1 of 7. Almost there!** 🚀
