# System Diagram Sourcing Guide

**Goal**: Populate `system_diagrams` table with 20-30 high-quality educational images

---

## Primary Source: Wikimedia Commons

### Step-by-Step Process

#### 1. Find Images

Go to **commons.wikimedia.org** and search:
- "catalytic converter diagram"
- "oxygen sensor cutaway"
- "EGR valve schematic"
- "mass air flow sensor"
- etc.

**Filter Tips**:
- Look for **technical diagrams** (not just photos)
- Prefer **labeled** or **cutaway** views (more educational)
- Check image quality (high resolution preferred)

#### 2. Check License (Critical!)

Click through to the **file page** for each image. Look for the license box:

**✅ GOOD LICENSES (Use These)**:
- **Public Domain** - No attribution needed (but still recommended)
- **CC0** (Creative Commons Zero) - Effectively public domain
- **CC BY** (Attribution) - Must credit author
- **CC BY-SA** (Attribution-ShareAlike) - Must credit + same license if modified

**❌ BAD LICENSES (Avoid These)**:
- **CC BY-NC** (Non-Commercial) - NOT allowed for paid product
- **CC BY-ND** (No Derivatives) - Can't modify/crop
- **All Rights Reserved** - Copyrighted, can't use

#### 3. Extract Metadata

From the Wikimedia file page, record:

| Field | Where to Find | Example |
|-------|--------------|---------|
| **system** | Your choice (matches DTC) | `catalytic converter` |
| **image_url** | Right-click image → "Copy image address" | `https://upload.wikimedia.org/wikipedia/commons/...` |
| **source** | Always | `Wikimedia Commons` |
| **license** | License section | `CC BY-SA 4.0` or `Public Domain` |
| **attribution_text** | Author + source | `Diagram by John Doe, via Wikimedia Commons` |
| **caption** | Write yourself (<60 chars!) | `How a catalytic converter works` |

**Caption Guidelines**:
- Keep under 60 characters (WhatsApp truncates longer)
- Make it descriptive but concise
- Examples:
  - ✅ "Catalytic converter internals" (36 chars)
  - ✅ "O2 sensor location and wiring" (30 chars)
  - ❌ "This diagram shows the internal structure of a catalytic converter and how it reduces emissions" (98 chars - TOO LONG)

---

## License Compliance Notes

### Public Domain / CC0
- **Legal requirement**: None
- **Best practice**: Still add `attribution_text: "Diagram via Wikimedia Commons"`
- **Why**: Good faith, avoids ambiguity, costs nothing

### CC BY / CC BY-SA
- **Legal requirement**: MUST credit author
- **Format**: `"Diagram by [Author Name], via Wikimedia Commons"`
- **ShareAlike note**: If you edit/relabel the image, the modified version must use same license
  - **Using as-is**: No problem
  - **Cropping/relabeling**: Be aware of requirement

### Non-Commercial (CC BY-NC)
- **DO NOT USE** - Your product has paid subscriptions
- Even if free tier exists, NC licenses prohibit use in commercial context

---

## Recommended Systems List (Priority Order)

Start with these ~25 systems (most common DTC codes):

### High Priority (Start Here)
1. ✅ **Catalytic converter** - P0420, P0430
2. ✅ **Oxygen sensor** - P0131, P0132, P0171, P0172
3. ✅ **EGR valve** - P0400, P0401, P0402
4. ✅ **EVAP system** - P0440, P0442, P0455
5. ✅ **Mass air flow sensor** - P0100, P0101, P0102
6. ✅ **Throttle body** - P0120, P0121, P0122
7. ✅ **Ignition coil** - P0300-P0308
8. ✅ **Spark plugs** - P0300-P0308

### Medium Priority
9. Fuel injector - P0200-P0208
10. Fuel pump - P0230, P0231
11. MAP sensor - P0105-P0109
12. Camshaft position sensor - P0340-P0349
13. Crankshaft position sensor - P0335-P0339
14. Knock sensor - P0325-P0334
15. Coolant temperature sensor - P0115-P0119
16. Thermostat - P0125, P0128

### Lower Priority (Nice to Have)
17. PCV valve
18. Radiator
19. Timing belt/chain
20. Alternator
21. Battery
22. Brake pads/rotors
23. Wheel speed sensor (ABS)
24. Transmission components
25. Air intake manifold

---

## Alternative Sources (If Commons Coverage Thin)

### OpenClipart.org
- All public domain (CC0)
- Good for simple schematics
- Less automotive-specific than Wikimedia

### Pixabay
- CC0 / Public Domain images
- Photo-heavy (less technical diagrams)
- Some automotive content

### Your Own Illustrations
- Draw simple schematics (PowerPoint, Inkscape, etc.)
- Take photos of clean engine bays
- Create labeled diagrams
- **License**: Mark as "Original Work" in database

---

## Workflow: Spreadsheet First, Then Import

### Phase 1: Build Spreadsheet

Use the provided template: `system_diagrams_template.csv`

**Columns**:
```csv
system,image_url,source,license,caption,attribution_text
```

**Fill it out** as you find images on Wikimedia Commons.

**Example Row**:
```csv
catalytic converter,https://upload.wikimedia.org/wikipedia/commons/a/b/c.jpg,Wikimedia Commons,CC BY-SA 4.0,How a catalytic converter works,"Diagram by John Doe, via Wikimedia Commons"
```

### Phase 2: Validate (Dry Run)

```bash
python tools/import_diagrams_from_csv.py system_diagrams.csv --dry-run
```

This will:
- ✅ Validate all required fields
- ✅ Check URLs are HTTPS
- ✅ Check captions are <60 chars
- ✅ Show preview of what will be imported
- ❌ **NOT** insert anything (dry run)

### Phase 3: Import to Database

```bash
python tools/import_diagrams_from_csv.py system_diagrams.csv
```

This will:
1. Validate all rows
2. Show preview
3. Ask for confirmation
4. Insert into `system_diagrams` table
5. Skip duplicates
6. Report success/errors

### Phase 4: Verify URLs

```bash
python tools/verify_diagram_urls.py
```

This will:
- ✅ Check each URL is accessible (HTTP 200)
- ✅ Verify content-type is image/*
- ✅ Check image size (<10MB recommended)
- ✅ Check response time (<5s, 10s timeout in prod)
- ⚠️ Warn about large/slow files
- ❌ Report broken URLs

---

## Image URL Best Practices

### ✅ DO:
- Use **HTTPS** URLs (WhatsApp requires it)
- Use **direct file URLs** (not wiki pages)
- Use **reliable hosts** (Wikimedia, your CDN, Supabase Storage)
- Check URLs work in incognito/private browser
- Keep images **under 5MB** (faster delivery)

### ❌ DON'T:
- Use HTTP URLs (WhatsApp blocks them)
- Use random internet URLs (can disappear)
- Use very large images (>10MB = slow delivery)
- Use URLs requiring authentication
- Use short-lived URLs (temporary CDN links)

### Wikimedia Direct File URL

**Wrong** (wiki page):
```
https://commons.wikimedia.org/wiki/File:Catalytic_converter.jpg
```

**Correct** (direct file):
```
https://upload.wikimedia.org/wikipedia/commons/a/b/c/Catalytic_converter.jpg
```

**How to get**: Right-click the image → "Copy image address"

---

## Example: Complete Entry

### Wikimedia Commons File Page Shows:
- **Title**: Catalytic converter diagram
- **Author**: John Doe
- **License**: Creative Commons Attribution-Share Alike 4.0 International
- **File URL**: https://upload.wikimedia.org/wikipedia/commons/abc123/Cat_converter.jpg

### Your CSV Entry:
```csv
catalytic converter,https://upload.wikimedia.org/wikipedia/commons/abc123/Cat_converter.jpg,Wikimedia Commons,CC BY-SA 4.0,Catalytic converter internals,"Diagram by John Doe, via Wikimedia Commons"
```

### Database Record:
```sql
INSERT INTO system_diagrams (system, image_url, source, license, caption, attribution_text)
VALUES (
    'catalytic converter',
    'https://upload.wikimedia.org/wikipedia/commons/abc123/Cat_converter.jpg',
    'Wikimedia Commons',
    'CC BY-SA 4.0',
    'Catalytic converter internals',
    'Diagram by John Doe, via Wikimedia Commons'
);
```

### What User Sees:
1. **Image message** with caption: "Catalytic converter internals"
2. **Text diagnosis** (2 seconds later) ending with: `📷 Diagram: Diagram by John Doe, via Wikimedia Commons`

---

## Quality Checklist

Before importing, verify each image:

- [ ] URL is HTTPS
- [ ] Image loads in browser
- [ ] License is compatible (CC BY, CC BY-SA, CC0, Public Domain)
- [ ] License is NOT non-commercial (CC BY-NC)
- [ ] Caption is under 60 characters
- [ ] Attribution text includes author (if required)
- [ ] System name matches DTC system field (check fuzzy matching)
- [ ] Image is educational (diagram/cutaway, not just a photo)
- [ ] Image is reasonable size (<5MB recommended)

---

## Quick Start Commands

```bash
# 1. Start with template
cp system_diagrams_template.csv system_diagrams.csv

# 2. Fill in the CSV (use Excel, Google Sheets, or text editor)

# 3. Validate (dry run)
python tools/import_diagrams_from_csv.py system_diagrams.csv --dry-run

# 4. Import to database
python tools/import_diagrams_from_csv.py system_diagrams.csv

# 5. Verify all URLs work
python tools/verify_diagram_urls.py

# 6. Test with a real DTC code
# Send "P0420" via WhatsApp → should receive image + text
```

---

## Troubleshooting

### "CSV validation error: Missing required field"
- Check CSV has all 6 columns: `system,image_url,source,license,caption,attribution_text`
- Use template as starting point

### "image_url must be HTTPS"
- WhatsApp requires HTTPS
- Wikimedia Commons URLs are always HTTPS
- Fix: Change `http://` to `https://`

### "caption too long"
- Max 60 characters
- Shorten it: "How a catalytic converter works" → "Catalytic converter internals"

### "URL verification failed"
- Run `python tools/verify_diagram_urls.py` to diagnose
- Check URL in browser
- May be temporary network issue or broken link

### "Image not sending in WhatsApp"
- Check `BAILEYS_OUTBOUND_URL` is configured in `.env`
- Check image URL is accessible
- Check Baileys is running
- Check logs: `grep system_diagram logs/app.log`

---

## Next Steps

1. ✅ Use this guide to source 20-30 images from Wikimedia Commons
2. ✅ Fill in `system_diagrams.csv`
3. ✅ Import with provided tool
4. ✅ Verify URLs
5. ✅ Test in WhatsApp

**Happy sourcing!** 🎉
