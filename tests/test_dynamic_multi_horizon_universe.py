#!/usr/bin/env python3
# =============================================================================
# tests/test_dynamic_multi_horizon_universe.py — Dynamic MultiHorizon & API Tests
# Verifies dynamic scoring, universe filtering, and REST API output.
# =============================================================================

import os
import sys
import unittest

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.multi_horizon_engine import MultiHorizonEngine
from core.egx_universe_loader import EGXUniverseLoader
from dashboard.app import app


class TestDynamicMultiHorizonUniverse(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()

    def test_01_dynamic_stock_scoring_for_all_universe(self):
        """Verify dynamic scoring works for representative sample in EGXUniverseLoader."""
        all_tickers = list(dict.fromkeys(EGXUniverseLoader.get_tickers("all")[:20] + EGXUniverseLoader.get_tickers("egx30")[:10]))
        for sym in all_tickers:
            res = MultiHorizonEngine.get_stock_multi_horizon_analysis(sym)
            self.assertIsNotNone(res, f"Failed to score ticker {sym}")
            self.assertEqual(res["ticker"], sym)
            if res.get("current_price") is not None:
                self.assertGreater(res["current_price"], 0.0)
                self.assertLess(res["stop_loss"], res["current_price"])
                self.assertGreaterEqual(res["stop_loss"], round(res["current_price"] * 0.89, 2))
                self.assertIn("–", res["entry_zone"])
            else:
                self.assertIn(res["status"], ["DATA_INSUFFICIENT", "ILLIQUID"])
            self.assertGreaterEqual(res["overall_score"], 0.0)
            self.assertLessEqual(res["overall_score"], 100.0)
            self.assertIn("20D", res["horizons"])

    def test_02_rankings_universe_filters(self):
        """Verify get_all_multi_horizon_rankings filters correctly."""
        all_ranks = MultiHorizonEngine.get_all_multi_horizon_rankings(universe="all")
        egx30_ranks = MultiHorizonEngine.get_all_multi_horizon_rankings(universe="egx30")
        egx70_ranks = MultiHorizonEngine.get_all_multi_horizon_rankings(universe="egx70")

        self.assertGreaterEqual(len(all_ranks), len(egx30_ranks))
        self.assertGreater(len(egx30_ranks), 0)
        self.assertGreater(len(egx70_ranks), 0)

        # Check sequential ranks
        for idx, item in enumerate(all_ranks, start=1):
            self.assertEqual(item["rank"], idx)

        # Verify scores are sorted descending
        scores = [r["overall_score"] for r in all_ranks]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_03_api_rankings_query_param(self):
        """Verify /api/rankings responds to ?universe=egx30 and ?universe=egx70."""
        res_default = self.client.get("/api/rankings")
        self.assertEqual(res_default.status_code, 200)
        data_default = res_default.get_json()
        self.assertGreaterEqual(len(data_default), 20)

        res_30 = self.client.get("/api/rankings?universe=egx30")
        self.assertEqual(res_30.status_code, 200)
        data_30 = res_30.get_json()
        self.assertGreaterEqual(len(data_30), 20)

        res_70 = self.client.get("/api/rankings?universe=egx70")
        self.assertEqual(res_70.status_code, 200)
        data_70 = res_70.get_json()
        self.assertGreaterEqual(len(data_70), 10)

        # Verify all returned records have required keys
        sample = data_30[0]
        for key in ["rank", "ticker", "company_name", "current_price", "entry_price", "target_price", "stop_loss", "alpha_score", "recommendation", "action"]:
            self.assertIn(key, sample)

    def test_04_explicit_ticker_list_scoring(self):
        """Verify custom ticker list ranking."""
        custom_list = ["EFIH.CA", "POUL.CA", "COMI.CA"]
        ranks = MultiHorizonEngine.get_all_multi_horizon_rankings(tickers=custom_list)
        self.assertEqual(len(ranks), 3)
        self.assertEqual(ranks[0]["rank"], 1)
        self.assertEqual(ranks[1]["rank"], 2)
        self.assertEqual(ranks[2]["rank"], 3)


if __name__ == "__main__":
    unittest.main()
