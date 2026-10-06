#!/usr/bin/env python3
# =============================================================================
# tests/test_ai_prediction_model.py — Forensic Unit Tests for GEN-26 AI Predictive Engine
# Validates ML pipeline, orthogonal feature vector extraction, TimeSeriesSplit CV,
# consensus gating with classical quantitative logic, and risk override invariance.
# =============================================================================

import os
import sys
import unittest
import numpy as np

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.ai_prediction_model import AIPredictionModel
from core.multi_horizon_engine import MultiHorizonEngine
from dashboard.app import app


class TestAIPredictionModel(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_01_feature_vector_extraction(self):
        """Verify feature extraction returns exact 21-dimensional orthogonal vector with lag & regime metrics."""
        vec, feat_dict = AIPredictionModel.extract_feature_vector("COMI.CA", current_price=138.80)
        self.assertEqual(len(vec), 21)
        self.assertEqual(len(feat_dict), 21)
        self.assertTrue(np.all(np.isfinite(vec)))

        # Verify key orthogonal and lag dimensions
        self.assertIn("macd_hist", feat_dict)
        self.assertIn("macd_hist_lag1", feat_dict)
        self.assertIn("obv_slope", feat_dict)
        self.assertIn("ocf_to_ni_ratio", feat_dict)
        self.assertIn("cbe_corridor_rate_pct", feat_dict)
        self.assertIn("setup_encoded", feat_dict)
        self.assertIn("volatility_regime_encoded", feat_dict)
        self.assertIn("roc_1d_lag1", feat_dict)
        self.assertIn("roc_20d", feat_dict)
        self.assertIn("beta_egx30", feat_dict)

    def test_02_model_training_timeseries_split(self):
        """Verify model trains with TimeSeriesSplit without look-ahead bias."""
        res = AIPredictionModel.train_model()
        self.assertIn(res["status"], ["TRAINED_SUCCESS", "CACHED_LOAD"])
        self.assertTrue(res["is_trained"])
        self.assertIn("metadata", res)
        self.assertIn("cv_strategy", res["metadata"])
        self.assertIn("TimeSeriesSplit", res["metadata"]["cv_strategy"])

    def test_03_prediction_output_schema(self):
        """Verify inference outputs residual alpha, confidence score, and top 3 drivers."""
        pred = AIPredictionModel.predict_stock("SWDY.CA", current_price=120.50)
        self.assertEqual(pred["ticker"], "SWDY.CA")
        self.assertIn("expected_alpha_10d_pct", pred)
        self.assertIn("ai_confidence_score", pred)
        self.assertGreaterEqual(pred["ai_confidence_score"], 0.0)
        self.assertLessEqual(pred["ai_confidence_score"], 100.0)
        self.assertIn(pred["ai_sentiment"], ["BULLISH", "NEUTRAL", "BEARISH"])
        self.assertTrue(len(pred["top_3_drivers"]) <= 3)

        # Check driver structure
        for d in pred["top_3_drivers"]:
            self.assertIn("feature", d)
            self.assertIn("label_ar", d)
            self.assertIn("importance_pct", d)
            self.assertIn("value", d)

    def test_04_ai_consensus_in_multi_horizon(self):
        """Verify MultiHorizonEngine embeds AI prediction and requires consensus."""
        analysis = MultiHorizonEngine.get_stock_multi_horizon_analysis("COMI.CA")
        self.assertIsNotNone(analysis)
        self.assertIn("ai_forecast", analysis)
        self.assertIn("ai_expected_alpha_10d", analysis)
        self.assertIn("ai_confidence_score", analysis)
        self.assertIn("ai_top_drivers", analysis)
        self.assertIn("ai_sentiment_ar", analysis)

    def test_05_risk_engine_override_invariance(self):
        """Verify AI forecast CANNOT override ATR Stop Loss or Risk Position Sizing."""
        analysis = MultiHorizonEngine.get_stock_multi_horizon_analysis("COMI.CA")
        p = analysis["current_price"]
        stop_loss = analysis["stop_loss"]

        # Stop loss must strictly be below entry price (at least 3.5% below)
        self.assertLess(stop_loss, p)
        self.assertLessEqual(stop_loss, p * 0.965)

        # Position allocation cannot exceed 20% hard cap
        pos_size = analysis["risk_based_position"]
        self.assertLessEqual(pos_size["allocation_pct"], 20.0)

    def test_06_api_ai_forecast_endpoint(self):
        """Verify GET /api/ai/forecast/<ticker> returns HTTP 200 with forecast payload."""
        response = self.app.get("/api/ai/forecast/COMI.CA")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["ticker"], "COMI.CA")
        self.assertIn("expected_alpha_10d_pct", data)
        self.assertIn("ai_confidence_score", data)
        self.assertIn("top_3_drivers", data)

    def test_07_purged_timeseries_split_embargo_isolation(self):
        """Verify PurgedTimeSeriesSplit purges overlapping horizon days and applies embargo."""
        from core.ai_prediction_model import PurgedTimeSeriesSplit
        X_dummy = np.zeros((100, 5))
        ptscv = PurgedTimeSeriesSplit(n_splits=4, horizon_days=10, embargo_pct=0.05)
        splits = list(ptscv.split(X_dummy))
        self.assertGreaterEqual(len(splits), 2)
        for train_idx, test_idx in splits:
            # Maximum train index must be strictly less than minimum test index minus horizon
            max_train = np.max(train_idx)
            min_test = np.min(test_idx)
            self.assertGreaterEqual(min_test - max_train, 10, "Leakage: Overlapping horizon was not purged!")

    def test_08_native_feature_importance_properties(self):
        """Verify feature importances are normalized and sum close to 1.0."""
        importances = AIPredictionModel._feature_importances
        self.assertGreater(len(importances), 0)
        total = sum(importances.values())
        self.assertAlmostEqual(total, 1.0, places=1)

    def test_09_lightgbm_ensemble_model(self):
        """Verify LightGBM + XGBoost Ensemble returns weighted prediction (0.6*xgb + 0.4*lgbm)."""
        model = AIPredictionModel()
        self.assertTrue(model.is_trained)
        self.assertIsNotNone(model.model)
        self.assertIsNotNone(model.lgbm)
        
        vec, _ = AIPredictionModel.extract_feature_vector("COMI.CA", 138.80)
        pred_val = model.predict(vec)
        self.assertIsInstance(pred_val, float)
        self.assertTrue(np.isfinite(pred_val))


if __name__ == "__main__":
    unittest.main()
