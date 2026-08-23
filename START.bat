@echo off
title GEN-26 Financial Manager v3.0 - Control Center
cd /d "%~dp0"

echo ======================================================================
echo 🏛️ GEN-26 FINANCIAL MANAGER v3.0 — PAPER CONTROL CENTER LAUNCHER
echo    Mode: READ-ONLY MONITORING ONLY
echo    Live Trading: STRICTLY BLOCKED
echo ======================================================================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python was not found in system PATH.
    pause
    exit /b 1
)

echo [1/2] Starting local read-only monitoring dashboard on http://127.0.0.1:5000 ...
start /b python dashboard\app.py

timeout /t 3 /nobreak >nul

echo [2/2] Opening default browser...
start http://127.0.0.1:5000

echo.
echo ✅ Dashboard is running at http://127.0.0.1:5000 (Auto-refresh every 15s)
echo Close this window to keep the server running, or press Ctrl+C to stop.
echo ======================================================================
cmd /k
