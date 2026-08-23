#!/usr/bin/env python3
# =============================================================================
# core/scheduler.py — GEN-26 Automated EGX Market Background Scheduler Alias
# Direct alias to core.market_scheduler.EGXMarketScheduler with price sync.
# =============================================================================

import os
import sys

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.market_scheduler import EGXMarketScheduler, APSCHEDULER_AVAILABLE, CAIRO_TZ
from core.price_sync_service import PriceSyncService

__all__ = ["EGXMarketScheduler", "PriceSyncService", "APSCHEDULER_AVAILABLE", "CAIRO_TZ"]

if __name__ == "__main__":
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    print("=" * 70)
    print("GEN-26 AUTOMATED EGX SCHEDULER & PRICE SYNC")
    print("=" * 70)
    res = EGXMarketScheduler.run_market_cycle(force=True)
    print(f"Status: {res['status']}")
    print(f"Ranked Stocks: {res['ranked_count']}")
    print(f"Prices Updated: {res['prices_updated']}")
    print("=" * 70)
