#!/usr/bin/env python3
# =============================================================================
# tests/test_core_engines.py — GEN-26 Comprehensive Core Engine Unit Tests
# Verifies Point-in-Time discipline, Data Quality verdicts, Company Intelligence,
# Valuation, Market Regime, Liquidity, Decision Replay, and Invariants.
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
from core.data_quality import DataQualityEngine
from core.feature_registry import FeatureRegistry
from core.company_intelligence import CompanyIntelligenceEngine
from core.valuation_engine import ValuationEngine
from core.market_intelligence import MarketIntelligenceEngine
from core.liquidity_engine import LiquidityEngine
from core.event_intelligence import EventIntelligenceEngine
from core.alpha_engine import AlphaEngine
from core.decision_builder import CanonicalDecisionBuilder, DecisionReplayEngine


class TestCoreEngines(unittest.TestCase):

    def setUp(self):
        self.pit_store = PointInTimeDataStore()
        self.tradable_universe = HistoricalTradableUniverse()
        self.registry = FeatureRegistry()

    def test_01_point_in_time_firewall(self):
        """Verify that PointInTimeDataStore strictly prevents lookahead leakage."""
        # Q2 financial results published on August 15, 2026
        self.pit_store.add_record(
            entity_id="COMI.CA",
            metric_name="net_income",
            value=8_500_000_000,
            period_end="2026-06-30",
            publication_time="2026-08-15T10:00:00"
        )

        # On August 10, 2026, the query MUST return None (not yet known)
        val_before = self.pit_store.get_as_of("COMI.CA", "net_income", "2026-08-10T12:00:00")
        self.assertIsNone(val_before)

        # On August 16, 2026, the query MUST return the correct value
        val_after = self.pit_store.get_as_of("COMI.CA", "net_income", "2026-08-16T12:00:00")
        self.assertEqual(val_after, 8_500_000_000)

    def test_02_historical_tradable_universe(self):
        """Verify tradable status and suspension handling."""
        self.assertTrue(self.tradable_universe.is_tradable_on("COMI.CA", "2026-08-20"))
        self.assertFalse(self.tradable_universe.is_tradable_on("FAKE_TICKER.CA", "2026-08-20"))

        # Register suspension
        self.tradable_universe.register_corporate_action(
            ticker="COMI.CA",
            action_type="SUSPENSION",
            effective_date="2026-09-01",
            announcement_date="2026-08-30",
            details={"end_date": "2026-09-10"}
        )
        self.assertFalse(self.tradable_universe.is_tradable_on("COMI.CA", "2026-09-05"))
        self.assertTrue(self.tradable_universe.is_tradable_on("COMI.CA", "2026-09-15"))

    def test_03_data_quality_engine(self):
        """Verify Data Quality Engine audits OHLCV and produces fail-closed verdicts."""
        dates = pd.date_range("2026-01-01", periods=100)
        df_valid = pd.DataFrame({
            "Open": np.linspace(80, 100, 100),
            "High": np.linspace(82, 102, 100),
            "Low": np.linspace(79, 99, 100),
            "Close": np.linspace(80, 100, 100),
            "Volume": [100000.0] * 100
        }, index=dates)

        res_valid = DataQualityEngine.audit_ohlcv_dataframe(df_valid, "COMI.CA")
        self.assertEqual(res_valid["health"], "PASS")
        self.assertTrue(res_valid["can_trade"])

        # Corrupt data with High < Low
        df_corrupt = df_valid.copy()
        df_corrupt.loc[df_corrupt.index[10], "High"] = 10.0
        df_corrupt.loc[df_corrupt.index[10], "Low"] = 90.0
        res_corrupt = DataQualityEngine.audit_ohlcv_dataframe(df_corrupt, "COMI.CA")
        self.assertIn("Invalid High < Low", str(res_corrupt["issues"]))

    def test_04_company_intelligence_and_accounting_risk(self):
        """Verify Company Quality and Accounting Risk indicator."""
        # Strong cash conversion -> Low accounting risk
        res_strong = CompanyIntelligenceEngine.compute_company_quality_score(
            roe_pct=25.0,
            net_margin_pct=32.0,
            operating_cash_flow_egp=10_000_000,
            net_income_egp=8_000_000,
            debt_to_equity=2.5,
            sector="Banking"
        )
        self.assertEqual(res_strong["accounting_risk"], "LOW")
        self.assertGreater(res_strong["quality_score"], 70.0)

        # Poor cash conversion -> High accounting risk
        res_risky = CompanyIntelligenceEngine.compute_company_quality_score(
            roe_pct=10.0,
            net_margin_pct=12.0,
            operating_cash_flow_egp=1_000_000,
            net_income_egp=10_000_000,
            debt_to_equity=15.0,
            sector="Banking"
        )
        self.assertEqual(res_risky["accounting_risk"], "HIGH")

    def test_05_valuation_and_fair_value_scenarios(self):
        """Verify multi-ratio valuation and conservative fair value envelopes."""
        val = ValuationEngine.evaluate_valuation(
            current_price=80.0,
            pe_ratio=8.0,
            pb_ratio=1.5,
            dividend_yield_pct=7.0
        )
        self.assertGreater(val["valuation_score"], 70.0)

        fv = ValuationEngine.compute_fair_value_scenarios(
            current_price=80.0,
            eps=10.0,
            base_pe=10.0
        )
        self.assertEqual(fv["base_case"], 100.0)
        self.assertEqual(fv["bear_case"], 80.0)
        self.assertEqual(fv["bull_case"], 125.0)
        self.assertGreater(fv["base_upside_pct"], 0.0)

    def test_06_market_regime_and_breadth(self):
        """Verify market regime classification and trailing breadth."""
        dates = pd.date_range("2026-01-01", periods=100)
        dfs = {
            "STOCK_A": pd.DataFrame({"Close": [10.0, 10.5]}, index=dates[:2]),
            "STOCK_B": pd.DataFrame({"Close": [20.0, 19.5]}, index=dates[:2]),
            "STOCK_C": pd.DataFrame({"Close": [30.0, 30.8]}, index=dates[:2]),
        }
        breadth = MarketIntelligenceEngine.compute_trailing_breadth(dfs)
        self.assertEqual(breadth["advances"], 2)
        self.assertEqual(breadth["declines"], 1)

    def test_07_liquidity_engine_capacity(self):
        """Verify ADV and tradability capacity limits."""
        dates = pd.date_range("2026-01-01", periods=30)
        df_liquid = pd.DataFrame({
            "Close": [50.0] * 30,
            "Volume": [200_000.0] * 30  # 10M EGP / day
        }, index=dates)
        liq = LiquidityEngine.evaluate_liquidity(df_liquid, target_position_value_egp=500_000.0)
        self.assertEqual(liq["tradability_status"], "HIGH_LIQUIDITY")
        self.assertTrue(liq["can_execute"])

    def test_08_event_intelligence_parser(self):
        """Verify Arabic disclosure parsing."""
        ev = EventIntelligenceEngine.parse_disclosure_text(
            text="إعلان توقيع عقد تنفيذ مشروع جديد بقيمة 500 مليون جنيه",
            ticker="SWDY.CA"
        )
        self.assertEqual(ev.event_type, "NEW_CONTRACT")
        self.assertEqual(ev.direction, "POSITIVE")
        self.assertEqual(ev.materiality, "HIGH")

    def test_09_decision_builder_and_replay_engine(self):
        """Verify SSoT Decision Builder, Frozen Core Risk Gates, and Decision Replay."""
        alpha = {"alpha_score": 85.0, "confidence_pct": 88.0}
        quality = {"quality_score": 80.0, "accounting_risk": "LOW"}
        valuation = {"valuation_score": 75.0}
        liquidity = {"liquidity_score": 90.0}

        # Test Case 1: Approved Buy Order
        dec = CanonicalDecisionBuilder.build_decision(
            ticker="COMI.CA",
            company_name="البنك التجاري الدولي",
            current_price=85.0,
            entry_price=83.0,  # Valid Pullback (ep < cp)
            stop_price=78.0,
            target_price=95.0,
            alpha_data=alpha,
            quality_data=quality,
            valuation_data=valuation,
            liquidity_data=liquidity,
            data_health="PASS",
            available_free_cash=200_000.0,
            current_stock_equity=300_000.0,
            total_portfolio_equity=1_000_000.0
        )
        self.assertEqual(dec["signal"]["status"], "APPROVED")
        self.assertEqual(dec["gates"]["cash_gate"], "PASS")
        self.assertEqual(dec["gates"]["allocation_gate"], "PASS")

        # Test Case 2: Replay historic decision
        replayed = DecisionReplayEngine.replay_decision(dec["decision_id"])
        self.assertIsNotNone(replayed)
        self.assertEqual(replayed["decision"]["decision_id"], dec["decision_id"])
        self.assertEqual(replayed["decision"]["ticker"], "COMI.CA")

        # Test Case 3: Pullback Invariant Rejection (ep >= cp)
        dec_invalid_ep = CanonicalDecisionBuilder.build_decision(
            ticker="COMI.CA",
            company_name="البنك التجاري الدولي",
            current_price=85.0,
            entry_price=86.0,  # Invalid Entry (ep >= cp)
            stop_price=78.0,
            target_price=95.0,
            alpha_data=alpha,
            quality_data=quality,
            valuation_data=valuation,
            liquidity_data=liquidity,
            data_health="PASS",
            available_free_cash=200_000.0,
            current_stock_equity=300_000.0,
            total_portfolio_equity=1_000_000.0
        )
        self.assertEqual(dec_invalid_ep["signal"]["status"], "BLOCKED")
        self.assertEqual(dec_invalid_ep["gates"]["pullback_gate"], "FAIL")


if __name__ == "__main__":
    unittest.main()
