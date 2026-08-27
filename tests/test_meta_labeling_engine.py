#!/usr/bin/env python3
# =============================================================================
# tests/test_meta_labeling_engine.py — Forensic Unit Tests for GEN-26 Meta-Labeling
# Validates Marcos López de Prado's Meta-Labeling paradigm:
# 1. Sector-Neutralization & Cross-Sectional Z-score computation.
# 2. Meta-Classifier Probability of Success (Target T1 vs ATR Stop).
# 3. Consensus Gating & Meta-Model Veto of weak BUY signals.
# 4. Volatility-Adjusted Target Return (Alpha / ATR).
# 5. Risk Engine Invariance (AI cannot override ATR Stop / 20% Cap).
# 6. REST API Endpoint JSON schema.
# =============================================================================

import os
import sys
import unittest
import numpy as np

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.feature_registry import SectorNeutralizer
from core.meta_labeling_engine import MetaLabelingEngine
from core.multi_horizon_engine import MultiHorizonEngine
from dashboard.app import app


class TestMetaLabelingEngine(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_01_sector_neutralizer_computation(self):
        """Verify cross-sectional sector-neutral Z-score calculation for EGX stocks."""
        res = SectorNeutralizer.compute_sector_neutral_features(
            ticker="COMI.CA",
            pe_ratio=6.0,
            rsi14=60.0,
            volume_z_score=1.2
        )
        self.assertEqual(res["sector"], "BANKING_FINTECH")
        self.assertIn("sector_neutral_pe", res)
        self.assertIn("sector_neutral_rsi", res)
        self.assertIn("sector_neutral_volume_zscore", res)
        self.assertIn("finbert_sentiment_score", res)

        # Cheaper P/E than sector mean (6.0 < 6.8) should yield positive value score
        self.assertGreater(res["sector_neutral_pe"], 0.0)
        # RSI above sector mean (60.0 > 54.0) should yield positive momentum Z
        self.assertGreater(res["sector_neutral_rsi"], 0.0)

    def test_02_meta_feature_vector_extraction(self):
        """Verify extraction of 16-dimensional sector-neutral meta-feature vector."""
        vec, feat_dict = MetaLabelingEngine.extract_meta_feature_vector("COMI.CA", current_price=138.80)
        self.assertEqual(len(vec), 16)
        self.assertTrue(np.all(np.isfinite(vec)))

        # Assert presence of key sector-neutral and macro indicators
        self.assertIn("sector_neutral_pe", feat_dict)
        self.assertIn("sector_neutral_rsi", feat_dict)
        self.assertIn("sector_neutral_volume_zscore", feat_dict)
        self.assertIn("finbert_sentiment_score", feat_dict)
        self.assertIn("cbe_corridor_rate_pct", feat_dict)
        self.assertIn("usd_egp_rate", feat_dict)
        self.assertIn("setup_encoded", feat_dict)

    def test_03_meta_model_training_and_schema(self):
        """Verify training of secondary meta-classifier and volatility regressor."""
        train_res = MetaLabelingEngine.train_meta_models()
        self.assertEqual(train_res["status"], "TRAINED_SUCCESS")
        self.assertTrue(train_res["is_trained"])
        self.assertIn("metadata", train_res)
        self.assertIn("paradigm", train_res["metadata"])

    def test_04_meta_label_evaluation_output(self):
        """Verify meta-label evaluation produces probability of success and decision."""
        eval_res = MetaLabelingEngine.evaluate_meta_label("SWDY.CA", current_price=120.50, base_quant_score=85.0)
        self.assertEqual(eval_res["ticker"], "SWDY.CA")
        self.assertIn("meta_decision", eval_res)
        self.assertIn(eval_res["meta_decision"], ["CONFIRM_BUY", "REJECT_BUY", "NEUTRAL"])
        self.assertIn("probability_of_success_pct", eval_res)
        self.assertGreaterEqual(eval_res["probability_of_success_pct"], 0.0)
        self.assertLessEqual(eval_res["probability_of_success_pct"], 100.0)
        self.assertIn("volatility_adjusted_return", eval_res)
        self.assertIn("top_meta_drivers", eval_res)
        self.assertLessEqual(len(eval_res["top_meta_drivers"]), 3)

    def test_05_consensus_chain_integration(self):
        """Verify that MultiHorizonEngine incorporates Meta-Label decision into consensus."""
        analysis = MultiHorizonEngine.get_stock_multi_horizon_analysis("COMI.CA")
        self.assertIn("meta_label", analysis)
        self.assertIn("meta_decision", analysis)
        self.assertIn("probability_of_success_pct", analysis)
        self.assertIn("volatility_adjusted_return", analysis)

        # If decision is BUY, meta probability must strictly be >= 65% and meta_decision CONFIRM_BUY
        if analysis["decision"] == "BUY":
            self.assertGreaterEqual(analysis["probability_of_success_pct"], 65.0)
            self.assertEqual(analysis["meta_decision"], "CONFIRM_BUY")

    def test_06_risk_engine_override_invariance(self):
        """Verify Meta-Model CANNOT override the dynamic ATR stop floor or position sizing."""
        analysis = MultiHorizonEngine.get_stock_multi_horizon_analysis("COMI.CA")
        p = analysis["current_price"]
        stop_loss = analysis["stop_loss"]

        # Dynamic Stop Loss must strictly be below entry price by at least 3.5%
        self.assertLess(stop_loss, p)
        self.assertLessEqual(stop_loss, p * 0.965)

        # Position Sizing hard floor: cannot exceed 20.0%
        pos = analysis["risk_based_position"]
        self.assertLessEqual(pos["allocation_pct"], 20.0)

    def test_07_api_ai_forecast_endpoint_meta_fields(self):
        """Verify GET /api/ai/forecast/<ticker> returns enriched Meta-Labeling payload."""
        response = self.app.get("/api/ai/forecast/COMI.CA")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["ticker"], "COMI.CA")
        self.assertIn("meta_decision", data)
        self.assertIn("probability_of_success_pct", data)
        self.assertIn("volatility_adjusted_return", data)
        self.assertIn("sector_neutral_features", data)
        self.assertIn("top_meta_drivers", data)


if __name__ == "__main__":
    unittest.main()
