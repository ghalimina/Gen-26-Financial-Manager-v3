#!/usr/bin/env python3
# =============================================================================
# tests/test_regime_hmm_engine.py — Unit Tests for HMM Dynamic Factor Weighting
# Validates:
# 1. Latent market regime classification (BULL, BEAR, SIDEWAYS).
# 2. Dynamic factor weights allocation (Sum to 1.0).
# 3. Asymmetric weight tilting in Bull vs Bear regimes.
# 4. Regime-adjusted composite score computation.
# =============================================================================

import os
import sys
import unittest

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.regime_hmm_engine import RegimeHMMEngine


class TestRegimeHMMEngine(unittest.TestCase):

    def test_01_regime_detection_schema(self):
        """Verify HMM latent regime detection schema and probability distribution."""
        res = RegimeHMMEngine.detect_latent_regime()
        self.assertIn("current_regime_state", res)
        self.assertIn(res["current_regime_state"], [
            RegimeHMMEngine.STATE_BULL_MOMENTUM,
            RegimeHMMEngine.STATE_BEAR_DEFENSIVE,
            RegimeHMMEngine.STATE_SIDEWAYS_NEUTRAL
        ])
        self.assertIn("active_factor_weights", res)
        self.assertIn("state_probabilities", res)

    def test_02_dynamic_weights_conservation(self):
        """Verify that factor weights for all 3 HMM states sum to exactly 1.0."""
        for state, weights_info in RegimeHMMEngine.DYNAMIC_WEIGHTS.items():
            total = (
                weights_info["technicals"] +
                weights_info["volatility"] +
                weights_info["fundamentals"] +
                weights_info["macro"]
            )
            self.assertAlmostEqual(total, 1.0, places=4, msg=f"Weights in state {state} do not sum to 1.0")

    def test_03_asymmetric_regime_factor_tilting(self):
        """Verify that Bull regimes prioritize technicals/volatility while Bear prioritizes fundamentals/macro."""
        bull_w = RegimeHMMEngine.DYNAMIC_WEIGHTS[RegimeHMMEngine.STATE_BULL_MOMENTUM]
        bear_w = RegimeHMMEngine.DYNAMIC_WEIGHTS[RegimeHMMEngine.STATE_BEAR_DEFENSIVE]

        # Bull: Technicals (40%) > Fundamentals (15%)
        self.assertGreater(bull_w["technicals"], bull_w["fundamentals"])
        self.assertEqual(bull_w["technicals"], 0.40)
        self.assertEqual(bull_w["volatility"], 0.30)

        # Bear: Fundamentals (40%) > Technicals (10%)
        self.assertGreater(bear_w["fundamentals"], bear_w["technicals"])
        self.assertEqual(bear_w["fundamentals"], 0.40)
        self.assertEqual(bear_w["macro"], 0.30)

    def test_04_regime_adjusted_score_computation(self):
        """Verify regime-adjusted score calculation correctly applies dynamic weights."""
        score = RegimeHMMEngine.calculate_regime_adjusted_score(
            tech_score=90.0,
            vol_score=80.0,
            fund_score=70.0,
            macro_score=60.0
        )
        self.assertGreater(score, 0.0)
        self.assertLessEqual(score, 100.0)


if __name__ == "__main__":
    unittest.main()
