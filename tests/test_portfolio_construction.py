#!/usr/bin/env python3
# =============================================================================
# tests/test_portfolio_construction.py — GEN-26 Portfolio Construction Tests
# Validates Institutional Portfolio Constructor, Correlation Penalties,
# and Paper-vs-Backtest divergence evaluations.
# =============================================================================

import unittest
import os
import sys
import pandas as pd
import numpy as np

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.portfolio_constructor import InstitutionalPortfolioConstructor
from core.portfolio_risk import PortfolioRiskEngine
from core.paper_vs_backtest import PaperVsBacktestComparator
from core.frozen_invariants import FrozenRiskInvariants


class TestPortfolioConstruction(unittest.TestCase):

    def test_01_portfolio_allocation_plan_and_solvency(self):
        """
        Verify that portfolio constructor generates valid allocation plan:
        - Strict 65% stock ceiling
        - 35% cash buffer
        - 10% maximum per stock
        """
        total_equity = 100_000.0
        free_cash = 100_000.0

        ranked_candidates = [
            {"ticker": "COMI.CA", "entry_price": 100.0, "current_price": 102.0, "stop_price": 93.0, "adv_20d_egp": 80_000_000, "alpha_score": 90.0},
            {"ticker": "SWDY.CA", "entry_price": 40.0, "current_price": 41.0, "stop_price": 37.2, "adv_20d_egp": 50_000_000, "alpha_score": 85.0},
            {"ticker": "TMGH.CA", "entry_price": 50.0, "current_price": 51.5, "stop_price": 46.5, "adv_20d_egp": 40_000_000, "alpha_score": 82.0},
            {"ticker": "EKHO.CA", "entry_price": 20.0, "current_price": 20.5, "stop_price": 18.6, "adv_20d_egp": 30_000_000, "alpha_score": 78.0},
            {"ticker": "ETEL.CA", "entry_price": 30.0, "current_price": 31.0, "stop_price": 27.9, "adv_20d_egp": 25_000_000, "alpha_score": 75.0},
            {"ticker": "ABUK.CA", "entry_price": 60.0, "current_price": 62.0, "stop_price": 55.8, "adv_20d_egp": 20_000_000, "alpha_score": 72.0},
            {"ticker": "MFPC.CA", "entry_price": 80.0, "current_price": 82.0, "stop_price": 74.4, "adv_20d_egp": 20_000_000, "alpha_score": 70.0},
            {"ticker": "HELI.CA", "entry_price": 15.0, "current_price": 15.5, "stop_price": 13.95, "adv_20d_egp": 15_000_000, "alpha_score": 68.0}
        ]

        sector_mapping = {
            "COMI.CA": "Banking",
            "SWDY.CA": "Industrial",
            "TMGH.CA": "Real Estate",
            "EKHO.CA": "Financial Services",
            "ETEL.CA": "Telecom",
            "ABUK.CA": "Fertilizers",
            "MFPC.CA": "Fertilizers",
            "HELI.CA": "Real Estate"
        }

        plan = InstitutionalPortfolioConstructor.construct_target_portfolio(
            ranked_candidates=ranked_candidates,
            total_portfolio_equity=total_equity,
            available_free_cash=free_cash,
            existing_positions={},
            sector_mapping=sector_mapping
        )

        self.assertTrue(plan["is_plan_valid"])
        self.assertLessEqual(plan["allocated_cash"], 65_000.0) # Cannot exceed 65,000 EGP
        self.assertGreaterEqual(plan["remaining_free_cash"], 35_000.0) # Must keep >= 35,000 EGP

        # Check individual order weights
        for order in plan["allocated_orders"]:
            self.assertLessEqual(order["target_weight_pct"], 10.0 + 1e-3) # <= 10%
            self.assertGreater(order["target_shares"], 0)

    def test_02_correlation_and_sector_penalty(self):
        """
        Verify that adding a second asset in the same sector receives a concentration penalty.
        """
        existing_allocations = {"ABUK.CA": 0.10} # 10% allocated in Fertilizers
        sector_mapping = {"ABUK.CA": "Fertilizers", "MFPC.CA": "Fertilizers"}

        penalty_res = PortfolioRiskEngine.calculate_correlation_penalty(
            target_ticker="MFPC.CA",
            target_sector="Fertilizers",
            existing_allocations=existing_allocations,
            sector_mapping=sector_mapping
        )

        self.assertLess(penalty_res["penalty_multiplier"], 1.0)
        self.assertIn("SECTOR_EXPOSURE_MODERATE", penalty_res["reason_codes"])

    def test_03_paper_vs_backtest_divergence(self):
        """
        Verify PaperVsBacktestComparator flags severe divergence when win rate collapses.
        """
        # Scenario A: Healthy alignment
        comp_healthy = PaperVsBacktestComparator.evaluate_divergence(
            paper_trades_count=10,
            paper_win_rate_pct=58.0,
            paper_profit_factor=2.20,
            paper_mean_net_return_pct=3.00,
            paper_realized_slippage_pct=0.10
        )
        self.assertTrue(comp_healthy["is_divergence_normal"])
        self.assertEqual(comp_healthy["status"], "HEALTHY_ALIGNMENT")

        # Scenario B: Severe degradation
        comp_bad = PaperVsBacktestComparator.evaluate_divergence(
            paper_trades_count=10,
            paper_win_rate_pct=35.0, # 21% below benchmark!
            paper_profit_factor=0.90,
            paper_mean_net_return_pct=-1.50,
            paper_realized_slippage_pct=0.35
        )
        self.assertFalse(comp_bad["is_divergence_normal"])
        self.assertEqual(comp_bad["status"], "DIVERGENCE_WARNING")
        self.assertIn("WIN_RATE_SEVERE_UNDERPERFORMANCE", comp_bad["warnings"])


if __name__ == "__main__":
    unittest.main()
