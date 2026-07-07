# C0035 Correction Summary

**Date:** 2026-07-07  
**Issue:** Conflicting data between web research and production database  
**Status:** ✅ Corrected

---

## Problem Identified

### Initial Web Research Said:
- **C0035:** "Left Front Wheel Speed Sensor Circuit Malfunction"
- Source: Generic automotive reference sites

### Production Database Said:
- **C0035:** "Right Front Wheel Speed Sensor Supply"
- Source: Your actual obd_codes table (source of truth)

### Root Cause:
C0035 code definition **varies by manufacturer**:
- Some manufacturers (e.g., Buick, certain GM models) use C0035 for **left front**
- Other manufacturers use C0035 for **right front**
- Web research pulled from a Buick-specific source

---

## Correction Applied

### 1. Updated `obd_codes` Table
```sql
UPDATE obd_codes 
SET description = 'Right Front Wheel Speed Sensor Supply'
WHERE code = 'C0035';
```

**Result:** ✅ C0035 now correctly says "Right Front" to match your production data

### 2. Corrected `parts` Table
**Deleted:** 5 incorrect "Left Front" parts entries  
**Inserted:** 5 corrected "Right Front" parts entries

**Corrected parts:**
- ✅ Right Front Wheel Speed Sensor (was: Left Front)
- Wheel Speed Sensor Wiring Harness
- Sensor Connector
- Wheel Bearing/Hub Assembly
- ABS Tone Ring/Reluctor Ring

### 3. Added Complete Enrichment Data

**Symptoms (5):**
- ABS warning light illuminated
- Traction control light on or system disabled
- ABS system not functioning
- Speedometer reading incorrectly or erratically
- Stability control disabled

**Repair Steps (9):**
1. Inspect **right front** wheel speed sensor wiring (includes manufacturer variation note)
2. Check sensor connector for corrosion
3. Clean wheel speed sensor and tone ring
4. Measure sensor resistance
5. Check sensor air gap (0.020-0.050 inches)
6. Inspect tone ring for damage
7. Test sensor signal with scan tool
8. Compare front wheel sensor readings to identify faulty sensor
9. Check for bearing play in wheel hub

**Related Codes (3):**
- C0040 - Other front wheel speed sensor
- C0045 - Left rear wheel speed sensor  
- C0050 - Right rear wheel speed sensor

---

## Hedge Language Added

**Step 1** includes manufacturer variation note:

> "Inspect right front wheel speed sensor wiring harness for damage, cuts, or chafing **(Note: C0035 may indicate left or right front depending on manufacturer)**"

This acknowledges the manufacturer variation while **keeping the primary framing aligned with your database** (Right Front).

---

## Key Principle Established

**Your Database is Source of Truth**

When web research conflicts with existing obd_codes data:
1. ✅ **Trust your database** (it reflects your actual production usage)
2. ✅ **Update research to match** database description
3. ✅ **Add hedge language** to acknowledge known variations
4. ❌ **Do not override** database with generic web research

This ensures:
- Consistency between OBD code description and enrichment data
- Users see the same terminology throughout their diagnosis
- Manufacturer variations are noted but don't contradict primary description

---

## Verification

```bash
# Check corrected data
python << 'EOF'
from supabase import create_client
import os

client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

obd = client.table("obd_codes").select("*").eq("code", "C0035").execute()
parts = client.table("parts").select("part_name").eq("code_id", "C0035").execute()
symptoms = client.table("common_symptoms").select("*").eq("code_id", "C0035").execute()
steps = client.table("repair_steps").select("*").eq("code_id", "C0035").execute()
related = client.table("related_codes").select("*").eq("code_id", "C0035").execute()

print(f"Description: {obd.data[0]['description']}")
print(f"Parts: {len(parts.data)} (includes 'Right Front Wheel Speed Sensor')")
print(f"Symptoms: {len(symptoms.data)}")
print(f"Steps: {len(steps.data)}")
print(f"Related: {len(related.data)}")
EOF
```

**Expected Output:**
```
Description: Right Front Wheel Speed Sensor Supply
Parts: 5 (includes 'Right Front Wheel Speed Sensor')
Symptoms: 5
Steps: 9
Related: 3
```

---

## Updated Database Stats

After correction, C0035 now has:
- ✅ **Complete enrichment data** (symptoms + steps + parts + related)
- ✅ **Aligned with obd_codes description** (Right Front)
- ✅ **Manufacturer variation noted** in repair steps
- ✅ **Ready for production use**

Total enriched codes: **6** (P0171, P0100, P0300, P0420, P0442, **C0035**)

---

## Lessons Learned

### For Future Population:

1. **Always check obd_codes first** before accepting web research
2. **Compare descriptions** between sources and your database
3. **Flag discrepancies** before inserting data
4. **Use hedge language** for known manufacturer variations
5. **Keep primary framing** aligned with your database

### Manufacturer-Specific Codes to Watch:

Codes known to vary by manufacturer:
- **C0035** - Wheel speed sensor (varies left/right)
- **C0040** - Wheel speed sensor (varies left/right)
- **P0402** - EGR flow (Ford DPFE sensors have specific issues)
- **P3497** - Cylinder deactivation (Honda VCM, Dodge MDS specific)

For these codes:
- ✅ Match your database description
- ✅ Add "Note: varies by manufacturer" in repair steps
- ✅ Include manufacturer-specific details in notes

---

## Summary

✅ **C0035 corrected** from "Left Front" to "Right Front"  
✅ **All enrichment data updated** to match  
✅ **Manufacturer variation noted** in repair steps  
✅ **Source of truth principle** established for future work  

The correction ensures users see consistent terminology between the initial OBD code description and the detailed diagnostic information.
