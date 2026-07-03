# 🔧 Supabase Connection Fix

## Problem Identified ✅

Your Supabase connection is failing because:

```
DNS Server: connectivity-check.warp-svc (127.0.2.2)
Error: Non-existent domain - ojxijkrkadymllbigcme.supabase.co
```

**Root Cause:** You're using **Cloudflare WARP VPN** which is blocking Supabase DNS resolution.

## Quick Solutions

### Solution 1: Disable Cloudflare WARP (Easiest) ⭐

**Windows:**
1. Click the WARP icon in system tray (near clock)
2. Click "Disconnect" or toggle OFF
3. Restart your backend: `Ctrl+C` then run `.\start_backend.bat`
4. Look for: `[info] supabase_connected`

**Or permanently disable:**
1. Open Cloudflare WARP app
2. Settings → Account → Logout
3. Or uninstall: Settings → Apps → Cloudflare WARP → Uninstall

### Solution 2: Add Supabase to WARP Split Tunnel

Keep WARP on but allow Supabase through:

1. Open Cloudflare WARP app
2. Settings → Gateway with WARP → Split Tunnels
3. Click "Manage"
4. Add these domains to "Exclude from WARP":
   ```
   *.supabase.co
   *.supabase.io
   ```
5. Save and reconnect WARP
6. Test: `nslookup ojxijkrkadymllbigcme.supabase.co`

### Solution 3: Change DNS Servers (Keep WARP)

Override WARP DNS temporarily:

**Windows:**
1. Press `Win + R`, type `ncpa.cpl`, press Enter
2. Right-click your network adapter → Properties
3. Select "Internet Protocol Version 4 (TCP/IPv4)" → Properties
4. Select "Use the following DNS server addresses":
   - Preferred: `8.8.8.8` (Google)
   - Alternate: `1.1.1.1` (Cloudflare)
5. Click OK, OK
6. Run: `ipconfig /flushdns`
7. Test: `nslookup ojxijkrkadymllbigcme.supabase.co`

### Solution 4: Verify Supabase Project Still Exists

**Check if your project is active:**

1. Go to: https://supabase.com/dashboard
2. Login to your account
3. Look for your project
4. If it doesn't exist or is paused:
   - Create a new project
   - Copy new URL and keys
   - Update `.env` file

## Testing the Fix

### Step 1: Test DNS Resolution

```bash
nslookup ojxijkrkadymllbigcme.supabase.co
```

**Should return:**
```
Server: [Your DNS]
Address: [DNS IP]

Non-authoritative answer:
Name:    ojxijkrkadymllbigcme.supabase.co
Address: [IP address]
```

### Step 2: Test HTTPS Connection

```bash
curl -I https://ojxijkrkadymllbigcme.supabase.co
```

**Should return:**
```
HTTP/2 200
server: Supabase
...
```

### Step 3: Restart Backend

```bash
# Stop current backend (Ctrl+C)
.\start_backend.bat
```

**Look for this in logs:**
```
[info] app_starting env=development supabase_url=https://ojxijkrkadymllbigcme.supabase.co
[info] supabase_connected  ← Success!
```

**NOT this:**
```
[warning] supabase_unreachable  ← Still broken
```

### Step 4: Test Full System

Send this via WhatsApp:
```
P0420
```

Check backend logs for:
```
[info] obd_lookup_success code=P0420 source=local_db
```

If it says `source=local_db` (not fallback), you're connected to Supabase!

## Verifying Supabase is Working

Once connected, you should have:
- ✅ 132+ OBD codes (vs 20 in fallback)
- ✅ Persistent sessions
- ✅ Message audit logs
- ✅ Usage analytics
- ✅ Rate limiting
- ✅ Auto-learning new codes

## Alternative: Use Different Supabase Project

If your project is deleted/paused:

### Create New Supabase Project

1. Go to: https://supabase.com/dashboard
2. Click "New Project"
3. Fill in details:
   - Name: `vehicle-diagnosis`
   - Database Password: (generate secure one)
   - Region: (closest to you)
4. Wait 2-3 minutes for setup

### Get Credentials

1. Go to: Settings → API
2. Copy:
   - **Project URL** (under Configuration)
   - **service_role key** (under Project API keys)

### Update .env File

```bash
SUPABASE_URL=https://your-new-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key-here
```

### Run Database Migrations

```bash
# 1. Go to Supabase Dashboard → SQL Editor
# 2. Copy contents of: supabase/migrations/001_initial_schema.sql
# 3. Paste and click "Run"
# 4. Seed OBD codes:
python scripts/import_obd_datasets.py
```

## Troubleshooting

### "Non-existent domain" Error
- ❌ WARP is still blocking
- ✅ Try Solution 1 (disable WARP)

### "Connection timeout" Error
- ❌ Firewall blocking outbound HTTPS
- ✅ Check Windows Firewall, antivirus

### "401 Unauthorized" Error
- ❌ Wrong API key
- ✅ Get service_role key (not anon key)

### "404 Not Found" Error
- ❌ Project deleted or URL changed
- ✅ Create new project (Solution 4)

### Still Not Working?
- Check if behind corporate proxy
- Try mobile hotspot to bypass network
- Check antivirus isn't blocking Python

## Current WARP Detection

Your system shows:
```
DNS Server: connectivity-check.warp-svc
Address: 127.0.2.2
```

This confirms WARP is active and intercepting DNS.

## Recommended Action

**Quickest Fix:**
1. Disable Cloudflare WARP temporarily
2. Restart backend
3. Test with WhatsApp
4. Re-enable WARP if needed (with split tunnel)

**Or keep WARP and add Supabase to split tunnel exclusions.**

---

**Next Steps:**
1. Choose a solution above
2. Test DNS resolution
3. Restart backend
4. Send WhatsApp message
5. Verify Supabase is connected

The fallback mode works great for now, but you'll want full Supabase for production!
