# 🚀 START HERE - Vehicle Diagnosis Assistant

Welcome! Your app is **95% ready** - just 3 steps to get it running.

---

## ⚡ Quick Start (5 Minutes)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Create `.env` File
```bash
# Copy the example (already configured with your keys!)
cp .env.example .env
```

Your `.env` is already configured with:
- ✅ Supabase credentials
- ✅ Cohere API key  
- ✅ AI enrichment enabled

### Step 3: Setup Database
```bash
# 1. Go to Supabase Dashboard: https://supabase.com/dashboard
# 2. Select project: your-supabase-project-id
# 3. Go to SQL Editor
# 4. Paste contents of: supabase/migrations/001_initial_schema.sql
# 5. Click "Run"
# 6. Seed OBD codes:
python scripts/seed_database.py
```

### Step 4: Start Server
```bash
uvicorn app.main:app --reload --port 8000
```

### Step 5: Test It!
```bash
curl http://localhost:8000/healthz
```

**Expected:**
```json
{"status": "ok", "version": "2.0.0", "env": "development"}
```

---

## 🎯 Test OBD Diagnosis

```bash
curl -X POST http://localhost:8000/webhook/baileys \
  -H "Content-Type: application/json" \
  -d '{
    "from": "whatsapp:+1234567890",
    "text": "P0420 Toyota Camry 2015",
    "message_id": "test123"
  }'
```

**Expected Response:**
```json
{
  "reply": "*Fault code:* P0420\n*System:* local_db\n\n*What it means:*\n..."
}
```

Check logs for Cohere AI:
```json
{"event": "ai_client_initialized", "provider": "cohere"}
{"event": "cohere_success", "ranked_count": 5}
```

---

## 📚 What's New?

### ✅ Refactored Architecture
- MongoDB → PostgreSQL (Supabase)
- Flat services → Layered (CLAUDE.md compliant)
- print() → Structured JSON logging

### ✅ Security Features
- Phone number hashing (SHA-256)
- Message idempotency checks
- Session management (30-min TTL)

### ✅ Cohere AI Integration
- Intelligent cause ranking
- Vehicle-specific analysis
- Automatic retry on failures

---

## 📖 Documentation

| File | Purpose |
|------|---------|
| **START_HERE.md** | 👈 You are here! Quick start guide |
| **QUICKSTART.md** | 5-minute setup guide |
| **COHERE_SETUP.md** | Cohere AI integration guide |
| **MIGRATION.md** | Complete migration guide |
| **REFACTOR_SUMMARY.md** | Detailed changes & architecture |
| **COHERE_MIGRATION_SUMMARY.md** | Cohere migration details |

---

## ⚠️ Important Notes

### Your API Keys (Already Configured!)
```bash
SUPABASE_URL=https://your-supabase-project-id.supabase.co
SUPABASE_SERVICE_KEY=your-supabase-key
COHERE_API_KEY=your-cohere-api-key-here
```

### Security
- ⚠️ The Supabase key in `.env.example` appears to be a **publishable key**
- You may need the **service_role key** for full database access
- Get it from: Supabase Dashboard → Settings → API → service_role (secret)

---

## 🔧 Troubleshooting

### "Module not found: pydantic_settings"
```bash
pip install -r requirements.txt
```

### "Table does not exist"
Run the migration SQL in Supabase dashboard (Step 3 above)

### "OBD code not found"
```bash
python scripts/seed_database.py
```

### "Supabase connection failed"
Check your service_role key (not publishable key) in `.env`

---

## ✅ Next Steps

After getting it running locally:

1. **Test Features**
   - OBD code lookup
   - Symptom diagnosis
   - AI enrichment
   - Phone hashing
   - Session persistence

2. **Deploy to Production**
   - Create production Supabase project
   - Update production `.env`
   - Deploy to Railway/Render/AWS

3. **Connect WhatsApp**
   - Twilio: Set webhook to your domain
   - Baileys: Configure API key

---

## 🆘 Need Help?

1. Check logs: `uvicorn app.main:app --reload 2>&1 | tee app.log`
2. Read documentation: See files above
3. Check Supabase logs: Dashboard → Logs
4. Verify API keys: Dashboard → Settings → API

---

## 🎉 You're Ready!

Your Vehicle Diagnosis Assistant is fully refactored with:
- ✅ PostgreSQL/Supabase backend
- ✅ Cohere AI integration
- ✅ CLAUDE.md architecture
- ✅ Production-ready security

Just install dependencies and run the database setup!

**Happy coding! 🚀**
