# Image Caching Solution

## Problem

Image sending is slow (18-53 seconds per diagnostic) because:

1. The Baileys server passes Wikimedia URLs directly to WhatsApp
2. WhatsApp downloads the image fresh from Wikimedia CDN on EVERY request
3. No caching occurs - every diagnostic triggers a full download

## Root Cause

```javascript
// baileys-server/index.js:481-482
const messagePayload = {
    image: { url: image.url }  // ← WhatsApp downloads this EVERY time
}
```

## Solution Implemented

### 1. Local Image Caching (baileys-server/cache-images.js)

Script that:
- Downloads all diagram images from Wikimedia once
- Saves them to `baileys-server/cached-images/` directory
- Updates database to point to local URLs (`http://localhost:3000/cached-images/...`)
- Includes retry logic for rate limiting

### 2. Static File Serving (baileys-server/index.js)

Added endpoint to serve cached images:

```javascript
app.use('/cached-images', express.static('cached-images', {
    maxAge: '1y',  // Cache for 1 year
    immutable: true
}))
```

### 3. Reduced Timeout (app/api/routes/webhook.py:650)

Once caching is in place, images load instantly from local server:

```python
timeout=15.0  # Images are cached locally, should be fast
```

## Current Issue: Wikimedia Rate Limiting

Wikimedia CDN is blocking bulk downloads (HTTP 429) even with:
- User-Agent headers
- 3-second delays between requests
- Exponential backoff retry logic

This is a common Wikimedia anti-scraping measure.

## Manual Workaround

**Option A: Manual download via browser**

1. Open each Wikimedia URL in a browser (bypasses rate limits)
2. Save images to `baileys-server/cached-images/`
3. Use these filenames (sanitized system names):

```
catalytic-converter.jpg
oxygen-sensor.svg
egr-valve.jpg
evap-system.jpg
mass-air-flow-sensor.jpg
throttle-body.png
ignition-coil.jpg
spark-plug.png
fuel-injector.jpg
fuel-pump.jpg
map-sensor.jpg
camshaft-position-sensor.jpg
crankshaft-position-sensor.jpg
knock-sensor.jpg
thermostat.jpg
pcv-valve.jpg
radiator.jpg
timing-belt.jpg
alternator.jpg
battery.jpeg
brake-pads.jpg
wheel-speed-sensor.jpg
transmission.jpg
air-intake-manifold.png
```

4. Manually update database URLs:

```sql
UPDATE system_diagrams
SET image_url = 'http://localhost:3000/cached-images/<filename>',
    source = source || ' (cached locally)'
WHERE system = '<system-name>';
```

**Option B: Wait 24 hours**

Wikimedia rate limits typically reset after 24 hours. Run the caching script again tomorrow:

```bash
cd baileys-server
node cache-images.js
```

**Option C: Use Supabase Storage**

Upload images to Supabase Storage via their web UI:

1. Go to Supabase dashboard → Storage
2. Create bucket `system-diagrams` (public)
3. Upload each image manually
4. Update database with Supabase Storage URLs

## Verification

Once caching is complete, test that images load quickly:

```bash
# Check cached images exist
ls baileys-server/cached-images/

# Test static serving
curl http://localhost:3000/cached-images/catalytic-converter.jpg

# Send a diagnostic and time the response
# Should be <5s total (was 18-53s before)
```

## Expected Performance After Caching

- **Before**: 18-53 seconds per image (fresh Wikimedia download every time)
- **After**: <2 seconds per image (local file served from Baileys server)
- **Image arrives BEFORE text** (already correct in code, just slow before)

## Files Changed

1. `baileys-server/cache-images.js` - Image caching script
2. `baileys-server/index.js` - Added `/cached-images` static endpoint
3. `app/api/routes/webhook.py` - Reduced timeout from 60s to 15s
4. `.env` - Added `BAILEYS_BASE_URL=http://localhost:3000`

## Database Status

Current diagram coverage (24 systems):
- air intake manifold
- alternator
- battery
- brake pads
- camshaft position sensor
- catalytic converter
- crankshaft position sensor
- egr valve
- evap system
- fuel injector
- fuel pump
- ignition coil
- knock sensor
- map sensor
- mass air flow sensor
- oxygen sensor
- pcv valve
- radiator
- spark plug
- thermostat
- throttle body
- timing belt
- transmission
- wheel speed sensor

All currently point to Wikimedia URLs that need to be cached.
