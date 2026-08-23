#!/usr/bin/env python3
# =============================================================================
# tests/test_advanced_quant_layers.py — GEN-26 Advanced Institutional Quant Tests
# Validates Market Breadth & Regime, Sector Relative Strength, Institutional Flow,
# and Decomposed Multi-Horizon Forecasting with the Uncertainty Rule.
# =============================================================================

import unittest
import os
import sys

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.market_breadth_engine import MarketBreadthEngine
from core.sector_rs_engine import SectorRelativeStrengthEngine
from core.institutional_flow_engine import InstitutionalFlowEngine
from core.multi_horizon_engine import MultiHorizonEngine


class TestAdvancedQuantLayers(unittest.TestCase):

    def setUp(self):
        self.sample_tickers = ["COMI.CA", "SWDY.CA", "TMGH.CA", "ORAS.CA", "ETEL.CA"]

    # =========================================================================
    # 1. Market Breadth & Regime Engine Tests
    # =========================================================================
    def test_01_market_breadth_baseline_computation(self):
        """Verify dynamic breadth metrics across the EGX universe."""
        breadth = MarketBreadthEngine.compute_market_breadth()
        self.assertGreaterEqual(breadth["total_constituents"], 24)
        self.assertIn("advances", breadth)
        self.assertIn("declines", breadth)
        self.assertIn("ad_ratio", breadth)
        self.assertIn("pct_above_ma20", breadth)
        self.assertIn("pct_above_ma50", breadth)
        self.assertIn("breadth_score", breadth)
        self.assertIn(breadth["market_regime"], [
            MarketBreadthEngine.REGIME_STRONG_BULL,
            MarketBreadthEngine.REGIME_NEUTRAL,
            MarketBreadthEngine.REGIME_DISTRIBUTION,
            MarketBreadthEngine.REGIME_PANIC_BEAR
        ])
        self.assertGreaterEqual(breadth["risk_multiplier"], 0.0)
        self.assertLessEqual(breadth["risk_multiplier"], 1.0)
        self.assertTrue(len(breadth["sentiment_summary_ar"]) > 10)

    def test_02_market_breadth_regime_switch_synthetic(self):
        """Verify regime classification logic under synthetic bull vs bear prices."""
        # 1. Bullish scenario: prices elevated above MA20
        bull_prices = {t: 200.0 for t in self.sample_tickers}
        bull_breadth = MarketBreadthEngine.compute_market_breadth(bull_prices, universe_tickers=self.sample_tickers)
        self.assertIn(bull_breadth["market_regime"], [MarketBreadthEngine.REGIME_STRONG_BULL, MarketBreadthEngine.REGIME_NEUTRAL])

        # 2. Bearish crash scenario: all prices deeply below MA50
        bear_prices = {t: 1.0 for t in self.sample_tickers}
        bear_breadth = MarketBreadthEngine.compute_market_breadth(bear_prices, universe_tickers=self.sample_tickers)
        self.assertEqual(bear_breadth["market_regime"], MarketBreadthEngine.REGIME_PANIC_BEAR)
        self.assertEqual(bear_breadth["risk_multiplier"], 0.0)

    # =========================================================================
    # 2. Dynamic Sector Relative Strength Tests
    # =========================================================================
    def test_03_sector_rs_aggregation(self):
        """Verify real-time sector indices and relative strength rankings."""
        res = SectorRelativeStrengthEngine.analyze_sector_relative_strength()
        self.assertGreaterEqual(res["sectors_count"], 5)
        self.assertTrue(len(res["sectors_ranking"]) >= 5)
        self.assertIn("top_performing_sector", res)
        self.assertIn("stocks_relative_strength", res)

        # Check stock-level profile
        comi_rs = res["stocks_relative_strength"].get("COMI.CA")
        self.assertIsNotNone(comi_rs)
        self.assertIn("rs_spread_pct", comi_rs)
        self.assertIn("rs_ratio", comi_rs)
        self.assertIn(comi_rs["leadership_tier"], [
            SectorRelativeStrengthEngine.SECTOR_LEADER,
            SectorRelativeStrengthEngine.SECTOR_PERFORMER,
            SectorRelativeStrengthEngine.SECTOR_LAGGARD
        ])

    def test_04_sector_rs_single_stock_query(self):
        """Verify get_stock_sector_rs helper."""
        rs_data = SectorRelativeStrengthEngine.get_stock_sector_rs("SWDY.CA")
        self.assertEqual(rs_data["ticker"], "SWDY.CA")
        self.assertIn("sector_name_ar", rs_data)
        self.assertIsInstance(rs_data["is_leader"], bool)

    # =========================================================================
    # 3. Institutional Flow & Volume Anomalies Tests
    # =========================================================================
    def test_05_institutional_flow_routine(self):
        """Verify Volume Z-score and routine liquidity evaluation."""
        flow = InstitutionalFlowEngine.evaluate_stock_flow("COMI.CA")
        self.assertEqual(flow["ticker"], "COMI.CA")
        self.assertIn("volume_z_score", flow)
        self.assertIn("flow_regime", flow)
        self.assertIn("flow_score", flow)
        self.assertIn("flow_alpha_impact", flow)

    def test_06_institutional_accumulation_detection(self):
        """Verify detection of institutional accumulation on high volume breakout."""
        # 10M shares volume on COMI (ADV is 2.5M) with +3.0% price gain
        flow = InstitutionalFlowEngine.evaluate_stock_flow(
            "COMI.CA",
            current_volume=10_000_000,
            current_price=141.0,
            open_price=137.0,
            previous_close=137.0
        )
        self.assertEqual(flow["flow_regime"], InstitutionalFlowEngine.FLOW_INSTITUTIONAL_ACCUMULATION)
        self.assertTrue(flow["is_volume_spike"])
        self.assertGreater(flow["volume_z_score"], 2.0)
        self.assertGreater(flow["flow_alpha_impact"], 0.10)

    def test_07_retail_distribution_detection(self):
        """Verify detection of retail distribution / panic dumping on heavy volume."""
        # 10M shares volume on COMI with -4.0% price drop
        flow = InstitutionalFlowEngine.evaluate_stock_flow(
            "COMI.CA",
            current_volume=10_000_000,
            current_price=131.50,
            open_price=137.0,
            previous_close=137.0
        )
        self.assertEqual(flow["flow_regime"], InstitutionalFlowEngine.FLOW_RETAIL_DISTRIBUTION)
        self.assertTrue(flow["is_volume_spike"])
        self.assertLess(flow["flow_alpha_impact"], 0.0)

    def test_08_scan_universe_flows(self):
        """Verify scanning entire active universe for volume anomalies."""
        scan = InstitutionalFlowEngine.scan_universe_flows()
        self.assertGreaterEqual(scan["total_scanned"], 24)
        self.assertIn("accumulation_count", scan)
        self.assertIn("distribution_count", scan)
        self.assertIn("flows", scan)

    # =========================================================================
    # 4. Decomposed Multi-Horizon Forecasting & Uncertainty Rule Tests
    # =========================================================================
    def test_09_multi_horizon_decomposed_drivers(self):
        """Verify UP DRIVERS and DOWN RISKS decomposition in multi-horizon analysis."""
        analysis = MultiHorizonEngine.get_stock_multi_horizon_analysis("COMI.CA")
        self.assertIsNotNone(analysis)
        self.assertIn("up_drivers", analysis)
        self.assertIn("down_risks", analysis)
        self.assertGreaterEqual(len(analysis["up_drivers"]), 1)
        self.assertGreaterEqual(len(analysis["down_risks"]), 1)

        # Check driver structure
        first_driver = analysis["up_drivers"][0]
        self.assertIn("factor", first_driver)
        self.assertIn("impact_value", first_driver)
        self.assertIn("description_ar", first_driver)

        # Check integrated quant layer outputs
        self.assertIn("market_regime", analysis)
        self.assertIn("sector_relative_strength", analysis)
        self.assertIn("institutional_flow", analysis)

    def test_10_uncertainty_rule_enforcement(self):
        """Verify uncertainty rule flags and decision outputs."""
        # Top quality stock under normal conditions
        comi = MultiHorizonEngine.get_stock_multi_horizon_analysis("COMI.CA")
        self.assertIn(comi["decision"], ["BUY", "WATCH", "AVOID", "NO_TRADE_WAIT"])
        self.assertIn(comi["uncertainty_level"], ["LOW", "MODERATE", "HIGH"])
        self.assertIsInstance(comi["uncertainty_score"], float)

        # Synthetic low-score stock
        raya = MultiHorizonEngine.get_stock_multi_horizon_analysis("RAYA.CA")
        self.assertIsNotNone(raya)
        self.assertIn("action_ar", raya)

    def test_11_cross_sectional_rankings_with_factors(self):
        """Verify full universe rankings are produced with complete factor attribution."""
        rankings = MultiHorizonEngine.get_all_multi_horizon_rankings(universe="core")
        self.assertGreaterEqual(len(rankings), 24)
        for r in rankings:
            self.assertIn("rank", r)
            self.assertIn("up_drivers", r)
            self.assertIn("down_risks", r)
            self.assertIn("decision", r)
            self.assertIn("horizons", r)
            self.assertEqual(len(r["horizons"]), 5)


if __name__ == "__main__":
    unittest.main()
