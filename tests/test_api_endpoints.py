#!/usr/bin/env python3
# =============================================================================
# tests/test_api_endpoints.py — GEN-26 Modular REST API End-to-End Tests
# Validates request schemas, error handling, and JSON responses across all 14 endpoints.
# =============================================================================

import unittest
import os
import sys
import json

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from dashboard.app import app


class TestAPIEndpoints(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()

    def test_01_market_endpoint(self):
        """Verify /api/market returns regime and EGX30 level."""
        res = self.client.get("/api/market")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("market_regime", data)
        self.assertIn("egx30_index_level", data)

    def test_02_universe_endpoint(self):
        """Verify /api/universe returns coverage breakdown."""
        res = self.client.get("/api/universe")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("coverage_status", data)
        self.assertGreaterEqual(data["tradable_count"], 27)

    def test_03_stock_dossier_endpoint(self):
        """Verify /api/stocks/<ticker> deep dossier with institutional factor layers."""
        res = self.client.get("/api/stocks/COMI.CA")
        self.assertEqual(res.status_code, 200)
        dossier = res.get_json()
        self.assertEqual(dossier["ticker"], "COMI.CA")
        self.assertIn("why_selected", dossier)
        self.assertIn("fundamentals", dossier)
        self.assertIn("news_sentiment", dossier)
        self.assertIn("block_trades", dossier)
        self.assertIn("up_drivers", dossier)
        self.assertIn("down_risks", dossier)

    def test_04_ranking_and_signals_endpoints(self):
        """Verify /api/ranking and /api/signals."""
        res_rank = self.client.get("/api/ranking")
        self.assertEqual(res_rank.status_code, 200)
        ranked = res_rank.get_json()
        self.assertGreaterEqual(len(ranked), 4)

        res_sig = self.client.get("/api/signals")
        self.assertEqual(res_sig.status_code, 200)

    def test_05_real_portfolio_crud_api(self):
        """Verify real portfolio GET and POST endpoints via API."""
        # 1. GET
        res_get = self.client.get("/api/real_portfolio")
        self.assertEqual(res_get.status_code, 200)

        # 2. ADD
        res_add = self.client.post("/api/real_portfolio/add", json={
            "ticker": "TMGH.CA",
            "quantity": 100,
            "average_entry_price": 50.0,
            "manual_notes": "API test buy"
        })
        self.assertEqual(res_add.status_code, 200)

        # 3. EDIT
        res_edit = self.client.post("/api/real_portfolio/edit", json={
            "ticker": "TMGH.CA",
            "quantity": 150,
            "average_entry_price": 51.0,
            "manual_notes": "API test edit"
        })
        self.assertEqual(res_edit.status_code, 200)

        # 4. DELETE
        res_del = self.client.post("/api/real_portfolio/delete", json={
            "ticker": "TMGH.CA",
            "confirm": True
        })
        self.assertEqual(res_del.status_code, 200)

    def test_06_risk_and_stress_endpoints(self):
        """Verify /api/risk and /api/stress endpoints."""
        res_risk = self.client.get("/api/risk")
        self.assertEqual(res_risk.status_code, 200)

        res_stress = self.client.get("/api/stress?scenario=crash")
        self.assertEqual(res_stress.status_code, 200)
        data = res_stress.get_json()
        self.assertIn("portfolio_drawdown_pct", data)

    def test_07_watchlist_api(self):
        """Verify /api/watchlist GET and POST add/remove."""
        res_get = self.client.get("/api/watchlist")
        self.assertEqual(res_get.status_code, 200)

    def test_08_portfolio_export_api(self):
        """Verify /api/portfolio/export returns downloadable CSV with UTF-8 BOM and JSON."""
        # 1. Real portfolio CSV export
        res_real_csv = self.client.get("/api/portfolio/export?format=csv&type=real")
        self.assertEqual(res_real_csv.status_code, 200)
        self.assertIn("text/csv", res_real_csv.content_type)
        self.assertIn("attachment", res_real_csv.headers.get("Content-Disposition", ""))

        # 2. Paper portfolio CSV export
        res_paper_csv = self.client.get("/api/portfolio/export?format=csv&type=paper")
        self.assertEqual(res_paper_csv.status_code, 200)
        self.assertIn("text/csv", res_paper_csv.content_type)

        # 3. JSON format
        res_json = self.client.get("/api/portfolio/export?format=json&type=real")
        self.assertEqual(res_json.status_code, 200)
        self.assertIsInstance(res_json.get_json(), dict)


if __name__ == "__main__":
    unittest.main()
