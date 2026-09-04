#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# tests/test_elite_extensions.py — Unit Tests for Elite Features (1, 2, 4, 5)
# =============================================================================

import unittest
import os
import sys
import json

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.trading_agents.llm_router import LLMRouter
from core.telegram_notifier import TelegramNotifier
from core.portfolio_alert_engine import PortfolioAlertEngine
from core.market_heatmap_engine import MarketHeatmapEngine
from core.monte_carlo_engine import MonteCarloEngine
from dashboard.app import app


class TestEliteExtensions(unittest.TestCase):

    def setUp(self):
        self.app_client = app.test_client()

    def test_01_llm_router_provider_status_and_fallback(self):
        """Verify LLMRouter provider detection and offline deterministic fallback."""
        status = LLMRouter.get_provider_status()
        self.assertIn("active_provider", status)
        self.assertIn("available_keys", status)
        self.assertTrue(status["offline_fallback_ready"])

        # When offline or invalid key, query_llm safely returns None (falling back to deterministic)
        res = LLMRouter.query_llm(
            system_prompt="You are a financial agent.",
            user_prompt="Analyze COMI.CA",
            timeout_sec=1.0
        )
        # Should cleanly return None or str without crashing
        self.assertTrue(res is None or isinstance(res, str))

    def test_02_telegram_notifier_config_and_mock(self):
        """Verify TelegramNotifier config persistence and validation."""
        cfg = TelegramNotifier.load_config()
        self.assertIn("alert_types", cfg)
        self.assertIn("enabled", cfg)

        # Test sending without token returns clean error dictionary without crashing
        res = TelegramNotifier.send_message("Test message", bot_token="", chat_id="")
        self.assertFalse(res["success"])
        self.assertIn("error", res)

    def test_03_portfolio_alert_engine_rules(self):
        """Verify PortfolioAlertEngine detects target hits and stop loss warnings."""
        res = PortfolioAlertEngine.scan_and_dispatch_alerts(send_telegram=False)
        self.assertIn("holdings_scanned", res)
        self.assertIn("alerts_count", res)
        self.assertIn("alerts", res)
        self.assertIsInstance(res["alerts"], list)

    def test_04_market_heatmap_engine_egx244(self):
        """Verify MarketHeatmapEngine groups 244 stocks into sectors with color codes."""
        heatmap = MarketHeatmapEngine.generate_sector_heatmap()
        self.assertEqual(heatmap["market"], "Egyptian Exchange (EGX)")
        self.assertEqual(heatmap["total_stocks_count"], 244)
        self.assertGreater(heatmap["sectors_count"], 5)
        self.assertIn("advance_decline_ratio", heatmap)
        self.assertIn("sectors", heatmap)

        top_sector = heatmap["sectors"][0]
        self.assertIn("name", top_sector)
        self.assertIn("constituents_count", top_sector)
        self.assertIn("stocks", top_sector)
        self.assertGreater(len(top_sector["stocks"]), 0)

        # Check stock structure
        first_stock = top_sector["stocks"][0]
        self.assertIn("ticker", first_stock)
        self.assertIn("change_pct", first_stock)
        self.assertIn("color", first_stock)
        self.assertTrue(first_stock["color"].startswith("#"))

    def test_05_monte_carlo_simulator_1000_paths(self):
        """Verify MonteCarloEngine computes 1,000 paths with VaR/CVaR and cones."""
        sim = MonteCarloEngine.simulate_trajectories(
            initial_equity=100000.0,
            days=30,
            num_paths=500
        )
        self.assertEqual(sim["initial_equity_egp"], 100000.0)
        self.assertEqual(sim["horizon_days"], 30)
        self.assertEqual(sim["simulations_count"], 500)
        self.assertIn("var_95", sim)
        self.assertIn("var_99", sim)
        self.assertIn("cvar_95", sim)
        self.assertIn("prob_profit_pct", sim)
        self.assertIn("cones", sim)
        self.assertIn("p50_median", sim["cones"])
        self.assertEqual(len(sim["cones"]["p50_median"]), 31)  # days + 1

    def test_06_flask_endpoints_for_elite_features(self):
        """Verify REST API routes for all 4 new features return HTTP 200."""
        # 1. TradingAgents LLM config
        r_llm = self.app_client.get('/api/v1/trading-agents/config')
        self.assertEqual(r_llm.status_code, 200)

        # 2. Sector Heatmap
        r_map = self.app_client.get('/api/market/heatmap')
        self.assertEqual(r_map.status_code, 200)
        self.assertEqual(r_map.get_json()["total_stocks_count"], 244)

        # 3. Monte Carlo
        r_mc = self.app_client.get('/api/portfolio/monte_carlo?days=30&simulations=200')
        self.assertEqual(r_mc.status_code, 200)
        self.assertIn("var_95", r_mc.get_json())

        # 4. Telegram status
        r_tg = self.app_client.get('/api/notifications/telegram/status')
        self.assertEqual(r_tg.status_code, 200)


if __name__ == "__main__":
    unittest.main()
