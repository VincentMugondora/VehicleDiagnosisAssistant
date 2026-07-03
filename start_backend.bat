@echo off
echo Starting Vehicle Diagnosis Assistant Backend...
echo.

cd /d "%~dp0"

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Start FastAPI server
echo Starting FastAPI on http://localhost:8001...
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

pause
