# Severity Review Summary

**Date:** 2026-07-10
**Reviewer:** Vincent Mugondora

---

## Phase 1: Automated Confidence-Based Corrections

**Executed:** `python apply_confidence_severity.py --yes`

### Results

| Category | Count | Action |
|----------|-------|--------|
| High confidence (≥90%) | 457 | ✅ Auto-applied |
| Medium confidence (60-89%) | 8 | 📋 Manual review required |
| Low confidence (<60%) | 522 | ⏸️ Left unchanged |
| **Total codes** | **1,000** | |

### Severity Distribution After Auto-Corrections

| Severity | Count | Percentage |
|----------|-------|------------|
| Critical | 2 | 0.2% |
| High | 274 | 27.4% |
| Moderate | 125 | 12.5% |
| Medium | 300 | 30.0% |
| Low | 301 | 30.1% |

---

## Phase 2: Manual Review of 8 Medium-Confidence Codes

### Approved and Applied (4 codes)

✅ **P0420** - Catalyst System Efficiency Below Threshold Bank 1
- **Change:** High → Moderate
- **Reasoning:** Catalyst efficiency below threshold affects emissions and fuel economy, not immediate engine safety
- **Status:** Applied 2026-07-10

✅ **P0430** - Catalyst System Efficiency Below Threshold Bank 2
- **Change:** High → Moderate
- **Reasoning:** Same as P0420 - emissions issue, not immediate danger
- **Status:** Applied 2026-07-10

✅ **P0217** - Engine Coolant Over Temperature Condition
- **Change:** High → **Critical**
- **Reasoning:** Engine coolant over-temperature can rapidly cause severe engine damage. Driver should stop immediately.
- **Status:** Applied 2026-07-10

✅ **P0218** - Transmission Fluid Temperature Sensor A Over Temperature Condition
- **Change:** High → **Critical**
- **Reasoning:** Transmission fluid over-temperature can quickly damage transmission. Driver should stop immediately.
- **Status:** Applied 2026-07-10

### Pending Further Review (4 codes)

⚠️ **P0506** - Idle Control System RPM - Lower Than Expected
- **Proposed:** High → Moderate (60% confidence)
- **Issue:** Low idle can sometimes cause stalling but rarely an immediate safety issue
- **Decision:** Needs additional context about specific failure modes

⚠️ **P0507** - Idle Control System RPM - Higher Than Expected
- **Proposed:** High → Moderate (60% confidence)
- **Issue:** High idle is generally moderate unless causing unintended acceleration symptoms
- **Decision:** Needs additional context about specific failure modes

❌ **P0520** - Engine Oil Pressure Sensor/Switch A Circuit
- **Proposed:** High → Critical (60% confidence)
- **Issue:** This is an **oil pressure sensor/switch CIRCUIT** fault, not actual low oil pressure
- **Decision:** **Do NOT elevate to Critical**. The sensor may be faulty while actual oil pressure is normal. Should remain High with clear explanation that it's a sensor issue requiring immediate diagnosis.
- **Recommended Action:** Update `severity_explanation` to clarify this is a sensor circuit fault, not actual low pressure

❌ **C0060** - Left Front ABS Motor Circuit Malfunction
- **Proposed:** Medium → Critical (60% confidence)
- **Issue:** ABS motor circuit faults reduce braking assistance features but usually do NOT mean total braking failure
- **Decision:** **Do NOT elevate to Critical**. Normal brakes still function; only ABS assist is affected. Critical severity would be misleading.
- **Recommended Action:** Update to Moderate with clear explanation about continued brake functionality

---

## Phase 3: Enhanced Severity Model Implementation

### Problem with Current Single-Severity Approach

The current model forces every DTC into one severity label, which oversimplifies automotive diagnostics:

**Example Issues:**
- P0520 (Oil Pressure Sensor): System wants "Critical" because low oil pressure causes engine damage, BUT this is a sensor circuit fault - actual pressure may be fine
- C0060 (ABS Circuit): System wants "Critical" because ABS affects control, BUT ABS failure ≠ brake failure
- P0217 (Coolant Over-Temp): IS critical, but only if driver keeps driving - requires actionable guidance

### Proposed Enhanced Multi-Dimensional Model

Instead of:
```json
{
  "severity": "Critical"
}
```

Use:
```json
{
  "severity": "High",
  "drivable": true,
  "stop_driving": false,
  "may_cause_engine_damage": false,
  "may_cause_safety_issue": false,
  "affects_emissions_only": false,
  "requires_urgent_repair": true,
  "repair_urgency": "within_day",
  "drive_restrictions": {
    "max_distance": 50,
    "avoid_highway": false,
    "reduced_performance": false
  }
}
```

### Benefits

✅ More accurate user guidance
✅ Differentiates sensor faults from actual failures
✅ Provides actionable driving restrictions
✅ Separates safety issues from emissions issues
✅ Allows context-aware WhatsApp messaging
✅ Backward compatible (severity field remains)

### Implementation Files Created

1. **enhanced_severity_model.md** - Complete specification with examples
2. **migrations/005_add_severity_metadata.sql** - Database migration to add JSONB column
3. **populate_severity_metadata.py** - Script to populate enhanced metadata with confidence scoring

### Example User Messages

**P0217 (Critical - Actual Overheating):**
> 🚨 **Critical - Stop Driving Immediately**
>
> Engine coolant temperature is dangerously high. Continuing to drive can cause severe engine damage within minutes. Pull over safely, turn off the engine, and do not restart until coolant system is repaired.

**P0520 (High - Sensor Circuit Issue):**
> ⚠️ **High - Diagnose Immediately**
>
> Oil pressure sensor circuit fault detected. This is likely a sensor or wiring issue, not actual low oil pressure. However, you cannot rely on your oil pressure warning light until this is fixed. Have it diagnosed immediately to confirm actual oil pressure is normal.

---

## Next Steps

### Immediate Actions

1. ✅ Apply approved corrections (P0420, P0430, P0217, P0218) - **COMPLETED**
2. 🔲 Update P0520 severity_explanation to clarify sensor circuit vs actual pressure
3. 🔲 Update C0060 to Moderate with explanation about normal brake function
4. 🔲 Decide on P0506/P0507 (idle control) severity after reviewing failure modes

### Phase 3 Implementation

1. 🔲 Run migration `005_add_severity_metadata.sql`
2. 🔲 Execute `populate_severity_metadata.py` to populate enhanced metadata
3. 🔲 Review medium-confidence metadata assignments
4. 🔲 Update WhatsApp bot response logic to use enhanced metadata
5. 🔲 Test new messaging with sample codes

### Long-term Improvements

- Consider manufacturer-specific severity adjustments
- Add vehicle type context (e.g., ABS more critical for heavy vehicles)
- Track user feedback on severity accuracy
- Build ML model from real-world repair urgency data

---

## Audit Trail

All changes logged to `enrichment_audit_log` table:

```sql
SELECT code, action, previous_state, new_state, actor, timestamp
FROM enrichment_audit_log
WHERE action = 'severity_correction'
ORDER BY timestamp DESC;
```

## Files Generated

- `severity_corrections_log_20260710_131243.json` - Full change log
- `severity_review_queue_20260710_131243.md` - Original review queue
- `apply_approved_corrections.py` - Script to apply approved changes
- `SEVERITY_REVIEW_SUMMARY.md` - This document
