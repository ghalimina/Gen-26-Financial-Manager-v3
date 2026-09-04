#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# tests/test_v2_architectural_enhancements.py — Verification Suite for V2 Quant Architecture
# Part of GEN-26 Expanded Version 2.0
# =============================================================================

import unittest
import json
from datetime import datetime, timedelta

from core.data_sources_registry import DataSourceRegistry
from core.news_deduplication_engine import NewsDeduplicationEngine
from core.market_breadth_engine import MarketBreadthEngine
from core.uncertainty_engine import UncertaintyEngine
from core.baseline_benchmark_suite import BaselineBenchmarkSuite
from core.trade_selection_model import TradeSelectionModel
from core.multi_objective_evaluator import MultiObjectiveEvaluator
from core.production_readiness_matrix import ProductionReadinessMatrix
from dashboard.app import app


class TestV2ArchitecturalEnhancements(unittest.TestCase):
    """
    Validates all Version 2.0 Architectural Enhancements:
    1. 5-Tier Data Source Registry & 3-Timestamp Governance
    2. News Deduplication & Event Clustering
    3. Market Breadth Engine
    4. Uncertainty Engine & Probabilistic Distribution
    5. 6-Standard Baseline Benchmark Suite
    6. Trade Selection Gate & Multi-Objective Evaluator
    7. Production Readiness Matrix & 5 Independent Audits
    8. Flask Observability Endpoints
    """

    def setUp(self):
        self.app_client = app.test_client()

    # -------------------------------------------------------------------------
    # 1. DATA SOURCE REGISTRY & 3-TIMESTAMP PROTOCOL
    # -------------------------------------------------------------------------
    def test_01_data_sources_registry_and_3_timestamps(self):
        tiers = DataSourceRegistry.get_all_tiers()
        self.assertIn("tier_1", tiers)
        self.assertIn("tier_2", tiers)
        self.assertIn("tier_3", tiers)
        self.assertIn("tier_4", tiers)
        self.assertIn("tier_5", tiers)

        # Reliability weights
        self.assertEqual(DataSourceRegistry.get_source_reliability_weight("EGX_OFFICIAL"), 1.00)
        self.assertEqual(DataSourceRegistry.get_source_reliability_weight("REUTERS"), 0.85)

        # 3-Timestamp Invariant Enforcement
        t_event = "2026-08-30T10:00:00"
        t_pub = "2026-08-30T10:15:00"
        t_eff = "2026-08-30T10:20:00"

        rec = {"headline": "EGX Blue Chips Rally", "price": 139.28}
        sanitized = DataSourceRegistry.enforce_3_timestamps(rec, t_event, t_pub, t_eff)

        self.assertEqual(sanitized["timestamp_audit_status"], "PASSED_3_TIMESTAMP_INVARIANT")
        self.assertGreaterEqual(sanitized["effective_time"], sanitized["publication_time"])
        self.assertGreaterEqual(sanitized["publication_time"], sanitized["event_time"])

        # Lookahead leakage check
        self.assertFalse(DataSourceRegistry.is_data_available_at(sanitized, "2026-08-30T10:10:00"))
        self.assertTrue(DataSourceRegistry.is_data_available_at(sanitized, "2026-08-30T10:25:00"))

    # -------------------------------------------------------------------------
    # 2. NEWS DEDUPLICATION & STORY CLUSTERING
    # -------------------------------------------------------------------------
    def test_02_news_deduplication_engine(self):
        raw_news = [
            {"headline": "CIB announces record earnings for Q2", "source": "REUTERS", "ticker": "COMI.CA", "sentiment_score": 0.85},
            {"headline": "Commercial International Bank posts record Q2 earnings", "source": "ZAWYA", "ticker": "COMI.CA", "sentiment_score": 0.80},
            {"headline": "البنك التجاري الدولي يحقق أرباحا قياسية", "source": "MUBASHER", "ticker": "COMI.CA", "sentiment_score": 0.82},
            {"headline": "Elsewedy signs major electrical transmission contract", "source": "ENTERPRISE", "ticker": "SWDY.CA", "sentiment_score": 0.90}
        ]

        result = NewsDeduplicationEngine.cluster_and_deduplicate(raw_news)
        self.assertEqual(result["raw_count"], 4)
        self.assertLessEqual(result["unique_clusters_count"], 3)
        self.assertGreater(result["reduction_pct"], 0.0)

        # Check cluster properties
        for clus in result["clusters"]:
            self.assertIn("cluster_sentiment_score", clus)
            self.assertIn("corroboration_confidence", clus)
            self.assertGreaterEqual(clus["corroboration_confidence"], 0.60)

    # -------------------------------------------------------------------------
    # 3. MARKET BREADTH ENGINE
    # -------------------------------------------------------------------------
    def test_03_market_breadth_engine(self):
        breadth = MarketBreadthEngine.calculate_market_breadth()
        self.assertIn("advance_decline_ratio", breadth)
        self.assertIn("pct_stocks_above_ma20", breadth)
        self.assertIn("pct_stocks_above_ma50", breadth)
        self.assertIn("sector_breadth_dispersion", breadth)
        self.assertIn("breadth_regime", breadth)
        self.assertGreater(breadth["total_universe_scanned"], 0)

    # -------------------------------------------------------------------------
    # 4. UNCERTAINTY ENGINE & PROBABILISTIC DISTRIBUTIONS
    # -------------------------------------------------------------------------
    def test_04_uncertainty_engine(self):
        # Low uncertainty test
        res_low = UncertaintyEngine.evaluate_forecast_distribution(
            ticker="COMI.CA",
            expected_return_pct=5.0,
            base_confidence=90.0,
            volatility_atr_pct=1.8,
            current_price=139.28,
            regime="STRONG_BULL"
        )
        self.assertEqual(res_low["uncertainty_tier"], "LOW")
        self.assertEqual(res_low["sizing_multiplier"], 1.00)
        self.assertGreater(res_low["prob_up_1pct"], 50.0)

        # High uncertainty / fog-of-war test
        res_high = UncertaintyEngine.evaluate_forecast_distribution(
            ticker="VOLATILE.CA",
            expected_return_pct=1.5,
            base_confidence=30.0,
            volatility_atr_pct=7.5,
            current_price=50.0,
            regime="FLASH_CRASH"
        )
        self.assertEqual(res_high["uncertainty_tier"], "HIGH")
        self.assertEqual(res_high["sizing_multiplier"], 0.00)
        self.assertEqual(res_high["trade_action"], "NO_TRADE_SAFETY_LOCK")

    # -------------------------------------------------------------------------
    # 5. 6-STANDARD BASELINE BENCHMARK SUITE
    # -------------------------------------------------------------------------
    def test_05_baseline_benchmark_suite(self):
        candidate = {
            "strategy_name": "GEN-26 Institutional Alpha",
            "oos_sharpe": 2.20,
            "annualized_return_pct": 48.0,
            "max_drawdown_pct": 8.5,
            "win_rate_pct": 68.0
        }
        res = BaselineBenchmarkSuite.evaluate_against_all_baselines(candidate)
        self.assertEqual(res["baselines_evaluated"], 6)
        self.assertGreaterEqual(res["benchmarks_beaten_count"], 5)
        self.assertTrue(res["passed_statistical_significance_hurdle"])

    # -------------------------------------------------------------------------
    # 6. TRADE SELECTION GATE & MULTI-OBJECTIVE EVALUATOR
    # -------------------------------------------------------------------------
    def test_06_trade_selection_and_multi_objective(self):
        # Eligible trade
        t_good = TradeSelectionModel.evaluate_trade_eligibility(
            ticker="COMI.CA",
            expected_return_pct=6.0,
            order_value_egp=150000,
            adv30_egp=50000000,
            uncertainty_score=0.20
        )
        self.assertTrue(t_good["is_tradeable"])
        self.assertEqual(t_good["decision"], "DECISION_TRADE_CANDIDATE")
        self.assertGreaterEqual(t_good["net_edge_pct"], 1.00)

        # Ineligible marginal trade
        t_bad = TradeSelectionModel.evaluate_trade_eligibility(
            ticker="MARGINAL.CA",
            expected_return_pct=0.90,
            order_value_egp=100000,
            adv30_egp=2000000,
            uncertainty_score=0.45
        )
        self.assertFalse(t_bad["is_tradeable"])
        self.assertEqual(t_bad["decision"], "DECISION_PASS_NO_TRADE")

        # Multi-objective fitness
        strat_metrics = {
            "strategy_name": "Robust System",
            "annualized_return_pct": 44.0,
            "oos_sharpe": 2.05,
            "degradation_pct": 14.0,
            "deflated_sharpe_ratio": 0.86,
            "max_drawdown_pct": 9.0,
            "annual_turnover_ratio": 2.1,
            "total_cost_drag_pct": 1.6,
            "cvar_99_pct": 11.0,
            "uncertainty_score": 0.22
        }
        obj_eval = MultiObjectiveEvaluator.evaluate_strategy_objective(strat_metrics)
        self.assertTrue(obj_eval["passed_multi_objective_gate"])
        self.assertGreaterEqual(obj_eval["net_objective_score"], 1.00)

    # -------------------------------------------------------------------------
    # 7. PRODUCTION READINESS MATRIX & 5 AUDITS
    # -------------------------------------------------------------------------
    def test_07_production_readiness_matrix(self):
        matrix = ProductionReadinessMatrix.compute_overall_readiness()
        self.assertEqual(matrix["layers_count"], 10)
        self.assertEqual(matrix["independent_audits_count"], 5)
        self.assertIn(matrix["production_status"], ["OPERATIONAL_ACTIVE", "INSTITUTIONAL_PRODUCTION_READY"])

    # -------------------------------------------------------------------------
    # 8. FLASK OBSERVABILITY ENDPOINTS
    # -------------------------------------------------------------------------
    def test_08_flask_observability_endpoints(self):
        r_matrix = self.app_client.get("/api/observability/readiness_matrix")
        self.assertEqual(r_matrix.status_code, 200)
        d_matrix = json.loads(r_matrix.data)
        self.assertIn("overall_readiness_score_pct", d_matrix)
        self.assertIn("layers", d_matrix)

        r_sources = self.app_client.get("/api/observability/data_sources")
        self.assertEqual(r_sources.status_code, 200)
        d_sources = json.loads(r_sources.data)
        self.assertEqual(d_sources["total_tiers"], 5)

        r_breadth = self.app_client.get("/api/observability/market_breadth")
        self.assertEqual(r_breadth.status_code, 200)
        d_breadth = json.loads(r_breadth.data)
        self.assertIn("advance_decline_ratio", d_breadth)
        self.assertIn("breadth_regime", d_breadth)


if __name__ == "__main__":
    unittest.main()
