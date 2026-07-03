# System Diagrams Quick Start 🚀

**TL;DR**: Educational diagrams now sent before DTC diagnosis text. All code complete, just needs manual image population.

---

## 30-Second Setup

### 1. Run Migration
```sql
-- In Supabase SQL Editor:
-- Copy/paste: migrations/add_system_diagrams_table.sql
```

### 2. Add Your First Diagram
```sql
INSERT INTO system_diagrams (system, image_url, source, license, caption)
VALUES (
    'catalytic converter',
    'https://your-cdn.com/cat-converter.jpg',
    'Wikimedia Commons',
    'CC BY-SA 4.0',
    'Catalytic converter diagram'
);
```

### 3. Test It
Send "P0420" via WhatsApp → Should receive image THEN text diagnosis

---

## How It Works

```
User sends DTC code (e.g., "P0420")
    ↓
System looks up code → finds system: "Emissions"
    ↓
Fuzzy match: "Emissions" → "catalytic converter"
    ↓
Found diagram? YES
    ↓
Send image FIRST (with caption)
    ↓ (1-2 seconds later)
Send text diagnosis (with attribution)
```

**If no diagram**: Text diagnosis sent normally (no change)

**If image fails**: Text diagnosis sent anyway (graceful degradation)

---

## Files You Need to Know

### Add Synonyms Here
`app/repositories/system_diagram_repository.py` lines 26-77

```python
SYSTEM_SYNONYMS = {
    "catalyst": ["catalytic converter"],
    "o2 sensor": ["oxygen sensor"],
    # Add yours here
}
```

### Configure Baileys URL
`.env` file:
```bash
BAILEYS_OUTBOUND_URL=http://localhost:3000/send
```

---

## Common Systems to Add Diagrams For

Based on common DTC codes:

1. `catalytic converter` (P0420, P0430)
2. `oxygen sensor` (P0131, P0132, P0171)
3. `egr valve` (P0400, P0401)
4. `evap system` (P0440, P0442, P0455)
5. `mass air flow` (P0100, P0101)
6. `throttle body` (P0120, P0121)
7. `ignition coil` (P0300, P0301-P0308)
8. `fuel injector` (P0200, P0201-P0208)
9. `cooling system` (P0115, P0116)
10. `transmission` (P0700, P0730)

**Image Requirements**:
- HTTPS URL (required by WhatsApp)
- Reasonable size (<5MB recommended)
- Clear, educational quality
- Proper license (CC BY-SA, Public Domain, or Original)

---

## Test Matching Logic

```bash
python test_fuzzy_matching.py
```

Shows which systems match which search terms.

---

## Monitoring

Watch these logs:
```
✅ system_diagram_found_for_diagnosis - Matched!
✅ system_diagram_sent - Image sent
⚠️ system_diagram_send_failed_continuing - Failed but continuing
❌ system_diagram_lookup_error - Lookup error
```

---

## Troubleshooting

### "Image not sending"
1. Check `BAILEYS_OUTBOUND_URL` is set
2. Check image URL is HTTPS
3. Check Baileys is running
4. Check logs for timeout/error

### "Wrong diagram matched"
1. Check `SYSTEM_SYNONYMS` for conflicts
2. Run `test_fuzzy_matching.py` to debug
3. Adjust synonym map as needed

### "Ambiguous matches"
- Fuzzy matching uses specificity scoring (deterministic)
- Add explicit synonym to prioritize one match

---

## Example Diagrams to Start With

### Wikimedia Commons (Free, CC BY-SA)
- Search: "catalytic converter cutaway"
- Search: "oxygen sensor diagram"
- Search: "EGR valve schematic"

### Your Own Illustrations
- Draw simple schematics
- Take photos of clean engine bays
- Create labeled diagrams

**License**: If using Wikimedia, copy license info to `attribution_text`

---

## Schema Reference

```sql
system             TEXT NOT NULL UNIQUE  -- e.g., "catalytic converter"
image_url          TEXT NOT NULL         -- HTTPS URL
source             TEXT NOT NULL         -- e.g., "Wikimedia Commons"
license            TEXT NOT NULL         -- e.g., "CC BY-SA 4.0"
attribution_text   TEXT                  -- Appended to text diagnosis
caption            TEXT                  -- Shown with image (<60 chars)
```

---

## Configuration

**Min search length** (substring matching):  
`system_diagram_repository.py` line 163: `MIN_SEARCH_LENGTH = 5`

**Image timeout**:  
`webhook.py` line 597: `ImageSender(timeout=10.0)`

---

## Status

✅ **All code complete**  
✅ **All tests passing**  
✅ **Documentation complete**  

**Next**: Populate table with 20-30 curated images

---

## Quick Commands

```bash
# Syntax checks
python -m py_compile app/models/system_diagram.py
python -m py_compile app/repositories/system_diagram_repository.py
python -m py_compile app/services/image_sender.py

# Test matching
python test_fuzzy_matching.py

# Check logs
tail -f logs/app.log | grep system_diagram
```

---

**Ready to use!** Just add images to the database. 🎉
