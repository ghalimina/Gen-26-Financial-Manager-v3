#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# tests/test_egx_trading_rules_engine.py — Unit Tests for EGXTradingRulesEngine
# Validates:
# 1. Circuit Breakers (Limit Up >= 9.8% / 19.8%, Limit Down <= -9.8% / -19.8%).
# 2. Settlement Tiers (T+0, T+1, T+2) and Margin Lists (A vs B).
# 3. Net Proceeds, 0.35% roundtrip friction, and 10% Capital Gains Tax.
# 4. Market Impact & ADV Order Sizing Safeguard (>10% ADV warning & chunking).
# =============================================================================

import os
import sys
import unittest

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.egx_trading_rules_engine import EGXTradingRulesEngine


class TestEGXTradingRulesEngine(unittest.TestCase):

    def test_01_circuit_breaker_limit_up_egx30(self):
        """Verify EGX30 stock hitting +19.8% wide limit returns can_buy=False with Arabic reason."""
        res = EGXTradingRulesEngine.evaluate_price_limits("COMI.CA", current_price=119.85, prev_close=100.0)
        self.assertFalse(res["can_buy"])
        self.assertTrue(res["can_sell"])
        self.assertEqual(res["status"], "LIMIT_UP")
        self.assertIn("الحد الأقصى للصعود", res["reason_ar"])
        self.assertEqual(res["max_limit_pct"], 20.0)

    def test_02_circuit_breaker_limit_down_standard(self):
        """Verify standard stock hitting -9.9% limit returns can_sell=False."""
        res = EGXTradingRulesEngine.evaluate_price_limits("UNKNOWN_STANDARD.CA", current_price=90.0, prev_close=100.0)
        self.assertTrue(res["can_buy"])
        self.assertFalse(res["can_sell"])
        self.assertEqual(res["status"], "LIMIT_DOWN")
        self.assertIn("الحد الأدنى", res["reason_ar"])
        self.assertEqual(res["max_limit_pct"], 10.0)

    def test_03_circuit_breaker_normal_trading(self):
        """Verify normal +3.5% move allows both buying and selling."""
        res = EGXTradingRulesEngine.evaluate_price_limits("SWDY.CA", current_price=103.50, prev_close=100.0)
        self.assertTrue(res["can_buy"])
        self.assertTrue(res["can_sell"])
        self.assertEqual(res["status"], "NORMAL_TRADING")

    def test_04_settlement_and_margin_tiers(self):
        """Verify settlement tagging for T+0 (List A), T+1 (List B), and T+2."""
        t0 = EGXTradingRulesEngine.get_settlement_and_margin_tier("COMI.CA")
        self.assertEqual(t0["settlement_type"], "T0_SAME_DAY")
        self.assertEqual(t0["margin_eligibility"], "MARGIN_LIST_A")
        self.assertTrue(t0["is_t0_eligible"])
        self.assertEqual(t0["max_margin_ratio_pct"], 80.0)

        t1 = EGXTradingRulesEngine.get_settlement_and_margin_tier("OLFI.CA")
        self.assertEqual(t1["settlement_type"], "T1_NEXT_DAY")
        self.assertEqual(t1["margin_eligibility"], "MARGIN_LIST_B")
        self.assertFalse(t1["is_t0_eligible"])
        self.assertEqual(t1["max_margin_ratio_pct"], 50.0)

        t2 = EGXTradingRulesEngine.get_settlement_and_margin_tier("SMALL_CAP_UNKNOWN.CA")
        self.assertEqual(t2["settlement_type"], "T2_REGULAR")
        self.assertEqual(t2["margin_eligibility"], "NON_MARGIN_LIST_B")
        self.assertFalse(t2["is_t0_eligible"])
        self.assertFalse(t2["is_marginable"])

    def test_05_net_profit_and_cgt_tax_calculation(self):
        """Verify deduction of 0.35% roundtrip friction and 10% CGT on positive profit."""
        # 100,000 gross pnl on 500,000 turnover
        calc = EGXTradingRulesEngine.calculate_net_proceeds(gross_pnl=100000.0, holding_days=10, order_turnover_egp=500000.0, is_resident=True)
        # Friction = 500,000 * 0.0035 = 1,750
        self.assertEqual(calc["friction_fees_egp"], 1750.0)
        # Net before tax = 100,000 - 1,750 = 98,250
        # CGT = 98,250 * 0.10 = 9,825.0
        self.assertEqual(calc["cgt_tax_egp"], 9825.0)
        # Net proceeds = 98,250 - 9,825 = 88,425.0
        self.assertEqual(calc["net_proceeds_egp"], 88425.0)
        self.assertTrue(calc["is_profitable_net"])

        # Loss case: No CGT tax
        loss_calc = EGXTradingRulesEngine.calculate_net_proceeds(gross_pnl=-20000.0, order_turnover_egp=200000.0)
        self.assertEqual(loss_calc["cgt_tax_egp"], 0.0)
        self.assertFalse(loss_calc["is_profitable_net"])

    def test_06_market_impact_order_sizer(self):
        """Verify order > 10% ADV triggers market impact warning and multi-session chunks."""
        # SWDY.CA has ~208M ADV turnover. Order of 30M is ~14.3% -> Exceeds 10%
        impact = EGXTradingRulesEngine.check_market_impact("SWDY.CA", order_value_egp=30_000_000.0)
        self.assertFalse(impact["is_safe"])
        self.assertGreater(impact["adv_ratio_pct"], 10.0)
        self.assertIsNotNone(impact["warning_ar"])
        self.assertGreaterEqual(impact["recommended_chunks"], 2)

        # Small safe order
        safe_impact = EGXTradingRulesEngine.check_market_impact("SWDY.CA", order_value_egp=500_000.0)
        self.assertTrue(safe_impact["is_safe"])
        self.assertEqual(safe_impact["recommended_chunks"], 1)
        self.assertIsNone(safe_impact["warning_ar"])


if __name__ == "__main__":
    unittest.main()
