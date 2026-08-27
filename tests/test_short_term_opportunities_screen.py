#!/usr/bin/env python3
# =============================================================================
# tests/test_short_term_opportunities_screen.py — GEN-26 10D Opportunities Tests
# Tests the 2-Week (10-Day) Short-Term Opportunities Screen logic, filters, and API.
# =============================================================================

import os
import sys
import unittest
import json

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.multi_horizon_engine import MultiHorizonEngine
from dashboard.app import app


class TestShortTermOpportunitiesScreen(unittest.TestCase):
    """
    Test suite for the 2-Week (10D) Short-Term Opportunities Screen.
    """

    def setUp(self):
        self.client = app.test_client()

    def test_01_screen_payload_structure_and_disclaimer(self):
        """Verify screen payload contains mandatory incubation disclaimer and metadata."""
        data = MultiHorizonEngine.get_short_term_10d_opportunities()
        self.assertIn("disclaimer_ar", data)
        self.assertIn("فترة الحضانة التجريبية", data["disclaimer_ar"])
        self.assertIn("horizon", data)
        self.assertIn("10D", data["horizon"])
        self.assertIn("opportunities", data)
        self.assertIn("has_sufficient_opportunities", data)

    def test_02_ranking_order_by_reward_to_downside_ratio(self):
        """Verify opportunities are ordered descending by reward_to_downside_ratio."""
        data = MultiHorizonEngine.get_short_term_10d_opportunities()
        opps = data["opportunities"]
        if len(opps) >= 2:
            for i in range(len(opps) - 1):
                self.assertGreaterEqual(
                    opps[i]["reward_to_downside_ratio"],
                    opps[i+1]["reward_to_downside_ratio"],
                    f"Order violation between rank {i+1} and {i+2}"
                )

    def test_03_disqualification_of_thin_liquidity_stocks(self):
        """Verify thin liquidity stocks (e.g. EKHO, EKHOA, BINV) are strictly excluded."""
        data = MultiHorizonEngine.get_short_term_10d_opportunities()
        opps = data["opportunities"]
        tickers = [o["ticker"] for o in opps]
        for bad_sym in ["EKHO.CA", "EKHOA.CA", "BINV.CA"]:
            self.assertNotIn(bad_sym, tickers, f"Thin liquidity stock {bad_sym} must be excluded from short-term screen.")

    def test_04_disqualification_of_downtrend_setups(self):
        """Verify DOWNTREND_PULLBACK setups are excluded."""
        data = MultiHorizonEngine.get_short_term_10d_opportunities()
        opps = data["opportunities"]
        for o in opps:
            self.assertNotEqual(o["setup_classification"], "DOWNTREND_PULLBACK")

    def test_05_presence_of_dynamic_atr_stop_and_invalidation(self):
        """Verify required stop loss, invalidation trigger, and target bounds are present."""
        data = MultiHorizonEngine.get_short_term_10d_opportunities()
        opps = data["opportunities"]
        self.assertGreaterEqual(len(opps), 1)
        sample = opps[0]
        self.assertIn("stop_loss", sample)
        self.assertIn("stop_loss_type_ar", sample)
        self.assertIn("invalidation_trigger_ar", sample)
        self.assertIn("expected_upside_10d_pct", sample)
        self.assertIn("expected_downside_10d_pct", sample)
        self.assertIn("target_price_10d", sample)
        self.assertIn("confidence", sample)

    def test_06_api_endpoint_short_term_opportunities(self):
        """Verify GET /api/opportunities/short-term endpoint returns 200 and matches logic."""
        res = self.client.get("/api/opportunities/short-term")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("disclaimer_ar", data)
        self.assertIn("opportunities", data)


if __name__ == "__main__":
    unittest.main()
