#!/bin/bash
echo "Starting Vehicle Diagnosis Assistant Backend..."
echo ""

cd "$(dirname "$0")"

# Activate virtual environment
source venv/Scripts/activate

# Start FastAPI server
echo "Starting FastAPI on http://localhost:8001..."
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
