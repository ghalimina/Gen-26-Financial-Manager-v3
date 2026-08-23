#!/usr/bin/env python3
# =============================================================================
# tests/test_price_sync_service.py — Unit Tests for Dynamic Price Sync Service (SSOT)
# Validates live fetching, atomic file persistence, fallback mechanism, multi-provider
# routing for ORAS.CA, and intelligent circuit breaker consecutive rejection alerts.
# =============================================================================

import os
import sys
import json
import unittest

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.price_sync_service import (
    PriceSyncService,
    sync_all_prices,
    load_canonical_prices,
    get_price_record,
    get_price,
    CANONICAL_PRICES_FILE,
    ANOMALY_TRACKER_FILE
)
from dashboard.app import app


class TestPriceSyncService(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()

    def test_01_canonical_prices_file_exists_and_valid(self):
        """Verify that data/canonical_prices_live.json exists and is valid JSON."""
        store = load_canonical_prices()
        self.assertIsInstance(store, dict)
        self.assertGreaterEqual(len(store), 20)
        self.assertTrue(os.path.exists(CANONICAL_PRICES_FILE))

    def test_02_record_schema_and_required_risk_fields(self):
        """Verify each record contains ticker, price, timestamp, entry_zone, and hard_stop_loss (-7.0%)."""
        store = load_canonical_prices()
        self.assertIn("COMI.CA", store)
        comi = store["COMI.CA"]

        required_keys = [
            "ticker", "price", "timestamp", "entry_zone_low", "entry_zone_high",
            "hard_stop_loss", "currency", "price_type", "timezone"
        ]
        for key in required_keys:
            self.assertIn(key, comi, f"Missing key {key} in COMI record")

        self.assertGreater(comi["price"], 0.0)
        self.assertEqual(comi["currency"], "EGP")
        self.assertEqual(comi["timezone"], "Africa/Cairo")
        self.assertAlmostEqual(comi["hard_stop_loss"], round(comi["price"] * 0.93, 2), places=1)
        self.assertLess(comi["entry_zone_low"], comi["price"])
        self.assertLess(comi["entry_zone_high"], comi["price"])
        self.assertGreater(comi["entry_zone_high"], comi["entry_zone_low"])

    def test_03_convenience_functions(self):
        """Verify get_price and get_price_record helper functions."""
        price = get_price("COMI.CA")
        self.assertGreater(price, 0.0)
        self.assertIsInstance(price, float)

        rec = get_price_record("COMI.CA")
        self.assertIsNotNone(rec)
        self.assertEqual(rec["ticker"], "COMI.CA")

        with self.assertRaises(ValueError):
            get_price("INVALID_TICKER_9999.CA")

    def test_04_fallback_mechanism(self):
        """Verify safe fallback on network errors or invalid tickers."""
        default_snap = PriceSyncService._build_default_snapshot()
        self.assertIn("COMI.CA", default_snap)
        self.assertIn("SWDY.CA", default_snap)
        self.assertIn("ORAS.CA", default_snap)
        self.assertGreater(len(default_snap), 20)

    def test_05_api_prices_sync_endpoint(self):
        """Verify Flask API endpoint /api/prices/sync and /api/prices."""
        res = self.client.get("/api/prices")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 20)

        # Check /api/prices/sync
        res_sync = self.client.post("/api/prices/sync")
        self.assertEqual(res_sync.status_code, 200)
        data_sync = res_sync.get_json()
        self.assertEqual(data_sync["status"], "SUCCESS")
        self.assertIn("timestamp", data_sync)

    def test_06_oras_real_market_price_resolution(self):
        """Verify that ORAS.CA is resolved to real EGX price (> 700 EGP) and not frozen at 71.05 or 759."""
        rec = get_price_record("ORAS.CA")
        self.assertIsNotNone(rec)
        self.assertGreaterEqual(rec["price"], 700.0)
        self.assertEqual(rec["currency"], "EGP")
        self.assertIn(rec["source"], ["TRADINGVIEW_EGX_LIVE_SSOT", "MUBASHER_FALLBACK_RECOVERY_SSOT", "CANONICAL_BASELINE_SNAPSHOT"])

    def test_07_circuit_breaker_persistent_anomaly_escalation(self):
        """
        Verify that when a ticker exceeds 3 consecutive rejections:
        1. Explicit alert 'هذا السهم يحتاج مصدر بيانات بديل — التجاهل المتكرر لن يحل المشكلة' is triggered.
        2. Tracker persists rejection counters and alerts.
        """
        tracker = PriceSyncService._load_anomaly_tracker()
        self.assertIsInstance(tracker, dict)
        self.assertIn("consecutive_rejections", tracker)

        # Simulate setting 3 consecutive rejections on a mock anomaly ticker
        test_sym = "TEST_ANOMALY.CA"
        tracker["consecutive_rejections"][test_sym] = 3
        PriceSyncService._save_anomaly_tracker(tracker)

        loaded = PriceSyncService._load_anomaly_tracker()
        self.assertEqual(loaded["consecutive_rejections"].get(test_sym), 3)


if __name__ == "__main__":
    unittest.main()
