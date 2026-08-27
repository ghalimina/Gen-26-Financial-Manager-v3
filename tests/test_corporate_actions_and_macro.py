#!/usr/bin/env python3
# =============================================================================
# tests/test_corporate_actions_and_macro.py — GEN-26 Corporate Actions & Macro Tests
# Tests CorporateActionsCalendar, MacroIntelligenceEngine, and their integration.
# =============================================================================

import os
import sys
import unittest
import json

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.corporate_actions_calendar import CorporateActionsCalendar, ActionType
from core.macro_intelligence_engine import MacroIntelligenceEngine
from core.multi_horizon_engine import MultiHorizonEngine
from dashboard.app import app


class TestCorporateActionsAndMacro(unittest.TestCase):
    """
    Validation test suite for Corporate Actions Calendar and Macro Factor Engine.
    """

    def setUp(self):
        self.client = app.test_client()

    def test_01_corporate_actions_calendar_loading(self):
        """Verify that CorporateActionsCalendar loads valid events and schemas."""
        events = CorporateActionsCalendar.load_events()
        self.assertIsInstance(events, list)
        self.assertGreaterEqual(len(events), 5)
        
        # Check required fields
        sample = events[0]
        self.assertIn("ticker", sample)
        self.assertIn("action_type", sample)
        self.assertIn("ex_date", sample)
        self.assertIn("description_ar", sample)

    def test_02_get_events_for_ticker(self):
        """Verify retrieving specific ticker events (e.g. ORAS.CA & COMI.CA)."""
        oras_evs = CorporateActionsCalendar.get_events_for_ticker("ORAS.CA")
        self.assertGreaterEqual(len(oras_evs), 1)
        self.assertTrue(all(e["ticker"] == "ORAS.CA" for e in oras_evs))

        comi_evs = CorporateActionsCalendar.get_events_for_ticker("COMI.CA")
        self.assertGreaterEqual(len(comi_evs), 1)

    def test_03_pre_trade_hazard_evaluation(self):
        """Verify hazard evaluation on theoretical dividend adjustment."""
        hazard = CorporateActionsCalendar.evaluate_pre_trade_corporate_hazard("ORAS.CA", current_price=782.25)
        self.assertIn("has_imminent_event", hazard)
        self.assertIn("theoretical_adjusted_price", hazard)
        self.assertIn("alpha_multiplier", hazard)

    def test_04_macro_intelligence_state(self):
        """Verify that MacroIntelligenceEngine loads rates, USD/EGP, and commodities with timestamps."""
        macro = MacroIntelligenceEngine.load_macro_state()
        indicators = macro.get("indicators", {})
        self.assertIn("cbe_corridor_rate_pct", indicators)
        self.assertIn("usd_egp_rate", indicators)
        self.assertIn("brent_oil_usd", indicators)
        self.assertGreater(indicators["cbe_corridor_rate_pct"]["value"], 15.0)
        self.assertGreater(indicators["usd_egp_rate"]["value"], 40.0)
        self.assertIn("last_updated", indicators["cbe_corridor_rate_pct"])
        self.assertIn("last_updated", indicators["usd_egp_rate"])

    def test_05_macro_sector_sensitivities(self):
        """Verify sector sensitivity calculations for Banking and Materials."""
        # Banking should have positive rate sensitivity
        bank_macro = MacroIntelligenceEngine.evaluate_stock_macro_alpha("COMI.CA", "الخدمات المالية والبنوك")
        self.assertGreater(bank_macro["rate_sensitivity"], 0.0)
        self.assertGreaterEqual(bank_macro["macro_score"], 60.0)

        # Basic Materials should have high FX and Commodity sensitivity
        mat_macro = MacroIntelligenceEngine.evaluate_stock_macro_alpha("ABUK.CA", "الموارد الأساسية والكيماويات")
        self.assertGreater(mat_macro["fx_sensitivity"], 0.3)
        self.assertGreater(mat_macro["commodity_sensitivity"], 0.2)

    def test_06_multi_horizon_engine_integration(self):
        """Verify that MultiHorizonEngine analysis contains macro and corporate hazard fields."""
        res = MultiHorizonEngine.get_stock_multi_horizon_analysis("ORAS.CA")
        self.assertIsNotNone(res)
        self.assertIn("macro_intelligence", res)
        self.assertIn("corporate_hazard", res)
        self.assertIn("target_1_bounds", res["horizons"]["20D"])
        
        # Check target bounds
        bounds = res["horizons"]["20D"]["target_1_bounds"]
        self.assertIn("low", bounds)
        self.assertIn("high", bounds)
        self.assertLessEqual(bounds["low"], bounds["high"])

    def test_07_api_corporate_actions_endpoint(self):
        """Verify GET /api/corporate_actions and /api/corporate_actions?ticker=ORAS.CA."""
        r_all = self.client.get("/api/corporate_actions")
        self.assertEqual(r_all.status_code, 200)
        data_all = r_all.get_json()
        self.assertIn("all_events", data_all)
        self.assertIn("upcoming_events", data_all)

        r_oras = self.client.get("/api/corporate_actions?ticker=ORAS.CA")
        self.assertEqual(r_oras.status_code, 200)
        data_oras = r_oras.get_json()
        self.assertIsInstance(data_oras, list)

    def test_08_api_macro_endpoint(self):
        """Verify GET /api/macro endpoint returns valid state."""
        res = self.client.get("/api/macro")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("indicators", data)
        self.assertIn("cbe_corridor_rate_pct", data["indicators"])
        self.assertIn("usd_egp_rate", data["indicators"])

    def test_09_api_ranking_contains_macro_and_hazard(self):
        """Verify GET /api/ranking includes macro_headline and corporate_hazard."""
        res = self.client.get("/api/ranking")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertGreaterEqual(len(data), 1)
        first = data[0]
        self.assertIn("macro_headline", first)
        self.assertIn("corporate_hazard", first)
        self.assertIn("target_bounds", first)


if __name__ == "__main__":
    unittest.main()
