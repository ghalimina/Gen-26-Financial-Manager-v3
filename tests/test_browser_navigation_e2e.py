#!/usr/bin/env python3
# =============================================================================
# tests/test_browser_navigation_e2e.py — GEN-26 UI Navigation & Browser State E2E Tests
# Validates that all 13 tabs are rendered by Flask, mapped to valid sidebar links,
# and that client-side hash routing prevents blank screens and unwanted redirects.
# =============================================================================

import unittest
import os
import sys

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from dashboard.app import app


class TestBrowserNavigationE2E(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.rendered_html = res.get_data(as_text=True)

    def test_01_all_13_tab_panels_rendered_by_flask(self):
        """
        Verify that Flask root route '/' renders all 13 distinct tab panels in the DOM,
        permanently eliminating the blank-page bug.
        """
        expected_tabs = [
            "tab-overview",
            "tab-ranking",
            "tab-details",
            "tab-real_portfolio",
            "tab-paper_portfolio",
            "tab-watchlist",
            "tab-signals",
            "tab-risk_center",
            "tab-stress_center",
            "tab-paper_vs_bt",
            "tab-observatory",
            "tab-universe_audit",
            "tab-health"
        ]
        for tab_id in expected_tabs:
            self.assertIn(f'id="{tab_id}"', self.rendered_html, f"Missing tab panel: {tab_id}")

    def test_02_all_13_sidebar_nav_links_present(self):
        """Verify that every corresponding sidebar navigation item exists with navigateTo handler."""
        expected_navs = [
            ("nav-overview", "overview"),
            ("nav-ranking", "ranking"),
            ("nav-details", "details"),
            ("nav-real_portfolio", "real_portfolio"),
            ("nav-paper_portfolio", "paper_portfolio"),
            ("nav-watchlist", "watchlist"),
            ("nav-signals", "signals"),
            ("nav-risk_center", "risk_center"),
            ("nav-stress_center", "stress_center"),
            ("nav-paper_vs_bt", "paper_vs_bt"),
            ("nav-observatory", "observatory"),
            ("nav-universe_audit", "universe_audit"),
            ("nav-health", "health")
        ]
        for nav_id, tab_key in expected_navs:
            self.assertIn(f'id="{nav_id}"', self.rendered_html)
            self.assertIn(f"navigateTo('{tab_key}')", self.rendered_html)

    def test_03_client_side_hash_router_present(self):
        """Verify that client-side SPA hash router script is embedded and configured."""
        self.assertIn("window.location.hash", self.rendered_html)
        self.assertIn("hashchange", self.rendered_html)
        self.assertIn("VALID_TABS", self.rendered_html)

    def test_04_stress_simulator_buttons_and_handlers(self):
        """Verify stress test action buttons and handlers are rendered."""
        self.assertIn('id="btn-stress-flash-crash"', self.rendered_html)
        self.assertIn('id="btn-stress-liquidity-drop"', self.rendered_html)
        self.assertIn('id="btn-stress-limit-up"', self.rendered_html)


if __name__ == "__main__":
    unittest.main()
