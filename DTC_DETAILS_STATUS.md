# DTC Details - Current Status

**Date**: 2026-07-06  
**Status**: Schema ready for review, migration not yet run

---

## 1. ✅ Migration Status: VERIFIED NOT RUN

**Verification Result:**
```
[NOT FOUND] code_vehicle_fitment
[NOT FOUND] repair_steps
[NOT FOUND] parts
[NOT FOUND] common_symptoms
[NOT FOUND] related_codes

Found: 0/5 tables

[MIGRATION NOT RUN]
```

**Confirmed:** None of the DTC detail tables exist in Supabase yet.

**Action Required:** Open Supabase SQL Editor and run `migrations/add_dtc_detail_tables.sql`

---

## 2. ✅ Table Rename: COMPLETED

**Changed:** `vehicles` → `code_vehicle_fitment`

**Reason:** Avoid future collision with potential user vehicle table

**Updated Files:**
- ✅ `migrations/add_dtc_detail_tables.sql` - All table references
- ✅ `app/repositories/dtc_details_repository.py` - All table queries
- ✅ `DTC_DETAILS_IMPLEMENTATION.md` - All documentation
- ✅ `DTC_DETAILS_QUICK_REF.md` - Quick reference

**Updated Elements:**
- Table name: `code_vehicle_fitment`
- Indexes: `idx_code_vehicle_fitment_*`
- Trigger: `update_code_vehicle_fitment_updated_at`
- Comments and documentation

---

## 3. ✅ Population Strategy: DEFINED

**Approach:** Manual entry for top 15-20 codes from production logs

**Target Codes (confirmed in production):**
- P0300 - Random/Multiple Cylinder Misfire
- P0420 - Catalyst System Efficiency Below Threshold
- P0171 - System Too Lean (Bank 1)
- P0442 - EVAP System Leak Detected (Small Leak)
- C0035 - (User to confirm details)
- Others from production logs

**Method:** Manual sourcing and verification (same as system_diagrams)

**NOT doing:**
- ❌ Bulk AI-generated import
- ❌ Automated scraping
- ❌ Unverified data population

---

## Current Schema

### Tables Ready to Create:

1. **code_vehicle_fitment** (renamed from vehicles)
   - Foreign key: `code_id` → `obd_codes(code)` (TEXT)
   - Fields: `make`, `model`, `year_start`, `year_end`, `engine`
   - Unique: `(code_id, make, model, year_start, year_end, engine)`

2. **repair_steps**
   - Foreign key: `code_id` → `obd_codes(code)` (TEXT)
   - Fields: `step_number`, `instruction`
   - Unique: `(code_id, step_number)`

3. **parts**
   - Foreign key: `code_id` → `obd_codes(code)` (TEXT)
   - Fields: `part_name`, `part_number` (nullable)

4. **common_symptoms**
   - Foreign key: `code_id` → `obd_codes(code)` (TEXT)
   - Fields: `symptom`
   - Unique: `(code_id, symptom)`

5. **related_codes**
   - Foreign key: `code_id` → `obd_codes(code)` (TEXT)
   - Fields: `related_code` (TEXT, not FK)
   - Unique: `(code_id, related_code)`

---

## Repository Methods Ready

**File:** `app/repositories/dtc_details_repository.py`

**Methods:**
```python
# Vehicle fitment
get_vehicles_for_code(code) -> list[dict]
get_vehicles_for_code_filtered(code, make, model, year) -> list[dict]

# Repair steps
get_repair_steps_for_code(code) -> list[dict]

# Parts
get_parts_for_code(code) -> list[dict]

# Symptoms
get_symptoms_for_code(code) -> list[dict]

# Related codes
get_related_codes_for_code(code) -> list[dict]

# Aggregate
get_all_details_for_code(code, vehicle_filter) -> dict

# Utility
has_enriched_data(code) -> dict
```

---

## Next Steps - Awaiting Your Action

### Step 1: Review Renamed Schema ⏸️
**File to review:** `migrations/add_dtc_detail_tables.sql`

**Check:**
- [ ] Table name `code_vehicle_fitment` acceptable?
- [ ] All 5 tables schema correct?
- [ ] Foreign keys to `obd_codes(code)` correct?
- [ ] Year ranges (`year_start`, `year_end`) work for your use case?

### Step 2: Run Migration (After Review) ⏸️
```sql
-- In Supabase SQL Editor:
-- Copy/paste migrations/add_dtc_detail_tables.sql
-- Click "Run"
```

**Expected output:**
```
✅ All 5 tables created successfully
✅ Created N indexes on DTC detail tables
✅ All 5 foreign key constraints created successfully
```

### Step 3: Verify Migration Success ⏸️
Run this verification query in Supabase SQL Editor:

```sql
-- Check tables exist
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('code_vehicle_fitment', 'repair_steps', 'parts',
                     'common_symptoms', 'related_codes')
ORDER BY table_name;

-- Should return 5 rows
```

### Step 4: Manual Data Entry ⏸️
**After migration succeeds:**

1. Source verified data for P0300, P0420, P0171, P0442, etc.
2. Insert via Supabase UI or direct SQL
3. Test with repository methods

**Example insert:**
```sql
-- Vehicle fitment for P0420
INSERT INTO code_vehicle_fitment (code_id, make, model, year_start, year_end, engine)
VALUES ('P0420', 'Toyota', 'Camry', 2012, 2017, '2.5L 4-cylinder');

-- Repair step
INSERT INTO repair_steps (code_id, step_number, instruction)
VALUES ('P0420', 1, 'Connect OBD scanner and verify code is present');

-- etc.
```

### Step 5: Integration (Much Later) ⏸️
**Hold off until:**
- Schema reviewed ✓
- Migration run ✓
- Data manually populated ✓
- You decide on message formatting approach

---

## Files Ready for Review

1. **`migrations/add_dtc_detail_tables.sql`** - Migration with renamed table
2. **`app/repositories/dtc_details_repository.py`** - Repository with updated table name
3. **`DTC_DETAILS_IMPLEMENTATION.md`** - Full documentation (updated)
4. **`DTC_DETAILS_QUICK_REF.md`** - Quick reference (updated)
5. **`DTC_DETAILS_STATUS.md`** - This status document

---

## Verification Command

To verify migration status at any time:

```bash
python -c "
from app.db.client import get_supabase_client
client = get_supabase_client()

tables = ['code_vehicle_fitment', 'repair_steps', 'parts', 'common_symptoms', 'related_codes']
for table in tables:
    try:
        client.table(table).select('id').limit(0).execute()
        print(f'[OK] {table}')
    except:
        print(f'[NOT FOUND] {table}')
"
```

---

## Summary

**✅ Completed:**
- Schema designed with year ranges
- Table renamed to avoid future collision
- Repository methods implemented
- Documentation updated
- Migration verified as NOT run yet

**⏸️ Awaiting Review:**
- Migration SQL (`migrations/add_dtc_detail_tables.sql`)
- Repository methods (`app/repositories/dtc_details_repository.py`)

**⏸️ Next Actions (After Review):**
1. You review and approve schema
2. Run migration in Supabase
3. Verify migration success
4. Begin manual data entry for top codes

**❌ Not Doing Yet:**
- Wiring into diagnostic flow
- Bulk data population
- AI-generated content
