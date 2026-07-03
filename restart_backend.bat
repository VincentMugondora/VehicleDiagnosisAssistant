@echo off
echo.
echo ============================================================
echo   Restarting Backend with Database Connection
echo ============================================================
echo.
echo Make sure you stopped the old backend first (Ctrl+C)
echo.
pause
echo.

cd /d "%~dp0"
call venv\Scripts\activate.bat

echo Starting backend...
echo Look for: [info] supabase_connected
echo.

uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
