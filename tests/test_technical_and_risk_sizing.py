#!/usr/bin/env python3
# =============================================================================
# tests/test_technical_and_risk_sizing.py — Unit Tests for Technical Engine & Risk Sizer
# =============================================================================

import unittest
from core.technical_setup_engine import TechnicalSetupEngine
from core.risk_position_sizer import RiskBasedPositionSizer
from core.multi_horizon_engine import MultiHorizonEngine
from core.market_breadth_engine import MarketBreadthEngine


class TestTechnicalAndRiskSizing(unittest.TestCase):
    """
    Validates technical factor calculations, setup classifications,
    fractional risk position sizing, and staged target exits.
    """

    def test_01_technical_setup_engine_structure(self):
        res = TechnicalSetupEngine.evaluate_technical_setup("COMI.CA")
        self.assertIn("technical_score", res)
        self.assertIn("setup_classification", res)
        self.assertIn("trend_regime", res)
        self.assertIn("rsi14", res)
        self.assertIn("adx14", res)
        self.assertTrue(10.0 <= res["technical_score"] <= 100.0)
        self.assertIn(res["setup_classification"], [
            TechnicalSetupEngine.SETUP_PULLBACK_UPTREND,
            TechnicalSetupEngine.SETUP_BREAKOUT_EXPANSION,
            TechnicalSetupEngine.SETUP_RANGE_CONSOLIDATION,
            TechnicalSetupEngine.SETUP_DOWNTREND_PULLBACK,
            TechnicalSetupEngine.SETUP_OVERSOLD_REVERSAL
        ])

    def test_02_risk_position_sizer_formula(self):
        # Entry 100, Stop 93 (7 EGP Risk per share). Account 100,000 EGP. Risk 1% = 1,000 EGP.
        # Shares = 1000 / 7 = 142 shares. Position Value = 14,200 EGP (14.2% NAV <= 20% cap).
        res = RiskBasedPositionSizer.calculate_position_size(
            entry_price=100.0,
            stop_loss_price=93.0,
            portfolio_nav_egp=100000.0,
            risk_per_trade_pct=1.0,
            market_regime=MarketBreadthEngine.REGIME_STRONG_BULL
        )
        self.assertEqual(res["shares"], 142)
        self.assertEqual(res["position_value_egp"], 14200.0)
        self.assertAlmostEqual(res["actual_risk_egp"], 142 * 7.0, places=1)
        self.assertTrue(res["allocation_pct"] <= 20.0)

    def test_03_panic_bear_regime_forces_zero_shares(self):
        res = RiskBasedPositionSizer.calculate_position_size(
            entry_price=100.0,
            stop_loss_price=93.0,
            portfolio_nav_egp=100000.0,
            market_regime=MarketBreadthEngine.REGIME_PANIC_BEAR
        )
        self.assertEqual(res["shares"], 0)
        self.assertEqual(res["position_value_egp"], 0.0)
        self.assertEqual(res["binding_constraint"], "PANIC_BEAR_CASH_LOCKOUT")

    def test_04_multi_horizon_engine_returns_enhanced_fields(self):
        analysis = MultiHorizonEngine.get_stock_multi_horizon_analysis("COMI.CA")
        self.assertIsNotNone(analysis)
        self.assertIn("two_tier_relative_strength", analysis)
        self.assertIn("technical_setup", analysis)
        self.assertIn("risk_based_position", analysis)
        self.assertIn("staged_exits", analysis)
        self.assertIn("T1", analysis["staged_exits"])
        self.assertIn("T2", analysis["staged_exits"])
        self.assertIn("T3", analysis["staged_exits"])
        self.assertIn("holding_period_ar", analysis)
        self.assertIn("dominant_catalyst", analysis)
        self.assertIn("expectancy_pct", analysis)
        self.assertTrue(analysis["expectancy_pct"] > 0)


if __name__ == "__main__":
    unittest.main()
