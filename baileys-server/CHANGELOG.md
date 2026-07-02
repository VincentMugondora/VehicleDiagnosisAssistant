# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-07-02

### 🔒 Security

#### Added
- **API Key Authentication**: X-API-Key header validation on protected endpoints
- **Rate Limiting**: 20 requests/minute per IP (configurable via env)
- **Input Validation**: Express-validator for all user inputs
  - Phone number format validation and sanitization
  - Message length limits (4096 chars)
  - Request body validation
- **CORS Configuration**: Configurable origin allowlist
- **Security Headers**: Helmet.js integration
  - Content-Security-Policy
  - Strict-Transport-Security (HSTS)
  - X-Content-Type-Options
  - X-Frame-Options
  - X-XSS-Protection
- **Request Size Limits**: 100KB max payload
- **SSRF Protection**: URL validation and internal IP warnings
- **Environment Validation**: Startup checks for required variables
  - Minimum API key length enforcement (32 chars)
  - Weak default detection
  - URL format validation
- **Error Sanitization**: Stack traces hidden from clients
- **Global Error Handlers**: Uncaught exceptions and unhandled rejections

#### Changed
- Removed weak default API key (`'your-secret-key-here'`)
- All errors now return generic messages to clients (detailed logs internally)
- Backend URL validation prevents SSRF attacks

### 🚀 Features

#### Added
- **Structured Logging**: Pino logger with JSON output
  - Request ID tracking across all operations
  - Log levels: trace, debug, info, warn, error, fatal
  - Pretty printing in development mode
  - No sensitive data logging
- **Metrics Endpoint**: `/metrics` with detailed statistics
  - Uptime tracking
  - Message counters (received/sent)
  - Error tracking
  - Success rate calculation
  - Last message timestamp
  - Reconnection attempts
- **Enhanced Health Checks**: `/health` endpoint improvements
  - Connection status
  - Uptime reporting
  - ISO timestamp
  - Proper HTTP status codes (503 when unhealthy)
- **Request ID Tracking**: UUID for each request/message
  - Correlation across services
  - Included in response headers
  - Logged with all operations
- **Environment File Support**: dotenv integration
- **Graceful Shutdown**: Proper cleanup on SIGINT/SIGTERM
  - Closes HTTP server
  - Logs out of WhatsApp
  - 10-second force-exit timeout
  - Waits for pending operations

### 🔧 Improvements

#### Changed
- **Exponential Backoff**: Smart reconnection delays
  - Delays: 3s, 6s, 12s, 30s, 60s (max)
  - Resets on successful connection
  - Prevents connection storms
- **Improved Message Splitting**: Better algorithm
  - Respects paragraph boundaries
  - Preserves word integrity
  - Better handling of edge cases
  - Markdown-aware splitting
- **Better Error Messages**: User-friendly error responses
- **Enhanced Logging**: All operations tracked with context
- **Configurable Timeouts**: Backend request timeout via env (default 60s)
- **Connection Configuration**: Better Baileys socket options
  - Increased timeouts for reliability
  - Keep-alive settings
  - Silent Baileys logger (uses Pino instead)
- **Startup Banner**: Clear visual server information

### 📦 Dependencies

#### Added
- `dotenv@16.4.5` - Environment variable management
- `helmet@8.0.0` - Security headers middleware
- `express-rate-limit@7.4.1` - Rate limiting
- `express-validator@7.2.0` - Input validation
- `pino@9.5.0` - Structured logging
- `pino-pretty@11.2.2` - Log formatting for development
- `uuid@11.0.3` - Request ID generation

#### Updated
- `axios@1.7.7` (from 1.6.0) - Security updates
- `express@4.21.1` (from 4.18.2) - Security updates
- `nodemon@3.1.7` (from 3.0.1) - Development improvements

#### Security Fixes
- Fixed 2 vulnerabilities via `npm audit fix`
- All dependencies now vulnerability-free

### 📚 Documentation

#### Added
- `.env.example` - Environment template with all variables
- `SECURITY.md` - Comprehensive security documentation
  - Security features overview
  - Best practices guide
  - Vulnerability reporting policy
  - Deployment checklist
  - Compliance notes
- `CHANGELOG.md` - This file
- Enhanced `README.md`:
  - Security features section
  - API documentation
  - Monitoring guide
  - Troubleshooting expanded
  - Deployment guide
  - Production checklist
  - Example nginx configuration
  - PM2 setup guide
- Enhanced `.gitignore`:
  - Additional patterns
  - Better organization
  - IDE/OS files
  - Process manager configs
- `test-security.sh` - Automated security testing script

### 🗑️ Removed
- Weak default API key value
- Console.log statements (replaced with structured logging)
- Exposed error details in API responses

### 🔄 Breaking Changes

⚠️ **Version 2.0 includes breaking changes:**

1. **Required Environment Variables**:
   - `BAILEYS_API_KEY` is now mandatory (no default)
   - Must be ≥32 characters
   - Weak values rejected at startup

2. **Authentication Required**:
   - `/send` endpoint now requires X-API-Key header
   - `/metrics` endpoint now requires X-API-Key header
   - Unauthenticated requests return 401/403

3. **Input Validation**:
   - `/send` endpoint validates phone numbers
   - Invalid inputs return 400 with validation details
   - Message length limited to 4096 characters

4. **Environment File**:
   - `.env` file now recommended (not required)
   - All config should move from hardcoded to env vars

5. **Log Format**:
   - JSON structured logs (configurable with LOG_LEVEL)
   - Use pino-pretty for human-readable output

### Migration Guide

**From v1.x to v2.0:**

1. **Create `.env` file**:
   ```bash
   cp .env.example .env
   ```

2. **Generate strong API key**:
   ```bash
   openssl rand -hex 32
   ```

3. **Configure environment**:
   - Set `BAILEYS_API_KEY` in `.env`
   - Set `BACKEND_URL` in `.env`
   - Review optional variables

4. **Update API clients**:
   - Add `X-API-Key` header to all `/send` requests
   - Add `X-API-Key` header to `/metrics` requests
   - Handle 401/403 authentication errors
   - Handle 400 validation errors

5. **Install new dependencies**:
   ```bash
   npm install
   ```

6. **Test thoroughly**:
   ```bash
   npm start
   # In another terminal:
   ./test-security.sh
   ```

7. **Update monitoring**:
   - Switch to `/health` for health checks
   - Use `/metrics` endpoint (with auth)
   - Update log parsing for JSON format

### 🐛 Bug Fixes

- Fixed potential race condition in reconnection logic
- Fixed message splitting edge cases (empty strings, very long words)
- Fixed health check not reflecting actual WhatsApp connection state
- Fixed memory leak in error handling (proper cleanup)
- Fixed unhandled promise rejections in message sending

### ⚡ Performance

- Reduced log overhead with appropriate log levels
- Optimized message splitting algorithm
- Better connection timeout handling
- Reduced unnecessary reconnection attempts

---

## [1.0.0] - 2025-05-30

### Initial Release

#### Features
- Basic WhatsApp integration using Baileys
- QR code authentication
- Incoming message handling
- Backend webhook integration
- `/send` endpoint for manual messages
- `/health` endpoint
- Express.js server
- Automatic reconnection (fixed delay)
- Message splitting for long texts
- Group/broadcast filtering

#### Dependencies
- @whiskeysockets/baileys@7.0.0-rc13
- axios@1.6.0
- express@4.18.2
- qrcode-terminal@0.12.0
- nodemon@3.0.1 (dev)

---

## Future Roadmap

### Planned for v2.1.0
- [ ] WebSocket support for real-time updates
- [ ] Message queue for high-volume scenarios
- [ ] Redis session storage option
- [ ] Prometheus metrics exporter
- [ ] Docker containerization
- [ ] Kubernetes manifests
- [ ] Additional MFA options

### Under Consideration
- [ ] Multi-device support
- [ ] Message templates
- [ ] Scheduled messages
- [ ] Media handling improvements
- [ ] Webhook signature verification
- [ ] GraphQL API option
- [ ] Admin dashboard
- [ ] Message archiving
- [ ] Analytics and reporting

---

**Legend:**
- 🔒 Security
- 🚀 Features  
- 🔧 Improvements
- 📦 Dependencies
- 📚 Documentation
- 🗑️ Removed
- 🔄 Breaking Changes
- 🐛 Bug Fixes
- ⚡ Performance
