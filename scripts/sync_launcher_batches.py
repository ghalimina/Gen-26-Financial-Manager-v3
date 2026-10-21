import os

workspace = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

files = [
    "00_START_GEN26_SYSTEM.bat",
    "START.bat",
    "start_dashboard.bat",
    "run.bat",
    "START_PAPER_SESSION.bat",
    "start_system.bat",
    "start system.bat"
]

batch_code = (
    "@echo off\r\n"
    "setlocal EnableExtensions\r\n"
    "chcp 65001 >nul 2>&1\r\n"
    "title GEN-26 QUANTUM TERMINAL (v4.7) - LIVE THNDR ^& EGX ENGINE\r\n"
    "color 0B\r\n"
    "\r\n"
    "cd /d \"%~dp0\"\r\n"
    "set \"PYTHONPATH=%~dp0\"\r\n"
    "set \"PYTHONUTF8=1\"\r\n"
    "set \"PYTHONIOENCODING=utf-8\"\r\n"
    "set \"FLASK_APP=dashboard/app.py\"\r\n"
    "\r\n"
    "echo ======================================================================\r\n"
    "echo   GEN-26 QUANTUM TERMINAL (v4.7) - LIVE THNDR ^& EGX ENGINE\r\n"
    "echo   Workspace : %~dp0\r\n"
    "echo   URL       : http://127.0.0.1:5000\r\n"
    "echo ======================================================================\r\n"
    "echo.\r\n"
    "\r\n"
    "echo [1/3] Safely cleaning up any old server process on port 5000...\r\n"
    "powershell -NoProfile -ExecutionPolicy Bypass -Command \"Get-NetTCPConnection -LocalPort 5000 -State Listen -ErrorAction SilentlyContinue | ForEach-Object { if ($_.OwningProcess -gt 4) { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue } }\" >nul 2>&1\r\n"
    "for /f \"tokens=5\" %%a in ('netstat -ano -p tcp ^| findstr /c:\":5000 \" ^| findstr /i \"LISTENING\"') do (\r\n"
    "    if not \"%%a\"==\"0\" if not \"%%a\"==\"4\" (\r\n"
    "        echo       Stopping old PID %%a on port 5000...\r\n"
    "        taskkill /F /PID %%a >nul 2>&1\r\n"
    "    )\r\n"
    ")\r\n"
    "\r\n"
    "set \"PY_EXE=C:\\Python312\\python.exe\"\r\n"
    "if not exist \"%PY_EXE%\" (\r\n"
    "    set \"PY_EXE=python\"\r\n"
    ")\r\n"
    "echo [2/3] Using Python Interpreter: %PY_EXE%\r\n"
    "echo [2.5/3] Fast-syncing live TradingView market prices...\r\n"
    "\"%PY_EXE%\" \"%~dp0scripts\\unify_ssot_prices.py\"\r\n"
    "echo.\r\n"
    "echo [3/3] Starting GEN-26 Live Server ^& Opening Browser (http://127.0.0.1:5000)...\r\n"
    "echo       Keep this window OPEN to view live [API LIVE] requests in real time.\r\n"
    "echo ======================================================================\r\n"
    "echo.\r\n"
    "\r\n"
    "\"%PY_EXE%\" \"%~dp0dashboard\\app.py\"\r\n"
    "\r\n"
    "echo.\r\n"
    "echo ======================================================================\r\n"
    "echo [NOTICE] Server process ended (Exit Code: %ERRORLEVEL%).\r\n"
    "echo Press any key to close this window...\r\n"
    "pause >nul\r\n"
)

for fname in files:
    fpath = os.path.join(workspace, fname)
    with open(fpath, "wb") as f:
        f.write(batch_code.encode("ascii"))
    print(f"Successfully generated safe pure-ASCII batch: {fname}")
