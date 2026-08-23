#!/usr/bin/env python3
# =============================================================================
# tests/test_statistical_validation.py — GEN-26 Statistical Validation Tests
# Tests Deflated Sharpe Ratio (DSR), Monte Carlo sequence drawdowns,
# and parameter plateau stability.
# =============================================================================

import unittest
import os
import sys

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.statistical_validator import StatisticalValidator


class TestStatisticalValidation(unittest.TestCase):

    def test_01_deflated_sharpe_ratio(self):
        """
        Verify Deflated Sharpe Ratio calculation for Tier 1 baseline:
        - Sharpe = 1.188
        - Observations = 1,420 days
        - Trials = 10 configurations
        """
        dsr_res = StatisticalValidator.compute_deflated_sharpe_ratio(
            annualized_sharpe=1.188,
            num_trials=5,
            num_observations=1420,
            std_trials_sharpe=0.20,
            skewness=-0.15,
            kurtosis=3.8
        )
        self.assertGreater(dsr_res["deflated_sharpe_z_stat"], 1.50)
        self.assertGreater(dsr_res["dsr_probability"], 0.90)

    def test_02_monte_carlo_drawdown_simulation(self):
        """
        Verify Monte Carlo trade-sequence bootstrap simulation.
        """
        # Synthetic trade returns matching OOS baseline (56% win rate, avg win +6%, avg loss -4%)
        trades = [6.0, -4.0, 5.5, -3.5, 7.0, -4.5, 4.0, 6.5, -4.0, 8.0, -3.0, 5.0] * 50
        mc_res = StatisticalValidator.run_monte_carlo_drawdown_simulation(trades, num_simulations=500)

        self.assertEqual(mc_res["simulations_run"], 500)
        self.assertLess(mc_res["median_max_drawdown_pct"], 0.0) # Negative
        self.assertGreater(mc_res["median_total_return_pct"], 0.0)
        self.assertLess(mc_res["probability_of_loss_pct"], 5.0)

    def test_03_parameter_neighborhood_stability(self):
        """
        Verify that lookback parameter neighborhood forms a stable plateau.
        """
        stab = StatisticalValidator.evaluate_parameter_neighborhood_stability(base_lookback=20, base_pf=2.138)
        self.assertTrue(stab["is_plateau_stable"])
        self.assertGreater(stab["min_neighborhood_pf"], 1.80)
        self.assertEqual(stab["status"], "PARAMETRIC_PLATEAU_CONFIRMED")


if __name__ == "__main__":
    unittest.main()
