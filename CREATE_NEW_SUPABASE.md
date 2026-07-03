# Create New Supabase Project

Your current Supabase project URL is not resolving. This means:
- The project was deleted/paused, OR
- The URL has changed

**Solution: Create a fresh project (takes 5 minutes)**

---

## Step 1: Go to Supabase Dashboard

Open your browser and go to:
```
https://supabase.com/dashboard
```

Login with your account.

---

## Step 2: Check Existing Projects

Look at the list of projects on the left.

**Do you see any projects?**

### If YES - Project exists:
1. Click on the project
2. Check if it's paused (look for "Resume" button)
3. If paused, click "Resume" and wait
4. Go to Settings → API
5. Copy the **Project URL** and **service_role key**
6. Skip to Step 4 below

### If NO - No projects or wrong project:
Continue to Step 3 to create a new one.

---

## Step 3: Create New Project

1. Click **"New Project"** button (top right or center)

2. Fill in the form:
   ```
   Name: vehicle-diagnosis
   Database Password: (click generate, then COPY and SAVE IT!)
   Region: (choose closest - e.g., US East, EU West, etc.)
   Pricing Plan: Free
   ```

3. Click **"Create new project"**

4. **WAIT 2-3 MINUTES** - Project is being set up
   - You'll see "Setting up project..."
   - Don't close the page!

5. When ready, you'll see the dashboard

---

## Step 4: Get Your Credentials

Once project is ready:

### A. Get Project URL

1. Look at the URL in your browser
2. It will be something like: `https://abcdefghijklmnop.supabase.co`
3. Copy the full URL

OR

1. Go to **Settings** (left sidebar)
2. Click **API**
3. Under "Configuration" section
4. Copy the **Project URL**

**Example:**
```
https://xyzabc123456.supabase.co
```

### B. Get Service Role Key

1. Still in Settings → API
2. Scroll to "Project API keys"
3. Find **service_role** (secret)
4. Click **"Reveal"** or the eye icon
5. Click **"Copy"**

**This is a LONG key that starts with `eyJ...`**

⚠️ **Use service_role, NOT anon/public key!**

---

## Step 5: Update .env File

1. Open: `C:\Users\vinmu\Desktop\VehicleDiagnosisAssistant\.env`

2. Find these lines:
```env
SUPABASE_URL=https://ojxijkrkadymllbigcme.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

3. Replace with YOUR NEW values:
```env
SUPABASE_URL=https://YOUR-NEW-PROJECT-ID.supabase.co
SUPABASE_SERVICE_KEY=YOUR-NEW-SERVICE-ROLE-KEY-HERE
```

4. **Save the file** (Ctrl+S)

---

## Step 6: Verify Connection

Open PowerShell and test:

```powershell
cd C:\Users\vinmu\Desktop\VehicleDiagnosisAssistant
.\venv\Scripts\activate
python -c "from app.db.client import get_supabase_client; from app.core.config import settings; print(f'URL: {settings.supabase_url}'); client = get_supabase_client(); print('Connected!' if client else 'Failed')"
```

**Expected output:**
```
URL: https://your-new-project.supabase.co
Connected!
```

**If you see "Connected!", proceed to Step 7!**

---

## Step 7: Create Tables

Now that you have a working project:

1. Go to Supabase Dashboard
2. Click **SQL Editor** (left sidebar)
3. Click **"New query"**
4. On your computer, open: `supabase\migrations\001_initial_schema.sql`
5. **Select ALL** (Ctrl+A)
6. **Copy** (Ctrl+C)
7. Go back to SQL Editor
8. **Paste** (Ctrl+V)
9. Click **"RUN"** (or Ctrl+Enter)

**Should see:** "Success. No rows returned"

---

## Step 8: Verify Tables

1. Click **Table Editor** (left sidebar)
2. You should see **7 tables**:
   - obd_codes
   - message_logs
   - diagnostic_logs
   - conversation_sessions
   - external_obd_cache
   - obd_summaries
   - vehicle_overrides

**✅ All 7 tables? Great!**

---

## Step 9: Import OBD Codes

```powershell
cd C:\Users\vinmu\Desktop\VehicleDiagnosisAssistant
.\venv\Scripts\activate
python scripts\import_obd_datasets.py
```

**Expected:**
```
Connected to Supabase: https://your-project.supabase.co
Loaded 132 codes from local dataset
...
Import complete!
Imported: 132+
```

---

## Step 10: Restart Backend

```powershell
# Stop backend (Ctrl+C in its terminal)
.\start_backend.bat
```

**Look for:**
```
[info] supabase_connected  <- SUCCESS!
```

---

## Step 11: Test!

Send via WhatsApp:
```
P0420
```

Backend logs should show:
```
[info] obd_lookup_success code=P0420 source=local_db
```

**✅ DONE!**

---

## Quick Summary

```
1. Go to supabase.com/dashboard
2. Create new project (or use existing)
3. Get Project URL + service_role key
4. Update .env file
5. Run migration SQL (create tables)
6. Import codes: python scripts\import_obd_datasets.py
7. Restart backend
8. Test via WhatsApp
```

**Total time: 10 minutes**

---

## What If I Can't Create Project?

**Reason 1: Account limit reached**
- Free tier: 2 projects max
- Solution: Delete old/unused projects, or upgrade

**Reason 2: Email not verified**
- Check your email for verification link
- Click it and try again

**Reason 3: Payment method required**
- Some accounts need payment method even for free tier
- Add a card (won't be charged for free tier)

---

## Need Help?

If stuck:
1. Take a screenshot of the error
2. Check Supabase status: status.supabase.com
3. Read Supabase docs: supabase.com/docs

The old project URL (`ojxijkrkadymllbigcme`) is not working.
Creating a fresh project is the fastest solution!

---

**Your Next Action:**
Go to https://supabase.com/dashboard and check your projects!
