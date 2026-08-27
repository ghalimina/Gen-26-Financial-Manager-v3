#!/usr/bin/env python3
# =============================================================================
# tests/test_incubation_gate_engine.py — GEN-26 Incubation Gating Engine Tests
# Simulates Winning Graduating Scenario, Failing Drawdown Scenario, and API endpoint.
# =============================================================================

import os
import sys
import unittest
import json

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.incubation_gate_engine import IncubationGateEngine
from dashboard.app import app


class TestIncubationGateEngine(unittest.TestCase):
    """
    Test suite for the automated 30-day incubation evaluation and fail-closed circuit breaker.
    """

    def setUp(self):
        self.client = app.test_client()

    def test_01_simulated_winning_graduation_scenario(self):
        """
        Simulate a successful 30-day incubation outcome (22 trades, 72.7% win rate, Sharpe 1.85, DD 2.8%):
        Must pass all 6 gates and authorize real-money deployment at 25% scale.
        """
        # 22 closed trades: 16 wins (+5.0% avg), 6 losses (-2.0% avg)
        winning_trades = []
        for i in range(16):
            winning_trades.append({
                "ticker": f"WIN_{i}.CA",
                "pnl_pct": 5.2,
                "pnl_egp": 2600.0,
                "status": "CLOSED"
            })
        for j in range(6):
            winning_trades.append({
                "ticker": f"LOSS_{j}.CA",
                "pnl_pct": -2.1,
                "pnl_egp": -1050.0,
                "status": "CLOSED"
            })

        # Daily NAV series with steady upward drift and small drawdown (max dd ~2.5%)
        nav_series = [100000.0]
        curr = 100000.0
        for ret in [0.004, 0.003, -0.005, 0.006, 0.002, 0.005, -0.008, 0.007, 0.004, 0.003, 0.006, 0.005, -0.004, 0.008, 0.005, 0.004, 0.006, 0.003, 0.005, 0.004]:
            curr *= (1.0 + ret)
            nav_series.append(curr)

        verdict = IncubationGateEngine.evaluate_incubation_state(
            custom_trades=winning_trades,
            custom_daily_nav=nav_series,
            benchmark_egx30_return_pct=2.00,
            evaluation_date="2026-09-22"
        )

        self.assertEqual(verdict["verdict_status"], IncubationGateEngine.STATUS_GRADUATED)
        self.assertTrue(verdict["all_gates_passed"])
        self.assertTrue(verdict["real_money_authorized"])
        self.assertEqual(verdict["authorized_capital_scale_pct"], 25.0)
        self.assertEqual(verdict["active_model_policy"], IncubationGateEngine.PROD_MODEL_MULTI_HORIZON)
        self.assertEqual(verdict["failed_gates_count"], 0)

        # Check all 6 gates passed
        matrix = verdict["gating_matrix"]
        self.assertTrue(matrix["gate_1_sharpe_ratio"]["passed"])
        self.assertTrue(matrix["gate_2_cumulative_alpha"]["passed"])
        self.assertTrue(matrix["gate_3_max_drawdown"]["passed"])
        self.assertTrue(matrix["gate_4_win_rate"]["passed"])
        self.assertTrue(matrix["gate_5_profit_factor"]["passed"])
        self.assertTrue(matrix["gate_6_sample_size"]["passed"])

    def test_02_simulated_failing_drawdown_scenario(self):
        """
        Simulate a failing incubation outcome (25 trades, Drawdown = 9.5% > 6.5% limit, Win Rate = 36%):
        Must trigger FROZEN_FAIL_CLOSED and fallback to 100% Cash / Tier-1 baseline.
        """
        # 25 closed trades: 9 wins (+2.0%), 16 losses (-3.5%)
        failing_trades = []
        for i in range(9):
            failing_trades.append({
                "ticker": f"WIN_{i}.CA",
                "pnl_pct": 2.0,
                "pnl_egp": 1000.0,
                "status": "CLOSED"
            })
        for j in range(16):
            failing_trades.append({
                "ticker": f"LOSS_{j}.CA",
                "pnl_pct": -3.5,
                "pnl_egp": -1750.0,
                "status": "CLOSED"
            })

        # Declining NAV series with -9.8% drawdown
        nav_series = [100000.0, 98000.0, 96500.0, 94000.0, 91500.0, 90200.0, 92000.0, 91000.0]

        verdict = IncubationGateEngine.evaluate_incubation_state(
            custom_trades=failing_trades,
            custom_daily_nav=nav_series,
            benchmark_egx30_return_pct=4.00,
            evaluation_date="2026-09-22"
        )

        self.assertEqual(verdict["verdict_status"], IncubationGateEngine.STATUS_FAIL_CLOSED)
        self.assertFalse(verdict["all_gates_passed"])
        self.assertFalse(verdict["real_money_authorized"])
        self.assertEqual(verdict["authorized_capital_scale_pct"], 0.0)
        self.assertEqual(verdict["active_model_policy"], IncubationGateEngine.FALLBACK_MODEL_TIER1)
        self.assertGreater(verdict["failed_gates_count"], 0)
        self.assertFalse(verdict["gating_matrix"]["gate_3_max_drawdown"]["passed"])

    def test_03_statistical_bootstrap_confidence_and_caveat(self):
        """Verify Bootstrap 95% CI calculation and N < 100 caveat warning."""
        trades = [{"pnl_pct": 2.5, "pnl_egp": 1250.0} for _ in range(25)]
        navs = [100000.0, 102000.0, 103500.0, 105000.0]

        verdict = IncubationGateEngine.evaluate_incubation_state(
            custom_trades=trades,
            custom_daily_nav=navs
        )

        stat = verdict["statistical_validation"]
        self.assertIn("confidence_score_pct", stat)
        self.assertIn("bootstrap_95_ci_pct", stat)
        self.assertIn("lower", stat["bootstrap_95_ci_pct"])
        self.assertIn("upper", stat["bootstrap_95_ci_pct"])
        self.assertLessEqual(stat["bootstrap_95_ci_pct"]["lower"], stat["bootstrap_95_ci_pct"]["upper"])

        # N=25 < 100 caveat check
        self.assertGreater(len(stat["statistical_caveats"]), 0)
        self.assertIn("PRELIMINARY_SAMPLE_SIZE_WARNING", stat["statistical_caveats"][0])

    def test_04_api_incubation_verdict_endpoint(self):
        """Verify GET /api/incubation/verdict returns HTTP 200 and valid JSON."""
        res = self.client.get("/api/incubation/verdict")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("verdict_status", data)
        self.assertIn("gating_matrix", data)
        self.assertIn("statistical_validation", data)


if __name__ == "__main__":
    unittest.main()
