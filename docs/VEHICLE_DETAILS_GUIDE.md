# Vehicle Details Database Guide

## Overview

This guide explains the enhanced OBD code database schema that adds vehicle-specific information including:

- **Vehicles**: Vehicle make, model, year, and engine configurations
- **Repair Steps**: Step-by-step repair instructions (generic or vehicle-specific)
- **Parts**: Required parts with pricing and part numbers
- **Common Symptoms**: What drivers experience when a code is triggered
- **Related Codes**: Codes that often appear together

## Database Schema

### Entity Relationship Diagram

```
obd_codes (existing)
    ↓
    ├── common_symptoms (1:N)
    ├── related_codes (1:N)
    ├── repair_steps (1:N) ──→ vehicles (N:1, optional)
    └── parts (1:N) ──────────→ vehicles (N:1, optional)

vehicles (independent)
```

### Tables

#### 1. **vehicles**

Stores vehicle configurations for vehicle-specific diagnostics.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| make | VARCHAR(50) | Vehicle make (e.g., 'Toyota') |
| model | VARCHAR(50) | Vehicle model (e.g., 'Camry') |
| year | INT | Model year (1996+) |
| engine | VARCHAR(100) | Engine specification |
| transmission | VARCHAR(50) | Transmission type |
| fuel_type | VARCHAR(30) | Fuel type |
| notes | TEXT | Additional notes |

**Example:**
```sql
INSERT INTO vehicles (make, model, year, engine, transmission, fuel_type)
VALUES ('Toyota', 'Camry', 2015, '2.5L 4-cylinder', 'Automatic', 'Gasoline');
```

#### 2. **repair_steps**

Step-by-step repair instructions.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| code_id | BIGINT | References obd_codes.id |
| vehicle_id | UUID | References vehicles.id (NULL = generic) |
| step_number | INT | Step order (1, 2, 3, ...) |
| instruction | TEXT | What to do |
| tools_required | TEXT[] | Array of tool names |
| estimated_time_minutes | INT | Time estimate |
| difficulty_level | VARCHAR | Easy/Moderate/Hard/Expert |
| safety_warnings | TEXT | Safety precautions |

**Example:**
```sql
INSERT INTO repair_steps (code_id, vehicle_id, step_number, instruction, tools_required, difficulty_level)
VALUES (1, NULL, 1, 'Connect OBD scanner and verify code', ARRAY['OBD Scanner'], 'Easy');
```

#### 3. **parts**

Parts needed for repairs.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| code_id | BIGINT | References obd_codes.id |
| vehicle_id | UUID | References vehicles.id (NULL = universal) |
| part_name | VARCHAR(200) | Part description |
| part_number | VARCHAR(100) | Manufacturer part number |
| manufacturer | VARCHAR(100) | Brand/manufacturer |
| price_estimate_usd | DECIMAL(10,2) | Estimated price |
| is_oem | BOOLEAN | True if OEM, false if aftermarket |

**Example:**
```sql
INSERT INTO parts (code_id, part_name, part_number, manufacturer, price_estimate_usd, is_oem)
VALUES (1, 'Oxygen Sensor Bank 1 Sensor 2', '234-4381', 'Bosch', 45.00, false);
```

#### 4. **common_symptoms**

What drivers experience when a code appears.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| code_id | BIGINT | References obd_codes.id |
| symptom | TEXT | Symptom description |
| severity | VARCHAR | Low/Medium/High/Critical |
| frequency | VARCHAR | Rare/Occasional/Common/Always |

**Example:**
```sql
INSERT INTO common_symptoms (code_id, symptom, severity, frequency)
VALUES (1, 'Check Engine Light illuminated', 'Medium', 'Always');
```

#### 5. **related_codes**

Codes that often appear together.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| code_id | BIGINT | References obd_codes.id |
| related_code | VARCHAR(10) | Related OBD code |
| relationship_type | VARCHAR(50) | Relationship description |
| description | TEXT | Why they're related |

**Example:**
```sql
INSERT INTO related_codes (code_id, related_code, relationship_type, description)
VALUES (1, 'P0430', 'Often appears with', 'Same issue but Bank 2 catalytic converter');
```

## Installation

### Step 1: Run Migration

```bash
# In Supabase SQL Editor, run:
migrations/add_vehicle_details_tables.sql
```

This creates:
- ✅ 5 new tables
- ✅ Indexes for performance
- ✅ Triggers for auto-updating timestamps
- ✅ Helper functions and views

### Step 2: Load Sample Data (Optional)

```bash
# In Supabase SQL Editor, run:
migrations/add_vehicle_details_sample_data.sql
```

This adds sample data for:
- 5 vehicles (Toyota, Honda, Ford, Chevrolet)
- P0420, P0171, P0300 with complete details

### Step 3: Verify Installation

```sql
-- Check tables exist
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('vehicles', 'repair_steps', 'parts', 'common_symptoms', 'related_codes');

-- Check sample data loaded
SELECT * FROM vehicles LIMIT 5;
SELECT * FROM get_repair_steps('P0420');
```

## Usage

### Python API

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

# Access data
print(details['symptoms'])       # List of symptoms
print(details['repair_steps'])   # Step-by-step instructions
print(details['parts'])          # Required parts
print(details['related_codes'])  # Related OBD codes

# Format for WhatsApp
steps_text = repo.format_repair_steps_text(details['repair_steps'])
parts_text = repo.format_parts_text(details['parts'])
symptoms_text = repo.format_symptoms_text(details['symptoms'])
```

### SQL Queries

```sql
-- Get repair steps for P0420
SELECT * FROM get_repair_steps('P0420');

-- Get parts for P0420 (Toyota Camry specific)
SELECT * FROM get_parts_for_code('P0420', '<vehicle_uuid>');

-- Get symptoms
SELECT * FROM get_symptoms_for_code('P0420');

-- Get related codes
SELECT * FROM get_related_codes('P0420');

-- Find vehicle
SELECT * FROM find_vehicle('Toyota', 'Camry', 2015, '2.5L 4-cylinder');
```

## Integration with Existing Code

### 1. Update OBD Service

```python
# app/services/obd_service.py

from app.repositories.vehicle_details_repository import get_vehicle_details_repository

class OBDService:
    def __init__(self):
        self.vehicle_repo = get_vehicle_details_repository()

    async def diagnose_code_with_details(self, code: str, vehicle_context: dict):
        """Enhanced diagnosis with vehicle-specific details."""

        # Get base code info (existing)
        code_info = await self.get_code_info(code)

        # Get enhanced details (new)
        details = self.vehicle_repo.get_complete_code_details(code, vehicle_context)

        return {
            **code_info,
            'symptoms': details['symptoms'],
            'repair_steps': details['repair_steps'],
            'parts': details['parts'],
            'related_codes': details['related_codes'],
            'vehicle_matched': details['vehicle'] is not None
        }
```

### 2. Enhance WhatsApp Responses

```python
# app/services/message_router.py

def format_enhanced_diagnosis(code: str, details: dict) -> str:
    """Format diagnosis with repair steps, parts, and symptoms."""

    repo = get_vehicle_details_repository()

    message = f"*{code}*\n\n"

    # Add symptoms
    if details['symptoms']:
        message += repo.format_symptoms_text(details['symptoms'])
        message += "\n\n"

    # Add repair steps
    if details['repair_steps']:
        message += repo.format_repair_steps_text(details['repair_steps'])
        message += "\n\n"

    # Add parts
    if details['parts']:
        message += repo.format_parts_text(details['parts'])
        message += "\n\n"

    # Add related codes
    if details['related_codes']:
        message += repo.format_related_codes_text(details['related_codes'])

    return message
```

### 3. Update AI Prompts

```python
# app/services/ai_client.py

def build_enhanced_prompt(code: str, details: dict) -> str:
    """Build AI prompt with enhanced context."""

    prompt = f"Diagnose OBD code {code}.\n\n"

    # Add symptoms context
    if details['symptoms']:
        prompt += "Common symptoms:\n"
        for symptom in details['symptoms']:
            prompt += f"- {symptom['symptom']} ({symptom['severity']})\n"
        prompt += "\n"

    # Add repair steps context
    if details['repair_steps']:
        prompt += f"There are {len(details['repair_steps'])} documented repair steps.\n\n"

    # Add parts context
    if details['parts']:
        prompt += "Common parts needed:\n"
        for part in details['parts'][:3]:  # Top 3
            prompt += f"- {part['part_name']}\n"
        prompt += "\n"

    return prompt
```

## Data Population Strategy

### Option 1: Manual Entry (Recommended for Critical Codes)

For high-priority codes (P0420, P0171, P0300, etc.):

1. Research authoritative sources (Mitchell, Alldata, manufacturer TSBs)
2. Add vehicle-specific repair procedures
3. Include OEM and aftermarket part numbers
4. Document common symptoms from repair forums

### Option 2: Bulk Import from CSV

```python
import pandas as pd
from app.repositories.vehicle_details_repository import get_vehicle_details_repository

# Load CSV
df = pd.read_csv('repair_steps.csv')

# Insert batch
repo = get_vehicle_details_repository()
for _, row in df.iterrows():
    # Insert logic here
    pass
```

### Option 3: API Integration

Integrate with automotive data APIs:
- **RepairPal API** - Repair cost estimates
- **Car MD API** - OBD code information
- **Mitchell1 API** - Professional repair data

### Option 4: AI-Generated Content (with Review)

Use AI to generate initial content, then manually review:

```python
from app.services.ai_client import get_ai_client

ai = get_ai_client()

prompt = """
Generate 5 repair steps for OBD code P0420 on a 2015 Toyota Camry 2.5L.
Format as JSON array with step_number, instruction, difficulty_level.
"""

steps = ai.complete(prompt)  # Returns structured data
# Review and insert
```

## Best Practices

### Generic vs. Vehicle-Specific

- **Generic steps** (`vehicle_id = NULL`): Universal procedures that apply to all vehicles
- **Vehicle-specific steps**: Manufacturer-specific procedures, TSBs, known issues

Example:
```sql
-- Generic step (applies to all)
INSERT INTO repair_steps (code_id, vehicle_id, step_number, instruction)
VALUES (1, NULL, 1, 'Connect OBD scanner and verify code');

-- Toyota-specific step
INSERT INTO repair_steps (code_id, vehicle_id, step_number, instruction)
VALUES (1, '<toyota_camry_id>', 10, 'Check TSB T-SB-0087-14 for software update');
```

### Severity Guidelines

**Symptoms:**
- **Critical**: Engine damage risk, unsafe to drive
- **High**: Significant performance impact
- **Medium**: Noticeable but drivable
- **Low**: Minor or intermittent

**Difficulty:**
- **Easy**: DIY-friendly, basic tools
- **Moderate**: Some mechanical knowledge needed
- **Hard**: Advanced skills, special tools
- **Expert**: Professional repair recommended

### Part Information

Always include:
- ✅ Part name with location (e.g., "O2 Sensor Bank 1 Sensor 2")
- ✅ OEM part number
- ✅ Aftermarket equivalent (if available)
- ✅ Price estimate (updated annually)
- ✅ Compatibility notes

## Performance Considerations

### Indexes

All tables have indexes on frequently queried columns:

```sql
-- Existing indexes
CREATE INDEX idx_repair_steps_code_id ON repair_steps (code_id);
CREATE INDEX idx_parts_code_id ON parts (code_id);
CREATE INDEX idx_common_symptoms_code_id ON common_symptoms (code_id);
CREATE INDEX idx_related_codes_code_id ON related_codes (code_id);
```

### Query Optimization

Use helper functions instead of manual JOINs:

```sql
-- ✅ Good: Use helper function
SELECT * FROM get_repair_steps('P0420');

-- ❌ Avoid: Manual JOIN
SELECT rs.* FROM repair_steps rs
INNER JOIN obd_codes oc ON oc.id = rs.code_id
WHERE oc.code = 'P0420';
```

### Caching Strategy

Cache complete code details at the application level:

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_code_details(code: str) -> dict:
    repo = get_vehicle_details_repository()
    return repo.get_complete_code_details(code)
```

## Testing

### Unit Tests

```python
# tests/test_vehicle_details_repository.py

def test_get_repair_steps():
    repo = get_vehicle_details_repository()
    steps = repo.get_repair_steps('P0420')
    assert len(steps) > 0
    assert steps[0]['step_number'] == 1

def test_find_vehicle():
    repo = get_vehicle_details_repository()
    vehicle = repo.find_vehicle('Toyota', 'Camry', 2015, '2.5L 4-cylinder')
    assert vehicle is not None
    assert vehicle['make'] == 'Toyota'
```

### Integration Tests

```python
def test_complete_diagnosis_flow():
    repo = get_vehicle_details_repository()

    details = repo.get_complete_code_details(
        'P0420',
        vehicle_context={'make': 'Toyota', 'model': 'Camry', 'year': 2015}
    )

    assert details['code'] == 'P0420'
    assert len(details['symptoms']) > 0
    assert len(details['repair_steps']) > 0
    assert details['vehicle'] is not None
```

## Migration from Existing Data

If you have existing `vehicle_overrides` table data:

```sql
-- Migrate vehicle_overrides to new schema
INSERT INTO vehicles (make, model, year, engine)
SELECT DISTINCT make, model, year, engine
FROM vehicle_overrides
ON CONFLICT (make, model, year, engine) DO NOTHING;

-- Migrate known_issues to repair_steps
INSERT INTO repair_steps (code_id, vehicle_id, step_number, instruction)
SELECT
    oc.id,
    v.id,
    ROW_NUMBER() OVER (PARTITION BY vo.id ORDER BY idx) + 100,  -- Start at step 100
    issue
FROM vehicle_overrides vo
INNER JOIN obd_codes oc ON oc.code = vo.code
INNER JOIN vehicles v ON v.make = vo.make AND v.model = vo.model
                      AND v.year = vo.year::int AND v.engine = vo.engine
CROSS JOIN LATERAL jsonb_array_elements_text(vo.known_issues) WITH ORDINALITY AS t(issue, idx);
```

## Roadmap

### Phase 1: Core Implementation ✅
- [x] Create database tables
- [x] Add Python repository layer
- [x] Create sample data
- [x] Write documentation

### Phase 2: Data Population
- [ ] Add top 50 most common codes
- [ ] Partner with automotive data providers
- [ ] Community contribution system

### Phase 3: Enhanced Features
- [ ] Video tutorials (YouTube links)
- [ ] Image uploads (component photos)
- [ ] Cost estimation API integration
- [ ] User-submitted repair experiences

### Phase 4: AI Integration
- [ ] AI-powered repair step generation
- [ ] Natural language symptom matching
- [ ] Predictive maintenance recommendations

## Support

For questions or issues:
- Check documentation: `docs/`
- Run sample queries: `migrations/add_vehicle_details_sample_data.sql`
- Review Python examples: `app/repositories/vehicle_details_repository.py`

---

**Last Updated**: 2026-07-06  
**Schema Version**: 1.0  
**Status**: ✅ Production Ready
