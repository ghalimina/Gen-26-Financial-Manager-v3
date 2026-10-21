@echo off
setlocal EnableExtensions
chcp 65001 >nul 2>&1
title GEN-26 QUANTUM TERMINAL (v4.6.2) - LIVE THNDR ^& EGX ENGINE
color 0B

cd /d "%~dp0"
set "PYTHONPATH=%~dp0"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
set "FLASK_APP=dashboard/app.py"

echo ======================================================================
echo   GEN-26 QUANTUM TERMINAL (v4.6.2) - LIVE THNDR ^& EGX ENGINE
echo   Workspace : %~dp0
echo   URL       : http://127.0.0.1:5000
echo ======================================================================
echo.

echo [1/3] Safely cleaning up any old server process on port 5000...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-NetTCPConnection -LocalPort 5000 -State Listen -ErrorAction SilentlyContinue | ForEach-Object { if ($_.OwningProcess -gt 4) { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue } }" >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano -p tcp ^| findstr /c:":5000 " ^| findstr /i "LISTENING"') do (
    if not "%%a"=="0" if not "%%a"=="4" (
        echo       Stopping old PID %%a on port 5000...
        taskkill /F /PID %%a >nul 2>&1
    )
)

set "PY_EXE=C:\Python312\python.exe"
if not exist "%PY_EXE%" (
    set "PY_EXE=python"
)
echo [2/3] Using Python Interpreter: %PY_EXE%
echo [3/3] Starting GEN-26 Live Server ^& Opening Browser (http://127.0.0.1:5000)...
echo       Keep this window OPEN to view live [API LIVE] requests in real time.
echo ======================================================================
echo.

"%PY_EXE%" "%~dp0dashboard\app.py"

echo.
echo ======================================================================
echo [NOTICE] Server process ended (Exit Code: %ERRORLEVEL%).
echo Press any key to close this window...
pause >nul
