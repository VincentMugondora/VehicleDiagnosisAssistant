# Migration Guide: MongoDB → PostgreSQL/Supabase

This guide walks through migrating the Vehicle Diagnosis Assistant from MongoDB to PostgreSQL/Supabase with CLAUDE.md-compliant architecture.

## Overview

**Changes:**
- Database: MongoDB → PostgreSQL (Supabase)
- Architecture: Flat services → Layered (core/models/repositories/services/api)
- Security: Raw phone storage → SHA-256 hashing
- Observability: print() → structlog with JSON output
- Sessions: Stateless → 30-min TTL sessions with idempotency

**Preserved:**
- All OBD lookup logic
- Gemini AI integration
- Symptom diagnosis
- WhatsApp webhooks (Twilio & Baileys)
- External search fallback

---

## Prerequisites

1. **Supabase Account**
   - Create project at https://supabase.com
   - Note your project URL and service key

2. **Python Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Variables**
   - Copy `.env.example` to `.env`
   - Update `SUPABASE_URL` and `SUPABASE_SERVICE_KEY`

---

## Step 1: Database Setup

### Create PostgreSQL Schema

Run the migration SQL to create all tables:

```bash
# If using Supabase CLI
supabase db push

# Or manually via Supabase dashboard:
# 1. Go to SQL Editor
# 2. Paste contents of supabase/migrations/001_initial_schema.sql
# 3. Run
```

Verify tables created:
- obd_codes
- message_logs
- diagnostic_logs
- conversation_sessions
- external_obd_cache
- obd_summaries
- vehicle_overrides

---

## Step 2: Migrate Data

### Seed OBD Codes

```bash
python scripts/seed_database.py
```

This migrates OBD codes from `app/data/obd_codes.json` to PostgreSQL.

**Verify:**
```sql
SELECT COUNT(*) FROM obd_codes;
-- Should return ~1000-5000 rows
```

### Migrate Existing MongoDB Data (Optional)

If you have production MongoDB data to preserve:

```python
# TODO: Create migration script
# For now, MongoDB data is archived (not migrated)
```

---

## Step 3: Update Environment

Update `.env` with new configuration:

```bash
# Remove MongoDB
# MONGODB_URI=...
# MONGODB_DB=...

# Add Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJxxxx

# Keep all other vars (Gemini, Twilio, etc.)
```

---

## Step 4: Test Locally

### Start Server

```bash
uvicorn app.main:app --reload --port 8000
```

### Health Check

```bash
curl http://localhost:8000/healthz
```

Expected response:
```json
{
  "status": "ok",
  "version": "2.0.0",
  "env": "development"
}
```

### Test Webhook

```bash
curl -X POST http://localhost:8000/webhook/baileys \
  -H "Content-Type: application/json" \
  -d '{
    "from": "whatsapp:+1234567890",
    "text": "P0420 Toyota Camry 2015",
    "message_id": "test123"
  }'
```

Expected response:
```json
{
  "reply": "*Fault code:* P0420\n*System:* local_db\n..."
}
```

---

## Step 5: Verify Features

### Phone Number Hashing

Check `message_logs` table - `phone_hash` should be 64-char hex string:
```sql
SELECT phone_hash FROM message_logs LIMIT 1;
-- e.g., "a3f5b2c1d4e6f7890abcdef1234567890abcdef1234567890abcdef12345678"
```

### Message Idempotency

Send same message twice:
```bash
# First time - should succeed
curl -X POST ... -d '{"message_id": "dup123", ...}'

# Second time - should return duplicate status
curl -X POST ... -d '{"message_id": "dup123", ...}'
```

### Structured Logging

Check logs for JSON output:
```bash
# Should see:
{"event": "app_starting", "env": "development", "timestamp": "..."}
{"event": "supabase_connected", ...}
{"event": "twilio_webhook_received", "phone_hash": "...", ...}
```

### Session Management

Send multiple messages from same number - session should persist:
```sql
SELECT state FROM conversation_sessions WHERE phone_hash = '...';
-- Should show turns array growing
```

---

## Step 6: Deploy

### Update Production Environment

1. Create production Supabase project
2. Run migration SQL in production
3. Seed OBD codes in production
4. Update production `.env`
5. Deploy application

### Rollback Plan

If issues arise:
1. Keep MongoDB running in parallel for 1 week
2. Compare results between MongoDB and PostgreSQL
3. Full cutover only after validation
4. Keep MongoDB backup for 30 days

---

## Architecture Changes

### Old Structure (MongoDB)
```
app/
├── db/mongo.py         # Direct MongoDB access
├── services/
│   ├── obd.py          # Direct db["collection"] calls
│   ├── parser.py
├── api/webhook.py      # Business logic + DB access
```

### New Structure (PostgreSQL)
```
app/
├── core/               # Config, logging, errors, middleware
├── models/             # Pydantic models
├── repositories/       # Data access layer
├── services/           # Business logic (no DB access)
├── api/routes/         # HTTP handlers (no business logic)
├── utils/              # Pure functions
```

---

## Key Differences

| Feature | Old (MongoDB) | New (PostgreSQL) |
|---------|--------------|-----------------|
| Phone storage | Raw numbers | SHA-256 hash |
| Message deduplication | None | message_id check |
| Sessions | Stateless | 30-min TTL |
| Logging | print() | structlog JSON |
| Config | os.getenv() | Pydantic settings |
| DB access | Direct in services | Repository pattern |
| Type safety | Partial | Full Pydantic |
| Errors | Generic Exception | Custom hierarchy |

---

## Troubleshooting

### "Supabase connection failed"
- Check `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` in `.env`
- Verify Supabase project is active
- Check network connectivity

### "Table does not exist"
- Run migration SQL: `supabase/migrations/001_initial_schema.sql`
- Verify via Supabase dashboard Table Editor

### "OBD code not found"
- Seed database: `python scripts/seed_database.py`
- Verify: `SELECT COUNT(*) FROM obd_codes;`

### "Import errors"
- Install dependencies: `pip install -r requirements.txt`
- Verify Python 3.11+

### "Signature validation failed" (Twilio)
- Check `TWILIO_AUTH_TOKEN` matches Twilio dashboard
- Verify webhook URL is correct in Twilio settings

---

## Performance Notes

- PostgreSQL queries are similar speed to MongoDB for this workload
- Indexes created on all lookup columns
- No N+1 query issues (repository pattern prevents this)
- Session state stored as JSONB (flexible like MongoDB)

---

## Next Steps

After successful migration:
1. Monitor logs for errors
2. Set up Supabase backups
3. Configure Row Level Security (RLS) policies
4. Add monitoring/alerting (e.g., Sentry)
5. Implement Phase 2 features (image recognition, VIN lookup)

---

## Support

Issues? Check:
- GitHub: [Repository Issues]
- Logs: Check structlog JSON output
- Supabase: Dashboard → Logs
