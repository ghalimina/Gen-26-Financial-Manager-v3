#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# tests/test_market_seasonality_engine.py — Unit Tests for MarketSeasonalityEngine
# Validates:
# 1. Ramadan Session Contraction Model.
# 2. Thursday Pre-Weekend Profit-Taking Dip Window.
# 3. December Year-End Window Dressing Effect.
# 4. Standard Active Market Cycle.
# =============================================================================

import os
import sys
import unittest

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.market_seasonality_engine import MarketSeasonalityEngine


class TestMarketSeasonalityEngine(unittest.TestCase):

    def test_01_ramadan_seasonality_detection(self):
        """Verify date within Ramadan window triggers RAMADAN_CONTRACTION."""
        res = MarketSeasonalityEngine.evaluate_current_seasonality("2026-03-01")
        self.assertEqual(res["seasonality_regime"], MarketSeasonalityEngine.REGIME_RAMADAN)
        self.assertTrue(res["is_ramadan"])
        self.assertEqual(res["volume_adjustment_factor"], 0.70)
        self.assertIn("شهر رمضان", res["strategy_tweak_ar"])

    def test_02_thursday_dip_detection(self):
        """Verify Thursday session triggers THURSDAY_PROFIT_TAKING."""
        # 2026-08-27 is Thursday
        res = MarketSeasonalityEngine.evaluate_current_seasonality("2026-08-27")
        self.assertEqual(res["seasonality_regime"], MarketSeasonalityEngine.REGIME_THURSDAY_DIP)
        self.assertTrue(res["is_thursday_session"])
        self.assertIn("خميس", res["strategy_tweak_ar"])

    def test_03_december_window_dressing(self):
        """Verify late December date triggers DECEMBER_WINDOW_DRESSING."""
        res = MarketSeasonalityEngine.evaluate_current_seasonality("2026-12-20")
        self.assertEqual(res["seasonality_regime"], MarketSeasonalityEngine.REGIME_DECEMBER_DRESSING)
        self.assertTrue(res["is_year_end_window"])
        self.assertGreater(res["volume_adjustment_factor"], 1.0)
        self.assertIn("تجميل الميزانيات", res["strategy_tweak_ar"])

    def test_04_standard_session_detection(self):
        """Verify typical Sunday/Tuesday outside special seasons returns standard cycle."""
        # 2026-08-25 is Tuesday
        res = MarketSeasonalityEngine.evaluate_current_seasonality("2026-08-25")
        self.assertEqual(res["seasonality_regime"], MarketSeasonalityEngine.REGIME_STANDARD)
        self.assertEqual(res["volume_adjustment_factor"], 1.00)


if __name__ == "__main__":
    unittest.main()
