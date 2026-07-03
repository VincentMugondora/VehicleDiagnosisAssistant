# System Diagrams: Complete Population Workflow 🚀

**End-to-end guide from sourcing to production**

---

## Overview

You now have **three helper tools** to make manual image population smooth:

1. **CSV Import Tool** - Bulk import from spreadsheet (validates, previews, inserts)
2. **URL Verification Tool** - Check all URLs are accessible and valid
3. **Lookup Test Tool** - Test matching logic for specific DTC codes

---

## Complete Workflow

### Phase 1: Source Images (Manual - You Do This)

**Time Estimate**: 2-4 hours for 20-30 images

#### Step 1.1: Set Up Spreadsheet

```bash
# Use the provided template
cp system_diagrams_template.csv system_diagrams.csv
```

Open `system_diagrams.csv` in Excel, Google Sheets, or text editor.

#### Step 1.2: Find Images on Wikimedia Commons

Go to **commons.wikimedia.org** and search for each system:

**High-Priority Systems** (start here):
1. catalytic converter
2. oxygen sensor
3. EGR valve
4. EVAP system
5. mass air flow sensor
6. throttle body
7. ignition coil
8. spark plugs

**Search Tips**:
- Add "diagram" or "cutaway" to search (e.g., "catalytic converter diagram")
- Filter by license if possible (look for CC BY-SA, CC0, Public Domain)
- Prefer labeled/technical diagrams over plain photos

#### Step 1.3: Extract Metadata for Each Image

For each image, click through to the **file page** and record:

| CSV Column | Where to Find | Example |
|------------|---------------|---------|
| `system` | Your choice (must match DTC system) | `catalytic converter` |
| `image_url` | Right-click image → Copy image address | `https://upload.wikimedia.org/...` |
| `source` | Always (for Wikimedia) | `Wikimedia Commons` |
| `license` | License section on file page | `CC BY-SA 4.0` |
| `caption` | Write yourself (<60 chars!) | `Catalytic converter cutaway` |
| `attribution_text` | Author from file page | `Diagram by John Doe, via Wikimedia Commons` |

**License Guide** (from `DIAGRAM_SOURCING_GUIDE.md`):
- ✅ **Use**: Public Domain, CC0, CC BY, CC BY-SA
- ❌ **Avoid**: CC BY-NC (non-commercial), CC BY-ND (no derivatives)

#### Step 1.4: Fill CSV

Example completed row:
```csv
catalytic converter,https://upload.wikimedia.org/wikipedia/commons/abc/Cat.jpg,Wikimedia Commons,CC BY-SA 4.0,Catalytic converter internals,"Diagram by John Doe, via Wikimedia Commons"
```

**Tips**:
- Keep captions under 60 characters (WhatsApp truncates longer)
- For Public Domain images, `attribution_text` can be empty (but recommended to include source)
- Use direct file URLs (right-click → copy image address), not wiki page URLs

---

### Phase 2: Validate (Dry Run)

**Time Estimate**: 2 minutes

```bash
python tools/import_diagrams_from_csv.py system_diagrams.csv --dry-run
```

**What it checks**:
- ✅ All required fields present
- ✅ URLs are HTTPS (WhatsApp requirement)
- ✅ Captions under 60 characters
- ✅ CSV format correct

**Output**:
```
📂 Reading: system_diagrams.csv
✅ Validated 25 records

==========================================
IMPORT PREVIEW
==========================================

1. catalytic converter
   URL: https://upload.wikimedia.org/wikipedia/commons/abc...
   Source: Wikimedia Commons
   License: CC BY-SA 4.0
   Caption: Catalytic converter cutaway
   Attribution: Diagram by John Doe, via Wikimedia Commons

2. oxygen sensor
   ...

==========================================
Total: 25 diagrams
==========================================

🔍 DRY RUN - No changes made
```

**If errors**: Fix in CSV and re-run.

---

### Phase 3: Import to Database

**Time Estimate**: 1 minute

```bash
python tools/import_diagrams_from_csv.py system_diagrams.csv
```

**What it does**:
1. Validates all rows
2. Shows preview
3. **Asks for confirmation**: `Import these diagrams to database? (yes/no):`
4. Inserts into `system_diagrams` table
5. Skips duplicates (if re-running)
6. Reports success/errors

**Output**:
```
📂 Reading: system_diagrams.csv
✅ Validated 25 records

[... preview ...]

❓ Import these diagrams to database? (yes/no): yes

📡 Connecting to Supabase...
📥 Importing...

✅ 1/25: 'catalytic converter' imported
✅ 2/25: 'oxygen sensor' imported
⚠️  3/25: 'EGR valve' already exists, skipping
...

==========================================
IMPORT COMPLETE
==========================================
✅ Success: 25
❌ Errors: 0
==========================================
```

**If duplicate**: Tool skips it (safe to re-run).

**If error**: Check error message, fix CSV, re-run.

---

### Phase 4: Verify URLs

**Time Estimate**: 1-2 minutes (depends on number of images)

```bash
python tools/verify_diagram_urls.py
```

**What it checks**:
- ✅ URL is accessible (HTTP 200)
- ✅ Content-Type is image/*
- ✅ Image size (<10MB)
- ✅ Response time (<5s, warns if slow)

**Output**:
```
==========================================
SYSTEM DIAGRAM URL VERIFICATION
==========================================

📡 Connecting to Supabase...
📥 Fetching diagrams...
✅ Found 25 diagrams

🔍 Verifying URLs...

[1/25] catalytic converter...
  ✅ OK - 2.34MB, 0.45s
[2/25] oxygen sensor...
  ✅ OK - 1.89MB, 0.32s
[3/25] EGR valve...
  ❌ Failed: Timeout (>5s)

==========================================
SUMMARY
==========================================
✅ Accessible images: 24/25
❌ Failed/timeout: 1
⚠️  Large files (>5MB): 0
⚠️  Slow responses (>2s): 0

❌ FAILED URLS (1):

  System: EGR valve
  URL: https://example.com/slow-host/egr.jpg
  Error: Timeout (>5s)

==========================================
⚠️  1 issue(s) need fixing
==========================================
```

**If warnings/errors**:
- **Large files (>5MB)**: Consider optimizing (compress image)
- **Slow responses (>2s)**: May timeout in production (10s limit)
- **Failed URLs**: Fix URL in database or re-source image

---

### Phase 5: Test Matching Logic

**Time Estimate**: 5 minutes

Test with real DTC codes to verify fuzzy matching works:

```bash
# Test specific DTC code
python tools/test_diagram_lookup.py P0420

# Test system name directly
python tools/test_diagram_lookup.py "catalytic converter"

# List all diagrams
python tools/test_diagram_lookup.py --list
```

**Output Example** (P0420):
```
==========================================
TEST: DTC Code P0420
==========================================

1. Looking up DTC: P0420
   ✅ Found: Catalyst System Efficiency Below Threshold
   📋 System: Emissions

2. Looking up diagram for system: 'Emissions'
   ✅ Found diagram!
   📋 Matched system: catalytic converter
   🔗 Image URL: https://upload.wikimedia.org/...
   📄 Source: Wikimedia Commons
   ⚖️  License: CC BY-SA 4.0
   💬 Caption: Catalytic converter cutaway
   📷 Attribution: Diagram by John Doe, via Wikimedia Commons

3. What user would see:
   ──────────────────────────────────────────────────────────────────
   [IMAGE MESSAGE]
   📷 Catalytic converter cutaway
   🔗 https://upload.wikimedia.org/...
   ──────────────────────────────────────────────────────────────────
   [TEXT MESSAGE - sent 1-2 seconds later]
   🔧 P0420: Catalyst System Efficiency Below Threshold
   ...
   
   📷 Diagram: Diagram by John Doe, via Wikimedia Commons
   ──────────────────────────────────────────────────────────────────

✅ Complete flow verified!
```

**If "No diagram found"**:
1. Check system name in DTC matches your CSV
2. Check `SYSTEM_SYNONYMS` in `system_diagram_repository.py` (add synonym if needed)
3. Run fuzzy matching test: `python test_fuzzy_matching.py`

---

### Phase 6: Configure Baileys (Optional)

If you want to test actual image sending:

**Add to `.env`**:
```bash
BAILEYS_OUTBOUND_URL=http://localhost:3000/send
```

**If not configured**: Image sending is skipped gracefully (text diagnosis still works).

---

### Phase 7: Production Test

**Send real DTC via WhatsApp**:

1. Start your backend: `uvicorn app.main:app --reload`
2. Start Baileys (if testing image sending)
3. Send WhatsApp message: `P0420`
4. Expect:
   - **Image message** (if diagram exists and Baileys configured)
   - **Text diagnosis** (1-2 seconds later)

**Check logs**:
```bash
tail -f logs/app.log | grep system_diagram
```

**Log messages**:
- `system_diagram_found_for_diagnosis` - Diagram matched ✅
- `sending_system_diagram` - Attempting to send
- `system_diagram_sent` - Sent successfully ✅
- `system_diagram_send_failed_continuing` - Failed but continuing ⚠️

---

## Troubleshooting

### Issue: "CSV validation error"

**Solution**: Check CSV format matches template exactly:
- 6 columns: `system,image_url,source,license,caption,attribution_text`
- No extra commas
- Quoted fields if they contain commas

### Issue: "image_url must be HTTPS"

**Solution**: Change `http://` to `https://` in URL.

**Note**: Wikimedia URLs are always HTTPS.

### Issue: "caption too long"

**Solution**: Shorten caption to 60 chars or less.

**Example**:
- ❌ "This is a detailed diagram of a catalytic converter showing internals" (72 chars)
- ✅ "Catalytic converter internals" (31 chars)

### Issue: "URL verification failed: Timeout"

**Possible causes**:
- Slow image host (try different image)
- Network issue (temporary, try again)
- Image host blocking automated requests (try different image)

**Solution**: Find alternative image or use your own CDN.

### Issue: "No diagram found for system"

**Possible causes**:
1. System name in DTC doesn't match any diagram
2. Fuzzy matching not finding synonym

**Solution**:
```bash
# Test what system name the DTC has
python tools/test_diagram_lookup.py P0420

# Check synonyms
# Edit: app/repositories/system_diagram_repository.py
# Add synonym to SYSTEM_SYNONYMS constant
```

### Issue: "Image not appearing in WhatsApp"

**Check**:
1. `BAILEYS_OUTBOUND_URL` configured in `.env`?
2. Baileys running?
3. Image URL accessible?
4. Check logs: `grep system_diagram logs/app.log`

**Note**: If image fails, text diagnosis still sends (graceful degradation).

---

## Quick Commands Reference

```bash
# Validate CSV (dry run)
python tools/import_diagrams_from_csv.py system_diagrams.csv --dry-run

# Import to database
python tools/import_diagrams_from_csv.py system_diagrams.csv

# Verify all URLs
python tools/verify_diagram_urls.py

# Test specific DTC
python tools/test_diagram_lookup.py P0420

# Test system name
python tools/test_diagram_lookup.py "catalytic converter"

# List all diagrams
python tools/test_diagram_lookup.py --list

# Check logs
tail -f logs/app.log | grep system_diagram
```

---

## File Locations

```
project_root/
├── system_diagrams_template.csv          # Template (copy to start)
├── system_diagrams.csv                   # Your filled data (gitignored)
├── migrations/
│   └── add_system_diagrams_table.sql     # Database schema
├── tools/
│   ├── import_diagrams_from_csv.py       # CSV importer
│   ├── verify_diagram_urls.py            # URL checker
│   └── test_diagram_lookup.py            # Matching tester
├── app/
│   ├── models/system_diagram.py          # Data model
│   ├── repositories/
│   │   └── system_diagram_repository.py  # Lookup logic (SYSTEM_SYNONYMS here)
│   └── services/
│       └── image_sender.py               # WhatsApp image sending
└── docs/
    ├── DIAGRAM_SOURCING_GUIDE.md         # Detailed sourcing guide
    ├── SYSTEM_DIAGRAMS_IMPLEMENTATION.md # Full implementation docs
    └── DIAGRAM_POPULATION_WORKFLOW.md    # This file
```

---

## Maintenance

### Adding More Diagrams Later

```bash
# Add new rows to CSV
# Then re-import (skips existing)
python tools/import_diagrams_from_csv.py system_diagrams.csv

# Verify new URLs
python tools/verify_diagram_urls.py
```

### Adding Synonyms

Edit `app/repositories/system_diagram_repository.py` lines 26-77:

```python
SYSTEM_SYNONYMS = {
    # Add your new synonym here
    "cat": ["catalytic converter"],
    "lambda sensor": ["oxygen sensor"],
    # etc.
}
```

Test: `python tools/test_diagram_lookup.py "cat"` (should find catalytic converter)

### Updating an Image

```sql
UPDATE system_diagrams
SET image_url = 'https://new-url.com/image.jpg'
WHERE system = 'catalytic converter';
```

Or delete and re-import from CSV.

---

## Success Criteria

✅ **Phase 1**: 20-30 systems sourced with valid licenses  
✅ **Phase 2**: CSV validates without errors  
✅ **Phase 3**: All diagrams imported to database  
✅ **Phase 4**: All URLs verified accessible  
✅ **Phase 5**: Test DTCs find correct diagrams  
✅ **Phase 6**: Baileys configured (optional)  
✅ **Phase 7**: Real WhatsApp test shows image + text

---

## Time Estimate

| Phase | Time | Who |
|-------|------|-----|
| 1. Source images | 2-4 hours | You (manual) |
| 2. Validate CSV | 2 minutes | Tool (automated) |
| 3. Import | 1 minute | Tool (automated) |
| 4. Verify URLs | 1-2 minutes | Tool (automated) |
| 5. Test matching | 5 minutes | Tool (automated) |
| 6. Configure Baileys | 2 minutes | You (config) |
| 7. Production test | 5 minutes | You (manual) |
| **Total** | **3-5 hours** | |

**Most time** is Phase 1 (sourcing images from Wikimedia Commons). Everything else is quick.

---

## You're Ready! 🎉

All tools are built and tested. Just follow this workflow and you'll have educational diagrams integrated into your WhatsApp bot.

**Questions? Check**:
- `DIAGRAM_SOURCING_GUIDE.md` - Detailed Wikimedia Commons process
- `SYSTEM_DIAGRAMS_IMPLEMENTATION.md` - Technical implementation details
- Tool help: `python tools/<tool_name>.py --help`
