# 🔑 Get Your Supabase Service Key

Your `.env` file currently has a **publishable key**, but you need the **service_role key** for database operations.

---

## Quick Fix (2 minutes)

### Step 1: Go to Supabase Dashboard
```
https://supabase.com/dashboard/project/your-supabase-project-id
```

### Step 2: Navigate to API Settings
```
Settings → API
```

### Step 3: Copy the Service Role Key
Look for the section: **Project API keys**

You'll see two keys:
- ✅ **anon / public** - For client-side (browser)
- ✅ **service_role** - For server-side ← **YOU NEED THIS ONE**

### Step 4: Update `.env` File
Replace line 3 in your `.env`:

**Current (wrong):**
```bash
SUPABASE_SERVICE_KEY=your-supabase-key
```

**Should be:**
```bash
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

The service_role key is a **long JWT token** that starts with `eyJ`.

---

## Visual Guide

```
Supabase Dashboard
    ↓
Your Project: your-supabase-project-id
    ↓
Settings (left sidebar)
    ↓
API
    ↓
Project API keys section
    ↓
service_role (secret) ← Copy this!
    ↓
Paste into .env file
```

---

## After Updating

1. **Save** the `.env` file
2. **Run** the seeding script again:
   ```bash
   python scripts/seed_database.py
   ```

---

## Security Note

⚠️ **NEVER commit the service_role key to git!**

The `.env` file is already in `.gitignore`, so it won't be committed.

The service_role key has **full database access** - keep it secret!

---

## Troubleshooting

### "I don't see the service_role key"
- Make sure you're logged in to Supabase
- Verify you have access to the project
- Try refreshing the page

### "The key is hidden"
- Click the "eye" icon to reveal it
- Or click "Copy" to copy it directly

### "Still getting validation error"
- Make sure there are no extra spaces
- Make sure you copied the entire key
- Key should be ~200+ characters long

---

## Next Steps

After updating the key:
1. ✅ Run database migration (SQL in Supabase dashboard)
2. ✅ Run seeding script: `python scripts/seed_database.py`
3. ✅ Start server: `uvicorn app.main:app --reload`

You're almost there! 🚀
