@echo off
title EGX Quant Master Engine - Full Execution
cls
echo ==================================================================
echo 🚀 EGX QUANT ENGINE - FULL WORKFLOW EXECUTION
echo ==================================================================
echo.

cd /d "%~dp0"

echo [1/3] Running Daily Paper Trade Logger...
python "daily_paper_trade_logger.py"
echo.

echo [2/3] Displaying Performance Dashboard...
python "show_my_results.py"
echo.

echo [3/3] Launching Live Streamlit Interactive Dashboard...
streamlit run "app.py"
pause
