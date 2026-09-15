#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# tests/test_direct_feed_and_anomaly.py — Unit Tests for Phase 1 Direct Feeds & Anomaly Resolver
# Validates:
# 1. Automated Stock Split & Par Value reduction recognition (PriceAnomalyResolver).
# 2. Persistent Anomaly escalation and reconciliation protocol.
# 3. Direct Real-time Egyptian Market Data Feed schema & latency (EGXDirectFeedService).
# 4. Live Market Breadth calculation (Advances/Declines/Sentiment).
# =============================================================================

import os
import sys
import unittest

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.price_anomaly_resolver import PriceAnomalyResolver
from core.egx_direct_feed_service import EGXDirectFeedService


class TestDirectFeedAndAnomaly(unittest.TestCase):

    def test_01_stock_split_10_to_1_detection(self):
        """Verify 10:1 split is recognized and previous close adjusted."""
        # Previous close 100.0, fetched post-split price 10.2 (~10:1 reduction)
        res = PriceAnomalyResolver.analyze_price_discrepancy("TEST.CA", 10.2, 100.0)
        self.assertTrue(res["is_corporate_action"])
        self.assertEqual(res["action_type"], "REVERSE_SPLIT_10_TO_1")
        self.assertEqual(res["adjusted_previous_close"], 10.0)
        self.assertGreaterEqual(res["confidence"], 0.9)

    def test_02_stock_split_2_to_1_detection(self):
        """Verify 2:1 split is recognized and previous close adjusted."""
        # Previous close 50.0, fetched post-split price 25.1
        res = PriceAnomalyResolver.analyze_price_discrepancy("TEST.CA", 25.1, 50.0)
        self.assertTrue(res["is_corporate_action"])
        self.assertEqual(res["action_type"], "REVERSE_SPLIT_2_TO_1")
        self.assertEqual(res["adjusted_previous_close"], 25.0)

    def test_03_bioc_capital_reduction_detection(self):
        """Verify BIOC historical anomaly is resolved via registered ratio."""
        # BIOC fetched ~273 EGP vs old nominal ~22.5 EGP
        res = PriceAnomalyResolver.analyze_price_discrepancy("BIOC.CA", 273.78, 22.50)
        self.assertTrue(res["is_corporate_action"])
        self.assertIn("BIOC", res["action_type"])
        self.assertAlmostEqual(res["adjusted_previous_close"], 274.39, places=1)

    def test_04_persistent_anomaly_escalation(self):
        """Verify rejections >= 5 trigger persistent reconciliation."""
        reconciled, adj_p, msg = PriceAnomalyResolver.reconcile_persistent_anomaly(
            ticker="PERSIST.CA",
            fetched_price=22.4,
            previous_close=8.0,
            consecutive_count=5
        )
        self.assertTrue(reconciled)
        self.assertEqual(adj_p, 22.4)
        self.assertIn("تسوية سعرية اضطرارية", msg)

    def test_05_egx_direct_quote_schema(self):
        """Verify EGXDirectFeedService returns structured live quote for active ticker."""
        quote = EGXDirectFeedService.get_live_quote("COMI.CA")
        self.assertIsNotNone(quote)
        self.assertEqual(quote["ticker"], "COMI.CA")
        self.assertGreater(quote["price"], 0.0)
        self.assertGreater(quote["previous_close"], 0.0)
        self.assertIn("volume", quote)
        self.assertTrue(quote["is_real_time"])

    def test_06_market_breadth_metrics(self):
        """Verify EGX market breadth computation."""
        breadth = EGXDirectFeedService.get_market_breadth()
        self.assertIn("advancers", breadth)
        self.assertIn("decliners", breadth)
        self.assertIn("market_sentiment", breadth)
        self.assertIn(breadth["market_sentiment"], ["BULLISH", "BEARISH", "NEUTRAL"])


if __name__ == "__main__":
    unittest.main()
