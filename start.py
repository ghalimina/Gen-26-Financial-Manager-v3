#!/usr/bin/env python3
# =============================================================================
# start.py — GEN-26 Cross-Platform Control Center Launcher
# Starts the local read-only dashboard on http://127.0.0.1:5000 and opens the browser.
# GUARANTEE: READ-ONLY MONITORING ONLY. ZERO REAL-MONEY EXECUTION.
# =============================================================================

import os
import sys
import webbrowser
import threading
import time

WORKSPACE = os.path.dirname(os.path.abspath(__file__))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from dashboard.app import app


def open_browser():
    time.sleep(1.5)
    webbrowser.open("http://127.0.0.1:5000")


if __name__ == "__main__":
    print("=" * 70)
    print("🏛️ GEN-26 FINANCIAL MANAGER v3.0 — QUANT CONTROL CENTER")
    print("   URL: http://127.0.0.1:5000")
    print("   Mode: READ-ONLY MONITORING ONLY")
    print("   Live Trading: STRICTLY BLOCKED")
    print("=" * 70)
    
    threading.Thread(target=open_browser, daemon=True).start()
    app.run(host="127.0.0.1", port=5000, debug=False)
