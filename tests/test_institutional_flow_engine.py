#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# tests/test_institutional_flow_engine.py — Unit Tests for InstitutionalFlowEngine
# Validates:
# 1. Volume Z-Score & Institutional Accumulation/Distribution Detection.
# 2. Institutional & Foreign Flow Telemetry and Blue-Chip Boost (>50M EGP).
# 3. MSCI & FTSE Semi-Annual Rebalancing Calendar.
# 4. Equity Risk Premium (ERP) vs Risk-Free Rate.
# =============================================================================

import os
import sys
import unittest

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.institutional_flow_engine import InstitutionalFlowEngine


class TestInstitutionalFlowEngine(unittest.TestCase):

    def test_01_stock_level_volume_zscore_accumulation(self):
        """Verify volume spike (+Z-Score) with price increase triggers INSTITUTIONAL_ACCUMULATION."""
        res = InstitutionalFlowEngine.evaluate_stock_flow(
            "COMI.CA",
            current_volume=6_000_000,  # Far above ADV of 2.5M
            current_price=145.0,
            open_price=140.0,
            previous_close=139.0
        )
        self.assertEqual(res["flow_regime"], InstitutionalFlowEngine.FLOW_INSTITUTIONAL_ACCUMULATION)
        self.assertTrue(res["is_volume_spike"])
        self.assertGreater(res["volume_z_score"], 2.0)
        self.assertGreater(res["flow_alpha_impact"], 0.0)

    def test_02_stock_level_retail_distribution(self):
        """Verify volume spike with severe price drop triggers RETAIL_DISTRIBUTION."""
        res = InstitutionalFlowEngine.evaluate_stock_flow(
            "SWDY.CA",
            current_volume=5_000_000,
            current_price=110.0,
            open_price=120.0,
            previous_close=122.0
        )
        self.assertEqual(res["flow_regime"], InstitutionalFlowEngine.FLOW_RETAIL_DISTRIBUTION)
        self.assertTrue(res["is_volume_spike"])
        self.assertLess(res["flow_alpha_impact"], 0.0)

    def test_03_institutional_flow_telemetry_and_blue_chip_boost(self):
        """Verify aggressive net buying (>50M EGP) activates blue chip composite boost factor."""
        telemetry = InstitutionalFlowEngine.get_institutional_flow_telemetry(
            foreign_net_egp=+90_000_000.0,
            egyptian_inst_net_egp=+120_000_000.0
        )
        self.assertTrue(telemetry["is_aggressive_accumulation"])
        self.assertGreater(telemetry["blue_chip_boost_factor"], 1.0)
        self.assertIn("COMI.CA", telemetry["boosted_blue_chips"])

    def test_04_msci_ftse_rebalancing_calendar_schema(self):
        """Verify rebalancing radar outputs valid review dates, countdown, and affected equities."""
        rebal = InstitutionalFlowEngine.get_index_rebalancing_calendar()
        self.assertIn("next_review_name", rebal)
        self.assertIn("next_rebalancing_date", rebal)
        self.assertIn("days_remaining", rebal)
        self.assertIsInstance(rebal["days_remaining"], int)
        self.assertIn("affected_equities", rebal)
        self.assertGreaterEqual(len(rebal["affected_equities"]), 3)
        self.assertIn("guidance_ar", rebal)

    def test_05_equity_risk_premium_calculation(self):
        """Verify ERP compares Earnings Yield vs CBE Risk Free Rate."""
        # PE = 8.0 -> Earnings Yield = 12.5%, Risk Free = 19.75%
        erp = InstitutionalFlowEngine.calculate_equity_risk_premium(egx30_pe_ratio=8.0, cbe_risk_free_rate_pct=19.75)
        self.assertEqual(erp["egx30_earnings_yield_pct"], 12.50)
        self.assertIn("equity_risk_premium_pct", erp)
        self.assertIn("allocation_regime", erp)
        self.assertIn("recommended_equity_pct", erp)
        self.assertIn("verdict_ar", erp)


if __name__ == "__main__":
    unittest.main()
