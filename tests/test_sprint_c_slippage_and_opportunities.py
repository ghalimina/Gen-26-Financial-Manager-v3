#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# tests/test_sprint_c_slippage_and_opportunities.py — Sprint C Verification Test Suite
# Tests:
# 1. SectorNeutralizer Z-score computation across sectors.
# 2. DynamicRiskManager Almgren-Chriss dynamic execution slippage model.
# 3. StatisticalArbitrageEngine Benjamini-Hochberg FDR cointegration screening.
# 4. MultiHorizonEngine 10D Short-Term Opportunities Screen.
# 5. REST API endpoints /api/opportunities/10d and /api/correlation.
# =============================================================================

import os
import sys
import json
import unittest

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.feature_registry import SectorNeutralizer
from core.dynamic_risk_manager import DynamicRiskManager
from core.statistical_arbitrage_engine import StatisticalArbitrageEngine
from core.multi_horizon_engine import MultiHorizonEngine
from core.portfolio_correlation_engine import PortfolioCorrelationEngine
from dashboard.app import app


class TestSprintCSlippageAndOpportunities(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        cls.client = app.test_client()

    def test_01_sector_neutralizer_computation(self):
        """TC-C01: Verify SectorNeutralizer calculates cross-sectional Z-scores."""
        res = SectorNeutralizer.compute_sector_neutral_features(
            ticker="COMI.CA",
            pe_ratio=7.5,
            rsi14=52.0,
            volume_z_score=0.2
        )
        self.assertEqual(res["sector_pe_neutral_z"], 0.0)
        self.assertEqual(res["sector_rsi_neutral_z"], 0.0)
        self.assertEqual(res["sector_volume_neutral_z"], 0.0)
        self.assertIn("sector", res)

        # Test non-banking stock
        res_ind = SectorNeutralizer.compute_sector_neutral_features(
            ticker="SWDY.CA",
            pe_ratio=12.0,
            rsi14=62.0,
            volume_z_score=1.0
        )
        self.assertIsInstance(res_ind["sector_pe_neutral_z"], float)
        self.assertIsInstance(res_ind["sector_rsi_neutral_z"], float)

    def test_02_almgren_chriss_dynamic_slippage(self):
        """TC-C02: Verify Almgren-Chriss dynamic slippage scaling."""
        # Micro trade in liquid asset (COMI.CA)
        slip_micro = DynamicRiskManager.calculate_dynamic_slippage(
            order_value_egp=50_000.0,
            adv30_egp=25_000_000.0,
            tier="LARGE_CAP"
        )
        self.assertGreaterEqual(slip_micro, 0.10)
        self.assertLessEqual(slip_micro, 0.20)

        # Large institutional block trade in small cap
        slip_block = DynamicRiskManager.calculate_dynamic_slippage(
            order_value_egp=5_000_000.0,
            adv30_egp=2_000_000.0,
            tier="SMALL_CAP"
        )
        self.assertGreater(slip_block, slip_micro)
        self.assertLessEqual(slip_block, 1.50)

    def test_03_statistical_arbitrage_fdr_correction(self):
        """TC-C03: Verify Benjamini-Hochberg FDR correction on cointegrated pairs."""
        fdr_pairs = StatisticalArbitrageEngine.scan_cointegrated_pairs(fdr_alpha=0.05)
        self.assertIsInstance(fdr_pairs, list)
        self.assertGreater(len(fdr_pairs), 0)

        for p in fdr_pairs:
            self.assertIn("raw_pvalue", p)
            self.assertIn("fdr_adjusted_pvalue", p)
            self.assertIn("is_fdr_significant", p)
            self.assertIn("fdr_critical_value", p)

    def test_04_short_term_10d_opportunities_engine(self):
        """TC-C04: Verify MultiHorizonEngine 10D short-term opportunities ranking."""
        opps_data = MultiHorizonEngine.get_short_term_10d_opportunities(universe="core")
        self.assertIn("opportunities", opps_data)
        self.assertIn("horizon", opps_data)
        self.assertIn("ranking_criterion", opps_data)

    def test_05_rest_api_10d_and_correlation_endpoints(self):
        """TC-C05: Verify /api/opportunities/10d and /api/correlation REST endpoints."""
        # 1. 10D Opportunities
        res1 = self.client.get("/api/opportunities/10d")
        self.assertEqual(res1.status_code, 200)
        data1 = res1.get_json()
        self.assertIn("opportunities", data1)

        # 2. Correlation Matrix
        res2 = self.client.get("/api/correlation?tickers=COMI.CA,SWDY.CA,TMGH.CA")
        self.assertEqual(res2.status_code, 200)
        data2 = res2.get_json()
        self.assertIn("correlation_matrix", data2)
        self.assertIn("cluster_risk", data2)


if __name__ == "__main__":
    unittest.main()
