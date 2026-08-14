import unittest
import pandas as pd
import numpy as np
import sys
import os

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, WORKSPACE)

import app

class TestLiquidityFilter(unittest.TestCase):

    def setUp(self):
        # Create a mock 40-day dataframe with known turnover
        dates = pd.date_range('2026-01-01', periods=40)
        # Volume = 10,000, Price = 10.0 -> Turnover = 100,000 EGP / day
        self.mock_df = pd.DataFrame({
            'Close': [10.0] * 40,
            'Volume': [10000.0] * 40
        }, index=dates)

    def test_market_impact_normal_portfolio(self):
        # Capital = 20,000 EGP, allocation = 10% -> Order = 2,000 EGP
        # Turnover = 100,000 EGP -> Impact = 2% (below 8% limit) -> OK
        flag, reason, adj_alloc = app.compute_liquidity_flag('TEST.CA', self.mock_df, 0.10, capital=20000.0)
        self.assertEqual(flag, 'OK')
        self.assertEqual(adj_alloc, 0.10)
        self.assertIn("مقبول", reason)

    def test_market_impact_large_portfolio_reduction(self):
        # Capital = 500,000 EGP, allocation = 10% -> Order = 50,000 EGP
        # Turnover = 100,000 EGP -> Impact = 50% (> 8% limit) -> REDUCE
        flag, reason, adj_alloc = app.compute_liquidity_flag('TEST.CA', self.mock_df, 0.10, capital=500000.0)
        self.assertEqual(flag, 'REDUCE')
        # Max allowed = 100,000 * 0.08 / 500,000 = 0.016 (1.6%)
        self.assertAlmostEqual(adj_alloc, 0.016, places=3)
        self.assertIn("خُفِّض التخصيص", reason)

    def test_etf_stricter_threshold(self):
        # ETF ticker: EGX30ETF.CA -> max limit is 5% instead of 8%
        # Capital = 100,000 EGP, allocation = 10% -> Order = 10,000 EGP
        # Turnover = 100,000 EGP -> Impact = 10% (> 5% ETF limit) -> REDUCE
        flag, reason, adj_alloc = app.compute_liquidity_flag('EGX30ETF.CA', self.mock_df, 0.10, capital=100000.0)
        self.assertEqual(flag, 'REDUCE')
        self.assertAlmostEqual(adj_alloc, 0.05, places=3)
        self.assertIn("صندوق مؤشر", reason)

    def test_zero_volume_rejection(self):
        zero_df = pd.DataFrame({'Close': [10.0]*40, 'Volume': [0.0]*40}, index=pd.date_range('2026-01-01', periods=40))
        flag, reason, adj_alloc = app.compute_liquidity_flag('DEAD.CA', zero_df, 0.05, capital=20000.0)
        self.assertEqual(flag, 'REJECT')
        self.assertEqual(adj_alloc, 0.0)

if __name__ == '__main__':
    unittest.main()
