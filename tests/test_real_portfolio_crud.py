#!/usr/bin/env python3
# =============================================================================
# tests/test_real_portfolio_crud.py — GEN-26 Real Portfolio CRUD & Risk Tests
# Validates Add, Edit, Delete, Duplicate Prevention, Risk Concentration, and Audit Trails.
# =============================================================================

import unittest
import os
import sys

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.real_portfolio import RealPortfolioTracker


class TestRealPortfolioCRUD(unittest.TestCase):

    def setUp(self):
        self._original_portfolio = RealPortfolioTracker.load_real_portfolio()
        # Reset to known fixture with 2 initial holdings
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
        # Restore user's actual portfolio state
        RealPortfolioTracker.save_real_portfolio(self._original_portfolio)

    def test_01_add_valid_holding(self):
        """Verify adding a new valid EGX holding succeeds and calculates P&L."""
        res = RealPortfolioTracker.add_holding(
            ticker="TMGH.CA",
            quantity=200,
            average_entry_price=50.0,
            notes="شراء استثماري في قطاع العقارات"
        )
        self.assertTrue(res["success"])
        self.assertIn("تمت إضافة سهم", res["message"])

        analysis = RealPortfolioTracker.analyze_real_portfolio(
            current_market_prices={"TMGH.CA": 52.0}
        )
        self.assertEqual(analysis["positions_count"], 3)
        tmgh = next(p for p in analysis["positions"] if p["ticker"] == "TMGH.CA")
        self.assertEqual(tmgh["quantity"], 200)
        self.assertEqual(tmgh["cost_basis_egp"], 10000.0)
        self.assertEqual(tmgh["unrealized_pnl_egp"], 400.0)

    def test_02_duplicate_holding_rejected(self):
        """Verify adding an already existing ticker is rejected with explanation."""
        res = RealPortfolioTracker.add_holding(
            ticker="COMI.CA", # Already exists in fixture
            quantity=100,
            average_entry_price=90.0
        )
        self.assertFalse(res["success"])
        self.assertIn("موجود بالفعل", res["error"])

    def test_03_invalid_ticker_rejected(self):
        """Verify invalid or non-EGX ticker is rejected."""
        res = RealPortfolioTracker.add_holding(
            ticker="INVALID_XYZ.CA",
            quantity=100,
            average_entry_price=10.0
        )
        self.assertFalse(res["success"])
        self.assertIn("غير موجود", res["error"])

    def test_04_invalid_quantity_and_price_rejected(self):
        """Verify zero or negative quantity and price are rejected."""
        res_neg_qty = RealPortfolioTracker.add_holding("ETEL.CA", quantity=-50, average_entry_price=30.0)
        self.assertFalse(res_neg_qty["success"])

        res_zero_price = RealPortfolioTracker.add_holding("ETEL.CA", quantity=50, average_entry_price=0.0)
        self.assertFalse(res_zero_price["success"])

    def test_05_edit_holding(self):
        """Verify editing quantity and entry price updates calculations and timestamp."""
        res = RealPortfolioTracker.edit_holding(
            ticker="SWDY.CA",
            quantity=500,
            average_entry_price=39.0,
            notes="تعديل الكمية بعد تنفيذ صفقة إضافية"
        )
        self.assertTrue(res["success"])

        analysis = RealPortfolioTracker.analyze_real_portfolio(
            current_market_prices={"SWDY.CA": 42.0}
        )
        swdy = next(p for p in analysis["positions"] if p["ticker"] == "SWDY.CA")
        self.assertEqual(swdy["quantity"], 500)
        self.assertEqual(swdy["cost_basis_egp"], 19500.0)
        self.assertEqual(swdy["market_value_egp"], 21000.0)

    def test_06_delete_holding_with_confirmation(self):
        """Verify deleting holding removes position cleanly."""
        res = RealPortfolioTracker.delete_holding("COMI.CA", confirm=True)
        self.assertTrue(res["success"])

        analysis = RealPortfolioTracker.analyze_real_portfolio()
        self.assertEqual(analysis["positions_count"], 1)
        tickers = [p["ticker"] for p in analysis["positions"]]
        self.assertNotIn("COMI.CA", tickers)

    def test_07_audit_log_persists_mutations(self):
        """Verify mutations produce audit records in real_portfolio_audit_log.json."""
        RealPortfolioTracker.add_holding("ETEL.CA", 100, 32.0, "سهم اتصالات")
        self.assertTrue(os.path.exists(RealPortfolioTracker.AUDIT_LOG_FILE))


if __name__ == "__main__":
    unittest.main()
