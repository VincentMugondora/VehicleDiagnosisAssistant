# Baileys WhatsApp Server v2.0

🔒 **Secure** WhatsApp integration for Vehicle Diagnosis Assistant using Baileys with enterprise-grade security.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Environment

```bash
# Copy the example configuration
cp .env.example .env

# Edit .env and set your configuration
nano .env  # or use your preferred editor
```

**⚠️ IMPORTANT:** Generate a strong API key:
```bash
# On Linux/Mac:
openssl rand -hex 32

# Or use Node.js:
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

Set this value in `.env` as `BAILEYS_API_KEY`.

### 3. Start Server

```bash
npm start       # Production
npm run dev     # Development with auto-reload
```

### 4. Scan QR Code

- Open WhatsApp on your phone
- Go to Settings → Linked Devices
- Tap "Link a Device"
- Scan the QR code shown in terminal

### 5. Test It!

Send a message to your WhatsApp number:
```
P0420 Toyota Camry 2015
```

You should receive an OBD diagnosis!

## 🔧 Configuration

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `BACKEND_URL` | FastAPI backend webhook URL | `http://localhost:8000/webhook/baileys` |
| `BAILEYS_API_KEY` | Strong API key (min 32 chars) | Generated using `openssl rand -hex 32` |

### Optional Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `3000` | Server port |
| `REQUEST_TIMEOUT` | `60000` | Backend request timeout (ms) |
| `RATE_LIMIT_MAX` | `20` | Max requests per window |
| `RATE_LIMIT_WINDOW_MS` | `60000` | Rate limit window (ms) |
| `LOG_LEVEL` | `info` | Logging level (trace, debug, info, warn, error, fatal) |
| `NODE_ENV` | `production` | Environment mode |
| `ALLOWED_ORIGINS` | None | CORS allowed origins (comma-separated) |

## 🔒 Security Features

### ✅ Implemented Security

- **Authentication**: X-API-Key header validation on all protected endpoints
- **Rate Limiting**: 20 requests/minute per IP (configurable)
- **Input Validation**: Phone numbers and message content sanitized
- **CORS**: Configurable origin allowlist
- **Security Headers**: Helmet.js with CSP, HSTS, X-Frame-Options
- **Request Size Limits**: 100KB max payload
- **SSRF Protection**: URL validation and internal IP warnings
- **Error Sanitization**: Stack traces hidden from clients
- **Structured Logging**: Pino with request IDs for audit trails
- **Graceful Shutdown**: Proper cleanup on termination signals

### 🔐 Best Practices

1. **Strong API Keys**: Use cryptographically random keys (≥32 chars)
2. **Environment Files**: Never commit `.env` files
3. **File Permissions**: Set `.env` to 600 (`chmod 600 .env`)
4. **HTTPS Only**: Use reverse proxy (nginx/Caddy) for TLS
5. **Firewall**: Restrict access to port 3000
6. **Monitoring**: Check `/health` and `/metrics` endpoints regularly
7. **Updates**: Keep dependencies updated (`npm audit`)

## 📡 API Endpoints

### `POST /send` (Protected)

Send a WhatsApp message.

**Headers:**
- `X-API-Key`: Your API key
- `Content-Type`: application/json

**Body:**
```json
{
  "to": "1234567890",
  "message": "Your message here"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Message sent",
  "request_id": "uuid-here"
}
```

### `GET /health`

Health check endpoint (public).

**Response:**
```json
{
  "status": "healthy",
  "connection": "connected",
  "uptime": 3600,
  "timestamp": "2026-07-02T12:00:00.000Z"
}
```

### `GET /metrics` (Protected)

Detailed metrics (requires X-API-Key).

**Response:**
```json
{
  "uptime_seconds": 3600,
  "connection_status": "connected",
  "reconnect_attempts": 0,
  "messages_received": 150,
  "messages_sent": 150,
  "errors": 2,
  "last_message_time": "2026-07-02T12:00:00.000Z",
  "success_rate": "98.67%"
}
```

## 🔍 Monitoring

### Health Checks

```bash
# Basic health
curl http://localhost:3000/health

# Detailed metrics (requires auth)
curl -H "X-API-Key: your-key" http://localhost:3000/metrics
```

### Logs

Logs are output in structured JSON format (or pretty-printed in development):

```bash
# View logs
npm start

# Filter by level
npm start 2>&1 | grep '"level":"error"'

# Follow logs
npm start 2>&1 | tee server.log
```

## 🐛 Troubleshooting

### Environment Validation Errors

**Error:** `Missing required environment variables`
- **Solution:** Copy `.env.example` to `.env` and configure all required variables

**Error:** `Weak environment variable values`
- **Solution:** Generate a strong API key with `openssl rand -hex 32`

### Connection Issues

**QR Code Not Showing**
- Ensure you're in the `baileys-server` directory
- Run `npm install` first
- Check console for errors

**Connection Keeps Dropping**
- Delete `auth_info_baileys` folder and re-scan QR
- Check internet connection stability
- Ensure WhatsApp Web is not open elsewhere
- Review logs for disconnect reasons

**Exponential Backoff**
- Server automatically retries with delays: 3s, 6s, 12s, 30s, 60s
- Resets on successful connection

### API Errors

**401 Unauthorized**
- Missing `X-API-Key` header
- **Solution:** Include header in request

**403 Forbidden**
- Invalid API key
- **Solution:** Verify `BAILEYS_API_KEY` in `.env` matches request header

**429 Too Many Requests**
- Rate limit exceeded
- **Solution:** Wait or increase `RATE_LIMIT_MAX` in config

**503 Service Unavailable**
- WhatsApp not connected
- **Solution:** Check connection status at `/health`

### Backend Issues

**Backend Not Responding**
```bash
# Verify FastAPI is running
curl http://localhost:8000/healthz

# Check BACKEND_URL in .env
echo $BACKEND_URL

# Test with verbose output
curl -v -X POST http://localhost:8000/webhook/baileys \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{"from":"test","text":"hello"}'
```

## 📁 File Structure

```
baileys-server/
├── index.js              # Main server code (v2.0 - fully refactored)
├── package.json          # Dependencies
├── .env.example          # Environment template
├── .env                  # Your configuration (DO NOT COMMIT!)
├── .gitignore            # Git ignore rules
├── auth_info_baileys/    # WhatsApp session (generated, do not commit!)
│   └── creds.json
└── README.md             # This file
```

## 🚢 Deployment

### Production Checklist

- [ ] Set `NODE_ENV=production`
- [ ] Generate strong API key (≥32 chars)
- [ ] Configure firewall rules
- [ ] Set up reverse proxy with TLS (nginx/Caddy)
- [ ] Configure process manager (PM2/systemd)
- [ ] Set up monitoring and alerting
- [ ] Configure log rotation
- [ ] Review and restrict CORS origins
- [ ] Test rate limiting
- [ ] Backup `auth_info_baileys` folder

### Example with PM2

```bash
# Install PM2
npm install -g pm2

# Start server
pm2 start index.js --name baileys-server

# View logs
pm2 logs baileys-server

# Restart
pm2 restart baileys-server

# Auto-start on boot
pm2 startup
pm2 save
```

### Example Nginx Config

```nginx
server {
    listen 443 ssl http2;
    server_name whatsapp.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_cache_bypass $http_upgrade;
    }
}
```

## 📚 See Also

- [Full Setup Guide](../BAILEYS_SETUP_GUIDE.md)
- [Baileys Documentation](https://github.com/WhiskeySockets/Baileys)
- [Security Best Practices](https://owasp.org/www-project-top-ten/)

## 🆘 Support

For issues or questions:
1. Check logs: `npm start`
2. Verify environment: `cat .env`
3. Test health: `curl http://localhost:3000/health`
4. Review this README

## 📄 License

MIT

---

**Version:** 2.0.0  
**Last Updated:** 2026-07-02  
**Security Level:** Enterprise-Grade ✅
