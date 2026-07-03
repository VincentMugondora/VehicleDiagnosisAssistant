# ✅ Database Setup Checklist

Quick reference checklist for setting up Supabase.

---

## Before You Start

- [ ] I have a Supabase account
- [ ] I have a Supabase project (or will create one)
- [ ] I have the project URL and service_role key
- [ ] Backend is currently running (we'll restart it later)

---

## Step 1: Disable Cloudflare WARP ⚠️ CRITICAL

**Current Status:** WARP is ACTIVE and blocking Supabase

- [ ] Click WARP icon in system tray (near clock)
- [ ] Click "Disconnect" or toggle OFF
- [ ] Run: `nslookup ojxijkrkadymllbigcme.supabase.co`
- [ ] Verify I see an IP address (NOT "Non-existent domain")

**Why:** WARP DNS blocks Supabase. Must be disabled for setup.

---

## Step 2: Get Supabase Credentials

Go to: https://supabase.com/dashboard

- [ ] Logged into Supabase
- [ ] Clicked on my project: `ojxijkrkadymllbigcme`
- [ ] If project doesn't exist, created a new one
- [ ] Went to Settings → API
- [ ] Copied **Project URL**
- [ ] Revealed and copied **service_role key** (NOT anon key!)

---

## Step 3: Update .env File

Edit `.env` file:

- [ ] Opened `.env` in text editor
- [ ] Found `SUPABASE_URL=` line
- [ ] Pasted my Project URL
- [ ] Found `SUPABASE_SERVICE_KEY=` line
- [ ] Pasted my service_role key
- [ ] Saved file

**Example:**
```
SUPABASE_URL=https://ojxijkrkadymllbigcme.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## Step 4: Create Database Tables

### Using Supabase Dashboard:

- [ ] Went to Supabase Dashboard
- [ ] Clicked **SQL Editor** (left sidebar)
- [ ] Clicked **New query** button
- [ ] Opened file: `supabase/migrations/001_initial_schema.sql`
- [ ] Selected ALL text (Ctrl+A)
- [ ] Copied it (Ctrl+C)
- [ ] Pasted into SQL Editor (Ctrl+V)
- [ ] Clicked **Run** button (or pressed Ctrl+Enter)
- [ ] Saw "Success. No rows returned"
- [ ] Clicked **Table Editor** (left sidebar)
- [ ] Verified 7 tables exist:
  - [ ] obd_codes
  - [ ] message_logs
  - [ ] diagnostic_logs
  - [ ] conversation_sessions
  - [ ] external_obd_cache
  - [ ] obd_summaries
  - [ ] vehicle_overrides

---

## Step 5: Import OBD Codes

In terminal/command prompt:

```bash
cd C:\Users\vinmu\Desktop\VehicleDiagnosisAssistant
.\venv\Scripts\activate
python scripts\import_obd_datasets.py
```

- [ ] Activated virtual environment
- [ ] Ran import script
- [ ] Saw "Connected to Supabase" message
- [ ] Saw "Loaded X codes from local dataset"
- [ ] Saw "Import complete! Imported: 132+" (or similar)
- [ ] No major errors

**If errors:**
- "Table does not exist" → Go back to Step 4
- "Cannot connect" → Check WARP is off, .env is correct

---

## Step 6: Verify Import

Run this command:

```bash
python -c "from app.db.client import get_supabase_client; client = get_supabase_client(); result = client.table('obd_codes').select('code', count='exact').execute(); print(f'Total codes: {result.count}')"
```

- [ ] Ran verification command
- [ ] Saw "Total codes: 130+" (or more)

**Or check in Supabase:**
- [ ] Went to Table Editor → obd_codes
- [ ] Saw 130+ rows
- [ ] Spot checked a few codes (P0420, P0300, etc.)

---

## Step 7: Restart Backend

- [ ] Went to terminal running backend
- [ ] Pressed **Ctrl+C** to stop it
- [ ] Ran: `uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload`
  - OR: `.\start_backend.bat`
- [ ] Watched startup logs
- [ ] Saw `[info] app_starting`
- [ ] Saw `[info] supabase_connected` ✅ (SUCCESS!)
- [ ] Did NOT see `[warning] supabase_unreachable` ❌

**If still seeing "unreachable":**
- Check WARP is disabled
- Check .env has correct credentials
- Restart terminal and try again

---

## Step 8: Test End-to-End

Send via WhatsApp:
```
P0420
```

Watch backend logs:
- [ ] Saw `[info] baileys_webhook_received`
- [ ] Saw `[info] obd_lookup_success code=P0420 source=local_db` ✅
- [ ] Did NOT see `source=fallback` ❌
- [ ] Received detailed response in WhatsApp

**Test more codes:**
- [ ] `P0300` - Misfire
- [ ] `P0171` - Too Lean
- [ ] `P0128` - Thermostat

---

## Step 9: Verify Full Functionality

- [ ] Sessions persist (send messages, restart backend, context maintained)
- [ ] Check message_logs table has entries
- [ ] Check diagnostic_logs table has entries
- [ ] Check conversation_sessions table has entries
- [ ] All 132+ codes work (test 5-10 random ones)

---

## Troubleshooting Quick Reference

### Still seeing fallback mode?
1. ✅ WARP disabled?
2. ✅ .env updated with service_role key?
3. ✅ Tables created in Supabase?
4. ✅ Codes imported?
5. ✅ Backend restarted?

### Import failed?
- Check file exists: `scripts/comprehensive_obd_codes.py`
- Check file exists: `data/obd_codes_dataset.json`
- Try: `pip install requests` if missing

### "Table does not exist"?
- Run migration SQL again in Supabase SQL Editor
- Make sure you copied the ENTIRE file content

### "401 Unauthorized"?
- Check you're using `service_role` key, NOT `anon` key
- Check key is copied correctly (no extra spaces)

---

## Success! 🎉

If all checkboxes are checked, you now have:

✅ **132+ OBD codes** in database  
✅ **Persistent sessions** across restarts  
✅ **Message audit logging**  
✅ **Usage analytics**  
✅ **Rate limiting** capability  
✅ **Full system functionality**  

---

## What Changed

### Before (Fallback Mode)
- ⚠️  20 codes only
- ⚠️  Sessions lost on restart
- ⚠️  No analytics
- ⚠️  No persistence

### After (Full Mode)
- ✅ 132+ codes
- ✅ Sessions persist
- ✅ Full analytics
- ✅ Complete logging
- ✅ Rate limiting
- ✅ Auto-learning enabled

---

## Quick Commands Reference

**Test connection:**
```bash
curl https://ojxijkrkadymllbigcme.supabase.co
```

**Count codes:**
```bash
python -c "from app.db.client import get_supabase_client; client = get_supabase_client(); result = client.table('obd_codes').select('code', count='exact').execute(); print(f'Codes: {result.count}')"
```

**Check tables:**
```bash
python -c "from app.db.client import get_supabase_client; client = get_supabase_client(); tables = ['obd_codes', 'message_logs', 'diagnostic_logs', 'conversation_sessions', 'external_obd_cache', 'obd_summaries', 'vehicle_overrides']; [print(f'✅ {t}') for t in tables if client.table(t).select('*').limit(1).execute()]"
```

**Re-import codes (safe):**
```bash
python scripts\import_obd_datasets.py
```

---

## Files to Reference

- **Full Guide**: `SETUP_DATABASE.md` (detailed instructions)
- **Quick Script**: `quick_setup.bat` (automated helper)
- **Network Fix**: `SUPABASE_FIX.md` (WARP troubleshooting)
- **This Checklist**: `DATABASE_SETUP_CHECKLIST.md` (you are here)

---

**Estimated Time:** 10-15 minutes  
**Difficulty:** Easy (if WARP is disabled)  
**Result:** Full production-ready system

---

**Last Updated:** 2026-07-03  
**Your Current Status:** Step 1 needed (disable WARP)
