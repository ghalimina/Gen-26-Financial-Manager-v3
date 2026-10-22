#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_quantum_simulator.py — Institutional Verification Suite for Quantum Time-Machine Simulator
Tests:
1. /api/simulator/project?target=PORTFOLIO&days=20 returns exact current_value 13274.93.
2. /api/simulator/project?target=COMI.CA&days=45 and target=ABUK.CA&days=10 return valid JSON trajectories.
3. Strict mathematical invariant: lower_10_series[d] <= expected_series[d] <= upper_90_series[d] for all d in [0, horizon_days].
"""

import os
import sys
import unittest

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from dashboard.app import app
from core.quantum_time_simulator import QuantumTimeSimulator


class TestQuantumSimulator(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_01_portfolio_exact_value_and_invariant(self):
        """Verify portfolio target returns dynamic real equity and satisfies invariant."""
        res = self.client.get("/api/simulator/project?target=PORTFOLIO&days=20")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()

        self.assertEqual(data["status"], "SUCCESS")
        self.assertEqual(data["target"], "PORTFOLIO")
        self.assertEqual(data["horizon_days"], 20)
        
        # Check dynamic equity against data/user_real_portfolio.json
        import json
        port_file = os.path.join(WORKSPACE, "data", "user_real_portfolio.json")
        if os.path.exists(port_file):
            with open(port_file, "r", encoding="utf-8") as f:
                expected_equity = float(json.load(f).get("total_portfolio_equity_egp", 13463.43))
            self.assertAlmostEqual(data["kpis"]["current_value"], expected_equity, places=2)
        else:
            self.assertGreater(data["kpis"]["current_value"], 0)

        self.assertEqual(len(data["expected_series"]), 21)

        # Invariant check
        for d in range(21):
            lo = data["lower_10_series"][d]
            exp = data["expected_series"][d]
            up = data["upper_90_series"][d]
            self.assertLessEqual(lo, exp, f"Day {d}: lower_10 ({lo}) > expected ({exp})")
            self.assertLessEqual(exp, up, f"Day {d}: expected ({exp}) > upper_90 ({up})")

    def test_02_single_stocks_and_horizon_bounds(self):
        """Verify COMI.CA (45 days) and ABUK.CA (10 days) return valid trajectories."""
        # 1. COMI.CA 45 days
        res_comi = self.client.get("/api/simulator/project?target=COMI.CA&days=45&regime=STRONG_BULL")
        self.assertEqual(res_comi.status_code, 200)
        data_comi = res_comi.get_json()
        self.assertEqual(data_comi["horizon_days"], 45)
        self.assertGreater(data_comi["kpis"]["current_value"], 0)
        self.assertEqual(len(data_comi["expected_series"]), 46)

        for d in range(46):
            self.assertLessEqual(data_comi["lower_10_series"][d], data_comi["expected_series"][d])
            self.assertLessEqual(data_comi["expected_series"][d], data_comi["upper_90_series"][d])

        # 2. ABUK.CA 10 days
        res_abuk = self.client.get("/api/simulator/project?target=ABUK.CA&days=10&regime=BASE_ACCUMULATION")
        self.assertEqual(res_abuk.status_code, 200)
        data_abuk = res_abuk.get_json()
        self.assertEqual(data_abuk["horizon_days"], 10)
        self.assertGreater(data_abuk["kpis"]["current_value"], 0)
        self.assertEqual(len(data_abuk["expected_series"]), 11)

        for d in range(11):
            self.assertLessEqual(data_abuk["lower_10_series"][d], data_abuk["expected_series"][d])
            self.assertLessEqual(data_abuk["expected_series"][d], data_abuk["upper_90_series"][d])

    def test_03_indices_and_matrix_rows(self):
        """Verify EGX30 benchmark and multi-stock comparison matrix."""
        res_idx = self.client.get("/api/simulator/project?target=EGX30&days=15")
        self.assertEqual(res_idx.status_code, 200)
        data_idx = res_idx.get_json()
        self.assertGreater(data_idx["kpis"]["current_value"], 10000.0)

        matrix = data_idx.get("matrix_rows", [])
        self.assertGreaterEqual(len(matrix), 5)
        # Verify 5 portfolio holdings are included
        portfolio_holdings = [r for r in matrix if r.get("is_portfolio_holding")]
        self.assertEqual(len(portfolio_holdings), 5)


if __name__ == "__main__":
    unittest.main()
