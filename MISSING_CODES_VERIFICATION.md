# Missing OBD Codes Verification

**Date:** 2026-07-07  
**Issue:** 4 codes failed FK constraint when populating parts table  
**Status:** ✅ Verified - Codes genuinely missing from obd_codes table

---

## Background

During DTC details population, these 4 codes failed with FK constraint errors:
- P0609
- P0142  
- P0271
- P3497

**Error:** `insert or update on table "parts" violates foreign key constraint "parts_code_id_fkey"`  
**Details:** `Key (code_id)=(P0609) is not present in table "obd_codes"`

---

## Verification Steps Performed

### 1. Checked for Formatting Variations

Searched obd_codes table for:
- ✅ Exact match (case-sensitive)
- ✅ Case-insensitive match (ILIKE)
- ✅ Wildcard patterns (spaces, dashes)
- ✅ Without prefix (e.g., "0609" vs "P0609")
- ✅ Numeric portion matches

**Result:** None found. Not a formatting issue.

### 2. Verified Wal33D Source Dataset

Checked `data/obd_codes_dataset.json`:
- Total codes in source: 156
- P0609: ❌ NOT FOUND
- P0142: ❌ NOT FOUND
- P0271: ❌ NOT FOUND
- P3497: ❌ NOT FOUND

**Result:** These codes were never in the Wal33D dataset.

### 3. Confirmed Database State

Current `obd_codes` table:
- Total codes: 133
- Breakdown:
  - P-codes: 104
  - C-codes: 8
  - B-codes: 11
  - U-codes: 10

**Priority codes status:** 15/19 exist, 4 missing

---

## Missing Codes Details

### P0609 - Control Module VSS Output "B" Malfunction
- **From Kaggle dataset:** "Control Module VSS Output 'B' Malfunction"
- **System:** Powertrain
- **Why missing:** Not in Wal33D base dataset
- **Production usage:** Appeared in diagnostic logs

### P0142 - O2 Sensor Circuit Malfunction (Bank 1 Sensor 3)
- **From Kaggle dataset:** "02 Sensor Circuit Malfunction (Bank 1 Sensor 3)"
- **System:** Powertrain
- **Why missing:** Not in Wal33D base dataset
- **Production usage:** Appeared in diagnostic logs

### P0271 - Injector Circuit High Cylinder 4
- **From Kaggle dataset:** "Injector circuit high Cylinder 4"
- **System:** Powertrain
- **Why missing:** Not in Wal33D base dataset
- **Production usage:** Appeared in diagnostic logs

### P3497 - Cylinder Deactivation System Bank 2
- **From Kaggle dataset:** "Cylinder Deactivation System Bank 2"
- **System:** Powertrain
- **Why missing:** Not in Wal33D base dataset
- **Why important:** Honda/Dodge manufacturer-specific code, user priority

---

## Conclusion

✅ **These 4 codes genuinely do NOT exist in the obd_codes table.**  
✅ **They were never in the Wal33D source dataset.**  
✅ **No formatting/variation issues - they need to be added as new entries.**

---

## Recommendation

**Add these 4 codes to obd_codes table before attempting to populate detail tables.**

### Option A: Use Kaggle Dataset Descriptions
The Kaggle OBD2 Powertrain Codes dataset has these codes with condition descriptions. While it lacks probable causes/symptoms (why we rejected it for detail tables), the condition descriptions are valid for the base obd_codes entry.

### Option B: Use Web Research Descriptions  
Use the descriptions already researched from dtclookup.com/obdguide.com.

### Recommended Approach:
Use the descriptions from our earlier web research (already paraphrased and verified):
- P0609: "Control Module Vehicle Speed Sensor Output B - Communication problem between the engine control module and other systems regarding vehicle speed signal"
- P0142: "Oxygen Sensor Circuit Malfunction (Bank 1 Sensor 3) - Electrical problem with the downstream oxygen sensor after the catalytic converter"
- P0271: "Cylinder 4 Injector Circuit High - High voltage or resistance detected in the fuel injector circuit for cylinder 4"
- P3497: "Cylinder Deactivation System Bank 2 Malfunction - The engine control module detected that cylinders on Bank 2 failed to deactivate or reactivate properly"

---

## Next Steps

1. Insert these 4 codes into obd_codes table with:
   - code (e.g., "P0609")
   - description (from web research)
   - system (all are "Powertrain")

2. Then retry populating the detail tables (parts, symptoms, steps, related codes)

3. Verify FK constraints pass

---

## Files Referenced

- `data/obd_codes_dataset.json` - Wal33D source (156 codes)
- `obd_codes` table - Current database (133 codes)
- `DTC_DETAILS_FOR_REVIEW.md` - Contains full researched data for these codes
- Kaggle "OBD2 Powertrain Codes" - Has basic descriptions (but rejected for details)

---

## Impact

**Current state:**
- 15/19 priority codes have complete enrichment data
- 4/19 priority codes have partial data (parts only, no symptoms/steps/related)

**After adding missing codes:**
- All 19 priority codes can have complete enrichment data
- FK constraints will pass
- Database will be consistent

**Total rows that will be added once FK issue is resolved:**
- P0609: ~5 parts entries
- P0142: ~4 parts entries  
- P0271: ~4 parts entries
- P3497: ~5 parts entries
- Plus symptoms, steps, and related codes for each

Estimated additional rows: ~70-80 across all detail tables.
