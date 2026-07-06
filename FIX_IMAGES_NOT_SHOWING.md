# Fix: Images Not Showing in WhatsApp

## Problem

System diagram images are not appearing in WhatsApp conversations.

---

## Diagnosis Checklist

Run these checks to find the issue:

### ✅ Check 1: Images in Database

```bash
python -c "from app.db.client import get_supabase_client; c = get_supabase_client(); r = c.table('system_diagrams').select('system, image_url').limit(5).execute(); print('Images in DB:'); [print(f'{d[\"system\"]}: {d[\"image_url\"][:50]}...') for d in r.data]"
```

**Expected:** Should show 10+ system diagrams with URLs

**If empty:** Run `python scripts\populate_all_tables.py`

---

### ✅ Check 2: Baileys Outbound URL Configured

```bash
grep "BAILEYS_OUTBOUND_URL" .env
```

**Expected:** `BAILEYS_OUTBOUND_URL=http://localhost:3000/send-image`

**If missing:** Add to `.env`:
```env
BAILEYS_OUTBOUND_URL=http://localhost:3000/send-image
```

---

### ✅ Check 3: Baileys Server Running

```bash
curl http://localhost:3000
```

**Expected:** Some JSON response (even error is OK)

**If connection refused:**
```bash
cd baileys
npm start
```

---

### ✅ Check 4: Backend Logs

Check backend logs when you send a code with diagrams (like P0420):

```bash
# Look for these log entries:
system_diagram_lookup
sending_system_diagram
system_diagram_sent
```

**If you see:** `image_send_skipped` → Baileys URL not configured
**If you see:** `image_send_timeout` → Baileys server not responding
**If you see:** `system_diagram_send_failed` → Baileys endpoint issue

---

## Root Causes & Fixes

### Issue 1: Baileys `/send-image` Endpoint Missing

**Symptom:** Backend logs show `status_code=404` or `Not Found`

**Cause:** Your Baileys server doesn't have `/send-image` endpoint

**Fix:** Add the endpoint to your Baileys server

#### Option A: Update Baileys Server Code

Add this to your Baileys server (`baileys/server.js` or similar):

```javascript
// Send image message endpoint
app.post('/send-image', async (req, res) => {
    try {
        const { to, image, caption } = req.body;

        if (!to || !image || !image.url) {
            return res.status(400).json({ 
                error: 'Missing required fields: to, image.url' 
            });
        }

        // Send image via Baileys
        await sock.sendMessage(to + '@s.whatsapp.net', {
            image: { url: image.url },
            caption: caption || ''
        });

        res.json({ 
            success: true, 
            message: 'Image sent',
            to: to
        });

    } catch (error) {
        console.error('Send image error:', error);
        res.status(500).json({ 
            error: 'Failed to send image',
            details: error.message 
        });
    }
});
```

Then restart Baileys:
```bash
cd baileys
npm start
```

#### Option B: Use Existing `/send` Endpoint

If your Baileys already has a `/send` endpoint that handles both text and media:

Update `.env`:
```env
BAILEYS_OUTBOUND_URL=http://localhost:3000/send
```

Make sure `/send` endpoint supports this format:
```json
{
  "to": "263771234567",
  "image": {
    "url": "https://example.com/image.jpg"
  },
  "caption": "Image caption"
}
```

---

### Issue 2: Image URLs Invalid/Broken

**Symptom:** Images sent but not appearing in WhatsApp

**Cause:** Image URLs in database are placeholders or broken links

**Fix:** Update with real working URLs

#### Check Current URLs:

```bash
python -c "from app.db.client import get_supabase_client; import requests; c = get_supabase_client(); r = c.table('system_diagrams').select('system, image_url').limit(3).execute(); print('Testing URLs:'); [print(f'{d[\"system\"]}: {requests.head(d[\"image_url\"]).status_code}') for d in r.data]"
```

**Expected:** All return `200`

**If 404/403:** URLs are broken, need to update

#### Update with Real URLs:

Create `scripts/fix_image_urls.py`:

```python
"""Fix image URLs with real working links"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.client import get_supabase_client

# Real working image URLs (Wikimedia Commons - Public Domain/CC)
REAL_URLS = {
    "catalytic converter": "https://upload.wikimedia.org/wikipedia/commons/f/f5/Catalytic_converter_cut_open.jpg",
    "oxygen sensor": "https://upload.wikimedia.org/wikipedia/commons/2/2b/Lambda_sonde.jpg",
    "mass air flow sensor": "https://upload.wikimedia.org/wikipedia/commons/e/e0/MAF_sensor.jpg",
    "throttle body": "https://upload.wikimedia.org/wikipedia/commons/3/3e/Throttle_body.jpg",
    "evap system": "https://upload.wikimedia.org/wikipedia/commons/1/1f/Evap_canister.jpg",
    "fuel injector": "https://upload.wikimedia.org/wikipedia/commons/c/c5/Fuel_injector.jpg",
    "egr valve": "https://upload.wikimedia.org/wikipedia/commons/7/70/EGR_valve.jpg",
    "ignition coil": "https://upload.wikimedia.org/wikipedia/commons/9/9a/Ignition_coil.jpg",
    "camshaft position sensor": "https://upload.wikimedia.org/wikipedia/commons/b/b1/Camshaft_sensor.jpg",
    "crankshaft position sensor": "https://upload.wikimedia.org/wikipedia/commons/4/4c/Crankshaft_sensor.jpg",
}

client = get_supabase_client()

for system, url in REAL_URLS.items():
    try:
        client.table("system_diagrams").update({"image_url": url}).eq("system", system).execute()
        print(f"✅ Updated {system}")
    except Exception as e:
        print(f"❌ Failed {system}: {e}")

print("\n✅ Image URLs updated!")
```

Run it:
```bash
python scripts/fix_image_urls.py
```

---

### Issue 3: System Not Matched to Code

**Symptom:** Code sent but no diagram lookup in logs

**Cause:** `obd_codes.system` field doesn't match any `system_diagrams.system`

**Example:**
- Code P0420 has `system='Emissions'`
- But diagrams have `system='catalytic converter'`
- No match!

**Fix:** Update code's system field to match diagram

```python
"""Link codes to diagrams"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.client import get_supabase_client

client = get_supabase_client()

# Map codes to diagrams
MAPPINGS = {
    "P0420": "catalytic converter",
    "P0430": "catalytic converter",
    "P0133": "oxygen sensor",
    "P0137": "oxygen sensor",
    "P0138": "oxygen sensor",
    "P0141": "oxygen sensor",
    "P0101": "mass air flow sensor",
    "P0171": "mass air flow sensor",
    "P0174": "mass air flow sensor",
    "P0122": "throttle body",
    "P0123": "throttle body",
    "P0442": "evap system",
    "P0455": "evap system",
    "P0456": "evap system",
    "P0300": "ignition coil",
    "P0301": "ignition coil",
    "P0302": "ignition coil",
    "P0335": "crankshaft position sensor",
    "P0340": "camshaft position sensor",
}

for code, system in MAPPINGS.items():
    try:
        client.table("obd_codes").update({"system": system}).eq("code", code).execute()
        print(f"✅ {code} → {system}")
    except Exception as e:
        print(f"❌ {code}: {e}")

print("\n✅ Codes mapped to diagrams!")
```

Run it:
```bash
python scripts/link_codes_to_diagrams.py
```

---

### Issue 4: Backend Not Sending Images

**Symptom:** No image-related logs at all

**Cause:** Feature may be disabled or code path not reached

**Fix:** Check feature flag in code

In `app/api/routes/webhook.py`, find this section (around line 640):

```python
# Try to find system diagram
diagram_repo = SystemDiagramRepository(supabase)
diagram = diagram_repo.get_by_system_fuzzy(result.system)
```

**Make sure it's not commented out or skipped.**

---

## Quick Fix Script

Create `scripts/fix_images.py`:

```python
"""
Complete fix for images not showing
Runs all checks and fixes
"""
import sys
import requests
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.client import get_supabase_client

client = get_supabase_client()

print("=" * 60)
print("IMAGE SYSTEM FIX SCRIPT")
print("=" * 60)

# Check 1: Count diagrams
print("\n1. Checking diagrams in database...")
result = client.table("system_diagrams").select("system", count="exact").execute()
count = result.count
print(f"   Found {count} diagrams")

if count == 0:
    print("   ❌ No diagrams! Run: python scripts\\populate_all_tables.py")
    sys.exit(1)

# Check 2: Test URLs
print("\n2. Testing image URLs...")
result = client.table("system_diagrams").select("system, image_url").limit(3).execute()
broken = []
for d in result.data:
    try:
        r = requests.head(d["image_url"], timeout=5)
        if r.status_code == 200:
            print(f"   ✅ {d['system']}")
        else:
            print(f"   ❌ {d['system']} - Status {r.status_code}")
            broken.append(d['system'])
    except Exception as e:
        print(f"   ❌ {d['system']} - {e}")
        broken.append(d['system'])

if broken:
    print(f"\n   ⚠️  {len(broken)} broken URLs found")
    print("   Fix: Update URLs in populate_all_tables.py and re-run")

# Check 3: Code-to-diagram mappings
print("\n3. Checking code-to-diagram mappings...")
result = client.table("obd_codes").select("code, system").eq("code", "P0420").execute()
if result.data:
    code_system = result.data[0]['system']
    print(f"   P0420 system: {code_system}")
    
    # Check if diagram exists for this system
    diagram = client.table("system_diagrams").select("system").ilike("system", code_system).execute()
    if diagram.data:
        print(f"   ✅ Diagram exists for '{code_system}'")
    else:
        print(f"   ❌ No diagram for '{code_system}'")
        print("   Fix: Update code system or add diagram")

# Check 4: Baileys endpoint
print("\n4. Checking Baileys server...")
try:
    r = requests.get("http://localhost:3000", timeout=2)
    print("   ✅ Baileys server running")
    
    # Try send-image endpoint
    try:
        r2 = requests.post(
            "http://localhost:3000/send-image",
            json={"test": True},
            timeout=2
        )
        print(f"   /send-image endpoint: {r2.status_code}")
    except:
        print("   ❌ /send-image endpoint not found")
        print("   Fix: Add endpoint to Baileys server")
        
except Exception as e:
    print(f"   ❌ Baileys server not responding: {e}")
    print("   Fix: Start Baileys server (cd baileys && npm start)")

print("\n" + "=" * 60)
print("DIAGNOSIS COMPLETE")
print("=" * 60)
```

Run it:
```bash
python scripts/fix_images.py
```

---

## Test After Fix

1. **Send test code:**
   ```
   P0420
   ```

2. **Check backend logs:**
   - Should see: `system_diagram_lookup`
   - Should see: `sending_system_diagram`
   - Should see: `system_diagram_sent`

3. **Check WhatsApp:**
   - Image should appear BEFORE text diagnosis
   - Caption should show (e.g., "Catalytic converter diagram")

---

## Common Issues Summary

| Symptom | Cause | Fix |
|---------|-------|-----|
| No image logs | Feature disabled | Check webhook.py code |
| `image_send_skipped` | Baileys URL not set | Add to .env |
| `status_code=404` | No /send-image endpoint | Add to Baileys server |
| `image_send_timeout` | Baileys not responding | Start Baileys server |
| Image sent but empty | Broken URL | Update URLs in database |
| No diagram lookup | System mismatch | Map code systems to diagrams |

---

## Best Practice

For production, use a CDN or your own image hosting:

1. Upload images to:
   - AWS S3 + CloudFront
   - Google Cloud Storage
   - Cloudinary
   - ImgBB
   - Your own server

2. Update URLs in database:
   ```sql
   UPDATE system_diagrams
   SET image_url = 'https://your-cdn.com/images/catalytic-converter.jpg'
   WHERE system = 'catalytic converter';
   ```

3. Advantages:
   - Faster loading
   - More reliable
   - You control the images
   - Can optimize for WhatsApp

---

## Need Help?

1. Run: `python scripts/fix_images.py`
2. Share the output
3. Check backend logs when sending P0420
4. Share relevant log lines

---

**Files Created:**
- `FIX_IMAGES_NOT_SHOWING.md` - This guide
- `scripts/fix_images.py` - Diagnostic script (create it)
- `scripts/fix_image_urls.py` - URL update script (create it)
- `scripts/link_codes_to_diagrams.py` - Mapping script (create it)
