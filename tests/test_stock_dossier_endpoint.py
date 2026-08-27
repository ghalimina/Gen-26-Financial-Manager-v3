#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import unittest
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

os.environ["FLASK_TESTING"] = "1"
WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from dashboard.app import app


class TestStockDossierEndpoint(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()

    def test_01_stock_dossier_comi(self):
        """Verify GET /api/stocks/COMI.CA returns all required keys and numeric prices."""
        res = self.client.get('/api/stocks/COMI.CA')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["ticker"], "COMI.CA")
        self.assertIn("company_name", data)
        self.assertIn("current_price", data)
        self.assertIsInstance(data["current_price"], (int, float))
        self.assertGreater(data["current_price"], 0)
        self.assertIn("entry_zone", data)
        self.assertIn("stop_loss", data)
        self.assertIsInstance(data["stop_loss"], (int, float))
        self.assertIn("horizons", data)
        self.assertIsInstance(data["horizons"], dict)
        for h in ["1D", "5D", "10D", "20D", "60D"]:
            self.assertIn(h, data["horizons"])
            h_data = data["horizons"][h]
            self.assertIn("target_1", h_data)
            self.assertIn("expected_return_pct", h_data)
            self.assertIn("prob_up", h_data)

    def test_02_stock_dossier_swdy(self):
        """Verify GET /api/stocks/SWDY.CA returns proper structure."""
        res = self.client.get('/api/stocks/SWDY.CA')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["ticker"], "SWDY.CA")
        self.assertIn("current_price", data)
        self.assertIn("stop_loss", data)

    def test_03_ranking_endpoint_structure(self):
        """Verify GET /api/ranking returns structured list with both Arabic name and ticker."""
        res = self.client.get('/api/ranking?universe=all')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        first = data[0]
        self.assertIn("ticker", first)
        self.assertIn("company_name", first)
        self.assertIn("current_price", first)
        self.assertIn("entry_zone", first)
        self.assertIn("target_price", first)
        self.assertIn("stop_loss", first)


if __name__ == "__main__":
    unittest.main()
