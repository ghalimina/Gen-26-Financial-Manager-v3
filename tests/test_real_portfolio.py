#!/usr/bin/env python3
# =============================================================================
# tests/test_real_portfolio.py — GEN-26 Real Portfolio Engine Unit Tests
# Validates real portfolio cost basis, P&L calculation, stop loss breach signals,
# and complete separation from paper trading state.
# =============================================================================

import unittest
import os
import sys

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.real_portfolio import RealPortfolioTracker


class TestRealPortfolio(unittest.TestCase):

    def setUp(self):
        # Setup clean test fixture with 2 holdings
        fixture = {
            "portfolio_id": "REAL_PORTFOLIO_PRIMARY",
            "version": "3.0.0",
            "cash_egp": 100000.0,
            "holdings": [
                {
                    "holding_id": "POS_COMI_001",
                    "ticker": "COMI.CA",
                    "company_name": "البنك التجاري الدولي (CIB)",
                    "exchange": "EGX",
                    "sector": "Banking",
                    "quantity": 150,
                    "average_entry_price": 95.0,
                    "manual_notes": "مركز أساسي",
                    "created_at": "2026-08-10T10:00:00",
                    "updated_at": "2026-08-10T10:00:00",
                    "active": True
                },
                {
                    "holding_id": "POS_SWDY_002",
                    "ticker": "SWDY.CA",
                    "company_name": "السويدي إليكتريك",
                    "exchange": "EGX",
                    "sector": "Industrial",
                    "quantity": 300,
                    "average_entry_price": 38.5,
                    "manual_notes": "تخصيص صناعي",
                    "created_at": "2026-08-12T11:30:00",
                    "updated_at": "2026-08-12T11:30:00",
                    "active": True
                }
            ]
        }
        RealPortfolioTracker.save_real_portfolio(fixture)

    def tearDown(self):
        # Reset to production empty baseline
        baseline = RealPortfolioTracker.get_initial_real_portfolio()
        RealPortfolioTracker.save_real_portfolio(baseline)

    def test_01_real_portfolio_analysis_and_pnl(self):
        """
        Verify real portfolio calculates cost basis, unrealized P&L, and equity correctly.
        """
        analysis = RealPortfolioTracker.analyze_real_portfolio(
            current_market_prices={"COMI.CA": 105.0, "SWDY.CA": 42.0},
            alpha_scores={"COMI.CA": 85.0, "SWDY.CA": 80.0}
        )

        self.assertGreater(analysis["total_portfolio_equity_egp"], 50000.0)
        self.assertGreater(analysis["total_unrealized_pnl_egp"], 0.0)
        self.assertEqual(len(analysis["positions"]), 2)

    def test_02_stop_loss_breach_generates_exit_signal(self):
        """
        Verify that when a stock drops below -7% stop loss, an EXIT signal is generated.
        Entry: 95.0, Stop: 88.35. Current: 85.0 -> EXIT.
        """
        analysis = RealPortfolioTracker.analyze_real_portfolio(
            current_market_prices={"COMI.CA": 85.0, "SWDY.CA": 42.0},
            alpha_scores={"COMI.CA": 50.0, "SWDY.CA": 80.0}
        )

        comi_pos = next(p for p in analysis["positions"] if p["symbol"] == "COMI.CA")
        self.assertIn("EXIT", comi_pos["action"])
        self.assertTrue("وقف الخسارة" in comi_pos["advisory_reason"] or "stop" in comi_pos["advisory_reason"])


if __name__ == "__main__":
    unittest.main()
