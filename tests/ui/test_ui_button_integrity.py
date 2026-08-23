#!/usr/bin/env python3
# =============================================================================
# tests/ui/test_ui_button_integrity.py — GEN-26 UI Button & Navigation Forensic Tests
# Validates that all interactive navigation items and action buttons exist with valid IDs.
# =============================================================================

import unittest
import os
import sys

WORKSPACE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)


class TestUIButtonIntegrity(unittest.TestCase):

    def setUp(self):
        html_path = os.path.join(WORKSPACE, "dashboard", "index.html")
        with open(html_path, "r", encoding="utf-8") as f:
            self.html = f.read()

    def test_01_all_12_navigation_buttons_exist(self):
        """Verify all 12 navigation tabs have corresponding ID elements."""
        nav_ids = [
            "nav-overview", "nav-ranking", "nav-details", "nav-real_portfolio",
            "nav-paper_portfolio", "nav-signals", "nav-risk_center", "nav-stress_center",
            "nav-paper_vs_bt", "nav-observatory", "nav-universe_audit", "nav-health"
        ]
        for nid in nav_ids:
            self.assertIn(f'id="{nid}"', self.html)

    def test_02_stress_test_action_buttons_exist(self):
        """Verify stress test action buttons have onclick handlers."""
        self.assertIn('id="btn-stress-flash-crash"', self.html)
        self.assertIn('id="btn-stress-liquidity-drop"', self.html)
        self.assertIn('id="btn-stress-limit-up"', self.html)

    def test_03_real_portfolio_modal_buttons_exist(self):
        """Verify real portfolio position addition buttons."""
        self.assertIn('id="btn-add-real-position"', self.html)
        self.assertIn('id="btn-submit-real-pos"', self.html)


if __name__ == "__main__":
    unittest.main()
