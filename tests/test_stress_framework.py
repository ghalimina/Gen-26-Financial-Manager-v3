#!/usr/bin/env python3
# =============================================================================
# tests/test_stress_framework.py — GEN-26 Stress Testing Framework Unit Tests
# Validates market gap-downs, liquidity collapses, and invariant resilience.
# =============================================================================

import unittest
import os
import sys

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.stress_testing import PortfolioStressEngine
from core.frozen_invariants import FrozenRiskInvariants


class TestStressFramework(unittest.TestCase):

    def test_01_market_gap_shock_resilience(self):
        """
        Verify portfolio response to -15% market gap-down:
        - Cash solvency intact (no negative balance)
        - Stock allocation remains <= 65%
        - Hard stop breaches detected
        """
        positions = {
            "COMI.CA": {"shares": 200, "current_price": 100.0, "entry_price": 100.0, "stop_price": 93.0},
            "SWDY.CA": {"shares": 500, "current_price": 40.0, "entry_price": 40.0, "stop_price": 37.2}
        }
        initial_equity = 100_000.0
        cash = 60_000.0 # 60% cash, 40% stock

        res = PortfolioStressEngine.simulate_market_gap_shock(
            current_portfolio_equity=initial_equity,
            current_cash=cash,
            positions=positions,
            market_gap_pct=-0.15 # -15% gap
        )

        self.assertEqual(res["status"], "PASS")
        self.assertTrue(res["cash_solvency_intact"])
        self.assertTrue(res["allocation_cap_intact"])
        self.assertLess(res["drawdown_pct"], 0.0)

        # Both positions should trigger stops under -15% gap
        for pos in res["stressed_positions"]:
            self.assertTrue(pos["stop_triggered"])

    def test_02_liquidity_collapse_downscaling(self):
        """
        Verify that 80% volume collapse properly triggers position downscaling.
        """
        res = PortfolioStressEngine.simulate_liquidity_collapse(
            order_shares=2000,
            entry_price=50.0, # 100,000 EGP order value
            normal_adv_20d_egp=10_000_000,
            liquidity_drop_factor=0.80 # Drops to 2,000,000 EGP ADV
        )

        # Stressed max safe value = 5% of 2,000,000 = 100,000 EGP
        self.assertEqual(res["stressed_adv_egp"], 2_000_000.0)
        self.assertEqual(res["max_safe_value_egp"], 100_000.0)
        self.assertTrue(res["can_execute_safely"])

        # Test extreme order exceeding capacity under stress
        res_overflow = PortfolioStressEngine.simulate_liquidity_collapse(
            order_shares=5000, # 250,000 EGP order value
            entry_price=50.0,
            normal_adv_20d_egp=10_000_000,
            liquidity_drop_factor=0.80
        )
        self.assertFalse(res_overflow["can_execute_safely"])
        self.assertEqual(res_overflow["action"], "DOWNSCALE_POSITION_TO_SAFE_CAPACITY")
        self.assertEqual(res_overflow["recommended_shares_under_stress"], 2000)

    def test_03_frozen_invariants_verification_methods(self):
        """
        Directly test FrozenRiskInvariants verification helper methods.
        """
        # Solvency
        self.assertTrue(FrozenRiskInvariants.verify_cash_solvency(50_000, 60_000))
        self.assertFalse(FrozenRiskInvariants.verify_cash_solvency(70_000, 60_000))

        # Allocation Ceiling
        self.assertTrue(FrozenRiskInvariants.verify_stock_allocation_ceiling(60_000, 100_000)) # 60% <= 65%
        self.assertFalse(FrozenRiskInvariants.verify_stock_allocation_ceiling(70_000, 100_000)) # 70% > 65%

        # Pullback Invariant
        self.assertTrue(FrozenRiskInvariants.verify_pullback_invariant(95.0, 100.0))
        self.assertFalse(FrozenRiskInvariants.verify_pullback_invariant(105.0, 100.0))

        # Circuit Breaker
        self.assertTrue(FrozenRiskInvariants.verify_egx_circuit_breaker(105.0, 100.0, "BUY")) # +5% OK
        self.assertFalse(FrozenRiskInvariants.verify_egx_circuit_breaker(120.0, 100.0, "BUY")) # +20% Blocked Limit Up


if __name__ == "__main__":
    unittest.main()
