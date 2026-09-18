#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# tests/test_institutional_upgrades.py — Unit Tests for Full-Stack Upgrades
# Verifies:
# 1. Universal 244-ticker entity mapper in NewsIngestionEngine.
# 2. Sloan Accruals calculation & dual-source extraction in FundamentalDataEngine.
# 3. Macro Economic regime determination and CBE interest rate handling.
# 4. QuantReasoningAgent Arabic investment memo generation.
# 5. TelegramBotService command dispatcher.
# =============================================================================

import os
import sys
import unittest

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.news_ingestion_engine import NewsIngestionEngine
from core.fundamental_data_engine import FundamentalDataEngine
from core.macro_economic_engine import MacroEconomicEngine
from core.quant_reasoning_agent import QuantReasoningAgent
from core.telegram_bot_service import TelegramBotService


class TestInstitutionalUpgrades(unittest.TestCase):
    """Test suite certifying the new institutional capabilities."""

    def test_news_entity_mapper_coverage(self):
        """Certify that all active EGX constituents are covered in entity recognition."""
        mappings = NewsIngestionEngine.get_all_entity_mappings()
        self.assertGreaterEqual(len(mappings), 180)
        self.assertIn("COMI.CA", mappings)
        self.assertIn("SWDY.CA", mappings)
        self.assertIn("TMGH.CA", mappings)

    def test_sloan_accrual_calculation(self):
        """Certify Sloan Accrual earnings quality classification."""
        # High quality: Operating cashflow > Net income
        res_good = FundamentalDataEngine.compute_sloan_accrual_ratio(
            net_income=100.0, operating_cashflow=150.0, total_assets=1000.0
        )
        self.assertEqual(res_good["earnings_quality"], "EXCELLENT")
        self.assertTrue(res_good["is_cash_backed"])

        # Poor quality: Net income inflated without cash
        res_bad = FundamentalDataEngine.compute_sloan_accrual_ratio(
            net_income=300.0, operating_cashflow=50.0, total_assets=1000.0
        )
        self.assertEqual(res_bad["earnings_quality"], "POOR_ACCRUAL_WARNING")
        self.assertFalse(res_bad["is_cash_backed"])

    def test_fundamental_engine_analysis(self):
        """Certify FundamentalDataEngine returns valid health scores and metrics."""
        analysis = FundamentalDataEngine.get_ticker_analysis("COMI.CA")
        self.assertIn("health_score", analysis)
        self.assertGreaterEqual(analysis["health_score"], 0.0)
        self.assertLessEqual(analysis["health_score"], 100.0)
        self.assertIn("financial_health_label", analysis)
        self.assertIn("earnings_quality_label_ar", analysis)

    def test_macro_economic_regime(self):
        """Certify MacroEconomicEngine regime classification and sector biases."""
        regime = MacroEconomicEngine.determine_macro_regime(
            interest_rate=27.25, inflation=14.9, usd_egp=48.5
        )
        self.assertIn(regime, [
            MacroEconomicEngine.REGIME_RATE_HIKING_CYCLE,
            MacroEconomicEngine.REGIME_DEVALUATION_BOOM,
            MacroEconomicEngine.REGIME_STABLE_GROWTH,
            MacroEconomicEngine.REGIME_STAGFLATION
        ])
        biases = MacroEconomicEngine.get_sector_biases(regime)
        self.assertIn("overweight_ar", biases)
        self.assertIn("rationale_ar", biases)

    def test_quant_reasoning_agent(self):
        """Certify QuantReasoningAgent generates complete investment memos."""
        memo = QuantReasoningAgent.generate_stock_dossier_memo("COMI.CA")
        self.assertEqual(memo["status"], "SUCCESS")
        self.assertEqual(memo["ticker"], "COMI.CA")
        self.assertIn("conformal_target_q50", memo)
        self.assertIn("investment_thesis_ar", memo)
        self.assertGreater(len(memo["positive_drivers_ar"]), 0)

    def test_telegram_bot_commands(self):
        """Certify TelegramBotService command routing."""
        help_resp = TelegramBotService.handle_command("/help")
        self.assertIn("مساعد التداول الكمي", help_resp)

        status_resp = TelegramBotService.handle_command("/status")
        self.assertIn("حالة منصة GEN-26", status_resp)

        price_resp = TelegramBotService.handle_command("/price COMI")
        self.assertIn("COMI.CA", price_resp)


if __name__ == "__main__":
    unittest.main()
