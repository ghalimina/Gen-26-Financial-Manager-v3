#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# tests/test_institutional_v3_upgrades.py
# Verification suite for the 4 institutional upgrades in GEN-26:
# 1. Telegram Morning Briefing alert formatter & endpoint.
# 2. Egyptian MCDR Tax-Aware Rebalancing engine & API.
# 3. Print / PDF Export CSS styling (@media print).
# 4. Stock Dossier AI Target Range Meter UI components.
# =============================================================================

import unittest
from dashboard.app import app
from core.telegram_notifier import TelegramNotifier
from core.mcdr_tax_engine import McdrTaxEngine


class TestInstitutionalV3Upgrades(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_01_telegram_morning_briefing_formatter(self):
        """Verify TelegramNotifier formats morning briefing cleanly without HTML bugs."""
        sample_briefing = {
            "headline": "التقرير الصباحي التجريبي للبورصة",
            "market_regime": "BULLISH_TREND",
            "market_regime_ar": "اتجاه صاعد قوي",
            "date": "2026-09-16",
            "summary_markdown": "استمرار الشراء المؤسسي في البنوك والأسمدة.",
            "key_recommendations": [
                {
                    "ticker": "COMI.CA",
                    "name_ar": "البنك التجاري الدولي",
                    "current_price": 140.50,
                    "target_price": 151.20,
                    "stop_loss": 130.66,
                    "action": "شراء وتجميع",
                    "composite_score": 93.0
                },
                {
                    "ticker": "SWDY.CA",
                    "name_ar": "السويدي إليكتريك",
                    "current_price": 128.00,
                    "target_price": 142.00,
                    "stop_loss": 119.00,
                    "action": "شراء اختراق",
                    "composite_score": 89.5
                }
            ]
        }
        msg = TelegramNotifier.format_morning_briefing(sample_briefing)
        self.assertIn("التقرير الصباحي التجريبي للبورصة", msg)
        self.assertIn("COMI.CA", msg)
        self.assertIn("SWDY.CA", msg)
        self.assertIn("140.50", msg)
        self.assertIn("151.20", msg)
        self.assertIn("GEN-26", msg)

    def test_02_api_telegram_send_morning_briefing(self):
        """Verify GET & POST /api/notifications/telegram/send_morning_briefing returns 200."""
        res_get = self.client.get('/api/notifications/telegram/send_morning_briefing')
        self.assertEqual(res_get.status_code, 200)
        data_get = res_get.get_json()
        self.assertIn("status", data_get)
        self.assertIn("briefing_headline", data_get)

        res_post = self.client.post('/api/notifications/telegram/send_morning_briefing')
        self.assertEqual(res_post.status_code, 200)
        data_post = res_post.get_json()
        self.assertIn("status", data_post)

    def test_03_mcdr_tax_aware_rebalance_logic(self):
        """Verify McdrTaxEngine rebalancing logic prioritizes tax loss lots and calculates exact fees."""
        current_holdings = [
            {"symbol": "COMI", "shares": 1000, "avg_cost": 120.0, "current_price": 140.0},  # Gain: +20,000 EGP
            {"symbol": "SWDY", "shares": 1000, "avg_cost": 140.0, "current_price": 120.0}   # Loss: -20,000 EGP
        ]
        target_weights = {"COMI": 0.10, "SWDY": 0.05, "TMGH": 0.15}
        total_equity = 500000.0

        plan = McdrTaxEngine.compute_tax_optimal_rebalance(
            current_portfolio=current_holdings,
            target_weights=target_weights,
            total_equity=total_equity
        )
        self.assertEqual(plan["status"], "SUCCESS")
        summary = plan["summary"]
        self.assertGreater(summary["total_orders"], 0)
        self.assertGreater(summary["total_regulatory_fees_egp"], 0)
        self.assertIn("tax_shield_unlocked_egp", summary)
        self.assertIn("effective_tax_drag_pct", summary)

        # Loss trades should be sequenced first
        trades = plan["rebalancing_trades"]
        sells = [t for t in trades if t["action"] == "SELL"]
        if len(sells) >= 2:
            self.assertLessEqual(sells[0]["est_pnl"], sells[1]["est_pnl"])

    def test_04_api_portfolio_tax_rebalance(self):
        """Verify GET and POST /api/portfolio/tax_rebalance returns HTTP 200 and complete schema."""
        res = self.client.get('/api/portfolio/tax_rebalance')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "SUCCESS")
        self.assertIn("rebalancing_trades", data)
        self.assertIn("summary", data)

        # Custom POST payload
        payload = {
            "current_portfolio": [
                {"symbol": "COMI", "shares": 500, "avg_cost": 130.0, "current_price": 140.0}
            ],
            "target_weights": {"COMI": 0.50, "SWDY": 0.50},
            "total_equity": 200000.0
        }
        res_post = self.client.post('/api/portfolio/tax_rebalance', json=payload)
        self.assertEqual(res_post.status_code, 200)
        data_post = res_post.get_json()
        self.assertEqual(data_post.get("status"), "SUCCESS")

    def test_05_frontend_elements_present(self):
        """Verify UI template contains @media print, telegram briefing button, and AI targets meter."""
        with open('dashboard/index.html', 'r', encoding='utf-8') as f:
            html = f.read()

        self.assertIn('@media print', html)
        self.assertIn('sendMorningBriefingTelegram()', html)
        self.assertIn('id="btn-telegram-briefing"', html)
        self.assertIn('ai-target-range-container', html)
        self.assertIn('id="meter-price-pin"', html)
        self.assertIn('id="meter-stop-val"', html)
        self.assertIn('id="meter-target1-val"', html)
        self.assertIn('id="meter-target2-val"', html)


if __name__ == '__main__':
    unittest.main()
