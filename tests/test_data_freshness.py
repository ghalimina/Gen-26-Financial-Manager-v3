#!/usr/bin/env python3
# =============================================================================
# tests/test_data_freshness.py — GEN-26 Data Freshness Gate Unit Tests
# Validates stale data rejection, future timestamp rejection, and clean data acceptance.
# =============================================================================

import unittest
import os
import sys
import datetime

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.data_freshness import DataFreshnessGate


class TestDataFreshness(unittest.TestCase):

    def test_01_fresh_data_accepted(self):
        """Verify that recent data (e.g. 2 hours old) passes cleanly."""
        now_iso = datetime.datetime.now().isoformat()
        res = DataFreshnessGate.evaluate_data_freshness(now_iso, data_record_count=27)
        self.assertTrue(res["is_fresh"])
        self.assertEqual(res["reason_code"], "DATA_FRESH_AND_VALID")

    def test_02_stale_data_rejected(self):
        """Verify that 100-hour-old data is rejected as DATA_STALE."""
        stale_dt = datetime.datetime.now() - datetime.timedelta(hours=100)
        res = DataFreshnessGate.evaluate_data_freshness(stale_dt.isoformat(), data_record_count=27)
        self.assertFalse(res["is_fresh"])
        self.assertEqual(res["reason_code"], "DATA_STALE")

    def test_03_future_data_rejected(self):
        """Verify that future timestamps are rejected for lookahead leakage risk."""
        future_dt = datetime.datetime.now() + datetime.timedelta(days=2)
        res = DataFreshnessGate.evaluate_data_freshness(future_dt.isoformat(), data_record_count=27)
        self.assertFalse(res["is_fresh"])
        self.assertEqual(res["reason_code"], "LOOKAHEAD_TEMPORAL_VIOLATION")

    def test_04_zero_records_rejected(self):
        """Verify that zero records in feed returns NO_VALID_UNIVERSE."""
        res = DataFreshnessGate.evaluate_data_freshness(datetime.datetime.now().isoformat(), data_record_count=0)
        self.assertFalse(res["is_fresh"])
        self.assertEqual(res["reason_code"], "NO_VALID_UNIVERSE")


if __name__ == "__main__":
    unittest.main()
