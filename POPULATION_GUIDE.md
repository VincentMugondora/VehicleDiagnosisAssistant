# Database Population Guide

**Complete guide to populating all database tables with real data**

Last Updated: 2026-07-06

---

## Quick Start

### Run the Complete Population Script

```bash
cd C:\Users\vinmu\Desktop\VehicleDiagnosisAssistant
python scripts\populate_all_tables.py
```

This will populate:
- ✅ `obd_codes` (132+ codes)
- ✅ `system_diagrams` (10 diagrams)
- ✅ `code_vehicle_fitment` (sample data for top codes)
- ✅ `repair_steps` (sample data for top codes)
- ✅ `parts` (sample data for top codes)
- ✅ `common_symptoms` (sample data for top codes)
- ✅ `related_codes` (sample data for top codes)

---

## What Gets Populated

### 1. OBD Codes (`obd_codes`)

**Source:** `scripts/comprehensive_obd_codes.py`

**Data Included:**
- 132+ diagnostic trouble codes
- P0xxx (generic powertrain)
- P1xxx (manufacturer-specific)
- P2xxx (generic powertrain)
- P3xxx (generic)
- B, C, U codes (body, chassis, network)

**Fields Populated:**
- `code` - DTC code (e.g., "P0420")
- `description` - What the code means
- `symptoms` - What driver experiences
- `common_causes` - Why it triggers
- `generic_fixes` - How to fix it
- `system` - Vehicle system (e.g., "Emissions")
- `severity` - Urgency level

### 2. System Diagrams (`system_diagrams`)

**Source:** Wikimedia Commons (Public Domain / CC-BY-SA)

**10 Diagrams Included:**
1. Catalytic Converter
2. Oxygen Sensor
3. Mass Air Flow Sensor
4. Throttle Body
5. EVAP System
6. Fuel Injector
7. EGR Valve
8. Ignition Coil
9. Camshaft Position Sensor
10. Crankshaft Position Sensor

**Note:** The URLs in the script are placeholders. You need to:
1. Find actual free/public domain images
2. Update the URLs in `populate_all_tables.py`
3. Or host your own images

**Recommended Image Sources:**
- Wikimedia Commons: https://commons.wikimedia.org
- Search: `"catalytic converter" site:commons.wikimedia.org`
- Filter by: Public Domain or CC-BY-SA licenses
- Get direct image URLs (right-click → Copy Image Address)

### 3. Vehicle Fitment (`code_vehicle_fitment`)

**Sample Data for Top Codes:**
- P0420 (Catalytic Converter)
- P0300 (Random Misfire)
- P0171 (System Too Lean)
- P0128 (Coolant Temperature)

**Vehicles Included:**
- Toyota Camry, Corolla, Prius
- Honda Civic, Accord, CR-V
- Ford F-150, Focus, Explorer
- Chevrolet Silverado

**Fields:**
- Code applies to specific make/model/year/engine combinations

### 4. Repair Steps (`repair_steps`)

**Step-by-step instructions for:**
- P0420 (6 steps)
- P0300 (6 steps)
- P0171 (6 steps)

Professional diagnostic and repair procedures.

### 5. Parts (`parts`)

**Required parts lists for:**
- P0420: Catalytic converter, O2 sensors, gaskets
- P0300: Spark plugs, ignition coils, wires
- P0171: MAF sensor, vacuum hoses, fuel components

### 6. Common Symptoms (`common_symptoms`)

**Driver-reported symptoms for:**
- P0420: Check light, poor MPG, sulfur smell
- P0300: Flashing light, rough idle, power loss
- P0171: Rough idle, hesitation, hard start
- P0128: Slow warmup, poor heater

### 7. Related Codes (`related_codes`)

**Code relationships:**
- P0420 → P0430, P0137, P0138, P0141
- P0300 → P0301-P0308 (cylinder-specific)
- P0171 → P0174, P0101, P0106, P0172

---

## Customizing the Data

### Adding More OBD Codes

Edit `scripts/comprehensive_obd_codes.py`:

```python
ALL_CODES = {
    "P0XXX": {
        "description": "Your description",
        "symptoms": "What happens",
        "common_causes": "Why it occurs",
        "generic_fixes": "How to fix",
        "system": "System name",
        "severity": "High/Medium/Low"
    },
    # ... more codes
}
```

### Adding More System Diagrams

Edit `populate_all_tables.py`, update `SYSTEM_DIAGRAMS`:

```python
SYSTEM_DIAGRAMS = [
    {
        "system": "your system name",
        "image_url": "https://your-actual-image-url.jpg",
        "source": "Source name",
        "license": "License type",
        "caption": "Short description",
        "attribution_text": "Attribution if required"
    },
    # ... more diagrams
]
```

**Finding Free Images:**

1. **Wikimedia Commons** (Recommended)
   - https://commons.wikimedia.org
   - Search: `"automotive component name"`
   - Filter: Public Domain or CC-BY-SA
   - Get direct URL: Right-click image → Copy Image Address

2. **Unsplash** (Free license)
   - https://unsplash.com
   - Search automotive parts
   - Free to use, no attribution required

3. **Pixabay** (Free license)
   - https://pixabay.com
   - Free for commercial use

4. **Your Own Images**
   - Take photos of parts
   - Upload to your own hosting
   - Use those URLs

### Adding More Vehicle Fitment

Edit `VEHICLE_FITMENT_DATA`:

```python
VEHICLE_FITMENT_DATA = {
    "P0420": [
        {
            "make": "Toyota",
            "model": "Camry",
            "year_start": 2007,
            "year_end": 2020,
            "engine": "2.5L"
        },
        # Add more vehicles
    ],
}
```

### Adding More Repair Steps

Edit `REPAIR_STEPS_DATA`:

```python
REPAIR_STEPS_DATA = {
    "P0420": [
        {"step_number": 1, "instruction": "First step"},
        {"step_number": 2, "instruction": "Second step"},
        # ... more steps
    ],
}
```

---

## Verification After Population

### Check OBD Codes

```sql
-- Count codes
SELECT COUNT(*) FROM obd_codes;

-- Sample codes
SELECT code, description, system
FROM obd_codes
WHERE code IN ('P0420', 'P0300', 'P0171')
ORDER BY code;
```

### Check System Diagrams

```sql
-- Count diagrams
SELECT COUNT(*) FROM system_diagrams;

-- View all
SELECT system, caption, license
FROM system_diagrams
ORDER BY system;
```

### Check DTC Details

```sql
-- Vehicle fitment for P0420
SELECT make, model, year_start, year_end, engine
FROM code_vehicle_fitment
WHERE code_id = 'P0420';

-- Repair steps for P0420
SELECT step_number, instruction
FROM repair_steps
WHERE code_id = 'P0420'
ORDER BY step_number;

-- Parts for P0420
SELECT part_name, part_number
FROM parts
WHERE code_id = 'P0420';

-- Symptoms for P0420
SELECT symptom
FROM common_symptoms
WHERE code_id = 'P0420';

-- Related codes for P0420
SELECT related_code
FROM related_codes
WHERE code_id = 'P0420';
```

---

## Expanding the Database

### Priority 1: More Common Codes

Add DTC details for these popular codes:

- P0301-P0308 (Cylinder misfires)
- P0174 (System Too Lean Bank 2)
- P0442 (EVAP Leak Small)
- P0455 (EVAP Leak Large)
- P0101 (MAF Sensor Range)
- P0340 (Camshaft Position Sensor)
- P0335 (Crankshaft Position Sensor)

### Priority 2: More Vehicle Models

Expand fitment data to include:

- Nissan (Altima, Sentra, Rogue)
- Mazda (Mazda3, CX-5)
- Volkswagen (Jetta, Passat)
- Hyundai (Elantra, Sonata)
- Kia (Optima, Forte)

### Priority 3: More System Diagrams

Add diagrams for:

- Transmission systems
- Cooling system components
- Brake system components
- Suspension components
- Electrical system components

---

## Data Sources

### For OBD Codes

1. **OBD-II Standards** (SAE J2012)
   - Generic codes are standardized
   - Public information

2. **GitHub Repositories**
   - https://github.com/OBDb/OBDb
   - https://github.com/wal33d/dtc-lookup
   - Community-maintained databases

3. **Automotive Manuals**
   - Factory service manuals
   - Alldata / Mitchell databases (paid)

### For Repair Procedures

1. **OEM Service Manuals**
2. **Chilton / Haynes Manuals**
3. **Professional Forums**
   - iATN.net
   - MechanicAdvice subreddit

### For Vehicle Fitment

1. **VIN Decoders**
2. **Parts Catalogs** (RockAuto, AutoZone)
3. **Service Bulletins** (TSBs)

---

## Automated Population (Future)

### Option 1: Web Scraping (Legal Sources Only)

```python
# Example: Scrape from OBDb GitHub
import requests

url = "https://raw.githubusercontent.com/OBDb/OBDb/main/data/generic/powertrain.json"
response = requests.get(url)
codes = response.json()
# Process and import
```

### Option 2: API Integration

Some services offer OBD data APIs:
- CarMD API
- OBD Auto Doctor API
- (Most are paid)

### Option 3: Community Contributions

1. Create contribution form
2. Users submit code details
3. Admin reviews and approves
4. Automatic import to database

---

## Maintenance

### Weekly Tasks

1. Review new codes from `external_obd_cache`
2. Add popular codes to main database
3. Update vehicle fitment for recent model years

### Monthly Tasks

1. Add new system diagrams
2. Expand vehicle coverage
3. Update repair procedures based on feedback

### Quarterly Tasks

1. Review and update outdated information
2. Add new vehicle makes/models
3. Expand code coverage

---

## Population Checklist

After running the script, verify:

- [ ] `obd_codes` has 132+ rows
- [ ] `system_diagrams` has 10 rows
- [ ] `code_vehicle_fitment` has data
- [ ] `repair_steps` has data
- [ ] `parts` has data
- [ ] `common_symptoms` has data
- [ ] `related_codes` has data
- [ ] Image URLs in `system_diagrams` actually work
- [ ] Test code lookup: P0420 returns full details
- [ ] Test system diagram retrieval

---

## Troubleshooting

### Script Fails to Import

**Error:** "Module not found"
```bash
pip install requests
python scripts\populate_all_tables.py
```

### Image URLs Don't Work

1. Open `populate_all_tables.py`
2. Update `SYSTEM_DIAGRAMS` with real URLs
3. Test URLs in browser first
4. Re-run script

### Foreign Key Errors

Make sure `obd_codes` table is populated first before populating detail tables.

Run in order:
1. OBD codes
2. System diagrams
3. DTC details (all can run in parallel after step 1)

---

## Next Steps

1. ✅ Run `python scripts\populate_all_tables.py`
2. ✅ Verify all tables have data
3. ✅ Test with WhatsApp bot (send P0420)
4. ✅ Check system diagrams display
5. ⏳ Gradually expand data over time

---

**Script Location:** `scripts/populate_all_tables.py`  
**Data Source:** `scripts/comprehensive_obd_codes.py`  
**Estimated Time:** 2-5 minutes to populate
