#!/usr/bin/env python3
# =============================================================================
# tests/test_dashboard_read_only.py — GEN-26 Dashboard Read-Only Security & UI Tests
# Validates that the Flask dashboard exposes read-only endpoints, blocks live money orders,
# and renders the interactive Research Lab Tab & 10 Books Quant Dashboard.
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

    def test_05_research_lab_ui_and_council_cards_rendered(self):
        """
        Verify that #tab-research-lab exists and contains:
        - 7-Agent Council Deliberation Card (#council-deliberation-card)
        - 10 Books Quant Metrics Card (#quant-books-card)
        - Research Experiments Table (#research-experiments-card / tbody)
        - Episodic Failure Memory Card (#failure-memory-card)
        """
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html_str = response.data.decode("utf-8")

        self.assertIn('id="tab-research-lab"', html_str)
        self.assertIn('id="council-deliberation-card"', html_str)
        self.assertIn('id="quant-books-card"', html_str)
        self.assertIn('id="research-experiments-card"', html_str)
        self.assertIn('id="failure-memory-card"', html_str)
        self.assertIn('triggerResearchCycleUI()', html_str)

    def test_06_research_api_endpoints(self):
        """
        Verify /api/research/experiments and /api/research/memory/failures return HTTP 200 with valid JSON.
        """
        res_exp = self.client.get("/api/research/experiments")
        self.assertEqual(res_exp.status_code, 200)
        data_exp = res_exp.get_json()
        self.assertEqual(data_exp["status"], "SUCCESS")
        self.assertIn("experiments", data_exp)

        res_fail = self.client.get("/api/research/memory/failures")
        self.assertEqual(res_fail.status_code, 200)
        data_fail = res_fail.get_json()
        self.assertEqual(data_fail["status"], "SUCCESS")
        self.assertIn("failure_memory", data_fail)

    def test_07_books_api_endpoints(self):
        """
        Verify /api/books/piotroski/COMI.CA and /api/books/psychology/status return HTTP 200.
        """
        res_pio = self.client.get("/api/books/piotroski/COMI.CA")
        self.assertEqual(res_pio.status_code, 200)
        data_pio = res_pio.get_json()
        self.assertEqual(data_pio["status"], "SUCCESS")
        self.assertIn("f_score", data_pio["data"])

        res_psych = self.client.get("/api/books/psychology/status")
        self.assertEqual(res_psych.status_code, 200)
        data_psych = res_psych.get_json()
        self.assertEqual(data_psych["status"], "SUCCESS")
        self.assertIn("psychology_guard", data_psych)


if __name__ == "__main__":
    unittest.main()
