#!/usr/bin/env python3
# =============================================================================
# tests/test_market_data_truth.py — Market Data Truth & Provenance Validation Tests
# Validates distinct separation between official EOD, unadjusted, adjusted, bid, ask,
# and verifies that only verified assets are eligible for ranking.
# =============================================================================

import unittest
import os
import sys

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.market_data_truth import MarketDataTruthEngine


class TestMarketDataTruth(unittest.TestCase):

    def test_01_truth_records_separation_of_price_types(self):
        """Verify that official EOD, unadjusted, adjusted, and vwap prices are explicitly distinguished."""
        records = MarketDataTruthEngine.get_all_truth_dossiers()
        self.assertGreaterEqual(len(records), 8)

        for r in records:
            self.assertIn("official_eod_price", r)
            self.assertIn("unadjusted_close", r)
            self.assertIn("adjusted_close", r)
            self.assertIn("bid", r)
            self.assertIn("ask", r)
            self.assertIn("vwap", r)
            self.assertEqual(r["currency"], "EGP")
            self.assertEqual(r["truth_status"], MarketDataTruthEngine.PRICE_STATUS_VERIFIED)
            self.assertTrue(r["eligible_for_ranking"])

    def test_02_freshness_audit_gate(self):
        """Verify that price freshness gate evaluates validity and eligibility."""
        audit = MarketDataTruthEngine.audit_price_freshness("COMI.CA")
        self.assertEqual(audit["status"], "VERIFIED")
        self.assertTrue(audit["eligible"])

        missing = MarketDataTruthEngine.audit_price_freshness("NONEXISTENT.CA")
        self.assertEqual(missing["status"], "MISSING")
        self.assertFalse(missing["eligible"])


if __name__ == "__main__":
    unittest.main()
