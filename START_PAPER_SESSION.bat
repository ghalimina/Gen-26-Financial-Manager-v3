@echo off
title GEN-26 Safe Paper Trading Session Runner
cd /d "%~dp0"

echo ======================================================================
echo  GEN-26 FINANCIAL MANAGER v3.0 - SAFE PAPER SESSION RUNNER
echo    WARNING: LIVE TRADING IS COMPLETELY BLOCKED.
echo    This script runs ONE isolated simulated paper trading session only.
echo ======================================================================
echo.

REM -----------------------------------------------------------------------
REM  SMART PYTHON RESOLVER
REM -----------------------------------------------------------------------
set PYTHON_EXE=

if exist "C:\Python312\python.exe" (
    set PYTHON_EXE=C:\Python312\python.exe
) else if exist "C:\Python315\python.exe" (
    set PYTHON_EXE=C:\Python315\python.exe
) else (
    where python >nul 2>nul
    if %errorlevel% neq 0 (
        echo [ERROR] Python was not found. Install Python and try again.
        pause
        exit /b 1
    )
    set PYTHON_EXE=python
)
echo [INFO] Using Python: %PYTHON_EXE%

set /p confirm="Run ONE SAFE PAPER TRADING session? (Y/N): "
if /i "%confirm%" neq "Y" (
    echo [ABORTED] Session cancelled by user.
    pause
    exit /b 0
)

echo.
echo [1/2] Executing Paper Trading Orchestrator...
%PYTHON_EXE% -m core.paper_trading_orchestrator

echo.
echo [2/2] Paper trading session execution finished.
pause
