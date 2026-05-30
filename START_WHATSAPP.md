# 🚀 Start WhatsApp Integration

Quick guide to get your WhatsApp bot running in 2 minutes!

---

## Prerequisites

✅ FastAPI server running  
✅ Node.js installed (check: `node --version`)  

---

## Steps

### 1. Open Two Terminals

**Terminal 1 (PowerShell)** - FastAPI Backend:
```powershell
cd C:\Users\vinmu\Desktop\VehicleDiagnosisAssistant
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

Keep this running! You should see:
```
{"event": "app_starting", ...}
{"event": "supabase_connected", ...}
```

---

**Terminal 2 (PowerShell or CMD)** - Baileys WhatsApp:
```powershell
cd C:\Users\vinmu\Desktop\VehicleDiagnosisAssistant\baileys-server
npm install
npm start
```

---

### 2. Scan QR Code

You'll see a QR code in Terminal 2:

```
🔄 Connecting to WhatsApp...
📱 Scan this QR code with WhatsApp:

█████████████████████████████
█████████████████████████████
███████░░░░░░░░░░░░░░░░░█████
███████░░░░░░░░░░░░░░░░░█████
█████████████████████████████
```

**On your phone:**
1. Open WhatsApp
2. Tap ⋮ (menu) → Linked Devices
3. Tap "Link a Device"
4. Scan the QR code

---

### 3. Wait for Connection

Terminal 2 will show:
```
✅ WhatsApp Connected!
📱 Ready to receive messages
```

---

### 4. Test It!

Send a message to **your own WhatsApp number**:

```
P0420
```

You should receive:
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
```

---

## What You'll See

### Terminal 1 (FastAPI) Logs:
```json
{"event": "baileys_webhook_received", "phone_hash": "...", ...}
{"event": "message_parsed", "code": "P0420", ...}
{"event": "obd_lookup_success", "code": "P0420", ...}
```

### Terminal 2 (Baileys) Logs:
```
📩 Message from 1234567890@s.whatsapp.net
   Text: P0420
✅ Sent reply (1 message)
```

---

## Test Examples

### Simple Code:
```
P0420
```

### With Vehicle Info:
```
P0420 Toyota Camry 2015
```

### Symptom-Based:
```
Car shaking and rough idle
```

### Multiple Codes:
```
P0300 P0301 Honda Civic 2018
```

---

## Troubleshooting

### "Cannot find module @whiskeysockets/baileys"
```bash
cd baileys-server
npm install
```

### QR Code Not Showing
- Make sure you're in `baileys-server` directory
- Check Node.js is installed: `node --version`

### Connection Closes Immediately
- Check internet connection
- Close WhatsApp Web if open
- Delete `auth_info_baileys` folder and try again

### Backend Not Responding
Check Terminal 1 - FastAPI should be running:
```powershell
# Test in new terminal:
curl http://localhost:8000/healthz
```

Should return:
```json
{"status":"ok","version":"2.0.0"}
```

---

## Stopping the Servers

**Terminal 1 (FastAPI):**
```
Ctrl + C
```

**Terminal 2 (Baileys):**
```
Ctrl + C
```

Baileys will logout gracefully:
```
👋 Shutting down gracefully...
```

---

## Next Time

After first setup, just run:

**Terminal 1:**
```powershell
cd C:\Users\vinmu\Desktop\VehicleDiagnosisAssistant
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

**Terminal 2:**
```powershell
cd C:\Users\vinmu\Desktop\VehicleDiagnosisAssistant\baileys-server
npm start
```

No QR code needed - it remembers your session!

---

## Production Tips

### Keep Running 24/7

Use PM2 (Node.js process manager):

```bash
# Install PM2
npm install -g pm2

# Start Baileys with PM2
cd baileys-server
pm2 start index.js --name whatsapp-bot

# View logs
pm2 logs whatsapp-bot

# Stop
pm2 stop whatsapp-bot

# Restart
pm2 restart whatsapp-bot
```

### Auto-restart on System Boot

```bash
pm2 startup
pm2 save
```

---

## Security

### Add API Key (Recommended)

**1. Update .env:**
```bash
BAILEYS_API_KEY=your-super-secret-key-12345
```

**2. Update baileys-server/index.js:**

Change line 9:
```javascript
const API_KEY = process.env.BAILEYS_API_KEY || 'your-super-secret-key-12345'
```

Restart both servers!

---

## Summary

✅ **Terminal 1**: FastAPI backend (port 8000)  
✅ **Terminal 2**: Baileys WhatsApp (port 3000)  
✅ **Scan QR**: Link your WhatsApp  
✅ **Test**: Send "P0420" to yourself  

**That's it! Your WhatsApp bot is live!** 🎉

---

## Full Documentation

- Setup guide: `BAILEYS_SETUP_GUIDE.md`
- Baileys code: `baileys-server/`
- Backend code: `app/`

---

**Ready? Open two terminals and let's go!** 🚀
