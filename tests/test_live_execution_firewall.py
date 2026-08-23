#!/usr/bin/env python3
# =============================================================================
# tests/test_live_execution_firewall.py — GEN-26 Live Execution Firewall Tests
# Validates that live real-money order routing is strictly blocked and raises exceptions.
# =============================================================================

import unittest
import os
import sys

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.live_execution_firewall import LiveExecutionFirewall, LiveExecutionBlockedError


class TestLiveExecutionFirewall(unittest.TestCase):

    def test_01_assert_paper_mode_only_passes_on_paper(self):
        """Verify that passing 'PAPER' mode succeeds cleanly."""
        try:
            LiveExecutionFirewall.assert_paper_mode_only("PAPER")
            LiveExecutionFirewall.assert_paper_mode_only("paper")
        except Exception as e:
            self.fail(f"assert_paper_mode_only raised unexpectedly: {e}")

    def test_02_assert_paper_mode_blocks_live_and_prod(self):
        """Verify that 'LIVE', 'REAL', or 'PROD' raises LiveExecutionBlockedError."""
        for mode in ["LIVE", "REAL", "PRODUCTION", "BROKER_DIRECT", ""]:
            with self.assertRaises(LiveExecutionBlockedError):
                LiveExecutionFirewall.assert_paper_mode_only(mode)

    def test_03_validate_execution_safety_blocks_live_payload(self):
        """Verify that order payload with is_live=True is blocked."""
        with self.assertRaises(LiveExecutionBlockedError):
            LiveExecutionFirewall.validate_execution_safety({"mode": "PAPER", "is_live": True})

        # Valid payload succeeds
        self.assertTrue(LiveExecutionFirewall.validate_execution_safety({"mode": "PAPER", "is_live": False}))


if __name__ == "__main__":
    unittest.main()
