@echo off
title ReLoop AI Launcher
echo ========================================================
echo                 Starting ReLoop AI
echo ========================================================
echo.
echo [1/2] Starting FastAPI Backend on http://127.0.0.1:8000 ...
start "ReLoop AI - Backend" cmd /k "cd /d "%~dp0backend" && .venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

echo [2/2] Starting Next.js Frontend on http://localhost:3000 ...
start "ReLoop AI - Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo Both services are launching in separate terminals:
echo - Frontend: http://localhost:3000
echo - Backend:  http://127.0.0.1:8000 (API Docs: http://127.0.0.1:8000/docs)
echo ========================================================

