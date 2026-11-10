# ReLoop AI PowerShell Launcher
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "                Starting ReLoop AI                      " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

$root = $PSScriptRoot

Write-Host "`n[1/2] Starting FastAPI Backend on http://127.0.0.1:8000 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\backend'; .venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

Write-Host "[2/2] Starting Next.js Frontend on http://localhost:3000 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\frontend'; npm run dev"

Write-Host "`nBoth services are running in separate windows!" -ForegroundColor Yellow
Write-Host " - Frontend UI: http://localhost:3000" -ForegroundColor White
Write-Host " - Backend API: http://127.0.0.1:8000 (Docs: http://127.0.0.1:8000/docs)" -ForegroundColor White
Write-Host "========================================================`n" -ForegroundColor Cyan

