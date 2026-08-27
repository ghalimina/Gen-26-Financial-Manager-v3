#!/usr/bin/env python3
# =============================================================================
# tests/test_mlops_triggers.py — GEN-26 Dual-Track MLOps Retraining Triggers Tests
# Validates both Event-Driven Emergency Triggers and Time-Driven Weekly Fallback.
# =============================================================================

import unittest
import os
import sys
import datetime
from unittest.mock import patch

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.mlops_pipeline import MLOpsPipeline
from core.multi_horizon_engine import MultiHorizonEngine


class TestMLOpsTriggers(unittest.TestCase):

    def setUp(self):
        # Reset system status to OPERATIONAL before each test
        MLOpsPipeline.set_system_status("OPERATIONAL", reason="Test Suite Setup")

    def tearDown(self):
        # Clean up system status
        MLOpsPipeline.set_system_status("OPERATIONAL", reason="Test Suite Teardown")

    def test_01_emergency_trigger_macro_shock_tuesday(self):
        """
        Test A: A simulated CBE Rate hike on a Tuesday (weekday=1)
        triggers an immediate emergency retrain, sends Telegram alert, and sets status.
        """
        # Tuesday: 2026-08-25
        tuesday_date = datetime.date(2026, 8, 25)
        self.assertEqual(tuesday_date.weekday(), 1)  # 1 = Tuesday

        mock_macro_shock = {
            "cbe_rate_changed": True,
            "cbe_rate_delta": 2.0,  # 200 bps hike
            "usd_egp_pct_change_24h": 0.5,
            "egx30_daily_return_pct": -0.8,
            "consecutive_stop_losses": 0,
            "rolling_hit_rate_pct": 80.0,
            "closed_trades_count": 10,
            "cross_sectional_atr_pct": 2.5,
            "atr_pct_ma20": 2.5
        }

        with patch("core.notification_gateway.TelegramNotifier.send_message") as mock_telegram:
            result = MLOpsPipeline.run_dual_track_cycle(today_date=tuesday_date, mock_state=mock_macro_shock)

            # Assertions
            self.assertTrue(result["retrain_triggered"])
            self.assertEqual(result["track"], "EVENT_DRIVEN_EMERGENCY")
            self.assertEqual(result["action"], "EMERGENCY_RETRAIN_EXECUTED")
            self.assertIn("صدمة اقتصاد كلي", result["reason"])

            # Verify Telegram alert was dispatched with emergency icon
            self.assertTrue(mock_telegram.called)
            call_args = mock_telegram.call_args_list[0]
            alert_text = call_args[0][0] if len(call_args[0]) > 0 else call_args[1].get("text", "")
            self.assertTrue("🚨" in alert_text or "طوارئ" in alert_text or "EMERGENCY" in alert_text)

    def test_02_routine_weekly_retrain_friday(self):
        """
        Test B: A quiet week with no alarms triggers the routine retrain
        when the date is set to a Friday (weekday=4) without halting the system.
        """
        # Friday: 2026-08-28
        friday_date = datetime.date(2026, 8, 28)
        self.assertEqual(friday_date.weekday(), 4)  # 4 = Friday

        mock_quiet_market = {
            "cbe_rate_changed": False,
            "cbe_rate_delta": 0.0,
            "usd_egp_pct_change_24h": 0.2,
            "egx30_daily_return_pct": 0.45,
            "consecutive_stop_losses": 0,
            "rolling_hit_rate_pct": 85.0,
            "closed_trades_count": 10,
            "cross_sectional_atr_pct": 2.2,
            "atr_pct_ma20": 2.3
        }

        with patch("core.notification_gateway.TelegramNotifier.send_message") as mock_telegram:
            result = MLOpsPipeline.run_dual_track_cycle(today_date=friday_date, mock_state=mock_quiet_market)

            # Assertions
            self.assertTrue(result["retrain_triggered"])
            self.assertEqual(result["track"], "TIME_DRIVEN_ROUTINE_FALLBACK")
            self.assertEqual(result["action"], "ROUTINE_WEEKLY_RETRAIN_EXECUTED")
            self.assertEqual(result["system_status"], "OPERATIONAL")

            # Verify Telegram alert was dispatched with routine icon
            self.assertTrue(mock_telegram.called)
            call_args = mock_telegram.call_args_list[0]
            alert_text = call_args[0][0] if len(call_args[0]) > 0 else call_args[1].get("text", "")
            self.assertTrue("🔄" in alert_text or "صيانة" in alert_text or "ROUTINE" in alert_text)

    def test_03_quiet_midweek_no_retrain(self):
        """
        Verify that a quiet Wednesday (weekday=2) with normal conditions
        does NOT trigger retraining (NO_ACTION).
        """
        # Wednesday: 2026-08-26
        wednesday_date = datetime.date(2026, 8, 26)
        self.assertEqual(wednesday_date.weekday(), 2)  # 2 = Wednesday

        mock_normal_state = {
            "cbe_rate_changed": False,
            "cbe_rate_delta": 0.0,
            "usd_egp_pct_change_24h": -0.1,
            "egx30_daily_return_pct": 0.30,
            "consecutive_stop_losses": 0,
            "rolling_hit_rate_pct": 80.0,
            "closed_trades_count": 10,
            "cross_sectional_atr_pct": 2.4,
            "atr_pct_ma20": 2.4
        }

        result = MLOpsPipeline.run_dual_track_cycle(today_date=wednesday_date, mock_state=mock_normal_state)
        self.assertFalse(result["retrain_triggered"])
        self.assertEqual(result["action"], "NO_ACTION")
        self.assertEqual(result["system_status"], "OPERATIONAL")

    def test_04_emergency_market_crash_trigger(self):
        """
        Verify that a single-session EGX30 drop > 5% triggers emergency retrain.
        """
        mock_crash_state = {
            "egx30_daily_return_pct": -5.60,
            "cbe_rate_changed": False,
            "consecutive_stop_losses": 0,
            "cross_sectional_atr_pct": 2.5,
            "atr_pct_ma20": 2.5
        }
        res = MLOpsPipeline.evaluate_emergency_triggers(mock_crash_state)
        self.assertTrue(res["emergency_triggered"])
        self.assertTrue(res["metrics"]["market_crash"])
        self.assertIn("انهيار سوق حاد", res["primary_reason"])

    def test_05_emergency_performance_bleed_consecutive_stops(self):
        """
        Verify that 3 consecutive stop losses hit triggers emergency retrain.
        """
        mock_bleed_state = {
            "consecutive_stop_losses": 3,
            "rolling_hit_rate_pct": 60.0,
            "closed_trades_count": 10,
            "egx30_daily_return_pct": -0.5
        }
        res = MLOpsPipeline.evaluate_emergency_triggers(mock_bleed_state)
        self.assertTrue(res["emergency_triggered"])
        self.assertTrue(res["metrics"]["performance_bleed"])
        self.assertIn("نزيف أداء متتالي", res["primary_reason"])

    def test_06_emergency_volatility_explosion(self):
        """
        Verify that ATR% expanding > 50% vs 20-day MA triggers emergency retrain.
        """
        mock_vol_state = {
            "cross_sectional_atr_pct": 4.5,
            "atr_pct_ma20": 2.5,  # 4.5 / 2.5 = 1.80 (> 1.50)
            "egx30_daily_return_pct": -1.0
        }
        res = MLOpsPipeline.evaluate_emergency_triggers(mock_vol_state)
        self.assertTrue(res["emergency_triggered"])
        self.assertTrue(res["metrics"]["volatility_explosion"])
        self.assertIn("انفجار تقلبات السوق", res["primary_reason"])

    def test_07_emergency_halt_blocks_short_term_opportunities(self):
        """
        Verify that when SYSTEM_STATUS is EMERGENCY_HALT, MultiHorizonEngine blocks BUY opportunities.
        """
        MLOpsPipeline.set_system_status("EMERGENCY_HALT", reason="Active Emergency Retraining Test")
        opps = MultiHorizonEngine.generate_short_term_opportunities()

        self.assertEqual(opps["system_status"], "EMERGENCY_HALT")
        self.assertEqual(opps["opportunities_count"], 0)
        self.assertEqual(len(opps["opportunities"]), 0)
        self.assertIn("تعليق", opps["fallback_message_ar"])


if __name__ == "__main__":
    unittest.main()
