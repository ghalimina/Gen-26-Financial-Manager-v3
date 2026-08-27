#!/usr/bin/env python3
# =============================================================================
# tests/test_hardening_phase_2.py — GEN-26 Hardening Phase 2 Test Suite
# Rigorously validates:
# 1. Dynamic Weight Calibration (SciPy SLSQP Sharpe Optimization)
# 2. Vectorized Statistical Edge Verification (Profit Factor, Hit Rate, Max DD)
# 3. ML Permutation Importance Testing & Anti-Noise Constraints
# =============================================================================

import os
import sys
import unittest
import numpy as np
import pandas as pd

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.weight_calibrator import WeightCalibrator
from core.edge_verifier import StatisticalEdgeVerifier
from core.model_evaluator import PermutationImportanceValidator
from core.meta_labeling_engine import MetaLabelingEngine
from core.multi_horizon_engine import MultiHorizonEngine


class TestGenesisHardeningPhase2(unittest.TestCase):

    def test_01_dynamic_weight_calibration_optimization(self):
        """Verify WeightCalibrator optimizes weights to sum=1.0 and factor floor >= 5%."""
        res = WeightCalibrator.calibrate_weights(lookback_months=12, min_factor_weight=0.05)
        self.assertEqual(res["status"], "CALIBRATED_OPTIMAL")
        self.assertIn("weights", res)

        w = res["weights"]
        self.assertIn("w_fundamental", w)
        self.assertIn("w_technical", w)
        self.assertIn("w_flow", w)
        self.assertIn("w_rs", w)

        # Constraint check: sum of weights equals 1.0 (with floating precision)
        total_w = sum(w.values())
        self.assertAlmostEqual(total_w, 1.0, places=3)

        # Constraint check: each factor has at least 5% weight
        for k, v in w.items():
            self.assertGreaterEqual(v, 0.049, f"Weight for {k} ({v}) below 5% floor")

        self.assertGreater(res["optimal_sharpe_ratio"], 0.0)

    def test_02_scoring_engine_loads_calibrated_weights(self):
        """Verify MultiHorizonEngine applies dynamic calibrated weights for overall score."""
        analysis = MultiHorizonEngine.get_stock_multi_horizon_analysis("COMI.CA")
        self.assertIsNotNone(analysis)
        self.assertIn("overall_score", analysis)
        self.assertGreater(analysis["overall_score"], 0.0)

    def test_03_statistical_edge_verifier_vectorized_backtest(self):
        """Verify StatisticalEdgeVerifier computes Profit Factor, Hit Rate, and Max DD."""
        res = StatisticalEdgeVerifier.run_vectorized_backtest(lookback_days=250)
        self.assertEqual(res["status"], "BACKTEST_COMPLETED")
        self.assertGreater(res["total_trades"], 10)
        self.assertIn("hit_rate_pct", res)
        self.assertIn("profit_factor", res)
        self.assertIn("max_drawdown_pct", res)

        # Verify Profit Factor and Hit Rate are numeric and valid
        self.assertIsInstance(res["profit_factor"], float)
        self.assertIsInstance(res["hit_rate_pct"], float)
        self.assertLess(res["max_drawdown_pct"], 0.0) # Drawdown is negative

    def test_04_ml_permutation_importance_validation(self):
        """Verify PermutationImportanceValidator evaluates feature contribution and detects noise."""
        train_res = MetaLabelingEngine.train_meta_models()
        self.assertEqual(train_res["status"], "TRAINED_SUCCESS")
        self.assertIn("permutation_importance", train_res)

        perm = train_res["permutation_importance"]
        self.assertEqual(perm["status"], "PERMUTATION_VALIDATION_COMPLETED")
        self.assertEqual(len(perm["top_5_features"]), 5)

        # Top feature must have positive mean importance
        top_f = perm["top_5_features"][0]
        self.assertGreater(top_f["importance_mean"], 0.0)

        # Verify all top 5 features have non-negative importance
        for f in perm["top_5_features"]:
            self.assertGreaterEqual(f["importance_mean"], 0.0)


if __name__ == "__main__":
    unittest.main()
