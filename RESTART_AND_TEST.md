# Quick Start: Restart & Test

## Step 1: Restart Server

**Stop current server:**
- Go to the terminal running `start_backend.bat`
- Press `Ctrl+C`

**Start again:**
```bash
.\start_backend.bat
```

**Wait for:**
```
INFO:     Application startup complete.
[info] supabase_connected
[info] ai_client_initialized  provider=cohere
```

✅ Server ready!

---

## Step 2: Test (3 Minutes)

### Test A: Enrichment
**Send via WhatsApp:**
```
P0171
```

**Check response has:**
- ✅ "Vacuum leak" in causes
- ✅ "Inspect for vacuum leaks" in checks
- ✅ NOT blank sections

---

### Test B: LLM Follow-up (NEW!)
**Send via WhatsApp:**
```
P0507
```

**Wait for diagnosis, then send:**
```
explain in simple terms
```

**Check response:**
- ✅ Natural language (not "Send an OBD-II code")
- ✅ References P0507 / idle issue
- ✅ Conversational tone

---

### Test C: Mixed Input
**Send via WhatsApp:**
```
P0442, fuel odor, Kia Rio 2020
```

**Check response:**
- ✅ EVAP diagnosis appears
- ✅ No error message
- ✅ Has causes/checks

---

## Step 3: Verify Logs

**Check terminal for:**

```
[info] baileys_webhook_received
[info] message_parsed            code=P0507
[info] routing_to_code_diagnosis
[info] obd_lookup_success        source=local_db
```

**For follow-up:**
```
[info] routing_to_followup_with_context  last_code=P0507
[info] cohere_request                     model=command-r-plus
```

**No errors like:**
```
[error] message_routing_failed       ← Should NOT see this
[error] cohere_generate_failed       ← Should NOT see this
```

---

## Done! ✅

If all 3 tests pass:
- ✅ Enrichment working
- ✅ LLM responding to questions
- ✅ Error handling robust

**Your bot is production-ready!** 🚀

---

## Quick Reference

**To ask bot questions:**
- After any code (P0507, P0420, etc.)
- Send: "explain", "I don't understand", "what's the cost", "can I drive"
- Bot uses context from last diagnosis

**To test specific codes:**
- `P0171` → Fuel/air system (lean)
- `P0300` → Misfire
- `P0420` → Catalyst
- `P0442` → EVAP leak
- `P0507` → High idle

**If something breaks:**
1. Check `ALL_ISSUES_RESOLVED.md` troubleshooting section
2. Check server logs for errors
3. Verify `.env` settings match the guide
