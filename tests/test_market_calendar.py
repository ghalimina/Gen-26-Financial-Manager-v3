#!/usr/bin/env python3
# =============================================================================
# tests/test_market_calendar.py — GEN-26 EGX Market Calendar Unit Tests
# Validates Egyptian Exchange trading days, weekend rules, and holiday filtering.
# =============================================================================

import unittest
import os
import sys
import datetime

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.market_calendar import EGXMarketCalendar


class TestMarketCalendar(unittest.TestCase):

    def test_01_valid_trading_days(self):
        """
        Verify that Sunday to Thursday dates are valid trading days (if not holidays).
        2026-08-16 was Sunday
        2026-08-17 was Monday
        2026-08-18 was Tuesday
        2026-08-19 was Wednesday
        2026-08-20 was Thursday
        """
        for d in ["2026-08-16", "2026-08-17", "2026-08-18", "2026-08-19", "2026-08-20"]:
            res = EGXMarketCalendar.is_trading_day(d)
            self.assertTrue(res["is_trading_day"], f"Expected {d} to be trading day")
            self.assertEqual(res["reason"], "VALID_EGX_TRADING_DAY")

    def test_02_weekend_rejection(self):
        """
        Verify that Friday and Saturday are rejected as EGX weekends.
        2026-08-21 is Friday
        2026-08-22 is Saturday
        """
        res_fri = EGXMarketCalendar.is_trading_day("2026-08-21")
        self.assertFalse(res_fri["is_trading_day"])
        self.assertIn("EGX_WEEKEND", res_fri["reason"])

        res_sat = EGXMarketCalendar.is_trading_day("2026-08-22")
        self.assertFalse(res_sat["is_trading_day"])
        self.assertIn("EGX_WEEKEND", res_sat["reason"])

    def test_03_holiday_rejection(self):
        """
        Verify that Egyptian national/market holidays are rejected.
        2026-01-07 (Wednesday - Coptic Christmas)
        2026-06-30 (Tuesday - 30 June)
        2026-07-23 (Thursday - Revolution Day)
        2026-10-06 (Tuesday - Armed Forces Day)
        """
        for hol in ["2026-01-07", "2026-06-30", "2026-07-23", "2026-10-06"]:
            res = EGXMarketCalendar.is_trading_day(hol)
            self.assertFalse(res["is_trading_day"])
            self.assertIn("EGX_HOLIDAY", res["reason"])

    def test_04_continuous_trading_hours(self):
        """
        Verify 10:00 to 14:30 Cairo market hours.
        """
        dt_open = datetime.datetime(2026, 8, 18, 11, 30) # Tuesday 11:30 -> Open
        self.assertTrue(EGXMarketCalendar.is_market_session_open(dt_open))

        dt_pre = datetime.datetime(2026, 8, 18, 9, 30) # Tuesday 09:30 -> Closed
        self.assertFalse(EGXMarketCalendar.is_market_session_open(dt_pre))

        dt_post = datetime.datetime(2026, 8, 18, 15, 0) # Tuesday 15:00 -> Closed
        self.assertFalse(EGXMarketCalendar.is_market_session_open(dt_post))


if __name__ == "__main__":
    unittest.main()
