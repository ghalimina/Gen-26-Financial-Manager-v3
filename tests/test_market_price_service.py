#!/usr/bin/env python3
# =============================================================================
# tests/test_market_price_service.py — Market Price Service Truth & Provenance Tests
# Validates SSoT Canonical Price contract, currency validation (EGP),
# raw unadjusted flag, timestamp freshness, and external price reconciliation.
# =============================================================================

import unittest
import os
import sys

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.market_price_service import MarketPriceService


class TestMarketPriceService(unittest.TestCase):

    def test_01_canonical_price_record_schema(self):
        """Verify that every canonical price record satisfies the full data contract."""
        records = MarketPriceService.get_all_canonical_prices()
        self.assertGreaterEqual(len(records), 8)

        for rec in records:
            self.assertIn("ticker", rec)
            self.assertIn("company_name", rec)
            self.assertIn("price", rec)
            self.assertGreater(rec["price"], 0.0)
            self.assertEqual(rec["currency"], "EGP")
            self.assertIn(rec["price_type"], ["OFFICIAL_LAST_CLOSE", "CROSS_VERIFIED_REAL_DATA", "SINGLE_SOURCE_ONLY"])
            self.assertFalse(rec["is_adjusted"], "Tradable price must be raw unadjusted")
            self.assertIn("timestamp", rec)
            self.assertEqual(rec["timezone"], "Africa/Cairo")
            self.assertIn(rec["freshness"], ["FRESH_EOD_VERIFIED", "STALE_FALLBACK_SNAPSHOT", "FRESH_LIVE_QUOTE", "FRESH_LIVE_SSOT", "FRESH_LIVE_TICK", "PRICE_ANOMALY_FLAGGED"])
            self.assertIsInstance(rec["is_real_time"], bool)

    def test_02_get_latest_price_helper(self):
        """Verify get_latest_price retrieves exact positive price."""
        p = MarketPriceService.get_latest_price("COMI.CA")
        self.assertGreater(p, 50.0)

        with self.assertRaises(ValueError):
            MarketPriceService.get_latest_price("UNKNOWN_TICKER.CA")

    def test_03_reconcile_with_external_reference(self):
        """Verify reconciliation against external broker feed (e.g. Thndr)."""
        current_p = MarketPriceService.get_latest_price("COMI.CA")
        res = MarketPriceService.reconcile_with_external_reference("COMI.CA", external_price=current_p - 1.0, external_source="Thndr")
        self.assertEqual(res["ticker"], "COMI.CA")
        self.assertEqual(res["gen26_price"], current_p)
        self.assertEqual(res["external_reference_price"], current_p - 1.0)
        self.assertAlmostEqual(res["absolute_difference"], 1.00)
        self.assertIn("root_cause", res)


if __name__ == "__main__":
    unittest.main()
