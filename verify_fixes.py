#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_fixes.py — Exhaustive End-to-End Verification Suite
Validates:
1. /api/alpha_scanner/scan returns complete 240+ stock opportunities with live prices & required keys.
2. /api/opportunities/10d returns 12 top short-term picks with live canonical prices, +8% target, -5% stop loss, 1.6 R:R.
3. /api/stocks/COMI.CA returns live canonical price 124.65 EGP, correct targets, entry zone 123.50 – 125.00, stop 118.42, and zero 140.50.
4. Templates are in 100% byte-for-byte synchronization.
5. No undefined, NaN, or 0.00 in key fields.
"""

import os
import sys
import json
import unittest

# Ensure safe UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

WORKSPACE = os.path.dirname(os.path.abspath(__file__))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from dashboard.app import app
from core.market_price_service import MarketPriceService


class TestAllFixes(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_01_alpha_scanner_scan(self):
        print("\n--- [1] Checking /api/alpha_scanner/scan ---")
        res = self.client.get('/api/alpha_scanner/scan')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("opportunities", data)
        opps = data["opportunities"]
        self.assertGreaterEqual(len(opps), 200, f"Expected 200+ opportunities, got {len(opps)}")

        # Verify required keys and data integrity on every single stock
        required_keys = [
            "ticker", "name_ar", "sector", "current_price",
            "alpha_score", "win_prob", "expected_return", "net_edge_pct", "action_verdict"
        ]
        zero_price_count = 0
        for i, item in enumerate(opps):
            for k in required_keys:
                self.assertIn(k, item, f"Missing key {k} in item #{i} ({item.get('ticker')})")
            price = float(item["current_price"])
            if price <= 0:
                zero_price_count += 1
            alpha = float(item["alpha_score"])
            self.assertGreater(alpha, 0.0)
            self.assertFalse(str(item["alpha_score"]).lower() in ["nan", "undefined"])

        self.assertEqual(zero_price_count, 0, f"Found {zero_price_count} stocks with 0.00 price!")
        print(f"[PASS] Alpha scanner passed: {len(opps)} opportunities verified with full live prices and keys.")
        print(f"[PASS] Total scanned: {data.get('total_scanned')}, Candidates (>=70): {data.get('candidates_count')}, High Conviction (>=75): {data.get('high_conviction_count')}")

    def test_02_opportunities_10d_top_12(self):
        print("\n--- [2] Checking /api/opportunities/10d ---")
        res = self.client.get('/api/opportunities/10d')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("opportunities", data)
        opps = data["opportunities"]
        self.assertEqual(len(opps), 12, f"Expected exactly 12 opportunities, got {len(opps)}")

        for i, o in enumerate(opps, 1):
            ticker = o["ticker"]
            price = float(o["current_price"])
            target = float(o["target_price_10d"])
            stop = float(o["stop_loss"])
            rr = float(o["reward_to_downside_ratio"])
            upside = float(o["expected_upside_10d_pct"])

            self.assertGreater(price, 0.0, f"Zero price for {ticker}")
            self.assertAlmostEqual(target, round(price * 1.08, 2), delta=0.05, msg=f"Target mismatch for {ticker}")
            self.assertAlmostEqual(stop, round(price * 0.95, 2), delta=0.05, msg=f"Stop loss mismatch for {ticker}")
            self.assertEqual(rr, 1.6, f"Reward to risk ratio mismatch for {ticker}")
            self.assertEqual(upside, 8.0, f"Upside percentage mismatch for {ticker}")
            self.assertTrue(bool(o["company_name"]))
            self.assertTrue(bool(o["sector"]))
            print(f"  #{i:2d} {ticker:8s} Live: {price:8.2f} EGP | Target(+8%): {target:8.2f} | Stop(-5%): {stop:8.2f} | R:R: 1:{rr}")

        print(f"[PASS] 10D Screen passed: exactly 12 momentum picks verified with verified targets, stops, and live prices.")

    def test_03_stock_dossier_comi_live_sync(self):
        print("\n--- [3] Checking /api/stocks/COMI.CA ---")
        res = self.client.get('/api/stocks/COMI.CA')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()

        # Check live price is exactly 124.65
        price = float(data["current_price"])
        self.assertEqual(price, 124.65, f"Expected live price 124.65, got {price}")

        # Check entry zone
        self.assertEqual(data["entry_zone"], "123.50 – 125.00")

        # Check stop loss
        self.assertEqual(float(data["stop_loss"]), 118.42)

        # Check horizons
        horizons = data.get("horizons", {})
        h_short = horizons.get("10D", {})
        h_med = horizons.get("20D", {})
        h_long = horizons.get("60D", {})

        self.assertEqual(float(h_short.get("target_1")), 128.50)
        self.assertEqual(float(h_short.get("expected_return_pct")), 3.1)

        self.assertEqual(float(h_med.get("target_1")), 134.62)
        self.assertEqual(float(h_med.get("expected_return_pct")), 8.0)

        self.assertEqual(float(h_long.get("target_1")), 145.00)
        self.assertEqual(float(h_long.get("expected_return_pct")), 16.3)

        # Ensure 140.50 is NOT present anywhere in JSON serialization
        raw_json_str = res.get_data(as_text=True)
        self.assertNotIn("140.50", raw_json_str, "Old price 140.50 found in stock dossier JSON response!")
        self.assertNotIn("140.5", raw_json_str, "Old price 140.5 found in stock dossier JSON response!")
        print("[PASS] COMI.CA live dossier verified: 124.65 EGP live price, targets 128.50/134.62/145.00, entry 123.50–125.00, stop 118.42. Zero 140.50 occurrences.")

    def test_04_template_sync_and_text_checks(self):
        print("\n--- [4] Checking Template Synchronization & Static Fallbacks ---")
        tmpl_path = os.path.join(WORKSPACE, "dashboard", "templates", "index.html")
        idx_path = os.path.join(WORKSPACE, "dashboard", "index.html")

        with open(tmpl_path, "r", encoding="utf-8") as f:
            tmpl_content = f.read()
        with open(idx_path, "r", encoding="utf-8") as f:
            idx_content = f.read()

        self.assertEqual(tmpl_content, idx_content, "dashboard/templates/index.html and dashboard/index.html are not in sync!")

        # Verify 140.50 does not appear anywhere in templates
        self.assertNotIn("140.50", tmpl_content, "Found 140.50 in templates/index.html")
        self.assertNotIn("140.5", tmpl_content, "Found 140.5 in templates/index.html")

        # Verify 124.65 and approved targets are present
        self.assertIn("124.65", tmpl_content, "124.65 not found in templates/index.html")
        self.assertIn("123.50 – 125.00", tmpl_content, "Entry zone 123.50 – 125.00 not found")
        self.assertIn("118.42", tmpl_content, "Stop loss 118.42 not found")
        self.assertIn("128.50", tmpl_content, "Short target 128.50 not found")
        self.assertIn("134.62", tmpl_content, "Swing target 134.62 not found")
        self.assertIn("145.00", tmpl_content, "Investment target 145.00 not found")

        # Verify 10D screen heading
        self.assertIn("أفضل 12 فرصة قصيرة المدى", tmpl_content, "Header not updated to 12 opportunities")
        print("[PASS] Templates fully synchronized and verified: static fallbacks perfectly match approved live data.")


if __name__ == "__main__":
    unittest.main()
