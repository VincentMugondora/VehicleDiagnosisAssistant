@echo off
REM Development server startup script (Windows)
REM Workaround for Windows App Control blocking uvicorn.exe

echo Starting Vehicle Diagnosis Assistant (Development Mode)
echo ========================================================
echo.
echo Server will be available at: http://127.0.0.1:8000
echo API docs: http://127.0.0.1:8000/docs
echo.
echo Press CTRL+C to stop the server
echo.

REM Run uvicorn as Python module instead of exe
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
