#!/usr/bin/env python3
# =============================================================================
# tests/test_gap_closure.py — GEN-26 Gap-Closure Unit & Integration Test Suite
# Validates Broker Adapters, External Provider Fallbacks, Contextual Arabic NLP,
# Unified Risk Reason Codes, and Alpha Sub-Score attribution.
# =============================================================================

import unittest
import os
import sys

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.broker_adapter import PaperBrokerAdapter, AdvisoryBrokerAdapter, FutureOfficialBrokerAdapter, OrderStatus
from core.external_providers import (
    ConsensusEstimatesProvider,
    OrderBookDepthProvider,
    InvestorFlowProvider,
    DelistedArchiveProvider,
    ProviderStatus
)
from core.event_intelligence import EventIntelligenceEngine, EventStage
from core.decision_builder import CanonicalDecisionBuilder, RiskReasonCode
from core.alpha_engine import AlphaEngine


class TestGapClosure(unittest.TestCase):

    def test_01_paper_broker_lifecycle(self):
        """Test PaperBrokerAdapter order validation, execution, cash tracking, and reconciliation."""
        broker = PaperBrokerAdapter(initial_cash=50_000.0)

        # 1. Reject BUY order exceeding cash
        rej = broker.place_order("COMI.CA", "BUY", 10_000, 100.0) # 1,000,000 EGP > 50,000
        self.assertEqual(rej["status"], OrderStatus.REJECTED)
        self.assertEqual(rej["rejection_reason"], "INSUFFICIENT_CASH_SOLVENCY")

        # 2. Execute valid BUY
        fill_buy = broker.place_order("COMI.CA", "BUY", 200, 100.0) # ~20,000 EGP
        self.assertEqual(fill_buy["status"], OrderStatus.FILLED)
        self.assertEqual(broker.get_positions().get("COMI.CA"), 200)
        self.assertLess(broker.get_cash(), 30_000.0)

        # 3. Execute SELL portion
        fill_sell = broker.place_order("COMI.CA", "SELL", 100, 105.0)
        self.assertEqual(fill_sell["status"], OrderStatus.FILLED)
        self.assertEqual(broker.get_positions().get("COMI.CA"), 100)

        # 4. Reconciliation
        rec = broker.reconcile()
        self.assertEqual(rec["reconciliation_status"], "MATCHED")
        self.assertEqual(rec["executed_orders"], 2)

    def test_02_advisory_and_official_broker_safety(self):
        """Verify advisory mode creates recommendations and official adapter blocks live orders."""
        advisory = AdvisoryBrokerAdapter()
        rec = advisory.place_order("SWDY.CA", "BUY", 500, 45.0)
        self.assertEqual(rec["status"], "AWAITING_MANUAL_EXECUTION")

        official = FutureOfficialBrokerAdapter()
        val = official.validate_order("SWDY.CA", "BUY", 500, 45.0)
        self.assertFalse(val["valid"])
        self.assertIn("BLOCKED_EXTERNAL_DEPENDENCY", val["reason"])

        with self.assertRaises(NotImplementedError):
            official.place_order("SWDY.CA", "BUY", 500, 45.0)

    def test_03_external_provider_graceful_fallbacks(self):
        """Verify external providers report proper statuses without faking data."""
        consensus = ConsensusEstimatesProvider()
        res_c = consensus.get_forward_eps_estimate("TMGH.CA")
        self.assertEqual(res_c["status"], ProviderStatus.BLOCKED_EXTERNAL_DEPENDENCY)
        self.assertIsNone(res_c["consensus_eps"])

        order_book = OrderBookDepthProvider(is_live_feed=False)
        res_ob = order_book.get_order_book_spread("COMI.CA", 100.0, adv_20d_egp=80_000_000)
        self.assertEqual(res_ob["data_nature"], ProviderStatus.MODELED)
        self.assertFalse(res_ob["is_real_depth"])

        flow_prov = InvestorFlowProvider(bulletin_feed_active=False)
        res_flow = flow_prov.get_investor_flow_breakdown("SWDY.CA", volume_zscore=2.5)
        self.assertEqual(res_flow["status"], ProviderStatus.MODELED)
        self.assertEqual(res_flow["smart_money_proxy"], "HIGH_ACCUMULATION_PROXY")

        delisted = DelistedArchiveProvider(archive_available=False)
        res_del = delisted.get_delisted_series("OLD_STOCK.CA")
        self.assertEqual(res_del["status"], ProviderStatus.BLOCKED_EXTERNAL_DEPENDENCY)

    def test_04_contextual_arabic_event_stages(self):
        """Verify that rumors and intentions are discounted compared to completed acquisitions."""
        # 1. Rumor / Study text
        ev_rumor = EventIntelligenceEngine.parse_disclosure_text(
            text="الشركة تدرس الاستحواذ على حصة غير حاكمة",
            ticker="ETEL.CA"
        )
        self.assertEqual(ev_rumor.event_type, "ACQUISITION")
        self.assertEqual(ev_rumor.stage, EventStage.INTENTION)
        self.assertLess(ev_rumor.confidence, 0.80)

        # 2. Completed text
        ev_comp = EventIntelligenceEngine.parse_disclosure_text(
            text="الشركة أتمت الاستحواذ رسمياً على أصول المصنع",
            ticker="ETEL.CA"
        )
        self.assertEqual(ev_comp.event_type, "ACQUISITION")
        self.assertEqual(ev_comp.stage, EventStage.COMPLETED)
        self.assertEqual(ev_comp.confidence, 0.88)

    def test_05_decision_builder_risk_reason_codes(self):
        """Verify that risk reason codes and unified risk score are included in decision output."""
        alpha_data = {"alpha_score": 75.0, "confidence_pct": 80.0}
        quality_data = {"quality_score": 80.0, "accounting_risk": "HIGH"}
        valuation_data = {"valuation_score": 70.0}
        liquidity_data = {"liquidity_score": 40.0}

        dec = CanonicalDecisionBuilder.build_decision(
            ticker="TEST.CA",
            company_name="Test Company",
            current_price=50.0,
            entry_price=48.0,
            stop_price=45.0,
            target_price=60.0,
            alpha_data=alpha_data,
            quality_data=quality_data,
            valuation_data=valuation_data,
            liquidity_data=liquidity_data,
            data_health="PASS",
            available_free_cash=100_000.0,
            current_stock_equity=20_000.0,
            total_portfolio_equity=100_000.0
        )

        self.assertIn("risk_score", dec["risk"])
        self.assertIn("risk_reason_codes", dec["risk"])
        self.assertIn(RiskReasonCode.ACCOUNTING_HIGH_RISK, dec["risk"]["risk_reason_codes"])
        self.assertIn(RiskReasonCode.LIQUIDITY_INSUFFICIENT, dec["risk"]["risk_reason_codes"])
        self.assertLess(dec["risk"]["risk_score"], 70.0)

    def test_06_alpha_sub_score_attribution(self):
        """Verify that AlphaEngine computes complete explainable sub-scores across all 7 dimensions."""
        sub = AlphaEngine.compute_sub_scores(
            tech_features={"mom_20d": 0.15, "rsi_14": 52.0, "close_gt_sma50": True, "gk_volatility": 0.025},
            fund_features={"roe": 22.0, "ocf_net_income_ratio": 1.2},
            val_features={"margin_of_safety_pct": 15.0},
            event_features={"direction_score": 0.8},
            regime_features={"breadth_ratio": 0.65},
            liq_features={"adv_20d_egp": 25_000_000}
        )

        self.assertIn("TECHNICAL_ALPHA", sub)
        self.assertIn("FUNDAMENTAL_ALPHA", sub)
        self.assertIn("VALUATION_ALPHA", sub)
        self.assertIn("EVENT_ALPHA", sub)
        self.assertIn("REGIME_ALPHA", sub)
        self.assertIn("LIQUIDITY_SCORE", sub)
        self.assertIn("RISK_SCORE", sub)
        self.assertGreater(sub["TECHNICAL_ALPHA"], 60.0)


if __name__ == "__main__":
    unittest.main()
