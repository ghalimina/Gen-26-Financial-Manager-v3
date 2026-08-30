#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#imports for testing alpha scanner
import unittest
import os, sys

SYS_PATH_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SYS_PATH_BASE not in sys.path:
    sys.path.insert(0, SYS_PATH_BASE)

from core.alpha_scanner import MultiLayerScanner, AlphaScorer, OpportunityRanker, MonotonicityValidator
from dashboard.app import app


class TestAlphaIntelligenceScanner(unittest.TestCase):
    "Tests for EGX Alpha Intelligence Engine"

    def setUp(self):
        self.client = app.test_client()

    def test_01_multi_layer_scanner_layers(self):
        res = MultiLayerScanner.scan_single_stock('COMI.CA', 95.5, "BULL")
        self.assertIn("technical", res["layer_scores"])
        self.assertIn("relative_strength", res["layer_scores"])
        self.assertIn("fundamental", res["layer_scores"])
        self.assertIn("events", res["layer_scores"])
        self.assertIn("sentiment", res["layer_scores"])
        self.assertGreaterEqual(res["layer_scores"]["technical"], 10.0)
        self.assertLessEqual(res["layer_scores"]["technical"], 100.0)

    def test_02_regime_adaptive_weights(self):
        bull_w = MultiLayerScanner.get_regime_weights("BULL_EXPANSION")
        bear_w = MultiLayerScanner.get_regime_weights("BEAR_CORRECTION")
        self.assertAlmostEqual(sum(bull_w.values()), 1.00, places=2)
        self.assertAlmostEqual(sum(bear_w.values()), 1.00, places=2)
        self.assertGreater(bear_w["fundamental"], bull_w["fundamental"])

    def test_03_alpha_scorer_bounds(self):
        scan = MultiLayerScanner.scan_single_stock('SWDY.CA', 48.5)
        scored = AlphaScorer.calculate_alpha_score(scan)
        self.assertGreaterEqual(scored["alpha_score"], 10.0)
        self.assertLessEqual(scored["alpha_score"], 100.0)
        self.assertGreaterEqual(scored["win_probability_pct"], 25.0)
        self.assertLessEqual(scored["win_probability_pct"], 88.0)
        self.assertIn(scored["tier"], ["STRONG_ALPHA", "MODERATE_ALPHA", "NEUTRAL_WATCH", "UNDERPERFORMANCE_AVOID"])

    def test_04_opportunity_ranking_universe(self):
        res = OpportunityRanker.scan_universe(universe_filter="all")
        self.assertGreaterEqual(res["total_scanned"], 10)
        self.assertIn("opportunities", res)
        opps = res["opportunities"]
        for i in range(len(opps) - 1):
            self.assertGreaterEqual(opps[i]["opportunity_score"], opps[i+1]["opportunity_score"])

    def test_05_monotonicity_validator(self):
        mono = MonotonicityValidator.validate_monotonic_buckets()
        self.assertTrue(mono["is_monotonic"])
        self.assertEqual(mono["validation_status"], "MATHEMATICALLY_MONOTONIC_VERIFIED")
        self.assertGreater(mono["spearman_rank_ic"], 0.30)

    def test_06_flask_alpha_scanner_endpoints(self):
        # 1. Scan API
        r1 = self.client.get('/api/alpha_scanner/scan')
        self.assertEqual(r1.status_code, 200)
        j1 = r1.get_json()
        self.assertIn("opportunities", j1)

        # 2. Stock Detail API
        r2 = self.client.get('/api/alpha_scanner/stock/COMI.CA')
        self.assertEqual(r2.status_code, 200)
        j2 = r2.get_json()
        self.assertEqual(j2["ticker"], "COMI.CA")

        # 3. Monotonicity API
        r3 = self.client.get('/api/alpha_scanner/monotonicity')
        self.assertEqual(r3.status_code, 200)

if __name__ == '__main__':
    unittest.main()
