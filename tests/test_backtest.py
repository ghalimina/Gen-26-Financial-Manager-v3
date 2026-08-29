#!/usr/bin/env python3
# =============================================================================
# tests/test_backtest.py — GEN-26 Backtest & Promotion Gate Unit Tests
# =============================================================================

import unittest
import pandas as pd
import numpy as np
import sys
import os

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.promotion_gate import PromotionGate


class TestBacktestEngine(unittest.TestCase):

    def setUp(self):
        self.candidate_strategy = {
            "hypothesis_title": "Adaptive Volatility Dynamic Momentum",
            "in_sample_sharpe": 2.35,
            "oos_sharpe": 1.90,
            "max_drawdown_pct": 11.2,
            "win_rate_pct": 66.5,
            "seed": 42
        }

    def test_walk_forward_evaluation_and_metrics(self):
        res = PromotionGate.evaluate_candidate_strategy(self.candidate_strategy)
        self.assertIsNotNone(res)
        self.assertIn("in_sample_sharpe", res)
        self.assertIn("oos_sharpe", res)
        self.assertIn("max_drawdown_pct", res)
        self.assertIn("win_rate_pct", res)
        self.assertIn("deflated_sharpe_ratio", res)
        self.assertEqual(res["folds_evaluated"], 5)

    def test_promotion_decision_gating(self):
        eval_metrics = PromotionGate.evaluate_candidate_strategy(self.candidate_strategy)
        verdict = PromotionGate.judge_promotion(eval_metrics, baseline_sharpe=1.45)
        self.assertIn(verdict["promotion_status"], ["PROMOTED", "REJECTED"])
        self.assertIn("verdict_ar", verdict)


if __name__ == "__main__":
    unittest.main()
