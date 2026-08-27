#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# tests/test_walk_forward_ml_engine.py — Unit Tests for WalkForwardMLEngine
# =============================================================================

import unittest
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.walk_forward_ml_engine import WalkForwardMLEngine


class TestWalkForwardMLEngine(unittest.TestCase):

    def setUp(self):
        # Reset cache for clean test runs
        WalkForwardMLEngine._cached_calibration = None
        WalkForwardMLEngine._last_calibration_time = 0.0

    def test_01_default_base_weights_conservation(self):
        """Verify baseline default engine weights sum to exactly 1.0."""
        base = WalkForwardMLEngine.DEFAULT_BASE_WEIGHTS
        self.assertIn("fundamental", base)
        self.assertIn("insider", base)
        self.assertIn("alternative", base)
        self.assertIn("sentiment", base)
        self.assertAlmostEqual(sum(base.values()), 1.0, places=4)

    def test_02_simulate_historical_accuracy_structure(self):
        """Verify simulated rolling accuracy outputs valid percentages."""
        acc = WalkForwardMLEngine.simulate_historical_accuracy(force_refresh=True)
        self.assertIsInstance(acc, dict)
        for key in ["fundamental", "insider", "alternative", "sentiment"]:
            self.assertIn(key, acc)
            self.assertGreaterEqual(acc[key], 0.0)
            self.assertLessEqual(acc[key], 1.0)
        self.assertIn("lookback_period", acc)

    def test_03_accuracy_reward_and_penalty_dynamics(self):
        """Verify that high accuracy increases weight and low accuracy reduces weight."""
        # High accuracy for Insider (0.90), Low for Fundamental (0.35)
        test_acc = {
            "fundamental": 0.35,
            "insider": 0.90,
            "alternative": 0.60,
            "sentiment": 0.60
        }
        calibrated = WalkForwardMLEngine.calibrate_engine_weights(accuracies=test_acc)

        # 1. Insider must be rewarded (higher than its base weight of 0.25)
        self.assertGreater(calibrated["insider"], WalkForwardMLEngine.DEFAULT_BASE_WEIGHTS["insider"])

        # 2. Fundamental must be penalized (lower than its base weight of 0.30)
        self.assertLess(calibrated["fundamental"], WalkForwardMLEngine.DEFAULT_BASE_WEIGHTS["fundamental"])

        # 3. Insider weight must exceed Fundamental weight
        self.assertGreater(calibrated["insider"], calibrated["fundamental"])

        # 4. Weights must sum to 1.0
        self.assertAlmostEqual(sum(calibrated.values()), 1.0, places=4)

    def test_04_extreme_edge_cases_weights_sum_to_one(self):
        """Verify strict weight conservation (Sum = 1.0000) under extreme scenarios."""
        # Case A: All zero accuracy
        zeros = {"fundamental": 0.0, "insider": 0.0, "alternative": 0.0, "sentiment": 0.0}
        cal_zeros = WalkForwardMLEngine.calibrate_engine_weights(accuracies=zeros)
        self.assertAlmostEqual(sum(cal_zeros.values()), 1.0, places=4)

        # Case B: All 100% accuracy
        ones = {"fundamental": 1.0, "insider": 1.0, "alternative": 1.0, "sentiment": 1.0}
        cal_ones = WalkForwardMLEngine.calibrate_engine_weights(accuracies=ones)
        self.assertAlmostEqual(sum(cal_ones.values()), 1.0, places=4)

        # Case C: Extreme single-engine monopoly (Insider = 1.0, others = 0.0)
        monopoly = {"fundamental": 0.0, "insider": 1.0, "alternative": 0.0, "sentiment": 0.0}
        cal_monopoly = WalkForwardMLEngine.calibrate_engine_weights(accuracies=monopoly)
        self.assertAlmostEqual(sum(cal_monopoly.values()), 1.0, places=4)
        # Clamping constraint ensures minimum weights for all engines
        self.assertGreaterEqual(cal_monopoly["fundamental"], WalkForwardMLEngine.MIN_WEIGHT)
        self.assertLessEqual(cal_monopoly["insider"], WalkForwardMLEngine.MAX_WEIGHT)

        # Case D: Fractional arbitrary values
        fractional = {"fundamental": 0.1234, "insider": 0.9876, "alternative": 0.5432, "sentiment": 0.6789}
        cal_frac = WalkForwardMLEngine.calibrate_engine_weights(accuracies=fractional)
        self.assertAlmostEqual(sum(cal_frac.values()), 1.0, places=4)

    def test_05_get_active_model_weights_and_rationale(self):
        """Verify get_active_model_weights compiles full metadata and diagnostic Arabic rationale."""
        res = WalkForwardMLEngine.get_active_model_weights(force_refresh=True)
        self.assertEqual(res["status"], "CALIBRATED")
        self.assertIn("active_weights", res)
        self.assertIn("base_weights", res)
        self.assertIn("accuracy_metrics", res)
        self.assertIn("calibration_delta", res)
        self.assertIn("top_performing_engine", res)
        self.assertIn("weakest_engine", res)
        self.assertIn("diagnostic_rationale_ar", res)
        self.assertGreater(len(res["diagnostic_rationale_ar"]), 15)
        self.assertAlmostEqual(sum(res["active_weights"].values()), 1.0, places=4)

    def test_06_calculate_walk_forward_composite_score(self):
        """Verify composite score weighting math."""
        score = WalkForwardMLEngine.calculate_walk_forward_composite_score(
            fundamental_score=80.0,
            insider_score=95.0,
            alternative_score=90.0,
            sentiment_score=70.0,
            custom_weights={"fundamental": 0.20, "insider": 0.40, "alternative": 0.25, "sentiment": 0.15}
        )
        # 80*0.2 + 95*0.4 + 90*0.25 + 70*0.15 = 16 + 38 + 22.5 + 10.5 = 87.0
        self.assertEqual(score, 87.0)

    def test_07_invalid_and_negative_accuracy_robustness(self):
        """Verify engine gracefully recovers from negative, string, or NaN accuracies."""
        bad_acc = {
            "fundamental": -0.5,
            "insider": "0.85",
            "alternative": float("nan"),
            "sentiment": 1.5
        }
        cal = WalkForwardMLEngine.calibrate_engine_weights(accuracies=bad_acc)
        self.assertAlmostEqual(sum(cal.values()), 1.0, places=4)
        for w in cal.values():
            self.assertGreaterEqual(w, WalkForwardMLEngine.MIN_WEIGHT)
            self.assertLessEqual(w, WalkForwardMLEngine.MAX_WEIGHT)

    def test_08_custom_base_weights(self):
        """Verify calibration works with custom base weight topologies."""
        custom_base = {"fundamental": 0.40, "insider": 0.30, "alternative": 0.20, "sentiment": 0.10}
        acc = {"fundamental": 0.90, "insider": 0.30, "alternative": 0.50, "sentiment": 0.50}
        cal = WalkForwardMLEngine.calibrate_engine_weights(accuracies=acc, base_weights=custom_base)
        self.assertAlmostEqual(sum(cal.values()), 1.0, places=4)
        # Fundamental had high base and high accuracy -> highest weight
        self.assertEqual(max(cal, key=cal.get), "fundamental")


if __name__ == "__main__":
    unittest.main()
