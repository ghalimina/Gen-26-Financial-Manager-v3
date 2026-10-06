#!/usr/bin/env python3
# =============================================================================
# tests/test_model_evaluator.py — Unit Tests for GEN-26 Out-Of-Sample Model Evaluator
# Validates mathematical computation of Information Coefficient (Spearman Rank IC),
# Directional Hit Rate, RMSE, and rolling walk-forward Out-of-Sample metrics.
# =============================================================================

import os
import sys
import unittest
import numpy as np

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.model_evaluator import WalkForwardValidator
from dashboard.app import app


class TestModelEvaluator(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_01_information_coefficient_perfect_positive(self):
        """Verify Spearman Rank IC equals 1.0 for monotonic rank alignment."""
        y_pred = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y_true = np.array([0.5, 1.5, 2.8, 3.9, 6.2])
        ic = WalkForwardValidator.calculate_information_coefficient(y_pred, y_true)
        self.assertAlmostEqual(ic, 1.0, places=2)

    def test_02_information_coefficient_inverse_negative(self):
        """Verify Spearman Rank IC equals -1.0 for perfectly inverted ranking."""
        y_pred = np.array([5.0, 4.0, 3.0, 2.0, 1.0])
        y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        ic = WalkForwardValidator.calculate_information_coefficient(y_pred, y_true)
        self.assertAlmostEqual(ic, -1.0, places=2)

    def test_03_hit_rate_directional_accuracy(self):
        """Verify hit rate computes exact directional sign percentage."""
        y_pred = np.array([+2.0, +1.5, -3.0, +4.0, -1.0])
        y_true = np.array([+1.0, +0.5, -2.0, -1.0, -0.5])  # 4 out of 5 match signs
        hit_rate = WalkForwardValidator.calculate_hit_rate(y_pred, y_true)
        self.assertEqual(hit_rate, 80.0)

    def test_04_rmse_calculation(self):
        """Verify RMSE calculation against ground truth values."""
        y_pred = np.array([1.0, 2.0, 3.0])
        y_true = np.array([1.0, 2.0, 3.0])
        self.assertEqual(WalkForwardValidator.calculate_rmse(y_pred, y_true), 0.0)

        y_pred2 = np.array([2.0, 4.0])
        y_true2 = np.array([0.0, 0.0])  # diffs = 2, 4 -> mean square = (4+16)/2 = 10 -> sqrt(10) = 3.162
        self.assertAlmostEqual(WalkForwardValidator.calculate_rmse(y_pred2, y_true2), 3.162, places=2)

    def test_05_walk_forward_simulation_oos_integrity(self):
        """Verify Out-of-Sample Walk-Forward Simulation produces robust empirical metrics."""
        metrics = WalkForwardValidator.run_walk_forward_simulation()
        self.assertEqual(metrics["status"], "VALIDATED_OUT_OF_SAMPLE")
        self.assertGreater(metrics["n_oos_samples"], 20)
        self.assertIn("information_coefficient", metrics)
        self.assertIn("hit_rate_pct", metrics)
        self.assertIn("rmse_pct", metrics)
        self.assertIsInstance(metrics["information_coefficient"], float)
        self.assertIsInstance(metrics["hit_rate_pct"], float)
        self.assertIn("ic_target_met", metrics)
        self.assertIn("hit_rate_target_met", metrics)

    def test_06_api_ai_validation_metrics_endpoint(self):
        """Verify GET /api/ai/validation_metrics returns HTTP 200 with complete metrics payload."""
        response = self.app.get("/api/ai/validation_metrics")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "VALIDATED_OUT_OF_SAMPLE")
        self.assertIn("information_coefficient", data)
        self.assertIn("hit_rate_pct", data)
        self.assertIn("rmse_pct", data)

    def test_07_triple_barrier_label(self):
        """Verify Triple Barrier label correctly detects upper barrier, lower barrier, and timeout."""
        from core.model_evaluator import compute_triple_barrier_label
        
        # Upper barrier (+5%): 100 -> 106 (+6%)
        prices_up = [100.0, 102.0, 106.0, 101.0]
        self.assertEqual(compute_triple_barrier_label(prices_up, 0, target_pct=0.05, stop_pct=0.03, max_days=10), 1)

        # Lower barrier (-3%): 100 -> 96 (-4%)
        prices_down = [100.0, 98.0, 96.0, 95.0]
        self.assertEqual(compute_triple_barrier_label(prices_down, 0, target_pct=0.05, stop_pct=0.03, max_days=10), -1)

        # Timeout (horizontal): price moves sideways within bounds for max_days
        prices_flat = [100.0, 101.0, 101.5, 100.5]
        self.assertEqual(compute_triple_barrier_label(prices_flat, 0, target_pct=0.05, stop_pct=0.03, max_days=3), 0)

    def test_08_brier_score_calibration(self):
        """Verify Brier Score computation on perfect, random, and inverse probabilities."""
        # Perfect probabilities
        y_prob_perf = np.array([1.0, 0.0, 1.0, 0.0])
        y_true_perf = np.array([1, 0, 1, 0])
        self.assertAlmostEqual(WalkForwardValidator.calculate_brier_score(y_prob_perf, y_true_perf), 0.0, places=3)

        # Uninformative 50% coin flip
        y_prob_coin = np.array([0.5, 0.5, 0.5, 0.5])
        self.assertAlmostEqual(WalkForwardValidator.calculate_brier_score(y_prob_coin, y_true_perf), 0.25, places=3)

        # Inverse probabilities (worst case)
        y_prob_inv = np.array([0.0, 1.0, 0.0, 1.0])
        self.assertAlmostEqual(WalkForwardValidator.calculate_brier_score(y_prob_inv, y_true_perf), 1.0, places=3)

    def test_09_expected_calibration_error_decile_bins(self):
        """Verify Expected Calibration Error (ECE) partitions across 10 deciles and returns reliability diagram."""
        # 100 samples with perfect calibration
        np.random.seed(42)
        y_prob = np.linspace(0.05, 0.95, 100)
        y_true = (np.random.rand(100) < y_prob).astype(int)

        ece_res = WalkForwardValidator.calculate_expected_calibration_error(y_prob, y_true, n_bins=10)
        self.assertIn("ece", ece_res)
        self.assertIn("mce", ece_res)
        self.assertIn("reliability_bins", ece_res)
        self.assertEqual(len(ece_res["reliability_bins"]), 10)
        self.assertLessEqual(ece_res["ece"], 0.15)

        # Check bin structure
        first_bin = ece_res["reliability_bins"][0]
        self.assertEqual(first_bin["bin_index"], 1)
        self.assertIn("bin_range", first_bin)
        self.assertIn("confidence", first_bin)
        self.assertIn("accuracy", first_bin)
        self.assertIn("sample_count", first_bin)

    def test_10_calibrated_triad_disentanglement(self):
        """Verify triad mathematically decouples P(Up) in [0, 1], E[R] expectation, and 90% Conformal Interval."""
        p_up = 0.70
        r_up = +6.0
        r_down = -4.0
        q10 = -2.1
        q90 = +8.4

        triad = WalkForwardValidator.calculate_calibrated_triad(
            p_up=p_up,
            r_up_mean=r_up,
            r_down_mean=r_down,
            q10_downside_pct=q10,
            q90_upside_pct=q90
        )

        self.assertEqual(triad["p_up"], 0.70)
        self.assertEqual(triad["p_down"], 0.30)
        # Expected return: 0.70 * 6.0 + 0.30 * (-4.0) = 4.2 - 1.2 = 3.0
        self.assertAlmostEqual(triad["expected_return_pct"], 3.0, places=2)
        self.assertEqual(triad["conformal_interval_90"]["lower_bound_pct"], -2.1)
        self.assertEqual(triad["conformal_interval_90"]["upper_bound_pct"], +8.4)
        self.assertIn("formula_str", triad)

    def test_11_insufficient_real_data_aborts_walkforward(self):
        """Verify walk-forward evaluation strictly aborts when empirical samples < 30."""
        import pandas as pd
        small_df = pd.DataFrame({
            "residual_alpha_10d": [0.1, 0.2, -0.1]
        })
        with self.assertRaises(ValueError) as ctx:
            WalkForwardValidator.run_walk_forward_simulation(dataset=small_df)
        self.assertIn("EVALUATION_FAILED_INSUFFICIENT_DATA", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
