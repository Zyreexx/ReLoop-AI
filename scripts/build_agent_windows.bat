@echo off
REM ReLoop AI Diagnostics Agent - Windows Build Script
echo ================================================================================
echo Building ReLoop AI Diagnostics Agent for Windows (x64)
echo ================================================================================

cd /d "%~dp0\.."
if exist "backend\.venv\Scripts\python.exe" (
    backend\.venv\Scripts\python.exe scripts\package_agent.py
) else (
    python scripts\package_agent.py
)
if %ERRORLEVEL% equ 0 (
    echo [SUCCESS] Windows executable built at dist\reloop-agent.exe
) else (
    echo [ERROR] Packaging failed with exit code %ERRORLEVEL%
)
pause

