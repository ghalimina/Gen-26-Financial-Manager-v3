@echo off
title Gen-26 Institutional System Audit (10 Checks)
echo ======================================================
echo 🔍 Running Gen-26 System Audit Checklist (10/10)...
echo ======================================================
cd /d "%~dp0"
python system_full_audit.py
pause
