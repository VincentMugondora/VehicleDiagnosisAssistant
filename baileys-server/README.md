# Baileys WhatsApp Server

WhatsApp integration for Vehicle Diagnosis Assistant using Baileys.

## Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Start Server

```bash
npm start
```

### 3. Scan QR Code

- Open WhatsApp on your phone
- Go to Settings → Linked Devices
- Tap "Link a Device"
- Scan the QR code shown in terminal

### 4. Test It!

Send a message to your WhatsApp number:
```
P0420 Toyota Camry 2015
```

You should receive an OBD diagnosis!

## Configuration

Create `.env` file (optional):

```bash
BACKEND_URL=http://localhost:8000/webhook/baileys
BAILEYS_API_KEY=your-secret-key
PORT=3000
```

## Commands

```bash
npm start       # Start server
npm run dev     # Start with auto-reload (development)
```

## Troubleshooting

### QR Code Not Showing
- Make sure you're in the baileys-server directory
- Run `npm install` first

### Connection Issues
- Delete `auth_info_baileys` folder and scan QR again
- Check internet connection
- Make sure WhatsApp Web is not open elsewhere

### Backend Not Responding
- Verify FastAPI is running: `curl http://localhost:8000/healthz`
- Check BACKEND_URL is correct

## File Structure

```
baileys-server/
├── index.js              # Main server code
├── package.json          # Dependencies
├── auth_info_baileys/    # Generated after QR scan (don't commit!)
│   └── creds.json
└── README.md             # This file
```

## See Also

- Full setup guide: `../BAILEYS_SETUP_GUIDE.md`
- Baileys documentation: https://github.com/WhiskeySockets/Baileys
