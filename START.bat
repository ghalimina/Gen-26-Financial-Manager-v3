@echo off
title GEN-26 QUANTUM TERMINAL (v4.5) — LIVE THNDR & EGX ENGINE
cd /d "%~dp0"

echo ======================================================================
echo  GEN-26 QUANTUM TERMINAL (v4.5) — LIVE THNDR & EGX ENGINE
echo    Mode: HIGH-SPEED QUANTUM MONITORING & INTRADAY EXECUTION
echo    Port: 5000 (Auto-Killing Any Zombie Port 5000 Processes)
echo ======================================================================
echo.

REM -----------------------------------------------------------------------
REM  1. AUTO-KILL ZOMBIE PYTHON PROCESSES ON PORT 5000
REM -----------------------------------------------------------------------
echo [0/3] Purging any zombie processes on port 5000...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":5000" ^| find "LISTENING"') do (
    echo [CLEANUP] Terminating zombie process on port 5000 (PID: %%a)...
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 1 /nobreak >nul

REM -----------------------------------------------------------------------
REM  2. SMART PYTHON RESOLVER (Priority: C:\Python312 -> C:\Python315 -> PATH)
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
        echo [ERROR] Python was not found. Please install Python and try again.
        pause
        exit /b 1
    )
    echo [INFO] Using Python from system PATH
    set PYTHON_EXE=python
)

REM -----------------------------------------------------------------------
REM  3. VERIFY REQUIRED PACKAGES
REM -----------------------------------------------------------------------
%PYTHON_EXE% -c "import flask" >nul 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] Flask not found on %PYTHON_EXE%. Installing required packages...
    %PYTHON_EXE% -m pip install flask pandas numpy scipy beautifulsoup4 requests yfinance plotly apscheduler scikit-learn xgboost lxml pytz --quiet
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install Flask. Check internet connection.
        pause
        exit /b 1
    )
    echo [OK] Dependencies installed successfully.
)

REM -----------------------------------------------------------------------
REM  4. LAUNCH BROWSER IN BACKGROUND AFTER 2 SECONDS DELAY
REM -----------------------------------------------------------------------
echo [1/2] Opening default browser at http://127.0.0.1:5000 ...
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:5000"

REM -----------------------------------------------------------------------
REM  5. RUN FLASK SERVER IN FOREGROUND WITH LIVE TERMINAL API LOGGING
REM -----------------------------------------------------------------------
echo [2/2] Booting GEN-26 Quantum Terminal v4.5 Server in foreground...
echo ======================================================================
echo  LIVE TERMINAL ACTIVE — Streaming all [API LIVE] requests in real time
echo  Press Ctrl+C to gracefully stop the server.
echo ======================================================================
echo.

%PYTHON_EXE% dashboard\app.py

echo.
echo [SERVER STOPPED] Press any key to exit.
pause >nul
