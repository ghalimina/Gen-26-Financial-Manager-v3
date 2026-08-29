#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# tests/test_sprint_b_feedback_and_registry.py — Sprint B Verification Test Suite
# Tests:
# 1. Prediction vs Actual table CRUD and DB persistence.
# 2. PredictionActualTracker recording, closed horizons reconciliation & metrics.
# 3. Deflated Sharpe Ratio (DSR) & 4-Stage Promotion Lifecycle State Machine.
# 4. 48-Feature Registry & 1st/99th Percentile Winsorization.
# 5. REST API Endpoints in dashboard/app.py.
# =============================================================================

import os
import sys
import json
import unittest
import datetime

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.database_engine import db_engine
from core.prediction_actual_tracker import PredictionActualTracker
from core.promotion_gate import PromotionGate
from core.feature_registry import FeatureRegistry
from dashboard.app import app


class TestSprintBFeedbackAndRegistry(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        db_engine.initialize_database()
        app.config["TESTING"] = True
        cls.client = app.test_client()

    def test_01_database_prediction_table_and_crud(self):
        """TC-B01: Verify prediction_vs_actual table CRUD operations."""
        test_pred_id = f"PRED_TEST_COMI_1D_{os.urandom(4).hex()}"
        pred_record = {
            "prediction_id": test_pred_id,
            "ticker": "COMI.CA",
            "horizon": "1D",
            "timestamp_created": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "timestamp_target": (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
            "entry_price": 139.28,
            "predicted_target_price": 145.00,
            "predicted_direction": "BULLISH",
            "predicted_confidence_pct": 92.5,
            "features_snapshot_json": {"rsi_14": 58.2, "piotroski_f": 9},
            "status": "PENDING"
        }
        ok = db_engine.record_prediction_forecast(pred_record)
        self.assertTrue(ok)

        pending = db_engine.get_pending_predictions(limit=100)
        self.assertTrue(any(p["prediction_id"] == test_pred_id for p in pending))

        reconcile_ok = db_engine.update_reconciled_prediction(
            prediction_id=test_pred_id,
            actual_price=146.50,
            is_hit=1,
            forecast_error_pct=1.03,
            actual_direction="BULLISH"
        )
        self.assertTrue(reconcile_ok)

        stats = db_engine.get_prediction_accuracy_stats(ticker="COMI.CA")
        self.assertGreaterEqual(stats["total_reconciled"], 1)
        self.assertGreaterEqual(stats["hits_count"], 1)

    def test_02_prediction_actual_tracker_lifecycle(self):
        """TC-B02: Verify PredictionActualTracker record and reconciliation."""
        rec = PredictionActualTracker.record_prediction(
            ticker="SWDY.CA",
            horizon="1D",
            predicted_target_price=135.0,
            predicted_direction="BULLISH",
            predicted_confidence_pct=90.0,
            features_snapshot={"adx": 31.0}
        )
        self.assertTrue(rec["success"])
        self.assertIn("PRED_SWDY_CA_1D", rec["prediction_id"])

        # Reconcile
        recon_res = PredictionActualTracker.reconcile_closed_horizons()
        self.assertIn("reconciled_count", recon_res)
        self.assertIn("hit_rate_pct", recon_res)

        metrics = PredictionActualTracker.get_rolling_accuracy_metrics(lookback_days=30)
        self.assertIn("total_reconciled", metrics)
        self.assertIn("hit_rate_pct", metrics)
        self.assertEqual(metrics["feedback_loop_status"], "ACTIVE_SELF_CALIBRATING")

    def test_03_deflated_sharpe_ratio_and_promotion_stages(self):
        """TC-B03: Verify Deflated Sharpe Ratio equation and 4-stage lifecycle state machine."""
        # DSR calculation with 15 trials
        dsr_val = PromotionGate.calculate_deflated_sharpe_ratio(
            observed_sharpe=1.95,
            num_trials=15,
            sample_length_days=252
        )
        self.assertIsInstance(dsr_val, float)
        self.assertGreaterEqual(dsr_val, 0.0)
        self.assertLessEqual(dsr_val, 1.0)

        # 4-stage lifecycle status
        lifecycle = PromotionGate.get_promotion_lifecycle_status("STRAT_TEST_48")
        self.assertIn("current_active_stage", lifecycle)
        self.assertIn("STAGE_1_SHADOW_MODE", lifecycle["lifecycle_stages"])
        self.assertIn("STAGE_2_PAPER_FULL", lifecycle["lifecycle_stages"])
        self.assertIn("STAGE_3_LIVE_MICRO", lifecycle["lifecycle_stages"])
        self.assertIn("STAGE_4_SCALE_UP", lifecycle["lifecycle_stages"])
        self.assertTrue(lifecycle["overall_promotion_ready"])

    def test_04_feature_registry_and_winsorization(self):
        """TC-B04: Verify 48-feature catalog, outlier winsorization, and deprecation logic."""
        all_feats = FeatureRegistry.get_all_features()
        self.assertEqual(len(all_feats), 48)

        # Winsorization of outlier
        raw_tensor = {
            "murphy_adx_strength": 999.0, # Clamped to p99 = 65.0
            "rsi_14_level": -50.0,         # Clamped to p01 = 15.0
            "piotroski_f_score": 9.0
        }
        clean_tensor = FeatureRegistry.winsorize_tensor(raw_tensor)
        self.assertEqual(clean_tensor["murphy_adx_strength"], 65.0)
        self.assertEqual(clean_tensor["rsi_14_level"], 15.0)
        self.assertEqual(clean_tensor["piotroski_f_score"], 9.0)

        # Feature evaluation and deprecation
        eval_res = FeatureRegistry.evaluate_and_deprecate_features({
            "obv_slope": -0.05 # Negative importance -> deprecated
        })
        self.assertIn("obv_slope", eval_res["deprecated_features"])

        summary = FeatureRegistry.get_summary()
        self.assertEqual(summary["total_features"], 48)
        self.assertIn("TECHNICAL", summary["dimensions_breakdown"])

    def test_05_observability_rest_api_endpoints(self):
        """TC-B05: Verify /api/observability/* REST endpoints."""
        # 1. Forecast vs Actual
        res1 = self.client.get("/api/observability/forecast_vs_actual?lookback_days=30")
        self.assertEqual(res1.status_code, 200)
        data1 = res1.get_json()
        self.assertIn("hit_rate_pct", data1)
        self.assertIn("recent_reconciled_records", data1)

        # 2. Feature Registry
        res2 = self.client.get("/api/observability/feature_registry")
        self.assertEqual(res2.status_code, 200)
        data2 = res2.get_json()
        self.assertEqual(data2["total_features"], 48)
        self.assertIn("features_catalog", data2)

        # 3. Promotion Lifecycle
        res3 = self.client.get("/api/observability/promotion_lifecycle")
        self.assertEqual(res3.status_code, 200)
        data3 = res3.get_json()
        self.assertIn("current_active_stage", data3)
        self.assertIn("lifecycle_stages", data3)


if __name__ == "__main__":
    unittest.main()
