#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# tests/test_insider_trading_engine.py — Unit Tests for InsiderTradingEngine
# =============================================================================

import unittest
from unittest.mock import patch
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.insider_trading_engine import InsiderTradingEngine


class TestInsiderTradingEngine(unittest.TestCase):

    def setUp(self):
        InsiderTradingEngine._cache.clear()
        InsiderTradingEngine._cache_timestamps.clear()

    @patch("core.insider_trading_engine.InsiderTradingEngine.scrape_live_insider_deals")
    def test_01_fetch_insider_deals_formatting(self, mock_scrape):
        """Verify fetch_insider_deals retrieves and formats real scraped deals."""
        mock_scrape.return_value = [
            {
                "ticker": "COMI.CA",
                "transaction_type": "BUY",
                "shares_transacted": 150_000,
                "price_egp": 136.20,
                "total_value_egp": 20_430_000.0,
                "insider_title": "عضو مجلس إدارة تنفيذي ومجموعة مرتبطة"
            }
        ]

        comi_deals = InsiderTradingEngine.fetch_insider_deals("COMI.CA")
        self.assertIsInstance(comi_deals, list)
        self.assertEqual(len(comi_deals), 1)
        first = comi_deals[0]
        self.assertEqual(first["ticker"], "COMI.CA")
        self.assertEqual(first["transaction_type"], "BUY")
        self.assertEqual(first["shares_transacted"], 150000)
        self.assertEqual(first["total_value_egp"], 20430000.0)

    def test_02_fetch_insider_deals_empty_or_unknown(self):
        """Verify fetch_insider_deals handles unknown or invalid tickers safely."""
        self.assertEqual(InsiderTradingEngine.fetch_insider_deals(""), [])
        self.assertEqual(InsiderTradingEngine.fetch_insider_deals(None), [])

    def test_03_calculate_insider_conviction_scoring(self):
        """Verify conviction scoring logic from -100 to +100."""
        # Empty deals -> 0.0
        self.assertEqual(InsiderTradingEngine.calculate_insider_conviction([]), 0.0)
        self.assertEqual(InsiderTradingEngine.calculate_insider_conviction(None), 0.0)

        # Pure Buy deals -> Strongly Positive
        buy_deals = [
            {
                "transaction_type": "BUY",
                "shares_transacted": 100_000,
                "price_egp": 100.0,
                "total_value_egp": 10_000_000.0,
                "insider_title": "مساهم رئيسي"
            }
        ]
        score_buy = InsiderTradingEngine.calculate_insider_conviction(buy_deals)
        self.assertGreater(score_buy, 50.0)
        self.assertLessEqual(score_buy, 100.0)

        # Pure Sell deals -> Strongly Negative
        sell_deals = [
            {
                "transaction_type": "SELL",
                "shares_transacted": 500_000,
                "price_egp": 10.0,
                "total_value_egp": 5_000_000.0,
                "insider_title": "عضو مجلس إدارة"
            }
        ]
        score_sell = InsiderTradingEngine.calculate_insider_conviction(sell_deals)
        self.assertLess(score_sell, -50.0)
        self.assertGreaterEqual(score_sell, -100.0)

        # Mixed deals: larger buy than sell -> net positive
        mixed_deals = [
            {
                "transaction_type": "BUY",
                "shares_transacted": 200_000,
                "price_egp": 50.0,
                "total_value_egp": 10_000_000.0,
                "insider_title": "مساهم رئيسي"
            },
            {
                "transaction_type": "SELL",
                "shares_transacted": 20_000,
                "price_egp": 50.0,
                "total_value_egp": 1_000_000.0,
                "insider_title": "مطلع"
            }
        ]
        score_mixed = InsiderTradingEngine.calculate_insider_conviction(mixed_deals)
        self.assertGreater(score_mixed, 0.0)

    @patch("core.insider_trading_engine.InsiderTradingEngine.fetch_insider_deals")
    def test_04_evaluate_insider_activity_signals(self, mock_fetch):
        """Verify evaluate_insider_activity produces expected signals and Arabic labels."""
        # 1. Strong Buy Scenario
        mock_fetch.return_value = [
            {
                "transaction_type": "BUY",
                "shares_transacted": 150_000,
                "price_egp": 100.0,
                "total_value_egp": 15_000_000.0,
                "insider_title": "عضو مجلس إدارة تنفيذي ومجموعة مرتبطة"
            }
        ]
        buy_eval = InsiderTradingEngine.evaluate_insider_activity("COMI.CA")
        self.assertEqual(buy_eval["ticker"], "COMI.CA")
        self.assertEqual(buy_eval["signal"], "STRONG_INSIDER_BUYING")
        self.assertEqual(buy_eval["action_type"], "INSIDER_BUYING")
        self.assertGreater(buy_eval["conviction_score"], 30.0)
        self.assertEqual(buy_eval["insider_action"], 1.0)
        self.assertIn("شراء", buy_eval["diagnostic_label_ar"])
        self.assertGreater(buy_eval["confidence_boost_pct"], 0.0)

        # 2. Insider Dumping Scenario
        mock_fetch.return_value = [
            {
                "transaction_type": "SELL",
                "shares_transacted": 500_000,
                "price_egp": 10.0,
                "total_value_egp": 5_000_000.0,
                "insider_title": "مساهم رئيسي"
            }
        ]
        sell_eval = InsiderTradingEngine.evaluate_insider_activity("CCAP.CA")
        self.assertEqual(sell_eval["ticker"], "CCAP.CA")
        self.assertEqual(sell_eval["signal"], "INSIDER_DUMPING")
        self.assertEqual(sell_eval["action_type"], "INSIDER_SELLING")
        self.assertLess(sell_eval["conviction_score"], -30.0)
        self.assertEqual(sell_eval["insider_action"], -1.0)
        self.assertTrue("بيع" in sell_eval["diagnostic_label_ar"] or "تخارج" in sell_eval["diagnostic_label_ar"])
        self.assertLess(sell_eval["confidence_boost_pct"], 0.0)

        # 3. Neutral / No deals
        mock_fetch.return_value = []
        neutral_eval = InsiderTradingEngine.evaluate_insider_activity("UNKNOWN.CA")
        self.assertEqual(neutral_eval["ticker"], "UNKNOWN.CA")
        self.assertEqual(neutral_eval["signal"], "NEUTRAL")
        self.assertEqual(neutral_eval["action_type"], "NEUTRAL")
        self.assertEqual(neutral_eval["conviction_score"], 0.0)
        self.assertEqual(neutral_eval["insider_action"], 0.0)
        self.assertEqual(neutral_eval["filings_count"], 0)
        self.assertIsNone(neutral_eval["latest_filing"])

    @patch("core.insider_trading_engine.InsiderTradingEngine.scrape_live_insider_deals")
    def test_05_get_market_wide_insider_deals(self, mock_scrape):
        """Verify market-wide radar returns deals sorted descending by trade value."""
        mock_scrape.return_value = [
            {"ticker": "SMALL.CA", "total_value_egp": 500_000.0},
            {"ticker": "BIG.CA", "total_value_egp": 35_000_000.0},
            {"ticker": "MED.CA", "total_value_egp": 5_000_000.0}
        ]
        top_deals = InsiderTradingEngine.get_market_wide_insider_deals(top_n=2)
        self.assertEqual(len(top_deals), 2)
        self.assertEqual(top_deals[0]["ticker"], "BIG.CA")
        self.assertEqual(top_deals[1]["ticker"], "MED.CA")

    def test_06_edge_case_and_malformed_deal_handling(self):
        """Verify calculation handles zero amounts and missing keys without raising exceptions."""
        malformed = [
            {"transaction_type": "BUY", "shares_transacted": 0, "price_egp": 0.0},
            {"transaction_type": "INVALID", "total_value_egp": -100},
            {"random_key": "val"}
        ]
        conviction = InsiderTradingEngine.calculate_insider_conviction(malformed)
        self.assertEqual(conviction, 0.0)


if __name__ == "__main__":
    unittest.main()
