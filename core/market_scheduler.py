#!/usr/bin/env python3
# =============================================================================
# core/market_scheduler.py — GEN-26 Automated EGX Market Background Scheduler
# Schedules automated 15-minute quantitative cycles during active EGX trading hours
# (Sunday to Thursday, 10:00 AM to 02:30 PM Cairo Time) using APScheduler.
# =============================================================================

import os
import sys
import logging
import datetime
from typing import Dict, List, Any, Optional

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

try:
    import pytz
    CAIRO_TZ = pytz.timezone("Africa/Cairo")
except ImportError:
    CAIRO_TZ = None

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    APSCHEDULER_AVAILABLE = True
except ImportError:
    BackgroundScheduler = None
    CronTrigger = None
    APSCHEDULER_AVAILABLE = False

from core.market_calendar import EGXMarketCalendar
from core.market_price_service import MarketPriceService
from core.price_sync_service import PriceSyncService
from core.multi_horizon_engine import MultiHorizonEngine
from core.database import DatabaseManager
from core.real_portfolio import RealPortfolioTracker

logger = logging.getLogger("GEN26.MarketScheduler")


class EGXMarketScheduler:
    """
    Automated Background Scheduler for the Egyptian Exchange (EGX).
    Executes quantitative ranking, database price sync, and risk invariant audits
    every 15 minutes exclusively during active trading sessions.
    """

    JOB_ID = "egx_market_15min_cycle"
    _scheduler: Optional[Any] = None
    _last_run_result: Optional[Dict[str, Any]] = None

    @classmethod
    def get_scheduler_instance(cls):
        """Returns or creates the BackgroundScheduler singleton instance."""
        if cls._scheduler is None and APSCHEDULER_AVAILABLE:
            timezone = CAIRO_TZ if CAIRO_TZ else "Africa/Cairo"
            cls._scheduler = BackgroundScheduler(timezone=timezone)
        return cls._scheduler

    @classmethod
    def is_running(cls) -> bool:
        """Returns True if the background scheduler is active and running."""
        return cls._scheduler is not None and cls._scheduler.running

    @classmethod
    def start(cls) -> bool:
        """
        Starts the background scheduler gracefully without blocking the HTTP server.
        Registers the 15-minute EGX market trading cycle job.
        """
        if not APSCHEDULER_AVAILABLE:
            logger.warning("APScheduler is not installed. Background scheduler disabled.")
            return False

        scheduler = cls.get_scheduler_instance()
        if scheduler is None:
            return False

        if scheduler.running:
            logger.info("EGX Market Scheduler is already running.")
            return True

        # EGX Active Trading Hours: Sunday to Thursday, 10:00 AM to 02:30 PM Cairo Time
        # Run every 15 minutes during hours 10, 11, 12, 13, 14
        trigger = CronTrigger(
            day_of_week="sun,mon,tue,wed,thu",
            hour="10-14",
            minute="*/15",
            timezone=CAIRO_TZ if CAIRO_TZ else "Africa/Cairo"
        )

        # Remove existing job if already registered
        if scheduler.get_job(cls.JOB_ID):
            scheduler.remove_job(cls.JOB_ID)

        scheduler.add_job(
            func=cls.run_market_cycle,
            trigger=trigger,
            id=cls.JOB_ID,
            name="EGX 15-Minute MultiHorizon & Risk Audit Cycle",
            replace_existing=True,
            max_instances=1,
            coalesce=True
        )

        scheduler.start()
        logger.info("EGX Market Scheduler successfully started in background.")
        return True

    @classmethod
    def stop(cls) -> bool:
        """Gracefully shuts down the background scheduler."""
        if cls._scheduler is not None and cls._scheduler.running:
            cls._scheduler.shutdown(wait=False)
            cls._scheduler = None
            logger.info("EGX Market Scheduler shutdown complete.")
            return True
        return False

    @classmethod
    def get_job_info(cls) -> Dict[str, Any]:
        """Returns metadata about the registered scheduler job."""
        if not cls.is_running() or cls._scheduler is None:
            return {"status": "STOPPED", "job": None}

        job = cls._scheduler.get_job(cls.JOB_ID)
        if not job:
            return {"status": "RUNNING_NO_JOB", "job": None}

        next_run = str(job.next_run_time) if job.next_run_time else None
        return {
            "status": "RUNNING",
            "job_id": job.id,
            "name": job.name,
            "next_run_time": next_run,
            "trigger": str(job.trigger),
            "last_run_result": cls._last_run_result
        }

    @classmethod
    def run_market_cycle(cls, force: bool = False) -> Dict[str, Any]:
        """
        Executes one full market cycle:
        1. Checks whether EGX market is currently open (unless force=True).
        2. Refreshes MultiHorizonEngine cross-sectional rankings.
        3. Updates canonical market prices in DatabaseManager.
        4. Audits active portfolio stop-loss invariants (-7.0% hard floor).
        """
        now_cairo = EGXMarketCalendar.get_cairo_time()
        is_open = EGXMarketCalendar.is_market_session_open(now_cairo)

        if not is_open and not force:
            result = {
                "timestamp": now_cairo.strftime("%Y-%m-%d %H:%M:%S"),
                "status": "SKIPPED_MARKET_CLOSED",
                "reason": "EGX continuous trading is currently closed (Trading hours: Sun-Thu 10:00-14:30 Cairo)",
                "market_open": False
            }
            cls._last_run_result = result
            return result

        logger.info(f"Executing EGX Quantitative Cycle at {now_cairo.isoformat()}...")

        # Step 1: Live Market Price Synchronization (SSOT)
        sync_meta = {}
        try:
            sync_meta = PriceSyncService.sync_all_prices()
        except Exception as e:
            logger.warning(f"Price sync during market cycle encountered warning: {e}")

        # Step 2: Trigger MultiHorizon Engine Cross-Sectional Ranking
        rankings = MultiHorizonEngine.get_all_multi_horizon_rankings(universe="all")
        ranked_count = len(rankings)

        # Step 3: Update Market Prices in SQLite Database
        prices_updated = 0
        try:
            canonical_prices = MarketPriceService.get_all_canonical_prices(universe="all")
            now_iso = datetime.datetime.now().isoformat()
            with DatabaseManager.get_connection() as conn:
                cur = conn.cursor()
                for rec in canonical_prices:
                    # Guarantee parent stock record exists to satisfy foreign key constraint
                    cur.execute("""
                    INSERT OR IGNORE INTO stocks (ticker, company_name, sector, isin, status, is_core, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?);
                    """, (
                        rec["ticker"],
                        rec.get("company_name", rec["ticker"]),
                        rec.get("sector", "General"),
                        rec.get("isin", ""),
                        "TRADABLE",
                        1,
                        now_iso
                    ))

                    p_val = rec.get("price")
                    turnover_val = float(rec.get("turnover_egp", 0.0) or 0.0)
                    adv_calc = (turnover_val / p_val) if (p_val is not None and p_val > 0) else 0.0

                    cur.execute("""
                    INSERT OR REPLACE INTO market_prices (ticker, market_date, open_price, high_price, low_price, close_price, volume, adv_20d, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """, (
                        rec["ticker"],
                        rec.get("market_date") or now_cairo.strftime("%Y-%m-%d"),
                        float(rec.get("open") or p_val or 0.0),
                        float(rec.get("high") or p_val or 0.0),
                        float(rec.get("low") or p_val or 0.0),
                        float(p_val or 0.0),
                        int(rec.get("volume") or 0),
                        adv_calc,
                        now_iso
                    ))
                conn.commit()
                prices_updated = len(canonical_prices)
        except Exception as e:
            logger.error(f"Failed to update database prices: {e}")

        # Step 3: Check Active Portfolio Stop-Loss Invariants
        stop_loss_breaches = []
        try:
            portfolio_analysis = RealPortfolioTracker.analyze_real_portfolio()
            for pos in portfolio_analysis.get("positions", []):
                cp = pos.get("current_price", 0.0)
                sl = pos.get("stop_loss", 0.0)
                if cp > 0 and sl > 0 and cp <= sl:
                    stop_loss_breaches.append({
                        "ticker": pos.get("ticker"),
                        "company_name": pos.get("company_name"),
                        "current_price": cp,
                        "stop_loss": sl,
                        "alert": "STOP_LOSS_BREACHED",
                        "action_required": "EXIT_POSITION"
                    })
        except Exception as e:
            logger.error(f"Failed to audit portfolio stop losses: {e}")

        result = {
            "timestamp": now_cairo.strftime("%Y-%m-%d %H:%M:%S"),
            "status": "SUCCESS",
            "market_open": is_open,
            "ranked_count": ranked_count,
            "prices_updated": prices_updated,
            "stop_loss_breaches_count": len(stop_loss_breaches),
            "stop_loss_breaches": stop_loss_breaches
        }

        cls._last_run_result = result
        logger.info(f"EGX Quantitative Cycle completed: {ranked_count} stocks ranked, {prices_updated} prices updated, {len(stop_loss_breaches)} stop-loss breaches.")
        return result


if __name__ == "__main__":
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    print("=" * 70)
    print("GEN-26 AUTOMATED EGX MARKET SCHEDULER CLI")
    print("=" * 70)
    res = EGXMarketScheduler.run_market_cycle(force=True)
    print(f"Status: {res['status']}")
    print(f"Ranked Stocks: {res['ranked_count']}")
    print(f"Prices Updated: {res['prices_updated']}")
    print(f"Stop-Loss Breaches: {res['stop_loss_breaches_count']}")
    print("=" * 70)
