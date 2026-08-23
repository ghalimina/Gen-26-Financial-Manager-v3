#!/usr/bin/env python3
# =============================================================================
# tests/test_multi_horizon_engine.py — GEN-26 Multi-Horizon Engine & API Tests
# Validates 1D, 5D, 10D, 20D, and 60D forecast objects, expected return calculations,
# target prices (T1, T2, T3), stop loss enforcement, and REST API endpoints.
# =============================================================================

import unittest
import os
import sys

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.multi_horizon_engine import MultiHorizonEngine
from dashboard.app import app


class TestMultiHorizonEngine(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()

    def test_01_all_five_horizons_present(self):
        """Verify that analysis produces forecasts across all 5 horizons."""
        res = MultiHorizonEngine.get_stock_multi_horizon_analysis("COMI.CA")
        self.assertIsNotNone(res)
        horizons = res["horizons"]
        for h in ["1D", "5D", "10D", "20D", "60D"]:
            self.assertIn(h, horizons)
            h_obj = horizons[h]
            self.assertGreater(h_obj["expected_price"], 0)
            self.assertGreater(h_obj["prob_up"], 0.5)
            self.assertGreater(h_obj["target_1"], res["current_price"])
            self.assertLess(h_obj["stop_loss"], res["current_price"])

    def test_02_term_scores_and_overall_score(self):
        """Verify that short, medium, and long term scores combine into overall score."""
        res = MultiHorizonEngine.get_stock_multi_horizon_analysis("COMI.CA")
        self.assertGreaterEqual(res["short_term_score"], 0)
        self.assertGreaterEqual(res["medium_term_score"], 0)
        self.assertGreaterEqual(res["long_term_score"], 0)
        self.assertGreaterEqual(res["overall_score"], 50)
        self.assertIn("🟢", res["explanation_ar"])

    def test_03_rankings_descending_order(self):
        """Verify that ranking returns stocks sorted by overall score descending."""
        ranks = MultiHorizonEngine.get_all_multi_horizon_rankings()
        self.assertGreaterEqual(len(ranks), 5)
        for i in range(len(ranks) - 1):
            self.assertGreaterEqual(ranks[i]["overall_score"], ranks[i+1]["overall_score"])
        self.assertEqual(ranks[0]["rank"], 1)

    def test_04_api_forecasts_endpoints(self):
        """Verify /api/forecasts and /api/forecasts/<ticker> endpoints."""
        res = self.client.get("/api/forecasts")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

        res_single = self.client.get("/api/forecasts/COMI.CA")
        self.assertEqual(res_single.status_code, 200)
        data_single = res_single.get_json()
        self.assertEqual(data_single["ticker"], "COMI.CA")
        self.assertIn("horizons", data_single)

        res_invalid = self.client.get("/api/forecasts/NONEXISTENT.CA")
        self.assertEqual(res_invalid.status_code, 404)


if __name__ == "__main__":
    unittest.main()
