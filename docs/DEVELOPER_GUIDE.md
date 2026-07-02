# Developer Guide - Vehicle Diagnosis Assistant

**Version:** 2.0  
**Last Updated:** 2026-07-02

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Development Setup](#development-setup)
3. [Testing](#testing)
4. [Debugging](#debugging)
5. [Adding Features](#adding-features)
6. [Common Tasks](#common-tasks)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

---

## Getting Started

### Prerequisites

- **Python 3.12+**
- **Node.js 18+**
- **Git**
- **Supabase account** (free tier works)
- **Cohere or Gemini API key**

### Quick Setup (5 minutes)

```bash
# 1. Clone repository
git clone <repo-url>
cd VehicleDiagnosisAssistant

# 2. Backend setup
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your keys

# 4. Load OBD codes
python scripts/load_obd_codes.py

# 5. Start backend
uvicorn app.main:app --reload --port 8001

# 6. Baileys setup (new terminal)
cd baileys-server
npm install
cp .env.example .env
# Edit .env

npm start
```

---

## Development Setup

### Project Structure

```
VehicleDiagnosisAssistant/
├── app/                           # FastAPI backend
│   ├── api/
│   │   └── routes/
│   │       └── webhook.py         # Main webhook endpoint
│   ├── core/
│   │   ├── config.py              # Settings & environment
│   │   ├── errors.py              # Custom exceptions
│   │   └── logging.py             # Structured logging
│   ├── db/
│   │   └── client.py              # Supabase client
│   ├── models/
│   │   ├── diagnostic.py          # Pydantic models
│   │   └── session.py             # Session state
│   ├── repositories/
│   │   ├── obd_repository.py      # Database queries
│   │   └── session_repository.py
│   ├── services/
│   │   ├── message_router.py      # ⭐ Core routing logic
│   │   ├── obd_service.py         # ⭐ OBD diagnosis
│   │   ├── session_manager.py     # Session management
│   │   ├── ai_client.py           # AI integration
│   │   └── parser.py              # Message parsing
│   ├── utils/
│   │   └── obd_parser.py          # Regex extraction
│   └── main.py                    # FastAPI app
│
├── baileys-server/                # WhatsApp bridge
│   ├── index.js                   # ⭐ Main server
│   ├── package.json
│   └── .env
│
├── data/
│   └── obd_codes_dataset.json     # 250+ OBD codes
│
├── scripts/
│   └── load_obd_codes.py          # Database loader
│
├── tests/
│   └── test_system_e2e.py         # End-to-end tests
│
└── docs/
    ├── ARCHITECTURE.md
    └── DEVELOPER_GUIDE.md         # This file
```

### Development Workflow

```bash
# Terminal 1: Backend with auto-reload
cd VehicleDiagnosisAssistant
venv\Scripts\activate
uvicorn app.main:app --reload --port 8001

# Terminal 2: Baileys with auto-reload
cd baileys-server
npm run dev

# Terminal 3: Testing
python test_system_e2e.py
```

---

## Testing

### End-to-End Tests

```bash
# Run full test suite
python test_system_e2e.py

# Expected output:
# ✅ Configuration check
# ✅ Code validation  
# ✅ Message parsing
# ✅ Database connection
# ⚠️  Backend health (requires running backend)
# ⚠️  Webhook integration (requires running backend)
```

### Unit Tests (Create These)

```python
# tests/test_parser.py
import pytest
from app.utils.obd_parser import parse_message

def test_parse_simple_code():
    result = parse_message("P0420")
    assert result["code"] == "P0420"
    assert result["make"] is None

def test_parse_with_vehicle():
    result = parse_message("P0420 Toyota Camry 2015")
    assert result["code"] == "P0420"
    assert result["make"] == "Toyota"
    assert result["model"] == "Camry"
    assert result["year"] == "2015"
```

### Manual Testing

**Test 1: Simple Code**
```bash
curl -X POST http://localhost:8001/webhook/baileys \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key-here" \
  -d '{
    "from": "test@s.whatsapp.net",
    "text": "P0420",
    "message_id": "test1"
  }'
```

**Test 2: Code with Vehicle**
```bash
curl -X POST http://localhost:8001/webhook/baileys \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key-here" \
  -d '{
    "from": "test@s.whatsapp.net",
    "text": "P0420 Toyota Camry 2015",
    "message_id": "test2"
  }'
```

**Test 3: Followup Question**
```bash
# First, send a code diagnosis
curl -X POST http://localhost:8001/webhook/baileys \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key-here" \
  -d '{
    "from": "test@s.whatsapp.net",
    "text": "P0420",
    "message_id": "test3a"
  }'

# Then, send a followup
curl -X POST http://localhost:8001/webhook/baileys \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key-here" \
  -d '{
    "from": "test@s.whatsapp.net",
    "text": "is this expensive to fix?",
    "message_id": "test3b"
  }'
```

---

## Debugging

### Backend Debugging

**Enable Debug Logs:**
```bash
# In .env
LOG_LEVEL=debug

# Restart backend
uvicorn app.main:app --reload --port 8001
```

**Check Logs:**
```json
{
  "event": "message_parsed",
  "code": "P0420",
  "vehicle_detected": true,
  "level": "info"
}

{
  "event": "obd_lookup_success",
  "code": "P0420",
  "source": "local_db",
  "level": "info"
}
```

**Common Issues:**

**Issue:** "Module not found"
```bash
# Solution: Reinstall dependencies
pip install -r requirements.txt
```

**Issue:** "Supabase connection failed"
```bash
# Solution: Check environment variables
python -c "from app.core.config import settings; print(settings.supabase_url)"
```

**Issue:** "AI provider not working"
```bash
# Check API key
python -c "from app.core.config import settings; print(settings.ai_provider, bool(settings.cohere_api_key))"
```

### Baileys Debugging

**Enable Verbose Logs:**
```bash
# In baileys-server/.env
LOG_LEVEL=debug
NODE_ENV=development

# Restart
npm run dev
```

**Common Issues:**

**Issue:** "QR code not showing"
```bash
# Check terminal encoding
# Try: npm start 2>&1 | tee output.log
```

**Issue:** "Connection keeps dropping"
```bash
# Delete session and rescan
rm -rf auth_info_baileys
npm start
```

### Database Debugging

**Check Table Contents:**
```bash
# Using Python
python -c "
from app.db.client import get_supabase_client
client = get_supabase_client()
result = client.table('obd_codes').select('code').limit(10).execute()
print(f'Found {len(result.data)} codes')
for code in result.data:
    print(code['code'])
"
```

**Check Session State:**
```bash
python -c "
from app.db.client import get_supabase_client
from app.utils.phone import hash_phone_number

client = get_supabase_client()
phone_hash = hash_phone_number('1234567890')
result = client.table('conversation_sessions').select('*').eq('phone_hash', phone_hash).execute()
print(result.data)
"
```

---

## Adding Features

### Example: Add a New OBD Code

```python
# Method 1: Via JSON dataset
# Edit data/obd_codes_dataset.json
{
  "code": "P1234",
  "description": "New code description",
  "system": "Fuel & Air",
  "severity": "Medium",
  "symptoms": "Symptoms here",
  "common_causes": "Cause 1, Cause 2, Cause 3",
  "generic_fixes": "Fix 1, Fix 2, Fix 3"
}

# Then reload
python scripts/load_obd_codes.py

# Method 2: Direct database insert
from app.db.client import get_supabase_client
from app.repositories.obd_repository import OBDRepository

client = get_supabase_client()
repo = OBDRepository(client)

repo.insert_code({
    "code": "P1234",
    "description": "New code description",
    "system": "Fuel & Air",
    "severity": "Medium",
    "symptoms": "Symptoms here",
    "common_causes": "Cause 1, Cause 2, Cause 3",
    "generic_fixes": "Fix 1, Fix 2, Fix 3"
})
```

### Example: Add Vehicle Override

```python
from app.db.client import get_supabase_client

client = get_supabase_client()

client.table("vehicle_overrides").insert({
    "code": "P0420",
    "make": "toyota",
    "model": "camry",
    "year": "2015",
    "engine": "2.5l",
    "known_issues": ["Issue specific to this vehicle"],
    "priority_checks": ["Check 1", "Check 2"],
    "notes": "Common problem with this year/model"
}).execute()
```

### Example: Add New Message Route

```python
# In app/services/message_router.py

async def route_message(self, raw_text, phone_hash, request_id, session):
    parsed = parse_message(raw_text)
    
    # Add new route here
    if "check engine light" in raw_text.lower():
        return await self.handle_check_engine_light(session)
    
    # Existing routes...
    if parsed.code and validate_obd_code(parsed.code):
        return await self.route_to_code_diagnosis(parsed, session)
```

### Example: Add New AI Provider

```python
# 1. Create new client file
# app/services/claude_client.py

class ClaudeClient:
    def __init__(self):
        self.api_key = settings.claude_api_key
        # Initialize client
    
    async def generate(self, prompt, temperature, max_tokens):
        # Implementation
        pass

# 2. Update AIClient
# app/services/ai_client.py

def __init__(self):
    self.provider = settings.ai_provider.lower()
    
    if self.provider == "claude":
        from app.services.claude_client import ClaudeClient
        self._client = ClaudeClient()
    # ... existing providers
```

---

## Common Tasks

### Task: Update OBD Code Database

```bash
# 1. Edit dataset
nano data/obd_codes_dataset.json

# 2. Reload (uses upsert, safe to run multiple times)
python scripts/load_obd_codes.py

# 3. Verify
python -c "
from app.db.client import get_supabase_client
client = get_supabase_client()
result = client.table('obd_codes').select('code', count='exact').execute()
print(f'Total codes: {result.count}')
"
```

### Task: Clear All Sessions

```bash
python -c "
from app.db.client import get_supabase_client
client = get_supabase_client()
# WARNING: Deletes all sessions!
client.table('conversation_sessions').delete().neq('id', 0).execute()
print('All sessions cleared')
"
```

### Task: View Recent Messages

```bash
python -c "
from app.db.client import get_supabase_client
client = get_supabase_client()
result = client.table('message_logs').select('*').order('created_at', desc=True).limit(10).execute()
for msg in result.data:
    print(f\"{msg['created_at']}: {msg['request_text'][:50]}\")
"
```

### Task: Check AI Usage

```bash
python -c "
from app.db.client import get_supabase_client
client = get_supabase_client()

# Codes learned from AI
result = client.table('diagnostic_logs').select('code').eq('source', 'ai_learned').execute()
print(f'AI-learned codes: {len(result.data)}')
for code in result.data:
    print(f\"  {code['code']}\")
"
```

### Task: Deploy to Production

```bash
# 1. Update environment
export NODE_ENV=production
export APP_ENV=production

# 2. Backend (using systemd)
sudo nano /etc/systemd/system/vehicle-diagnosis.service

[Unit]
Description=Vehicle Diagnosis FastAPI
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/VehicleDiagnosisAssistant
Environment="PATH=/var/www/VehicleDiagnosisAssistant/venv/bin"
ExecStart=/var/www/VehicleDiagnosisAssistant/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8001
Restart=always

[Install]
WantedBy=multi-user.target

# 3. Baileys (using PM2)
cd baileys-server
pm2 start index.js --name baileys-server
pm2 save
pm2 startup

# 4. Setup nginx reverse proxy
sudo nano /etc/nginx/sites-available/vehicle-diagnosis

server {
    listen 80;
    server_name your-domain.com;
    
    location /webhook {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /baileys {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
    }
}

# 5. Enable and restart
sudo ln -s /etc/nginx/sites-available/vehicle-diagnosis /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## Troubleshooting

### Backend Won't Start

**Symptom:** `ModuleNotFoundError` or import errors

**Solutions:**
```bash
# 1. Check Python version
python --version  # Must be 3.12+

# 2. Reinstall dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 3. Check virtual environment
which python  # Should point to venv
```

### Database Connection Issues

**Symptom:** `[Errno 11001] getaddrinfo failed`

**Solutions:**
```bash
# 1. Check internet connection
ping supabase.com

# 2. Verify Supabase URL
python -c "from app.core.config import settings; print(settings.supabase_url)"

# 3. Test connection directly
python -c "
from app.db.client import get_supabase_client
client = get_supabase_client()
result = client.table('obd_codes').select('code').limit(1).execute()
print('Connected!' if result.data else 'Empty table')
"
```

### WhatsApp Won't Connect

**Symptom:** QR code shown but connection fails

**Solutions:**
```bash
# 1. Delete session and retry
rm -rf baileys-server/auth_info_baileys
cd baileys-server && npm start

# 2. Check WhatsApp Web isn't open
# Close all WhatsApp Web tabs

# 3. Try different QR scan
# Wait 60 seconds for timeout, scan new QR
```

### AI Provider Errors

**Symptom:** `401 Unauthorized` or `API key invalid`

**Solutions:**
```bash
# 1. Verify API key
python -c "
from app.core.config import settings
print(f'Provider: {settings.ai_provider}')
print(f'Cohere key: {settings.cohere_api_key[:10]}...' if settings.cohere_api_key else 'Not set')
"

# 2. Test API key directly
curl https://api.cohere.ai/v1/generate \
  -H "Authorization: Bearer YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"test","max_tokens":10}'

# 3. Switch providers
# Edit .env: AI_PROVIDER=gemini
```

---

## Best Practices

### Code Style

```python
# ✅ Good: Descriptive names
async def get_obd_diagnosis(code: str, vehicle: VehicleContext) -> DiagnosticResult:
    """Get OBD diagnosis with optional vehicle-specific overrides"""
    pass

# ❌ Bad: Vague names
async def get_data(c: str, v: dict) -> dict:
    pass
```

### Error Handling

```python
# ✅ Good: Specific exceptions, logged with context
try:
    result = await self.obd_service.get_obd_info(code, vehicle)
except OBDCodeNotFound as e:
    logger.warning("code_not_found", code=code)
    return fallback_response(code)
except Exception as e:
    logger.error("unexpected_error", code=code, error=str(e))
    raise

# ❌ Bad: Bare except, no logging
try:
    result = get_info(code)
except:
    return {}
```

### Logging

```python
# ✅ Good: Structured with context
logger.info(
    "diagnosis_completed",
    code=code,
    vehicle=f"{vehicle.make} {vehicle.model}",
    confidence=result.confidence,
    source=result.source,
    duration_ms=elapsed
)

# ❌ Bad: Unstructured string
logger.info(f"Got diagnosis for {code}")
```

### Database Queries

```python
# ✅ Good: Use repository pattern
result = self.obd_repo.get_by_code(code)

# ❌ Bad: Direct Supabase calls in business logic
result = client.table("obd_codes").select("*").eq("code", code).execute()
```

### Testing

```python
# ✅ Good: Test edge cases
def test_parse_code_with_spaces():
    # User might type spaces
    result = parse_message("P 0 4 2 0")
    # Currently fails, but good to document

def test_parse_malformed_year():
    result = parse_message("P0420 Toyota 20015")  # Typo
    assert result["year"] is None  # Should not extract bad year

# ❌ Bad: Only happy path
def test_parse():
    result = parse_message("P0420 Toyota Camry 2015")
    assert result["code"] == "P0420"
```

---

## Performance Tips

### Optimize Database Queries

```python
# ✅ Good: Single query with join
result = client.table("obd_codes")\
    .select("*, vehicle_overrides(*)")\
    .eq("code", code)\
    .execute()

# ❌ Bad: N+1 queries
base = client.table("obd_codes").select("*").eq("code", code).execute()
override = client.table("vehicle_overrides").select("*").eq("code", code).execute()
```

### Cache Expensive Operations

```python
# Consider adding caching for:
# - OBD code lookups (Redis)
# - AI responses for common followups
# - Session state (in-memory with TTL)

from functools import lru_cache

@lru_cache(maxsize=1000)
def get_cached_code(code: str):
    return obd_repo.get_by_code(code)
```

### Batch AI Requests

```python
# If processing multiple codes, batch them
codes = ["P0420", "P0171", "P0300"]

# ✅ Good: Single AI call
prompt = f"Rank causes for these codes: {', '.join(codes)}"
result = await ai_client.complete(prompt)

# ❌ Bad: Multiple AI calls
for code in codes:
    result = await ai_client.complete(f"Rank causes for {code}")
```

---

## Resources

### Documentation
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Supabase Docs](https://supabase.com/docs)
- [Baileys Docs](https://github.com/WhiskeySockets/Baileys)
- [Cohere API](https://docs.cohere.com/)

### Internal Docs
- `docs/ARCHITECTURE.md` - System design
- `README.md` - Project overview
- `baileys-server/README.md` - Baileys setup
- `baileys-server/SECURITY.md` - Security guide

### Tools
- **Database GUI**: [Supabase Dashboard](https://app.supabase.com/)
- **API Testing**: [Postman](https://www.postman.com/) or `curl`
- **Log Viewing**: `tail -f` or [Papertrail](https://papertrailapp.com/)

---

**Document Version:** 2.0  
**Last Updated:** 2026-07-02  
**Questions?** Check `ARCHITECTURE.md` or create an issue
