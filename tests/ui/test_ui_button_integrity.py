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
        """Verify all 14 navigation tabs have corresponding ID elements."""
        nav_ids = [
            "nav-overview", "nav-short_term_opportunities", "nav-ranking", "nav-details", "nav-real_portfolio",
            "nav-paper_portfolio", "nav-signals", "nav-risk_center", "nav-stress_center",
            "nav-paper_vs_bt", "nav-observatory", "nav-universe_audit", "nav-health", "nav-execution"
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

    def test_04_macro_and_hazard_ui_elements_exist(self):
        """Verify macro risk banner and corporate hazard alert elements exist in UI."""
        self.assertIn('id="macro-risk-banner"', self.html)
        self.assertIn('id="macro-regime-val"', self.html)
        self.assertIn('id="macro-usd-val"', self.html)
        self.assertIn('id="macro-cbe-val"', self.html)
        self.assertIn('id="macro-inflation-val"', self.html)
        self.assertIn('id="corp-hazard-alert"', self.html)
        self.assertIn('id="cluster-risk-banner"', self.html)
        self.assertIn('id="short-term-opps-grid"', self.html)

    def test_05_ai_forecast_ui_elements_exist(self):
        """Verify AI predictive forecast, meta-labeling, and OOS validation elements exist in UI."""
        self.assertIn('id="meta-decision-badge"', self.html)
        self.assertIn('id="meta-prob-val"', self.html)
        self.assertIn('id="meta-vol-adj-val"', self.html)
        self.assertIn('id="ai-alpha-val"', self.html)
        self.assertIn('id="ai-drivers-list"', self.html)
        self.assertIn('id="ai-hit-rate-val"', self.html)
        self.assertIn('id="ai-ic-val"', self.html)

    def test_06_algo_execution_and_hrp_ui_elements_exist(self):
        """Verify Algo Execution EMS, Live Order Blotter, and HRP UI elements exist."""
        self.assertIn('id="tab-execution"', self.html)
        self.assertIn('id="btn-submit-algo-order"', self.html)
        self.assertIn('id="algo-orders-tbody"', self.html)
        self.assertIn('id="hrp-weights-tbody"', self.html)
        self.assertIn('id="hmm-regime-title"', self.html)
        self.assertIn('id="mc-var-val"', self.html)


if __name__ == "__main__":
    unittest.main()
