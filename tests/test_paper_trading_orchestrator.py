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
        import copy
        orig_state = copy.deepcopy(PaperTradingStateManager.load_state())
        try:
            # Seed a mock completed session in history
            test_state = copy.deepcopy(orig_state)
            test_state["verified_session_history"] = [
                {"session_number": 1, "date": "2026-08-18", "status": "COMPLETED", "pnl": 0.0}
            ]
            PaperTradingStateManager.save_state(test_state)

            res = PaperTradingOrchestrator.run_session(target_date="2026-08-18")
            self.assertEqual(res["status"], "SKIPPED")
            self.assertEqual(res["reason_code"], "PAPER_SESSION_ABORTED_DUPLICATE_DATE")
        finally:
            PaperTradingStateManager.save_state(orig_state)

    def test_03_automatic_position_closing_after_10_sessions(self):
        """
        Verify that positions open > 10 sessions are automatically closed at market price
        with real PnL calculated (exit - entry - 0.90% cost) and 500.0 fixed mock eliminated.
        """
        from core.paper_trading_state import PaperTradingStateManager
        from core.session_manager import SessionManager
        import copy
        orig_state = copy.deepcopy(PaperTradingStateManager.load_state())
        orig_sessions = copy.deepcopy(SessionManager._load())
        created_session_num = None
        try:
            # Clean any existing session for the test date
            test_date = "2026-09-17"
            filtered_sessions = [s for s in orig_sessions if s.get("date") != test_date]
            SessionManager._save(filtered_sessions)

            test_state = copy.deepcopy(orig_state)
            test_state["portfolio"]["open_positions"] = [
                {
                    "ticker": "COMI.CA",
                    "shares": 60,
                    "entry_price": 130.0,
                    "entry_date": "2026-08-10",
                    "sessions_held": 10, # Becomes 11 in next session -> triggers exit
                    "entry_fee": 13.65,
                    "sector": "Banking & Financial Services"
                },
                {
                    "ticker": "SWDY.CA",
                    "shares": 60,
                    "entry_price": 120.0,
                    "entry_date": "2026-09-01",
                    "sessions_held": 4, # Becomes 5 -> stays open
                    "entry_fee": 12.60,
                    "sector": "Industrial & Construction"
                }
            ]
            test_state["portfolio"]["cash"] = 85000.0
            test_state["portfolio"]["portfolio_equity"] = 100000.0
            test_state["portfolio"]["closed_positions_count"] = 0
            test_state["portfolio"]["closed_positions_history"] = []
            test_state["performance"]["realized_pnl_egp"] = 0.0
            test_state["verified_session_history"] = []
            PaperTradingStateManager.save_state(test_state)

            res = PaperTradingOrchestrator.run_session(target_date=test_date, force_paper_mode=True)
            self.assertEqual(res["status"], "SUCCESS")
            self.assertEqual(res["closed_positions_count"], 1)
            created_session_num = res.get("session_number")

            updated_state = PaperTradingStateManager.load_state()
            closed_hist = updated_state["portfolio"].get("closed_positions_history", [])
            self.assertEqual(len(closed_hist), 1)
            trade = closed_hist[0]
            self.assertEqual(trade["ticker"], "COMI.CA")
            self.assertEqual(trade["sessions_held"], 11)

            # Realized PnL: (exit - entry) * shares - 0.90% friction
            gross = (trade["exit_price"] - trade["entry_price"]) * trade["shares"]
            turnover = (trade["entry_price"] + trade["exit_price"]) * trade["shares"]
            expected_cost = turnover * 0.0045
            expected_net = round(gross - expected_cost, 2)
            self.assertEqual(trade["net_pnl_egp"], expected_net)
            self.assertEqual(res["session_realized_pnl"], expected_net)

            # Confirm 500.0 is eliminated
            last_hist = updated_state["verified_session_history"][-1]
            self.assertEqual(last_hist["pnl"], expected_net)
            self.assertNotEqual(last_hist["pnl"], 500.0)
        finally:
            PaperTradingStateManager.save_state(orig_state)
            SessionManager._save(orig_sessions)
            # Hermetically clean up any created session report files
            candidates_to_clean = ["reports/paper_sessions/session_02.json", "reports/paper_sessions/session_02.md"]
            if created_session_num:
                candidates_to_clean.extend([
                    f"reports/paper_sessions/session_{created_session_num:02d}.json",
                    f"reports/paper_sessions/session_{created_session_num:02d}.md"
                ])
            for p in candidates_to_clean:
                if os.path.exists(p):
                    try:
                        os.remove(p)
                    except Exception:
                        pass


if __name__ == "__main__":
    unittest.main()

