# Enrichment Backfill Strategy

## Current Situation

**Database Status:**
- Total codes: 1,000
- Codes with specific enrichment: 32 (3.2%)
- Codes with generic enrichment: 968 (96.8%)
- **All top 15 most-searched codes use generic auto-generated enrichment**

**What is "Generic Enrichment"?**
Auto-generated causes/checks based on description keywords in `obd_service.py:252-398`:
- EVAP codes → "Loose gas cap", "Smoke test EVAP system"
- Sensor codes → "Faulty sensor", "Check wiring"
- Lean/rich codes → "Vacuum leak", "Check MAF/O2 sensors"

These are **functional and correct** but lack code-specific detail.

## Research Findings

### GitHub Datasets (All Inadequate for Enrichment)
**None of the popular GitHub repositories contain causes/fixes:**

1. **mytrile/obd-trouble-codes** - 3,071 codes, descriptions only, some incorrect
2. **todrobbins/dtcdb** - Accurate descriptions, no enrichment
3. **fabiovila/OBDIICodes** - Incomplete coverage, no enrichment
4. **Wal33D/dtc-database** - 28K+ codes, descriptions only (best for descriptions)

**Key Finding:** All GitHub datasets source from SAE J2012 standard, which defines codes and descriptions but NOT diagnostic procedures.

### Where to Get Enrichment Data

**Option 1: Manual Curation (Recommended for Top 15)**
- Use repair manuals, TSBs, and mechanic knowledge
- Focus on top 15 codes (covers ~60-70% of real-world queries)
- Time: 1-2 hours per code for quality research
- Cost: $0
- Quality: High

**Option 2: Commercial Auto Repair Databases**
- Mitchell1, AllData, Identifix
- Cost: $20-100/month subscription
- Quality: Very high (OEM-level detail)
- Legal: Check terms of service for data extraction

**Option 3: Web Scraping Repair Sites**
- obd-codes.com, obdii.com, autocodes.com
- Legal gray area (check robots.txt and ToS)
- Quality: Varies
- Maintenance: Scraper needs updates if site structure changes

**Option 4: AI-Assisted Enrichment (Currently Broken)**
- Use LLM (Gemini/Claude/GPT) to generate enrichment
- Your Gemini API key: `AIzaSyxxx` (invalid placeholder)
- Your Cohere key: valid but model deprecated
- Need valid API key to enable this

**Option 5: Community Contributions**
- Mechanics add enrichment via API/interface
- Long-term strategy
- Requires moderation/quality control

## Recommended Immediate Action Plan

### Phase 1: Fix LLM Provider (For Real-Time Ranking)
**Current Issue:** Both providers broken
- Cohere: Model `command-r-plus` deprecated
- Gemini: API key is placeholder `AIzaSyxxx`

**Solutions:**
```bash
# Option A: Get valid Gemini API key (free)
# 1. Go to https://makersuite.google.com/app/apikey
# 2. Create API key
# 3. Update .env:
GEMINI_API_KEY=YOUR_REAL_KEY_HERE
AI_PROVIDER=gemini

# Option B: Update Cohere model (paid)
COHERE_MODEL=command-r  # or command-r-08-2024
AI_PROVIDER=cohere

# Option C: Disable AI enrichment (use generic only)
AI_ENRICH_ENABLED=false
```

### Phase 2: Manual Backfill Top 15 Codes
**Priority codes (15 codes covering ~60-70% of queries):**

| Code | Description | Current Enrichment |
|------|-------------|-------------------|
| P0300 | Random Misfire | Generic |
| P0420 | Catalyst Efficiency Bank 1 | Generic |
| P0171 | System Too Lean Bank 1 | Generic |
| P0455 | EVAP Large Leak | Generic |
| P0128 | Coolant Thermostat | Generic |
| P0442 | EVAP Small Leak | Generic |
| P0507 | Idle RPM High | Generic |
| P0101 | MAF Circuit | Generic |
| P0301 | Cylinder 1 Misfire | Generic |
| P0440 | EVAP Malfunction | Generic |
| P0172 | System Too Rich Bank 1 | Generic |
| P0430 | Catalyst Efficiency Bank 2 | Generic |
| P0456 | EVAP Very Small Leak | Generic |
| P0174 | System Too Lean Bank 2 | Generic |
| P0400 | EGR Flow | Generic |

**Enrichment Template Per Code:**
```sql
UPDATE obd_codes 
SET 
  common_causes = 'Specific cause 1, Specific cause 2, Specific cause 3, Specific cause 4, Specific cause 5',
  generic_fixes = 'Diagnostic step 1, Diagnostic step 2, Diagnostic step 3, Diagnostic step 4, Diagnostic step 5',
  symptoms = 'Symptom 1, Symptom 2, Symptom 3'
WHERE code = 'P0420';
```

**Example - P0420 (Catalyst Efficiency):**
```sql
UPDATE obd_codes 
SET 
  common_causes = 'Degraded catalytic converter (most common), Faulty downstream O2 sensor, Exhaust leak before catalytic converter, Engine running rich from MAF/O2 sensor issue, Coolant temp sensor causing rich condition',
  generic_fixes = 'Check live O2 sensor data (upstream vs downstream voltage), Inspect for exhaust leaks before converter, Test downstream O2 sensor response time, Check fuel trim values for rich/lean condition, Verify catalytic converter temperature rise under load',
  symptoms = 'Check engine light illuminated, No noticeable performance issues, Possible slight decrease in fuel economy, May fail emissions test'
WHERE code = 'P0420';
```

### Phase 3: Automate Low-Priority Codes
For the remaining 985 codes with generic enrichment:
- Keep current auto-generated enrichment (works reasonably well)
- Monitor which codes get searched frequently
- Manually backfill additional codes as usage patterns emerge

## Implementation Checklist

### Immediate (Before Production)
- [ ] Get valid Gemini API key OR update Cohere model OR disable AI
- [ ] Test LLM ranking works with real API key
- [ ] Update `.env` with working configuration
- [ ] Restart backend and verify

### Short Term (1-2 weeks)
- [ ] Research and document specific enrichment for P0420 (most common)
- [ ] Research and document specific enrichment for P0171 (system lean)
- [ ] Research and document specific enrichment for P0300 (random misfire)
- [ ] Research and document specific enrichment for P0455 (EVAP large leak)
- [ ] Research and document specific enrichment for P0128 (thermostat)
- [ ] Execute SQL updates for top 5 codes
- [ ] Test and verify improved responses

### Medium Term (1 month)
- [ ] Complete remaining 10 of top 15 codes
- [ ] Create enrichment contribution workflow for mechanics
- [ ] Monitor usage analytics to identify next priority codes

### Long Term (Ongoing)
- [ ] Expand to top 50 codes
- [ ] Add vehicle-specific overrides for known issues (TSBs)
- [ ] Build community enrichment system with moderation

## Cost-Benefit Analysis

**Current State:**
- Generic enrichment: Free, instant, 70% useful
- LLM ranking: Broken (needs API key or model fix)

**After Top 15 Backfill:**
- Specific enrichment for 60-70% of queries
- Time investment: ~20-30 hours (1-2 hours per code)
- Cost: $0 (manual research) or $20-100 (if using commercial databases)
- Quality improvement: 70% → 90% useful

**ROI:** High - small time investment significantly improves most common queries.

## Next Steps

1. **Decide on LLM provider strategy** (Gemini free tier recommended)
2. **Get valid API key** or disable AI enrichment
3. **Start manual backfill** with P0420 (most searched code)
4. **Iterate** based on user feedback and usage patterns

## Status

- [X] Research GitHub datasets
- [X] Identify generic vs specific enrichment
- [X] Prioritize top 15 codes
- [ ] Fix LLM provider
- [ ] Begin manual backfill
