# Enable AI Enrichment Fix

**Date:** 2026-07-10
**Issue:** OBD codes returning basic info without enrichment (symptoms, causes, diagnostic steps, technician tips)

---

## Problem

Users were receiving bare-bones responses like this:

```
🔧 Fault Code: P0563
System: Powertrain
📖 What it means: System Voltage High
⚠️ Severity: High
```

Instead of fully enriched responses with:
- ✅ Detailed description
- ✅ Common symptoms
- ✅ Possible causes
- ✅ Diagnostic steps
- ✅ Technician tips
- ✅ Pre-replacement checks

### Root Cause

The `.env` file had:
```env
AUTO_LEARN_CODES=false
```

This disabled the AI enrichment system entirely.

### Logs Showing the Issue

```
enrichment_needed code=P0563 missing_causes=True missing_checks=True missing_symptoms=True
enrichment_skipped code=P0563 reason=ai_not_available
```

Even though:
- ✅ Cohere AI client initialized successfully
- ✅ Database connection working
- ✅ Code exists in database

The enrichment was skipped because `auto_learn_codes=False`.

---

## Solution

Changed `.env` to enable auto-learning:

```env
# Before
AUTO_LEARN_CODES=false

# After
AUTO_LEARN_CODES=true
```

### How It Works

**webhook.py:**
```python
def get_message_router(repos: dict = Depends(get_repositories)):
    ai_client = None
    if settings.auto_learn_codes:  # <-- This was False
        try:
            ai_client = AIClient()  # Now initializes
        except:
            pass

    obd_service = OBDService(
        repos["obd_repo"],
        ai_client=ai_client,        # Now has AI client
        auto_learn=settings.auto_learn_codes  # Now True
    )
    return MessageRouter(obd_service)
```

**obd_service.py:**
```python
# Check if enrichment needed and AI available
if needs_enrichment and self.auto_learn and self.code_generator:
    # Now ALL three conditions are True:
    # ✅ needs_enrichment (P0563 missing fields)
    # ✅ self.auto_learn (now True from settings)
    # ✅ self.code_generator (now initialized with AIClient)
    enriched = await self._enrich_and_save(code, base)
```

---

## Expected Behavior After Fix

### Before (AUTO_LEARN_CODES=false)

**Query:** P0563

**Response:**
```
🔧 Fault Code: P0563
System: Powertrain
📖 What it means: System Voltage High
⚠️ Severity: High

This code can lead to engine damage if left unaddressed.
```

### After (AUTO_LEARN_CODES=true)

**Query:** P0563

**Response:**
```
🔧 Fault Code: P0563
System: Powertrain

📖 What it means
The engine control module (ECM) has detected that the charging system voltage
is higher than expected. Normal operating voltage is typically 13.5-14.5V.
This code triggers when voltage exceeds approximately 16V.

⚠️ Severity: High
High charging voltage can damage electronic components, cause premature bulb
failure, and boil battery electrolyte. Address this issue promptly to avoid
expensive electrical system damage.

🔍 Common Symptoms
* Battery warning light illuminated
* Headlights unusually bright
* Electrical accessories behaving erratically
* Battery boiling/overheating
* Burnt smell from electrical components
* Premature bulb failures

🛠️ Possible Causes
* Faulty voltage regulator
* Defective alternator
* Damaged wiring to alternator
* Corroded battery terminals
* Faulty PCM/ECM (rare)

✅ Recommended Diagnostic Steps
1. Measure battery voltage with engine running (should be 13.5-14.5V)
2. Inspect alternator wiring and connectors for damage
3. Test voltage regulator operation
4. Check for aftermarket electrical modifications
5. Inspect battery condition and terminals

🔧 Technician Tip
Start by measuring voltage at the battery with engine running at idle and at
2000 RPM. If voltage exceeds 15.5V, the voltage regulator is the most likely
culprit. Many modern vehicles have the regulator built into the alternator.

🔎 Before Replacing Parts
* Verify battery terminals are clean and tight
* Check for aftermarket accessories drawing excessive current
* Inspect alternator wiring harness for damage
* Test battery condition (weak battery can cause overcharging)
```

---

## Deployment

### 1. Update .env File

Already done:
```bash
sed -i 's/^AUTO_LEARN_CODES=false/AUTO_LEARN_CODES=true/' .env
```

### 2. Restart Application

```bash
# Stop current process (Ctrl+C if running in foreground)

# Restart
python -m app.main

# Or if using uvicorn
uvicorn app.main:app --reload
```

### 3. Test Enrichment

Send a test code via WhatsApp:
```
P0563
```

Expected log output:
```
enrichment_needed code=P0563 missing_causes=True ...
ai_enrichment_started code=P0563
ai_enrichment_success code=P0563
code_saved_to_db code=P0563
```

### 4. Verify Response Quality

The response should now include:
- ✅ Detailed "What it means" section
- ✅ Common symptoms (4-7 bullet points)
- ✅ Possible causes (5-8 bullet points)
- ✅ Diagnostic steps (numbered checklist)
- ✅ Technician tip
- ✅ Pre-replacement checks

---

## Configuration Options

### .env Variables

```env
# Enable/disable AI enrichment
AUTO_LEARN_CODES=true

# AI Provider (cohere or gemini)
AI_PROVIDER=cohere

# Cohere API Key
COHERE_API_KEY=your_key_here

# Optional: Gemini API Key (used as backup)
GEMINI_API_KEY=your_key_here
```

### When to Disable AUTO_LEARN_CODES

Set to `false` when:
- Running in development without AI credits
- Testing basic database lookups only
- Debugging without AI overhead
- Running cost-sensitive load tests

### Cost Implications

**AUTO_LEARN_CODES=true:**
- First lookup of each code: ~1,000-2,000 tokens (enrichment)
- Subsequent lookups: 0 tokens (cached in database)
- Average cost per new code: ~$0.001-0.003 (Cohere pricing)

**AUTO_LEARN_CODES=false:**
- All lookups: 0 tokens
- Responses are basic (description + severity only)
- No dynamic learning

---

## Monitoring

### Check Enrichment Success Rate

```bash
# Count enrichments today
grep "ai_enrichment_success" app.log | grep "$(date +%Y-%m-%d)" | wc -l

# Count enrichment failures
grep "ai_enrichment_failed" app.log | grep "$(date +%Y-%m-%d)"
```

### Check Cost Tracking

```bash
# Total tokens used today
grep "ai_response_received" app.log | grep "$(date +%Y-%m-%d)" | \
  grep -oP 'input_tokens=\K[0-9]+|output_tokens=\K[0-9]+' | \
  awk '{s+=$1} END {print s}'
```

---

## Troubleshooting

### Issue: Still Not Enriching After Restart

**Check:**
```bash
# Verify setting loaded
grep AUTO_LEARN .env

# Check logs for AI client initialization
grep "ai_client_initialized" app.log | tail -1
```

**Expected:**
```
ai_client_initialized provider=cohere
```

### Issue: Enrichment Failing

**Check logs:**
```bash
grep "ai_enrichment_failed" app.log | tail -5
```

**Common causes:**
- Invalid COHERE_API_KEY
- Rate limit exceeded
- Network timeout

### Issue: Cohere API Key Invalid

Update `.env`:
```env
COHERE_API_KEY=your_valid_key_here
```

Get key from: https://dashboard.cohere.com/api-keys

---

## Related Files

- ✅ `.env` - Changed `AUTO_LEARN_CODES=false` → `true`
- 📖 `app/api/routes/webhook.py` - AI client initialization
- 📖 `app/services/obd_service.py` - Enrichment logic
- 📖 `app/core/config.py` - Settings definition

---

## Next Steps

1. ✅ Enable AUTO_LEARN_CODES in .env
2. 🔲 Restart application
3. 🔲 Test with P0563 or any code
4. 🔲 Verify enriched response received
5. 🔲 Monitor enrichment success rate for 24 hours
6. 🔲 Implement Phase 3: Enhanced Severity Metadata

The enrichment system should now work as designed!
