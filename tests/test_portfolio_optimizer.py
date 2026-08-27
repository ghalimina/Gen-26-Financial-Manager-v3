#!/usr/bin/env python3
# =============================================================================
# tests/test_portfolio_optimizer.py — Unit Tests for HRP and Stress Testing
# Validates:
# 1. Distance matrix computation and Tree Clustering.
# 2. Quasi-Diagonalization and Recursive Bisection.
# 3. Maximum single-asset cap constraint (20% max).
# 4. Monte Carlo VaR 99% simulation and automated halt guard.
# 5. REST API endpoint GET /api/portfolio/hrp_weights.
# =============================================================================

import os
import sys
import unittest
import numpy as np

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.portfolio_optimizer import HRPOptimizer
from core.stress_testing_engine import MonteCarloStressTester
from dashboard.app import app


class TestPortfolioOptimizer(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_01_distance_matrix_properties(self):
        """Verify correlation distance matrix properties: 0 on diagonal, bounded in [0, 1]."""
        corr = np.array([
            [1.0, 0.6, 0.2],
            [0.6, 1.0, 0.4],
            [0.2, 0.4, 1.0]
        ])
        dist = HRPOptimizer.compute_distance_matrix(corr)
        self.assertEqual(dist.shape, (3, 3))
        np.testing.assert_array_almost_equal(np.diag(dist), np.zeros(3))
        self.assertTrue(np.all(dist >= 0.0))
        self.assertTrue(np.all(dist <= 1.0))

    def test_02_hrp_optimization_end_to_end(self):
        """Verify complete HRP optimization pipeline on top EGX stocks."""
        tickers = ["COMI.CA", "SWDY.CA", "TMGH.CA", "AMOC.CA", "EAST.CA"]
        res = HRPOptimizer.optimize_portfolio(tickers=tickers, max_cap=0.20)

        self.assertEqual(res["status"], "HRP_OPTIMIZED_SUCCESS")
        self.assertEqual(res["n_assets"], 5)
        self.assertIn("allocations", res)
        self.assertIn("portfolio_metrics", res)

        allocations = res["allocations"]
        total_weight = sum(a["weight_pct"] for a in allocations)
        self.assertAlmostEqual(total_weight, 100.0, delta=0.5)

        # Assert no stock exceeds 20.0% max cap
        for a in allocations:
            self.assertLessEqual(a["weight_pct"], 20.01)

    def test_03_monte_carlo_var_and_cvar_computation(self):
        """Verify Monte Carlo 10,000-path simulation computes valid VaR and CVaR."""
        res = MonteCarloStressTester.run_portfolio_monte_carlo(
            annualized_return=0.25,
            annualized_volatility=0.16,
            n_simulations=5000,
            horizon_days=30
        )

        self.assertEqual(res["status"], "MONTE_CARLO_SIMULATION_SUCCESS")
        self.assertEqual(res["n_simulations"], 5000)
        self.assertGreater(res["var_95_pct"], 0.0)
        self.assertGreater(res["var_99_pct"], res["var_95_pct"])
        self.assertGreaterEqual(res["cvar_99_pct"], res["var_99_pct"])
        self.assertIn("can_execute_orders", res)

    def test_04_monte_carlo_halt_circuit_breaker(self):
        """Verify that extreme volatility (>50%) causing VaR 99% > 12% triggers execution halt."""
        res = MonteCarloStressTester.run_portfolio_monte_carlo(
            annualized_return=-0.10,
            annualized_volatility=0.60,  # Extreme shock volatility
            n_simulations=2000,
            horizon_days=30
        )
        self.assertTrue(res["var_99_pct"] > 12.0)
        self.assertTrue(res["execution_halted"])
        self.assertFalse(res["can_execute_orders"])

    def test_05_api_hrp_weights_endpoint(self):
        """Verify REST API GET /api/portfolio/hrp_weights returns combined HRP and Risk payload."""
        response = self.app.get("/api/portfolio/hrp_weights")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("hrp_optimization", data)
        self.assertIn("hmm_regime", data)
        self.assertIn("monte_carlo_var", data)


if __name__ == "__main__":
    unittest.main()
