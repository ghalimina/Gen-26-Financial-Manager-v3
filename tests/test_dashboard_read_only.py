#!/usr/bin/env python3
# =============================================================================
# tests/test_dashboard_read_only.py — GEN-26 Dashboard Read-Only Security Tests
# Validates that the Flask dashboard exposes read-only endpoints and has zero order capability.
# =============================================================================

import unittest
import os
import sys

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from dashboard.app import app


class TestDashboardReadOnly(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()

    def test_01_index_html_renders(self):
        """Verify that GET / returns HTML control center with HTTP 200."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"GEN-26", response.data)
        # Check Arabic-first RTL indicators
        self.assertIn(b'dir="rtl"', response.data)
        self.assertTrue(b"GEN-26" in response.data)

    def test_02_api_status_read_only(self):
        """Verify GET /api/status returns paper mode only."""
        response = self.client.get("/api/status")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["deployment_mode"], "PAPER_ONLY")
        self.assertFalse(data["live_trading"])
        self.assertTrue(data["live_trading_blocked"])

    def test_03_api_progress_read_only(self):
        """Verify GET /api/progress returns 30-day gate information."""
        response = self.client.get("/api/progress")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertGreaterEqual(data["verified_sessions"], 0)
        self.assertEqual(data["total_sessions_required"], 30)

    def test_04_no_order_post_routes_exist(self):
        """Verify that attempting to POST an order fails with HTTP 404/405."""
        for endpoint in ["/api/order", "/api/trade", "/api/execute", "/order", "/trade"]:
            res = self.client.post(endpoint, json={"symbol": "COMI.CA", "qty": 100})
            self.assertIn(res.status_code, [404, 405])


if __name__ == "__main__":
    unittest.main()
