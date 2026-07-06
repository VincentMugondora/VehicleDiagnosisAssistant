# Image Caching Status

## Problem Identified

**Performance Issue**: Images take 18-53 seconds to send because WhatsApp/Baileys downloads them fresh from Wikimedia on EVERY diagnostic request.

**Root Cause**: The Baileys server passes Wikimedia URLs directly to WhatsApp:
```javascript
image: { url: "https://upload.wikimedia.org/..." }  // ← Downloaded fresh every time
```

## Solution Implemented

### Supabase Storage Caching

Created `tools/cache_to_supabase_storage.py` to:
1. Download each diagram image from Wikimedia once
2. Upload to Supabase Storage bucket `system-diagrams`
3. Update database `image_url` to point to Supabase Storage URL
4. Result: Images served from Supabase CDN (fast, durable, no re-downloads)

### Code Changes

1. **tools/cache_to_supabase_storage.py** - New caching script
2. **app/api/routes/webhook.py:650** - Reduced timeout from 60s to 15s
3. **tools/__init__.py** - Made tools a Python package
4. Removed local file caching approach (cache-images.js, static endpoint)

## Current Blocker: Wikimedia Rate Limiting

Wikimedia is blocking our IP with 403 Forbidden after earlier bulk download attempts. This is a standard anti-scraping measure.

**All 24 images failed to download** due to 403 errors.

## Manual Workaround Required

**Option 1: Wait 24 Hours**

Wikimedia rate limits typically reset after 24 hours. Run tomorrow:
```bash
python tools/cache_to_supabase_storage.py
```

**Option 2: Manual Browser Download + Upload**

Since browser downloads won't be rate-limited:

1. Download each image URL manually via browser (see list below)
2. Upload to Supabase Storage via dashboard:
   - Go to: https://supabase.com/dashboard/project/yalpyodkymdkgkridtom/storage/buckets
   - Bucket: `system-diagrams`
   - Create folder: `diagrams/`
   - Upload each image with sanitized filename (see mapping below)
3. Update database URLs manually or re-run the script (it will skip already-cached images)

### Image URL → Filename Mapping

```
air-intake-manifold.png → https://upload.wikimedia.org/wikipedia/commons/7/7f/Manly_1919_Fig_133_Fordson_intake.png
alternator.jpg → https://upload.wikimedia.org/wikipedia/commons/7/7a/Alternator_%28cut-away%29_%2801%29.JPG
battery.jpeg → https://upload.wikimedia.org/wikipedia/commons/8/85/Car_battery_cross-section.jpeg
brake-pads.jpg → https://upload.wikimedia.org/wikipedia/commons/7/76/Hydraylic_disc_brake_diagram.jpg
camshaft-position-sensor.png → https://upload.wikimedia.org/wikipedia/commons/7/7c/Crankshaft_sensor.png
catalytic-converter.jpg → https://upload.wikimedia.org/wikipedia/commons/8/85/Catalytic_Converter_Interior.jpg
crankshaft-position-sensor.png → https://upload.wikimedia.org/wikipedia/commons/7/7c/Crankshaft_sensor.png
egr-valve.jpg → https://upload.wikimedia.org/wikipedia/commons/d/d9/EGR_Cooler.JPG
evap-system.png → https://upload.wikimedia.org/wikipedia/commons/9/98/Principe_de_fonctionnement_d%27un_canister_d%27automobile.png
fuel-injector.png → https://upload.wikimedia.org/wikipedia/commons/8/8e/Fuelinjector.png
fuel-pump.jpg → https://upload.wikimedia.org/wikipedia/commons/c/cb/Automobile_Fuel_tank_cutaway.JPG
ignition-coil.jpg → https://upload.wikimedia.org/wikipedia/commons/8/8f/Induction_coil_cutaway.jpg
knock-sensor.jpg → https://upload.wikimedia.org/wikipedia/commons/3/33/Piezoelectric_sensor.jpg
map-sensor.jpg → https://upload.wikimedia.org/wikipedia/commons/0/06/K-car_MAP_and_logic_module_location_%284217323585%29.jpg
mass-air-flow-sensor.jpg → https://upload.wikimedia.org/wikipedia/commons/d/df/Detail_Hei%C3%9Ffilm-Luftmassenmesser.jpg
oxygen-sensor.svg → https://upload.wikimedia.org/wikipedia/commons/b/bd/ZirconiaSensor.svg
pcv-valve.jpg → https://upload.wikimedia.org/wikipedia/commons/d/d9/Carterventilatie.JPG
radiator.jpg → https://upload.wikimedia.org/wikipedia/commons/4/4c/Thermo-syphon_cooling_circulation_%28Manual_of_Driving_and_Maintenance%29.jpg
spark-plug.png → https://upload.wikimedia.org/wikipedia/commons/7/7c/Spark_Plug_%28PSF%29.png
thermostat.jpg → https://upload.wikimedia.org/wikipedia/commons/0/01/Double_valve_automotive_thermostat.jpg
throttle-body.png → https://upload.wikimedia.org/wikipedia/commons/3/3d/USPatent6646395.png
timing-belt.jpg → https://upload.wikimedia.org/wikipedia/commons/e/e1/Timing_belt_RB30E.jpg
transmission.jpg → https://upload.wikimedia.org/wikipedia/commons/5/5d/Porsche-gearbox-cutaway.jpg
wheel-speed-sensor.jpg → https://upload.wikimedia.org/wikipedia/commons/3/39/Anti-lock_braking_system_diagram.jpg
```

After manual upload, update database:
```sql
UPDATE system_diagrams
SET image_url = 'https://yalpyodkymdkgkridtom.supabase.co/storage/v1/object/public/system-diagrams/diagrams/<filename>',
    source = source || ' (cached in Supabase Storage)'
WHERE system = '<system-name>';
```

## Expected Performance After Caching

- **Before**: 18-53 seconds per image (Wikimedia download every time)
- **After**: <2 seconds per image (Supabase Storage CDN)
- **Sequencing**: Image sends BEFORE text diagnosis (already correct in code)

## Verification After Caching

```bash
# Check Supabase Storage bucket has 24 images
# Visit: https://supabase.com/dashboard/project/yalpyodkymdkgkridtom/storage/buckets/system-diagrams

# Verify database URLs point to Supabase Storage
python -c "
import sys; sys.path.insert(0, '.')
from app.db.client import get_supabase_client
client = get_supabase_client()
result = client.table('system_diagrams').select('system, image_url').execute()
for row in result.data:
    if 'supabase' in row['image_url']:
        print(f'✅ {row[\"system\"]}: CACHED')
    else:
        print(f'❌ {row[\"system\"]}: Still Wikimedia')
"

# Test image delivery speed
# Send a diagnostic for "P0420" (catalytic converter)
# Time from request to image arrival should be <5s total
```

## Database Review Completed

All 24 diagram rows were reviewed and approved:
- air intake manifold
- alternator
- battery
- brake pads
- camshaft position sensor
- catalytic converter (originally approved)
- crankshaft position sensor
- egr valve
- evap system
- fuel injector
- fuel pump
- ignition coil
- knock sensor
- map sensor
- mass air flow sensor
- oxygen sensor
- pcv valve
- radiator
- spark plug
- thermostat
- throttle body
- timing belt
- transmission
- wheel speed sensor

All use Wikimedia Commons images with proper licensing (CC BY-SA, CC0, Public Domain).
