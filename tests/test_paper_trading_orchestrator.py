#!/usr/bin/env python3
# =============================================================================
# tests/test_paper_trading_orchestrator.py — GEN-26 Paper Orchestrator Unit Tests
# Validates fail-closed behavior, duplicate detection, and live execution blocking.
# =============================================================================

import unittest
import os
import sys

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.paper_trading_orchestrator import PaperTradingOrchestrator
from core.live_execution_firewall import LiveExecutionBlockedError


class TestPaperTradingOrchestrator(unittest.TestCase):

    def test_01_orchestrator_blocks_non_paper_mode(self):
        """
        Verify that orchestrator raises LiveExecutionBlockedError if force_paper_mode is False.
        """
        with self.assertRaises(LiveExecutionBlockedError):
            PaperTradingOrchestrator.run_session(force_paper_mode=False)

    def test_02_orchestrator_duplicate_date_skip(self):
        """
        Verify that attempting to run an already completed date returns SKIPPED with reason code.
        """
        from core.paper_trading_state import PaperTradingStateManager
        orig_state = PaperTradingStateManager.load_state()
        try:
            # Seed a mock completed session in history
            test_state = dict(orig_state)
            test_state["verified_session_history"] = [
                {"session_number": 1, "date": "2026-08-18", "status": "COMPLETED", "pnl": 0.0}
            ]
            PaperTradingStateManager.save_state(test_state)

            res = PaperTradingOrchestrator.run_session(target_date="2026-08-18")
            self.assertEqual(res["status"], "SKIPPED")
            self.assertEqual(res["reason_code"], "PAPER_SESSION_ABORTED_DUPLICATE_DATE")
        finally:
            PaperTradingStateManager.save_state(orig_state)


if __name__ == "__main__":
    unittest.main()
