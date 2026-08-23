#!/usr/bin/env python3
# =============================================================================
# tests/ui/test_rtl_and_ranking_order.py — GEN-26 RTL Ranking Safety Unit Tests
# Validates that RTL rendering does NOT reverse semantic ranking order (Rank 1 = best).
# =============================================================================

import unittest
import os
import sys

WORKSPACE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.ranking_engine import CrossSectionalRankingEngine


class TestRTLRankingSafety(unittest.TestCase):

    def test_01_ranking_order_best_to_worst(self):
        """
        Verify that Rank #1 corresponds to the highest alpha score,
        and subsequent ranks are monotonically decreasing in score.
        """
        candidates = [
            {"ticker": "COMI.CA", "alpha_score": 90.0, "current_price": 102.5, "previous_close": 102.0},
            {"ticker": "SWDY.CA", "alpha_score": 82.0, "current_price": 41.2, "previous_close": 41.0},
            {"ticker": "TMGH.CA", "alpha_score": 79.0, "current_price": 51.5, "previous_close": 51.0},
            {"ticker": "EKHO.CA", "alpha_score": 74.0, "current_price": 20.5, "previous_close": 20.4}
        ]

        ranked = CrossSectionalRankingEngine.rank_universe(candidates, score_key="alpha_score")

        self.assertEqual(ranked[0]["rank"], 1)
        self.assertEqual(ranked[0]["ticker"], "COMI.CA")
        self.assertEqual(ranked[-1]["ticker"], "EKHO.CA")

        # Check monotonic ranking
        scores = [c["alpha_score"] for c in ranked]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_02_html_direction_and_ltr_spans(self):
        """
        Verify that dashboard/index.html has dir="rtl" on html root
        and uses ltr-text class for ticker symbols.
        """
        html_path = os.path.join(WORKSPACE, "dashboard", "index.html")
        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn('dir="rtl"', content)
        self.assertIn('lang="ar"', content)
        self.assertIn('ltr-text', content)
        self.assertIn('COMI.CA', content)


if __name__ == "__main__":
    unittest.main()
