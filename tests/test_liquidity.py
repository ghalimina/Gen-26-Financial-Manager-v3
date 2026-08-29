#!/usr/bin/env python3
# =============================================================================
# tests/test_liquidity.py — GEN-26 Dynamic Liquidity Gate Unit Tests
# =============================================================================

import unittest
import pandas as pd
import numpy as np
import sys
import os

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.liquidity_filter import LiquidityGateEngine


class TestLiquidityFilter(unittest.TestCase):

    def setUp(self):
        # Create a mock 40-day dataframe with known turnover
        dates = pd.date_range('2026-01-01', periods=40)
        # Volume = 600,000, Price = 10.0 -> Turnover = 6,000,000 EGP / day
        self.mock_liquid_df = pd.DataFrame({
            'Open': [10.0] * 40,
            'High': [10.5] * 40,
            'Low': [9.5] * 40,
            'Close': [10.0] * 40,
            'Volume': [600000.0] * 40
        }, index=dates)

        # Illiquid dataframe with 0 volume
        self.mock_illiquid_df = pd.DataFrame({
            'Open': [10.0] * 40,
            'High': [10.5] * 40,
            'Low': [9.5] * 40,
            'Close': [10.0] * 40,
            'Volume': [0.0] * 40
        }, index=dates)

    def test_liquid_stock_passes_gate(self):
        res = LiquidityGateEngine.evaluate_stock_liquidity("COMI.CA", self.mock_liquid_df)
        self.assertTrue(res["is_liquid"])
        self.assertEqual(res["status"], "TRADABLE_LIQUID")

    def test_zero_volume_stock_rejected(self):
        res = LiquidityGateEngine.evaluate_stock_liquidity("DEAD.CA", self.mock_illiquid_df)
        self.assertFalse(res["is_liquid"])
        self.assertEqual(res["status"], "ILLIQUID")

    def test_universe_filtering(self):
        sample_tickers = ["COMI.CA", "SWDY.CA", "UNKNOWN_DEAD_TICKER.CA"]
        filtered = LiquidityGateEngine.filter_universe(sample_tickers)
        self.assertIn("liquid_tickers", filtered)
        self.assertIn("liquid_count", filtered)
        self.assertGreaterEqual(filtered["liquid_count"], 2)


if __name__ == '__main__':
    unittest.main()
