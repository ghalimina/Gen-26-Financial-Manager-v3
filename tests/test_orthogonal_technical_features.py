#!/usr/bin/env python3
# =============================================================================
# tests/test_orthogonal_technical_features.py — Tests for Orthogonal Technical Engine
# Validates HH/HL Structure, OBV Regression Slope, ROC, ATR_PCT, HV20, and 5D Scoring.
# =============================================================================

import os
import sys
import unittest
import json
import pandas as pd

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.technical_setup_engine import TechnicalSetupEngine
from core.feature_registry import FeatureRegistry


class TestOrthogonalTechnicalFeatures(unittest.TestCase):
    """
    Test suite for orthogonal technical indicators and 5-dimension scoring architecture.
    """

    def setUp(self):
        self.registry = FeatureRegistry()

    def test_01_feature_registry_orthogonal_registrations(self):
        """Verify all new orthogonal features are registered in feature_registry.py."""
        expected_feature_ids = [
            "FEAT_MARKET_STRUCTURE_HH_HL",
            "FEAT_52W_HIGH_PROXIMITY_PCT",
            "FEAT_52W_LOW_PROXIMITY_PCT",
            "FEAT_DIST_TO_SUPPORT_PCT",
            "FEAT_DIST_TO_RESISTANCE_PCT",
            "FEAT_OBV_SLOPE_10D",
            "FEAT_ROC_5D",
            "FEAT_ROC_20D",
            "FEAT_HISTORICAL_VOLATILITY_20D",
            "FEAT_ATR_PCT"
        ]
        all_features = [f["feature_id"] for f in self.registry.list_all()]
        for feat_id in expected_feature_ids:
            self.assertIn(feat_id, all_features, f"Feature {feat_id} missing from FeatureRegistry.")

    def test_02_market_structure_hh_hl_and_52w_proximity(self):
        """Verify Higher-Highs/Higher-Lows detection and 52W proximity calculations."""
        res_oras = TechnicalSetupEngine.evaluate_technical_setup("ORAS.CA", 782.25)
        self.assertIn("market_structure", res_oras)
        ms = res_oras["market_structure"]
        self.assertIn(ms["hh_hl_status"], ["HH_HL", "CONSOLIDATION", "LH_LL"])
        self.assertIn("distance_from_52w_high_pct", ms)
        self.assertIn("distance_from_52w_low_pct", ms)
        self.assertIn("dist_to_support_pct", ms)
        self.assertIn("dist_to_resistance_pct", ms)

        # 52W high proximity checks
        self.assertIsInstance(ms["distance_from_52w_high_pct"], float)
        self.assertIsInstance(ms["distance_from_52w_low_pct"], float)

    def test_03_obv_regression_slope_and_accumulation(self):
        """Verify OBV Regression Slope and accumulation status."""
        res_swdy = TechnicalSetupEngine.evaluate_technical_setup("SWDY.CA", 120.89)
        self.assertIn("volume_and_obv", res_swdy)
        v_obv = res_swdy["volume_and_obv"]
        self.assertIn("obv_slope", v_obv)
        self.assertIsInstance(v_obv["obv_slope"], (int, float))
        self.assertIn("obv_status_ar", v_obv)
        self.assertIn("rvol_10d", v_obv)

    def test_04_roc_pure_price_acceleration(self):
        """Verify ROC_5D and ROC_20D calculations distinct from RSI."""
        res_comi = TechnicalSetupEngine.evaluate_technical_setup("COMI.CA", 138.80)
        self.assertIn("momentum_roc", res_comi)
        roc = res_comi["momentum_roc"]
        self.assertIn("roc_5d", roc)
        self.assertIn("roc_20d", roc)
        self.assertIsInstance(roc["roc_5d"], float)
        self.assertIsInstance(roc["roc_20d"], float)

    def test_05_volatility_normalization_atr_pct_and_hv20(self):
        """Verify ATR_PCT and HV20 historical volatility normalization."""
        res_egal = TechnicalSetupEngine.evaluate_technical_setup("EGAL.CA", 330.00)
        self.assertIn("volatility_metrics", res_egal)
        vm = res_egal["volatility_metrics"]
        self.assertIn("atr_pct", vm)
        self.assertIn("hv_20", vm)
        self.assertGreater(vm["atr_pct"], 0.0)
        self.assertGreater(vm["hv_20"], 0.0)

    def test_06_5_dimension_orthogonal_scoring_breakdown(self):
        """Verify 5 independent dimensions (20% each) aggregate to composite technical score."""
        res = TechnicalSetupEngine.evaluate_technical_setup("SWDY.CA", 120.89)
        self.assertIn("scoring_dimensions", res)
        dims = res["scoring_dimensions"]
        self.assertIn("dim1_trend_strength_20", dims)
        self.assertIn("dim2_price_structure_20", dims)
        self.assertIn("dim3_momentum_20", dims)
        self.assertIn("dim4_volume_obv_20", dims)
        self.assertIn("dim5_volatility_risk_20", dims)

        # Each dimension bounded within [0, 20]
        for k, v in dims.items():
            self.assertGreaterEqual(v, 0.0, f"Dimension {k} below 0")
            self.assertLessEqual(v, 20.0, f"Dimension {k} exceeds 20.0 pts")

        # Sum of dimensions equals technical score
        total_dim = sum(dims.values())
        self.assertAlmostEqual(res["technical_score"], total_dim, delta=1.0)


if __name__ == "__main__":
    unittest.main()
