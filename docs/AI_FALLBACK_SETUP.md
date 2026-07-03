# AI Provider Fallback Configuration

This document explains how the automatic AI provider fallback system works in the Vehicle Diagnosis Assistant.

## Overview

The system supports two AI providers:
- **Cohere** (Primary) - Used for production diagnosis and enrichment
- **Gemini** (Backup) - Automatically used when Cohere fails or is unavailable

## How It Works

### Automatic Fallback Behavior

When `AI_PROVIDER=cohere` is set, the system will:

1. **Try Cohere first** for all AI operations
2. **Detect failures** including:
   - Rate limit errors (429)
   - Service unavailable errors (503)
   - API key issues
   - Model deprecation errors
   - Network timeouts

3. **Automatically switch to Gemini** when:
   - Cohere API fails after retries
   - Cohere returns unchanged results (graceful degradation)
   - Any non-retryable error occurs

4. **Log all fallback events** for monitoring and debugging

### Supported Operations

Both providers support:
- **Cause Ranking** (`rank_causes_with_retry`) - Ranks OBD code causes by likelihood
- **Text Completion** (`complete`) - General AI text generation

## Configuration

### Environment Variables

```bash
# Primary AI Provider
AI_PROVIDER=cohere

# Cohere Configuration
COHERE_API_KEY=your-cohere-api-key
COHERE_MODEL=command-r-plus-08-2024

# Gemini Configuration (Fallback)
GEMINI_API_KEY=AQ.your-gemini-api-key
GEMINI_MODEL=gemini-2.0-flash-exp
```

### Current Configuration

Your `.env` file is configured with:
- **Primary**: Cohere (`command-r-plus-08-2024`)
- **Backup**: Gemini (`gemini-2.0-flash-exp`)
- **API Keys**: Both configured and validated ✅

## Testing

Run the fallback test to verify configuration:

```bash
python test_ai_fallback.py
```

Expected output:
```
[OK] Client initialized
   Primary: cohere
   Backup available: True

[SUCCESS] Ranking successful!
[SUCCESS] Complete successful!
[SUCCESS] All tests passed!
```

## Monitoring

### Log Events

The system logs the following events:

| Event | Description |
|-------|-------------|
| `ai_client_initialized` | Primary provider initialized |
| `ai_backup_initialized` | Backup provider initialized |
| `ai_attempting_backup` | Switching to backup provider |
| `ai_using_backup` | Backup provider being used |
| `ai_backup_success` | Backup provider succeeded |
| `ai_backup_failed` | Backup provider also failed |
| `ai_primary_failed` | Primary provider failed |

### Example Logs

```
2026-07-03 12:13:09 [info] ai_client_initialized provider=cohere
2026-07-03 12:13:09 [info] ai_backup_initialized backup_provider=gemini
2026-07-03 12:13:11 [info] ai_using_backup provider=gemini
2026-07-03 12:13:12 [info] ai_backup_success
```

## Model Selection

### Cohere Models

Recommended models:
- `command-r-plus-08-2024` - Most capable (recommended for production)
- `command-r-08-2024` - Faster, lower cost
- `command-r-plus` - Latest version (may change)

**Note**: `command-r` was deprecated on September 15, 2025

### Gemini Models

Recommended models:
- `gemini-2.0-flash-exp` - Latest experimental (fast)
- `gemini-1.5-pro` - Most capable
- `gemini-1.5-flash` - Balanced speed/quality

## Troubleshooting

### Issue: Backup not initializing

**Symptom**: Log shows `ai_backup_init_failed`

**Solution**: 
1. Verify `GEMINI_API_KEY` is set in `.env`
2. Check API key format (should start with `AQ.`)
3. Ensure `google-genai` package is installed

### Issue: Both providers failing

**Symptom**: Returns original causes unchanged

**Solution**:
1. Check API keys are valid
2. Verify network connectivity
3. Check rate limits haven't been exceeded
4. Review model names are correct

### Issue: Fallback not triggering

**Symptom**: No `ai_using_backup` logs

**Solution**:
1. Ensure `GEMINI_API_KEY` is configured
2. Primary provider may be succeeding (check logs)
3. Verify backup client initialized (`ai_backup_initialized` log)

## Cost Optimization

### Rate Limiting

Both providers have rate limits:

| Provider | Free Tier | Rate Limit |
|----------|-----------|------------|
| Cohere | 1000 calls/month | 20 calls/trial |
| Gemini | 60 requests/min | Varies by region |

### Best Practices

1. **Cache results** - Use the built-in caching system
2. **Monitor usage** - Check `X-Trial-Endpoint-Call-Remaining` headers
3. **Adjust retries** - Reduce `max_retries` if hitting limits
4. **Use appropriate models** - Smaller models for simple tasks

## Implementation Details

### Code Location

- **Main Client**: `app/services/ai_client.py`
- **Cohere Client**: `app/services/cohere_client.py`
- **Gemini Client**: `app/services/gemini_client.py`

### Key Methods

```python
from app.services.ai_client import get_ai_client

# Get client instance
client = get_ai_client()

# Rank causes with automatic fallback
ranked = client.rank_causes_with_retry(
    base_causes=["cause1", "cause2"],
    vehicle_context={"make": "Toyota", "model": "Camry"},
    max_retries=3
)

# Generate text with automatic fallback
response = await client.complete(
    prompt="Explain P0420",
    temperature=0.3,
    max_tokens=1000
)
```

## Future Enhancements

Potential improvements:
- [ ] Add more providers (OpenAI, Anthropic)
- [ ] Implement circuit breaker pattern
- [ ] Add provider health checks
- [ ] Automatic provider selection based on load
- [ ] Cost-based routing
- [ ] Response quality monitoring

## Related Documentation

- [Architecture](ARCHITECTURE.md)
- [Developer Guide](DEVELOPER_GUIDE.md)
- [Cohere Migration](../COHERE_MIGRATION_SUMMARY.md)
