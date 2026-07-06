# ✅ Complete Database Setup Checklist

**Complete reference for setting up all database tables, functions, and features.**

Last Updated: 2026-07-06  
Total Tables Required: **17**  
Total Functions: **4**  
Total Views: **1**

---

## Quick Summary

### What This System Needs:
1. **7 Core Tables** - OBD codes, sessions, logging
2. **5 DTC Detail Tables** - Vehicle fitment, repair steps, parts, symptoms
3. **3 Payment Tables** - Transactions, subscriptions, usage tracking
4. **1 Educational Table** - System diagrams
5. **1 Auxiliary Table** - External OBD cache
6. **4 Database Functions** - Payment/subscription helpers
7. **1 View** - Active subscriptions

---

## Before You Start

- [ ] I have a Supabase account
- [ ] I have a Supabase project (or will create one)
- [ ] I have the project URL and service_role key
- [ ] Backend is currently running (we'll restart it later)
- [ ] All migration files are present in my project

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

## Step 7: Run Additional Migrations

### A. DTC Detail Tables (Vehicle Fitment, Repair Steps, Parts)

In Supabase SQL Editor:

- [ ] Opened file: `migrations/add_dtc_detail_tables.sql`
- [ ] Copied all content
- [ ] Pasted into new SQL query
- [ ] Clicked Run
- [ ] Verified success messages in output
- [ ] Checked Table Editor for new tables:
  - [ ] code_vehicle_fitment
  - [ ] repair_steps
  - [ ] parts
  - [ ] common_symptoms
  - [ ] related_codes

### B. System Diagrams Table

In Supabase SQL Editor:

- [ ] Opened file: `migrations/add_system_diagrams_table.sql`
- [ ] Copied all content
- [ ] Pasted into new SQL query
- [ ] Clicked Run
- [ ] Verified `system_diagrams` table exists

### C. Payment & Subscription Tables

In Supabase SQL Editor:

- [ ] Opened file: `migrations/add_payments_tables.sql`
- [ ] Copied all content
- [ ] Pasted into new SQL query
- [ ] Clicked Run
- [ ] Verified success messages
- [ ] Checked Table Editor for new tables:
  - [ ] transactions
  - [ ] subscriptions
  - [ ] user_usage
- [ ] Verified functions created:
  - [ ] has_active_subscription()
  - [ ] get_weekly_usage()
  - [ ] increment_user_usage()
- [ ] Verified view created:
  - [ ] active_subscriptions

---

## Step 8: Verify All Tables Exist

Run this in Supabase SQL Editor:

```sql
-- Check table count (should be 17)
SELECT COUNT(*) as table_count
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_type = 'BASE TABLE';

-- List all tables
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_type = 'BASE TABLE'
ORDER BY table_name;
```

Expected tables (17 total):

- [ ] obd_codes
- [ ] message_logs
- [ ] diagnostic_logs
- [ ] conversation_sessions
- [ ] external_obd_cache
- [ ] obd_summaries
- [ ] vehicle_overrides
- [ ] code_vehicle_fitment
- [ ] repair_steps
- [ ] parts
- [ ] common_symptoms
- [ ] related_codes
- [ ] system_diagrams
- [ ] transactions
- [ ] subscriptions
- [ ] user_usage
- [ ] (Plus internal Supabase tables)

---

## Step 9: Restart Backend

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

**Estimated Time:** 15-25 minutes  
**Difficulty:** Easy (if WARP is disabled)  
**Result:** Full production-ready system with payments and rich diagnostics

---

## Complete Database Inventory

### Tables by Category

| Category | Table Name | Rows (Estimated) | Purpose |
|----------|-----------|------------------|---------|
| **Core OBD** | obd_codes | 5,000+ | Master DTC code database |
| | message_logs | Growing | WhatsApp message audit trail |
| | diagnostic_logs | Growing | Analytics/usage tracking |
| | conversation_sessions | Active users | Multi-turn conversation state |
| | external_obd_cache | As needed | Cache external API responses |
| | obd_summaries | As needed | AI-generated summaries |
| | vehicle_overrides | As needed | Vehicle-specific known issues |
| **DTC Details** | code_vehicle_fitment | 50,000+ | Which vehicles per code |
| | repair_steps | 25,000+ | Step-by-step repair instructions |
| | parts | 15,000+ | Required parts |
| | common_symptoms | 10,000+ | Driver-reported symptoms |
| | related_codes | 20,000+ | Related DTC codes |
| **Educational** | system_diagrams | 100+ | System diagram URLs |
| **Payments** | transactions | Growing | Payment records |
| | subscriptions | Active users | Active subscriptions |
| | user_usage | Active users | Free tier usage tracking |

**Total: 16 user tables** (plus Supabase internal tables)

### Database Functions

| Function Name | Returns | Purpose |
|--------------|---------|---------|
| update_updated_at_column() | TRIGGER | Auto-update timestamps |
| has_active_subscription(phone_hash) | BOOLEAN | Check subscription status |
| get_weekly_usage(phone_hash) | INT | Get diagnostic count for week |
| increment_user_usage(phone_hash) | INT | Increment usage counter |

### Views

| View Name | Purpose |
|-----------|---------|
| active_subscriptions | Currently active subscriptions only |

---

## Migration File Reference

| Order | File | Creates |
|-------|------|---------|
| 1 | `supabase/migrations/001_initial_schema.sql` | 7 core tables |
| 2 | `migrations/add_system_diagrams_table.sql` | 1 educational table |
| 3 | `migrations/add_dtc_detail_tables.sql` | 5 DTC detail tables + triggers |
| 4 | `migrations/add_payments_tables.sql` | 3 payment tables + functions + view |

---

## Data Population Checklist

### Immediate Priority (Required for Launch)

- [ ] **obd_codes**: Import base 132+ codes via `scripts/import_obd_datasets.py`
- [ ] Test codes: P0420, P0300, P0171, P0128

### High Priority (Enhances UX)

- [ ] **system_diagrams**: Add 10-20 most common systems
  - Catalytic converter, O2 sensor, MAF sensor, throttle body
  - Source: Wikimedia Commons (CC-licensed)

### Medium Priority (Rich Diagnostics)

- [ ] **code_vehicle_fitment**: Top 100 codes × top 20 vehicle models
- [ ] **repair_steps**: Instructions for top 50 common codes
- [ ] **parts**: Parts for top 50 common codes
- [ ] **common_symptoms**: Symptoms for top 50 codes
- [ ] **related_codes**: Relationships for top 50 codes

### Low Priority (Build Over Time)

- [ ] **vehicle_overrides**: Add as discovered
- [ ] **obd_summaries**: Auto-populated by AI system
- [ ] **external_obd_cache**: Auto-populated during operation

---

## Environment Variables Required

```env
# Supabase Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key

# Paynow Payment Gateway (Zimbabwe)
PAYNOW_INTEGRATION_ID=your-paynow-id
PAYNOW_INTEGRATION_KEY=your-paynow-key
PAYNOW_RETURN_URL=https://your-domain.com/payment/return
PAYNOW_RESULT_URL=https://your-domain.com/payment/callback

# WhatsApp Business API
WHATSAPP_TOKEN=your-meta-token
WHATSAPP_PHONE_NUMBER_ID=your-phone-id
WHATSAPP_VERIFY_TOKEN=your-webhook-verify-token

# Optional: External OBD APIs
EXTERNAL_API_KEY=your-api-key
```

---

## Post-Setup Testing Checklist

### Core Functionality

- [ ] Test OBD code lookup (P0420)
- [ ] Test multi-turn conversation
- [ ] Verify session persistence after restart
- [ ] Check message logging works

### Payment Flow

- [ ] Test subscription purchase (dev/test mode)
- [ ] Verify transaction recorded
- [ ] Check subscription activated
- [ ] Test usage limits (free tier)

### DTC Details (Once Populated)

- [ ] Test vehicle fitment query
- [ ] Test repair steps retrieval
- [ ] Test parts lookup
- [ ] Test symptom matching

### Educational Content (Once Populated)

- [ ] Test system diagram retrieval
- [ ] Verify image URLs work
- [ ] Check attribution text

---

## Troubleshooting Reference

### Database Connection Issues

**Symptom:** "supabase_unreachable" in logs

Solutions:

1. Disable Cloudflare WARP
2. Check .env has correct SUPABASE_URL and SUPABASE_SERVICE_KEY
3. Test connection: `curl https://your-project.supabase.co`
4. Verify Supabase project is not paused

### Table Missing Errors

**Symptom:** "relation does not exist" errors

Solutions:

1. Run migrations in order (see Migration File Reference above)
2. Check Supabase Table Editor to verify tables exist
3. Re-run migration SQL if needed

### Permission Errors

**Symptom:** "401 Unauthorized" or "403 Forbidden"

Solutions:

1. Use service_role key, not anon key
2. Check grants in migration files ran successfully
3. Manually grant permissions if needed

### Payment Function Errors

**Symptom:** Functions not found

Solutions:

1. Verify `migrations/add_payments_tables.sql` ran completely
2. Check functions exist: SQL Editor → Database → Functions
3. Re-run payment migration if needed

---

## Success Indicators

You're fully set up when:

- ✅ All 16 user tables exist in Table Editor
- ✅ 4 functions visible in Database → Functions
- ✅ 1 view (active_subscriptions) exists
- ✅ 132+ OBD codes in obd_codes table
- ✅ Backend logs show "supabase_connected"
- ✅ Test code P0420 returns local_db source
- ✅ Sessions persist across backend restarts
- ✅ Messages logged to message_logs table
- ✅ Payment functions can be called

---

**Last Updated:** 2026-07-06  
**Schema Version:** v4 (with payments + DTC details)  
**Your Current Status:** Ready to begin setup
