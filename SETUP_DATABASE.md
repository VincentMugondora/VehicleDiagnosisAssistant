# 🗄️ Complete Database Setup Guide

This guide will help you set up Supabase with all tables and 132+ OBD codes.

---

## Prerequisites

✅ Supabase account (free tier works)  
✅ Supabase project created  
✅ Backend code already has the migrations  
⚠️  **Cloudflare WARP must be disabled** (see below)

---

## Step 1: Fix Network Connection (CRITICAL)

Your system is using Cloudflare WARP which blocks Supabase. You **MUST** disable it first.

### Option A: Disable WARP Temporarily ⭐ (Easiest)

**Windows:**
1. Click WARP icon in system tray (near clock)
2. Click "Disconnect" or toggle OFF
3. Verify: Run `nslookup ojxijkrkadymllbigcme.supabase.co`
4. Should see an IP address (not "Non-existent domain")

### Option B: Add Supabase to Split Tunnel

Keep WARP on but exclude Supabase:

1. Open Cloudflare WARP app
2. Settings → Gateway with WARP → Split Tunnels
3. Click "Manage"
4. Add to "Exclude from WARP":
   - `*.supabase.co`
   - `*.supabase.io`
5. Save and reconnect

### Verify Network is Fixed

```bash
nslookup ojxijkrkadymllbigcme.supabase.co
```

**Should show:**
```
Server: [DNS server]
Address: [IP]

Non-authoritative answer:
Name:    ojxijkrkadymllbigcme.supabase.co
Addresses: [IP addresses]
```

**NOT this:**
```
*** connectivity-check.warp-svc can't find ojxijkrkadymllbigcme.supabase.co: Non-existent domain
```

---

## Step 2: Get Your Supabase Credentials

### A. Check Current Project

1. Go to: https://supabase.com/dashboard
2. Login to your account
3. Look for project: `ojxijkrkadymllbigcme`

### B. If Project Exists

1. Click on the project
2. Go to **Settings** (left sidebar) → **API**
3. Copy these values:
   - **Project URL**: Under "Configuration" section
   - **service_role key**: Under "Project API keys" → Click "Reveal" → Copy the **service_role** (NOT anon/public)

### C. If Project Doesn't Exist or is Paused

Create a new project:

1. Click "New Project"
2. Fill in:
   - **Name**: `vehicle-diagnosis`
   - **Database Password**: Generate a strong password (save it!)
   - **Region**: Choose closest to you (e.g., US East)
   - **Pricing Plan**: Free
3. Click "Create new project"
4. Wait 2-3 minutes for provisioning
5. Follow Step B above to get credentials

---

## Step 3: Update .env File

Edit `.env` file with your Supabase credentials:

```bash
# Update these lines (keep everything else the same)
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key-here
```

**IMPORTANT:** Use the `service_role` key, NOT the `anon` key!

**Example:**
```bash
SUPABASE_URL=https://ojxijkrkadymllbigcme.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS...
```

---

## Step 4: Create Database Tables

### Option A: Using Supabase Dashboard (Recommended)

1. Go to your Supabase project
2. Click **SQL Editor** (left sidebar)
3. Click **New query**
4. Open file: `supabase/migrations/001_initial_schema.sql`
5. Copy the entire contents
6. Paste into SQL Editor
7. Click **Run** (or press Ctrl+Enter)

**Expected Result:**
```
Success. No rows returned
```

### Option B: Using CLI (Alternative)

If you have Supabase CLI installed:

```bash
cd C:\Users\vinmu\Desktop\VehicleDiagnosisAssistant
supabase db push
```

---

## Step 5: Verify Tables Created

In Supabase Dashboard:

1. Click **Table Editor** (left sidebar)
2. You should see these tables:
   - ✅ `obd_codes`
   - ✅ `message_logs`
   - ✅ `diagnostic_logs`
   - ✅ `conversation_sessions`
   - ✅ `external_obd_cache`
   - ✅ `obd_summaries`
   - ✅ `vehicle_overrides`

If you see all 7 tables, SUCCESS! ✅

---

## Step 6: Import OBD Codes

Now let's load 132+ OBD codes into the database.

### Activate Virtual Environment

```bash
cd C:\Users\vinmu\Desktop\VehicleDiagnosisAssistant
.\venv\Scripts\activate
```

### Run Import Script

```bash
python scripts/import_obd_datasets.py
```

**Expected Output:**
```
============================================================
🚗 OBD-II Code Dataset Importer
============================================================

🔌 Checking Supabase connection...
✅ Connected to Supabase: https://ojxijkrkadymllbigcme.supabase.co

✅ Loaded 132 codes from local comprehensive dataset
📦 Starting with 132 codes from local dataset

📥 Attempting to download additional datasets from GitHub...
📥 Downloading generic_powertrain...
✅ Downloaded generic_powertrain: 45 codes
...

📦 Total unique codes collected: 150+

============================================================
📤 Importing to Supabase...
============================================================

📊 Total codes to import: 150+
✅ Imported batch 1: 100 codes (Total: 100)
✅ Imported batch 2: 50 codes (Total: 150)

🎉 Import complete!
   ✅ Imported: 150+

============================================================
📊 SUMMARY
============================================================
Total codes collected: 150+
Successfully imported: 150+

✅ Your database is now populated with OBD-II codes!
```

### Troubleshooting Import

**Error: "Could not import comprehensive_obd_codes.py"**
- This is OK! The script will still work with the JSON dataset
- You'll get ~80 codes instead of 132+

**Error: "Failed to connect to Supabase"**
- Check WARP is disabled
- Verify SUPABASE_URL and SUPABASE_SERVICE_KEY in .env
- Run: `curl https://your-project.supabase.co`

**Error: "Table does not exist"**
- Go back to Step 4 and run the migration SQL

---

## Step 7: Verify OBD Codes Imported

### Option A: Supabase Dashboard

1. Go to **Table Editor**
2. Click `obd_codes` table
3. You should see 130-150+ rows
4. Check a few codes (P0420, P0300, etc.)

### Option B: Python Script

```bash
python -c "
from app.db.client import get_supabase_client
client = get_supabase_client()
result = client.table('obd_codes').select('code', count='exact').execute()
print(f'Total codes in database: {result.count}')
"
```

**Expected:** `Total codes in database: 130+`

---

## Step 8: Restart Backend

Now restart your backend to connect to Supabase:

```bash
# Stop current backend (Ctrl+C in the terminal)

# Start it again
cd C:\Users\vinmu\Desktop\VehicleDiagnosisAssistant
.\venv\Scripts\activate
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

**Look for these logs:**
```
[info] app_starting env=development supabase_url=https://...
[info] supabase_connected  ✅ SUCCESS!
```

**NOT this:**
```
[warning] supabase_unreachable  ❌ FAILED
```

---

## Step 9: Test End-to-End

Send this via WhatsApp:
```
P0420
```

**Check Backend Logs:**
```
[info] baileys_webhook_received
[info] obd_lookup_success code=P0420 source=local_db  ✅ FROM DATABASE!
[info] session_saved
```

If you see `source=local_db` (NOT "fallback"), you're connected! 🎉

---

## What You Get After Setup

### Before (Fallback Mode)
- ❌ 20 OBD codes only
- ❌ No persistence
- ❌ No rate limiting
- ❌ No analytics
- ❌ Sessions lost on restart

### After (Full Mode)
- ✅ **132+ OBD codes**
- ✅ **Persistent sessions**
- ✅ **Message audit logs**
- ✅ **Usage analytics**
- ✅ **Rate limiting**
- ✅ **Auto-learning new codes**
- ✅ **Vehicle-specific overrides**

---

## Quick Reference

### Check Database Connection

```bash
python -c "
from app.db.client import get_supabase_client
from app.core.config import settings
print(f'Supabase URL: {settings.supabase_url}')
print(f'Supabase Enabled: {settings.supabase_enabled}')
try:
    client = get_supabase_client()
    if client:
        result = client.table('obd_codes').select('code').limit(1).execute()
        print('✅ Connected!')
    else:
        print('❌ Client is None (fallback mode)')
except Exception as e:
    print(f'❌ Error: {e}')
"
```

### Count Codes in Database

```bash
python -c "
from app.db.client import get_supabase_client
client = get_supabase_client()
result = client.table('obd_codes').select('*', count='exact').execute()
print(f'Total codes: {result.count}')
print('Sample codes:')
for code in result.data[:5]:
    print(f\"  - {code['code']}: {code['description'][:50]}...\")
"
```

### Re-import Codes (If Needed)

```bash
# This is safe - it uses UPSERT so won't create duplicates
python scripts/import_obd_datasets.py
```

---

## Common Issues

### Issue 1: "Non-existent domain"

**Cause:** Cloudflare WARP still active  
**Fix:** Disable WARP (Step 1)

### Issue 2: "401 Unauthorized"

**Cause:** Wrong API key or using `anon` key instead of `service_role`  
**Fix:** Get `service_role` key from Supabase Dashboard → Settings → API

### Issue 3: "Table does not exist"

**Cause:** Migration not run  
**Fix:** Run Step 4 again

### Issue 4: "0 codes imported"

**Cause:** Missing data files or import error  
**Fix:** Check `data/obd_codes_dataset.json` exists, or download it from GitHub

### Issue 5: Backend still in fallback mode

**Check:**
1. WARP disabled?
2. .env has correct credentials?
3. Tables created?
4. Backend restarted?

---

## Advanced: Alternative Data Sources

If the import script doesn't work, manually add codes via SQL:

```sql
-- Add individual codes
INSERT INTO obd_codes (code, description, system, severity, common_causes, symptoms)
VALUES 
('P0420', 'Catalyst System Efficiency Below Threshold (Bank 1)', 'Emissions', 'Moderate', 
 'Faulty catalytic converter, Damaged oxygen sensors, Exhaust leak', 
 'Check engine light, Reduced fuel efficiency'),
('P0300', 'Random/Multiple Cylinder Misfire Detected', 'Ignition', 'Serious',
 'Worn spark plugs, Faulty ignition coils, Vacuum leaks, Low fuel pressure',
 'Engine runs rough, Loss of power, Check engine light flashing')
ON CONFLICT (code) DO NOTHING;
```

---

## Success Checklist

- [ ] WARP disabled or Supabase excluded
- [ ] DNS resolves Supabase URL
- [ ] .env has correct credentials (service_role key)
- [ ] 7 tables created in Supabase
- [ ] 130+ OBD codes imported
- [ ] Backend shows `[info] supabase_connected`
- [ ] WhatsApp message returns code from database
- [ ] Backend logs show `source=local_db`

If all checked, you're done! 🎉

---

## Next Steps

After successful setup:

1. **Test More Codes**: Try P0300, P0171, P0128, etc.
2. **Check Analytics**: View message_logs and diagnostic_logs tables
3. **Monitor Usage**: Check conversation_sessions table
4. **Enable Auto-learning**: Set `AI_ENRICH_ENABLED=true` in .env

---

## Need Help?

- **Network issues**: See `SUPABASE_FIX.md`
- **Import errors**: Check Python version (3.11+)
- **Database errors**: Verify migration ran correctly
- **Still stuck**: Check backend logs for detailed errors

---

**Last Updated:** 2026-07-03  
**Status:** Ready to use  
**Expected Time:** 10-15 minutes
