# Revised Implementation Plan - Incremental Knowledge Base Strategy

**Date:** 2026-07-10  
**Status:** Ready for Implementation  
**Approach:** Curated incremental enrichment with quality control

---

## Key Changes from Original Plan

### ❌ What We're NOT Doing

1. **NOT bulk enriching all 1,000 codes**
   - Wasteful (many codes are rare/manufacturer-specific)
   - No quality control
   - High upfront cost for unused data

2. **NOT using AI for severity classification**
   - AI severity was 98.9% incorrect
   - Replaced with deterministic expert rules
   - More consistent and maintainable

3. **NOT deploying AI content directly to users**
   - Added review workflow
   - Prevents unvetted content from reaching production

### ✅ What We ARE Doing

1. **Curated priority-based enrichment**
   - Top 50 codes cover ~90% of requests
   - Top 157 codes cover ~98% of requests
   - Focus on highest-value content first

2. **Deterministic severity rules**
   - Expert-defined rules by category
   - 100% validation on test cases
   - Code-specific overrides when needed

3. **Iterative quality improvement**
   - Small batches (25-50 codes)
   - Review each batch
   - Improve AI prompt based on feedback
   - Repeat

4. **Review workflow states**
   - `RAW_DATABASE` → `AI_ENRICHED` → `REVIEWED` → `PUBLISHED`
   - Only `PUBLISHED` content shown to users
   - `NEEDS_REVISION` for content requiring changes

---

## Implementation Components

### 1. Severity Rules System ✅ COMPLETE

**File:** `severity_rules.py`

**Features:**
- Deterministic classification by diagnostic category
- Expert-defined rules for Critical/High/Moderate/Low
- Code-specific overrides
- Severity explanation generation
- 100% validation (12/12 test cases passed)

**Example Rules:**
```python
EVAP System      → Moderate (emissions only, rarely drivability)
O2 Sensor        → Moderate (affects fuel trim, not engine damage)
Misfire Detected → High (catalyst damage risk)
ABS/Brake        → Critical (safety system)
Oil Pressure     → Critical (immediate engine damage risk)
```

**Usage:**
```python
from severity_rules import classify_severity, get_severity_explanation

severity, reasoning = classify_severity("P0450", "EVAP Pressure Sensor", "Powertrain")
# Returns: ("Moderate", "EVAP system - emissions primarily")

explanation = get_severity_explanation(severity, reasoning)
# Returns: User-facing explanation paragraph
```

---

### 2. Priority Code Lists ✅ COMPLETE

**File:** `priority_codes.py`

**Three-Tier System:**

**Tier 1 (48 codes)** - Top priority, ~90% of requests
- Misfires (P0300-P0308)
- Catalyst (P0420, P0430)
- Fuel Trim (P0171, P0172, P0174, P0175)
- EVAP (P0440-P0457)
- O2 Sensors (P0130-P0138)
- MAF/MAP (P0100-P0108)
- Common systems (thermostat, EGR, idle, VVT)

**Tier 2 (78 codes)** - Medium priority, ~8% of requests
- Additional sensor codes
- Crankshaft/camshaft position
- Throttle position
- Coolant/IAT sensors
- Transmission basics
- Fuel system

**Tier 3 (31 codes)** - Lower priority, ~2% of requests
- Advanced Bank 2 codes
- Turbo/boost codes
- Advanced emissions

**Total:** 157 priority codes (covers ~98% of real-world requests)

---

### 3. Enrichment Tool ✅ COMPLETE

**File:** `enrichment_tool.py`

**Features:**
- Batch processing (configurable size: 25, 50, 100)
- Resume capability (skips already-enriched codes)
- Review workflow integration
- Improved AI prompt (OEM-style guidance)
- Automatic review report generation
- Rate limiting (1 sec between calls)

**Improved AI Prompt:**
- OEM-style diagnostic language
- Emphasis on testing before replacement
- No severity exaggeration
- Specific observable symptoms
- Ordered causes (most common first)
- Systematic diagnostic steps with values
- Practical technician tips
- Electrical testing emphasis

**Usage:**
```bash
# Enrich 25 Tier 1 codes
python enrichment_tool.py 25

# Enrich 50 Tier 2 codes
python enrichment_tool.py 50 2

# Re-enrich (no resume)
python enrichment_tool.py 25 1 --no-resume
```

**Output:**
- Enriched codes saved with status: `AI_ENRICHED`
- Review report generated: `enrichment_review_TIMESTAMP.md`

---

## Workflow States

### State Transitions

```
RAW_DATABASE
    ↓ (enrichment tool)
AI_ENRICHED
    ↓ (human review)
REVIEWED ────→ NEEDS_REVISION
    ↓               ↓ (fix & re-enrich)
PUBLISHED    AI_ENRICHED
```

### State Definitions

**RAW_DATABASE**
- Initial state for all codes
- Contains: description, system, basic severity
- Missing: symptoms, causes, diagnostic steps, tips

**AI_ENRICHED**
- AI-generated content added
- Status: Waiting for human review
- Not shown to production users
- Review report generated

**REVIEWED**
- Human-approved content
- Quality validated
- Ready for publication

**PUBLISHED**
- Live in production
- Shown to users
- Considered authoritative

**NEEDS_REVISION**
- Reviewed but requires changes
- Specific issues noted
- Re-enrichment needed

---

## Database Schema Changes Required

### Add enrichment_status Column

```sql
ALTER TABLE obd_codes
ADD COLUMN enrichment_status TEXT DEFAULT 'raw_database';

-- Valid values: 'raw_database', 'ai_enriched', 'reviewed', 'published', 'needs_revision'
```

### Update Existing Records

```sql
-- Mark current records as raw_database
UPDATE obd_codes
SET enrichment_status = 'raw_database'
WHERE enrichment_status IS NULL;
```

---

## Phase 1: Foundation (Immediate - Today)

### Step 1.1: Apply Deterministic Severity Rules

**Goal:** Fix 989 incorrect severity ratings

**Script:** Create `apply_severity_rules.py`

```python
from severity_rules import classify_severity, get_severity_explanation

# For each code in database:
#   1. Classify using deterministic rules
#   2. Generate severity explanation
#   3. Update database
#   4. Log changes
```

**Expected Results:**
- P0450: High → Moderate ✓
- P0130-P0138: High → Moderate ✓
- 989 codes: "Medium" → "Moderate" ✓
- All codes have severity_explanation ✓

**Time:** 10-15 minutes  
**Cost:** $0 (database updates only)

### Step 1.2: Add enrichment_status Column

```bash
# Update database schema
# Set all existing records to 'raw_database'
```

**Time:** 5 minutes  
**Cost:** $0

---

## Phase 2: Tier 1 Enrichment (This Week)

### Step 2.1: Enrich First Batch (25 codes)

```bash
python enrichment_tool.py 25 1
```

**Includes:**
- P0300-P0304 (misfires)
- P0420, P0430 (catalyst)
- P0171, P0172 (fuel trim)
- P0440-P0457 (EVAP sample)
- P0130-P0135 (O2 sensors)
- Additional high-priority codes

**Time:** ~45 minutes (25 codes × 1.5 min each)  
**Cost:** ~$0.50-0.75

**Output:** `enrichment_review_TIMESTAMP.md`

### Step 2.2: Review Batch 1

**Manual Review Checklist:**
- [ ] Symptoms accurate and specific?
- [ ] Causes complete and ordered correctly?
- [ ] Diagnostic steps follow OEM procedures?
- [ ] Technician tip practical and valuable?
- [ ] Pre-replacement checks thorough?
- [ ] Severity rating appropriate?

**Actions:**
- Mark reviewed codes: `UPDATE enrichment_status = 'reviewed'`
- Note improvements needed in AI prompt
- Identify patterns in AI output

### Step 2.3: Improve AI Prompt (Based on Review)

**Common Issues to Watch For:**
- Generic symptoms ("Check engine light on")
- Vague causes ("Bad sensor")
- Missing test values
- Overly cautious language
- Missing practical tips

**Refinement:** Update `ENRICHMENT_PROMPT_TEMPLATE` in `enrichment_tool.py`

### Step 2.4: Enrich Remaining Tier 1 (23 codes)

```bash
python enrichment_tool.py 23 1
```

**Time:** ~40 minutes  
**Cost:** ~$0.50

### Step 2.5: Review & Publish Tier 1

- Review second batch
- Mark all approved codes as `published`
- Test sample codes in production

**Milestone:** Top 48 codes production-ready

---

## Phase 3: Tier 2 Enrichment (Next Week)

### Approach: Incremental Batches

**Batch 1:** 25 codes → Review → Improve → Continue  
**Batch 2:** 25 codes → Review → Improve → Continue  
**Batch 3:** 28 codes (remaining)

**Time:** 2-3 hours (spread over week)  
**Cost:** ~$1.50-2.00

**Milestone:** Top 126 codes production-ready (~95% coverage)

---

## Phase 4: Tier 3 & Long Tail (Future)

### Options:

**Option A: Complete Tier 3**
- Enrich remaining 31 priority codes
- Time: ~1 hour
- Cost: ~$0.50

**Option B: Enable AUTO_LEARN for Long Tail**
- Tier 1 & 2 published (126 codes)
- Enable `AUTO_LEARN_CODES=true`
- Rare codes enriched on-demand
- Review queue for on-demand enrichments

**Option C: Hybrid**
- Complete Tier 3 (31 codes)
- Enable AUTO_LEARN for remaining 843 codes
- 157 codes curated, 843 on-demand

**Recommendation:** Option C (hybrid approach)

---

## Quality Control Process

### Before Enrichment
1. Validate AI prompt improvements
2. Test on 2-3 sample codes
3. Verify JSON parsing

### During Enrichment
1. Monitor AI output quality
2. Check for API errors
3. Verify database updates

### After Enrichment
1. Generate review report
2. Manual review (checklist)
3. Mark approved codes
4. Document issues/improvements

### Before Publishing
1. Spot-check 5-10 codes
2. Test in staging environment
3. Verify formatting
4. Confirm severity accuracy

---

## Cost Analysis - Revised Plan

### Phase 1: Severity Rules (Free)
- Database updates only
- No AI costs
- One-time fix

### Phase 2: Tier 1 (48 codes)
- API calls: 48 × $0.02 = ~$0.96
- Time: 2-3 hours (including review)
- Coverage: ~90% of requests

### Phase 3: Tier 2 (78 codes)
- API calls: 78 × $0.02 = ~$1.56
- Time: 3-4 hours (including review)
- Coverage: ~95% of requests

### Phase 4: Tier 3 (31 codes)
- API calls: 31 × $0.02 = ~$0.62
- Time: 1-2 hours (including review)
- Coverage: ~98% of requests

### Total for Curated Content
- **Cost:** ~$3.14
- **Time:** 6-9 hours (spread over 2 weeks)
- **Coverage:** 157 codes (~98% of requests)
- **Quality:** Human-reviewed, production-ready

### Comparison: Original Bulk Plan
- **Cost:** ~$20-25
- **Time:** 8-12 hours (single batch)
- **Coverage:** 1,000 codes (including rare/unused)
- **Quality:** Unreviewed AI output

### Savings
- **Cost:** 85% reduction ($3 vs $20)
- **Quality:** Human-reviewed vs unvetted
- **Efficiency:** Only enrich valuable codes

---

## Success Metrics

### Phase 2 Complete (Tier 1)
- ✅ 48 codes enriched and published
- ✅ 90% of user requests have complete information
- ✅ Average response time <1 second
- ✅ Zero severity misclassifications
- ✅ Review approval rate >80%

### Phase 3 Complete (Tier 2)
- ✅ 126 total codes published
- ✅ 95% of user requests have complete information
- ✅ AI prompt refined based on 3+ review cycles
- ✅ Enrichment quality consistently high

### Phase 4 Complete (Tier 3)
- ✅ 157 codes published (curated knowledge base)
- ✅ 98% of requests covered
- ✅ AUTO_LEARN enabled for long tail
- ✅ Review workflow established

---

## Next Steps

### Immediate (Today)
1. ✅ Review this plan
2. ⏳ Approve revised approach
3. ⏳ Create `apply_severity_rules.py` script
4. ⏳ Run severity corrections
5. ⏳ Add `enrichment_status` column

### This Week
6. ⏳ Enrich Tier 1 Batch 1 (25 codes)
7. ⏳ Review Batch 1
8. ⏳ Improve AI prompt
9. ⏳ Enrich Tier 1 Batch 2 (23 codes)
10. ⏳ Review and publish Tier 1

### Next Week
11. ⏳ Begin Tier 2 enrichment
12. ⏳ Incremental review and improvement
13. ⏳ Publish Tier 2
14. ⏳ Decide on Tier 3/AUTO_LEARN strategy

---

## Scripts Summary

### Completed ✅
- `audit_database_completeness.py` - Database audit
- `severity_rules.py` - Deterministic severity classification
- `priority_codes.py` - Curated code priorities
- `enrichment_tool.py` - Batch enrichment with review workflow

### To Create
- `apply_severity_rules.py` - Apply deterministic severity to all codes
- `update_enrichment_status.py` - Mark codes as reviewed/published
- Database migration for `enrichment_status` column

---

## Key Insights

### Why This Approach is Better

1. **Focus on Value**
   - Top 50 codes = 90% of requests
   - Don't waste resources on rare codes

2. **Quality Over Quantity**
   - Human review prevents bad content
   - Iterative improvement builds better AI output
   - Professional-grade knowledge base

3. **Maintainable**
   - Deterministic severity rules (no AI inconsistency)
   - Review workflow prevents content drift
   - Clear states and processes

4. **Cost-Effective**
   - 85% cost reduction vs bulk approach
   - Only pay for codes that matter
   - Better ROI on AI spending

5. **Scalable**
   - Can enable AUTO_LEARN later
   - Review process works for long tail
   - System grows with usage

---

## Conclusion

This revised plan transforms the database from a skeletal lookup table into a **curated diagnostic knowledge base** incrementally, with quality control at every step.

**Key Differentiators:**
- Deterministic severity (not AI-guessed)
- Curated priorities (not bulk processing)
- Review workflow (not unvetted content)
- Iterative improvement (not one-shot generation)

**Expected Outcome:**
- Professional-grade diagnostic information
- 98% request coverage with 157 codes
- Human-reviewed quality
- 85% cost savings
- Maintainable long-term

**Status:** Ready for implementation pending approval.
