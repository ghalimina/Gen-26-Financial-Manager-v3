#!/usr/bin/env python3
# =============================================================================
# tests/test_advanced_methodology_features.py — GEN-26 Advanced Features Test Suite
# Validates MACD, Bollinger Bands, ATR Dynamic Stop Loss, Retest Setup, Multi-Timeframe,
# Quality of Earnings, Correlation Matrix, Beta, Expected Downside, and Report Fields.
# =============================================================================

import os
import sys
import unittest
import json

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.technical_setup_engine import TechnicalSetupEngine
from core.live_fundamentals_engine import LiveFundamentalsEngine
from core.portfolio_correlation_engine import PortfolioCorrelationEngine
from core.multi_horizon_engine import MultiHorizonEngine
from dashboard.app import app


class TestAdvancedMethodologyFeatures(unittest.TestCase):
    """
    Test suite for all 9 newly introduced quantitative methodology enhancements.
    """

    def setUp(self):
        self.client = app.test_client()

    def test_01_macd_and_bollinger_bands_structure(self):
        """Verify TechnicalSetupEngine computes MACD and Bollinger Bands squeeze/expansion."""
        res = TechnicalSetupEngine.evaluate_technical_setup("ORAS.CA", 782.25)
        self.assertIn("macd", res)
        self.assertIn("bollinger_bands", res)
        self.assertIn("macd_hist", res["macd"])
        self.assertIn("is_squeeze", res["bollinger_bands"])
        self.assertIn("bandwidth_pct", res["bollinger_bands"])

    def test_02_retest_setup_classification(self):
        """Verify TechnicalSetupEngine recognizes BREAKOUT_RETEST_SUPPORT setup."""
        self.assertIn("BREAKOUT_RETEST_SUPPORT", TechnicalSetupEngine.SETUP_ARABIC)
        res = TechnicalSetupEngine.evaluate_technical_setup("SWDY.CA", 120.89)
        self.assertEqual(res["setup_classification"], TechnicalSetupEngine.SETUP_BREAKOUT_RETEST_SUPPORT)
        self.assertIn("expected_holding_period_ar", res)
        self.assertIn("invalidation_trigger_ar", res)

    def test_03_multi_timeframe_weekly_trend(self):
        """Verify Multi-Timeframe weekly trend confirmation filter."""
        res_comi = TechnicalSetupEngine.evaluate_technical_setup("COMI.CA", 138.80)
        self.assertIn("multi_timeframe", res_comi)
        self.assertEqual(res_comi["multi_timeframe"]["weekly_trend"], "BULLISH")
        self.assertIn("alignment_ar", res_comi["multi_timeframe"])

    def test_04_dynamic_atr_stop_loss(self):
        """Verify stop loss is dynamic based on ATR and clamped within [3.5%, 10.0%]."""
        comi_analysis = MultiHorizonEngine.get_stock_multi_horizon_analysis("COMI.CA")
        p = comi_analysis["current_price"]
        sl = comi_analysis["stop_loss"]
        loss_pct = (p - sl) / p * 100.0
        self.assertGreaterEqual(loss_pct, 3.50)
        self.assertLessEqual(loss_pct, 10.00)

    def test_05_expected_upside_and_downside_per_horizon(self):
        """Verify each horizon contains both expected_return_pct and expected_downside_pct."""
        res = MultiHorizonEngine.get_stock_multi_horizon_analysis("TMGH.CA")
        for h_key in ["1D", "5D", "10D", "20D", "60D"]:
            h = res["horizons"][h_key]
            self.assertIn("expected_return_pct", h)
            self.assertIn("expected_downside_pct", h)
            self.assertLessEqual(h["expected_downside_pct"], 0.0)

    def test_06_quality_of_earnings_analysis(self):
        """Verify LiveFundamentalsEngine evaluates Cash Flow Conversion (OCF/NI) and flags."""
        fund = LiveFundamentalsEngine.get_stock_fundamentals("COMI.CA")
        self.assertIn("ocf_to_ni", fund)
        self.assertIn("earnings_quality_rating", fund)
        self.assertIn("earnings_quality_score", fund)
        self.assertIn("earnings_quality_flag_ar", fund)
        self.assertIn("has_non_recurring_gain", fund)

    def test_07_portfolio_correlation_and_beta_engine(self):
        """Verify PortfolioCorrelationEngine computes Beta vs EGX30 and correlation matrix."""
        beta = PortfolioCorrelationEngine.get_stock_beta("COMI.CA")
        self.assertGreater(beta, 0.5)

        cluster = PortfolioCorrelationEngine.evaluate_portfolio_cluster_risk(["COMI.CA", "SWDY.CA", "TMGH.CA"])
        self.assertIn("cluster_risk", cluster)
        self.assertIn("correlation_matrix", cluster)
        self.assertIn("max_pairwise_correlation", cluster)

    def test_08_multi_horizon_engine_new_report_fields(self):
        """Verify MultiHorizonEngine includes confidence, beta, invalidation triggers, and tailored holding."""
        res = MultiHorizonEngine.get_stock_multi_horizon_analysis("ORAS.CA")
        self.assertIn("confidence_score", res)
        self.assertIn("beta_egx30", res)
        self.assertIn("invalidation_trigger_ar", res)
        self.assertIn("holding_period_ar", res)

    def test_09_api_ranking_and_correlation_endpoints(self):
        """Verify /api/ranking contains new report fields and /api/correlation works."""
        r_rank = self.client.get("/api/ranking")
        self.assertEqual(r_rank.status_code, 200)
        data = r_rank.get_json()
        self.assertGreaterEqual(len(data), 1)
        first = data[0]
        self.assertIn("confidence", first)
        self.assertIn("beta_egx30", first)
        self.assertIn("expected_downside_pct", first)
        self.assertIn("expected_holding_period", first)
        self.assertIn("invalidation_trigger", first)
        self.assertIn("quality_of_earnings", first)

        r_corr = self.client.get("/api/correlation")
        self.assertEqual(r_corr.status_code, 200)
        corr_data = r_corr.get_json()
        self.assertIn("cluster_risk", corr_data)
        self.assertIn("correlation_matrix", corr_data)


if __name__ == "__main__":
    unittest.main()
