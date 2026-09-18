@echo off
title GEN-26 Safe Paper Trading Session Runner
cd /d "%~dp0"

echo ======================================================================
echo 🏛️ GEN-26 FINANCIAL MANAGER v3.0 — SAFE PAPER SESSION RUNNER
echo    WARNING: LIVE TRADING IS COMPLETELY BLOCKED.
echo    This script runs ONE isolated simulated paper trading session only.
echo ======================================================================
echo.

set /p confirm="Run ONE SAFE PAPER TRADING session? (Y/N): "
if /i "%confirm%" neq "Y" (
    echo [ABORTED] Session cancelled by user.
    pause
    exit /b 0
)

echo.
echo [1/2] Executing Paper Trading Orchestrator...
python -m core.paper_trading_orchestrator

echo.
echo [2/2] Paper trading session execution finished.
pause
