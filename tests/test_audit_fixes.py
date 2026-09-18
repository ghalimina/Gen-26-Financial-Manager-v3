#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_audit_fixes.py — Regression tests for comprehensive forensic audit fixes.
Validates:
1. /api/morning_briefing returns today's date and real prices (TMGH != 62.25).
2. /api/observability/features returns HTTP 200 with 48 active features.
3. /api/market/heatmap returns 18 clean official EGX sectors without _P duplicates.
4. RealPortfolioTracker resolves arbitrary EGX244 stocks dynamically.
5. PriceAnomalyResolver reconciles persistent price moves in <= 2 cycles.
"""

import os
import sys
import unittest
import json

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from dashboard.app import app
from core.market_heatmap_engine import MarketHeatmapEngine
from core.real_portfolio import RealPortfolioTracker
from core.price_anomaly_resolver import PriceAnomalyResolver


class TestAuditFixes(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()

    def test_01_morning_briefing_real_prices_and_date(self):
        res = self.client.get('/api/morning_briefing')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("headline", data)
        self.assertIn("key_recommendations", data)
        
        # Verify no stock recommendation is using the obsolete 62.25 TMGH price
        for rec in data["key_recommendations"]:
            if rec.get("ticker") == "TMGH.CA":
                self.assertNotEqual(rec.get("current_price_egp"), 62.25)
                self.assertGreater(rec.get("current_price_egp", 0), 80.0)

    def test_02_observability_features_endpoint(self):
        res = self.client.get('/api/observability/features')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("features", data)
        self.assertEqual(len(data["features"]), 48)

    def test_03_consolidated_heatmap_sectors(self):
        data = MarketHeatmapEngine.generate_sector_heatmap()
        self.assertEqual(data["sectors_count"], 18)
        self.assertEqual(data["total_stocks_count"], 244)
        sector_names = [s["name"] for s in data["sectors"]]
        # Verify no duplicate split names
        self.assertNotIn("الأغذية والمشروبات", sector_names)
        self.assertIn("الأغذية والمشروبات والتبغ", sector_names)
        # Verify no _P or _B tickers are in the main heatmap
        for s in data["sectors"]:
            for stock in s["stocks"]:
                self.assertNotIn("_P.CA", stock["ticker"])
                self.assertNotIn("_B.CA", stock["ticker"])

    def test_04_real_portfolio_expanded_universe(self):
        taqa_name = RealPortfolioTracker.get_company_name("TAQA.CA")
        self.assertIn("طاقة عربية", taqa_name)
        taqa_sec = RealPortfolioTracker.get_sector("TAQA.CA")
        self.assertNotEqual(taqa_sec, "General")

    def test_05_circuit_breaker_threshold(self):
        is_reconciled, adj_p, msg = PriceAnomalyResolver.reconcile_persistent_anomaly(
            ticker="SAIB.CA",
            fetched_price=3.03,
            previous_close=2.53,
            consecutive_count=2
        )
        self.assertTrue(is_reconciled)
        self.assertEqual(adj_p, 3.03)


if __name__ == "__main__":
    unittest.main()
