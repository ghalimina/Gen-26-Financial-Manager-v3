#!/usr/bin/env python3
# =============================================================================
# tests/test_quant_books_engine.py — Sprint 2 STLC Quant Books Engine Tests
# Validates the 10 Books Quantitative Mathematical Suite & Algorithmic Integration:
# - TC-B01: Piotroski F-Score on COMI.CA returns score 0-9 with breakdown.
# - TC-B02: Lynch classification and PEG calculation.
# - TC-B03: Candlestick pattern detection on simulated/real OHLCV candles.
# - TC-B04: Murphy ADX trend classification and Fibonacci level calculations.
# - TC-B05: Anti-Revenge lockout triggering on 2 consecutive losses and R:R >= 2.5 enforcement.
# =============================================================================

import os
import sys
import unittest
import datetime

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.quant_books_engine import QuantBooksEngine
from dashboard.app import app


class TestQuantBooksEngine(unittest.TestCase):

    def setUp(self):
        """Set up testing client and reset lockout state."""
        self.app = app.test_client()
        self.app.testing = True
        QuantBooksEngine._LOCKOUT_UNTIL = None
        QuantBooksEngine._CLOSED_TRADES_MEMORY = []

    def test_tc_b01_piotroski_f_score(self):
        """
        TC-B01: Piotroski F-Score on COMI.CA returns score 0-9 with breakdown.
        Verifies all 3 dimensions (Profitability, Leverage/Liquidity, Operating Efficiency).
        """
        res = QuantBooksEngine.calculate_piotroski_f_score("COMI.CA")
        
        self.assertIsNotNone(res)
        self.assertEqual(res["ticker"], "COMI.CA")
        self.assertGreaterEqual(res["f_score"], 0)
        self.assertLessEqual(res["f_score"], 9)
        self.assertIn(res["rating"], ["STRONG_FINANCIAL_HEALTH", "MODERATE_HEALTH", "WEAK_DISTRESSED"])
        self.assertIsInstance(res["signals"], dict)
        self.assertIn("positive_roa", res["signals"])
        self.assertIn("positive_cfo", res["signals"])
        self.assertIn("lower_leverage", res["signals"])
        self.assertIn("higher_gross_margin", res["signals"])
        self.assertGreater(len(res["breakdown_ar"]), 0)

        # Test Flask API Endpoint
        resp = self.app.get("/api/books/piotroski/COMI.CA")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "SUCCESS")
        self.assertEqual(data["data"]["ticker"], "COMI.CA")

    def test_tc_b02_peter_lynch_metrics(self):
        """
        TC-B02: Lynch classification and PEG calculation.
        Verifies PEG calculation, Net Cash Per Share, Lynch Fair Value, and Categorization.
        """
        res = QuantBooksEngine.evaluate_peter_lynch_metrics("COMI.CA", current_price=139.28)
        
        self.assertIsNotNone(res)
        self.assertEqual(res["ticker"], "COMI.CA")
        self.assertGreater(res["trailing_pe"], 0.0)
        self.assertGreater(res["growth_rate_pct"], 0.0)
        self.assertGreater(res["peg_ratio"], 0.0)
        self.assertIn(res["category"], ["FAST_GROWER", "STALWART", "CYCLICAL", "TURNAROUND", "SLOW_GROWER"])
        self.assertIn("lynch_fair_value", res)
        self.assertIn("valuation_status", res)

        # Test Flask API Endpoint
        resp = self.app.get("/api/books/lynch/COMI.CA")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "SUCCESS")
        self.assertIn("peg_ratio", data["data"])

    def test_tc_b03_candlestick_pattern_detection(self):
        """
        TC-B03: Candlestick pattern detection on simulated/real OHLCV candles.
        Tests Bullish Engulfing, Hammer at Support, Morning Star, and Piercing Line.
        """
        # 1. Test Bullish Engulfing
        engulfing_candles = [
            {"open": 100.0, "high": 101.0, "low": 95.0, "close": 96.0, "volume": 10000}, # Red candle
            {"open": 95.0, "high": 104.0, "low": 94.0, "close": 103.0, "volume": 25000}  # Green candle engulfing
        ]
        patterns = QuantBooksEngine.detect_candlestick_patterns(engulfing_candles)
        self.assertTrue(any(p["pattern"] == "BULLISH_ENGULFING" for p in patterns))

        # 2. Test Hammer at Support
        hammer_candles = [
            {"open": 100.0, "high": 100.5, "low": 92.0, "close": 99.5, "volume": 15000}
        ]
        patterns_hammer = QuantBooksEngine.detect_candlestick_patterns(hammer_candles)
        self.assertTrue(any(p["pattern"] == "HAMMER_AT_SUPPORT" for p in patterns_hammer))

        # 3. Test Morning Star (3 candles)
        morning_star_candles = [
            {"open": 105.0, "high": 106.0, "low": 98.0, "close": 99.0, "volume": 10000}, # Big red
            {"open": 97.5, "high": 98.0, "low": 96.5, "close": 97.0, "volume": 8000},   # Small star
            {"open": 98.0, "high": 106.0, "low": 97.5, "close": 104.0, "volume": 28000} # Big green
        ]
        patterns_star = QuantBooksEngine.detect_candlestick_patterns(morning_star_candles)
        self.assertTrue(any(p["pattern"] == "MORNING_STAR" for p in patterns_star))

        # Test Flask API Endpoint
        resp = self.app.get("/api/books/candlesticks/COMI.CA")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "SUCCESS")
        self.assertIn("patterns", data)

    def test_tc_b04_murphy_adx_and_fibonacci(self):
        """
        TC-B04: Murphy ADX trend classification and Fibonacci level calculations.
        """
        # 1. Fibonacci Retracements
        fib = QuantBooksEngine.calculate_fibonacci_retracements(swing_high=150.0, swing_low=100.0)
        self.assertEqual(fib["swing_high"], 150.0)
        self.assertEqual(fib["swing_low"], 100.0)
        self.assertEqual(fib["diff_egp"], 50.0)
        self.assertEqual(fib["fib_50_0"], 125.0)
        self.assertAlmostEqual(fib["fib_61_8_golden"], 119.1, places=1)
        self.assertAlmostEqual(fib["fib_38_2"], 130.9, places=1)
        self.assertAlmostEqual(fib["fib_23_6"], 138.2, places=1)

        # 2. ADX Trend Filter
        highs = [100.0 + i for i in range(25)]
        lows = [95.0 + i for i in range(25)]
        closes = [98.0 + i for i in range(25)]
        adx_res = QuantBooksEngine.calculate_adx_trend_filter(highs, lows, closes, period=14)
        self.assertIn("adx", adx_res)
        self.assertIn("trend_strength", adx_res)
        self.assertEqual(adx_res["trend_direction"], "BULLISH")

    def test_tc_b05_anti_revenge_lockout_and_risk_reward(self):
        """
        TC-B05: Anti-Revenge lockout triggering on 2 consecutive losses and R:R >= 2.5 enforcement.
        """
        # 1. Risk-to-Reward Gate
        # Case A: Favorable R:R = 3.0 (Target 130, Entry 100, Stop 90) -> (30 / 10 = 3.0 >= 2.5)
        rr_good = QuantBooksEngine.verify_risk_reward_gate(entry_price=100.0, target_price=130.0, stop_loss_price=90.0)
        self.assertTrue(rr_good["passed"])
        self.assertEqual(rr_good["verdict"], "APPROVED")
        self.assertEqual(rr_good["risk_reward_ratio"], 3.0)

        # Case B: Unfavorable R:R = 1.0 (Target 110, Entry 100, Stop 90) -> (10 / 10 = 1.0 < 2.5)
        rr_bad = QuantBooksEngine.verify_risk_reward_gate(entry_price=100.0, target_price=110.0, stop_loss_price=90.0)
        self.assertFalse(rr_bad["passed"])
        self.assertEqual(rr_bad["verdict"], "REJECTED_UNFAVORABLE_RR")

        # 2. Anti-Revenge Lockout
        now = datetime.datetime.now()
        trades_with_losses = [
            {"timestamp": now - datetime.timedelta(hours=2), "pnl_pct": -4.5, "exit_reason": "STOP_LOSS"},
            {"timestamp": now - datetime.timedelta(hours=1), "pnl_pct": -3.8, "exit_reason": "STOP_LOSS"}
        ]
        lockout_res = QuantBooksEngine.evaluate_anti_revenge_circuit_breaker(trades_with_losses)
        self.assertTrue(lockout_res["is_locked"])
        self.assertEqual(lockout_res["status"], "LOCKOUT_ACTIVE")
        self.assertIn("قفل الحماية", lockout_res["reason_ar"])

        # Test Flask API Endpoint for Psychology Status
        resp = self.app.get("/api/books/psychology/status")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "SUCCESS")
        self.assertTrue(data["psychology_guard"]["is_locked"])


if __name__ == "__main__":
    unittest.main()
