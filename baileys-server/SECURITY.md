# Security Policy

## 🔒 Security Features

This server implements multiple layers of security to protect against common web vulnerabilities:

### Authentication & Authorization
- **API Key Authentication**: All protected endpoints require X-API-Key header
- **Strong Key Requirements**: Minimum 32 characters, rejects weak defaults
- **Constant-Time Comparison**: Prevents timing attacks (Node.js built-in)

### Input Validation
- **Express Validator**: Sanitizes and validates all inputs
- **Phone Number Validation**: Regex pattern matching + sanitization
- **Message Length Limits**: 4096 characters max
- **Request Size Limits**: 100KB max payload

### Rate Limiting
- **Per-IP Limiting**: Configurable requests per time window
- **Endpoint-Specific**: Critical endpoints have stricter limits
- **Headers**: Returns RateLimit-* headers per RFC draft

### Security Headers (Helmet.js)
```
Content-Security-Policy: default-src 'self'
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 0
```

### SSRF Protection
- **URL Validation**: Verifies BACKEND_URL uses http/https
- **Internal IP Warnings**: Alerts on localhost/private IPs in production
- **No User-Controlled URLs**: Backend URL is environment-only

### Error Handling
- **Sanitized Errors**: Stack traces never exposed to clients
- **Structured Logging**: All errors logged with context
- **Graceful Degradation**: Sends generic error messages to users

### Logging & Monitoring
- **Structured Logs**: JSON format with request IDs
- **Audit Trail**: All authentication failures logged
- **Metrics Endpoint**: Track success rates and errors
- **No Sensitive Data**: API keys never logged

## 🔍 Security Best Practices

### API Key Management

**Generate Strong Keys:**
```bash
# Linux/Mac
openssl rand -hex 32

# Node.js
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"

# Python
python3 -c "import secrets; print(secrets.token_hex(32))"
```

**Store Securely:**
- Use environment variables (never hardcode)
- Set file permissions: `chmod 600 .env`
- Use secrets management in production (AWS Secrets Manager, Vault)
- Rotate keys regularly (every 90 days)

**Never:**
- Commit `.env` files to version control
- Log API keys
- Send keys in URLs or query parameters
- Use weak defaults

### Environment Configuration

**Production Checklist:**
```bash
# Set production mode
NODE_ENV=production

# Generate strong key
BAILEYS_API_KEY=$(openssl rand -hex 32)

# Use HTTPS backend
BACKEND_URL=https://api.yourdomain.com/webhook/baileys

# Restrict CORS
ALLOWED_ORIGINS=https://yourdomain.com

# Enable strict logging
LOG_LEVEL=warn
```

### Network Security

**Firewall Rules:**
```bash
# Allow only necessary traffic
ufw allow 3000/tcp
ufw enable

# Or restrict to specific IPs
ufw allow from 192.168.1.0/24 to any port 3000
```

**Reverse Proxy (Recommended):**
- Use nginx/Caddy/Traefik for TLS termination
- Enable HTTP/2
- Add additional rate limiting
- Hide server implementation details

**TLS Configuration:**
```nginx
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers HIGH:!aNULL:!MD5;
ssl_prefer_server_ciphers on;
```

### Dependency Security

**Regular Audits:**
```bash
# Check for vulnerabilities
npm audit

# Fix automatically (review changes!)
npm audit fix

# Update dependencies
npm update

# Check for outdated packages
npm outdated
```

**Lock File:**
- Commit `package-lock.json`
- Use exact versions in production
- Review dependency changes before updating

### Process Management

**Run as Non-Root:**
```bash
# Create dedicated user
useradd -r -s /bin/false baileys

# Set ownership
chown -R baileys:baileys /path/to/baileys-server

# Run as user
su -s /bin/bash baileys -c "npm start"
```

**Resource Limits:**
```bash
# Limit memory
node --max-old-space-size=512 index.js

# Or use systemd
[Service]
MemoryLimit=512M
CPUQuota=50%
```

## 🚨 Vulnerability Reporting

### Scope
- Authentication bypass
- Injection vulnerabilities (SQL, Command, XSS)
- SSRF attacks
- DoS vulnerabilities
- Information disclosure
- Authorization issues

### Out of Scope
- Social engineering
- Physical attacks
- Issues in dependencies (report to upstream)
- Theoretical issues without PoC

### Reporting Process

**DO NOT** create public GitHub issues for security vulnerabilities.

**Instead:**
1. Email security details to the project maintainer
2. Include:
   - Description of vulnerability
   - Steps to reproduce
   - Proof of concept (if applicable)
   - Suggested fix (if known)
3. Allow 90 days for fix before public disclosure

## 🛡️ Security Checklist

### Deployment
- [ ] `NODE_ENV=production` set
- [ ] Strong API key generated (≥32 chars)
- [ ] `.env` file permissions set to 600
- [ ] TLS/SSL enabled via reverse proxy
- [ ] Firewall configured
- [ ] Running as non-root user
- [ ] Process manager configured (PM2/systemd)
- [ ] Log rotation enabled
- [ ] Monitoring and alerting set up
- [ ] Backups configured
- [ ] Dependencies audited
- [ ] CORS origins restricted
- [ ] Rate limits reviewed and tested

### Runtime
- [ ] Monitor `/health` endpoint
- [ ] Review `/metrics` for anomalies
- [ ] Check logs for authentication failures
- [ ] Monitor error rates
- [ ] Track connection stability
- [ ] Review resource usage

### Maintenance
- [ ] Rotate API keys every 90 days
- [ ] Update dependencies monthly
- [ ] Run `npm audit` weekly
- [ ] Review logs for suspicious activity
- [ ] Test disaster recovery procedures
- [ ] Update security policies

## 📋 Compliance

### Data Protection
- **No PII Storage**: WhatsApp numbers are not persisted
- **Session Data**: Stored in `auth_info_baileys/` (encrypt in production)
- **Logs**: May contain phone numbers (sanitize if required by GDPR/CCPA)

### Recommendations:
- Encrypt `auth_info_baileys/` directory
- Implement log sanitization for PII
- Add data retention policies
- Document data flows
- Obtain user consent for message processing

## 🔄 Security Updates

**v2.0.0 (2026-07-02)**
- ✅ Added API key authentication
- ✅ Implemented rate limiting
- ✅ Added input validation
- ✅ Configured security headers
- ✅ Implemented SSRF protection
- ✅ Sanitized error messages
- ✅ Added structured logging
- ✅ Implemented graceful shutdown
- ✅ Added metrics endpoint

## 📚 References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP API Security](https://owasp.org/www-project-api-security/)
- [Node.js Security Best Practices](https://nodejs.org/en/docs/guides/security/)
- [Express Security Best Practices](https://expressjs.com/en/advanced/best-practice-security.html)
- [Helmet.js Documentation](https://helmetjs.github.io/)

---

**Last Updated:** 2026-07-02  
**Security Contact:** See project maintainer
