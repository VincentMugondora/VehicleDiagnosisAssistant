# Enhanced Severity Model for OBD-II Codes

## Problem with Current Single-Severity Model

Current model forces every DTC into one severity label:
```json
{
  "code": "P0217",
  "severity": "Critical"
}
```

This oversimplifies automotive diagnostics. Real-world examples:

- **P0520** (Oil Pressure Sensor Circuit): Current system wants to mark "Critical" because low oil pressure causes immediate engine damage. BUT this is a **sensor circuit** fault - the sensor may be broken while actual oil pressure is normal. Single severity can't express this nuance.

- **C0060** (ABS Motor Circuit): Current system wants "Critical" because ABS affects vehicle control. BUT ABS failure means you lose anti-lock assist, not total braking capability. Most vehicles can brake safely without ABS.

- **P0217** (Engine Coolant Over-Temp): This IS critical - but only if you keep driving. The severity depends on driver action.

## Enhanced Multi-Dimensional Model

```sql
ALTER TABLE obd_codes ADD COLUMN severity_metadata JSONB DEFAULT '{}'::jsonb;

-- Structure:
{
  "severity": "High",                    -- Overall severity label (Low/Moderate/High/Critical)
  "drivable": true,                      -- Can vehicle be driven safely?
  "stop_driving": false,                 -- Should driver stop immediately?
  "may_cause_engine_damage": false,      -- Risk of engine/transmission damage if ignored
  "may_cause_safety_issue": false,       -- Risk to occupant/pedestrian safety
  "affects_emissions_only": false,       -- Only impacts emissions compliance
  "requires_urgent_repair": true,        -- Needs immediate repair vs can wait
  "repair_urgency": "within_week",       -- immediate / within_day / within_week / within_month / non_urgent
  "drive_restrictions": {
    "max_distance": null,                -- Max safe driving distance (km) or null
    "avoid_highway": false,              -- Should avoid highway driving
    "reduced_performance": false         -- Vehicle has reduced performance
  }
}
```

## Example Mappings

### P0217 - Engine Coolant Over-Temperature
```json
{
  "severity": "Critical",
  "drivable": false,
  "stop_driving": true,
  "may_cause_engine_damage": true,
  "may_cause_safety_issue": false,
  "affects_emissions_only": false,
  "requires_urgent_repair": true,
  "repair_urgency": "immediate",
  "drive_restrictions": {
    "max_distance": 0,
    "avoid_highway": true,
    "reduced_performance": true
  }
}
```

**User Message:**
> 🚨 **Critical - Stop Driving Immediately**
> 
> Engine coolant temperature is dangerously high. Continuing to drive can cause severe engine damage within minutes. Pull over safely, turn off the engine, and do not restart until coolant system is repaired.

### P0520 - Engine Oil Pressure Sensor/Switch Circuit
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

**User Message:**
> ⚠️ **High - Diagnose Immediately**
> 
> Oil pressure sensor circuit fault detected. This is likely a sensor or wiring issue, not actual low oil pressure. However, you cannot rely on your oil pressure warning light until this is fixed. Have it diagnosed immediately to confirm actual oil pressure is normal.

### C0060 - Left Front ABS Motor Circuit Malfunction
```json
{
  "severity": "Moderate",
  "drivable": true,
  "stop_driving": false,
  "may_cause_engine_damage": false,
  "may_cause_safety_issue": true,
  "affects_emissions_only": false,
  "requires_urgent_repair": true,
  "repair_urgency": "within_week",
  "drive_restrictions": {
    "max_distance": null,
    "avoid_highway": false,
    "reduced_performance": false
  }
}
```

**User Message:**
> ⚠️ **Moderate - ABS System Affected**
> 
> Anti-lock brake system has a motor circuit fault. Your regular brakes still work normally, but ABS may not activate during hard braking. Drive cautiously, especially in wet conditions. Schedule repair within a week.

### P0420 - Catalyst System Efficiency Below Threshold
```json
{
  "severity": "Moderate",
  "drivable": true,
  "stop_driving": false,
  "may_cause_engine_damage": false,
  "may_cause_safety_issue": false,
  "affects_emissions_only": true,
  "requires_urgent_repair": false,
  "repair_urgency": "within_month",
  "drive_restrictions": {
    "max_distance": null,
    "avoid_highway": false,
    "reduced_performance": false
  }
}
```

**User Message:**
> ℹ️ **Moderate - Emissions Issue**
> 
> Catalytic converter efficiency is below threshold. This affects emissions and fuel economy but does not pose immediate danger. Vehicle is safe to drive. Schedule repair within the next month, especially if you have an emissions test coming up.

### P0506 - Idle Control System RPM Lower Than Expected
```json
{
  "severity": "Moderate",
  "drivable": true,
  "stop_driving": false,
  "may_cause_engine_damage": false,
  "may_cause_safety_issue": false,
  "affects_emissions_only": false,
  "requires_urgent_repair": false,
  "repair_urgency": "within_week",
  "drive_restrictions": {
    "max_distance": null,
    "avoid_highway": false,
    "reduced_performance": true
  }
}
```

**User Message:**
> ℹ️ **Moderate - Idle Quality Issue**
> 
> Engine idle speed is lower than expected. You may experience rough idle or occasional stalling. Vehicle is safe to drive but may be inconvenient. Schedule repair within the next week.

## Implementation Strategy

### Phase 1: Add Column and Populate Defaults
```sql
-- Add the new JSONB column
ALTER TABLE obd_codes ADD COLUMN IF NOT EXISTS severity_metadata JSONB DEFAULT '{}'::jsonb;

-- Create index for JSONB queries
CREATE INDEX IF NOT EXISTS idx_obd_codes_severity_metadata_gin 
ON obd_codes USING gin(severity_metadata);
```

### Phase 2: Populate Enhanced Metadata
Create `populate_severity_metadata.py` that:
1. Analyzes each code's description and existing severity
2. Uses rule-based logic to populate all fields
3. Generates review queue for ambiguous cases
4. Applies high-confidence mappings automatically

### Phase 3: Update WhatsApp Response Logic
```python
def generate_user_message(code_data):
    """Generate contextual message based on enhanced severity metadata."""
    meta = code_data.get('severity_metadata', {})
    severity = meta.get('severity', 'Unknown')
    
    # Determine icon and header
    if meta.get('stop_driving'):
        icon = "🚨"
        header = "Critical - Stop Driving Immediately"
    elif severity == "Critical":
        icon = "🚨"
        header = "Critical - Immediate Attention Required"
    elif severity == "High":
        icon = "⚠️"
        header = "High - Urgent Repair Needed"
    elif severity == "Moderate":
        icon = "ℹ️"
        header = "Moderate"
    else:
        icon = "ℹ️"
        header = "Low"
    
    # Build contextual message
    message = f"{icon} **{header}**\n\n"
    message += f"{code_data['description']}\n\n"
    
    # Add driving guidance
    if meta.get('stop_driving'):
        message += "🛑 Stop driving immediately. "
        if meta.get('may_cause_engine_damage'):
            message += "Continuing can cause severe engine damage within minutes. "
    elif not meta.get('drivable'):
        message += "⚠️ Vehicle should not be driven. "
    elif meta.get('drive_restrictions', {}).get('max_distance'):
        max_km = meta['drive_restrictions']['max_distance']
        message += f"⚠️ Limit driving to {max_km}km or less. "
    elif meta.get('drive_restrictions', {}).get('avoid_highway'):
        message += "⚠️ Avoid highway driving. "
    
    # Add repair urgency
    urgency_map = {
        'immediate': 'Repair immediately before driving again.',
        'within_day': 'Schedule repair within 24 hours.',
        'within_week': 'Schedule repair within the next week.',
        'within_month': 'Schedule repair within the next month.',
        'non_urgent': 'Repair at your convenience.'
    }
    urgency = meta.get('repair_urgency', 'within_week')
    message += urgency_map.get(urgency, 'Schedule repair as needed.')
    
    return message
```

## Migration Path

1. **Add column** (non-breaking)
2. **Populate metadata** for all 1000 codes (with manual review queue)
3. **Update API** to return both old severity and new metadata (backward compatible)
4. **Update WhatsApp bot** to use enhanced messaging
5. **Deprecate single severity** field eventually (optional)

## Benefits

✅ More accurate user guidance
✅ Differentiates sensor faults from actual failures
✅ Provides actionable driving restrictions
✅ Separates safety from emissions issues
✅ Allows context-aware messaging
✅ Backward compatible (severity field remains)
