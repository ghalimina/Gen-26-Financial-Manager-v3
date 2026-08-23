#!/usr/bin/env python3
# =============================================================================
# tests/test_market_scheduler.py — Unit Tests for EGX Automated Market Scheduler
# Verifies trading session hours, APScheduler job registration, and cycle execution.
# =============================================================================

import os
import sys
import datetime
import unittest

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

try:
    import pytz
    CAIRO_TZ = pytz.timezone("Africa/Cairo")
except ImportError:
    CAIRO_TZ = None

from core.market_calendar import EGXMarketCalendar
from core.market_scheduler import EGXMarketScheduler
from dashboard.app import app


class TestEGXMarketScheduler(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()

    def tearDown(self):
        # Ensure scheduler is stopped cleanly after tests
        EGXMarketScheduler.stop()

    def test_01_active_trading_hours_logic(self):
        """Verify EGX trading hours logic: Sun-Thu 10:00 to 14:30 Cairo Time."""
        # Active trading session: Sunday at 11:30 AM Cairo
        dt_active = datetime.datetime(2026, 8, 23, 11, 30, 0)  # Sunday
        if CAIRO_TZ:
            dt_active = CAIRO_TZ.localize(dt_active)
        self.assertTrue(EGXMarketCalendar.is_market_session_open(dt_active))

        # Pre-market: Sunday at 09:30 AM Cairo
        dt_pre = datetime.datetime(2026, 8, 23, 9, 30, 0)
        if CAIRO_TZ:
            dt_pre = CAIRO_TZ.localize(dt_pre)
        self.assertFalse(EGXMarketCalendar.is_market_session_open(dt_pre))

        # Post-market: Sunday at 15:00 PM Cairo
        dt_post = datetime.datetime(2026, 8, 23, 15, 0, 0)
        if CAIRO_TZ:
            dt_post = CAIRO_TZ.localize(dt_post)
        self.assertFalse(EGXMarketCalendar.is_market_session_open(dt_post))

        # Weekend: Friday at 11:30 AM Cairo
        dt_friday = datetime.datetime(2026, 8, 21, 11, 30, 0)  # Friday
        if CAIRO_TZ:
            dt_friday = CAIRO_TZ.localize(dt_friday)
        self.assertFalse(EGXMarketCalendar.is_market_session_open(dt_friday))

        # Weekend: Saturday at 12:00 PM Cairo
        dt_saturday = datetime.datetime(2026, 8, 22, 12, 0, 0)  # Saturday
        if CAIRO_TZ:
            dt_saturday = CAIRO_TZ.localize(dt_saturday)
        self.assertFalse(EGXMarketCalendar.is_market_session_open(dt_saturday))

        # Holiday: 2026-10-06 Armed Forces Day (Tuesday at 11:30 AM)
        dt_holiday = datetime.datetime(2026, 10, 6, 11, 30, 0)
        if CAIRO_TZ:
            dt_holiday = CAIRO_TZ.localize(dt_holiday)
        self.assertFalse(EGXMarketCalendar.is_market_session_open(dt_holiday))

    def test_02_scheduler_lifecycle_and_job_registration(self):
        """Verify scheduler start, job registration, and graceful stop."""
        started = EGXMarketScheduler.start()
        self.assertTrue(started)
        self.assertTrue(EGXMarketScheduler.is_running())

        # Check job registration
        info = EGXMarketScheduler.get_job_info()
        self.assertEqual(info["status"], "RUNNING")
        self.assertEqual(info["job_id"], EGXMarketScheduler.JOB_ID)
        self.assertIn("15", str(info["trigger"]))

        # Check idempotent start
        self.assertTrue(EGXMarketScheduler.start())

        # Check graceful stop
        stopped = EGXMarketScheduler.stop()
        self.assertTrue(stopped)
        self.assertFalse(EGXMarketScheduler.is_running())

    def test_03_run_market_cycle_execution(self):
        """Verify run_market_cycle updates rankings, database prices, and audits stop losses."""
        res = EGXMarketScheduler.run_market_cycle(force=True)
        self.assertEqual(res["status"], "SUCCESS")
        self.assertGreater(res["ranked_count"], 0)
        self.assertGreater(res["prices_updated"], 0)
        self.assertIsInstance(res["stop_loss_breaches"], list)
        self.assertIn("timestamp", res)

    def test_04_api_scheduler_endpoints(self):
        """Verify Flask API endpoints /api/scheduler/status and /api/scheduler/run_cycle."""
        EGXMarketScheduler.start()

        # Status endpoint
        res_status = self.client.get("/api/scheduler/status")
        self.assertEqual(res_status.status_code, 200)
        data_status = res_status.get_json()
        self.assertIn("status", data_status)
        self.assertEqual(data_status["status"], "RUNNING")

        # Run cycle endpoint
        res_run = self.client.post("/api/scheduler/run_cycle?force=true")
        self.assertEqual(res_run.status_code, 200)
        data_run = res_run.get_json()
        self.assertEqual(data_run["status"], "SUCCESS")
        self.assertGreater(data_run["ranked_count"], 0)


if __name__ == "__main__":
    unittest.main()
