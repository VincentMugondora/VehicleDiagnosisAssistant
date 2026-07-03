# Action Items - Vehicle Diagnosis Assistant

## 🚨 IMMEDIATE (Before Production)

### 1. Fix LLM Provider - CRITICAL
**Issue:** Both Cohere and Gemini are non-functional
- Cohere: Model `command-r-plus` deprecated (removed Sept 2025)
- Gemini: API key is placeholder `AIzaSyxxx` (invalid)

**Impact:** LLM vehicle-specific ranking not working (graceful fallback to generic)

**Choose ONE option:**

#### Option A: Gemini Free Tier (Recommended - $0/month)
```bash
# 1. Get API key
Open: https://makersuite.google.com/app/apikey
Click: "Create API Key"
Copy: Your new API key

# 2. Update .env
GEMINI_API_KEY=<paste-your-real-key-here>
AI_PROVIDER=gemini

# 3. Restart backend
# Windows:
restart_backend.bat

# Or manually:
# Press Ctrl+C in uvicorn terminal
uvicorn app.main:app --reload --port 8000
```

#### Option B: Fix Cohere (Paid ~$0.50-5/month)
```bash
# Update .env
COHERE_MODEL=command-r
AI_PROVIDER=cohere

# Restart backend
restart_backend.bat
```

#### Option C: Disable AI (Use generic enrichment only)
```bash
# Update .env
AI_ENRICH_ENABLED=false

# Restart backend
restart_backend.bat
```

**Time:** 10 minutes  
**Priority:** HIGH

---

### 2. Test LLM Enrichment
```bash
# After fixing API key, test it works:
python test_gemini_enrichment.py

# Expected output:
# [OK] Gemini enrichment appears to be working!
# Ranked Causes:
#   1. (vehicle-specific cause)
#   2. (vehicle-specific cause)
#   ...

# If you see "gemini_failed" or "cohere_failed" in logs:
# - Check API key is correct (no extra spaces/quotes)
# - Check you have internet connection
# - Try option C (disable AI) as fallback
```

**Time:** 5 minutes  
**Priority:** HIGH

---

## ✅ VERIFIED (No Action Needed)

### P0442 Mixed-Input Bug
**Status:** FIXED and stable (tested 3/3 iterations)

Input: `"P0442, fuel odor, Kia Rio 2020"`  
Output: Correct diagnostic with EVAP-specific guidance

**No further action required.**

---

## 📈 RECOMMENDED (Optional Improvements)

### 3. Manual Enrichment Backfill - Top 5 Codes
**Goal:** Upgrade most-searched codes from generic → specific enrichment

**Priority codes (covers ~40-50% of queries):**
1. P0420 - Catalyst Efficiency Bank 1
2. P0171 - System Too Lean Bank 1
3. P0300 - Random/Multiple Cylinder Misfire
4. P0455 - EVAP Large Leak
5. P0128 - Coolant Thermostat

**Process per code:**
```sql
-- Example for P0420:
UPDATE obd_codes 
SET 
  common_causes = 'Degraded catalytic converter (most common - 60% of cases), Faulty downstream O2 sensor (sensor drift), Exhaust leak between engine and converter, Engine running rich from bad MAF sensor, Coolant temp sensor stuck reading cold',
  generic_fixes = 'Check live O2 sensor data (upstream 0.1-0.9V, downstream ~0.45V), Inspect exhaust manifold gaskets and flex pipe for leaks, Test downstream O2 sensor response time with propane enrichment, Check short-term and long-term fuel trims (-10% to +10%), Verify converter reaches 600-900F under load',
  symptoms = 'Check engine light illuminated, No noticeable performance issues, Slight decrease in fuel economy, May fail emissions test'
WHERE code = 'P0420';
```

**Research sources:**
- Repair manuals (Haynes, Chilton, OEM)
- Mechanic forums (Bob Is The Oil Guy, Automotive Forums)
- Technical Service Bulletins (TSBs)
- Commercial databases (Mitchell1, AllData if you have access)

**Time:** 1-2 hours per code (research + testing)  
**Priority:** MEDIUM  
**When:** After LLM provider is working

---

### 4. Monitor Usage Patterns
```bash
# Check which codes are searched most:
# Query Supabase diagnostic_log table
SELECT code, COUNT(*) as searches 
FROM diagnostic_log 
GROUP BY code 
ORDER BY searches DESC 
LIMIT 20;

# Prioritize backfill based on actual usage
```

**Time:** 10 minutes  
**Priority:** LOW  
**When:** After 1-2 weeks of production usage

---

### 5. Set Up Enrichment Contribution Workflow
**Future enhancement:** Allow mechanics to improve enrichment

**Steps:**
1. Add "Suggest Improvement" API endpoint
2. Store suggestions in Supabase
3. Moderator reviews and approves
4. Update database with approved enrichment

**Time:** 4-8 hours development  
**Priority:** LOW  
**When:** After manual top 15 backfill complete

---

## 📊 Current System Status

### Working ✅
- P0442 and all other code lookups
- Generic enrichment (keyword-based fallback)
- WhatsApp webhook (Baileys integration)
- Database queries (Supabase)
- Session management
- Message routing

### Broken ❌
- LLM vehicle-specific ranking (both providers non-functional)

### Safe to Deploy? 
**Yes, with LLM disabled:**
- Set `AI_ENRICH_ENABLED=false` in `.env`
- System falls back to generic enrichment
- Users still get correct diagnostic guidance
- Just not vehicle-ranked

**Better: Deploy with working LLM:**
- Fix API key first (10 min)
- Enables vehicle-specific ranking
- Better user experience

---

## 🎯 Success Criteria

### Before Enabling LLM in Production
- [ ] Valid API key configured (Gemini or Cohere)
- [ ] `python test_gemini_enrichment.py` passes
- [ ] No `gemini_failed` or `cohere_failed` in logs
- [ ] Test query returns vehicle-specific ranked causes

### Before Claiming "Production Ready"
- [ ] LLM working (above)
- [ ] Tested with 10+ real DTC codes
- [ ] Verified WhatsApp integration end-to-end
- [ ] Monitored logs for errors
- [ ] Load tested if expecting high traffic

### Long-Term Quality Goals
- [ ] Top 15 codes have specific enrichment (60-70% coverage)
- [ ] Top 50 codes have specific enrichment (80-90% coverage)
- [ ] Community contribution workflow active
- [ ] Vehicle-specific overrides for common TSBs

---

## 📞 Support

### If LLM Still Not Working After Fix
1. Check logs: `grep "gemini" app.log` or `grep "cohere" app.log`
2. Verify API key in Gemini console: https://makersuite.google.com/app/apikey
3. Test API key with curl:
```bash
curl "https://generativelanguage.googleapis.com/v1beta/models?key=YOUR_API_KEY"
# Should return list of models, not 403 error
```
4. Fallback: Set `AI_ENRICH_ENABLED=false` and deploy without LLM

### If Enrichment Quality Issues
1. Check `analyze_enrichment_simple.py` output
2. Verify code exists: `SELECT * FROM obd_codes WHERE code = 'P0420'`
3. Check causes/fixes not null: Look for empty strings
4. Manual backfill if needed (see step 3 above)

---

## 📝 Quick Reference

### Key Files
- `.env` - Configuration (LLM provider, API keys)
- `app/services/ai_client.py` - LLM provider switcher
- `app/services/obd_service.py` - Generic enrichment logic
- `VERIFICATION_COMPLETE_REPORT.md` - Full audit results
- `ENRICHMENT_BACKFILL_STRATEGY.md` - Long-term improvement plan

### Test Commands
```bash
# Test P0442 fix
python test_p0442_verification.py

# Test Gemini enrichment
python test_gemini_enrichment.py

# Analyze enrichment quality
python analyze_enrichment_simple.py

# Test webhook
curl -X POST http://localhost:8000/webhook/baileys \
  -H "Content-Type: application/json" \
  -d '{"from":"whatsapp:+1234567890","text":"P0420","message_id":"test1"}'
```

---

## ✅ Completion Checklist

### Today (Required)
- [ ] Choose LLM option (A, B, or C)
- [ ] Update `.env` with choice
- [ ] Restart backend
- [ ] Test with `test_gemini_enrichment.py`
- [ ] Verify no errors in logs

### This Week (Recommended)
- [ ] Research P0420 specific enrichment
- [ ] Research P0171 specific enrichment
- [ ] Update database with improved data
- [ ] Test improved responses

### This Month (Optional)
- [ ] Complete top 15 codes backfill
- [ ] Monitor usage patterns
- [ ] Plan community contribution feature

---

**Next Step:** Fix LLM provider (choose option A, B, or C above) ⬆️
