#!/usr/bin/env python3
import unittest
import os
import sys
import tempfile
import json
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import portfolio_journal as pj


class TestPortfolioJournal(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.test_dir, "test_transactions.json")

    def tearDown(self):
        if os.path.exists(self.test_file):
            try:
                os.remove(self.test_file)
            except Exception:
                pass

    def test_01_add_manual_transaction(self):
        """Test adding manual transactions persists properly."""
        tx1 = pj.add_transaction(
            ticker="COMI.CA",
            action="BUY",
            quantity=10,
            price=130.0,
            date="2026-08-01",
            source="MANUAL",
            notes="Initial purchase",
            file_path=self.test_file
        )
        self.assertIsNotNone(tx1.get("transaction_id"))
        self.assertEqual(tx1["ticker"], "COMI.CA")
        self.assertEqual(tx1["quantity"], 10)
        self.assertEqual(tx1["price"], 130.0)
        self.assertEqual(tx1["source"], "MANUAL")

        # Verify on disk
        saved = pj.load_transactions(self.test_file)
        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0]["transaction_id"], tx1["transaction_id"])

    def test_02_edit_and_delete_transaction(self):
        """Test editing and deleting transactions."""
        tx = pj.add_transaction(
            ticker="SWDY.CA",
            action="BUY",
            quantity=20,
            price=115.0,
            date="2026-08-05",
            file_path=self.test_file
        )
        tx_id = tx["transaction_id"]

        # Edit
        updated = pj.update_transaction(tx_id, quantity=25, price=118.0, file_path=self.test_file)
        self.assertTrue(updated)

        saved = pj.load_transactions(self.test_file)
        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0]["quantity"], 25)
        self.assertEqual(saved[0]["price"], 118.0)

        # Delete
        deleted = pj.delete_transaction(tx_id, file_path=self.test_file)
        self.assertTrue(deleted)
        saved_after = pj.load_transactions(self.test_file)
        self.assertEqual(len(saved_after), 0)

    def test_03_confirm_from_suggestion_links_decision_id(self):
        """Test confirming from system suggestion correctly links decision_id."""
        mock_decision_id = "COMI.CA_2026-08-19 03:44_b4332169"
        tx = pj.add_transaction(
            ticker="COMI",
            action="BUY",
            quantity=50,
            price=138.5,
            source="SYSTEM_SUGGESTION",
            decision_id=mock_decision_id,
            notes="Confirmed via UI suggestion button",
            file_path=self.test_file
        )
        self.assertEqual(tx["ticker"], "COMI.CA")
        self.assertEqual(tx["source"], "SYSTEM_SUGGESTION")
        self.assertEqual(tx["decision_id"], mock_decision_id)

    def test_04_weighted_average_cost_basis(self):
        """
        Test multi-buy weighted average cost basis.
        Buy 10 @ 100 EGP + Buy 10 @ 120 EGP -> Expected Average Cost = 110 EGP
        """
        pj.add_transaction("TMGH.CA", "BUY", 10, 100.0, date="2026-08-01", file_path=self.test_file)
        pj.add_transaction("TMGH.CA", "BUY", 10, 120.0, date="2026-08-02", file_path=self.test_file)

        txs = pj.load_transactions(self.test_file)
        live_quotes = {"TMGH.CA": 125.0}
        perf = pj.compute_portfolio_performance(txs, live_quotes)

        self.assertEqual(len(perf["open_positions"]), 1)
        pos = perf["open_positions"][0]
        self.assertEqual(pos["ticker"], "TMGH.CA")
        self.assertEqual(pos["quantity"], 20)
        self.assertEqual(pos["avg_cost_price"], 110.0)
        self.assertEqual(pos["total_cost_basis"], 2200.0)
        self.assertEqual(pos["market_value"], 2500.0)
        self.assertEqual(pos["unrealized_pnl"], 300.0)
        self.assertEqual(pos["unrealized_pnl_pct"], round(300.0 / 2200.0 * 100, 2))

    def test_05_fifo_realized_pnl(self):
        """
        Test FIFO realized P&L matching:
        Buy 10 @ 100 (Lot 1)
        Buy 10 @ 120 (Lot 2)
        Sell 15 @ 130:
          - 10 matched from Lot 1 @ 100 -> P&L = 10 * (130 - 100) = +300
          - 5 matched from Lot 2 @ 120 -> P&L = 5 * (130 - 120) = +50
          - Total Realized P&L = +350 EGP
          - Remaining Open Lot: 5 @ 120 (Avg cost = 120 EGP, Cost basis = 600 EGP)
        """
        pj.add_transaction("ETEL.CA", "BUY", 10, 100.0, date="2026-08-01", file_path=self.test_file)
        pj.add_transaction("ETEL.CA", "BUY", 10, 120.0, date="2026-08-02", file_path=self.test_file)
        pj.add_transaction("ETEL.CA", "SELL", 15, 130.0, date="2026-08-05", file_path=self.test_file)

        txs = pj.load_transactions(self.test_file)
        live_quotes = {"ETEL.CA": 135.0}
        perf = pj.compute_portfolio_performance(txs, live_quotes)

        # Closed trades verification
        self.assertEqual(len(perf["closed_trades"]), 2)
        self.assertEqual(perf["total_realized_pnl"], 350.0)
        self.assertEqual(perf["closed_trades_count"], 2)
        self.assertEqual(perf["winning_trades_count"], 2)
        self.assertEqual(perf["win_rate_pct"], 100.0)

        # Open positions verification
        self.assertEqual(len(perf["open_positions"]), 1)
        open_pos = perf["open_positions"][0]
        self.assertEqual(open_pos["quantity"], 5)
        self.assertEqual(open_pos["avg_cost_price"], 120.0)
        self.assertEqual(open_pos["total_cost_basis"], 600.0)
        self.assertEqual(open_pos["market_value"], 5 * 135.0)
        self.assertEqual(open_pos["unrealized_pnl"], (5 * 135.0) - 600.0)

    def test_06_zero_interference_with_production_core(self):
        """
        Assert that calling portfolio journal functions NEVER modifies
        gen_decision_log.csv or authoritative_paper_sessions.json.
        """
        dec_log_path = os.path.join(BASE_DIR, "gen_decision_log.csv")
        paper_sessions_path = os.path.join(BASE_DIR, "data", "authoritative_paper_sessions.json")

        dec_log_mtime_before = os.path.getmtime(dec_log_path) if os.path.exists(dec_log_path) else None
        paper_mtime_before = os.path.getmtime(paper_sessions_path) if os.path.exists(paper_sessions_path) else None

        # Perform journal operations
        pj.add_transaction("FWRY.CA", "BUY", 100, 19.0, date="2026-08-10", file_path=self.test_file)
        pj.add_transaction("FWRY.CA", "SELL", 50, 20.0, date="2026-08-12", file_path=self.test_file)
        txs = pj.load_transactions(self.test_file)
        _ = pj.compute_portfolio_performance(txs, {"FWRY.CA": 20.5})

        dec_log_mtime_after = os.path.getmtime(dec_log_path) if os.path.exists(dec_log_path) else None
        paper_mtime_after = os.path.getmtime(paper_sessions_path) if os.path.exists(paper_sessions_path) else None

        self.assertEqual(dec_log_mtime_before, dec_log_mtime_after, "VIOLATION: gen_decision_log.csv was touched!")
        self.assertEqual(paper_mtime_before, paper_mtime_after, "VIOLATION: authoritative_paper_sessions.json was touched!")


if __name__ == "__main__":
    unittest.main()
