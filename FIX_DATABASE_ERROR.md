# Fix Database Error - Missing Subscriptions Table

## ❌ Current Error

```
APIError: Could not find the table 'public.subscriptions' in the schema cache
```

Your backend is crashing because the `subscriptions` table doesn't exist in your Supabase database.

## ✅ Solution

You need to run the SQL migration to create the missing tables.

---

## 🔧 Step-by-Step Fix

### Step 1: Open Supabase Dashboard

1. Go to: **https://supabase.com/dashboard/project/yalpyodkymdkgkridtom**
2. Log in if needed

### Step 2: Open SQL Editor

1. Click **"SQL Editor"** in the left sidebar
2. Click **"New query"** button

### Step 3: Run the Migration

1. Open the file: `migrations/add_payments_tables.sql`
2. **Copy ALL contents** (239 lines)
3. **Paste** into the Supabase SQL Editor
4. Click **"Run"** button

### Step 4: Verify Tables Created

Run this query to verify:

```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('transactions', 'subscriptions', 'user_usage');
```

You should see 3 tables listed:
- ✅ `transactions`
- ✅ `subscriptions`
- ✅ `user_usage`

### Step 5: Restart Backend

```powershell
# Stop current backend (Ctrl+C)
# Then restart:
.\start_backend.bat
```

---

## 📋 What Gets Created

The migration creates:

### Tables
1. **`transactions`** - Payment records (Paynow integration)
2. **`subscriptions`** - Active user subscriptions
3. **`user_usage`** - Free tier usage tracking (5 diagnostics/week)

### Helper Functions
- `has_active_subscription()` - Check if user is subscribed
- `get_weekly_usage()` - Get user's weekly diagnostic count
- `increment_user_usage()` - Track diagnostic usage

### Views
- `active_subscriptions` - View of currently active subscriptions

---

## 🎯 After Fix

Once tables are created, your backend will:
- ✅ Accept WhatsApp webhook requests without crashing
- ✅ Track user subscriptions
- ✅ Enforce free tier limits (5 diagnostics per week)
- ✅ Allow paid users unlimited diagnostics

---

## 🔍 Troubleshooting

### Issue: SQL Editor shows error

**Solution**: Make sure you're logged in with the correct Supabase account that owns this project.

### Issue: Tables still not found after running SQL

**Solution**: 
1. Check the SQL ran without errors
2. Verify tables exist:
   ```sql
   \dt public.*
   ```
3. Restart Supabase connection (restart backend)

### Issue: Permission errors

**Solution**: The migration includes GRANT statements to give proper permissions to `authenticated` and `service_role`.

---

## 📝 Quick Test

After fixing, test with:

```bash
# Check if backend starts without errors
.\start_backend.bat

# Send a test WhatsApp message
# Should no longer get 500 error
```

---

## ℹ️ Why This Happened

The payment system tables were added later to support:
- Paynow payment integration (Zimbabwe EcoCash)
- Monthly subscriptions ($2/month unlimited)
- Free tier limits (5 diagnostics per week)

These tables need to be created in your database before the payment features work.

---

## 🎉 After Fix Expected Logs

You should see:
```
✅ ai_client_initialized provider=cohere
✅ ai_backup_initialized backup_provider=gemini
✅ supabase_connected
✅ Application startup complete
```

And webhook requests should return `200 OK` instead of `500 Internal Server Error`.

---

**File to run in Supabase**: `migrations/add_payments_tables.sql`  
**Supabase Project**: https://supabase.com/dashboard/project/yalpyodkymdkgkridtom
