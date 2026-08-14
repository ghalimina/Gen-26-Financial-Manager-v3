@echo off
cd /d "%~dp0"
python "daily_paper_trade_logger.py" >> "paper_trade_execution.log" 2>&1
