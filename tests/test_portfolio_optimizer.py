#!/usr/bin/env python3
# =============================================================================
# tests/test_portfolio_optimizer.py — Unit Tests for Portfolio Optimizer & HRP
# Validates:
# 1. Distance matrix computation and Tree Clustering.
# 2. Quasi-Diagonalization and Recursive Bisection.
# 3. Maximum single-asset cap constraint (20% HRP max).
# 4. Monte Carlo VaR 99% simulation and automated halt guard.
# 5. REST API endpoint GET /api/portfolio/hrp_weights.
# 6. PortfolioOptimizer Inverse Volatility Risk Parity weighting.
# 7. PortfolioOptimizer Strict 30% Maximum Position Cap constraint.
# 8. PortfolioOptimizer Capital Allocation & Integer Share Lot Sizing in EGP.
# 9. PortfolioOptimizer Edge Case Resilience (zero volatility, missing prices).
# =============================================================================

import os
import sys
import unittest
import numpy as np

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.portfolio_optimizer import PortfolioOptimizer, HRPOptimizer
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

    def test_06_portfolio_optimizer_inverse_volatility_weighting(self):
        """Verify Inverse Volatility assigns higher weights to lower volatility stocks."""
        tickers = ["STOCK_A.CA", "STOCK_B.CA", "STOCK_C.CA", "STOCK_D.CA", "STOCK_E.CA"]
        volatilities = {
            "STOCK_A.CA": 0.18,
            "STOCK_B.CA": 0.22,
            "STOCK_C.CA": 0.26,
            "STOCK_D.CA": 0.32,
            "STOCK_E.CA": 0.40
        }
        weights = PortfolioOptimizer.calculate_optimal_weights(tickers, volatility_dict=volatilities)

        self.assertEqual(len(weights), 5)
        self.assertGreater(weights["STOCK_A.CA"], weights["STOCK_B.CA"])
        self.assertGreater(weights["STOCK_B.CA"], weights["STOCK_C.CA"])
        self.assertGreater(weights["STOCK_C.CA"], weights["STOCK_D.CA"])
        self.assertGreater(weights["STOCK_D.CA"], weights["STOCK_E.CA"])
        self.assertAlmostEqual(sum(weights.values()), 1.0, places=3)

    def test_07_strict_30pct_max_position_cap(self):
        """Verify no single stock ever exceeds the 30% (0.30) regulatory position limit."""
        tickers = ["SAFE_STOCK.CA", "RISKY_1.CA", "RISKY_2.CA", "RISKY_3.CA", "RISKY_4.CA"]
        # Ultra-low volatility for SAFE_STOCK would normally dominate >60% of portfolio
        volatilities = {
            "SAFE_STOCK.CA": 0.05,
            "RISKY_1.CA": 0.60,
            "RISKY_2.CA": 0.70,
            "RISKY_3.CA": 0.80,
            "RISKY_4.CA": 0.90
        }
        weights = PortfolioOptimizer.calculate_optimal_weights(tickers, volatility_dict=volatilities)

        for ticker, weight in weights.items():
            self.assertLessEqual(weight, 0.3001, f"{ticker} weight {weight} exceeded 30% cap!")

        self.assertAlmostEqual(sum(weights.values()), 1.0, places=3)

    def test_08_capital_allocation_and_lot_sizing(self):
        """Verify capital allocation properly computes integer share lots and cash reserves in EGP."""
        weights = {
            "COMI.CA": 0.30,
            "SWDY.CA": 0.25,
            "TMGH.CA": 0.25,
            "ORAS.CA": 0.20
        }
        prices = {
            "COMI.CA": 140.0,
            "SWDY.CA": 125.0,
            "TMGH.CA": 60.0,
            "ORAS.CA": 300.0
        }
        capital_egp = 100000.0  # 100,000 EGP

        alloc = PortfolioOptimizer.allocate_capital(capital_egp, weights, prices)

        self.assertEqual(alloc["status"], "CAPITAL_ALLOCATION_SUCCESS")
        self.assertEqual(alloc["total_capital_egp"], 100000.0)
        self.assertGreater(alloc["total_allocated_egp"], 95000.0)
        self.assertGreaterEqual(alloc["remaining_cash_egp"], 0.0)

        # Shares must be exact positive integers
        for t, d in alloc["allocations"].items():
            self.assertIsInstance(d["shares_to_buy"], int)
            self.assertGreater(d["shares_to_buy"], 0)
            self.assertAlmostEqual(d["actual_amount_egp"], d["shares_to_buy"] * prices[t], places=2)

    def test_09_edge_cases_zero_volatility_and_missing_prices(self):
        """Verify robust handling of zero/missing volatilities and missing prices without crashes."""
        tickers = ["ZERO_VOL.CA", "MISSING_VOL.CA", "NORMAL_VOL.CA", "FOURTH.CA"]
        volatilities = {
            "ZERO_VOL.CA": 0.0,  # Zero volatility edge case
            "NORMAL_VOL.CA": 0.25
            # MISSING_VOL.CA and FOURTH.CA omitted
        }
        weights = PortfolioOptimizer.calculate_optimal_weights(tickers, volatility_dict=volatilities)
        self.assertEqual(len(weights), 4)
        for w in weights.values():
            self.assertGreater(w, 0.0)
            self.assertLessEqual(w, 0.3001)

        # Missing price in allocation
        prices = {
            "ZERO_VOL.CA": 50.0,
            "NORMAL_VOL.CA": 0.0  # Invalid 0 price
            # Others missing
        }
        alloc = PortfolioOptimizer.allocate_capital(50000.0, weights, prices)
        self.assertEqual(alloc["status"], "CAPITAL_ALLOCATION_SUCCESS")
        self.assertEqual(alloc["allocations"]["NORMAL_VOL.CA"]["shares_to_buy"], 0)
        self.assertEqual(alloc["allocations"]["NORMAL_VOL.CA"]["status"], "SKIPPED_MISSING_PRICE")


if __name__ == "__main__":
    unittest.main()
