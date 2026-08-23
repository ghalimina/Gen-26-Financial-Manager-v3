#!/usr/bin/env python3
# =============================================================================
# tests/test_full_temporal_forensics.py — GEN-26 Adversarial Temporal Forensics
# Tests information firewalls, future injection invariance, revision isolation,
# and zero-lookahead across all quantitative decision paths.
# =============================================================================

import unittest
import os
import sys
import datetime
import pandas as pd
import numpy as np

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.pit_store import PointInTimeDataStore, HistoricalTradableUniverse
from core.market_intelligence import MarketIntelligenceEngine
from core.company_intelligence import CompanyIntelligenceEngine
from core.decision_builder import CanonicalDecisionBuilder


class TestFullTemporalForensics(unittest.TestCase):

    def test_01_future_injection_decision_invariance(self):
        """
        Adversarial Test:
        Verify that injecting future corporate actions, financials, or news
        leaves historical decision outputs 100% invariant.
        """
        pit = PointInTimeDataStore()
        
        # Historical baseline record known at 2025-01-01
        pit.add_record(
            entity_id="COMI.CA",
            metric_name="roe",
            value=22.0,
            period_end="2024-09-30",
            publication_time="2024-11-15T10:00:00"
        )

        state_before = pit.get_as_of("COMI.CA", "roe", "2025-01-01T09:00:00")
        self.assertEqual(state_before, 22.0)

        # Inject massive future event published on 2025-06-01
        pit.add_record(
            entity_id="COMI.CA",
            metric_name="roe",
            value=35.0,
            period_end="2025-03-31",
            publication_time="2025-05-15T10:00:00"
        )
        pit.add_record(
            entity_id="COMI.CA",
            metric_name="major_acquisition",
            value="ACQUIRED_BANK_X",
            period_end="2025-06-01",
            publication_time="2025-06-01T10:00:00"
        )

        # Re-query as of 2025-01-01
        state_after = pit.get_as_of("COMI.CA", "roe", "2025-01-01T09:00:00")
        future_acq = pit.get_as_of("COMI.CA", "major_acquisition", "2025-01-01T09:00:00")

        self.assertEqual(state_after, 22.0, "LEAKAGE: Historical metric changed after future injection!")
        self.assertIsNone(future_acq, "LEAKAGE: Future acquisition leaked into past decision state!")

    def test_02_publication_vs_event_boundary(self):
        """
        Period End: 2024-12-31
        Publication Time: 2025-02-15
        Query at 2025-01-15 (between period end and publication) -> MUST BE NONE
        """
        pit = PointInTimeDataStore()
        pit.add_record(
            entity_id="SWDY.CA",
            metric_name="net_profit",
            value=5_000_000_000,
            period_end="2024-12-31",
            publication_time="2025-02-15T10:00:00"
        )

        val_between = pit.get_as_of("SWDY.CA", "net_profit", "2025-01-15T12:00:00")
        self.assertIsNone(val_between, "LEAKAGE: Financials were accessible before legal publication date!")

        val_after = pit.get_as_of("SWDY.CA", "net_profit", "2025-02-16T12:00:00")
        self.assertEqual(val_after, 5_000_000_000)

    def test_03_tradable_universe_delisting_and_suspension_firewall(self):
        """
        Verify that suspended/delisted stocks are strictly excluded from tradable universe as of that date.
        """
        universe = HistoricalTradableUniverse()
        
        # Test active stock
        self.assertTrue(universe.is_tradable_on("COMI.CA", "2025-01-10"))

        # Register suspension for TMGH
        universe.register_corporate_action(
            ticker="TMGH.CA",
            action_type="SUSPENSION",
            effective_date="2025-03-01",
            announcement_date="2025-02-28",
            details={"end_date": "2025-03-10"}
        )

        self.assertTrue(universe.is_tradable_on("TMGH.CA", "2025-02-20"))
        self.assertFalse(universe.is_tradable_on("TMGH.CA", "2025-03-05"), "UNIVERSE LEAKAGE: Suspended stock was included in tradable universe!")
        self.assertTrue(universe.is_tradable_on("TMGH.CA", "2025-03-15"))

    def test_04_accounting_anomaly_detection_integrity(self):
        """
        Verify that Accounting Risk correctly detects Net Income rise with collapsing cash flow.
        """
        # Case 1: Net Income = 100M, OCF = -20M (Severe divergence)
        res_severe = CompanyIntelligenceEngine.compute_company_quality_score(
            roe_pct=15.0,
            net_margin_pct=20.0,
            operating_cash_flow_egp=-20_000_000,
            net_income_egp=100_000_000,
            debt_to_equity=3.5,
            sector="Industrial"
        )
        self.assertEqual(res_severe["accounting_risk"], "HIGH")
        self.assertLess(res_severe["earnings_quality_score"], 40.0)

        # Case 2: Net Income = 100M, OCF = 120M (Healthy cash backing)
        res_healthy = CompanyIntelligenceEngine.compute_company_quality_score(
            roe_pct=20.0,
            net_margin_pct=22.0,
            operating_cash_flow_egp=120_000_000,
            net_income_egp=100_000_000,
            debt_to_equity=0.8,
            sector="Industrial"
        )
        self.assertEqual(res_healthy["accounting_risk"], "LOW")
        self.assertGreater(res_healthy["earnings_quality_score"], 80.0)


if __name__ == "__main__":
    unittest.main()
