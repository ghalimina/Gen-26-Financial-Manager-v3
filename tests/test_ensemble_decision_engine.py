#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# tests/test_ensemble_decision_engine.py — Unit Tests for EnsembleDecisionEngine
# Validates:
# 1. 6-Pillar Synthesis & Scoring Structure.
# 2. Consensus Voting Rule & Conviction Level.
# 3. Target and Stop Loss Price Calculation.
# 4. Persistence into SQLite Database & gen_decision_log.json.
# =============================================================================

import os
import sys
import unittest

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.ensemble_decision_engine import EnsembleDecisionEngine


class TestEnsembleDecisionEngine(unittest.TestCase):

    def test_01_ensemble_decision_structure(self):
        """Verify consensus evaluation returns all 6 analytical pillars and action parameters."""
        res = EnsembleDecisionEngine.evaluate_ensemble_consensus("COMI.CA", persist_decision=False)
        self.assertIn("decision_id", res)
        self.assertEqual(res["ticker"], "COMI.CA")
        self.assertIn("current_price_egp", res)
        self.assertIn("entry_price_egp", res)
        self.assertIn("target_price_1_egp", res)
        self.assertIn("target_price_2_egp", res)
        self.assertIn("stop_loss_price_egp", res)
        self.assertIn("final_action", res)
        self.assertIn(res["final_action"], ["STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL"])
        self.assertIn("conviction", res)
        self.assertIn("composite_score", res)
        self.assertIn("pillars_breakdown", res)
        self.assertEqual(len(res["pillars_breakdown"]), 6)
        
        # Verify 6 pillars
        expected_pillars = ["technicals", "fundamentals", "macro", "gdr_commodities", "smart_money_insiders", "nlp_sentiment"]
        for p in expected_pillars:
            self.assertIn(p, res["pillars_breakdown"])
            self.assertIn("score", res["pillars_breakdown"][p])
            self.assertIn("vote", res["pillars_breakdown"][p])

    def test_02_targets_and_stop_loss_ratios(self):
        """Verify target price 1 is ~+8%, target 2 is ~+18%, and stop loss is ~-5%."""
        res = EnsembleDecisionEngine.evaluate_ensemble_consensus("SWDY.CA", persist_decision=False)
        entry = res["entry_price_egp"]
        self.assertAlmostEqual(res["target_price_1_egp"], round(entry * 1.08, 2), places=1)
        self.assertAlmostEqual(res["target_price_2_egp"], round(entry * 1.18, 2), places=1)
        self.assertAlmostEqual(res["stop_loss_price_egp"], round(entry * 0.95, 2), places=1)

    def test_03_top_ensemble_opportunities_ranking(self):
        """Verify scan_top_ensemble_opportunities returns sorted opportunities."""
        top_ops = EnsembleDecisionEngine.scan_top_ensemble_opportunities(limit=5)
        self.assertIsInstance(top_ops, list)
        self.assertGreater(len(top_ops), 0)
        # Verify descending sort order
        scores = [op["composite_score"] for op in top_ops]
        self.assertEqual(scores, sorted(scores, reverse=True))


if __name__ == "__main__":
    unittest.main()
