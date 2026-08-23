#!/usr/bin/env python3
# =============================================================================
# tests/test_egx_universe_loader.py — Unit Tests for EGXUniverseLoader
# Verifies full constituent catalog, index filtering, and metadata completeness.
# =============================================================================

import os
import sys
import unittest

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.egx_universe_loader import EGXUniverseLoader


class TestEGXUniverseLoader(unittest.TestCase):

    def test_01_universe_coverage_counts(self):
        """Verify universe coverage satisfies EGX30 and EGX70 requirements."""
        stats = EGXUniverseLoader.get_universe_stats()
        self.assertGreaterEqual(stats["total_active_equities"], 45)
        self.assertGreaterEqual(stats["egx30_constituents"], 25)
        self.assertGreaterEqual(stats["egx70_constituents"], 15)
        self.assertGreaterEqual(stats["sectors_count"], 5)

    def test_02_index_filtering(self):
        """Verify index filtering returns proper subsets."""
        all_tickers = EGXUniverseLoader.get_tickers("all")
        egx30_tickers = EGXUniverseLoader.get_tickers("egx30")
        egx70_tickers = EGXUniverseLoader.get_tickers("egx70")

        self.assertGreater(len(all_tickers), len(egx30_tickers))
        self.assertGreater(len(all_tickers), len(egx70_tickers))
        self.assertIn("COMI.CA", egx30_tickers)
        self.assertIn("SWDY.CA", egx30_tickers)
        self.assertIn("EFIH.CA", egx30_tickers)
        self.assertIn("POUL.CA", egx70_tickers)
        self.assertIn("MOIL.CA", egx70_tickers)

    def test_03_explicit_requested_equities_exist(self):
        """Verify all specific tickers requested by the user are properly mapped."""
        requested_tickers = [
            "EFIH.CA", "EGAL.CA", "BTFH.CA", "EMFD.CA",
            "ESRS.CA", "EKHOA.CA", "POUL.CA", "MOIL.CA"
        ]
        for sym in requested_tickers:
            self.assertTrue(
                EGXUniverseLoader.is_valid_ticker(sym),
                f"Requested ticker {sym} must be present in EGXUniverseLoader."
            )
            info = EGXUniverseLoader.get_stock_info(sym)
            self.assertIsNotNone(info)
            self.assertIn("name_ar", info)
            self.assertIn("sector", info)
            self.assertIn("nominal_price", info)
            self.assertGreater(info["nominal_price"], 0.0)
            self.assertTrue(info["is_active"])

    def test_04_sector_enumeration(self):
        """Verify sector listing retrieves unique non-empty sectors."""
        sectors = EGXUniverseLoader.get_all_sectors()
        self.assertGreaterEqual(len(sectors), 5)
        for sec in sectors:
            self.assertIsInstance(sec, str)
            self.assertGreater(len(sec), 2)

    def test_05_ticker_normalization(self):
        """Verify get_stock_info normalizes ticker casing and suffix."""
        info1 = EGXUniverseLoader.get_stock_info("comi.ca")
        info2 = EGXUniverseLoader.get_stock_info("COMI")
        self.assertIsNotNone(info1)
        self.assertEqual(info1["ticker"], "COMI.CA")
        self.assertEqual(info1, info2)


if __name__ == "__main__":
    unittest.main()
