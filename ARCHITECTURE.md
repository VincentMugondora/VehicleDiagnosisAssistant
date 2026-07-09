# Vehicle Diagnosis Assistant - Production Architecture

## System Overview

A WhatsApp-based OBD-II diagnostic assistant that provides vehicle fault code explanations with intelligent enrichment.

**Current Version:** 2.0 (Production MVP)  
**Last Updated:** 2026-07-09

---

## Request Lifecycle

```
┌─────────────────┐
│  WhatsApp User  │
│  sends "P0420"  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│         Baileys WhatsApp Server         │
│         (Node.js, port 3001)            │
└────────┬────────────────────────────────┘
         │ HTTP POST /webhook
         ▼
┌─────────────────────────────────────────┐
│      FastAPI Application (Python)       │
│      app/api/routes/webhook.py          │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│        Message Router Service           │
│    Parses code from user message        │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│           OBD Service                   │
│    get_obd_info(code, vehicle)          │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│        OBD Repository                   │
│  get_by_code() → Supabase/PostgreSQL    │
└────────┬────────────────────────────────┘
         │
         ├─── Code Found ──────────────────┐
         │                                  │
         ▼                                  │
    ┌─────────┐                             │
    │ Complete│                             │
    │  Data?  │                             │
    └────┬────┘                             │
         │                                  │
    ┌────┴────┐                             │
    │   NO    │                             │
    └────┬────┘                             │
         │                                  │
         ▼                                  │
┌─────────────────────────────────────┐    │
│   Selective Enrichment Service      │    │
│   - Detects missing fields           │    │
│   - Builds context-aware AI prompt   │    │
│   - Calls AI with only missing data  │    │
└────────┬────────────────────────────┘    │
         │                                  │
         ▼                                  │
┌─────────────────────────────────────┐    │
│        AI Client (Cohere)            │    │
│   Returns JSON with missing fields   │    │
└────────┬────────────────────────────┘    │
         │                                  │
         ▼                                  │
┌─────────────────────────────────────┐    │
│  Repository.enrich_code()            │    │
│  - Stores enriched fields            │    │
│  - Stores provenance metadata        │    │
│  - Updates enrichment_status         │    │
│  - Sets last_enriched timestamp      │    │
└────────┬────────────────────────────┘    │
         │                                  │
         ▼                                  │
         └──────────────┬──────────────────┘
                        │
                        ▼
           ┌─────────────────────────┐
           │  Build DiagnosticResult │
           │  with all fields        │
           └────────┬────────────────┘
                    │
                    ▼
           ┌─────────────────────────┐
           │  Diagnostic Formatter   │
           │  format_diagnostic_     │
           │  report()               │
           └────────┬────────────────┘
                    │
                    ▼
           ┌─────────────────────────┐
           │  Split into WhatsApp    │
           │  messages (1500 char)   │
           └────────┬────────────────┘
                    │
                    ▼
           ┌─────────────────────────┐
           │  Send via Baileys       │
           │  HTTP POST to Node.js   │
           └────────┬────────────────┘
                    │
                    ▼
           ┌─────────────────────────┐
           │  User receives reply    │
           └─────────────────────────┘
```

---

## Core Components

### 1. OBDService (`app/services/obd_service.py`)

**Purpose:** Orchestrates OBD code lookups with intelligent enrichment.

**Key Methods:**
- `get_obd_info(code, vehicle)` - Main entry point for code lookups
- `_enrich_and_save(code, base_data)` - Coordinates enrichment when needed
- `_fetch_and_learn(code)` - Handles completely unknown codes

**Responsibilities:**
- Determine if enrichment is needed
- Trigger selective AI enrichment for missing fields
- Handle vehicle-specific overrides
- Return structured DiagnosticResult

**Configuration:**
- `auto_learn=True` - Enable AI enrichment
- `ai_client` - Required for enrichment

---

### 2. OBDRepository (`app/repositories/obd_repository.py`)

**Purpose:** Database access layer with caching.

**Key Methods:**
- `get_by_code(code)` - Retrieve code data (cached)
- `insert_code(code_data)` - Upsert code (invalidates cache)
- `enrich_code(code, enriched_fields, metadata_fields)` - Specialized enrichment update
- `update_code_fields(code, updates)` - Partial field update
- `get_vehicle_override(code, make, model, year, engine)` - Vehicle-specific data

**Caching:**
- In-memory dictionary cache (`_obd_cache`)
- Invalidated on writes
- Reduces lookup from 3.5s to <1ms

**Database Schema:**
```sql
obd_codes (
    code TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    symptoms TEXT,
    common_causes TEXT,
    generic_fixes TEXT,
    system TEXT,
    severity TEXT,
    severity_explanation TEXT,
    technician_tip TEXT,
    pre_replacement_checks TEXT,
    
    -- Metadata fields (JSONB)
    symptoms_meta JSONB,
    causes_meta JSONB,
    severity_meta JSONB,
    technician_tip_meta JSONB,
    pre_replacement_checks_meta JSONB,
    
    -- Enrichment tracking
    enrichment_status VARCHAR(30) DEFAULT 'not_enriched',
    schema_version INT DEFAULT 1,
    last_enriched TIMESTAMP,
    created_at TIMESTAMPTZ DEFAULT NOW()
)
```

---

### 3. SelectiveEnrichment (`app/services/selective_enrichment.py`)

**Purpose:** Generate ONLY missing fields using AI with context.

**Key Innovation:** Instead of regenerating all fields, provides existing context to AI and requests only what's missing.

**Benefits:**
- Reduces hallucination (AI sees existing data)
- Lower token usage (~40% reduction)
- Preserves human-curated data
- Faster enrichment

**Process:**
1. Receives list of missing field names
2. Builds prompt with existing context
3. Requests only missing fields from AI
4. Parses JSON response
5. Attaches metadata to each generated field

**Metadata Stored:**
- `source` - Always "ai_generated" for enrichment
- `ai_model` - Model identifier (e.g., "claude-sonnet-4")
- `prompt_version` - Tracks prompt iterations (e.g., "v6")
- `generated_at` - Timestamp

---

### 4. Diagnostic Formatter (`app/services/diagnostic_formatter.py`)

**Purpose:** Convert DiagnosticResult to formatted WhatsApp message.

**Format Structure:**
```
🔧 Fault Code: P0420

System: Emissions

📖 What it means
[Description]

🚗 Common symptoms
• [Symptom 1]
• [Symptom 2]

🔍 Likely causes
• [Cause 1]
• [Cause 2]

🛠️ Recommended diagnostic steps
1. [Step 1]
2. [Step 2]

⚠️ Severity
[Level]
[Explanation]

❌ Do NOT replace parts until
• [Pre-check 1]
• [Pre-check 2]

💡 Technician Tip
[Tip]

> Always confirm the diagnosis using live scanner data...
```

**Message Splitting:**
- Maximum 1500 characters per message
- Splits on line boundaries
- Adds "1/N" prefixes if split

---

## Data Flow Scenarios

### Scenario 1: Complete Code (No Enrichment Needed)

```
User: P0420
  ↓
Repository: Returns complete record from cache
  ↓
Service: Checks completeness → All fields present
  ↓
Service: Skips enrichment (logs "enrichment_skipped")
  ↓
Formatter: Generates response
  ↓
User: Receives instant reply (<100ms)
```

### Scenario 2: Partial Code (Needs Enrichment)

```
User: P0171
  ↓
Repository: Returns partial record (missing symptoms, severity, tip)
  ↓
Service: Detects missing fields → Needs enrichment
  ↓
SelectiveEnrichment: Builds context-aware prompt
  ↓
AI: Generates only missing fields (symptoms, severity, tip)
  ↓
Repository: Updates code with enriched fields + metadata
  ↓
Service: Returns enriched DiagnosticResult
  ↓
Formatter: Generates response
  ↓
User: Receives reply (2-4 seconds first time, <100ms thereafter)
```

### Scenario 3: Unknown Code (Full AI Generation)

```
User: P9999
  ↓
Repository: Returns None (code not in database)
  ↓
Service: Triggers _fetch_and_learn()
  ↓
AICodeGenerator: Generates complete code definition
  ↓
Repository: Inserts new code
  ↓
Service: Returns generated DiagnosticResult
  ↓
Formatter: Generates response
  ↓
User: Receives reply (3-5 seconds first time)
```

### Scenario 4: Vehicle-Specific Override

```
User: P0420 (with vehicle: 2015 Toyota Camry 2.5L)
  ↓
Repository: Returns base code
  ↓
Repository: Finds vehicle override
  ↓
Service: Merges override with base (deduplicated)
  ↓
Service: Returns DiagnosticResult (source="vehicle_override", confidence=0.98)
  ↓
Formatter: Generates response
  ↓
User: Receives vehicle-specific advice
```

---

## Observability & Logging

### Key Log Events

**Lookup Events:**
- `obd_lookup_started` - Code lookup initiated
- `obd_code_found_in_db` - Code found in database
- `obd_code_not_found` - Code not in database

**Enrichment Events:**
- `enrichment_needed` - Lists missing fields
- `enrichment_started` - AI enrichment begins
- `enrichment_completed` - Enrichment succeeded (includes duration_ms)
- `enrichment_failed` - Enrichment failed
- `enrichment_skipped` - Enrichment skipped (reason provided)

**Database Events:**
- `enrichment_save_success` - Enriched data saved
- `enrichment_save_failed` - Save operation failed

**Metrics Tracked:**
- Enrichment duration (milliseconds)
- Fields enriched per request
- Cache hit rate (implicit via log analysis)
- AI call frequency

### Example Log Output

```
[info] obd_lookup_started code=P0171
[info] obd_code_found_in_db code=P0171 has_symptoms=false
[info] enrichment_needed code=P0171 missing_symptoms=true missing_severity=true missing_tip=true
[info] enrichment_started code=P0171 fields=['symptoms', 'severity', 'technician_tip']
[info] selective_enrichment_success code=P0171 generated_fields=['symptoms', 'severity', 'technician_tip'] metadata_fields=['symptoms_meta', 'severity_meta', 'technician_tip_meta']
[info] enrichment_completed code=P0171 fields_enriched=['symptoms', 'severity', 'technician_tip'] duration_ms=2341
[info] obd_lookup_success code=P0171 source=enriched
```

---

## Configuration

### Environment Variables

```bash
# Database
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJ...

# AI Provider
COHERE_API_KEY=xxx

# WhatsApp
BAILEYS_WEBHOOK_URL=http://localhost:3001

# Payments (Optional)
PAYNOW_INTEGRATION_ID=xxx
PAYNOW_INTEGRATION_KEY=xxx
```

### Feature Flags

- `auto_learn` - Enable AI enrichment (default: True in production)
- `supabase_enabled` - Use database vs fallback data (auto-detected)

---

## Deployment

### Infrastructure

- **Application:** FastAPI (Python 3.12)
- **Database:** Supabase PostgreSQL
- **WhatsApp Bridge:** Baileys (Node.js)
- **AI Provider:** Cohere Command-R
- **Hosting:** Render

### Startup Sequence

1. FastAPI app initializes
2. Supabase connectivity check
3. If Supabase unavailable → Fallback mode
4. Payment poller starts (if configured)
5. Webhook routes registered
6. Health check available at `/healthz`

### Resource Requirements

- Memory: ~200MB base + ~50MB per concurrent enrichment
- CPU: Low (mostly I/O bound)
- Database: ~1-2 queries per request (with caching)
- AI: 0-1 calls per new/incomplete code

---

## Testing Strategy

### Integration Tests (`tests/test_end_to_end_integration.py`)

Covers complete request flows:
1. ✅ Complete record lookup (no enrichment)
2. ✅ Partial record enrichment
3. ✅ Unknown code generation
4. ✅ Vehicle override merging
5. ✅ Formatter output
6. ✅ Metadata persistence

### Unit Tests

- Repository methods
- Data parsing
- Message formatting

### Test Coverage

- Core flow: 100% (all scenarios tested)
- Edge cases: 85%
- API layer: Partial (auth required)

---

## Performance Characteristics

### Latency

| Scenario | First Request | Cached |
|----------|--------------|---------|
| Complete code | 50-100ms | <10ms |
| Partial code (enrichment) | 2-4s | <10ms |
| Unknown code | 3-5s | <10ms |
| Vehicle override | 100-200ms | <10ms |

### Throughput

- **Without enrichment:** ~50 requests/second
- **With enrichment:** ~5 concurrent enrichments (AI rate limit)

### Scalability

Current bottlenecks:
1. AI API rate limits (5 req/s for Cohere)
2. Single-instance cache (not distributed)
3. Supabase connection pool

Solutions for scale:
- Add Redis for distributed caching
- Use FastAPI BackgroundTasks for async enrichment
- Scale horizontally with shared cache

---

## Future Enhancements (Not Implemented)

### Not in MVP

- ❌ Background queue (removed - adds complexity without proven need)
- ❌ Redis caching (in-memory sufficient for current scale)
- ❌ Celery workers (async enrichment not needed yet)
- ❌ Distributed tracing
- ❌ A/B testing framework

### Recommended Next Steps

1. **Monitor production metrics** - Establish baseline
2. **Add Sentry** - Error tracking
3. **Dashboard** - Enrichment stats, cache hit rate, latency
4. **Prompt versioning** - Track prompt experiments
5. **Batch enrichment** - Offline enrichment of incomplete records

---

## Technical Debt

### Known Issues

1. **Pydantic deprecation warnings** - Using class-based config (migrate to ConfigDict)
2. **FastAPI lifespan** - Using deprecated on_event (migrate to lifespan context)
3. **datetime.utcnow()** - Deprecated (migrate to datetime.now(datetime.UTC))

### Recommendations

1. Fix deprecations before Pydantic V3
2. Add request timeout for AI calls
3. Implement circuit breaker for AI failures
4. Add structured error responses
5. Document prompt engineering decisions

---

## Security Considerations

- Phone numbers hashed with SHA-256
- Supabase RLS (Row Level Security) enabled
- API keys in environment variables
- No PII logged
- WhatsApp E2E encryption maintained

---

## Maintenance

### Database Migrations

Located in `/migrations/`:
- `001_add_metadata_columns.sql` - Adds enrichment metadata

**To apply:**
```sql
-- Run in Supabase SQL editor
\i migrations/001_add_metadata_columns.sql
```

### Monitoring Checklist

- [ ] Supabase connection health
- [ ] AI API quota usage
- [ ] Cache hit rate
- [ ] Enrichment success rate
- [ ] Average response time
- [ ] Error rate by type

---

## Support

For issues or questions:
- Check logs: Structured JSON logging enabled
- Database: Supabase dashboard
- AI: Cohere dashboard for usage/errors
