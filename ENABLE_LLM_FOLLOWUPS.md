# Enable LLM Follow-up Conversations — Quick Fix

**Problem:** User asks "I DON'T UNDERSTAND" after diagnosis, gets canned "Send an OBD-II code" message instead of helpful LLM explanation.

---

## Root Cause

**AI enrichment is disabled:**
```
AI_ENRICH_ENABLED=false
```

When disabled, `MessageRouter.ai_client = None`, so follow-up questions fall through to the "no valid input" error message.

**Also:** Your Cohere model `command-r` was deprecated in Sept 2025.

---

## Quick Fix (3 Steps)

### Step 1: Update `.env`

**Change these lines:**
```bash
# OLD (broken)
AI_ENRICH_ENABLED=false
COHERE_MODEL=command-r

# NEW (working)
AI_ENRICH_ENABLED=true
COHERE_MODEL=command-r-plus
```

**What each setting does:**
- `AI_ENRICH_ENABLED=true` → Enables LLM for follow-up questions
- `COHERE_MODEL=command-r-plus` → Uses current Cohere model (not deprecated)

---

### Step 2: Restart Server

```bash
# Stop current server (Ctrl+C)
.\start_backend.bat
```

---

### Step 3: Test

**Send via WhatsApp:**
```
P0507
```

**Bot responds with diagnosis** (should already work) ✅

**Then send:**
```
I don't understand
```

**Bot should now:**
- Recognize you're asking about P0507
- Use LLM to explain in simpler terms
- Reference the previous diagnosis context

---

## How Follow-up Works (Technical)

### Flow Diagram

```
User: "P0507"
  ↓
Bot: [Diagnosis with causes/checks]
  ↓
Session stores: last_diagnosis = {code: "P0507", description: "...", vehicle: "..."}
  ↓
User: "I don't understand"
  ↓
MessageRouter checks:
  1. Is there a code? No
  2. Is AI enabled? YES (after fix)
  3. Is there last_diagnosis in session? YES
  ↓
MessageRouter builds prompt:
  "Previous diagnosis: P0507 - Idle Control System RPM High
   Vehicle: Not specified
   User's question: I don't understand
   Provide a helpful response."
  ↓
Cohere LLM generates natural explanation
  ↓
Bot: [Natural language explanation]
```

### Code Location

**File:** `app/services/message_router.py` (lines 133-166)

```python
# Route 2: Free-text followup with context
if session and session.last_diagnosis and self.ai_client:
    # Build context from last diagnosis
    context = f"""Previous diagnosis context:
- OBD Code: {session.last_diagnosis.code}
- Issue: {session.last_diagnosis.description}
- Vehicle: {session.last_diagnosis.vehicle_context or 'Not specified'}

User's followup question: {raw_text}

Provide a helpful response based on the previous diagnosis context."""

    response = await self.ai_client.complete(
        prompt=context,
        temperature=0.3,
        max_tokens=500
    )

    return {
        "reply": response,
        "type": "followup_response"
    }
```

**This code already exists** — it just needs `AI_ENRICH_ENABLED=true` to activate.

---

## Alternative: Gemini API

If you prefer Google's Gemini over Cohere:

```bash
# In .env
AI_PROVIDER=gemini
AI_ENRICH_ENABLED=true
GEMINI_API_KEY=your-key-here
```

Your code already supports both providers.

---

## Cost Considerations

**Cohere Pricing (2026):**
- `command-r-plus`: ~$3 per 1M input tokens
- Follow-up query: ~200 tokens input + 500 tokens output = ~$0.0035 per conversation

**Estimated cost:**
- 100 follow-up questions/day = $0.35/day = $10.50/month
- 1000 follow-up questions/day = $3.50/day = $105/month

**Recommendation:** Start with `AI_ENRICH_ENABLED=true` and monitor usage.

---

## Session Memory

The system remembers:
- **Last diagnosis** for 24 hours (configurable)
- User can ask multiple follow-ups:
  - "What's the most common cause?"
  - "How much will this cost to fix?"
  - "Can I drive with this code?"
  - "What tools do I need?"

Each follow-up includes context from the original diagnosis.

---

## Testing Examples

### Example 1: Explanation Request
```
User: P0171
Bot: [Full diagnosis with causes/checks]

User: explain in simple terms
Bot: "P0171 means your engine is running 'lean' - it's getting too much 
air or not enough fuel. Think of it like a campfire that's getting too 
much wind - it burns poorly. The most common causes are vacuum leaks 
(unwanted air getting in) or a dirty mass air flow sensor..."
```

### Example 2: Cost Question
```
User: P0420
Bot: [Catalyst diagnosis]

User: how much to fix?
Bot: "P0420 repair costs vary widely depending on the cause:
- If it's just O2 sensors: $200-400
- If the catalytic converter needs replacement: $1,000-2,500
- Some causes (exhaust leaks, engine running rich) may be cheaper to fix
I'd recommend getting a proper diagnosis first to avoid replacing the 
expensive cat unnecessarily..."
```

### Example 3: Multiple Follow-ups
```
User: P0300
Bot: [Misfire diagnosis]

User: which cause is most likely?
Bot: "For P0300 (random misfire), bad spark plugs are the most common..."

User: how do i check spark plugs?
Bot: "To check spark plugs: 1. Remove one at a time using a spark plug 
socket, 2. Look for signs of wear, carbon buildup, or damage..."
```

---

## Monitoring

After enabling, check logs for:

```
[info] routing_to_followup_with_context   last_code=P0507
[info] cohere_request                     model=command-r-plus
[info] cohere_response_received           tokens=342
```

If you see errors:
```
[error] cohere_generate_failed            error=model 'command-r' was removed...
```
→ Update `COHERE_MODEL=command-r-plus` in `.env`

---

## Rollback

If you want to disable follow-ups again:

```bash
# In .env
AI_ENRICH_ENABLED=false
```

Restart server. Users will get the canned "Send an OBD-II code" message again.

---

## Summary

**Change 2 lines in `.env`:**
```bash
AI_ENRICH_ENABLED=true
COHERE_MODEL=command-r-plus
```

**Restart server:**
```bash
.\start_backend.bat
```

**Test:**
```
WhatsApp → P0507
WhatsApp → I don't understand
```

**Expected:** Natural language explanation from LLM ✅

---

**Prepared by:** Claude Code  
**Date:** 2026-07-03  
**Status:** Ready to implement
