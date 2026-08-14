import unittest
import pandas as pd
import numpy as np
import sys
import os

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, WORKSPACE)

import walk_forward_backtest_engine as wf

class TestBacktestEngine(unittest.TestCase):

    def setUp(self):
        # Create synthetic multi-asset price histories
        np.random.seed(42)
        dates = pd.date_range('2024-01-01', periods=150)
        self.mock_dfs = {}
        for ticker in ['COMI.CA', 'TMGH.CA', 'SWDY.CA']:
            # Upward trending series with volatility
            drift = np.linspace(100.0, 140.0, 150)
            noise = np.random.normal(0, 1.5, 150)
            closes = drift + noise
            self.mock_dfs[ticker] = pd.DataFrame({
                'Open': closes - 0.5,
                'High': closes + 2.0,
                'Low': closes - 2.0,
                'Close': closes,
                'Adj_Close': closes,
                'Volume': [50000.0] * 150
            }, index=dates)
            
        self.mock_egx30 = pd.DataFrame({
            'Close': np.linspace(25000.0, 30000.0, 150)
        }, index=dates)

    def test_walk_forward_execution_and_metrics(self):
        res = wf.run_walk_forward_simulation(
            self.mock_dfs, self.mock_egx30, 
            round_trip_cost_pct=0.90, min_hurdle_rate=2.0, use_regime_gate=True
        )
        self.assertIsNotNone(res)
        self.assertIn('total_net_return_pct', res)
        self.assertIn('cagr_pct', res)
        self.assertIn('max_drawdown_pct', res)
        self.assertIn('sharpe_ratio', res)
        self.assertIn('benchmark_egx30_buy_hold_pct', res)
        self.assertIn('alpha_vs_benchmark_pct', res)
        
        # Initial capital was 100,000 EGP
        self.assertEqual(res['initial_capital'], 100000.0)
        self.assertGreater(res['final_equity'], 0.0)

    def test_cost_friction_monotonicity(self):
        # Higher transaction costs must strictly produce lower or equal net returns
        res_zero_cost = wf.run_walk_forward_simulation(self.mock_dfs, self.mock_egx30, round_trip_cost_pct=0.0)
        res_high_cost = wf.run_walk_forward_simulation(self.mock_dfs, self.mock_egx30, round_trip_cost_pct=1.50)
        
        self.assertIsNotNone(res_zero_cost)
        self.assertIsNotNone(res_high_cost)
        self.assertGreaterEqual(res_zero_cost['total_net_return_pct'], res_high_cost['total_net_return_pct'])

if __name__ == '__main__':
    unittest.main()
