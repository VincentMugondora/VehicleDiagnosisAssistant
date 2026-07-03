@echo off
echo.
echo ============================================================
echo   Vehicle Diagnosis Assistant - Quick Database Setup
echo ============================================================
echo.
echo This script will help you set up Supabase with all tables
echo and 132+ OBD codes.
echo.
echo ============================================================
echo   STEP 1: Disable Cloudflare WARP (REQUIRED)
echo ============================================================
echo.
echo Your system is using Cloudflare WARP which blocks Supabase.
echo.
echo ACTION REQUIRED:
echo   1. Look for the WARP icon in your system tray (near clock)
echo   2. Click it and select "Disconnect" or toggle it OFF
echo   3. Come back here and press any key to continue
echo.
pause
echo.
echo Testing DNS resolution...
nslookup ojxijkrkadymllbigcme.supabase.co
echo.
echo If you see an IP address above, GREAT! Continue.
echo If you see "Non-existent domain", WARP is still on - disable it first!
echo.
pause
echo.
echo ============================================================
echo   STEP 2: Checking Supabase Connection
echo ============================================================
echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo.
echo Testing connection to Supabase...
python -c "from app.db.client import get_supabase_client; from app.core.config import settings; print(f'Supabase URL: {settings.supabase_url}'); client = get_supabase_client(); print('✅ Connected!' if client else '❌ Failed')"
echo.
if errorlevel 1 (
    echo ❌ Cannot connect to Supabase!
    echo.
    echo Please check:
    echo   1. WARP is disabled
    echo   2. .env file has correct SUPABASE_URL and SUPABASE_SERVICE_KEY
    echo.
    pause
    exit /b 1
)
echo.
echo ============================================================
echo   STEP 3: Create Tables in Supabase
echo ============================================================
echo.
echo ACTION REQUIRED - Follow these steps:
echo.
echo   1. Open: https://supabase.com/dashboard
echo   2. Login and select your project
echo   3. Click "SQL Editor" in left sidebar
echo   4. Click "New query"
echo   5. Open this file: supabase\migrations\001_initial_schema.sql
echo   6. Copy ALL the contents
echo   7. Paste into SQL Editor
echo   8. Click "Run" button (or press Ctrl+Enter)
echo   9. You should see "Success. No rows returned"
echo  10. Click "Table Editor" - you should see 7 tables
echo.
echo Press any key when done...
pause
echo.
echo ============================================================
echo   STEP 4: Import OBD Codes
echo ============================================================
echo.
echo Now importing 132+ OBD codes to your database...
echo This may take 1-2 minutes...
echo.
python scripts\import_obd_datasets.py
echo.
if errorlevel 1 (
    echo ❌ Import failed!
    echo Please check the error messages above.
    pause
    exit /b 1
)
echo.
echo ============================================================
echo   STEP 5: Verify Everything
echo ============================================================
echo.
echo Checking how many codes were imported...
python -c "from app.db.client import get_supabase_client; client = get_supabase_client(); result = client.table('obd_codes').select('code', count='exact').execute(); print(f'✅ Total codes in database: {result.count}')"
echo.
echo ============================================================
echo   STEP 6: Restart Backend
echo ============================================================
echo.
echo Your backend needs to be restarted to connect to Supabase.
echo.
echo   1. Go to the terminal running the backend
echo   2. Press Ctrl+C to stop it
echo   3. Run: uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
echo   4. Look for: [info] supabase_connected ✅
echo.
echo Or simply run: start_backend.bat
echo.
echo ============================================================
echo   ✅ SETUP COMPLETE!
echo ============================================================
echo.
echo Your database now has:
echo   ✅ 7 tables created
echo   ✅ 132+ OBD codes
echo   ✅ Ready for persistent storage
echo   ✅ Full analytics enabled
echo.
echo Test it by sending "P0420" via WhatsApp
echo Backend logs should show: source=local_db (not fallback!)
echo.
echo See SETUP_DATABASE.md for detailed instructions.
echo.
pause
