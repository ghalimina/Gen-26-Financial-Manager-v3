#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# run.py — GEN-26 Institutional Quant Terminal Single-Command Launcher
# Launches the production-grade Flask Terminal & 65-endpoint REST API backend.
# =============================================================================

import os
import sys
import argparse
import webbrowser
import threading
import time

# Enforce UTF-8 on Windows command prompts
if sys.platform == "win32":
    import io
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Ensure project root is in sys.path
WORKSPACE = os.path.dirname(os.path.abspath(__file__))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

def print_banner(host: str, port: int):
    url = f"http://localhost:{port}" if host in ["0.0.0.0", "127.0.0.1"] else f"http://{host}:{port}"
    print("\n" + "=" * 74)
    print("  GEN-26 INSTITUTIONAL QUANT ROBO-ADVISOR & TRADING TERMINAL")
    print("  المدير المالي الآلي للبورصة المصرية (Egyptian Exchange - EGX)")
    print("=" * 74)
    print(f"  Local Web Terminal : {url}")
    print(f"  REST API Endpoints : 65 Institutional Endpoints (/api/*)")
    print(f"  Operation Mode     : Read-Only Advisory & Paper Incubation")
    print(f"  Safety Guard       : Live Real-Money Execution HARD-BLOCKED")
    print(f"  Signal Guard       : 30-Min TTL & +0.5% Hard Entry Ceiling")
    print(f"  Active Equities    : 155 Stocks (130 Dual-Source + 25 Single-Source)")
    print(f"  Quarantined Stocks : 15 Stocks Isolated (NEEDS_MANUAL_REVIEW)")
    print("=" * 74)
    print("  Press Ctrl+C to stop the server gracefully.\n")

def open_browser_delayed(url: str, delay_sec: float = 1.5):
    time.sleep(delay_sec)
    try:
        webbrowser.open(url)
    except Exception:
        pass

def main():
    parser = argparse.ArgumentParser(description="GEN-26 Quant Terminal Launcher")
    parser.add_argument("--host", default="0.0.0.0", help="Host address (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=5000, help="Port number (default: 5000)")
    parser.add_argument("--no-browser", action="store_true", help="Do not automatically open the browser")
    parser.add_argument("--debug", action="store_true", help="Enable Flask debug mode")
    args = parser.parse_args()

    # Pre-flight imports
    try:
        from dashboard.app import app
    except ImportError as e:
        print(f"[ERROR] Failed to import dashboard app: {e}")
        sys.exit(1)

    print_banner(args.host, args.port)

    # Pre-warm multi-horizon rankings cache for instant sub-second responses
    try:
        from core.multi_horizon_engine import MultiHorizonEngine
        print("[INFO] Pre-warming Multi-Horizon Rankings cache for core universe...")
        MultiHorizonEngine.get_all_multi_horizon_rankings(universe="core")
        print("[INFO] Multi-Horizon Rankings cache ready.\n")
    except Exception as e:
        print(f"[WARN] Cache warm-up notice: {e}\n")

    # Launch browser automatically unless disabled
    if not args.no_browser:
        target_url = f"http://localhost:{args.port}"
        threading.Thread(target=open_browser_delayed, args=(target_url,), daemon=True).start()

    # Start Flask Web Server
    try:
        app.run(host=args.host, port=args.port, debug=args.debug)
    except KeyboardInterrupt:
        print("\n[INFO] Shutting down GEN-26 Quant Terminal gracefully...")
        sys.exit(0)

if __name__ == "__main__":
    main()
