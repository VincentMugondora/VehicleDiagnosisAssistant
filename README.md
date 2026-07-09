# Vehicle Diagnosis Assistant

**WhatsApp-based OBD-II diagnostic assistant with AI-powered enrichment**

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/tests-22%20passed-success.svg)](./tests/)

---

## Overview

A production-ready diagnostic assistant that explains OBD-II fault codes through WhatsApp. Features intelligent AI enrichment for incomplete data, vehicle-specific overrides, and comprehensive provenance tracking.

### Key Features

✅ **Instant Lookups** - <100ms response for cached codes  
✅ **Selective AI Enrichment** - Generates only missing fields  
✅ **Vehicle-Specific Advice** - Override data for known vehicle issues  
✅ **Provenance Tracking** - Records source and quality of every field  
✅ **Production Observability** - Structured logging with timing metrics  
✅ **Zero Dead Code** - No unused infrastructure or features

---

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+ (for WhatsApp bridge)
- PostgreSQL (Supabase)
- Cohere API key

### Installation

```bash
# 1. Clone repository
git clone <repo-url>
cd VehicleDiagnosisAssistant

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Install WhatsApp bridge
cd baileys-server
npm install
cd ..

# 4. Configure environment
cp .env.example .env
# Edit .env with your credentials
```

### Environment Variables

```bash
# Required
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJ...
COHERE_API_KEY=xxx
BAILEYS_WEBHOOK_URL=http://localhost:3001

# Optional
PAYNOW_INTEGRATION_ID=xxx  # For payments
PAYNOW_INTEGRATION_KEY=xxx
```

### Running

```bash
# Terminal 1: Start WhatsApp bridge
cd baileys-server
npm start

# Terminal 2: Start FastAPI application
uvicorn app.main:app --reload --port 8000

# Terminal 3: Expose with ngrok (for WhatsApp webhook)
ngrok http 8000
```

### Database Setup

```bash
# Apply migrations in Supabase SQL editor
cat migrations/001_add_metadata_columns.sql
# Copy and run in Supabase dashboard
```

---

## Architecture

### Request Flow

```
WhatsApp → Baileys → FastAPI → OBDService → Repository → Database
                                    ↓
                            Selective Enrichment
                                    ↓
                               AI Client
                                    ↓
                              Formatter → WhatsApp
```

See [ARCHITECTURE.md](./ARCHITECTURE.md) for complete system documentation.

---

## Usage Examples

### Simple Lookup

```
User: P0420

Bot: 🔧 Fault Code: P0420

System: Emissions

📖 What it means
Catalyst System Efficiency Below Threshold (Bank 1)

🚗 Common symptoms
• Check Engine Light illuminated
• Reduced fuel economy
• Sulfur smell from exhaust

🔍 Likely causes
• Failed catalytic converter
• Exhaust leak before catalytic converter
• Faulty oxygen sensor

...
```

### Vehicle-Specific Advice

```
User: P0420 on my 2015 Toyota Camry 2.5L

Bot: [Includes vehicle-specific known issues and priority checks]
```

---

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run integration tests only
pytest tests/test_end_to_end_integration.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

### Test Coverage

- ✅ 22 tests passing
- ✅ End-to-end integration (7 tests)
- ✅ Data-driven formatter (9 tests)
- ✅ Core enrichment flow

---

## Project Structure

```
VehicleDiagnosisAssistant/
├── app/
│   ├── api/              # FastAPI routes and formatters
│   ├── core/             # Config, logging, middleware
│   ├── models/           # Pydantic models
│   ├── repositories/     # Database access layer
│   ├── services/         # Business logic
│   │   ├── obd_service.py              # Main lookup service
│   │   ├── selective_enrichment.py     # AI enrichment
│   │   ├── diagnostic_formatter.py     # WhatsApp formatting
│   │   └── ...
│   └── main.py           # FastAPI application
├── baileys-server/       # WhatsApp bridge (Node.js)
├── migrations/           # Database migrations
├── tests/                # Test suite
├── ARCHITECTURE.md       # Complete system documentation
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

---

## Key Components

### OBDService

Main orchestration service for code lookups.

```python
from app.services.obd_service import OBDService

service = OBDService(
    obd_repo=repo,
    ai_client=ai_client,
    auto_learn=True  # Enable AI enrichment
)

result = await service.get_obd_info("P0420", vehicle_context)
```

### Selective Enrichment

Generates only missing fields with provenance tracking.

```python
from app.services.selective_enrichment import SelectiveEnrichment

enrichment = SelectiveEnrichment(ai_client)

# Returns enriched fields + metadata
data = await enrichment.enrich_missing_fields(
    code="P0171",
    existing_data=base_data,
    missing_fields=["symptoms", "severity", "technician_tip"]
)
```

### Diagnostic Formatter

Converts structured data to WhatsApp-ready messages.

```python
from app.api.formatters import format_diagnostic_response

messages = format_diagnostic_response(diagnostic_result)
# Returns list of strings, split if >1500 chars
```

---

## Configuration

### Feature Flags

- `auto_learn` - Enable AI enrichment (default: True)
- `supabase_enabled` - Use database vs fallback (auto-detected)

### Enrichment Settings

Located in `selective_enrichment.py`:

```python
CURRENT_PROMPT_VERSION = "v6"
CURRENT_AI_MODEL = "claude-sonnet-4"
```

Increment `CURRENT_PROMPT_VERSION` when changing prompts to track experiments.

---

## Monitoring

### Health Check

```bash
curl http://localhost:8000/healthz
```

### Key Metrics

Monitor via structured logs:

- **Cache hit rate** - `obd_code_found_in_db` vs `obd_code_not_found`
- **Enrichment frequency** - `enrichment_started` count
- **Enrichment duration** - `duration_ms` in `enrichment_completed`
- **AI call rate** - `selective_enrichment_success` count
- **Error rate** - `enrichment_failed` count

### Log Example

```json
{
  "event": "enrichment_completed",
  "code": "P0171",
  "fields_enriched": ["symptoms", "severity", "technician_tip"],
  "duration_ms": 2341,
  "timestamp": "2026-07-09T12:34:56Z"
}
```

---

## Deployment

### Render (Recommended)

```yaml
# render.yaml
services:
  - type: web
    name: vehicle-diagnosis-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_KEY
        sync: false
      - key: COHERE_API_KEY
        sync: false
```

### Production Checklist

- [ ] Apply database migrations
- [ ] Configure environment variables
- [ ] Set up Supabase Row Level Security
- [ ] Configure WhatsApp webhook URL
- [ ] Test health check endpoint
- [ ] Verify AI API quota
- [ ] Enable error tracking (Sentry recommended)

---

## Performance

| Scenario | Latency | Caching |
|----------|---------|---------|
| Complete code | 50-100ms | ✅ |
| Partial code (first) | 2-4s | ❌ |
| Partial code (cached) | <10ms | ✅ |
| Unknown code | 3-5s | ❌ |
| Vehicle override | 100-200ms | ✅ |

### Scalability

**Current capacity:**
- 50 requests/second (cached)
- 5 concurrent AI enrichments

**Bottlenecks:**
1. AI API rate limits
2. Single-instance cache
3. Database connection pool

**Scale solutions:**
- Redis for distributed caching
- FastAPI BackgroundTasks for async enrichment
- Horizontal scaling with load balancer

---

## Development

### Running Tests

```bash
# Watch mode
pytest-watch tests/

# With coverage
pytest tests/ --cov=app --cov-report=term-missing

# Specific test file
pytest tests/test_end_to_end_integration.py -v
```

### Code Quality

```bash
# Format code
black app/ tests/

# Lint
pylint app/

# Type checking
mypy app/
```

### Database Migrations

Create new migration:

```sql
-- migrations/002_add_your_feature.sql
ALTER TABLE obd_codes ADD COLUMN your_field TEXT;
```

Apply in Supabase SQL editor.

---

## API Documentation

Once running, visit:

- **Interactive docs:** http://localhost:8000/docs
- **OpenAPI schema:** http://localhost:8000/openapi.json
- **Health check:** http://localhost:8000/healthz

---

## Troubleshooting

### "Supabase unreachable"

- Check `SUPABASE_URL` and `SUPABASE_KEY`
- Verify network connectivity
- Application runs in fallback mode (limited data)

### "AI enrichment failed"

- Check `COHERE_API_KEY`
- Verify API quota not exceeded
- Check logs for specific error

### "WhatsApp not responding"

- Ensure baileys-server is running
- Check webhook URL configuration
- Verify ngrok tunnel is active

---

## Contributing

1. Fork repository
2. Create feature branch
3. Write tests for new features
4. Ensure all tests pass
5. Submit pull request

### Code Standards

- Python 3.12+ features encouraged
- Type hints required
- Docstrings for public methods
- Integration tests for new flows

---

## License

[Your License Here]

---

## Support

- **Documentation:** [ARCHITECTURE.md](./ARCHITECTURE.md)
- **Issues:** GitHub Issues
- **Logs:** Structured JSON logging enabled

---

## Changelog

### v2.0.0 (2026-07-09) - Production MVP

✅ Removed unused queue infrastructure  
✅ Implemented metadata persistence  
✅ Added observability logging  
✅ Built end-to-end integration tests  
✅ Complete architecture documentation  
✅ Zero dead code

### v1.x - Previous versions

See git history for older releases.
