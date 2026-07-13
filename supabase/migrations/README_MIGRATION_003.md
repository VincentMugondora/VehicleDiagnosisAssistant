# Migration 003: Enhanced OBD Codes Enrichment

## Overview

This migration enhances the `obd_codes` table with comprehensive enrichment tracking and user-helpful diagnostic fields. It transforms basic OBD code lookups into professional, actionable diagnostic reports.

## What This Migration Adds

### 1. **Enrichment Tracking** (Data Quality Management)
- `enrichment_status` - Lifecycle tracking (not_enriched → ai_enriched → reviewed → oem_verified)
- `knowledge_score` - Completeness score 0-100 (auto-calculated)
- `last_enriched` - Timestamp of last AI enrichment
- `schema_version` - Version tracking for iterative improvements

### 2. **Enhanced Diagnostic Fields** (Better User Experience)
- `severity_explanation` - Why this severity level and what could happen
- `technician_tip` - Practical diagnostic advice from experts
- `pre_replacement_checks` - Critical verifications before replacing parts

### 3. **Field-Level Metadata** (Provenance & Trust)
- `symptoms_meta`, `common_causes_meta`, etc. - JSONB tracking data source
- Enables transparency: "This data came from AI/OEM/Manual curation"
- Tracks AI model, prompt version, generation timestamp

### 4. **User-Helpful Information** (Practical Guidance)
- `typical_repair_time` - "1-3 hours", "30 minutes", "Full day"
- `typical_cost_range` - "$200-$800", "$1,000-$2,500"
- `diy_difficulty` - Easy | Moderate | Advanced | Professional Required

### 5. **Advanced Diagnostic Guidance** (Avoid Misdiagnosis)
- `related_codes` - Array of related codes to check (e.g., ["P0430", "P0171"])
- `common_misdiagnoses` - What NOT to do (prevents expensive mistakes)
- `freeze_frame_data_to_check` - Scanner data points to review
- `cause_likelihoods` - Probability ranking (60% bad cat, 25% O2 sensor, etc.)

### 6. **Additional Context**
- `detailed_explanation` - Long-form technical explanation
- `common_vehicle_notes` - Vehicle-specific issues (e.g., "Common on 2008-2012 Honda Accord")
- `emissions_impact` - Will Fail | May Fail | Monitor Not Ready | No Impact

## Running the Migration

### Option 1: Supabase CLI (Recommended)

```bash
# Apply the migration
supabase db push

# Or apply specific migration
supabase migration up
```

### Option 2: Direct SQL Execution

```bash
# Using psql
psql -h <your-host> -U <user> -d <database> -f supabase/migrations/003_enhance_obd_codes_enrichment.sql

# Using Supabase SQL Editor
# 1. Go to Supabase Dashboard → SQL Editor
# 2. Copy contents of 003_enhance_obd_codes_enrichment.sql
# 3. Execute
```

### Option 3: Python Script

```bash
# Create a migration runner script
python scripts/run_migration_003.py
```

## Post-Migration Steps

### 1. Verify Migration Success

```sql
-- Check new columns exist
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'obd_codes' 
  AND column_name IN (
    'enrichment_status', 
    'knowledge_score', 
    'technician_tip',
    'related_codes'
  );

-- Check triggers are active
SELECT trigger_name, event_manipulation, action_statement
FROM information_schema.triggers
WHERE event_object_table = 'obd_codes';

-- Check views exist
SELECT viewname FROM pg_views 
WHERE viewname IN ('obd_codes_needing_enrichment', 'obd_enrichment_stats');
```

### 2. Review Enrichment Status

```sql
-- Check enrichment stats
SELECT * FROM obd_enrichment_stats;

-- Find codes needing enrichment
SELECT code, description, knowledge_score 
FROM obd_codes_needing_enrichment
LIMIT 20;
```

### 3. Test Knowledge Score Auto-Calculation

```sql
-- Insert a test code to verify trigger works
INSERT INTO obd_codes (code, description, system, severity)
VALUES ('P9999', 'Test Code', 'Test System', 'Low');

-- Check if knowledge_score was auto-calculated
SELECT code, knowledge_score, enrichment_status 
FROM obd_codes 
WHERE code = 'P9999';

-- Clean up test
DELETE FROM obd_codes WHERE code = 'P9999';
```

## Rollback Instructions

If you need to revert this migration:

```bash
# Using SQL file
psql -h <host> -U <user> -d <db> -f supabase/migrations/003_rollback_enhance_obd_codes_enrichment.sql

# Or in Supabase SQL Editor
# Copy and execute: 003_rollback_enhance_obd_codes_enrichment.sql
```

**⚠️ Warning:** Rollback will **permanently delete** all enriched data. Back up first:

```sql
-- Backup enriched data before rollback
CREATE TABLE obd_codes_backup_003 AS 
SELECT * FROM obd_codes;
```

## Next Steps After Migration

### 1. **Backfill Existing Codes**

Run AI enrichment on existing codes with low knowledge scores:

```bash
# Script to be created in Phase 2
python scripts/enrich_existing_codes.py --batch-size 50 --min-score 50
```

### 2. **Update Application Code**

- Update `app/repositories/obd_repository.py` to use new fields
- Update `app/services/diagnostic_formatter.py` to format new sections
- Update `app/models/diagnostic.py` with new fields

### 3. **Monitor Enrichment Quality**

```sql
-- Daily enrichment progress
SELECT 
    DATE(last_enriched) as date,
    COUNT(*) as codes_enriched,
    AVG(knowledge_score) as avg_score
FROM obd_codes
WHERE last_enriched IS NOT NULL
GROUP BY DATE(last_enriched)
ORDER BY date DESC
LIMIT 7;

-- Find stale enrichments (>30 days old)
SELECT code, description, last_enriched
FROM obd_codes
WHERE last_enriched < NOW() - INTERVAL '30 days'
  AND enrichment_status IN ('ai_generated', 'ai_enriched')
ORDER BY last_enriched ASC
LIMIT 20;
```

## Schema Weights for Knowledge Score

The auto-calculated `knowledge_score` uses these weights:

| Field | Weight | Notes |
|-------|--------|-------|
| `description` | 15% | Required - base info |
| `symptoms` | 10% | User-facing symptoms |
| `common_causes` | 15% | Critical for diagnosis |
| `generic_fixes` | 15% | Actionable steps |
| `severity` | 10% | Risk assessment |
| `severity_explanation` | 5% | Context for severity |
| `technician_tip` | 15% | Expert knowledge |
| `pre_replacement_checks` | 10% | Prevent misdiagnosis |
| `system` | 5% | Categorization |
| **Total** | **100%** | |

**Completeness Thresholds:**
- `< 40%` = `not_enriched`
- `40-79%` = `partial`
- `≥ 80%` = `ai_generated` or higher

## Example: Update Code with New Fields

```sql
-- Enrich P0420 with comprehensive data
UPDATE obd_codes
SET
    severity_explanation = 'Can drive for now, but address soon to prevent reduced fuel economy and failed emissions.',
    
    technician_tip = '80% of P0420 codes are misdiagnosed. Always test the rear O2 sensor first - it is cheaper and more likely faulty than the catalytic converter itself.',
    
    pre_replacement_checks = 'Confirm no other codes present, Verify downstream O2 sensor is responding, Check fuel trims within spec',
    
    typical_repair_time = '1-3 hours',
    typical_cost_range = '$200-$2,500',
    diy_difficulty = 'Moderate',
    
    related_codes = ARRAY['P0430', 'P0300', 'P0171', 'P0174'],
    
    common_misdiagnoses = 'Do not replace the cat without testing the O2 sensor first!',
    
    freeze_frame_data_to_check = ARRAY[
        'Short Term Fuel Trim: -10% to +10%',
        'Long Term Fuel Trim: -10% to +10%',
        'O2 Voltage: Front toggle 0.1-0.9V'
    ],
    
    cause_likelihoods = '[
        {"cause": "Worn catalytic converter", "likelihood": 60},
        {"cause": "Faulty O2 sensor", "likelihood": 25},
        {"cause": "Engine running rich/lean", "likelihood": 10},
        {"cause": "Exhaust leak", "likelihood": 5}
    ]'::jsonb,
    
    emissions_impact = 'Will Fail',
    enrichment_status = 'ai_enriched',
    last_enriched = NOW()
    
WHERE code = 'P0420';

-- Verify knowledge_score auto-updated (should be near 100)
SELECT code, knowledge_score, enrichment_status FROM obd_codes WHERE code = 'P0420';
```

## Useful Monitoring Queries

```sql
-- 1. Find codes with missing technician tips
SELECT code, description, knowledge_score
FROM obd_codes
WHERE technician_tip IS NULL
ORDER BY knowledge_score DESC
LIMIT 50;

-- 2. Find codes with related_codes populated (good examples)
SELECT code, description, related_codes
FROM obd_codes
WHERE related_codes IS NOT NULL
LIMIT 10;

-- 3. Count codes by DIY difficulty
SELECT diy_difficulty, COUNT(*)
FROM obd_codes
WHERE diy_difficulty IS NOT NULL
GROUP BY diy_difficulty;

-- 4. Find codes with highest knowledge scores (quality examples)
SELECT code, description, knowledge_score, enrichment_status
FROM obd_codes
WHERE knowledge_score >= 90
ORDER BY knowledge_score DESC;
```

## Troubleshooting

### Issue: Knowledge score not auto-updating

```sql
-- Check trigger exists
SELECT * FROM pg_trigger WHERE tgname = 'trigger_update_obd_knowledge_score';

-- Manually recalculate for all codes
UPDATE obd_codes SET code = code;  -- Triggers recalculation
```

### Issue: Migration fails on constraint

```sql
-- Check for invalid enrichment_status values
SELECT code, enrichment_status FROM obd_codes 
WHERE enrichment_status NOT IN ('not_enriched', 'partial', 'ai_generated', 'ai_enriched', 'reviewed', 'oem_verified');

-- Fix invalid values
UPDATE obd_codes SET enrichment_status = 'not_enriched' 
WHERE enrichment_status IS NULL OR enrichment_status NOT IN (...);
```

## Performance Impact

- **Storage:** ~5-10KB per enriched code (vs ~1KB basic)
- **Query Performance:** GIN indexes added for JSONB/array searches
- **Trigger Overhead:** Minimal (~1ms per INSERT/UPDATE)
- **Recommended:** Run `VACUUM ANALYZE obd_codes;` after bulk enrichment

## Support

For issues or questions:
1. Check existing GitHub issues
2. Review migration logs
3. Test with rollback/re-apply cycle
4. Contact: [your-support-email]

---

**Migration Version:** 003  
**Created:** 2026-07-13  
**Author:** Vehicle Diagnosis Assistant Team  
**Status:** ✅ Ready for Production
