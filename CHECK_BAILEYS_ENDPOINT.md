# Check Baileys Endpoint for Images

## The Issue

Your backend is trying to send images to: `http://localhost:3000/send-image`

But the endpoint returns **401 Unauthorized**.

This means:
- ✅ Backend code is working
- ✅ Database has images
- ✅ URLs are configured
- ❌ Baileys endpoint needs fixing

---

## Quick Test

Run this to see what Baileys returns:

```bash
curl -X POST http://localhost:3000/send-image \
  -H "Content-Type: application/json" \
  -H "X-API-Key: a3bb4b6660552743096545286d5c6677d820b0326542bc8228d428c04bca0298" \
  -d '{
    "to": "263771234567",
    "image": {
      "url": "https://commons.wikimedia.org/wiki/Special:FilePath/Catalytic_converter_cut_open.jpg"
    },
    "caption": "Test image"
  }'
```

**Expected:** JSON response (not 401 error)

---

## Fix Options

### Option 1: Check Baileys Server Code

Look in your Baileys server file (probably `baileys/server.js` or `baileys/index.js`):

**Does this endpoint exist?**
```javascript
app.post('/send-image', async (req, res) => {
    // ... endpoint code
});
```

**If NO** → Add the endpoint (see below)
**If YES** → Check API key validation

### Option 2: Check API Key Validation

Your backend sends this header:
```
X-API-Key: a3bb4b6660552743096545286d5c6677d820b0326542bc8228d428c04bca0298
```

Baileys endpoint must accept it:

```javascript
app.post('/send-image', async (req, res) => {
    // Check API key
    const apiKey = req.headers['x-api-key'];
    const expectedKey = process.env.BAILEYS_API_KEY || 'a3bb4b6660552743096545286d5c6677d820b0326542bc8228d428c04bca0298';

    if (apiKey !== expectedKey) {
        return res.status(401).json({ error: 'Unauthorized' });
    }

    // ... rest of endpoint
});
```

### Option 3: Disable API Key Check (Quick Fix)

Temporarily disable authentication to test:

```javascript
app.post('/send-image', async (req, res) => {
    // SKIP API KEY CHECK FOR NOW
    // const apiKey = req.headers['x-api-key'];
    // if (apiKey !== expectedKey) {
    //     return res.status(401).json({ error: 'Unauthorized' });
    // }

    try {
        const { to, image, caption } = req.body;

        if (!to || !image || !image.url) {
            return res.status(400).json({ 
                error: 'Missing required fields: to, image.url' 
            });
        }

        // Send via Baileys
        await sock.sendMessage(to + '@s.whatsapp.net', {
            image: { url: image.url },
            caption: caption || ''
        });

        console.log('[OK] Image sent to', to);

        res.json({ 
            success: true, 
            message: 'Image sent',
            to: to
        });

    } catch (error) {
        console.error('[ERROR] Send image failed:', error);
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

### Option 4: Use Existing /send Endpoint

If Baileys already has a `/send` endpoint that works:

**Update `.env`:**
```env
BAILEYS_OUTBOUND_URL=http://localhost:3000/send
```

Make sure it accepts this format:
```json
{
  "to": "263771234567",
  "image": {
    "url": "https://example.com/image.jpg"
  },
  "caption": "Caption text"
}
```

---

## Complete /send-image Endpoint Code

If the endpoint doesn't exist, add this to your Baileys server:

```javascript
// POST /send-image - Send image message
app.post('/send-image', async (req, res) => {
    try {
        // Optional: Validate API key
        const apiKey = req.headers['x-api-key'];
        const expectedKey = process.env.BAILEYS_API_KEY || 'a3bb4b6660552743096545286d5c6677d820b0326542bc8228d428c04bca0298';

        if (apiKey && apiKey !== expectedKey) {
            console.log('[WARN] Invalid API key');
            return res.status(401).json({ error: 'Unauthorized' });
        }

        // Parse request
        const { to, image, caption } = req.body;

        // Validate required fields
        if (!to) {
            return res.status(400).json({ error: 'Missing "to" field' });
        }

        if (!image || !image.url) {
            return res.status(400).json({ error: 'Missing "image.url" field' });
        }

        // Format phone number
        const jid = to.includes('@') ? to : to + '@s.whatsapp.net';

        console.log('[INFO] Sending image to', jid);
        console.log('[INFO] Image URL:', image.url);

        // Send image via Baileys
        await sock.sendMessage(jid, {
            image: { url: image.url },
            caption: caption || ''
        });

        console.log('[OK] Image sent successfully');

        res.json({ 
            success: true, 
            message: 'Image sent',
            to: to,
            timestamp: new Date().toISOString()
        });

    } catch (error) {
        console.error('[ERROR] Send image failed:', error);
        res.status(500).json({ 
            error: 'Failed to send image',
            details: error.message 
        });
    }
});
```

**Then restart:**
```bash
cd baileys
npm start
```

---

## Test After Fix

1. **Send P0420 via WhatsApp**
2. **Check backend logs** - should see `system_diagram_sent`
3. **Check Baileys logs** - should see `[OK] Image sent`
4. **Check WhatsApp** - image should appear before text

---

## Debugging Tips

### Check if endpoint exists:
```bash
curl http://localhost:3000/send-image
```

**If 404** → Endpoint doesn't exist, add it
**If 401** → Endpoint exists but needs API key
**If 400** → Endpoint works! (just missing body fields)

### Check Baileys logs:
```bash
cd baileys
npm start
# Watch for logs when backend sends image
```

### Check backend logs:
Look for:
- `sending_system_diagram` - Backend attempting send
- `system_diagram_sent` - Success
- `image_send_failed` - Failed with reason

---

## Summary

**Most likely issue:** Baileys `/send-image` endpoint either:
1. Doesn't exist → Add it
2. Has strict API key check → Temporarily disable or fix key
3. Not handling the request format → Update endpoint code

**Quick fix:** Temporarily remove API key validation to test, then add it back properly.

---

Last Updated: 2026-07-06
