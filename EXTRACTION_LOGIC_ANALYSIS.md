# Component Extraction Logic Analysis

## Summary

**FOUND: 367 codes with FREE coverage potential!**

These codes mention components we already have images for, but our extraction patterns don't catch them. Fixing this will increase coverage from **23.0%** to **26.9%** (+3.9%) **WITHOUT sourcing any new images**.

---

## Current Extraction Logic

Located in: `app/services/component_mapper.py`

### Method 1: Description Regex Patterns (24 patterns)
Hardcoded regex patterns match component names in descriptions:

```python
COMPONENT_PATTERNS = [
    (r'\bcatalyst\b|\bcatalytic converter\b', 'catalytic converter'),
    (r'\bo2\s*sensor\b|\boxygen sensor\b', 'oxygen sensor'),
    (r'\bmaf\b|\bmass air flow\b', 'mass air flow sensor'),
    (r'\bfuel\s*injector', 'fuel injector'),
    # ... 20 more patterns
]
```

### Method 2: Code Prefix Patterns (10 code ranges)
Maps specific code ranges to components:

```python
# P0300-P0312 → ignition coil
# P0420-P0434 → catalytic converter
# P0100-P0104 → mass air flow sensor
# etc.
```

---

## Missed Matches Breakdown

### 1. **Fuel Injector: 184 missed codes** 🎯

**Current pattern:** `r'\bfuel\s*injector'`

**Misses:**
- "injector" alone (without "fuel")
- "Injection pump"
- "Air Assisted Injector"

**Examples:**
- P0067: Air Assisted **Injector** Control Circuit High
- P0260: **Injection** Pump Fuel Metering Control
- P0261: Cylinder 1 **Injector** A Circuit Low

**Fix:** Add `r'\binjector\b|\binjection\b'` pattern

---

### 2. **Camshaft Position Sensor: 116 missed codes** 🎯

**Current pattern:** `r'\bcamshaft\s*position\s*sensor'`

**Misses:**
- "Camshaft Position Actuator" (says "position" but not "sensor")
- "Camshaft Position - Timing" (says "position" but formatted differently)

**Examples:**
- P2088: A **Camshaft Position** Actuator Control Circuit Low
- P0011: A **Camshaft Position** - Timing Over-Advanced

**Fix:** Change pattern to `r'\bcamshaft\s*position'` (drop "sensor" requirement)

---

### 3. **Throttle Body: 46 missed codes** 🎯

**Current pattern:** `r'\bthrottle\s*body\b|\bthrottle\s*position'`

**Misses:**
- "Throttle Actuator" (common in electronic throttle codes)

**Examples:**
- P2110: **Throttle Actuator** A Control System
- P2111: **Throttle Actuator** A Control System - Stuck Open
- P210F: **Throttle Actuator** B Control System

**Fix:** Add `r'\bthrottle\s*actuator'` to existing pattern

---

### 4. **Mass Air Flow Sensor: 8 missed codes**

**Current pattern:** `r'\bmaf\b|\bmass air flow\b'`

**Misses:**
- "Air Flow Sensor" (without "mass" prefix)
- "Mass or Volume Air Flow" (has extra words)

**Examples:**
- P010A: Mass or Volume **Air Flow Sensor** B Circuit

**Fix:** Add `r'\bair\s*flow\s*sensor\b'` pattern

---

### 5. **EVAP System: 7 missed codes**

**Current pattern:** `r'\bevap\b|\bevaporative\s*emission'`

**Misses:**
- "Purge Valve" (part of EVAP system, but pattern doesn't catch it)

**Examples:**
- P1440: **Purge Valve** Stuck Open
- P24F6: Exhaust Aftertreatment Fuel Air **Purge Valve** Stuck Open

**Fix:** Add `r'\bpurge\s*valve'` to existing pattern

---

### 6. **Crankshaft Position Sensor: 4 missed codes**

**Current pattern:** `r'\bcrankshaft\s*position\s*sensor'`

**Misses:**
- "Crankshaft Position" without "sensor" word

**Examples:**
- P0315: **Crankshaft Position** System Variation Not Learned

**Fix:** Change to `r'\bcrankshaft\s*position'` (drop "sensor" requirement)

---

### 7. **Wheel Speed Sensor: 2 missed codes**

**Current pattern:** `r'\bwheel\s*speed\s*sensor'`

**Misses:**
- "Wheel Speed" without "sensor" word

**Examples:**
- P215A: Vehicle Speed - **Wheel Speed** Correlation

**Fix:** Change to `r'\bwheel\s*speed'` (drop "sensor" requirement)

---

## Recommended Pattern Updates

### File: `app/services/component_mapper.py`

```python
# OLD patterns:
(r'\bfuel\s*injector', 'fuel injector'),
(r'\bcamshaft\s*position\s*sensor', 'camshaft position sensor'),
(r'\bthrottle\s*body\b|\bthrottle\s*position', 'throttle body'),
(r'\bmaf\b|\bmass air flow\b', 'mass air flow sensor'),
(r'\bevap\b|\bevaporative\s*emission', 'evap system'),
(r'\bcrankshaft\s*position\s*sensor', 'crankshaft position sensor'),
(r'\bwheel\s*speed\s*sensor', 'wheel speed sensor'),

# NEW patterns:
(r'\bfuel\s*injector|\binjector\b|\binjection\b', 'fuel injector'),
(r'\bcamshaft\s*position', 'camshaft position sensor'),
(r'\bthrottle\s*body\b|\bthrottle\s*position|\bthrottle\s*actuator', 'throttle body'),
(r'\bmaf\b|\bmass.*air\s*flow|\bair\s*flow\s*sensor', 'mass air flow sensor'),
(r'\bevap\b|\bevaporative\s*emission|\bpurge\s*valve', 'evap system'),
(r'\bcrankshaft\s*position', 'crankshaft position sensor'),
(r'\bwheel\s*speed', 'wheel speed sensor'),
```

---

## Impact Estimate

**Before fixes:**
- Coverage: 2,166 codes (23.0%)

**After fixes:**
- Coverage: 2,533 codes (26.9%)
- **Increase: +367 codes (+3.9%)**

**No new images needed!** This is purely improving extraction logic to match codes that already mention our covered components.

---

## Testing Plan

After implementing fixes:

1. Run `scripts/audit_component_coverage.py` again
2. Verify coverage increases to ~26.9%
3. Test specific codes:
   - P0067 (injector) → should now extract "fuel injector"
   - P2088 (camshaft position actuator) → should extract "camshaft position sensor"
   - P2110 (throttle actuator) → should extract "throttle body"

---

## Next Steps

1. ✅ **Update patterns in component_mapper.py** (high priority - free coverage!)
2. Test and verify improved extraction
3. THEN consider Tier 2 image sourcing if desired

---

**Date:** 2026-07-08
**Status:** Ready to implement
**Estimated time:** 10 minutes to update patterns
**Expected impact:** +3.9% coverage (367 codes)
