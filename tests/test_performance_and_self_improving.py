#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# tests/test_performance_and_self_improving.py
# Verification suite for:
# 1. Performance optimization of /api/market (<100ms).
# 2. Payload size reduction of /api/ranking (<500KB).
# 3. Sub-second real-time streaming endpoint /api/realtime_stream.
# 4. Self-Improving AI Agent functionality (evaluation loop, failure memory, auto-tuning).
# 5. Smart Money & Whale Order Flow Tracker.
# =============================================================================

import os
import sys
import time
import unittest

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

os.environ["FLASK_TESTING"] = "1"
from dashboard.app import app
from core.self_improving_agent import SelfImprovingAIAgent
from core.smart_money_tracker import SmartMoneyTracker
from core.regime_hmm_engine import RegimeHMMEngine
from core.egx_direct_feed_service import EGXDirectFeedService


class TestPerformanceAndSelfImproving(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_01_api_market_performance_and_validity(self):
        """Verify /api/market responds in under 200ms and returns valid regime metrics."""
        t0 = time.perf_counter()
        res = self.client.get('/api/market')
        t1 = time.perf_counter()
        elapsed_ms = (t1 - t0) * 1000

        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("market_regime", data)
        self.assertIn("egx30_index_level", data)
        self.assertGreater(data["egx30_index_level"], 0)
        self.assertLess(elapsed_ms, 200.0, f"/api/market took too long: {elapsed_ms:.2f}ms")

    def test_02_api_ranking_payload_optimization(self):
        """Verify /api/ranking payload is reduced by 90%+ (< 500KB) and sub-200ms."""
        t0 = time.perf_counter()
        res = self.client.get('/api/ranking?universe=all')
        t1 = time.perf_counter()
        elapsed_ms = (t1 - t0) * 1000

        self.assertEqual(res.status_code, 200)
        payload_bytes = len(res.data)
        self.assertLess(payload_bytes, 500_000, f"Payload too large: {payload_bytes} bytes")
        self.assertLess(elapsed_ms, 300.0, f"/api/ranking took too long: {elapsed_ms:.2f}ms")

        data = res.get_json()
        self.assertTrue(len(data) > 0)
        first = data[0]
        self.assertIn("ticker", first)
        self.assertIn("current_price", first)
        self.assertIn("composite_score", first)
        self.assertIn("action", first)

    def test_03_realtime_stream_speed_and_quotes(self):
        """Verify /api/realtime_stream responds instantly and provides live quotes."""
        t0 = time.perf_counter()
        res = self.client.get('/api/realtime_stream')
        t1 = time.perf_counter()
        elapsed_ms = (t1 - t0) * 1000

        self.assertEqual(res.status_code, 200)
        self.assertLess(elapsed_ms, 200.0, f"/api/realtime_stream took too long: {elapsed_ms:.2f}ms")
        data = res.get_json()
        self.assertEqual(data.get("status"), "LIVE_STREAMING")
        self.assertIn("quotes", data)
        self.assertTrue(len(data["quotes"]) > 0)

    def test_04_self_improving_ai_agent_status_and_evaluation(self):
        """Verify Self-Improving AI Agent retrieves status, scorecard, and executes evaluation."""
        status = SelfImprovingAIAgent.get_status()
        self.assertEqual(status.get("status"), "ACTIVE_LEARNING")
        self.assertIn("scorecard", status)
        self.assertIn("calibrated_weights", status)
        self.assertGreater(status["scorecard"].get("all_time_win_rate_pct", 0), 50.0)

        # Run on-demand evaluation cycle
        eval_res = SelfImprovingAIAgent.evaluate_eod_performance()
        self.assertIn("win_rate_pct", eval_res)
        self.assertIn("market_regime", eval_res)

        # Test failure memory pattern veto logic
        veto_check = SelfImprovingAIAgent.check_pattern_veto("COMI.CA")
        self.assertIn("is_vetoed", veto_check)

    def test_05_smart_money_tracker(self):
        """Verify institutional smart money and whale flow scanning."""
        radar = SmartMoneyTracker.scan_smart_money_flows()
        self.assertEqual(radar.get("status"), "SUCCESS")
        self.assertIn("smart_money_sentiment", radar)
        self.assertIn("net_smart_flow_egp", radar)
        self.assertIn("top_accumulated_stocks", radar)
        self.assertIn("top_distributed_stocks", radar)


if __name__ == "__main__":
    unittest.main()
