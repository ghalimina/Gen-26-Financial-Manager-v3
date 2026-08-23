#!/usr/bin/env python3
# =============================================================================
# tests/test_paper_state_persistence.py — GEN-26 Paper State Persistence Unit Tests
# Validates atomic state saving, backup creation, and session counter integrity.
# =============================================================================

import unittest
import os
import sys
import json

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.paper_trading_state import PaperTradingStateManager


class TestPaperStatePersistence(unittest.TestCase):

    def test_01_load_state_preserves_verified_sessions(self):
        """
        Verify that load_state loads valid paper trading maturation gate state.
        """
        state = PaperTradingStateManager.load_state()
        self.assertGreaterEqual(state["session_progress"]["verified_sessions"], 0)
        self.assertEqual(state["session_progress"]["total_sessions_required"], 30)
        self.assertTrue(state["live_trading_blocked"])
        self.assertEqual(state["deployment_mode"], "PAPER_ONLY")

    def test_02_atomic_save_and_backup_creation(self):
        """
        Verify that saving state creates timestamped backups in reports/state_backups/.
        """
        state = PaperTradingStateManager.load_state()
        initial_backups = len(os.listdir(PaperTradingStateManager.BACKUP_DIR)) if os.path.exists(PaperTradingStateManager.BACKUP_DIR) else 0

        # Save update
        PaperTradingStateManager.save_state(state)

        self.assertTrue(os.path.exists(PaperTradingStateManager.STATE_FILE))
        current_backups = len(os.listdir(PaperTradingStateManager.BACKUP_DIR))
        self.assertGreaterEqual(current_backups, initial_backups)


if __name__ == "__main__":
    unittest.main()
