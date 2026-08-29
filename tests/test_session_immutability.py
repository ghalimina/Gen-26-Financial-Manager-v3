#!/usr/bin/env python3
# =============================================================================
# tests/test_session_immutability.py — GEN-26 Session Immutability Unit Tests
# Validates that completed session records cannot be silently overwritten or modified.
# =============================================================================

import unittest
import os
import sys

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.paper_observatory import PaperTradingObservatory
from core.session_manager import SessionManager


class TestSessionImmutability(unittest.TestCase):

    def setUp(self):
        self.orig_sessions = SessionManager._load()

    def tearDown(self):
        SessionManager._save(self.orig_sessions)

    def test_01_duplicate_date_session_rejection(self):
        """
        Verify that SessionManager rejects starting a session for an already completed market date.
        """
        test_date = "2026-08-18"
        sess_id = SessionManager.start_session(test_date, bypass_weekend=True)
        if sess_id:
            SessionManager.complete_session(sess_id)
        
        # Second attempt on same date must be rejected
        sess_id_dup = SessionManager.start_session(test_date, bypass_weekend=True)
        self.assertIsNone(sess_id_dup, "SessionManager should return None for duplicate completed date")

    def test_02_session_history_integrity(self):
        """
        Verify that authoritative paper sessions file tracks valid days cleanly.
        """
        valid_days = SessionManager.get_valid_days()
        self.assertGreaterEqual(valid_days, 0)
        self.assertIsInstance(valid_days, int)


if __name__ == "__main__":
    unittest.main()
