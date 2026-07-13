# Migration 003 Quick Start Guide

## 🎯 What This Does

Transforms your basic OBD code responses into comprehensive, professional diagnostic reports with:

- ✅ **Cost estimates** ($200-$800)
- ✅ **Time estimates** (1-3 hours)
- ✅ **DIY difficulty** (Easy/Moderate/Advanced/Professional)
- ✅ **Likelihood rankings** (60% bad cat, 25% O2 sensor...)
- ✅ **Related codes** (P0430, P0171, P0174)
- ✅ **Common mistakes** ("Don't replace cat without testing O2 sensor!")
- ✅ **Scanner data guidance** (What freeze frame data to check)
- ✅ **Quality tracking** (Knowledge score, enrichment status)

## 🚀 Quick Start (3 Steps)

### Step 1: Run the Migration

**Option A: Supabase CLI (Easiest)**
```bash
cd C:\Users\vinmu\Desktop\VehicleDiagnosisAssistant
supabase db push
```

**Option B: Supabase Dashboard**
1. Go to: https://app.supabase.com/project/YOUR_PROJECT/sql
2. Copy contents of: `supabase/migrations/003_enhance_obd_codes_enrichment.sql`
3. Click "Run"

**Option C: Direct PostgreSQL**
```bash
# If you have DATABASE_URL or DB credentials
python scripts/run_migration_003_psycopg2.py
```

### Step 2: Verify It Worked

```bash
# Using Supabase client
python scripts/run_migration_003.py --verify-only

# OR using PostgreSQL
python scripts/run_migration_003_psycopg2.py --verify-only
```

### Step 3: Update Your Code

See [Implementation Steps](#implementation-steps) below.

---

## 📊 Before & After Comparison

### BEFORE (Basic Response)
```
🔧 Fault Code: P0420
System: Emissions

📖 What it means
Catalyst System Efficiency Below Threshold

🔍 Likely causes
• Worn catalytic converter
• Oxygen sensor malfunction

🛠️ Recommended diagnostic steps
1. Check for other codes
2. Inspect oxygen sensors
```

### AFTER (Enhanced Response)
```
🔧 Fault Code: P0420
System: Emissions | Severity: ⚠️ Moderate

═══════════════════════════

📖 What This Code Means
Catalyst System Efficiency Below Threshold (Bank 1)
[Detailed explanation...]

🔍 Most Common Causes (in order of likelihood)
1. ⭐ Worn catalytic converter (60%)
2. ⭐ Faulty downstream O2 sensor (25%)
3. Engine running too rich/lean (10%)
4. Exhaust leak before cat (5%)

❌ STOP - Check These BEFORE Replacing Parts
• Verify downstream O2 sensor is responding
• Check fuel trims are within spec (-10% to +10%)
• Rule out exhaust leaks

💡 Technician Insight
80% of P0420 codes are misdiagnosed. Always test
the rear O2 sensor first - it's $200 vs $1,500 cat!

⏱️ Typical Repair Time: 1-3 hours
💰 Typical Cost Range: $200-$2,500
🔧 DIY Difficulty: Moderate

🔗 Related Codes to Check
• P0430 (Bank 2 catalyst)
• P0300 (Check for misfires first!)

📊 Data to Review (if you have a scanner)
• Short Term Fuel Trim: -10% to +10%
• Long Term Fuel Trim: -10% to +10%
• O2 Sensor Voltage: Front toggle 0.1-0.9V
```

---

## 📋 What Got Added to Database

### New Columns in `obd_codes` table:

**Enrichment Tracking:**
- `enrichment_status` - not_enriched → ai_enriched → reviewed → oem_verified
- `knowledge_score` - 0-100% (auto-calculated)
- `last_enriched` - timestamp
- `schema_version` - version tracking

**User-Helpful Fields:**
- `severity_explanation` - Why this severity
- `technician_tip` - Expert advice
- `pre_replacement_checks` - Critical checks
- `typical_repair_time` - "1-3 hours"
- `typical_cost_range` - "$200-$2,500"
- `diy_difficulty` - Easy/Moderate/Advanced/Professional

**Advanced Guidance:**
- `related_codes` - Array: ["P0430", "P0171"]
- `common_misdiagnoses` - What NOT to do
- `freeze_frame_data_to_check` - Scanner data to review
- `cause_likelihoods` - JSONB: [{"cause": "...", "likelihood": 60}]
- `emissions_impact` - Will Fail / May Fail / No Impact

**Metadata (Provenance Tracking):**
- `symptoms_meta`, `common_causes_meta`, `diagnostic_steps_meta`
- `severity_explanation_meta`, `technician_tip_meta`, `pre_replacement_checks_meta`

### New Database Objects:

**Functions:**
- `calculate_obd_knowledge_score()` - Auto-calc completeness score
- `update_obd_knowledge_score()` - Trigger function

**Triggers:**
- `trigger_update_obd_knowledge_score` - Auto-update score on INSERT/UPDATE

**Views:**
- `obd_codes_needing_enrichment` - Codes with score < 80%
- `obd_enrichment_stats` - Summary by enrichment_status

**Indexes:**
- GIN indexes on JSONB fields (fast searching)
- Indexes on enrichment_status, knowledge_score, last_enriched

---

## 🔧 Implementation Steps

### 1. Update Repository (Already Done ✅)

Your `obd_repository.py` already has `enrich_code()` method that handles metadata fields.

### 2. Update Formatter (Next Step)

Edit `app/services/diagnostic_formatter.py`:

```python
# Add these new sections to format_full_report():

def _format_cause_likelihoods(self) -> str:
    """Format causes with likelihood percentages"""
    if not self.result.cause_likelihoods:
        return self._format_causes()  # Fallback to basic

    causes = json.loads(self.result.cause_likelihoods)
    causes_list = "\n".join(
        f"{i+1}. ⭐ {c['cause']} ({c['likelihood']}%)"
        for i, c in enumerate(causes[:6])
    )
    return f"""🔍 *Most Common Causes* (in order of likelihood)

{causes_list}"""

def _format_cost_time_info(self) -> str:
    """Format cost and time information"""
    if not (self.result.typical_cost_range or self.result.typical_repair_time):
        return None

    lines = []
    if self.result.typical_repair_time:
        lines.append(f"⏱️ *Typical Repair Time:* {self.result.typical_repair_time}")
    if self.result.typical_cost_range:
        lines.append(f"💰 *Typical Cost Range:* {self.result.typical_cost_range}")
    if self.result.diy_difficulty:
        lines.append(f"🔧 *DIY Difficulty:* {self.result.diy_difficulty}")

    return "\n".join(lines)

def _format_related_codes(self) -> str:
    """Format related codes section"""
    if not self.result.related_codes:
        return None

    codes_list = "\n".join(f"• {code}" for code in self.result.related_codes[:5])
    return f"""🔗 *Related Codes to Check*

{codes_list}"""

def _format_common_misdiagnoses(self) -> str:
    """Format misdiagnosis warning"""
    if not self.result.common_misdiagnoses:
        return None

    return f"""⚠️ *Common Misdiagnosis*

{self.result.common_misdiagnoses}"""

def _format_freeze_frame_guidance(self) -> str:
    """Format freeze frame data guidance"""
    if not self.result.freeze_frame_data_to_check:
        return None

    data_list = "\n".join(
        f"• {data}" for data in self.result.freeze_frame_data_to_check[:6]
    )
    return f"""📊 *Data to Review* (if you have a scanner)

{data_list}"""
```

### 3. Update DiagnosticResult Model

Edit `app/models/diagnostic.py`:

```python
class DiagnosticResult(BaseModel):
    # ... existing fields ...

    # Add new fields
    typical_repair_time: str | None = None
    typical_cost_range: str | None = None
    diy_difficulty: str | None = None
    related_codes: list[str] | None = None
    common_misdiagnoses: str | None = None
    freeze_frame_data_to_check: list[str] | None = None
    cause_likelihoods: str | None = None  # JSON string
    emissions_impact: str | None = None
```

### 4. Create Enrichment Script (Phase 2)

```bash
# Script to backfill existing codes with AI
python scripts/enrich_existing_codes.py --batch-size 50
```

---

## 📈 Monitoring Enrichment Quality

### Check Enrichment Status
```sql
SELECT * FROM obd_enrichment_stats;
```

### Find Codes Needing Work
```sql
SELECT code, description, knowledge_score, missing_field
FROM obd_codes_needing_enrichment
LIMIT 20;
```

### Find Highest Quality Codes (Examples)
```sql
SELECT code, description, knowledge_score
FROM obd_codes
WHERE knowledge_score >= 90
ORDER BY knowledge_score DESC;
```

### Find Stale Enrichments (>30 days)
```sql
SELECT code, description, last_enriched
FROM obd_codes
WHERE last_enriched < NOW() - INTERVAL '30 days'
ORDER BY last_enriched ASC;
```

---

## 🔄 Rollback (If Needed)

**⚠️ WARNING: This deletes all enriched data!**

```bash
# Option 1: Supabase Dashboard
# Run: supabase/migrations/003_rollback_enhance_obd_codes_enrichment.sql

# Option 2: Python script
python scripts/run_migration_003_psycopg2.py --rollback
```

---

## 🐛 Troubleshooting

### Issue: "Column doesn't exist"

**Cause:** Migration didn't run successfully

**Fix:**
```bash
# Verify migration status
python scripts/run_migration_003_psycopg2.py --verify-only

# Re-run if needed
python scripts/run_migration_003_psycopg2.py
```

### Issue: Knowledge score not updating

**Cause:** Trigger not installed

**Fix:**
```sql
-- Check trigger exists
SELECT * FROM pg_trigger WHERE tgname = 'trigger_update_obd_knowledge_score';

-- Manually recalculate all scores
UPDATE obd_codes SET code = code;
```

### Issue: Views not accessible

**Cause:** Views not created or permissions issue

**Fix:**
```sql
-- Check views exist
SELECT viewname FROM pg_views WHERE viewname LIKE 'obd_%';

-- Recreate if needed (copy from migration file)
```

---

## 📚 Next Steps

1. ✅ **Run Migration** (this guide)
2. 🔄 **Update Code** (formatter, models) - See [Implementation Steps](#implementation-steps)
3. 🤖 **Backfill Data** - Run AI enrichment on existing codes
4. 📊 **Monitor Quality** - Track knowledge_score improvements
5. 🎨 **Test Responses** - Verify enhanced format looks good

---

## 📞 Support

- **Documentation:** See `supabase/migrations/README_MIGRATION_003.md`
- **Issues:** Check logs and verify with `--verify-only`
- **Questions:** Review example queries in migration file

---

**Migration Version:** 003  
**Created:** 2026-07-13  
**Status:** ✅ Ready for Production  
**Estimated Impact:** ~5-10KB per enriched code, 10-15 min to run migration
