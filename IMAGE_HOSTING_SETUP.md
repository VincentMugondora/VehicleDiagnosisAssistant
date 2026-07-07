# Image Hosting Setup

## Overview
Local static image hosting for automotive component diagrams, replacing unreliable Wikimedia Commons URLs.

## Implementation

### 1. Static File Serving
- **Location:** `app/static/images/`
- **Endpoint:** `http://localhost:8000/static/images/`
- **Format:** SVG (scalable, lightweight, text-based)

### 2. Generated Images
10 placeholder SVG images for automotive components:
1. `catalytic-converter.svg` - Catalytic Converter
2. `oxygen-sensor.svg` - Oxygen Sensor  
3. `maf-sensor.svg` - MAF Sensor
4. `throttle-body.svg` - Throttle Body
5. `evap-system.svg` - EVAP System
6. `fuel-injector.svg` - Fuel Injector
7. `egr-valve.svg` - EGR Valve
8. `ignition-coil.svg` - Ignition Coil
9. `camshaft-sensor.svg` - Camshaft Sensor
10. `crankshaft-sensor.svg` - Crankshaft Sensor

### 3. Database Updates
System diagrams table updated to use local URLs:
```sql
UPDATE system_diagrams 
SET image_url = 'http://localhost:8000/static/images/{component}.svg',
    source = 'Local',
    license = 'Placeholder'
WHERE system IN (...);
```

## Why Local Hosting?

### Problems with Wikimedia Commons
1. **403 Forbidden Errors** - All tested URLs returned 403
2. **Non-Existent Files** - Image filenames in populate script don't actually exist
3. **Dependency Risk** - External service can change/remove images
4. **Rate Limiting** - Bot protection blocks automated access

### Benefits of Local Hosting
- ✅ **100% Availability** - No external dependencies
- ✅ **Consistent Branding** - Uniform design across all components
- ✅ **Fast Loading** - Served directly from FastAPI
- ✅ **Easy Updates** - Replace files without database changes
- ✅ **Offline Capable** - Works in development without internet

## Architecture

```
FastAPI App (app/main.py)
│
├── Static Files Mount
│   └── /static → app/static/
│       └── /images → app/static/images/
│           ├── catalytic-converter.svg
│           ├── oxygen-sensor.svg
│           └── ... (8 more)
│
└── Baileys Image Sender
    └── Fetches from local URL
        └── Sends via WhatsApp
```

## Usage

### Access Images
```bash
# Browser/curl
curl http://localhost:8000/static/images/ignition-coil.svg

# From Baileys
POST http://localhost:8000/send-image
{
  "to": "user_jid",
  "imageUrl": "http://localhost:8000/static/images/ignition-coil.svg"
}
```

### Add New Images
1. Place SVG/PNG/JPG in `app/static/images/`
2. Update database if needed:
```sql
UPDATE system_diagrams 
SET image_url = 'http://localhost:8000/static/images/new-component.svg'
WHERE system = 'new component';
```

## SVG Placeholder Design

### Specifications
- **Size:** 600x400px
- **Format:** SVG (scalable vector graphics)
- **Colors:** Neutral grays with gradient background
- **Text:** Component name + "Diagram Placeholder"
- **Style:** Clean, professional, consistent

### Example Structure
```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 400">
  <!-- Gradient background -->
  <!-- Component icon/shape -->
  <!-- Title text -->
  <!-- Subtitle -->
</svg>
```

## Production Considerations

### For Deployment
1. **CDN Hosting** - Upload to CloudFlare/AWS S3 for production
2. **Image Optimization** - Convert to WebP for smaller size
3. **Caching Headers** - Set long cache times for static images
4. **HTTPS** - Update URLs to use HTTPS in production

### Example Production URLs
```
# Development
http://localhost:8000/static/images/ignition-coil.svg

# Production (CDN)
https://cdn.yourapp.com/images/ignition-coil.webp

# Production (self-hosted)
https://api.yourapp.com/static/images/ignition-coil.svg
```

## Future Improvements

### Short-Term
- [ ] Replace placeholders with actual component photos
- [ ] Add image alt text for accessibility
- [ ] Implement image caching in Baileys

### Long-Term
- [ ] Upload real automotive component photos
- [ ] Add multilingual image descriptions
- [ ] Generate images dynamically with component data
- [ ] Implement lazy loading for mobile

## Testing

### Manual Test
```bash
# 1. Start backend
python -m uvicorn app.main:app --reload

# 2. Test static file serving
curl http://localhost:8000/static/images/ignition-coil.svg

# 3. Send via WhatsApp (requires Baileys running)
# Send message: "P0301" (misfire code)
# Should receive diagram image
```

### Automated Test
```python
import httpx

async def test_images():
    async with httpx.AsyncClient() as client:
        r = await client.get("http://localhost:8000/static/images/ignition-coil.svg")
        assert r.status_code == 200
        assert "svg" in r.headers["content-type"]
```

## Troubleshooting

### Images Not Loading
1. Check `app/static/images/` directory exists
2. Verify FastAPI static mount in `app/main.py`
3. Check file permissions (readable by uvicorn process)
4. View browser console for 404 errors

### Baileys Can't Fetch Images
1. Ensure backend server is running
2. Check Baileys can reach `http://localhost:8000`
3. Verify image URLs in database use correct host/port
4. Check Baileys logs for fetch errors

### Database URLs Wrong
```python
# Run this script to reset to local URLs
python update_to_local_images.py  # (if script still exists)
```

## Related Files
- `app/main.py` - FastAPI static mount configuration
- `app/static/images/` - Image storage directory
- `app/services/image_sender.py` - WhatsApp image sending logic
- `scripts/populate_all_tables.py` - Initial database population

## Change Log

| Date | Change | Impact |
|------|--------|--------|
| 2026-07-07 | Created local hosting infrastructure | Images now load reliably |
| 2026-07-07 | Generated 10 SVG placeholders | All components have visuals |
| 2026-07-07 | Updated database URLs | WhatsApp bot can send images |

---

**Status:** ✅ Implemented and tested
**Last Updated:** 2026-07-07
