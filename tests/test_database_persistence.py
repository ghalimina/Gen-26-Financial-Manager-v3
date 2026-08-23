#!/usr/bin/env python3
# =============================================================================
# tests/test_database_persistence.py — GEN-26 SQLite Relational DB Unit Tests
# Validates schema creation, catalog seeding, indexes, and transactional queries.
# =============================================================================

import unittest
import os
import sys

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.database import DatabaseManager


class TestDatabasePersistence(unittest.TestCase):

    def test_01_schema_initialization_and_seeding(self):
        """Verify database tables and indexes initialize cleanly and seed stocks."""
        DatabaseManager.seed_initial_catalog()
        self.assertTrue(os.path.exists(DatabaseManager.DB_PATH))

        with DatabaseManager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT count(*) as cnt FROM stocks;")
            row = cursor.fetchone()
            self.assertGreaterEqual(row["cnt"], 27)

    def test_02_paper_session_storage(self):
        """Verify saving paper session record into database."""
        with DatabaseManager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO paper_sessions (session_id, session_number, market_date, status, realized_pnl, portfolio_equity, cash_reserve, sha256_hash, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, ("SESS_TEST_01", 999, "2099-01-01", "COMPLETED", 500.0, 100000.0, 65000.0, "abc123hash", "2099-01-01T15:00:00"))
            conn.commit()

            cursor.execute("SELECT * FROM paper_sessions WHERE session_id = 'SESS_TEST_01';")
            rec = cursor.fetchone()
            self.assertIsNotNone(rec)
            self.assertEqual(rec["session_number"], 999)

            # Cleanup test record
            cursor.execute("DELETE FROM paper_sessions WHERE session_id = 'SESS_TEST_01';")
            conn.commit()


if __name__ == "__main__":
    unittest.main()
