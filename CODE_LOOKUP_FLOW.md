# OBD Code Lookup Flow - What Happens When a Code is Missing

## Database Contents Summary

**Current State:**
- **Total OBD Codes:** 9,422
  - Powertrain (P): 7,387 codes
  - Body (B): 302 codes
  - Chassis (C): 503 codes
  - Network (U): 1,230 codes

**Data Quality:**
- **Basic descriptions:** 9,415 codes (99.9%) - from Wal33D import
- **Enriched with symptoms/causes/fixes:** 7 codes (0.1%) - manually curated
- **Detail tables:**
  - common_symptoms: 35 rows
  - repair_steps: 35 rows
  - parts: 117 rows
  - related_codes: 27 rows

---

## Lookup Flow When User Sends a Code

### Step 1: Validation
**File:** `app/services/obd.py:8`

```python
def validate_obd_code(code: str) -> bool:
    return bool(re.match(r"^[PBCU][0-9]{4}$", code))
```

**Action:** Check if code matches OBD-II format (P/B/C/U + 4 digits)

---

### Step 2: Database Lookup
**File:** `app/repositories/obd_repository.py:16`

```python
def get_by_code(self, code: str) -> dict | None:
    # Check cache first
    if code_upper in _obd_cache:
        return _obd_cache[code_upper]
    
    # Query Supabase
    result = self.client.table("obd_codes")
        .select("*")
        .eq("code", code_upper)
        .execute()
    
    code_data = result.data[0] if result.data else None
    _obd_cache[code_upper] = code_data  # Cache result
    return code_data
```

**Action:** 
1. Check in-memory cache (hot path - instant)
2. If not cached, query Supabase `obd_codes` table
3. Cache the result (even if None)

---

### Step 3A: Code FOUND in Database ✅

**Returns:**
```json
{
  "code": "P0420",
  "description": "Catalyst System Efficiency Below Threshold Bank 1",
  "system": "Powertrain",
  "severity": "Medium",
  "symptoms": null,          // Usually null (99.9% of codes)
  "common_causes": null,     // Usually null (99.9% of codes)
  "generic_fixes": null,     // Usually null (99.9% of codes)
  "source": "local_db",
  "confidence": 0.95
}
```

**Next Steps:**
1. Check for vehicle-specific overrides (if vehicle make/model/year provided)
2. If enriched data is missing AND `AI_ENRICH_ENABLED=true`, trigger AI enrichment
3. If AI enrichment disabled AND `INTERNET_FALLBACK_ENABLED=true`, try web search
4. Return data to user via WhatsApp

---

### Step 3B: Code NOT FOUND in Database ❌

**File:** `app/repositories/obd_repository.py:28`

If Supabase lookup returns `None`, falls back to:

```python
# Fallback mode - check hardcoded fallback data
return get_fallback_code(code)
```

**Fallback Data Source:** `app/repositories/fallback_obd_data.py`
- Contains ~40 hardcoded common codes (P0420, P0300, P0171, etc.)
- Used when Supabase is disabled OR code not in database

**If code NOT in fallback data either:**

Returns generic placeholder:
```json
{
  "code": "PXXXX",
  "description": "Generic OBD-II diagnostic trouble code",
  "symptoms": "",
  "common_causes": "Faulty sensor, Wiring or connector issue, ECM software fault",
  "generic_fixes": "Inspect wiring, Check connectors, Clear code and retest",
  "source": "fallback",
  "confidence": 0.30
}
```

---

## AI Enrichment Flow (When Basic Data is Found)

**Trigger Conditions:**
```bash
AI_ENRICH_ENABLED=true          # Currently: true
AUTO_LEARN_CODES=false          # Currently: false (won't auto-save to DB)
```

**File:** `app/services/obd_service.py:171`

```python
async def _fetch_and_learn(self, code: str) -> Optional[DiagnosticResult]:
    # Try web search first
    if settings.internet_fallback_enabled:
        web_data = await self.web_fetcher.fetch_code(code)
        if web_data:
            return web_data
    
    # Fall back to AI generation
    if settings.ai_enrich_enabled:
        ai_data = await self.ai_provider.generate_diagnostic(code)
        return ai_data
    
    return None
```

**Web Search Sources:**
- Brave Search API (if `BRAVE_API_KEY` configured)
- Trusted sites: obd-codes.com, autocodes.com, obdii.com
- Caches results for 30 days (`EXTERNAL_CACHE_TTL_SECONDS=2592000`)

**AI Provider:**
- **Current:** Cohere (`AI_PROVIDER=cohere`)
- **Model:** command-r-plus-08-2024
- Generates symptoms, causes, and fixes based on code description

---

## Full Flow Diagram

```
User sends "P0420"
        |
        v
[1] Validate format (PXXXX pattern)
        |
        +-- Invalid --> Return error
        |
        v-- Valid
        |
[2] Check in-memory cache
        |
        +-- Found --> Skip to [4]
        |
        v-- Miss
        |
[3] Query Supabase obd_codes table
        |
        +-- Found (9,422 codes) --> [4]
        |
        v-- Not found
        |
[3a] Check fallback data (~40 codes)
        |
        +-- Found --> [4]
        |
        v-- Not found
        |
[3b] Return generic placeholder
     (confidence: 0.30)
        |
        v
[4] Check if enrichment needed
    (symptoms/causes/fixes missing?)
        |
        +-- No (0.1% of codes) --> [6]
        |
        v-- Yes (99.9% of codes)
        |
[5] AI Enrichment (if enabled)
        |
        +-- INTERNET_FALLBACK_ENABLED=true
        |   --> Web search (Brave API)
        |   --> Cache for 30 days
        |
        +-- AI_ENRICH_ENABLED=true
        |   --> Cohere AI generation
        |   --> NOT saved to DB (AUTO_LEARN_CODES=false)
        |
        v
[6] Check vehicle overrides
    (if make/model/year provided)
        |
        v
[7] Format response for WhatsApp
        |
        v
[8] Send to user
```

---

## Configuration Options

### Current Settings (.env)
```bash
# Database
SUPABASE_ENABLED=true

# AI Enrichment
AI_PROVIDER=cohere
AI_ENRICH_ENABLED=true
AUTO_LEARN_CODES=false              # AI-generated data NOT saved to DB

# Web Fallback
INTERNET_FALLBACK_ENABLED=true
SEARCH_PROVIDER=brave
BRAVE_API_KEY=                      # Not configured
TRUSTED_SITES=obd-codes.com,autocodes.com,obdii.com
EXTERNAL_CACHE_TTL_SECONDS=2592000  # 30 days
```

### What Gets Saved vs. Ephemeral

**Saved to Database:**
- ✅ Imported codes from Wal33D (9,415 codes)
- ✅ Manually curated enrichments (7 codes)
- ❌ AI-generated enrichments (AUTO_LEARN_CODES=false)
- ❌ Web search results (cached in memory/temp, not persisted)

**Cached in Memory:**
- ✅ All database lookups (hot path optimization)
- ✅ Web search results (30-day TTL)
- ✅ AI-generated responses (session-based)

---

## Real-World Examples

### Example 1: Common Code in Database
**Input:** "P0420"
**Result:** 
- Found in database ✅
- Description: "Catalyst System Efficiency Below Threshold Bank 1"
- No symptoms/causes in DB (basic entry)
- AI enrichment triggers (if enabled)
- Returns enriched response to user
- **Confidence:** 0.95 (database) → enhanced by AI

### Example 2: Rare Code in Database
**Input:** "P3497" (Honda Cylinder Deactivation)
**Result:**
- Found in database ✅ (part of 9,415 generic codes)
- Description: "Cylinder Deactivation System Bank 2"
- No enrichment data
- AI enrichment triggers
- **Confidence:** 0.95

### Example 3: Manufacturer-Specific Code NOT in Database
**Input:** "P1234" (hypothetical Honda-specific code)
**Result:**
- NOT in database ❌ (manufacturer-specific codes excluded)
- Falls back to hardcoded data → NOT found
- Returns generic placeholder:
  - "Generic OBD-II diagnostic trouble code"
  - Generic causes/fixes
  - **Confidence:** 0.30
- AI enrichment still triggers (may improve response)

### Example 4: Invalid Code
**Input:** "P04200" (5 digits - invalid)
**Result:**
- Fails validation ❌
- Error message: "Invalid OBD code format"

---

## Improving Coverage

### Option 1: Import Manufacturer-Specific Codes
**Action:** Modify `scripts/import_wal33d_dtc.py` to remove the `is_generic` filter

**Impact:**
- Add 9,390 more codes (total: 18,805)
- Covers Honda, Toyota, Ford, GM, etc. specific codes
- Most won't have enrichment data (same 99.9% basic only)

**Command:**
```python
# Change line 113 in import_wal33d_dtc.py:
query = """
    SELECT code, description, type, manufacturer, is_generic
    FROM dtc_definitions
    -- Remove: WHERE is_generic = 1 AND manufacturer = 'GENERIC'
    ORDER BY code
"""
```

### Option 2: Enable Auto-Learning
**Action:** Set `AUTO_LEARN_CODES=true` in .env

**Impact:**
- AI-generated enrichments saved to database
- Builds up enriched data over time
- Risk: AI hallucinations persisted

**Risk Mitigation:**
- Keep confidence scores
- Review AI-generated entries periodically
- Mark as "ai_generated" vs "manually_verified"

### Option 3: Manual Curation (Current Approach)
**Status:** 7 codes enriched, 9,415 to go

**Process:** (from POPULATION_SUCCESS_SUMMARY.md)
1. Prioritize by diagnostic_logs usage
2. Cross-reference 2+ trusted sources
3. Paraphrase (copyright compliance)
4. Manual entry into detail tables

---

## Summary

| Scenario | Database | Fallback | AI Enrich | Confidence |
|----------|----------|----------|-----------|------------|
| Common code (e.g., P0420) | ✅ Found | N/A | ✅ Yes | 0.95 |
| Rare generic (e.g., P3497) | ✅ Found | N/A | ✅ Yes | 0.95 |
| Manufacturer-specific | ❌ Not found | ⚠️ Maybe | ✅ Yes | 0.30-0.60 |
| Invalid format | ❌ Invalid | N/A | N/A | 0.00 |

**Current database covers ~50% of all OBD codes (9,422 / 18,805 total)**
**But covers ~100% of generic SAE J2012 standard codes**
