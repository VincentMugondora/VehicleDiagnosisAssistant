# Vehicle Details Enhancement - Quick Start

## What's New? 🚗

Your Vehicle Diagnosis Assistant now includes comprehensive vehicle-specific information for OBD codes!

### New Features

✅ **Vehicles** - Make, model, year, engine configurations  
✅ **Repair Steps** - Step-by-step instructions (generic + vehicle-specific)  
✅ **Parts** - Required parts with pricing and part numbers  
✅ **Symptoms** - What drivers experience when codes appear  
✅ **Related Codes** - Codes that often appear together  

## Quick Setup

### 1. Run Database Migration

```bash
# Open Supabase SQL Editor and run:
migrations/add_vehicle_details_tables.sql
```

**Creates:**
- 5 new tables with indexes
- Helper functions for easy queries
- Auto-updating timestamp triggers

### 2. Load Sample Data (Optional)

```bash
# In Supabase SQL Editor:
migrations/add_vehicle_details_sample_data.sql
```

**Includes:**
- 5 sample vehicles (Toyota, Honda, Ford, Chevrolet)
- Complete details for P0420, P0171, P0300

### 3. Test It

```python
from app.repositories.vehicle_details_repository import get_vehicle_details_repository

repo = get_vehicle_details_repository()

# Get complete code details
details = repo.get_complete_code_details(
    code='P0420',
    vehicle_context={
        'make': 'Toyota',
        'model': 'Camry',
        'year': 2015,
        'engine': '2.5L 4-cylinder'
    }
)

# Format for WhatsApp
print(repo.format_repair_steps_text(details['repair_steps']))
print(repo.format_parts_text(details['parts']))
print(repo.format_symptoms_text(details['symptoms']))
```

## Database Schema

```
vehicles
├── id (UUID)
├── make (Toyota, Honda, Ford...)
├── model (Camry, Civic, F-150...)
├── year (2015, 2018, 2020...)
└── engine (2.5L 4-cylinder, 3.5L V6...)

repair_steps
├── code_id → obd_codes.id
├── vehicle_id → vehicles.id (NULL = generic)
├── step_number (1, 2, 3...)
├── instruction (text)
├── tools_required (array)
├── difficulty_level (Easy/Moderate/Hard/Expert)
└── estimated_time_minutes

parts
├── code_id → obd_codes.id
├── vehicle_id → vehicles.id (NULL = universal)
├── part_name
├── part_number
├── manufacturer
├── price_estimate_usd
└── is_oem (true/false)

common_symptoms
├── code_id → obd_codes.id
├── symptom (text)
├── severity (Low/Medium/High/Critical)
└── frequency (Rare/Occasional/Common/Always)

related_codes
├── code_id → obd_codes.id
├── related_code (P0430, P0171...)
├── relationship_type (Often appears with, May cause...)
└── description
```

## SQL Helper Functions

```sql
-- Get repair steps for a code
SELECT * FROM get_repair_steps('P0420');
SELECT * FROM get_repair_steps('P0420', '<vehicle_id>');

-- Get parts needed
SELECT * FROM get_parts_for_code('P0420');
SELECT * FROM get_parts_for_code('P0420', '<vehicle_id>');

-- Get symptoms
SELECT * FROM get_symptoms_for_code('P0420');

-- Get related codes
SELECT * FROM get_related_codes('P0420');

-- Find vehicle
SELECT find_vehicle('Toyota', 'Camry', 2015, '2.5L 4-cylinder');
```

## Python API

### Basic Usage

```python
from app.repositories.vehicle_details_repository import get_vehicle_details_repository

repo = get_vehicle_details_repository()

# Find a vehicle
vehicle = repo.find_vehicle('Toyota', 'Camry', 2015, '2.5L 4-cylinder')

# Get repair steps
steps = repo.get_repair_steps('P0420')
steps_vehicle_specific = repo.get_repair_steps('P0420', vehicle['id'])

# Get parts
parts = repo.get_parts('P0420')
parts_vehicle_specific = repo.get_parts('P0420', vehicle['id'])

# Get symptoms
symptoms = repo.get_symptoms('P0420')

# Get related codes
related = repo.get_related_codes('P0420')
```

### Complete Details

```python
# Get everything at once
details = repo.get_complete_code_details(
    code='P0420',
    vehicle_context={
        'make': 'Toyota',
        'model': 'Camry',
        'year': 2015,
        'engine': '2.5L 4-cylinder'
    }
)

# Returns:
{
    'code': 'P0420',
    'vehicle': {...},           # Matched vehicle or None
    'symptoms': [...],          # List of symptoms
    'repair_steps': [...],      # Step-by-step instructions
    'parts': [...],             # Required parts
    'related_codes': [...]      # Related OBD codes
}
```

### Format for WhatsApp

```python
# Format as text for WhatsApp messages
steps_text = repo.format_repair_steps_text(details['repair_steps'])
parts_text = repo.format_parts_text(details['parts'])
symptoms_text = repo.format_symptoms_text(details['symptoms'])
related_text = repo.format_related_codes_text(details['related_codes'])

# Send to user
message = f"""
{symptoms_text}

{steps_text}

{parts_text}

{related_text}
"""
```

## Integration Examples

### 1. Enhance OBD Diagnosis

```python
# app/services/obd_service.py

from app.repositories.vehicle_details_repository import get_vehicle_details_repository

async def diagnose_with_details(code: str, vehicle_context: dict):
    # Get base diagnosis (existing)
    diagnosis = await get_code_info(code)
    
    # Add enhanced details (new)
    repo = get_vehicle_details_repository()
    details = repo.get_complete_code_details(code, vehicle_context)
    
    return {
        **diagnosis,
        'symptoms': details['symptoms'],
        'repair_steps': details['repair_steps'],
        'parts': details['parts'],
        'related_codes': details['related_codes']
    }
```

### 2. Update WhatsApp Responses

```python
# app/services/message_router.py

def format_diagnosis_message(code: str, details: dict) -> str:
    repo = get_vehicle_details_repository()
    
    message = [f"*Diagnosis: {code}*\n"]
    
    # Add symptoms
    if details['symptoms']:
        message.append(repo.format_symptoms_text(details['symptoms']))
    
    # Add repair steps
    if details['repair_steps']:
        message.append("\n" + repo.format_repair_steps_text(details['repair_steps']))
    
    # Add parts
    if details['parts']:
        message.append("\n" + repo.format_parts_text(details['parts']))
    
    return "\n\n".join(message)
```

### 3. Enhance AI Context

```python
# app/services/ai_client.py

def build_ai_prompt(code: str, details: dict) -> str:
    prompt = f"Diagnose {code}.\n\n"
    
    # Add symptoms as context
    if details['symptoms']:
        prompt += "Common symptoms:\n"
        for s in details['symptoms']:
            prompt += f"- {s['symptom']}\n"
    
    # Add repair steps count
    if details['repair_steps']:
        prompt += f"\nThere are {len(details['repair_steps'])} documented repair steps.\n"
    
    return prompt
```

## Sample Data

### P0420 Example (Catalyst Efficiency)

**Symptoms:**
- Check Engine Light (Medium severity, Always)
- Reduced fuel economy (Low severity, Common)
- Failed emissions test (High severity, Always)

**Repair Steps:**
1. Verify code with OBD scanner (Easy, 15 min)
2. Inspect O2 sensor wiring (Easy, 30 min)
3. Check for exhaust leaks (Moderate, 20 min)
4. Test oxygen sensors (Moderate, 30 min)
5. Inspect catalytic converter (Moderate, 20 min)
6. Replace catalytic converter if needed (Hard, 120 min)

**Parts:**
- Downstream O2 Sensor: $45 (Bosch, aftermarket)
- Upstream O2 Sensor: $55 (Denso, aftermarket)
- Catalytic Converter: $250-$850 (Universal to OEM)

**Related Codes:**
- P0430 (Often appears with) - Bank 2 catalyst
- P0171 (May cause) - Lean condition damages catalyst
- P0300 (Caused by) - Misfires damage catalyst

## Data Population

### Option 1: Manual Entry

```sql
-- Add a vehicle
INSERT INTO vehicles (make, model, year, engine)
VALUES ('Toyota', 'Corolla', 2020, '1.8L 4-cylinder');

-- Add repair steps
INSERT INTO repair_steps (code_id, step_number, instruction, difficulty_level)
VALUES (1, 1, 'Connect OBD scanner', 'Easy');

-- Add parts
INSERT INTO parts (code_id, part_name, part_number, price_estimate_usd)
VALUES (1, 'O2 Sensor', '234-4381', 45.00);
```

### Option 2: CSV Import

```python
import pandas as pd

df = pd.read_csv('repair_steps.csv')
# Columns: code, step_number, instruction, difficulty_level

for _, row in df.iterrows():
    # Insert into database
    pass
```

### Option 3: AI Generation

Use AI to generate initial content, then manually review.

## Files Created

1. **`migrations/add_vehicle_details_tables.sql`** - Database schema
2. **`migrations/add_vehicle_details_sample_data.sql`** - Sample data
3. **`app/repositories/vehicle_details_repository.py`** - Python API
4. **`docs/VEHICLE_DETAILS_GUIDE.md`** - Complete documentation
5. **`VEHICLE_DETAILS_README.md`** - This quick start guide

## Next Steps

### Immediate
1. ✅ Run `add_vehicle_details_tables.sql` in Supabase
2. ✅ Run `add_vehicle_details_sample_data.sql` (optional)
3. ✅ Test with sample queries

### Short Term
- [ ] Add top 20 most common codes (P0420, P0171, P0300, etc.)
- [ ] Integrate into existing OBD diagnosis flow
- [ ] Update WhatsApp message formatting

### Long Term
- [ ] Add 100+ most common codes
- [ ] Partner with automotive data providers
- [ ] Add video tutorials and images
- [ ] Build community contribution system

## Testing

```bash
# Test SQL functions
psql> SELECT * FROM get_repair_steps('P0420');
psql> SELECT * FROM get_parts_for_code('P0420');

# Test Python repository
python3 -c "
from app.repositories.vehicle_details_repository import get_vehicle_details_repository
repo = get_vehicle_details_repository()
details = repo.get_complete_code_details('P0420')
print(f'Found {len(details[\"repair_steps\"])} repair steps')
"
```

## Documentation

- **Quick Start**: `VEHICLE_DETAILS_README.md` (this file)
- **Complete Guide**: `docs/VEHICLE_DETAILS_GUIDE.md`
- **Database Schema**: `migrations/add_vehicle_details_tables.sql`
- **Python API**: `app/repositories/vehicle_details_repository.py`

## Support

Questions? Check:
- SQL comments in migration files
- Python docstrings in repository class
- Complete guide in `docs/VEHICLE_DETAILS_GUIDE.md`

---

**Status**: ✅ Ready to use  
**Version**: 1.0  
**Last Updated**: 2026-07-06
