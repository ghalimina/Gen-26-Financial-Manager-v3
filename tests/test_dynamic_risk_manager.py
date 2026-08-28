#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# tests/test_dynamic_risk_manager.py — Unit Tests for DynamicRiskManager
# Validates:
# 1. Progressive Trailing Stop Ratchet (+10% Breakeven, +20% & +30% Profit Locks).
# 2. Irreversible Stop Guard (Stop loss cannot decrease).
# 3. Sector Concentration Safeguard (Max 35% portfolio exposure).
# =============================================================================

import os
import sys
import unittest

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.dynamic_risk_manager import DynamicRiskManager


class TestDynamicRiskManager(unittest.TestCase):

    def test_01_trailing_stop_initial_buffer(self):
        """Verify gain < 10% defaults to initial stop buffer."""
        res = DynamicRiskManager.compute_trailing_stop(entry_price=100.0, peak_price=105.0, current_price=104.0)
        self.assertEqual(res["trailing_stop_price"], 95.0)
        self.assertFalse(res["is_stop_triggered"])
        self.assertEqual(res["risk_stage"], "INITIAL_RISK_BUFFER")

    def test_02_trailing_stop_stage1_breakeven(self):
        """Verify gain >= 10% raises stop to entry price (breakeven)."""
        res = DynamicRiskManager.compute_trailing_stop(entry_price=100.0, peak_price=112.0, current_price=110.0)
        self.assertEqual(res["trailing_stop_price"], 100.0)
        self.assertEqual(res["risk_stage"], "LOCK_STAGE_1_BREAKEVEN")

    def test_03_trailing_stop_stage2_profit_lock(self):
        """Verify gain >= 20% locks in profit at 92% of peak price."""
        res = DynamicRiskManager.compute_trailing_stop(entry_price=100.0, peak_price=125.0, current_price=120.0)
        # 125 * 0.92 = 115.0
        self.assertEqual(res["trailing_stop_price"], 115.0)
        self.assertGreater(res["locked_in_profit_pct"], 10.0)
        self.assertEqual(res["risk_stage"], "LOCK_STAGE_2_PROFIT_PROTECTION")

    def test_04_trailing_stop_stage3_aggressive_profit_lock(self):
        """Verify gain >= 30% locks in profit at 94% of peak price."""
        res = DynamicRiskManager.compute_trailing_stop(entry_price=100.0, peak_price=150.0, current_price=145.0)
        # 150 * 0.94 = 141.0
        self.assertEqual(res["trailing_stop_price"], 141.0)
        self.assertEqual(res["risk_stage"], "LOCK_STAGE_3_AGGRESSIVE_PROFIT")

    def test_05_trailing_stop_irreversible_ratchet(self):
        """Verify stop price never drops even if current_price falls from peak."""
        res = DynamicRiskManager.compute_trailing_stop(
            entry_price=100.0,
            peak_price=150.0,
            current_price=140.0,
            current_stop=141.0
        )
        self.assertEqual(res["trailing_stop_price"], 141.0)
        self.assertTrue(res["is_stop_triggered"])

    def test_06_sector_concentration_guard_enforcement(self):
        """Verify sector exposure exceeding 35% is rejected with Arabic explanation."""
        current_holdings = [
            {"ticker": "TMGH.CA", "market_value_egp": 30000.0, "sector": "العقارات"},
            {"ticker": "COMI.CA", "market_value_egp": 70000.0, "sector": "الخدمات المالية والبنوك"}
        ]
        # Total portfolio = 100k. Real estate is 30%.
        # Adding 20k to PHDC.CA (Real Estate) makes total 120k, Real Estate = 50k (41.6% > 35%)
        guard = DynamicRiskManager.evaluate_sector_concentration(
            current_holdings=current_holdings,
            new_order={"ticker": "PHDC.CA", "order_value_egp": 20000.0, "sector": "العقارات"},
            total_portfolio_value_egp=100000.0
        )
        self.assertFalse(guard["is_allowed"])
        self.assertIn("حظر تركيز قطاعي", guard["reason_ar"])
        self.assertGreater(guard["post_order_sector_exposure_pct"], 35.0)


if __name__ == "__main__":
    unittest.main()
