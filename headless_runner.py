#!/usr/bin/env python3
# =============================================================================
# headless_runner.py — GEN-26 V4.1 Headless Execution Engine
# Called by: GitHub Actions (.github/workflows/*.yml)
# Purpose: Run paper trading session autonomously without UI
# RULE: NO REAL TRADING. PAPER ONLY.
# =============================================================================
import sys
import os
import datetime
import json
import traceback

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
sys.path.insert(0, BASE_DIR)

try:
    import pytz
    cairo_tz = pytz.timezone('Africa/Cairo')
    now_cairo = datetime.datetime.now(cairo_tz)
except ImportError:
    now_cairo = datetime.datetime.utcnow() + datetime.timedelta(hours=3)
    print("[WARN] pytz not available, using UTC+3 approximation")

from session_manager import SessionManager

def main():
    print("=" * 70)
    print("🏛️ GEN-26 V4.1 — HEADLESS PAPER TRADING ENGINE")
    print(f"   Run Time (Cairo): {now_cairo.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Mode: PAPER ONLY — NO REAL EXECUTION")
    print("=" * 70)

    market_date = now_cairo.strftime("%Y-%m-%d")
    weekday = now_cairo.weekday()  # Mon=0..Sun=6

    # EGX closed on Friday (4) and Saturday (5)
    if weekday in [4, 5]:
        print(f"[SKIP] EGX is closed today ({now_cairo.strftime('%A')}). No paper session.")
        return 0

    print(f"\n[1/4] Starting paper session for date: {market_date}")
    session_id = SessionManager.start_session(market_date)

    if session_id is None:
        print(f"[SKIP] Session already completed for {market_date} or duplicate detected.")
        valid_days = SessionManager.get_valid_days()
        print(f"[INFO] Total valid paper days: {valid_days} / 30")
        return 0

    try:
        print(f"[2/4] Session ID: {session_id}")
        print(f"[3/4] Running screener pipeline...")

        # Import the screener pipeline
        from egx_screener import main as run_screener
        run_screener()

        print(f"[4/4] Completing session...")
        SessionManager.complete_session(session_id, data_status="VALID")

        valid_days = SessionManager.get_valid_days()
        print(f"\n✅ Session completed successfully.")
        print(f"   Paper days completed: {valid_days} / 30")
        print(f"   Production gate: {'BLOCKED (need more days)' if valid_days < 30 else '⚠️ READY FOR REVIEW'}")

        # Update execution_status.json
        status_path = os.path.join(BASE_DIR, "execution_status.json")
        status = {}
        if os.path.exists(status_path):
            try:
                with open(status_path, 'r', encoding='utf-8') as f:
                    status = json.load(f)
            except:
                pass

        status['last_updated'] = now_cairo.strftime("%Y-%m-%d %H:%M")
        status['last_headless_run'] = now_cairo.isoformat()
        status['paper_session_count'] = valid_days
        status['last_session_id'] = session_id
        status['last_market_date'] = market_date

        with open(status_path, 'w', encoding='utf-8') as f:
            json.dump(status, f, indent=2, ensure_ascii=False)

        return 0

    except Exception as e:
        print(f"\n❌ Session FAILED: {e}")
        traceback.print_exc()
        SessionManager.fail_session(session_id, reason=str(e)[:200])
        return 1

if __name__ == "__main__":
    sys.exit(main())
