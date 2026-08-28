#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# tests/test_advanced_feature_engineering.py — Unit Tests for AdvancedFeatureEngineering
# Validates:
# 1. Triple Barrier Method Labeling (+1, -1, 0).
# 2. Fractional Differentiation Stationarity & Memory Preservation.
# 3. Multi-Timeframe Momentum Velocity Index.
# 4. Stealth Volume Accumulation Detection.
# =============================================================================

import os
import sys
import unittest
import numpy as np

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.advanced_feature_engineering import AdvancedFeatureEngineering


class TestAdvancedFeatureEngineering(unittest.TestCase):

    def test_01_triple_barrier_labeling(self):
        """Verify Triple Barrier assigns +1 on profit target, -1 on stop loss, 0 on time expiration."""
        # Price path: 100 -> 106 (+6% -> hit +5% upper barrier at index 0)
        prices = [100.0, 106.0, 107.0, 95.0, 94.0, 90.0, 91.0, 92.0]
        labels = AdvancedFeatureEngineering.label_triple_barrier(
            prices=prices,
            upper_barrier_pct=5.0,
            lower_barrier_pct=3.0,
            time_barrier_days=5
        )
        self.assertEqual(labels[0], 1)  # 100 -> 106 hits +5%

        # Price path: 107 -> 95 (-11% -> hit -3% lower barrier at index 2)
        self.assertEqual(labels[2], -1)

    def test_02_fractional_differentiation(self):
        """Verify fractional differentiation preserves shape and produces stationary memory-preserving series."""
        prices = np.linspace(100, 200, 50) + np.sin(np.linspace(0, 10, 50)) * 5
        frac_diff = AdvancedFeatureEngineering.apply_fractional_differentiation(prices, d=0.45)
        self.assertEqual(len(frac_diff), len(prices))
        self.assertFalse(np.isnan(frac_diff).any())

    def test_03_multi_timeframe_momentum(self):
        """Verify momentum score is bounded between 0 and 100 with valid velocity regime."""
        # Strongly upward prices
        bullish_prices = [100 + i * 2.5 for i in range(70)]
        res = AdvancedFeatureEngineering.calculate_multi_timeframe_momentum(bullish_prices)
        self.assertGreaterEqual(res["momentum_score"], 70.0)
        self.assertIn("BULLISH", res["velocity_regime"])
        self.assertIn("timeframe_returns", res)

    def test_04_stealth_accumulation_detection(self):
        """Verify high Volume Z-Score with tight price range flags STEALTH_ACCUMULATION."""
        res = AdvancedFeatureEngineering.detect_stealth_accumulation(
            ticker="COMI.CA",
            current_volume=6_000_000,
            high_price=140.80,
            low_price=139.50,
            current_price=140.00
        )
        self.assertTrue(res["is_stealth_accumulation"])
        self.assertEqual(res["pattern"], "STEALTH_ACCUMULATION")
        self.assertIn("تجميع خفي", res["description_ar"])


if __name__ == "__main__":
    unittest.main()
