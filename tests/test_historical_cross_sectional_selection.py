#!/usr/bin/env python3
# =============================================================================
# tests/test_historical_cross_sectional_selection.py — GEN-26 Universe Selection Test
# Proves that given the entire tradable EGX universe on a historical date,
# the engine ranks and selects the best risk-adjusted stocks using ONLY as-of data.
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

from core.pit_store import PointInTimeDataStore, HistoricalTradableUniverse
from core.ranking_engine import CrossSectionalRankingEngine
from core.decision_builder import CanonicalDecisionBuilder
from core.alpha_engine import AlphaEngine


class TestHistoricalCrossSectionalSelection(unittest.TestCase):

    def test_01_as_of_universe_cross_sectional_ranking(self):
        """
        Simulate a historical date (2025-01-15) across 5 candidate EGX stocks:
        1. COMI.CA: High quality, strong momentum, high liquidity -> Expected Rank #1
        2. SWDY.CA: Good quality, moderate momentum -> Expected Rank #2
        3. TMGH.CA: Locked at Limit Up (+20%) -> Must be penalized / ineligible to buy
        4. LOW_LIQ.CA: Below min ADV threshold -> Must receive liquidity penalty
        5. SUSPENDED.CA: Suspended stock -> Must be excluded by Tradable Universe
        """
        as_of_date = "2025-01-15"
        universe = HistoricalTradableUniverse()
        
        # Register suspension
        universe.register_corporate_action(
            ticker="SUSPENDED.CA",
            action_type="SUSPENSION",
            effective_date="2025-01-10",
            announcement_date="2025-01-09",
            details={"end_date": "2025-01-20"}
        )

        candidates = [
            {"ticker": "COMI.CA", "price": 100.0, "previous_close": 98.0, "alpha_score": 88.0, "adv_20d_egp": 85_000_000},
            {"ticker": "SWDY.CA", "price": 45.0, "previous_close": 44.0, "alpha_score": 76.0, "adv_20d_egp": 35_000_000},
            {"ticker": "TMGH.CA", "price": 60.0, "previous_close": 50.0, "alpha_score": 92.0, "adv_20d_egp": 40_000_000}, # +20% Limit Up!
            {"ticker": "EKHO.CA", "price": 12.0, "previous_close": 12.0, "alpha_score": 80.0, "adv_20d_egp": 500_000}, # Illiquid < 2M EGP in this scenario
            {"ticker": "SUSPENDED.CA", "price": 20.0, "previous_close": 20.0, "alpha_score": 85.0, "adv_20d_egp": 15_000_000}
        ]

        # 1. Filter by Tradable Universe
        tradable_candidates = [c for c in candidates if universe.is_tradable_on(c["ticker"], as_of_date)]
        self.assertEqual(len(tradable_candidates), 4)
        self.assertNotIn("SUSPENDED.CA", [c["ticker"] for c in tradable_candidates])

        # 2. Cross-Sectional Ranking
        ranked = CrossSectionalRankingEngine.rank_universe(tradable_candidates, score_key="alpha_score", min_adv_egp=2_000_000)

        # 3. Assertions
        # Rank #1 must be COMI.CA
        self.assertEqual(ranked[0]["ticker"], "COMI.CA")
        self.assertEqual(ranked[0]["rank"], 1)

        # Rank #2 must be SWDY.CA
        self.assertEqual(ranked[1]["ticker"], "SWDY.CA")

        # TMGH.CA must be penalized for being locked at limit-up
        tmgh_entry = next(r for r in ranked if r["ticker"] == "TMGH.CA")
        self.assertEqual(tmgh_entry["rank_exclusion_reason"], "LOCKED_AT_LIMIT_UP")
        self.assertEqual(tmgh_entry["adjusted_rank_score"], 0.0)

        # EKHO.CA must have liquidity warning
        ekho_entry = next(r for r in ranked if r["ticker"] == "EKHO.CA")
        self.assertEqual(ekho_entry["rank_exclusion_reason"], "BELOW_MIN_ADV_THRESHOLD")
        self.assertLess(ekho_entry["adjusted_rank_score"], 50.0)

    def test_02_quantile_spread_monotonicity(self):
        """
        Verify that compute_quantile_spread properly computes monotonic spread across bins.
        """
        np.random.seed(42)
        ranks = pd.Series(np.linspace(1, 100, 100))
        # Forward return strongly correlated with rank
        fwd_returns = ranks * 0.002 + np.random.normal(0, 0.02, 100)

        df = pd.DataFrame({"rank": ranks, "fwd_return": fwd_returns})
        res = CrossSectionalRankingEngine.compute_quantile_spread(df, "rank", "fwd_return", num_quantiles=5)

        self.assertGreater(res["rank_ic"], 0.50)
        self.assertGreater(res["top_bottom_spread"], 0.10)
        self.assertTrue(res["is_monotonic"])


if __name__ == "__main__":
    unittest.main()
