@echo off
title GEN-26 Financial Manager v3.0 - Control Center
cd /d "%~dp0"

echo ======================================================================
echo  GEN-26 FINANCIAL MANAGER v3.0 - PAPER CONTROL CENTER LAUNCHER
echo    Mode: READ-ONLY MONITORING ONLY
echo    Live Trading: STRICTLY BLOCKED
echo ======================================================================
echo.

REM -----------------------------------------------------------------------
REM  SMART PYTHON RESOLVER
REM  Priority: C:\Python312 -> C:\Python315 -> system PATH
REM -----------------------------------------------------------------------
set PYTHON_EXE=

if exist "C:\Python312\python.exe" (
    echo [INFO] Using Python: C:\Python312\python.exe
    set PYTHON_EXE=C:\Python312\python.exe
) else if exist "C:\Python315\python.exe" (
    echo [INFO] Using Python: C:\Python315\python.exe
    set PYTHON_EXE=C:\Python315\python.exe
) else (
    where python >nul 2>nul
    if %errorlevel% neq 0 (
        echo [ERROR] Python was not found. Install Python and try again.
        pause
        exit /b 1
    )
    echo [INFO] Using Python from system PATH
    set PYTHON_EXE=python
)

REM -----------------------------------------------------------------------
REM  VERIFY FLASK IS AVAILABLE
REM -----------------------------------------------------------------------
%PYTHON_EXE% -c "import flask" >nul 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] Flask not found on %PYTHON_EXE%. Installing now...
    %PYTHON_EXE% -m pip install flask pandas numpy scipy beautifulsoup4 requests yfinance plotly apscheduler scikit-learn xgboost lxml pytz --quiet
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install Flask. Check internet or pip configuration.
        pause
        exit /b 1
    )
    echo [OK] Flask installed successfully.
)

echo [1/2] Starting local read-only monitoring dashboard on http://127.0.0.1:5000 ...
start /b %PYTHON_EXE% dashboard\app.py

timeout /t 4 /nobreak >nul

echo [2/2] Opening default browser...
start http://127.0.0.1:5000

echo.
echo [OK] Dashboard is running at http://127.0.0.1:5000 (Auto-refresh every 15s)
echo Close this window to keep the server running, or press Ctrl+C to stop.
echo ======================================================================
cmd /k
