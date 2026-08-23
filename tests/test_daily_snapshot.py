#!/usr/bin/env python3
# =============================================================================
# tests/test_daily_snapshot.py — GEN-26 Daily Snapshot Archive Unit Tests
# Validates daily immutable snapshot creation and SHA256 integrity hash verification.
# =============================================================================

import unittest
import os
import sys
import json

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.daily_snapshot import DailySnapshotArchive


class TestDailySnapshot(unittest.TestCase):

    def test_01_save_daily_snapshot_with_sha256(self):
        """
        Verify that save_daily_snapshot writes a valid JSON snapshot with sha256_hash.
        """
        filepath = DailySnapshotArchive.save_daily_snapshot(
            market_date="2026-08-20",
            universe_coverage={"tradable": 27, "coverage": "PARTIAL_UNIVERSE"},
            rankings=[{"symbol": "COMI.CA", "rank": 1}],
            portfolio_state={"equity": 100000.0, "cash": 65000.0},
            risk_state={"status": "PASS"},
            paper_trades=[]
        )

        self.assertTrue(os.path.exists(filepath))
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data["snapshot_metadata"]["market_date"], "2026-08-20")
        self.assertIn("sha256_hash", data["snapshot_metadata"])
        self.assertEqual(len(data["snapshot_metadata"]["sha256_hash"]), 64) # SHA256 hex length


if __name__ == "__main__":
    unittest.main()
