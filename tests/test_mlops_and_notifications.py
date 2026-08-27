#!/usr/bin/env python3
# =============================================================================
# tests/test_mlops_and_notifications.py — Master Unit Tests for MLOps & Ops Layer
# Validates:
# 1. MLOps continuous learning pipeline & dynamic drift triggers.
# 2. Telegram Bot notification gateway payload formatting (Mocked).
# 3. EGX Insider trading & board deals tracker.
# 4. Tax-Loss harvesting advisor & margin financing cost calculator.
# 5. REST API endpoints and UI element bindings.
# =============================================================================

import os
import sys
import unittest
from unittest.mock import patch
import json

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.mlops_pipeline import MLOpsPipeline
from core.notification_gateway import TelegramNotifier
from core.insider_trading_engine import InsiderTradingEngine
from core.tax_margin_manager import TaxMarginManager
from dashboard.app import app


class TestMLOpsAndNotifications(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_01_mlops_drift_triggers_assessment(self):
        """Verify MLOps drift trigger evaluates rolling accuracy and macro regime."""
        drift = MLOpsPipeline.check_drift_triggers()
        self.assertIn("needs_emergency_retrain", drift)
        self.assertIn("rolling_accuracy_pct", drift)
        self.assertIn("next_scheduled_retrain", drift)
        self.assertIn("الجمعة", drift["next_scheduled_retrain"])

    def test_02_mlops_retrain_execution(self):
        """Verify MLOps retraining pipeline executes safely and writes metadata."""
        res = MLOpsPipeline.execute_retraining_pipeline(trigger_source="UNIT_TEST_TRIGGER")
        self.assertEqual(res["status"], "RETRAIN_SUCCESS")
        self.assertEqual(res["trigger_source"], "UNIT_TEST_TRIGGER")
        self.assertIn("last_retrain_timestamp", res)

    def test_03_telegram_notifier_formatting_and_mock(self):
        """Verify TelegramNotifier dispatches correctly formatted Markdown alerts in Mock mode."""
        # 1. Order Executed Alert
        order_sample = {
            "order_id": "ORD-TEST-99",
            "ticker": "COMI.CA",
            "side": "BUY",
            "quantity": 500,
            "executed_price": 138.80,
            "slippage_pct": 0.045,
            "total_value_egp": 69400.0
        }
        res_order = TelegramNotifier.send_order_executed_alert(order_sample)
        self.assertTrue(res_order.get("delivered"))
        self.assertIn("status", res_order)

        # 2. Stop Loss Alert
        res_stop = TelegramNotifier.send_stop_loss_hit_alert("SWDY.CA", 108.0, 107.5, -6.8)
        self.assertTrue(res_stop.get("delivered"))

        # 3. Macro Shock Alert
        res_macro = TelegramNotifier.send_macro_shock_alert("EASING_DISINFLATION", 19.75, 50.80, "CBE Rate Decision")
        self.assertTrue(res_macro.get("delivered"))

    @patch("core.insider_trading_engine.InsiderTradingEngine.fetch_insider_deals")
    def test_04_insider_trading_engine_signals(self, mock_fetch):
        """Verify EGX Insider Trading Engine computes signals and boosts confidence."""
        # COMI.CA has recorded executive buying -> positive signal
        mock_fetch.return_value = [
            {
                "transaction_type": "BUY",
                "shares_transacted": 150_000,
                "price_egp": 136.20,
                "total_value_egp": 20_430_000.0,
                "insider_title": "عضو مجلس إدارة تنفيذي ومجموعة مرتبطة"
            }
        ]
        comi_insider = InsiderTradingEngine.evaluate_insider_activity("COMI.CA")
        self.assertEqual(comi_insider["ticker"], "COMI.CA")
        self.assertGreater(comi_insider["insider_action"], 0.0)
        self.assertGreater(comi_insider["confidence_boost_pct"], 0.0)
        self.assertTrue("شراء" in comi_insider["action_badge_ar"] or "تجميع" in comi_insider["action_badge_ar"])

        # Unknown / neutral ticker -> 0.0 signal
        mock_fetch.return_value = []
        neutral_insider = InsiderTradingEngine.evaluate_insider_activity("UNKNOWN.CA")
        self.assertEqual(neutral_insider["insider_action"], 0.0)
        self.assertEqual(neutral_insider["confidence_boost_pct"], 0.0)

        # Market-wide deals list
        with patch("core.insider_trading_engine.InsiderTradingEngine.scrape_live_insider_deals") as mock_scrape:
            mock_scrape.return_value = [
                {"ticker": "SWDY.CA", "total_value_egp": 32_000_000.0},
                {"ticker": "COMI.CA", "total_value_egp": 20_000_000.0},
                {"ticker": "TMGH.CA", "total_value_egp": 7_000_000.0}
            ]
            all_deals = InsiderTradingEngine.get_market_wide_insider_deals()
            self.assertGreaterEqual(len(all_deals), 3)

    def test_05_tax_loss_harvesting_and_margin_manager(self):
        """Verify margin financing cost calculation and tax-loss harvesting evaluation."""
        # Margin cost: 200,000 EGP for 10 days at ~21.25%
        m_cost = TaxMarginManager.calculate_margin_financing_cost(200_000, days_held=10, cbe_lending_rate_pct=19.25)
        self.assertGreater(m_cost["margin_interest_cost_egp"], 0.0)
        self.assertAlmostEqual(m_cost["annual_margin_rate_pct"], 21.25, places=2)

        # Tax-loss harvesting: scans losing positions
        mock_positions = [
            {"ticker": "CCAP.CA", "shares": 10000, "unrealized_pnl_egp": -6000.0},
            {"ticker": "COMI.CA", "shares": 500, "unrealized_pnl_egp": 8000.0}
        ]
        harvest = TaxMarginManager.evaluate_tax_loss_harvesting(realized_gains_ytd_egp=50_000.0, open_positions=mock_positions)
        self.assertEqual(harvest["status"], "TAX_HARVESTING_EVALUATED")
        self.assertGreater(harvest["potential_tax_savings_egp"], 0.0)
        self.assertEqual(len(harvest["harvesting_candidates"]), 1)
        self.assertEqual(harvest["harvesting_candidates"][0]["ticker"], "CCAP.CA")

    def test_06_api_endpoints_mlops_insider_tax(self):
        """Verify REST API endpoints for MLOps, Insider Deals, and Tax Harvesting."""
        # 1. GET /api/mlops/status
        r_mlops = self.app.get("/api/mlops/status")
        self.assertEqual(r_mlops.status_code, 200)
        data_mlops = r_mlops.get_json()
        self.assertIn("mlops", data_mlops)
        self.assertIn("telegram", data_mlops)

        # 2. GET /api/insider/COMI.CA
        r_insider = self.app.get("/api/insider/COMI.CA")
        self.assertEqual(r_insider.status_code, 200)
        data_insider = r_insider.get_json()
        self.assertEqual(data_insider["ticker"], "COMI.CA")

        # 3. GET /api/tax/harvesting
        r_tax = self.app.get("/api/tax/harvesting")
        self.assertEqual(r_tax.status_code, 200)
        data_tax = r_tax.get_json()
        self.assertIn("potential_tax_savings_egp", data_tax)

    def test_07_ui_insider_and_mlops_elements_exist(self):
        """Verify UI index.html contains Insider and MLOps elements."""
        html_path = os.path.join(WORKSPACE, "dashboard", "index.html")
        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()

        self.assertIn('id="detail-insider-badge"', html)
        self.assertIn('id="detail-insider-summary"', html)
        self.assertIn('id="mlops-next-retrain-val"', html)
        self.assertIn('id="telegram-bot-status-val"', html)


if __name__ == "__main__":
    unittest.main()
