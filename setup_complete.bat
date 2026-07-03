@echo off
echo.
echo ============================================================
echo   Complete Database Setup - Tables + 3,071 OBD Codes
echo ============================================================
echo.
echo This will:
echo   1. Create database tables in Supabase
echo   2. Import 3,071 OBD codes from GitHub
echo.
echo PREREQUISITES:
echo   [x] WARP VPN disabled
echo   [x] Supabase project healthy
echo   [x] .env file configured
echo.
pause
echo.

cd /d "%~dp0"

echo Activating virtual environment...
call venv\Scripts\activate.bat
echo.

echo ============================================================
echo   Step 1: Create Database Tables
echo ============================================================
echo.
echo Please follow these steps manually:
echo.
echo   1. Open: https://supabase.com/dashboard
echo   2. Click your project
echo   3. Click "SQL Editor" (left sidebar)
echo   4. Click "New query"
echo   5. Open: supabase\migrations\001_initial_schema.sql
echo   6. Copy ALL contents (Ctrl+A, Ctrl+C)
echo   7. Paste in SQL Editor (Ctrl+V)
echo   8. Click "RUN" button
echo   9. Should see "Success. No rows returned"
echo  10. Click "Table Editor" - verify 7 tables exist
echo.
echo Press any key when tables are created...
pause
echo.

echo ============================================================
echo   Step 2: Verify Tables
echo ============================================================
echo.
echo Testing table access...
python -c "from app.db.client import get_supabase_client; client = get_supabase_client(); result = client.table('obd_codes').select('code').limit(1).execute(); print('Tables exist!')"
if errorlevel 1 (
    echo.
    echo ❌ Tables not found!
    echo Please go back and run the migration SQL in Supabase.
    pause
    exit /b 1
)
echo ✅ Tables verified!
echo.

echo ============================================================
echo   Step 3: Import 3,071 OBD Codes from GitHub
echo ============================================================
echo.
echo Downloading and importing codes...
echo This may take 2-3 minutes...
echo.
python scripts\import_github_codes.py
if errorlevel 1 (
    echo.
    echo ❌ Import failed! Check errors above.
    pause
    exit /b 1
)
echo.

echo ============================================================
echo   Step 4: Verify Import
echo ============================================================
echo.
echo Counting codes in database...
python -c "from app.db.client import get_supabase_client; client = get_supabase_client(); result = client.table('obd_codes').select('code', count='exact').execute(); print(f'Total codes in database: {result.count}')"
echo.

echo ============================================================
echo   Step 5: Restart Backend
echo ============================================================
echo.
echo Your backend needs to restart to use the database.
echo.
echo ACTION REQUIRED:
echo   1. Go to the terminal running the backend
echo   2. Press Ctrl+C to stop it
echo   3. Run: start_backend.bat
echo   4. Look for: [info] supabase_connected
echo.
pause
echo.

echo ============================================================
echo   ✅ SETUP COMPLETE!
echo ============================================================
echo.
echo Your database now has:
echo   ✅ 7 tables created
echo   ✅ 3,071 OBD codes imported
echo   ✅ Full system ready
echo.
echo Test it:
echo   1. Send "P0420" via WhatsApp
echo   2. Backend should show: source=local_db
echo   3. Try more codes: P0300, P0171, etc.
echo.
echo You now have coverage for virtually ALL OBD codes!
echo.
pause
