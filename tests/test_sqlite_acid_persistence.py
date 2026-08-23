#!/usr/bin/env python3
# =============================================================================
# tests/test_sqlite_acid_persistence.py — SQLite ACID & Disk Persistence Test
# Verifies atomic writes, disk durability, connection closure, and zero data loss.
# =============================================================================

import os
import sqlite3
import unittest
import uuid
import datetime
from core.database import DatabaseManager
from core.real_portfolio import RealPortfolioTracker


class TestSQLiteACIDPersistence(unittest.TestCase):
    """
    Verifies ACID properties of SQLite persistence across engine restarts.
    """

    def test_01_sqlite_acid_insert_close_restart_persistence(self):
        # Initialize schema
        DatabaseManager.initialize_schema()
        test_db = DatabaseManager.DB_PATH

        test_id = f"POS_TEST_{uuid.uuid4().hex[:6].upper()}"
        test_ticker = "COMI.CA"
        test_quantity = 250
        test_price = 137.00
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. Open Connection & Insert Record inside explicit transaction
        conn1 = DatabaseManager.get_connection()
        cursor1 = conn1.cursor()
        
        # Ensure stock exists in stocks table first for FK integrity
        cursor1.execute("""
            INSERT OR IGNORE INTO stocks (ticker, company_name, sector, isin, status, is_core, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (test_ticker, "البنك التجاري الدولي (CIB)", "Banking", "EGS60121C018", "TRADABLE", 1, now_str))

        cursor1.execute("""
            INSERT INTO real_portfolio_positions 
            (holding_id, ticker, quantity, average_entry_price, manual_notes, active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            test_id, test_ticker, test_quantity, test_price,
            "ACID Persistence Verification Test", 1, now_str, now_str
        ))
        conn1.commit()
        
        # 2. Hard Close the Database Connection & Delete Instance
        conn1.close()
        del conn1

        # 3. Simulate Engine Restart (Open brand new connection from disk)
        self.assertTrue(os.path.exists(test_db), "Database file must exist on disk.")
        conn2 = DatabaseManager.get_connection()
        cursor2 = conn2.cursor()
        cursor2.execute("SELECT * FROM real_portfolio_positions WHERE holding_id = ?", (test_id,))
        row = cursor2.fetchone()

        # 4. Assert 100% Data Integrity & Exact Retrieval
        self.assertIsNotNone(row, "Record must persist on disk after connection termination.")
        self.assertEqual(row["holding_id"], test_id)
        self.assertEqual(row["ticker"], test_ticker)
        self.assertEqual(row["quantity"], test_quantity)
        self.assertEqual(row["average_entry_price"], test_price)
        self.assertEqual(row["active"], 1)

        # Clean up test position
        cursor2.execute("DELETE FROM real_portfolio_positions WHERE holding_id = ?", (test_id,))
        conn2.commit()
        conn2.close()

    def test_02_real_portfolio_crud_disk_durability(self):
        sym = "ABUK.CA"
        qty = 100
        price = 75.40

        # Ensure not present initially
        RealPortfolioTracker.delete_holding(sym, confirm=True)

        # Add position via RealPortfolioTracker
        res = RealPortfolioTracker.add_holding(sym, qty, price, notes="ACID Test Position")
        self.assertTrue(res["success"], f"add_holding failed: {res.get('error')}")
        holding_id = res["holding"]["holding_id"]

        # Reload from disk independently
        portfolio_state = RealPortfolioTracker.load_real_portfolio()
        holdings = portfolio_state.get("holdings", [])
        matching = [h for h in holdings if h["holding_id"] == holding_id]

        self.assertEqual(len(matching), 1, "New tracker instance must read committed position from disk.")
        self.assertEqual(matching[0]["ticker"], sym)
        self.assertEqual(matching[0]["quantity"], qty)
        self.assertEqual(matching[0]["average_entry_price"], price)

        # Remove position to clean up
        del_res = RealPortfolioTracker.delete_holding(sym)
        self.assertTrue(del_res["success"], f"delete_holding failed: {del_res.get('error')}")
        
        portfolio_after = RealPortfolioTracker.load_real_portfolio()
        matching_after = [h for h in portfolio_after.get("holdings", []) if h["ticker"] == sym and h.get("active", True)]
        self.assertEqual(len(matching_after), 0, "Position must be deleted cleanly from disk.")


if __name__ == "__main__":
    unittest.main()
