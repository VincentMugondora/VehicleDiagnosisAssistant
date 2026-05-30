# Cohere AI Integration Guide

The Vehicle Diagnosis Assistant now supports **Cohere** as the AI provider for ranking OBD causes!

---

## Why Cohere?

- **Fast inference** - Quick response times
- **Reliable API** - Stable and well-documented
- **Cost-effective** - Competitive pricing
- **Command-R model** - Optimized for reasoning tasks

---

## Quick Setup

### 1. Update Environment Variables

Your `.env` file should have:

```bash
# AI Provider
AI_PROVIDER=cohere

# Cohere API
COHERE_API_KEY=your-cohere-api-key-here
COHERE_MODEL=command-r

# Enable AI enrichment
AI_ENRICH_ENABLED=true
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs the Cohere Python SDK:
```
cohere>=5.0,<6.0
```

### 3. Test It

```bash
# Start server
uvicorn app.main:app --reload --port 8000

# Test with OBD code
curl -X POST http://localhost:8000/webhook/baileys \
  -H "Content-Type: application/json" \
  -d '{
    "from": "whatsapp:+1234567890",
    "text": "P0420 Toyota Camry 2015",
    "message_id": "test123"
  }'
```

Check logs for:
```json
{"event": "ai_client_initialized", "provider": "cohere"}
{"event": "cohere_request", "attempt": 1, ...}
{"event": "cohere_success", "ranked_count": 5}
{"event": "ai_enrichment_applied", "code": "P0420", "provider": "cohere"}
```

---

## Features

### ✅ Automatic Cause Ranking

Cohere analyzes OBD causes and ranks them by likelihood for the specific vehicle:

**Before AI:**
```
Likely causes:
• Worn catalytic converter
• Faulty rear O2 sensor
• Exhaust leak before sensor
• Vacuum leak
• Fuel injector issues
```

**After Cohere ranking:**
```
Likely causes:
• Worn catalytic converter (most common for 2015 Camry)
• Faulty rear O2 sensor
• Exhaust leak before sensor
```

### ✅ Retry Logic

- Automatic retry on rate limits (429)
- Exponential backoff (1s, 2s, 4s)
- Graceful fallback to original causes

### ✅ Vehicle-Specific

Cohere considers:
- Make (Toyota)
- Model (Camry)
- Year (2015)
- Engine (1.6L)

---

## Switching Between Providers

### Use Cohere (Default)
```bash
AI_PROVIDER=cohere
COHERE_API_KEY=your-key-here
AI_ENRICH_ENABLED=true
```

### Use Gemini (Legacy)
```bash
AI_PROVIDER=gemini
GEMINI_API_KEY=your-key-here
AI_ENRICH_ENABLED=true
```

### Disable AI Enrichment
```bash
AI_ENRICH_ENABLED=false
```

No code changes needed - just update `.env` and restart!

---

## Supported Models

### Cohere Models
- `command-r` (recommended) - Optimized for reasoning
- `command-r-plus` - More powerful, higher cost
- `command` - Legacy model

### Gemini Models (if using Gemini)
- `gemini-1.5-flash` (default)
- `gemini-1.5-pro`

---

## Architecture

```
Message → MessageRouter → OBDService (lookup)
                             ↓
                        DiagnosticResult
                             ↓
         AIClient (Cohere/Gemini) ← AI_PROVIDER config
                             ↓
                    Ranked causes
                             ↓
                    Updated DiagnosticResult
                             ↓
                    WhatsApp response
```

---

## Cost Comparison

| Provider | Model | Cost per 1M tokens | Speed |
|----------|-------|-------------------|-------|
| **Cohere** | command-r | $0.15 input, $0.60 output | Fast |
| **Gemini** | gemini-1.5-flash | $0.075 input, $0.30 output | Very fast |

For this use case (short prompts, short responses), both are very affordable (~$0.001 per diagnosis).

---

## Monitoring

Check logs for AI performance:

```bash
# Successful requests
grep "cohere_success" app.log

# Failed requests
grep "cohere_failed" app.log

# Average response time
grep "cohere_request" app.log | grep -o "attempt":[0-9]+ | awk '{sum+=$2; count++} END {print sum/count}'
```

---

## Troubleshooting

### "COHERE_API_KEY not set"
- Check `.env` file has `COHERE_API_KEY=...`
- Restart server after updating `.env`

### "Unsupported AI provider"
- Set `AI_PROVIDER=cohere` (not "Cohere" or "COHERE")
- Check spelling in `.env`

### "cohere_failed" in logs
- Check API key is valid
- Verify internet connectivity
- Check Cohere API status: https://status.cohere.com

### AI not ranking causes
- Enable with `AI_ENRICH_ENABLED=true`
- Check logs for "ai_client_initialized"
- Verify Cohere client initialized without errors

---

## API Key Security

⚠️ **Never commit API keys to git!**

✅ Use `.env` file (already in `.gitignore`)  
✅ Use environment variables in production  
✅ Rotate keys regularly  
✅ Monitor usage in Cohere dashboard  

---

## Next Steps

1. ✅ Setup complete - Cohere is now your AI provider
2. Test with real OBD codes
3. Monitor logs for performance
4. Adjust `COHERE_MODEL` if needed
5. Enable in production

---

## Support

- **Cohere Docs**: https://docs.cohere.com
- **API Status**: https://status.cohere.com
- **Dashboard**: https://dashboard.cohere.com

---

**Ready to go! 🚀**

Your Vehicle Diagnosis Assistant now uses Cohere AI to provide intelligent, vehicle-specific cause rankings!
