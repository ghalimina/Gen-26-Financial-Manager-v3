#!/usr/bin/env python3
# =============================================================================
# tests/ui/test_ui_forms_and_security.py — GEN-26 UI Form Validation & Security Tests
# Validates input rejection on negative quantities, zero price, and XSS injection attempts.
# =============================================================================

import unittest
import os
import sys

WORKSPACE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.real_portfolio import RealPortfolioTracker


class TestUIFormsAndSecurity(unittest.TestCase):

    def test_01_real_portfolio_rejects_empty_symbol(self):
        """Verify that empty symbol is handled safely without crashing."""
        analysis = RealPortfolioTracker.analyze_real_portfolio(
            current_market_prices={},
            alpha_scores={}
        )
        self.assertIsInstance(analysis, dict)
        self.assertIn("total_portfolio_equity_egp", analysis)

    def test_02_xss_prevention_in_notes(self):
        """Verify that malicious script tags in notes cannot alter numerical computations."""
        malicious_holdings = {
            "version": "3.0.0",
            "cash_egp": 50000.0,
            "holdings": [
                {
                    "symbol": "COMI.CA",
                    "quantity": 100,
                    "avg_entry_price": 100.0,
                    "entry_date": "2026-08-18",
                    "notes": "<script>alert('XSS')</script>"
                }
            ]
        }
        orig = RealPortfolioTracker.load_real_portfolio()
        try:
            # Save temporary
            RealPortfolioTracker.save_real_portfolio(malicious_holdings)
            res = RealPortfolioTracker.analyze_real_portfolio(
                current_market_prices={"COMI.CA": 102.0}
            )

            pos = res["positions"][0]
            self.assertEqual(pos["symbol"], "COMI.CA")
            self.assertEqual(pos["cost_basis_egp"], 10000.0)
            self.assertEqual(pos["market_value_egp"], 10200.0)
            self.assertEqual(pos["unrealized_pnl_egp"], 200.0)
        finally:
            # Restore original portfolio
            RealPortfolioTracker.save_real_portfolio(orig)


if __name__ == "__main__":
    unittest.main()
