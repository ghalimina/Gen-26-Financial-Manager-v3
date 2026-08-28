#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# tests/test_statistical_arbitrage_engine.py — Unit Tests for Statistical Arbitrage
# =============================================================================

import unittest
import os
import sys
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.statistical_arbitrage_engine import (
    StatisticalArbitrageEngine,
    EGX_KNOWN_PAIRS
)


class TestStatisticalArbitrageEngine(unittest.TestCase):

    def setUp(self):
        # Clear cache for isolated testing
        StatisticalArbitrageEngine._cache.clear()
        StatisticalArbitrageEngine._cache_timestamps.clear()

    def test_01_egx_known_pairs_structure(self):
        """Verify EGX_KNOWN_PAIRS contains essential sector pairs."""
        self.assertGreaterEqual(len(EGX_KNOWN_PAIRS), 3)
        tickers_pairs = [(p["ticker_A"], p["ticker_B"]) for p in EGX_KNOWN_PAIRS]
        self.assertIn(("COMI.CA", "QNBE.CA"), tickers_pairs)
        self.assertIn(("TMGH.CA", "PHDC.CA"), tickers_pairs)
        self.assertIn(("SWDY.CA", "ORAS.CA"), tickers_pairs)

        for p in EGX_KNOWN_PAIRS:
            self.assertIn("pair_id", p)
            self.assertIn("sector", p)
            self.assertIn("name_A_ar", p)
            self.assertIn("name_B_ar", p)

    def test_02_calculate_pair_spread_zscore_math(self):
        """Verify mathematical correctness of spread, mean, std, and Z-Score calculation."""
        # 60 days of constant spread with a sudden spike on day 60
        # 59 days of spread = 1.0, 1 day of spread = 1.5
        pA = np.array([100.0] * 59 + [150.0])
        pB = np.array([100.0] * 60)

        res = StatisticalArbitrageEngine.calculate_pair_spread_zscore(
            ticker_A="STOCK_A.CA",
            ticker_B="STOCK_B.CA",
            custom_prices_A=pA,
            custom_prices_B=pB
        )

        self.assertEqual(res["ticker_A"], "STOCK_A.CA")
        self.assertEqual(res["ticker_B"], "STOCK_B.CA")
        self.assertEqual(res["price_A"], 150.0)
        self.assertEqual(res["price_B"], 100.0)
        self.assertEqual(res["current_spread"], 1.5)
        self.assertGreater(res["mean_spread"], 1.0)
        self.assertGreater(res["std_spread"], 0.0)
        # Z-Score should be heavily positive due to spike
        self.assertGreater(res["z_score"], 2.0)

    def test_03_calculate_pair_spread_zscore_negative(self):
        """Verify negative Z-Score when A is undervalued relative to B."""
        # 59 days of spread = 2.0 (pA=200, pB=100), 1 day of spread = 1.2 (pA=120, pB=100)
        pA = np.array([200.0] * 59 + [120.0])
        pB = np.array([100.0] * 60)

        res = StatisticalArbitrageEngine.calculate_pair_spread_zscore(
            ticker_A="STOCK_A.CA",
            ticker_B="STOCK_B.CA",
            custom_prices_A=pA,
            custom_prices_B=pB
        )

        self.assertLess(res["z_score"], -2.0)

    def test_04_zero_variance_edge_case(self):
        """Verify zero variance handles division by zero safely (Z-Score = 0.0)."""
        pA = np.array([100.0] * 60)
        pB = np.array([50.0] * 60)

        res = StatisticalArbitrageEngine.calculate_pair_spread_zscore(
            ticker_A="A.CA",
            ticker_B="B.CA",
            custom_prices_A=pA,
            custom_prices_B=pB
        )

        self.assertEqual(res["current_spread"], 2.0)
        self.assertEqual(res["std_spread"], 0.0)
        self.assertEqual(res["z_score"], 0.0)

    def test_05_classify_arbitrage_signal_mapping(self):
        """Verify signal mapping for positive, negative, and neutral Z-scores."""
        # 1. Z-Score >= +2.0 -> SHORT A / LONG B
        sig_pos, dir_pos, desc_pos = StatisticalArbitrageEngine.classify_arbitrage_signal(
            z_score=2.45, ticker_A="COMI.CA", ticker_B="QNBE.CA",
            name_A_ar="البنك التجاري الدولي", name_B_ar="بنك قطر الوطني"
        )
        self.assertEqual(sig_pos, StatisticalArbitrageEngine.SIGNAL_SHORT_A_LONG_B)
        self.assertIn("COMI.CA", dir_pos)
        self.assertIn("QNBE.CA", dir_pos)
        self.assertIn("مراجحة", desc_pos)

        # 2. Z-Score <= -2.0 -> LONG A / SHORT B
        sig_neg, dir_neg, desc_neg = StatisticalArbitrageEngine.classify_arbitrage_signal(
            z_score=-2.30, ticker_A="TMGH.CA", ticker_B="PHDC.CA",
            name_A_ar="طلعت مصطفى", name_B_ar="بالم هيلز"
        )
        self.assertEqual(sig_neg, StatisticalArbitrageEngine.SIGNAL_LONG_A_SHORT_B)
        self.assertIn("شراء", dir_neg)
        self.assertIn("TMGH.CA", dir_neg)

        # 3. -2.0 < Z-Score < +2.0 -> NEUTRAL
        sig_neu, dir_neu, desc_neu = StatisticalArbitrageEngine.classify_arbitrage_signal(
            z_score=0.45, ticker_A="SWDY.CA", ticker_B="ORAS.CA"
        )
        self.assertEqual(sig_neu, StatisticalArbitrageEngine.SIGNAL_NEUTRAL)
        self.assertIn("توازن", dir_neu)

    def test_06_evaluate_arbitrage_opportunities(self):
        """Verify evaluate_arbitrage_opportunities returns structured opportunities for all known pairs."""
        opps = StatisticalArbitrageEngine.evaluate_arbitrage_opportunities()
        self.assertEqual(len(opps), len(EGX_KNOWN_PAIRS))

        for op in opps:
            self.assertIn("pair_id", op)
            self.assertIn("ticker_A", op)
            self.assertIn("ticker_B", op)
            self.assertIn("signal", op)
            self.assertIn(op["signal"], [
                StatisticalArbitrageEngine.SIGNAL_SHORT_A_LONG_B,
                StatisticalArbitrageEngine.SIGNAL_LONG_A_SHORT_B,
                StatisticalArbitrageEngine.SIGNAL_NEUTRAL,
                "INSUFFICIENT_DATA"
            ])
            self.assertIn("is_actionable", op)
            self.assertIsInstance(op["is_actionable"], bool)
            self.assertIn("telemetry", op)
            self.assertIn("z_score", op["telemetry"])
            self.assertIn("description_ar", op)
            self.assertGreater(len(op["description_ar"]), 10)

    def test_07_price_history_zero_mock_fallback(self):
        """Verify fetch_pair_price_history returns empty arrays on failure instead of fake noise."""
        pA, pB = StatisticalArbitrageEngine.fetch_pair_price_history(
            "NON_EXISTENT_1.CA", "NON_EXISTENT_2.CA", window_days=60, force_fallback=True
        )
        self.assertEqual(len(pA), 0)
        self.assertEqual(len(pB), 0)


if __name__ == "__main__":
    unittest.main()
