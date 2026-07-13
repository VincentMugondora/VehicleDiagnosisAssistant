# AI Enrichment Guide (Migration 003)

## Overview

The `enrich_existing_codes.py` script uses AI to populate Migration 003 fields for existing OBD codes in your database.

**Performance:** ~10-15 seconds per code (AI generation + database update)

---

## Quick Start

### 1. Test with Dry-Run (No Database Changes)

```bash
# Enrich 5 codes (dry-run)
python scripts/enrich_existing_codes.py --limit 5 --dry-run

# Enrich specific code (dry-run)
python scripts/enrich_existing_codes.py --code P0420 --dry-run
```

### 2. Enrich Small Batch (Recommended First Run)

```bash
# Enrich 10 codes (live)
python scripts/enrich_existing_codes.py --limit 10
```

### 3. Enrich All Codes (Production)

```bash
# Enrich all codes with knowledge_score < 80%
python scripts/enrich_existing_codes.py --all --batch-size 20
```

---

## What Gets Enriched

The script generates these Migration 003 fields using AI:

| Field | Example | Purpose |
|-------|---------|---------|
| `typical_repair_time` | "1-3 hours" | Time estimate |
| `typical_cost_range` | "$200-$2,500" | Cost estimate |
| `diy_difficulty` | "Moderate" | DIY assessment |
| `related_codes` | ["P0430", "P0300"] | Related codes to check |
| `common_misdiagnoses` | "Don't replace cat without..." | Warning about mistakes |
| `freeze_frame_data_to_check` | ["STFT: -10% to +10%"] | Scanner data guidance |
| `cause_likelihoods` | [{"cause": "...", "likelihood": 60}] | Ranked causes with % |
| `emissions_impact` | "Will Fail" | Emissions test impact |

Plus enrichment tracking:
- `enrichment_status` → "ai_enriched"
- `last_enriched` → timestamp
- `knowledge_score` → auto-calculated (trigger)

---

## Command Reference

### Basic Commands

```bash
# Dry-run (no changes)
python scripts/enrich_existing_codes.py --limit 10 --dry-run

# Enrich 10 codes
python scripts/enrich_existing_codes.py --limit 10

# Enrich specific code
python scripts/enrich_existing_codes.py --code P0420

# Enrich all codes needing it
python scripts/enrich_existing_codes.py --all
```

### Advanced Options

```bash
# Custom batch size (pause after N codes)
python scripts/enrich_existing_codes.py --all --batch-size 50

# Only enrich codes with score < 50%
python scripts/enrich_existing_codes.py --all --min-score 50.0

# Enrich first 100 codes
python scripts/enrich_existing_codes.py --limit 100 --batch-size 25
```

---

## Usage Examples

### Example 1: Test Before Production

```bash
# Step 1: Test with 3 codes (dry-run)
python scripts/enrich_existing_codes.py --limit 3 --dry-run

# Step 2: Enrich those 3 codes for real
python scripts/enrich_existing_codes.py --limit 3

# Step 3: Verify in database
python -c "
from supabase import create_client
from app.core.config import settings

client = create_client(settings.supabase_url, settings.supabase_service_key)
result = client.table('obd_enrichment_stats').select('*').execute()

for row in result.data:
    print(f\"{row['enrichment_status']}: {row['count']} codes\")
"
```

### Example 2: Enrich High-Priority Codes First

```bash
# Enrich common/important codes first
python scripts/enrich_existing_codes.py --code P0420  # Cat efficiency
python scripts/enrich_existing_codes.py --code P0300  # Random misfire
python scripts/enrich_existing_codes.py --code P0171  # System too lean
python scripts/enrich_existing_codes.py --code P0455  # EVAP leak
```

### Example 3: Production Backfill (All Codes)

```bash
# Enrich all codes in batches of 20
# Pauses 2 seconds between batches for rate limiting
python scripts/enrich_existing_codes.py --all --batch-size 20
```

**Estimated Time:**
- 500 codes × 15 seconds/code = ~2 hours
- Script pauses 2 seconds every 20 codes

---

## Monitoring Progress

### Check Enrichment Stats

```sql
-- View enrichment status distribution
SELECT * FROM obd_enrichment_stats;
```

```bash
# Via Python
python -c "
from supabase import create_client
from app.core.config import settings

client = create_client(settings.supabase_url, settings.supabase_service_key)
result = client.table('obd_enrichment_stats').select('*').execute()

print('Enrichment Status Distribution:')
print('='*60)
for row in result.data:
    status = row['enrichment_status']
    count = row['count']
    avg_score = row['avg_knowledge_score']
    print(f'{status:<20} {count:>6} codes (avg score: {avg_score:.1f}%)')
"
```

### Find Codes Still Needing Work

```sql
-- Find codes with lowest scores
SELECT code, description, knowledge_score
FROM obd_codes_needing_enrichment
ORDER BY knowledge_score ASC
LIMIT 20;
```

### Check Recently Enriched Codes

```sql
-- View recently enriched codes
SELECT code, description, knowledge_score, last_enriched
FROM obd_codes
WHERE enrichment_status = 'ai_enriched'
ORDER BY last_enriched DESC
LIMIT 10;
```

---

## Troubleshooting

### Issue: AI generation fails

**Cause:** AI API issues or rate limiting

**Fix:**
```bash
# Reduce batch size
python scripts/enrich_existing_codes.py --all --batch-size 5

# Or enrich in smaller chunks
python scripts/enrich_existing_codes.py --limit 50
# Wait a few minutes, then:
python scripts/enrich_existing_codes.py --limit 50
```

### Issue: Database update fails

**Cause:** Connection issues or schema mismatch

**Fix:**
```bash
# Verify migration ran successfully
python scripts/run_migration_via_supabase_api.py --verify-only

# Check for schema issues
python -c "
from supabase import create_client
from app.core.config import settings

client = create_client(settings.supabase_url, settings.supabase_service_key)
result = client.table('obd_codes').select('*').limit(1).execute()

if result.data:
    print('Available columns:')
    for key in sorted(result.data[0].keys()):
        print(f'  - {key}')
"
```

### Issue: Knowledge score not updating

**Cause:** Trigger not working

**Fix:**
```sql
-- Check trigger exists
SELECT * FROM pg_trigger 
WHERE tgname = 'trigger_update_obd_knowledge_score';

-- Manually recalculate all scores
UPDATE obd_codes SET code = code;
```

---

## Quality Assurance

### Verify Enriched Code Quality

```bash
# View enriched code details
python -c "
from supabase import create_client
from app.core.config import settings
import json

client = create_client(settings.supabase_url, settings.supabase_service_key)
result = client.table('obd_codes').select('*').eq('code', 'P0420').execute()

if result.data:
    code_data = result.data[0]
    print(f\"Code: {code_data['code']}\")
    print(f\"Score: {code_data['knowledge_score']}%\")
    print(f\"Status: {code_data['enrichment_status']}\")
    print(f\"Cost: {code_data['typical_cost_range']}\")
    print(f\"Time: {code_data['typical_repair_time']}\")
    print(f\"DIY: {code_data['diy_difficulty']}\")
    print(f\"Related: {code_data['related_codes']}\")
"
```

### Test Enhanced Response Format

```bash
# Test with enriched code
python scripts/test_enhanced_format.py
```

---

## Performance & Cost

### Performance Metrics
- **AI Generation:** ~8-12 seconds per code
- **Database Update:** ~1-2 seconds per code
- **Total:** ~10-15 seconds per code
- **Batch Pause:** 2 seconds every N codes

### Cost Estimates (Cohere)
- **Per Code:** ~2,000 tokens (input) + ~800 tokens (output)
- **500 Codes:** ~1.4M tokens total
- **Cohere Cost:** ~$0.70 for 500 codes (at current rates)

### Time Estimates
| Codes | Batch Size | Estimated Time |
|-------|------------|----------------|
| 10    | 10         | ~2 minutes |
| 50    | 20         | ~13 minutes |
| 100   | 20         | ~26 minutes |
| 500   | 20         | ~2.2 hours |

---

## Best Practices

### 1. Start Small
Always test with `--dry-run` and `--limit 10` first

### 2. Enrich High-Priority Codes First
Common codes like P0420, P0300, P0171, P0455

### 3. Monitor Quality
Check a few enriched codes manually before bulk processing

### 4. Use Appropriate Batch Sizes
- Small batches (5-10): More stable, slower
- Large batches (20-50): Faster, may hit rate limits

### 5. Track Progress
Check `obd_enrichment_stats` view regularly

### 6. Review and Refine
Manually review AI-generated content for accuracy

---

## Example Workflow

```bash
# Day 1: Test and pilot
python scripts/enrich_existing_codes.py --limit 10 --dry-run
python scripts/enrich_existing_codes.py --limit 10
# Review results manually

# Day 2: Enrich high-priority codes
python scripts/enrich_existing_codes.py --code P0420
python scripts/enrich_existing_codes.py --code P0300
python scripts/enrich_existing_codes.py --code P0171
# ... (top 20 most common codes)

# Day 3: Batch enrich remaining codes
python scripts/enrich_existing_codes.py --all --batch-size 20

# Day 4: Quality check
python scripts/run_migration_via_supabase_api.py --verify-only
# Review enrichment stats
# Spot-check random codes
```

---

## Next Steps

After enrichment:

1. ✅ **Verify Results**
   ```bash
   python scripts/run_migration_via_supabase_api.py --verify-only
   ```

2. ✅ **Test User-Facing Responses**
   ```bash
   python scripts/test_enhanced_format.py
   ```

3. ✅ **Monitor Quality**
   ```sql
   SELECT * FROM obd_enrichment_stats;
   ```

4. ✅ **Update Documentation**
   - Add examples of enriched responses
   - Update user guides with new fields

---

## Support

### View Logs
```bash
# Enrichment logs
tail -f logs/enrichment.log

# Application logs
tail -f logs/app.log
```

### Get Help
```bash
# Script help
python scripts/enrich_existing_codes.py --help

# Verification
python scripts/run_migration_via_supabase_api.py --verify-only
```

---

**Created:** 2026-07-13  
**Version:** 1.0  
**Status:** ✅ Production Ready
