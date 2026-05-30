# 🚗 Vehicle Diagnosis Assistant

> AI-powered OBD-II diagnostic trouble code assistant with WhatsApp integration and dynamic learning capabilities.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A production-ready vehicle diagnostic system that helps users understand OBD-II error codes through WhatsApp. Features AI-powered cause ranking, vehicle-specific diagnostics, and automatic code learning from real user requests.

## ✨ Features

### Core Capabilities
- 🔍 **132+ Pre-loaded OBD Codes** - Comprehensive coverage of common diagnostic codes
- 🤖 **AI-Powered Auto-Learn** - Automatically generates and saves new codes using Cohere AI
- 📱 **WhatsApp Integration** - Works with both Twilio and Baileys
- 🎯 **Smart Diagnosis** - Two modes: code lookup and symptom-based diagnosis
- 🚙 **Vehicle-Specific Insights** - Tailored responses based on make/model/year
- 📊 **Usage Analytics** - Track diagnostics, popular codes, and user engagement
- 🔒 **Rate Limiting** - Configurable per-user limits
- 💾 **Persistent Sessions** - Conversation context maintained across messages

### Auto-Learn Feature 🧠
When users ask about codes not in the database:
1. **AI Generation** - Cohere generates complete diagnostic information
2. **Structured Data** - Validates and formats as clean JSON
3. **Auto-Save** - Stores to Supabase for future users
4. **Self-Improving** - Database grows organically from real usage

Result: **No dead ends** - every code gets a detailed answer!

### Supported Systems
- ✅ **Powertrain (P)** - Engine, transmission, fuel, emissions (102 codes)
- ✅ **Chassis (C)** - ABS, brakes, suspension (8 codes)
- ✅ **Body (B)** - Airbags, electrical, comfort (11 codes)
- ✅ **Network (U)** - CAN bus, module communication (10 codes)

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Supabase account (free tier works)
- Cohere API key (free tier: 1000 calls/month)
- WhatsApp integration (Twilio or Baileys)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/VincentMugondora/VehicleDiagnosisAssistant.git
   cd VehicleDiagnosisAssistant
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   .\venv\Scripts\activate
   
   # Mac/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials (see Configuration section)
   ```

5. **Setup database**
   ```bash
   # Run Supabase migrations
   # See supabase/migrations/001_initial_schema.sql
   ```

6. **Import OBD codes**
   ```bash
   python scripts/import_obd_datasets.py
   ```

7. **Run the server**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

🎉 Server running at `http://localhost:8000`!

## ⚙️ Configuration

### Required Settings

Create a `.env` file with these required variables:

```bash
# Supabase Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key

# AI Provider (for auto-learn and ranking)
AI_PROVIDER=cohere  # or "gemini"
COHERE_API_KEY=your-cohere-api-key
COHERE_MODEL=command-r-plus

# WhatsApp Integration (choose one)
# Option 1: Twilio
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886

# Option 2: Baileys (for custom WhatsApp integration)
BAILEYS_API_KEY=your-baileys-api-key
```

### Optional Settings

```bash
# Feature Flags
AUTO_LEARN_CODES=true          # Enable dynamic code learning
AI_ENRICH_ENABLED=false        # Enable AI-powered cause ranking
INTERNET_FALLBACK_ENABLED=true # Enable web fallback (legacy)

# Rate Limiting
USAGE_LIMIT_PER_NUMBER=20      # Max messages per user
USAGE_LIMIT_WINDOW_DAYS=30     # Time window for limits

# Session Management
SESSION_TTL_SECONDS=1800       # 30 minutes
MAX_CONVERSATION_TURNS=10      # Max messages per session

# Response Formatting
REPLY_MAX_CAUSES=5             # Max causes to show
REPLY_MAX_CHECKS=5             # Max diagnostic steps to show
REPLY_MAX_CODES=3              # Max suggested codes
```

## 📖 Usage

### Via WhatsApp

**Code Lookup:**
```
User: P0420
Bot: 
Code: P0420
Description: Catalyst System Efficiency Below Threshold

Symptoms:
• Check engine light on
• Failed emissions test
• Reduced performance

Likely causes:
• Failing catalytic converter
• Faulty oxygen sensors
• Exhaust leak

Next steps:
1. Test O2 sensors first (cheaper fix)
2. Check for exhaust leaks
3. Replace catalytic converter if needed

Severity: Medium
Confidence: 85%
```

**With Vehicle Context:**
```
User: P0420 on my 2015 Toyota Camry 2.5L
Bot: [Vehicle-specific diagnostic info with known issues]
Confidence: 98%
```

**Symptom-Based:**
```
User: My car is running rough and shaking at idle
Bot: [Suggests probable codes like P0300-P0308]
```

### Via API

**Direct API Call:**
```bash
curl -X POST http://localhost:8000/webhook/baileys \
  -H "Content-Type: application/json" \
  -d '{
    "from": "1234567890",
    "text": "P0420",
    "message_id": "unique-id"
  }'
```

**Response:**
```json
{
  "reply": "Code: P0420\n\nDescription: Catalyst System...",
  "status": "success"
}
```

## 🏗️ Architecture

### Tech Stack
- **Backend**: FastAPI (Python)
- **Database**: Supabase (PostgreSQL)
- **AI**: Cohere (primary) / Gemini (legacy)
- **Messaging**: Twilio / Baileys (WhatsApp)
- **Logging**: Structlog

### Project Structure
```
VehicleDiagnosisAssistant/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   └── webhook.py          # WhatsApp webhook handlers
│   │   └── formatters.py           # Response formatting
│   ├── core/
│   │   ├── config.py                # Settings & environment
│   │   ├── errors.py                # Custom exceptions
│   │   └── logging.py               # Structured logging
│   ├── db/
│   │   └── client.py                # Supabase client
│   ├── models/
│   │   ├── diagnostic.py            # Data models
│   │   └── webhook.py               # Webhook payloads
│   ├── repositories/
│   │   ├── obd_repository.py        # OBD code database access
│   │   ├── session_repository.py   # Session management
│   │   └── message_log_repository.py
│   ├── services/
│   │   ├── obd_service.py           # Core diagnostic logic
│   │   ├── ai_code_generator.py    # AI auto-learn feature
│   │   ├── ai_client.py             # Unified AI client
│   │   ├── cohere_client.py         # Cohere integration
│   │   ├── message_router.py        # Message routing logic
│   │   └── session_manager.py       # Session handling
│   └── utils/
│       ├── obd_parser.py            # Message parsing
│       └── phone.py                 # Phone number hashing
├── scripts/
│   ├── comprehensive_obd_codes.py   # 132 code dataset
│   ├── import_obd_datasets.py       # Database importer
│   ├── test_code_coverage.py        # Dataset analysis
│   └── verify_codes_online.py       # Quality verification
├── supabase/
│   └── migrations/
│       └── 001_initial_schema.sql   # Database schema
├── docs/
│   ├── AUTO_LEARN_FEATURE.md        # Auto-learn documentation
│   ├── OBD_CODES_REFERENCE.md       # Complete code reference
│   └── COMMON_CODES_QUICK_REFERENCE.md
├── .env.example                      # Environment template
├── requirements.txt                  # Python dependencies
└── README.md                         # This file
```

### Database Schema

**Tables:**
- `obd_codes` - OBD-II code knowledge base (132+ codes, growing)
- `message_logs` - Message audit trail
- `diagnostic_logs` - Diagnostic analytics
- `conversation_sessions` - User session state
- `vehicle_overrides` - Vehicle-specific known issues
- `external_obd_cache` - External API response cache

### Key Components

**1. OBD Service** (`obd_service.py`)
- Code lookup with vehicle-specific overrides
- Auto-learn integration for unknown codes
- Confidence scoring (30%-98%)

**2. AI Code Generator** (`ai_code_generator.py`)
- Generates complete code information using Cohere
- Validates and structures data
- Auto-saves to database

**3. Message Router** (`message_router.py`)
- Routes to code lookup or symptom diagnosis
- Parses vehicle context from messages
- Handles session management

**4. Session Manager** (`session_manager.py`)
- Maintains conversation state
- Idempotency checking
- TTL-based expiration

## 🧪 Testing

### Run Tests
```bash
# Unit tests
pytest tests/

# Coverage report
pytest --cov=app tests/

# Specific test file
pytest tests/test_obd_service.py -v
```

### Test Auto-Learn Feature
```bash
# Test with rare code
python scripts/test_web_fetcher.py

# Verify code coverage
python scripts/test_code_coverage.py

# Validate against standards
python scripts/verify_codes_online.py
```

### Manual Testing
```bash
# Start server
uvicorn app.main:app --reload

# Send test message
curl -X POST http://localhost:8000/webhook/baileys \
  -H "Content-Type: application/json" \
  -d '{"from": "test", "text": "P3499", "message_id": "test1"}'
```

## 📊 Monitoring & Analytics

### View Logs
```bash
# Real-time logs
tail -f logs/app.log

# Error logs only
grep "error" logs/app.log

# Auto-learn activity
grep "ai_code_generation_started" logs/app.log
```

### Database Queries

**Most Popular Codes:**
```sql
SELECT code, COUNT(*) as count
FROM diagnostic_logs
GROUP BY code
ORDER BY count DESC
LIMIT 10;
```

**Auto-Learned Codes:**
```sql
SELECT code, description, created_at
FROM obd_codes
WHERE created_at > NOW() - INTERVAL '7 days'
ORDER BY created_at DESC;
```

**Usage Statistics:**
```sql
SELECT 
  DATE(created_at) as date,
  COUNT(*) as messages,
  COUNT(DISTINCT phone_hash) as unique_users
FROM message_logs
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

## 🔒 Security

### API Keys
- ✅ `.env` file in `.gitignore` (never committed)
- ✅ Phone numbers hashed with SHA-256
- ✅ Twilio signature verification
- ✅ Rate limiting per user
- ✅ Idempotency checking

### Best Practices
1. **Rotate API keys** regularly
2. **Use service role key** for Supabase (not anon key)
3. **Enable signature validation** for Twilio
4. **Monitor usage limits** to prevent abuse
5. **Review auto-learned codes** weekly for quality

## 🚀 Deployment

### Docker (Recommended)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Build
docker build -t vehicle-diagnosis .

# Run
docker run -p 8000:8000 --env-file .env vehicle-diagnosis
```

### Cloud Platforms

**Railway:**
```bash
# Install CLI
npm install -g @railway/cli

# Deploy
railway login
railway init
railway up
```

**Render:**
1. Connect GitHub repo
2. Set environment variables
3. Deploy automatically on push

**Heroku:**
```bash
heroku create your-app-name
heroku config:set SUPABASE_URL=...
git push heroku master
```

### Environment Variables
Ensure all variables from `.env.example` are set in your deployment platform.

## 📈 Performance

### Benchmarks
- **Code lookup** (in DB): ~50ms
- **Auto-learn** (new code): ~2-3s
  - AI generation: ~1-1.5s
  - Database save: ~0.5s
  - Response to user: ~1s
- **Subsequent lookups**: ~50ms (cached in DB)

### Optimization Tips
1. **Database indexes** - Added on frequently queried fields
2. **Caching** - Auto-learned codes cached permanently
3. **Batch operations** - Import codes in batches of 100
4. **Async operations** - All I/O operations are async

## 🤝 Contributing

Contributions welcome! Here's how:

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
4. **Run tests**
   ```bash
   pytest tests/
   ```
5. **Commit your changes**
   ```bash
   git commit -m "feat: add amazing feature"
   ```
6. **Push to branch**
   ```bash
   git push origin feature/amazing-feature
   ```
7. **Open a Pull Request**

### Code Style
- Follow PEP 8
- Use type hints
- Add docstrings to functions
- Write tests for new features

## 📝 Changelog

### v2.0.0 (2026-05-30)
- ✨ Added auto-learn feature with AI code generation
- ✨ Expanded dataset to 132 verified codes
- 🔧 Switched from Gemini to Cohere for better quality
- 📚 Added comprehensive documentation
- 🐛 Fixed async/await issues
- 🔒 Removed API keys from git history

### v1.0.0 (2026-01-15)
- 🎉 Initial release
- ✅ WhatsApp integration (Twilio)
- ✅ Basic code lookup
- ✅ Symptom-based diagnosis
- ✅ Session management

## 🐛 Troubleshooting

### Common Issues

**"COHERE_API_KEY not set"**
- Check `.env` file exists
- Verify key is correct
- Restart server after changes

**"Model not found" error**
- Use valid model: `command-r-plus`, `command-r`, or `command-light`
- Update `COHERE_MODEL` in `.env`

**Auto-learn not working**
- Verify `AUTO_LEARN_CODES=true` in `.env`
- Check Cohere API key is valid
- Review logs for specific errors

**Database connection failed**
- Verify Supabase URL and key
- Check network connectivity
- Ensure migrations are run

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/VincentMugondora/VehicleDiagnosisAssistant/issues)
- **Discussions**: [GitHub Discussions](https://github.com/VincentMugondora/VehicleDiagnosisAssistant/discussions)
- **Email**: vincent.mugondora@example.com

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details

## 🙏 Acknowledgments

- **OBD-II Standards** - SAE J2012
- **Cohere** - AI code generation
- **Supabase** - Database platform
- **FastAPI** - Web framework
- **Twilio** - WhatsApp API

## 🗺️ Roadmap

### Coming Soon
- [ ] Multi-language support (Spanish, French, Portuguese)
- [ ] Mobile app (React Native)
- [ ] Cost estimates for repairs
- [ ] Diagnostic flowcharts
- [ ] Integration with car scanners (Bluetooth OBD-II)
- [ ] Admin dashboard for code management
- [ ] Community voting on code quality
- [ ] Vehicle maintenance tracking

### Future Ideas
- [ ] Machine learning for better diagnosis
- [ ] Integration with repair shops
- [ ] Parts marketplace integration
- [ ] DIY repair video guides
- [ ] Recall check integration
- [ ] Insurance claim assistance

## 📊 Stats

- **132+ OBD Codes** in database
- **4 Systems** covered (Powertrain, Chassis, Body, Network)
- **95%+ Coverage** of common user codes
- **100% Complete** entries (all fields filled)
- **Auto-Learning** from unlimited codes via AI

---

<div align="center">

**Built with ❤️ for mechanics, car owners, and automotive enthusiasts**

⭐ Star this repo if you find it helpful!

[Report Bug](https://github.com/VincentMugondora/VehicleDiagnosisAssistant/issues) · 
[Request Feature](https://github.com/VincentMugondora/VehicleDiagnosisAssistant/issues) · 
[Documentation](docs/)

</div>
