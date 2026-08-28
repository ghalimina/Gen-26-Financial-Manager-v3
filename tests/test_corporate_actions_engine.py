#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# tests/test_corporate_actions_engine.py — Unit Tests for CorporateActionsEngine
# Validates:
# 1. Dividend & Ex-Date Shield (Suppresses false Stop-Loss triggers on dividend drops).
# 2. Two-Stage DCF Intrinsic Fair Value & Margin of Safety calculation.
# =============================================================================

import os
import sys
import unittest

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.corporate_actions_engine import CorporateActionsEngine


class TestCorporateActionsEngine(unittest.TestCase):

    def test_01_ex_dividend_shield_suppresses_stop_loss(self):
        """Verify price drop on ex-dividend date suppresses stop-loss."""
        # ORAS.CA has scheduled dividend event with ~13.50 EGP value on 2026-06-25
        res = CorporateActionsEngine.check_ex_dividend_shield(
            "ORAS.CA",
            current_price=275.0,
            prev_close=288.0,
            date_str="2026-06-25"
        )
        self.assertTrue(res["is_ex_dividend_window"])
        self.assertTrue(res["suppress_stop_loss"])
        self.assertIn("درع التوزيعات النقدية", res["reason_ar"])
        self.assertGreater(res["dividend_value_egp"], 0)

    def test_02_ex_dividend_shield_normal_trading_no_suppress(self):
        """Verify stock with no corporate action does not suppress stop-loss."""
        res = CorporateActionsEngine.check_ex_dividend_shield(
            "NON_EXISTENT_CO.CA",
            current_price=90.0,
            prev_close=100.0,
            date_str="2026-08-28"
        )
        self.assertFalse(res["is_ex_dividend_window"])
        self.assertFalse(res["suppress_stop_loss"])

    def test_03_dcf_fair_value_calculation_structure(self):
        """Verify calculate_fair_value returns fair value, margin of safety, and Arabic verdict."""
        res = CorporateActionsEngine.calculate_fair_value("COMI.CA")
        self.assertIn("fair_value_egp", res)
        self.assertGreater(res["fair_value_egp"], 0.0)
        self.assertIn("margin_of_safety_pct", res)
        self.assertIsInstance(res["margin_of_safety_pct"], float)
        self.assertIn("is_undervalued", res)
        self.assertIsInstance(res["is_undervalued"], bool)
        self.assertIn("verdict_ar", res)
        self.assertIn("inputs", res)
        self.assertIn("growth_rate_5y_pct", res["inputs"])
        self.assertIn("discount_rate_wacc_pct", res["inputs"])

    def test_04_dcf_fair_value_custom_parameters(self):
        """Verify custom discount and growth rates alter the computed fair value logically."""
        base_val = CorporateActionsEngine.calculate_fair_value("SWDY.CA", custom_growth_rate_pct=10.0, custom_discount_rate_pct=22.0)
        high_growth_val = CorporateActionsEngine.calculate_fair_value("SWDY.CA", custom_growth_rate_pct=20.0, custom_discount_rate_pct=22.0)

        # Higher growth must yield higher fair value
        self.assertGreater(high_growth_val["fair_value_egp"], base_val["fair_value_egp"])


if __name__ == "__main__":
    unittest.main()
