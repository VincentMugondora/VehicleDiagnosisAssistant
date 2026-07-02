# System Architecture - Vehicle Diagnosis Assistant

**Version:** 2.0  
**Last Updated:** 2026-07-02

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Components](#components)
4. [Data Flow](#data-flow)
5. [Database Schema](#database-schema)
6. [Decision Logic](#decision-logic)
7. [API Contracts](#api-contracts)
8. [Deployment Architecture](#deployment-architecture)

---

## Overview

The Vehicle Diagnosis Assistant is a WhatsApp-based OBD-II diagnostic system that uses a **hybrid lookup + LLM approach** to provide cost-effective, intelligent vehicle diagnostics.

### Design Principles

1. **Cost-Effective**: Database lookups first, AI only when necessary
2. **Fast**: <100ms response for known codes
3. **Intelligent**: Context-aware, learns new codes automatically
4. **Scalable**: Stateless services, database-backed sessions
5. **Reliable**: Multiple fallback layers, graceful degradation

### Technology Stack

- **Frontend**: WhatsApp (via Baileys bridge)
- **API Layer**: FastAPI (Python 3.12+)
- **Database**: Supabase (PostgreSQL)
- **AI**: Cohere/Gemini
- **Bridge**: Node.js + Baileys
- **Deployment**: Uvicorn (ASGI server)

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        WhatsApp User                             │
│                   "P0420 Toyota Camry 2015"                      │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Baileys Server (Node.js)                      │
│                         Port 3000                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ • Security: Helmet.js, Rate Limiting, API Key Auth       │  │
│  │ • Handles: QR auth, message events, typing indicators    │  │
│  │ • Forwards to: FastAPI via HTTP POST                     │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │ POST /webhook/baileys
                           │ Headers: X-API-Key, X-Request-ID
                           │ Body: {from, text, message_id}
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│               FastAPI Backend (Python)                           │
│                     Port 8001                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           Request Context Middleware                      │  │
│  │           • Request ID tracking                           │  │
│  │           • Structured logging (Pino-style)               │  │
│  └──────────────────────┬───────────────────────────────────┘  │
│                         ↓                                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Webhook Handler                              │  │
│  │              /webhook/baileys                             │  │
│  │           • API key validation                            │  │
│  │           • Message idempotency check                     │  │
│  │           • Usage limit enforcement                       │  │
│  └──────────────────────┬───────────────────────────────────┘  │
│                         ↓                                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │            SessionManager                                 │  │
│  │            • Load/create session                          │  │
│  │            • TTL check (30 min)                           │  │
│  │            • Last diagnosis tracking                      │  │
│  └──────────────────────┬───────────────────────────────────┘  │
│                         ↓                                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Message Parser                               │  │
│  │              • Extract OBD code (regex)                   │  │
│  │              • Extract vehicle (make/model/year/engine)   │  │
│  │              • Normalize input                            │  │
│  └──────────────────────┬───────────────────────────────────┘  │
│                         ↓                                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              MessageRouter                                │  │
│  │              DECISION POINT                               │  │
│  │              • Has OBD code? → Code diagnosis             │  │
│  │              • Has last diagnosis? → Followup with AI     │  │
│  │              • Has symptoms? → Symptom diagnosis          │  │
│  │              • None? → Help message                       │  │
│  └─────┬────────────────┬────────────────┬───────────────────┘  │
│        │                │                │                      │
│        ↓                ↓                ↓                      │
│  ┌──────────┐    ┌──────────┐    ┌────────────┐               │
│  │   OBD    │    │ Followup │    │  Symptom   │               │
│  │ Service  │    │   AI     │    │ Diagnosis  │               │
│  └─────┬────┘    └──────────┘    └────────────┘               │
│        │                                                        │
│        ↓                                                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              OBDService Execution Flow                    │  │
│  │                                                            │  │
│  │  1. Lookup in database (obd_codes table)                 │  │
│  │     └─ FOUND → Check vehicle override                    │  │
│  │        └─ FOUND → Merge causes, return (98% confidence)  │  │
│  │        └─ NOT FOUND → Return base (85% confidence)       │  │
│  │                                                            │  │
│  │  2. NOT FOUND in DB:                                      │  │
│  │     └─ [AUTO_LEARN_CODES=true] → AICodeGenerator         │  │
│  │        ├─ Generate with AI                                │  │
│  │        ├─ Save to database (upsert)                       │  │
│  │        └─ Return to user (75% confidence)                 │  │
│  │                                                            │  │
│  │  3. AI Generation Failed:                                 │  │
│  │     └─ Return generic fallback (30% confidence)           │  │
│  │                                                            │  │
│  │  4. [AI_ENRICH_ENABLED=true] Optional:                    │  │
│  │     └─ Rank causes by vehicle context                     │  │
│  └──────────────────────┬───────────────────────────────────┘  │
│                         ↓                                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Response Formatter                           │  │
│  │              • Format for WhatsApp                        │  │
│  │              • Split long messages                        │  │
│  │              • Add emojis and structure                   │  │
│  └──────────────────────┬───────────────────────────────────┘  │
│                         ↓                                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Audit Logger                                 │  │
│  │              • Log to message_logs table                  │  │
│  │              • Log to diagnostic_logs table               │  │
│  │              • Save session state                         │  │
│  └──────────────────────┬───────────────────────────────────┘  │
└─────────────────────────┼──────────────────────────────────────┘
                          │
                          ↓ JSON Response
                          │ {reply: "🔧 P0420..."}
┌─────────────────────────┴──────────────────────────────────────┐
│                    Baileys Server                                │
│                    • Sends reply via WhatsApp                    │
│                    • Handles message chunking                    │
└─────────────────────────┬──────────────────────────────────────┘
                          │
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│                        WhatsApp User                             │
│                  Receives formatted diagnosis                    │
└─────────────────────────────────────────────────────────────────┘

External Dependencies:
┌────────────┐    ┌──────────────┐    ┌───────────────┐
│  Supabase  │    │ Cohere/Gemini│    │  Web Scraping │
│ PostgreSQL │    │      AI      │    │   (Optional)  │
└────────────┘    └──────────────┘    └───────────────┘
```

---

## Components

### 1. Baileys Server (Node.js)

**Purpose**: WhatsApp bridge

**Responsibilities**:
- QR code authentication
- WhatsApp session management
- Message event handling
- Security (rate limiting, API key auth)
- Forward messages to FastAPI

**Key Files**:
- `baileys-server/index.js` - Main server
- `baileys-server/.env` - Configuration

**Security Features**:
- Helmet.js security headers
- Express rate limiting (20 req/min)
- API key authentication
- Request size limits (100KB)
- CORS protection

### 2. FastAPI Backend

**Purpose**: Core business logic

**Responsibilities**:
- Message routing and parsing
- Database lookups
- AI integration
- Session management
- Audit logging

**Key Files**:
- `app/main.py` - FastAPI application
- `app/api/routes/webhook.py` - Webhook handler
- `app/services/message_router.py` - Routing logic
- `app/services/obd_service.py` - OBD diagnosis
- `app/services/session_manager.py` - Session state

### 3. Supabase (PostgreSQL)

**Purpose**: Data persistence

**Tables**:
- `obd_codes` - OBD-II code library (250+ codes)
- `vehicle_overrides` - Make/model-specific diagnostics
- `message_logs` - Audit trail
- `conversation_sessions` - Session state
- `diagnostic_logs` - Analytics

### 4. AI Providers

**Cohere (Primary)**:
- `command-r` model
- Used for: cause ranking, code generation, followups

**Gemini (Legacy)**:
- `gemini-1.5-flash` model
- Fallback option

---

## Data Flow

### Happy Path: Known Code

```
1. User sends: "P0420 Toyota Camry 2015"
   ↓
2. Baileys receives, forwards to FastAPI
   Time: ~10ms
   ↓
3. Webhook validates API key, checks idempotency
   Time: ~5ms
   ↓
4. SessionManager loads session (or creates new)
   DB query: ~20ms
   ↓
5. Parser extracts: code="P0420", make="Toyota", model="Camry", year="2015"
   Time: ~1ms
   ↓
6. MessageRouter validates code format (regex)
   Time: ~1ms
   ↓
7. OBDService.get_obd_info():
   a. DB lookup: SELECT * FROM obd_codes WHERE code='P0420'
      Time: ~15ms
   b. Found! Check vehicle override
      Query: SELECT * FROM vehicle_overrides WHERE code='P0420' AND make='toyota'...
      Time: ~20ms
   c. Override found! Merge causes
      Time: ~1ms
   ↓
8. [Optional] AI cause ranking (if AI_ENRICH_ENABLED=true)
   API call: ~500ms
   Cost: ~$0.001
   ↓
9. Store last_diagnosis in session
   Time: ~1ms
   ↓
10. Format response for WhatsApp
    Time: ~2ms
   ↓
11. Log to message_logs and diagnostic_logs
    DB insert: ~25ms
   ↓
12. Return to Baileys
    Time: ~5ms
   ↓
13. Baileys sends to WhatsApp
    Time: ~50ms

Total Time (without AI): ~100ms
Total Time (with AI): ~600ms
Total Cost (without AI): $0.00
Total Cost (with AI): ~$0.001
```

### Unhappy Path: Unknown Code

```
1. User sends: "P9999"
   ↓
2-6. Same as above (~37ms)
   ↓
7. OBDService.get_obd_info():
   a. DB lookup: NOT FOUND
      Time: ~15ms
   b. [AUTO_LEARN_CODES=true] → AICodeGenerator
      API call to Cohere/Gemini: ~2000ms
      Cost: ~$0.01
   c. Save generated code to DB (upsert)
      DB insert: ~30ms
   d. Return to user with AI-generated diagnosis
      Confidence: 75%
   ↓
8-13. Same as above (~83ms)

Total Time: ~2100ms (first time)
Total Cost: ~$0.01 (first time)

Next user asking for P9999:
- Uses DB lookup (100ms, $0.00)
- AI cost amortized across all users
```

### Followup Flow

```
1. User previously diagnosed with P0420
   ↓
2. User sends: "it's also making a rattling noise"
   ↓
3-6. Same as above
   ↓
7. MessageRouter:
   - No OBD code detected
   - Session.last_diagnosis exists? YES
   - Has AI client? YES
   ↓
8. Build context:
   "Previous diagnosis:
   - Code: P0420
   - Issue: Catalyst System Efficiency Below Threshold
   - Vehicle: Toyota Camry 2015
   
   User's followup: it's also making a rattling noise"
   ↓
9. AI completion:
   API call: ~1500ms
   Cost: ~$0.005
   ↓
10. Return contextualized response

Total Time: ~1600ms
Total Cost: ~$0.005
```

---

## Database Schema

### obd_codes

```sql
CREATE TABLE obd_codes (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(10) UNIQUE NOT NULL,  -- P0420, B1234, etc
    description TEXT NOT NULL,
    system VARCHAR(50),                 -- "Emissions", "Fuel & Air", etc
    severity VARCHAR(20),               -- "Low", "Medium", "High"
    symptoms TEXT,
    common_causes TEXT,                 -- Comma-separated
    generic_fixes TEXT,                 -- Comma-separated
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_obd_codes_code ON obd_codes(code);
CREATE INDEX idx_obd_codes_system ON obd_codes(system);
```

### vehicle_overrides

```sql
CREATE TABLE vehicle_overrides (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(10) NOT NULL,
    make VARCHAR(50) NOT NULL,          -- Normalized lowercase
    model VARCHAR(50) NOT NULL,
    year VARCHAR(4) NOT NULL,
    engine VARCHAR(20) NOT NULL,
    known_issues JSONB,                 -- Array of strings
    priority_checks JSONB,              -- Array of strings
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(code, make, model, year, engine)
);

CREATE INDEX idx_vehicle_overrides_lookup 
ON vehicle_overrides(code, make, model, year, engine);
```

### message_logs

```sql
CREATE TABLE message_logs (
    id BIGSERIAL PRIMARY KEY,
    message_id VARCHAR(255) UNIQUE NOT NULL,
    phone_hash VARCHAR(64) NOT NULL,    -- SHA-256
    request_id UUID NOT NULL,
    session_id VARCHAR(255),
    request_text TEXT NOT NULL,
    response_text TEXT NOT NULL,
    code VARCHAR(10),                   -- OBD code if applicable
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_message_logs_phone_hash ON message_logs(phone_hash);
CREATE INDEX idx_message_logs_message_id ON message_logs(message_id);
CREATE INDEX idx_message_logs_created_at ON message_logs(created_at);
```

### conversation_sessions

```sql
CREATE TABLE conversation_sessions (
    id BIGSERIAL PRIMARY KEY,
    phone_hash VARCHAR(64) UNIQUE NOT NULL,
    state JSONB NOT NULL,               -- SessionState serialized
    last_active TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_sessions_phone_hash ON conversation_sessions(phone_hash);
CREATE INDEX idx_sessions_last_active ON conversation_sessions(last_active);
```

### diagnostic_logs

```sql
CREATE TABLE diagnostic_logs (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(10) NOT NULL,
    vehicle TEXT,                       -- "Toyota Camry 2015"
    source VARCHAR(50) NOT NULL,        -- "local_db", "ai_learned", etc
    confidence DECIMAL(3,2),            -- 0.00 to 1.00
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_diagnostic_logs_code ON diagnostic_logs(code);
CREATE INDEX idx_diagnostic_logs_created_at ON diagnostic_logs(created_at);
```

---

## Decision Logic

### MessageRouter Flow

```python
def route_message(raw_text, session):
    parsed = parse_message(raw_text)
    
    # Decision 1: Is there an OBD code?
    if parsed.code and validate_obd_code(parsed.code):
        return route_to_code_diagnosis(parsed)
    
    # Decision 2: Is this a followup to a previous diagnosis?
    if session.last_diagnosis and ai_client:
        return route_to_followup(raw_text, session.last_diagnosis)
    
    # Decision 3: Does the text describe symptoms?
    symptoms = normalize_symptoms(raw_text)
    if symptoms:
        return route_to_symptom_diagnosis(symptoms)
    
    # Decision 4: No valid input
    return help_message()
```

### OBDService Lookup Strategy

```python
def get_obd_info(code, vehicle):
    # Priority 1: Database lookup
    base = db.get_by_code(code)
    
    if base:
        # Priority 2: Vehicle-specific override
        if vehicle.is_complete():
            override = db.get_vehicle_override(code, vehicle)
            if override:
                return merge(base, override, confidence=0.98)
        
        return base_result(confidence=0.85)
    
    # Priority 3: AI auto-learning
    if settings.auto_learn_codes:
        ai_result = ai_generate_and_save(code)
        if ai_result:
            return ai_result(confidence=0.75)
    
    # Priority 4: Generic fallback
    return generic_response(confidence=0.30)
```

---

## API Contracts

### POST /webhook/baileys

**Request:**
```json
{
  "from": "1234567890@s.whatsapp.net",
  "sender": "1234567890@s.whatsapp.net",
  "text": "P0420 Toyota Camry 2015",
  "message": "P0420 Toyota Camry 2015",
  "message_id": "3EB0XXXXXXXXXXXX"
}
```

**Headers:**
```
Content-Type: application/json
X-API-Key: <32+ character key>
X-Request-ID: <UUID> (optional, auto-generated if missing)
```

**Response:**
```json
{
  "reply": "🔧 P0420 - Catalyst System Efficiency Below Threshold (Bank 1)\n\n📋 DESCRIPTION\nThe catalytic converter...\n\n⚠️ CAUSES\n• Worn catalytic converter\n• Faulty oxygen sensor\n...",
  "status": "success"
}
```

**Error Responses:**
```json
{
  "error": "Authentication required",
  "status": 401
}

{
  "error": "Rate limit exceeded",
  "status": 429
}

{
  "ok": true,
  "status": "duplicate"
}
```

### GET /health

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-07-02T12:00:00Z",
  "database": "connected",
  "ai_provider": "cohere"
}
```

---

## Deployment Architecture

### Development

```
┌─────────────────┐
│   Developer     │
│   Machine       │
│                 │
│ • Uvicorn :8001 │
│ • Node.js :3000 │
│ • Supabase SaaS │
└─────────────────┘
```

### Production (Recommended)

```
                    ┌──────────────────┐
                    │   Load Balancer  │
                    │   (nginx/Caddy)  │
                    │   :443 (HTTPS)   │
                    └────────┬─────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
              ↓                             ↓
   ┌──────────────────┐          ┌──────────────────┐
   │  Baileys Server  │          │  FastAPI Backend │
   │   (Node.js)      │          │   (Python)       │
   │   PM2/systemd    │←─────────│   Uvicorn        │
   │   Port 3000      │  HTTP    │   Port 8001      │
   └──────────────────┘          └────────┬─────────┘
                                          │
                    ┌─────────────────────┴──────────────────────┐
                    │                                             │
                    ↓                                             ↓
          ┌──────────────────┐                        ┌──────────────────┐
          │    Supabase      │                        │   AI Provider    │
          │   PostgreSQL     │                        │ Cohere/Gemini    │
          │   (Managed)      │                        │   (API)          │
          └──────────────────┘                        └──────────────────┘
```

### Scaling Strategy

**Current Load: 1-100 users**
- Single server handles both services
- Supabase free tier: 500MB, 2GB transfer
- Cost: ~$5/month (AI only)

**Medium Load: 100-1000 users**
- Separate containers for Baileys + FastAPI
- Supabase Pro: $25/month
- Horizontal scaling with load balancer
- Cost: ~$50-100/month

**High Load: 1000+ users**
- Kubernetes cluster (multiple replicas)
- Redis for session caching
- Supabase dedicated instance
- CDN for static assets
- Cost: $200-500/month

---

## Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| **Response Time (DB lookup)** | <200ms | ~100ms |
| **Response Time (AI fallback)** | <3000ms | ~2000ms |
| **Throughput** | 100 req/sec | 50 req/sec |
| **Uptime** | 99.9% | N/A |
| **Database Size** | <1GB | ~10MB |

---

## Security Considerations

### Authentication
- API keys minimum 32 characters
- Keys stored in environment variables only
- No keys in logs or error messages

### Rate Limiting
- 20 requests/minute per IP (Baileys)
- 20 requests/30-day window per phone number (Backend)
- Configurable via environment variables

### Data Privacy
- Phone numbers hashed (SHA-256) before storage
- No PII in logs
- Session data encrypted at rest (Supabase)
- GDPR compliant (data retention policies)

### Network Security
- TLS 1.2+ required
- CORS with allowlist
- Security headers (Helmet.js)
- No exposed internal APIs

---

## Monitoring & Observability

### Metrics to Track
- Request rate (requests/second)
- Response time (p50, p95, p99)
- Error rate (4xx, 5xx)
- AI call rate and cost
- Database query time
- Cache hit rate (future)

### Logging
- Structured JSON logs (Pino format)
- Request ID tracing
- Log levels: trace, debug, info, warn, error, fatal
- Retention: 30 days

### Alerts
- Error rate > 5%
- Response time p95 > 2000ms
- Database connection failures
- AI API failures
- Disk usage > 80%

---

**Document Version:** 2.0  
**Last Updated:** 2026-07-02  
**Maintained By:** Development Team
