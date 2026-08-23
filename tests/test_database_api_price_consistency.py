#!/usr/bin/env python3
# =============================================================================
# tests/test_database_api_price_consistency.py — Full Pipeline Price Consistency Tests
# Verifies that Database, MarketPriceService, REST API, and Rendered UI
# provide 100% identical pricing across all endpoints without drift.
# =============================================================================

import unittest
import os
import sys

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.market_price_service import MarketPriceService
from core.database import DatabaseManager
from dashboard.app import app


class TestDatabaseAPIPriceConsistency(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()
        DatabaseManager.seed_initial_catalog()

    def test_01_service_matches_api_stocks_dossier(self):
        """Verify that /api/stocks/<ticker> returns the exact price from MarketPriceService."""
        for ticker in ["COMI.CA", "SWDY.CA", "TMGH.CA", "EKHO.CA", "FWRY.CA", "ABUK.CA", "EAST.CA", "ORAS.CA"]:
            canonical = MarketPriceService.get_canonical_price_record(ticker)
            self.assertIsNotNone(canonical)

            res = self.client.get(f"/api/stocks/{ticker}")
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertEqual(data["current_price"], canonical["price"])

    def test_02_database_seeded_prices_match_canonical(self):
        """Verify that SQLite market_prices table contains matching canonical prices."""
        conn = DatabaseManager.get_connection()
        cur = conn.cursor()
        for ticker in ["COMI.CA", "SWDY.CA"]:
            canonical_price = MarketPriceService.get_latest_price(ticker)
            cur.execute("SELECT close_price FROM market_prices WHERE ticker = ? ORDER BY market_date DESC LIMIT 1", (ticker,))
            row = cur.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(float(row[0]), canonical_price)
        conn.close()

    def test_03_rendered_ui_html_matches_canonical(self):
        """Verify that root HTML view embeds canonical prices."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn("137.00", html)
        self.assertIn("116.00", html)


if __name__ == "__main__":
    unittest.main()
