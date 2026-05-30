# Baileys WhatsApp Setup Guide

Complete guide to connect your Vehicle Diagnosis Assistant to WhatsApp using Baileys.

---

## What is Baileys?

Baileys is a lightweight WhatsApp Web API for Node.js that lets you:
- Send/receive WhatsApp messages programmatically
- No official API needed (unlike Twilio)
- Free to use
- Connects like WhatsApp Web

---

## Quick Setup (3 Steps)

### Step 1: Install Node.js & Baileys

```bash
# Check if Node.js is installed
node --version

# If not installed, download from: https://nodejs.org
# Then install Baileys:
npm install @whiskeysockets/baileys
```

---

### Step 2: Create Baileys Server

Create a file: `baileys-server/index.js`

```javascript
const { default: makeWASocket, useMultiFileAuthState, DisconnectReason } = require('@whiskeysockets/baileys')
const express = require('express')
const axios = require('axios')

const app = express()
app.use(express.json())

let sock = null

// Your FastAPI backend URL
const BACKEND_URL = 'http://localhost:8000/webhook/baileys'

async function connectToWhatsApp() {
    const { state, saveCreds } = await useMultiFileAuthState('auth_info_baileys')
    
    sock = makeWASocket({
        auth: state,
        printQRInTerminal: true
    })

    sock.ev.on('creds.update', saveCreds)

    sock.ev.on('connection.update', (update) => {
        const { connection, lastDisconnect } = update
        if(connection === 'close') {
            const shouldReconnect = (lastDisconnect?.error)?.output?.statusCode !== DisconnectReason.loggedOut
            console.log('Connection closed. Reconnecting:', shouldReconnect)
            if(shouldReconnect) {
                connectToWhatsApp()
            }
        } else if(connection === 'open') {
            console.log('✅ WhatsApp Connected!')
        }
    })

    // Handle incoming messages
    sock.ev.on('messages.upsert', async ({ messages }) => {
        const msg = messages[0]
        if (!msg.message || msg.key.fromMe) return

        const from = msg.key.remoteJid
        const text = msg.message.conversation || msg.message.extendedTextMessage?.text || ''
        const messageId = msg.key.id

        console.log(`📩 Message from ${from}: ${text}`)

        try {
            // Send to your FastAPI backend
            const response = await axios.post(BACKEND_URL, {
                from: from,
                sender: from,
                text: text,
                message: text,
                message_id: messageId
            }, {
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Key': 'your-secret-key-here' // Optional: for security
                }
            })

            // Send reply back to WhatsApp
            const reply = response.data.reply
            await sock.sendMessage(from, { text: reply })
            console.log(`✅ Sent reply: ${reply.substring(0, 50)}...`)

        } catch (error) {
            console.error('❌ Error:', error.message)
            await sock.sendMessage(from, { text: 'Sorry, there was an error processing your request.' })
        }
    })
}

// API endpoint to send messages (optional)
app.post('/send', async (req, res) => {
    const { to, message } = req.body
    try {
        await sock.sendMessage(to, { text: message })
        res.json({ success: true })
    } catch (error) {
        res.status(500).json({ error: error.message })
    }
})

// Start server
app.listen(3000, () => {
    console.log('🚀 Baileys server running on port 3000')
    connectToWhatsApp()
})
```

---

### Step 3: Create package.json

Create `baileys-server/package.json`:

```json
{
  "name": "baileys-whatsapp-server",
  "version": "1.0.0",
  "description": "WhatsApp integration for Vehicle Diagnosis Assistant",
  "main": "index.js",
  "scripts": {
    "start": "node index.js"
  },
  "dependencies": {
    "@whiskeysockets/baileys": "^6.7.0",
    "express": "^4.18.2",
    "axios": "^1.6.0"
  }
}
```

---

## Running Baileys

### Terminal 1: Start FastAPI Backend

```powershell
# In VehicleDiagnosisAssistant directory
uvicorn app.main:app --reload --port 8000
```

### Terminal 2: Start Baileys Server

```bash
# In baileys-server directory
npm install
npm start
```

**You'll see a QR code in the terminal!**

---

## Connecting to WhatsApp

1. **Scan the QR Code**
   - Open WhatsApp on your phone
   - Go to: Settings → Linked Devices
   - Tap "Link a Device"
   - Scan the QR code from your terminal

2. **Wait for Connection**
   ```
   ✅ WhatsApp Connected!
   ```

3. **Test It!**
   - Send a message to your WhatsApp number
   - Example: "P0420 Toyota Camry 2015"
   - You should get an OBD diagnosis response!

---

## File Structure

```
VehicleDiagnosisAssistant/
├── app/                          # Your FastAPI backend
│   └── ...
├── baileys-server/               # NEW: WhatsApp connector
│   ├── package.json
│   ├── index.js
│   └── auth_info_baileys/        # Generated after QR scan
│       └── creds.json
└── ...
```

---

## Security Setup (Recommended)

### 1. Add API Key to .env

```bash
# In your .env file
BAILEYS_API_KEY=your-super-secret-key-12345
```

### 2. Update Baileys index.js

```javascript
// Add this at the top
const API_KEY = 'your-super-secret-key-12345'

// In axios.post, add header:
headers: {
    'Content-Type': 'application/json',
    'X-API-Key': API_KEY
}
```

### 3. Verify in Backend

Your FastAPI backend already checks this in `app/api/routes/webhook.py`:

```python
# Line 294-299 - Already implemented!
if settings.baileys_api_key:
    auth_header = request.headers.get("X-API-Key", "")
    if auth_header != settings.baileys_api_key:
        return Response(status_code=401)
```

---

## Testing the Integration

### Test 1: Simple OBD Code

Send to your WhatsApp:
```
P0420
```

Expected response:
```
*Fault code:* P0420
*System:* local_db

*What it means:*
Catalyst system efficiency below threshold (Bank 1)

*Likely causes:*
• Catalytic converter degraded
• Oxygen sensor issue
• Exhaust leak

*Recommended action:*
1. Check for exhaust leaks
2. Evaluate upstream/downstream O2 sensors
3. Assess catalytic converter

_Always confirm with live scanner data before replacing parts._
_Confidence: High_
```

### Test 2: With Vehicle Info

Send:
```
P0420 Toyota Camry 2015
```

Response will include vehicle-specific analysis!

### Test 3: Symptom-Based

Send:
```
Car shaking and rough idle
```

Response will suggest probable codes and checks.

---

## Troubleshooting

### QR Code Not Showing

```bash
# Make sure you're in baileys-server directory
cd baileys-server
npm install
npm start
```

### "Cannot find module '@whiskeysockets/baileys'"

```bash
npm install @whiskeysockets/baileys
```

### Connection Closes Immediately

- Check your internet connection
- Make sure WhatsApp Web is not open elsewhere
- Delete `auth_info_baileys` folder and scan QR again

### Backend Not Responding

Check FastAPI is running:
```powershell
curl http://localhost:8000/healthz
```

Should return:
```json
{"status":"ok","version":"2.0.0"}
```

### Messages Not Forwarding

Check Baileys logs:
```
📩 Message from 1234567890@s.whatsapp.net: P0420
✅ Sent reply: *Fault code:* P0420...
```

If you see errors, check:
1. BACKEND_URL is correct (`http://localhost:8000/webhook/baileys`)
2. FastAPI server is running
3. No firewall blocking requests

---

## Advanced: Deploy to Production

### Option 1: Local Server

Keep both running on your computer:
```bash
# Terminal 1
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Terminal 2
cd baileys-server && npm start
```

### Option 2: VPS/Cloud Server

1. Deploy FastAPI to Railway/Render/AWS
2. Deploy Baileys to same server
3. Update BACKEND_URL to your production domain
4. Use PM2 to keep Baileys running:

```bash
npm install -g pm2
pm2 start index.js --name baileys-whatsapp
pm2 save
pm2 startup
```

### Option 3: Docker (Both Together)

Create `docker-compose.yml`:

```yaml
version: '3.8'
services:
  fastapi:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env

  baileys:
    image: node:18
    working_dir: /app
    volumes:
      - ./baileys-server:/app
    command: npm start
    ports:
      - "3000:3000"
    depends_on:
      - fastapi
```

---

## Multiple WhatsApp Numbers

To connect multiple WhatsApp accounts:

1. Create separate folders:
   ```
   baileys-server-1/
   baileys-server-2/
   ```

2. Use different ports:
   ```javascript
   // baileys-server-1: port 3001
   // baileys-server-2: port 3002
   ```

3. Each gets its own QR code and auth

---

## Monitoring & Logs

### View Baileys Logs

```bash
# In baileys-server terminal
# You'll see:
📩 Message from ...
✅ Sent reply: ...
❌ Error: ...
```

### View FastAPI Logs

```bash
# In FastAPI terminal
# You'll see JSON logs:
{"event": "baileys_webhook_received", ...}
{"event": "message_parsed", ...}
{"event": "obd_lookup_success", ...}
```

---

## Cost Comparison

| Method | Setup | Cost | Scalability |
|--------|-------|------|-------------|
| **Baileys** | Medium | Free | Good |
| **Twilio** | Easy | $0.005/msg | Excellent |
| **Official API** | Easy | $0.005/msg | Excellent |

**Baileys is perfect for:**
- Personal/small business use
- Testing and development
- Low-medium volume (<1000 msgs/day)

**Use Twilio/Official API for:**
- High volume (>1000 msgs/day)
- Enterprise clients
- Mission-critical applications
- Need official support

---

## Summary

✅ **Step 1**: Install Node.js and create baileys-server  
✅ **Step 2**: Run `npm start` and scan QR code  
✅ **Step 3**: Test by sending messages to your WhatsApp  

**That's it!** Your Vehicle Diagnosis Assistant is now connected to WhatsApp! 🎉

---

## Need Help?

- **Baileys Docs**: https://github.com/WhiskeySockets/Baileys
- **Issues**: Check baileys-server terminal for errors
- **Backend Issues**: Check FastAPI logs (JSON format)

---

**Ready to connect? Run the baileys-server and scan the QR code!** 📱
