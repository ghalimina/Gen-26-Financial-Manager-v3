#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# tests/test_gdr_arbitrage_engine.py — Unit Tests for GDRArbitrageEngine
# Validates:
# 1. USD Implied EGP Parity Conversion.
# 2. Bullish Opening Gap Forecast (Spread >= +2.0%).
# 3. Bearish Opening Gap Forecast (Spread <= -2.0%).
# 4. Parity Neutral State.
# 5. Multi-pair universe scan.
# =============================================================================

import os
import sys
import unittest

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.gdr_arbitrage_engine import GDRArbitrageEngine


class TestGDRArbitrageEngine(unittest.TestCase):

    def test_01_gdr_bullish_gap_forecast(self):
        """Verify London GDR price trading at premium (> +2%) forecasts OVERNIGHT_GDR_BULLISH_GAP."""
        # Cairo price = 140.0 EGP, GDR USD = 3.00 USD, USD/EGP = 50.0 -> Implied = 150.0 EGP (+7.14%)
        res = GDRArbitrageEngine.calculate_gdr_premium(
            cairo_ticker="COMI.CA",
            gdr_ticker="CBKD.L",
            shares_per_gdr=1.0,
            live_usd_egp=50.0,
            override_cairo_price=140.0,
            override_gdr_price=3.00
        )
        self.assertEqual(res["implied_cairo_egp"], 150.0)
        self.assertGreaterEqual(res["spread_pct"], 2.0)
        self.assertEqual(res["arbitrage_signal"], "OVERNIGHT_GDR_BULLISH_GAP")
        self.assertEqual(res["sentiment"], "BULLISH")
        self.assertIn("فجوة صاعدة متوقعة", res["action_guidance_ar"])

    def test_02_gdr_bearish_gap_forecast(self):
        """Verify London GDR trading at discount (<= -2%) forecasts OVERNIGHT_GDR_BEARISH_GAP."""
        # Cairo price = 150.0 EGP, GDR USD = 2.70 USD, USD/EGP = 50.0 -> Implied = 135.0 EGP (-10.0%)
        res = GDRArbitrageEngine.calculate_gdr_premium(
            cairo_ticker="COMI.CA",
            gdr_ticker="CBKD.L",
            shares_per_gdr=1.0,
            live_usd_egp=50.0,
            override_cairo_price=150.0,
            override_gdr_price=2.70
        )
        self.assertEqual(res["implied_cairo_egp"], 135.0)
        self.assertLessEqual(res["spread_pct"], -2.0)
        self.assertEqual(res["arbitrage_signal"], "OVERNIGHT_GDR_BEARISH_GAP")
        self.assertEqual(res["sentiment"], "BEARISH")
        self.assertIn("فجوة هابطة متوقعة", res["action_guidance_ar"])

    def test_03_gdr_parity_neutral(self):
        """Verify spread within ±2% returns GDR_PARITY_NEUTRAL."""
        res = GDRArbitrageEngine.calculate_gdr_premium(
            cairo_ticker="COMI.CA",
            gdr_ticker="CBKD.L",
            shares_per_gdr=1.0,
            live_usd_egp=50.0,
            override_cairo_price=140.0,
            override_gdr_price=2.81  # 2.81 * 50 = 140.50 (+0.36%)
        )
        self.assertEqual(res["arbitrage_signal"], "GDR_PARITY_NEUTRAL")
        self.assertEqual(res["sentiment"], "NEUTRAL")

    def test_04_scan_all_gdr_pairs_schema(self):
        """Verify multi-pair GDR scanner returns structured array with COMI, ETEL, HRHO."""
        pairs = GDRArbitrageEngine.scan_all_gdr_pairs()
        self.assertIsInstance(pairs, list)
        self.assertGreaterEqual(len(pairs), 3)
        tickers = [p["cairo_ticker"] for p in pairs]
        self.assertIn("COMI.CA", tickers)
        self.assertIn("ETEL.CA", tickers)

    def test_05_ekho_usd_dual_currency_parity(self):
        """
        Verify EKHO.CA (quoted in USD on EGX) does not produce dimensional unit mismatch.
        Spread must be computed in consistent units (USD vs USD or EGP vs EGP),
        completely preventing the astronomical +6501% calculation defect.
        """
        res = GDRArbitrageEngine.calculate_gdr_premium(
            cairo_ticker="EKHO.CA",
            gdr_ticker="EKHO.L",
            shares_per_gdr=1.0,
            live_usd_egp=50.0,
            override_cairo_price=0.67,  # Quoted in USD
            override_gdr_price=0.85     # Quoted in USD
        )
        self.assertEqual(res["cairo_currency"], "USD")
        self.assertEqual(res["cairo_price_usd"], 0.67)
        self.assertEqual(res["cairo_price_egp"], 33.50)  # 0.67 * 50.0
        self.assertEqual(res["implied_cairo_usd"], 0.85)
        self.assertEqual(res["implied_cairo_egp"], 42.50) # 0.85 * 50.0
        
        # Expected spread: (0.85 - 0.67) / 0.67 * 100 = +26.87%
        self.assertAlmostEqual(res["spread_pct"], 26.87, places=1)
        self.assertLess(res["spread_pct"], 50.0)


if __name__ == "__main__":
    unittest.main()

