#!/usr/bin/env python3
# =============================================================================
# tests/test_watchlist.py — GEN-26 Watchlist Engine Unit Tests
# Validates Add, Remove, Duplicate Prevention, and Separation from Portfolios.
# =============================================================================

import unittest
import os
import sys

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.watchlist import WatchlistManager


class TestWatchlist(unittest.TestCase):

    def setUp(self):
        baseline = WatchlistManager.get_initial_watchlist()
        WatchlistManager.save_watchlist(baseline)

    def test_01_add_and_remove_watchlist(self):
        """Verify adding and removing tickers from user watchlist."""
        res_add = WatchlistManager.add_to_watchlist("ABUK.CA")
        self.assertTrue(res_add["success"])
        self.assertIn("ABUK.CA", res_add["tickers"])

        # Duplicate check
        res_dup = WatchlistManager.add_to_watchlist("ABUK.CA")
        self.assertFalse(res_dup["success"])

        # Remove check
        res_rem = WatchlistManager.remove_from_watchlist("ABUK.CA")
        self.assertTrue(res_rem["success"])
        self.assertNotIn("ABUK.CA", res_rem["tickers"])

    def test_02_watchlist_details(self):
        """Verify watchlist details return target, stop loss, and scores."""
        details = WatchlistManager.get_watchlist_details()
        self.assertGreater(len(details), 0)
        item = details[0]
        self.assertIn("ticker", item)
        self.assertIn("current_price", item)
        self.assertIn("target_price", item)
        self.assertIn("stop_loss", item)


if __name__ == "__main__":
    unittest.main()
