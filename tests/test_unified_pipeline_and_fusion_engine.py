#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# tests/test_unified_pipeline_and_fusion_engine.py — STLC Test Suite for Sprint 5
# Validates:
# - TC-U01: Multi-Source Intelligence Aggregation & Bilingual Sentiment Scoring.
# - TC-U02: 48-Dimensional Quant Feature Tensor & Two-Stage Meta-Labeling.
# - TC-U03: Full End-to-End Execution of UnifiedPipelineOrchestrator.
# - TC-U04: Fail-Closed Protection for Unknown / Illiquid / Invalid Assets.
# - TC-U05: SQLite Audit Persistence & REST API Endpoints.
# =============================================================================

import unittest
import os
import sys
import json

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.multi_source_intelligence import MultiSourceIntelligence
from core.deep_quant_fusion_engine import DeepQuantFusionEngine
from core.unified_pipeline_orchestrator import UnifiedPipelineOrchestrator
from core.database_engine import db_engine
from dashboard.app import app


class TestUnifiedPipelineAndFusionEngine(unittest.TestCase):
    """
    Master STLC Test Battery for Sprint 5: Multi-Source Intelligence & Deep Quant Fusion.
    """

    def setUp(self):
        self.client = app.test_client()

    def test_tc_u01_multi_source_intelligence_aggregation(self):
        """
        TC-U01: Verify multi-source intelligence gathering across 5 feeds and sentiment scoring.
        """
        intel = MultiSourceIntelligence.get_all_intelligence(ticker="COMI.CA")
        self.assertEqual(intel["status"], "SUCCESS")
        self.assertIn("composite_sentiment_score", intel)
        self.assertTrue(-1.0 <= intel["composite_sentiment_score"] <= 1.0)
        self.assertIn("sentiment_label_ar", intel)

        # 5 Feeds Verification
        self.assertIn("feed_1_mubasher_disclosures", intel)
        self.assertGreater(len(intel["feed_1_mubasher_disclosures"]), 0)

        self.assertIn("feed_2_al_borsa_news", intel)
        self.assertIn("market_sentiment_ar", intel["feed_2_al_borsa_news"])

        self.assertIn("feed_3_enterprise_press", intel)
        self.assertIn("foreign_investment_telemetry", intel["feed_3_enterprise_press"])

        self.assertIn("feed_4_cbe_telemetry", intel)
        self.assertGreater(intel["feed_4_cbe_telemetry"]["cbe_deposit_rate_pct"], 0.0)

        self.assertIn("feed_5_global_commodities_gdrs", intel)
        self.assertIn("commodities", intel["feed_5_global_commodities_gdrs"])
        self.assertIn("london_gdrs", intel["feed_5_global_commodities_gdrs"])

        # Sentiment scoring helper check
        bull_score = MultiSourceIntelligence.compute_sentiment_score("نمو كبير في الأرباح وتوزيعات فائضة ممتازة")
        self.assertGreater(bull_score, 0.0)
        bear_score = MultiSourceIntelligence.compute_sentiment_score("خسائر فادحة وتراجع حاد في الإيرادات وركود اقتصادي")
        self.assertLess(bear_score, 0.0)

    def test_tc_u02_deep_quant_fusion_48_tensor_and_meta_labeling(self):
        """
        TC-U02: Verify 48-feature tensor extraction and Two-Stage Meta-Labeling AI predictor.
        """
        features_data = DeepQuantFusionEngine.extract_48_features("COMI.CA")
        self.assertEqual(features_data["feature_dimensions"], 48)
        self.assertEqual(len(features_data["tensor_vector"]), 48)
        self.assertEqual(len(features_data["feature_names"]), 48)

        # Check required named features
        raw = features_data["raw_features"]
        self.assertIn("murphy_adx_strength", raw)
        self.assertIn("piotroski_f_score", raw)
        self.assertIn("lynch_peg_ratio", raw)
        self.assertIn("cbe_corridor_rate_pct", raw)
        self.assertIn("multi_source_composite_nlp", raw)
        self.assertIn("stealth_volume_accumulation", raw)

        # Two-Stage Meta-Labeling Output
        fusion = DeepQuantFusionEngine.compute_fusion("COMI.CA")
        self.assertEqual(fusion["status"], "SUCCESS")
        self.assertEqual(fusion["ticker"], "COMI.CA")

        primary = fusion["primary_model"]
        self.assertIn(primary["predicted_direction"], ["BULLISH", "BEARISH", "RANGEBOUND"])
        self.assertIn("expected_return_pct", primary)

        meta = fusion["meta_confidence_model"]
        self.assertIn("probability_profitable", meta)
        self.assertTrue(0.0 <= meta["probability_profitable"] <= 1.0)
        self.assertIn("recommended_sizing_multiplier", meta)
        self.assertTrue(0.0 <= meta["recommended_sizing_multiplier"] <= 1.0)

    def test_tc_u03_full_unified_pipeline_orchestrator_execution(self):
        """
        TC-U03: Verify end-to-end execution of UnifiedPipelineOrchestrator for COMI.CA.
        """
        result = UnifiedPipelineOrchestrator.execute_unified_pipeline(
            ticker="COMI.CA",
            trigger_research=False,
            portfolio_equity=100_000.0
        )
        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(result["ticker"], "COMI.CA")
        self.assertIn(result["final_decision"], ["APPROVED_BUY", "HOLD_OR_REJECT"])
        self.assertIsInstance(result["approved_for_execution"], bool)
        self.assertGreater(result["current_price"], 0.0)
        self.assertGreater(result["target_price"], 0.0)
        self.assertGreater(result["stop_loss"], 0.0)

        # Confirm all subsystems are populated
        self.assertIn("multi_source_intelligence", result)
        self.assertIn("deep_quant_fusion", result)
        self.assertIn("council_deliberation", result)
        self.assertIn("quant_books_summary", result)
        self.assertIn("risk_and_execution_parameters", result)

        self.assertEqual(result["deep_quant_fusion"]["feature_dimensions"], 48)
        self.assertIn("trailing_stop_stage", result["risk_and_execution_parameters"])

    def test_tc_u04_fail_closed_fallback_protection(self):
        """
        TC-U04: Verify fail-closed behavior for invalid or unknown tickers.
        """
        for bad_ticker in ["UNKNOWN", "UNKNOWN.CA", "INVALID_STOCK", "NONE", ""]:
            res = UnifiedPipelineOrchestrator.execute_unified_pipeline(bad_ticker)
            self.assertEqual(res["status"], "FAILED_CLOSED")
            self.assertFalse(res["approved_for_execution"])
            self.assertEqual(res["final_decision"], "ABORT_AND_HOLD")

    def test_tc_u05_sqlite_persistence_and_rest_api_endpoints(self):
        """
        TC-U05: Verify SQLite persistence and REST API endpoints (/api/intelligence/multi_source,
        /api/signals/deep_fusion/<ticker>, /api/pipeline/run_unified).
        """
        # Execute pipeline to write to SQLite
        UnifiedPipelineOrchestrator.execute_unified_pipeline("SWDY.CA")
        recent_votes = db_engine.get_recent_council_votes(limit=5, ticker="SWDY.CA")
        self.assertGreater(len(recent_votes), 0)
        self.assertEqual(recent_votes[0]["ticker"], "SWDY.CA")

        # 1. Multi-source API endpoint
        res_intel = self.client.get("/api/intelligence/multi_source?ticker=COMI.CA")
        self.assertEqual(res_intel.status_code, 200)
        data_intel = res_intel.get_json()
        self.assertEqual(data_intel["status"], "SUCCESS")
        self.assertIn("feed_1_mubasher_disclosures", data_intel)

        # 2. Deep fusion API endpoint
        res_fusion = self.client.get("/api/signals/deep_fusion/COMI.CA")
        self.assertEqual(res_fusion.status_code, 200)
        data_fusion = res_fusion.get_json()
        self.assertEqual(data_fusion["status"], "SUCCESS")
        self.assertEqual(data_fusion["features_tensor"]["feature_dimensions"], 48)

        # 3. Unified pipeline execution endpoint
        res_pipe = self.client.post("/api/pipeline/run_unified", json={"ticker": "TMGH.CA"})
        self.assertEqual(res_pipe.status_code, 200)
        data_pipe = res_pipe.get_json()
        self.assertEqual(data_pipe["status"], "SUCCESS")
        self.assertEqual(data_pipe["ticker"], "TMGH.CA")


if __name__ == "__main__":
    unittest.main()
