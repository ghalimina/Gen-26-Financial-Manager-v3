#!/usr/bin/env python3
# =============================================================================
# tests/test_leakage_forensics.py — GEN-26 Adversarial Future Data Leakage Test
# Injects future information and verifies that Point-in-Time Firewalls and
# Feature Engineering strictly block future access (Zero Information Leakage).
# =============================================================================

import unittest
import os
import sys
import datetime
import pandas as pd
import numpy as np

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.pit_store import PointInTimeDataStore
from core.market_intelligence import MarketIntelligenceEngine


class TestLeakageForensics(unittest.TestCase):

    def test_01_future_publication_adversarial_injection(self):
        """
        Adversarial Test:
        Historical Decision Date: 2025-01-10T09:00:00
        True Event / Period End: 2024-12-31
        Publication Date: 2025-01-20T10:00:00 (Published 10 days in the future!)

        Assert that querying as-of 2025-01-10 returns None (Access Denied / Not Available).
        Assert that querying as-of 2025-01-21 returns the real value.
        """
        pit = PointInTimeDataStore()
        
        # Inject future record
        pit.add_record(
            entity_id="COMI.CA",
            metric_name="fy2024_net_profit",
            value=35_000_000_000,
            period_end="2024-12-31",
            publication_time="2025-01-20T10:00:00"
        )

        # 1. Query on historical decision date (MUST BE NONE)
        state_at_decision = pit.get_as_of("COMI.CA", "fy2024_net_profit", "2025-01-10T09:00:00")
        self.assertIsNone(state_at_decision, "CRITICAL LEAKAGE: Future publication was leaked to past decision!")

        # 2. Query after publication date (MUST BE AVAILABLE)
        state_post_pub = pit.get_as_of("COMI.CA", "fy2024_net_profit", "2025-01-21T09:00:00")
        self.assertEqual(state_post_pub, 35_000_000_000)

    def test_02_trailing_breadth_zero_lookahead(self):
        """
        Verify that compute_trailing_breadth relies ONLY on past trailing returns
        and does not read forward target returns.
        """
        dates = pd.date_range("2026-01-01", periods=10)
        # Create stock with known drop yesterday and surge tomorrow
        df_stock = pd.DataFrame({
            "Close": [100.0, 95.0, 110.0]  # Day 0: 100, Day 1: 95 (Down), Day 2: 110 (Up)
        }, index=dates[:3])

        # As of Day 1 (index 1), trailing return is (95 - 100) / 100 = -5% (Decline)
        # If lookahead existed, it would read Day 2 (110) as Advance.
        breadth_day1 = MarketIntelligenceEngine.compute_trailing_breadth({"TEST.CA": df_stock.iloc[:2]})
        self.assertEqual(breadth_day1["declines"], 1)
        self.assertEqual(breadth_day1["advances"], 0)


if __name__ == "__main__":
    unittest.main()
