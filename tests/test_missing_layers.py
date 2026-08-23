#!/usr/bin/env python3
# =============================================================================
# tests/test_missing_layers.py — Tests for Live Fundamentals, News NLP & Block Trades
# Validates full integration into GEN-26 Multi-Horizon Forecasting Engine.
# =============================================================================

import unittest
import os
import sys

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.live_fundamentals_engine import LiveFundamentalsEngine
from core.news_sentiment_engine import NewsSentimentEngine
from core.block_trades_engine import BlockTradesEngine
from core.multi_horizon_engine import MultiHorizonEngine


class TestMissingInstitutionalLayers(unittest.TestCase):

    def setUp(self):
        self.sample_tickers = ["COMI.CA", "SWDY.CA", "TMGH.CA", "ORAS.CA", "ETEL.CA", "CCAP.CA"]

    # =========================================================================
    # 1. Live Fundamentals Engine Tests
    # =========================================================================
    def test_01_fundamentals_retrieval(self):
        """Verify fundamental metrics retrieval and normalization."""
        for t in self.sample_tickers:
            f = LiveFundamentalsEngine.get_stock_fundamentals(t)
            self.assertEqual(f["ticker"], t)
            self.assertIn("pe_ratio", f)
            self.assertIn("pb_ratio", f)
            self.assertIn("dividend_yield_pct", f)
            self.assertIn("roe_pct", f)
            self.assertIn("debt_to_equity", f)
            self.assertIn("eps_growth_pct", f)
            self.assertGreaterEqual(f["fundamental_score"], 0.0)
            self.assertLessEqual(f["fundamental_score"], 100.0)

    def test_02_fundamentals_score_helper(self):
        """Verify get_fundamental_score helper returns expected range."""
        score = LiveFundamentalsEngine.get_fundamental_score("COMI.CA")
        self.assertGreater(score, 60.0)
        self.assertLessEqual(score, 100.0)

    # =========================================================================
    # 2. News & Disclosures NLP Engine Tests
    # =========================================================================
    def test_03_news_sentiment_retrieval(self):
        """Verify news sentiment impact scoring."""
        comi_sent = NewsSentimentEngine.get_sentiment_impact("COMI.CA")
        self.assertEqual(comi_sent["ticker"], "COMI.CA")
        self.assertEqual(comi_sent["sentiment_label"], NewsSentimentEngine.SENTIMENT_POSITIVE)
        self.assertTrue(comi_sent["is_catalyst"])
        self.assertGreater(comi_sent["alpha_shock_pct"], 0.0)

        ccap_sent = NewsSentimentEngine.get_sentiment_impact("CCAP.CA")
        self.assertEqual(ccap_sent["ticker"], "CCAP.CA")
        self.assertEqual(ccap_sent["sentiment_label"], NewsSentimentEngine.SENTIMENT_NEGATIVE)
        self.assertTrue(ccap_sent["is_risk_event"])
        self.assertLess(ccap_sent["alpha_shock_pct"], 0.0)

    def test_04_arbitrary_headline_nlp_scoring(self):
        """Verify text NLP sentiment classifier on synthetic Arabic/English headlines."""
        pos = NewsSentimentEngine.score_text_sentiment("تحقيق نمو قياسي في صافي أرباح الربع الثاني وتوزيعات أرباح استثنائية")
        self.assertEqual(pos["label"], NewsSentimentEngine.SENTIMENT_POSITIVE)
        self.assertGreater(pos["score"], 0.0)

        neg = NewsSentimentEngine.score_text_sentiment("تراجع حاد في الأرباح وتكبد خسائر تشغيلية نتيجة ارتفاع الديون")
        self.assertEqual(neg["label"], NewsSentimentEngine.SENTIMENT_NEGATIVE)
        self.assertLess(neg["score"], 0.0)

    # =========================================================================
    # 3. Block Trades & Large Order Detector Tests
    # =========================================================================
    def test_05_block_trade_detection_routine(self):
        """Verify block trade evaluation on standard tickers."""
        res = BlockTradesEngine.detect_block_trades("COMI.CA")
        self.assertEqual(res["ticker"], "COMI.CA")
        self.assertIn("has_block_trades", res)
        self.assertIn("ticket_multiple", res)
        self.assertIn("classification", res)

    def test_06_block_trade_smart_money_vs_distribution(self):
        """Verify classification of smart money accumulation vs distribution."""
        # Smart money inflow: block size 300k shares with +2.0% price jump
        inflow = BlockTradesEngine.detect_block_trades("COMI.CA", current_price=140.0, simulated_block_size=300000)
        self.assertEqual(inflow["classification"], BlockTradesEngine.SIGNAL_SMART_MONEY_INFLOW)
        self.assertGreater(inflow["block_alpha_impact"], 0.0)

        # Distribution pressure: block size 300k shares with -3.0% price drop
        outflow = BlockTradesEngine.detect_block_trades("COMI.CA", current_price=130.0, simulated_block_size=300000)
        self.assertEqual(outflow["classification"], BlockTradesEngine.SIGNAL_DISTRIBUTION_PRESSURE)
        self.assertLess(outflow["block_alpha_impact"], 0.0)

    def test_07_scan_all_block_trades(self):
        """Verify universe scan of block executions."""
        scan = BlockTradesEngine.scan_all_block_trades()
        self.assertGreaterEqual(scan["total_universe"], 24)
        self.assertIn("blocks_count", scan)
        self.assertIn("smart_money_count", scan)
        self.assertIn("distribution_count", scan)

    # =========================================================================
    # 4. Multi-Horizon Engine Factor Integration Tests
    # =========================================================================
    def test_08_multi_horizon_full_factor_payload(self):
        """Verify that multi-horizon analysis payload contains all newly added layers."""
        analysis = MultiHorizonEngine.get_stock_multi_horizon_analysis("COMI.CA")
        self.assertIsNotNone(analysis)
        self.assertIn("fundamentals", analysis)
        self.assertIn("news_sentiment", analysis)
        self.assertIn("block_trades", analysis)
        self.assertIn("up_drivers", analysis)
        self.assertIn("down_risks", analysis)

        # Check driver factors exist
        driver_factors = [d["factor"] for d in analysis["up_drivers"]]
        self.assertTrue(any("Fundamental" in f for f in driver_factors))
        self.assertTrue(any("Corporate Disclosure" in f or "News" in f for f in driver_factors))

    def test_09_multi_horizon_rankings_with_missing_layers(self):
        """Verify cross-sectional ranking produces complete factor attribution across all stocks."""
        rankings = MultiHorizonEngine.get_all_multi_horizon_rankings(universe="core")
        self.assertGreaterEqual(len(rankings), 24)
        for r in rankings:
            self.assertIn("fundamentals", r)
            self.assertIn("news_sentiment", r)
            self.assertIn("block_trades", r)
            self.assertIn("decision", r)


if __name__ == "__main__":
    unittest.main()
