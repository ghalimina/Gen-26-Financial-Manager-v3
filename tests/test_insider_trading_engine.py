#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# tests/test_insider_trading_engine.py — Unit Tests for InsiderTradingEngine
# =============================================================================

import unittest
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.insider_trading_engine import InsiderTradingEngine


class TestInsiderTradingEngine(unittest.TestCase):

    def test_01_fetch_insider_deals_known_ticker(self):
        """Verify fetch_insider_deals retrieves formatted deals for known tickers."""
        comi_deals = InsiderTradingEngine.fetch_insider_deals("COMI.CA")
        self.assertIsInstance(comi_deals, list)
        self.assertGreater(len(comi_deals), 0)
        first = comi_deals[0]
        self.assertEqual(first["ticker"], "COMI.CA")
        self.assertEqual(first["transaction_type"], "BUY")
        self.assertGreater(first["shares_transacted"], 0)
        self.assertGreater(first["total_value_egp"], 0)
        self.assertIn("insider_title", first)

        # Without .CA suffix
        swdy_deals = InsiderTradingEngine.fetch_insider_deals("SWDY")
        self.assertGreater(len(swdy_deals), 0)
        self.assertEqual(swdy_deals[0]["ticker"], "SWDY.CA")

    def test_02_fetch_insider_deals_empty_or_unknown(self):
        """Verify fetch_insider_deals handles unknown or invalid tickers safely."""
        self.assertEqual(InsiderTradingEngine.fetch_insider_deals("UNKNOWN.CA"), [])
        self.assertEqual(InsiderTradingEngine.fetch_insider_deals("INVALID_999.CA"), [])
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

    def test_04_evaluate_insider_activity_signals(self):
        """Verify evaluate_insider_activity produces expected signals and Arabic labels."""
        # Strong Buy (COMI.CA)
        comi_eval = InsiderTradingEngine.evaluate_insider_activity("COMI.CA")
        self.assertEqual(comi_eval["ticker"], "COMI.CA")
        self.assertEqual(comi_eval["signal"], "STRONG_INSIDER_BUYING")
        self.assertEqual(comi_eval["action_type"], "INSIDER_BUYING")
        self.assertGreater(comi_eval["conviction_score"], 30.0)
        self.assertEqual(comi_eval["insider_action"], 1.0)
        self.assertIn("شراء", comi_eval["diagnostic_label_ar"])
        self.assertGreater(comi_eval["confidence_boost_pct"], 0.0)

        # Insider Dumping (CCAP.CA)
        ccap_eval = InsiderTradingEngine.evaluate_insider_activity("CCAP.CA")
        self.assertEqual(ccap_eval["ticker"], "CCAP.CA")
        self.assertEqual(ccap_eval["signal"], "INSIDER_DUMPING")
        self.assertEqual(ccap_eval["action_type"], "INSIDER_SELLING")
        self.assertLess(ccap_eval["conviction_score"], -30.0)
        self.assertEqual(ccap_eval["insider_action"], -1.0)
        self.assertTrue("بيع" in ccap_eval["diagnostic_label_ar"] or "تخارج" in ccap_eval["diagnostic_label_ar"])
        self.assertLess(ccap_eval["confidence_boost_pct"], 0.0)

        # Neutral / Unknown (UNKNOWN.CA)
        unknown_eval = InsiderTradingEngine.evaluate_insider_activity("UNKNOWN.CA")
        self.assertEqual(unknown_eval["ticker"], "UNKNOWN.CA")
        self.assertEqual(unknown_eval["signal"], "NEUTRAL")
        self.assertEqual(unknown_eval["action_type"], "NEUTRAL")
        self.assertEqual(unknown_eval["conviction_score"], 0.0)
        self.assertEqual(unknown_eval["insider_action"], 0.0)
        self.assertEqual(unknown_eval["filings_count"], 0)
        self.assertIsNone(unknown_eval["latest_filing"])

    def test_05_get_market_wide_insider_deals(self):
        """Verify market-wide radar returns top 5 largest deals sorted by trade value."""
        top_deals = InsiderTradingEngine.get_market_wide_insider_deals()
        self.assertEqual(len(top_deals), 5)

        # Ensure sorted descending by total_value_egp
        values = [float(d["total_value_egp"]) for d in top_deals]
        self.assertEqual(values, sorted(values, reverse=True))

        # Check largest trade is SWDY.CA (~32M EGP)
        self.assertEqual(top_deals[0]["ticker"], "SWDY.CA")
        self.assertGreaterEqual(top_deals[0]["total_value_egp"], 30_000_000.0)

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
