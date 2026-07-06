# Gemini Backup - Quick Start Guide

## ✅ Current Status

Your Gemini backup is **configured and working**.

## 📋 Configuration

```bash
# Primary Provider
AI_PROVIDER=cohere

# Backup Provider (automatic)
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-2.0-flash-exp
```

## 🧪 Test It

```bash
python test_ai_fallback.py
```

Expected: `[SUCCESS] All tests passed!`

## 🔍 How It Works

```
Request → Cohere (primary)
              ↓ if fails
          Gemini (backup) → Response
```

## 📊 Monitor Logs

```bash
# Watch for fallback events
grep -E "ai_(backup|using|primary)" logs/app.log
```

Key log events:
- `ai_backup_initialized` - Backup ready ✅
- `ai_using_backup` - Switched to Gemini
- `ai_backup_success` - Gemini worked

## 🚨 Troubleshooting

| Issue | Solution |
|-------|----------|
| No backup available | Check `GEMINI_API_KEY` in `.env` |
| Backup not working | Verify model: `gemini-2.0-flash-exp` |
| Both failing | Check internet + API keys valid |

## 📚 Full Documentation

See: `docs/AI_FALLBACK_SETUP.md`

## 🎯 When Fallback Activates

Automatically switches to Gemini on:
- Rate limits (429)
- Service errors (503)
- Timeouts
- API failures
- Model deprecation

## ✨ No Code Changes Needed

All existing code works automatically with backup:
```python
from app.services.ai_client import get_ai_client

client = get_ai_client()
# Automatically uses Cohere → Gemini fallback
result = client.rank_causes_with_retry(...)
```

---

**Status**: ✅ Ready to use  
**Last Updated**: July 3, 2026
