#!/usr/bin/env python3
# =============================================================================
# tests/test_broker_execution.py — Institutional Tests for Algo Broker Execution
# Validates:
# 1. BrokerAPIClient initialization and Sandbox mode toggle.
# 2. Dynamic Slippage / Market Impact calculation vs ADV.
# 3. Market, Limit, and Trailing Stop order state machine (PENDING/FILLED/CANCELED).
# 4. Order cancellation safety.
# 5. Order blotter and REST API endpoints.
# =============================================================================

import os
import sys
import unittest
import json

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.broker_execution_engine import BrokerExecutionEngine, BrokerAPIClient, OrderStatus, OrderType, OrderSide
from dashboard.app import app


class TestBrokerExecutionEngine(unittest.TestCase):

    def setUp(self):
        self.engine = BrokerExecutionEngine(sandbox_mode=True)
        self.app = app.test_client()
        self.app.testing = True

    def test_01_broker_api_client_alias_and_sandbox(self):
        """Verify BrokerAPIClient class exists and default is sandbox mode."""
        self.assertTrue(self.engine.sandbox_mode)
        client = BrokerAPIClient(sandbox_mode=True)
        self.assertIsInstance(client, BrokerExecutionEngine)

    def test_02_dynamic_slippage_market_impact(self):
        """Verify dynamic slippage scales with order size vs Average Daily Volume."""
        market_price = 100.0
        # Small order: 500 shares
        slip_small, exec_small = self.engine.calculate_market_impact("COMI.CA", 500, market_price, side=OrderSide.BUY)
        # Large order: 50,000 shares
        slip_large, exec_large = self.engine.calculate_market_impact("COMI.CA", 50_000, market_price, side=OrderSide.BUY)

        self.assertGreaterEqual(slip_small, 0.0)
        self.assertGreater(slip_large, slip_small)
        self.assertGreater(exec_large, exec_small)
        self.assertGreater(exec_small, market_price)

    def test_03_submit_market_order_sandbox_fill(self):
        """Verify market order in sandbox executes immediately with filled status."""
        res = self.engine.submit_market_order("COMI.CA", OrderSide.BUY, 250, price_hint=138.80)
        self.assertEqual(res["status"], OrderStatus.FILLED)
        self.assertIn("order_id", res)
        order = res["order"]
        self.assertEqual(order["ticker"], "COMI.CA")
        self.assertEqual(order["side"], "BUY")
        self.assertEqual(order["order_type"], OrderType.MARKET)
        self.assertGreater(order["executed_price"], 0.0)
        self.assertEqual(order["quantity"], 250)
        self.assertEqual(order["total_value_egp"], round(order["executed_price"] * 250, 2))

    def test_04_submit_limit_order(self):
        """Verify limit order submission and status."""
        # Limit buy far below market -> PENDING
        res = self.engine.submit_limit_order("COMI.CA", OrderSide.BUY, 100, limit_price=50.0)
        self.assertIn(res["status"], [OrderStatus.PENDING, OrderStatus.FILLED])
        self.assertIn("order_id", res)

    def test_05_submit_trailing_stop(self):
        """Verify trailing stop order calculation."""
        res = self.engine.submit_trailing_stop("SWDY.CA", 300, trail_pct=5.0, activation_price=120.0)
        self.assertEqual(res["status"], OrderStatus.PENDING)
        order = res["order"]
        self.assertEqual(order["trail_pct"], 5.0)
        self.assertEqual(order["current_stop_price"], 114.0)  # 120 * 0.95

    def test_06_cancel_order(self):
        """Verify order cancellation state machine."""
        limit_res = self.engine.submit_limit_order("TMGH.CA", OrderSide.BUY, 50, limit_price=10.0)
        order_id = limit_res["order_id"]
        if limit_res["status"] == OrderStatus.PENDING:
            cancel_res = self.engine.cancel_order(order_id)
            self.assertEqual(cancel_res["status"], OrderStatus.CANCELED)

    def test_07_api_execution_endpoints(self):
        """Verify REST API GET /api/execution/orders and POST /api/execution/order/submit."""
        # 1. GET blotter
        get_res = self.app.get("/api/execution/orders")
        self.assertEqual(get_res.status_code, 200)
        data = get_res.get_json()
        self.assertIn("orders", data)
        self.assertIn("sandbox_mode", data)

        # 2. POST submit order
        post_payload = {
            "ticker": "COMI.CA",
            "side": "BUY",
            "quantity": 150,
            "order_type": "MARKET",
            "price": 138.80
        }
        post_res = self.app.post("/api/execution/order/submit",
                                 data=json.dumps(post_payload),
                                 content_type="application/json")
        self.assertEqual(post_res.status_code, 200)
        submit_data = post_res.get_json()
        self.assertEqual(submit_data["status"], OrderStatus.FILLED)


if __name__ == "__main__":
    unittest.main()
