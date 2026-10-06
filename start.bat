@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

echo ==================================================
echo Starting Signal Clone Fullstack Platform...
echo ==================================================

:: Start Backend
echo [1/2] Starting Backend (FastAPI on port 8000)...
start "Signal Backend (FastAPI)" cmd /k "cd /d "%~dp0backend" && .venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

:: Start Frontend
echo [2/2] Starting Frontend (Vite on port 8443)...
start "Signal Frontend (Vite)" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo ==================================================
echo Both services are launching in separate windows!
echo - Frontend: http://localhost:8443
echo - Backend API: http://localhost:8000
echo - API Docs: http://localhost:8000/docs
echo ==================================================
