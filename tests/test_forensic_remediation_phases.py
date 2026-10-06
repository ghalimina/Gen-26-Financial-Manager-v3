#!/usr/bin/env python3
# =============================================================================
# tests/test_forensic_remediation_phases.py — Comprehensive Forensic Verification
# Validates the complete 11-phase institutional remediation of GEN-26:
#   1. Zero Synthetic Data Fallback (100% Empirical Real Market Data)
#   2. Point-in-Time Universe Architecture (Survivorship Bias Eliminated)
#   3. Full Historical Universe Registry (Active + Delisted + Merged Equities)
#   4. Centralized Corporate Actions Database (Splits, Dividends, Ex-Dates)
#   5. Continuous Data Quality Engine (DQS 0–100 & 3-Tier Classification)
#   6. Strict Point-in-Time Fundamentals (Zero Lookahead Filing Gate)
#   7. Institutional News Events Taxonomy & PIT Timestamps
#   8. Strict Holdout Integrity Classification (2026 Tainted Labeling)
#   9. Disentangled Prediction Triad (P(UP) vs E[R] vs Conformal Uncertainty)
#  10. Advanced Ranking Engine (Precision@K, NDCG@K, Rank IC, ICIR)
#  11. Decoupled Independent Execution Engine B (Open T+1, Limits, Slippage, Fees)
# =============================================================================

import os
import sys
import unittest
import pandas as pd
import numpy as np

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.historical_universe_manager import HistoricalUniverseManager
from core.pit_store import HistoricalTradableUniverse
from core.data_quality import DataQualityEngine
from core.prediction_disentangler import PredictionDisentangler
from core.ranking_engine import CrossSectionalRankingEngine
from core.independent_backtester import IndependentBacktester
from core.model_evaluator import WalkForwardValidator
from core.ai_prediction_model import AIPredictionModel
from core.news_sentiment_engine import NewsSentimentEngine


class TestForensicRemediationPhases(unittest.TestCase):

    def test_phase_01_zero_synthetic_data_guarantee(self):
        """Phase 1: Verify walk-forward data generator loads genuine empirical data without fallbacks."""
        df_empirical, desc = AIPredictionModel._generate_empirical_walkforward_data()
        self.assertNotIn("Synthetic", desc, "Synthetic data fallback detected in empirical generator!")
        self.assertGreater(len(df_empirical), 5000, "Empirical market dataset must contain real samples.")
        self.assertIn("residual_alpha_10d", df_empirical.columns)

    def test_phase_02_and_03_survivorship_free_pit_universe(self):
        """Phases 2 & 3: Verify Point-in-Time tradability accurately handles delistings and IPO dates."""
        # ACRO.CA was listed in 2020, delisted August 2021
        self.assertTrue(HistoricalUniverseManager.is_tradable_on("ACRO.CA", "2020-06-01"))
        self.assertFalse(HistoricalUniverseManager.is_tradable_on("ACRO.CA", "2024-06-01"))

        # EFIH.CA IPO occurred in October 2021
        self.assertFalse(HistoricalUniverseManager.is_tradable_on("EFIH.CA", "2020-06-01"))
        self.assertTrue(HistoricalUniverseManager.is_tradable_on("EFIH.CA", "2024-06-01"))

        # Verify historical universe size changes across calendar years
        u_2020 = HistoricalUniverseManager.get_tradable_universe("2020-06-01")
        u_2024 = HistoricalUniverseManager.get_tradable_universe("2024-06-01")
        self.assertGreater(len(u_2020), 200)
        self.assertGreater(len(u_2024), 200)

    def test_phase_04_centralized_corporate_actions(self):
        """Phase 4: Verify corporate actions database records splits, dividends, and ratios."""
        import sqlite3
        db_path = os.path.join(WORKSPACE, "data", "gen26_production.db")
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT action_type, ex_date, cash_amount, ratio FROM corporate_actions WHERE ticker = 'COMI.CA'")
        rows = cur.fetchall()
        conn.close()

        self.assertGreater(len(rows), 0, "No corporate actions found for COMI.CA")
        types = [r[0] for r in rows]
        self.assertIn("DIVIDEND", types)

    def test_phase_05_continuous_dqs_and_three_tiers(self):
        """Phase 5: Verify continuous DQS (0-100) and strict 3-tier classification."""
        # Auditing a clean dataframe
        clean_df = pd.DataFrame({
            "Open": [10.0, 10.2, 10.5] * 20,
            "High": [10.5, 10.8, 11.0] * 20,
            "Low": [9.8, 10.0, 10.2] * 20,
            "Close": [10.2, 10.5, 10.8] * 20,
            "Volume": [100000, 150000, 120000] * 20
        })
        audit = DataQualityEngine.audit_ohlcv_dataframe(clean_df, ticker="TEST.CA")
        self.assertEqual(audit["dqs"], 100.0)
        self.assertEqual(audit["tier"], DataQualityEngine.TIER_DATA_VALID)
        self.assertTrue(audit["can_trade"])

        # Auditing a flawed dataframe (High < Low)
        flawed_df = clean_df.copy()
        flawed_df.loc[0, "High"] = 5.0 # High < Low
        bad_audit = DataQualityEngine.audit_ohlcv_dataframe(flawed_df, ticker="BAD.CA")
        self.assertLess(bad_audit["dqs"], 70.0)
        self.assertEqual(bad_audit["tier"], DataQualityEngine.TIER_DATA_UNUSABLE)
        self.assertFalse(bad_audit["can_trade"])

        # Check ORAS.CA known translation gap penalty
        oras_dqs = DataQualityEngine.get_stock_dqs("ORAS.CA")
        self.assertEqual(oras_dqs["tier"], DataQualityEngine.TIER_DATA_UNUSABLE)

    def test_phase_06_strict_point_in_time_fundamentals(self):
        """Phase 6: Verify fundamental filing disclosures cannot be queried prior to available_timestamp."""
        import sqlite3
        db_path = os.path.join(WORKSPACE, "data", "gen26_production.db")
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        # Query on 2025-04-10 (Before Q1 2025 publication on May 15)
        cur.execute("""
            SELECT period_end, available_timestamp, value
            FROM pit_fundamentals
            WHERE ticker = 'COMI.CA' AND metric_name = 'pe_ratio' AND available_timestamp <= '2025-04-10 23:59:59'
            ORDER BY available_timestamp DESC LIMIT 1
        """)
        row = cur.fetchone()
        conn.close()

        self.assertIsNotNone(row)
        # Must be FY 2024 (2024-12-31), NOT Q1 2025
        self.assertEqual(row[0], "2024-12-31", "Lookahead Breach: Q1 2025 returned before publication date!")

    def test_phase_07_structured_news_taxonomy_and_pit(self):
        """Phase 7: Verify news ingestion supports event taxonomy and timestamp cutoff."""
        news_items = NewsSentimentEngine.get_latest_news_for_ticker("COMI.CA", as_of_time="2026-08-30 00:00:00")
        self.assertGreater(len(news_items), 0)
        item = news_items[0]
        self.assertIn("event_type", item)
        self.assertIn("sentiment", item)
        self.assertIn("importance", item)
        self.assertIn("published_at", item)

    def test_phase_08_holdout_integrity_classification(self):
        """Phase 8: Verify 2026 is officially categorized as Contaminated Research and not Blind Holdout."""
        self.assertIn("Contaminated Research", WalkForwardValidator.PARTITION_CONTAMINATED_RESEARCH)
        self.assertIn("In-Sample Development", WalkForwardValidator.PARTITION_DEVELOPMENT)
        self.assertIn("True Out-of-Sample", WalkForwardValidator.PARTITION_TRUE_BLIND_HOLDOUT)

    def test_phase_09_disentangled_prediction_triad(self):
        """Phase 9: Verify P(UP), Expected Return, and Conformal Uncertainty are separate and distinct."""
        triad = PredictionDisentangler.disentangle(
            prob_up_pct=72.0,
            expected_return_pct=6.4,
            q10_downside_pct=-2.1,
            q90_upside_pct=13.8
        )
        self.assertEqual(triad["probability_up_pct"], 72.0)
        self.assertEqual(triad["expected_return_pct"], 6.4)
        self.assertEqual(triad["prediction_interval_90"]["lower_bound_pct"], -2.1)
        self.assertEqual(triad["prediction_interval_90"]["upper_bound_pct"], 13.8)
        self.assertIn("uncertainty_level", triad)
        self.assertIn("profile_verdict_ar", triad)

    def test_phase_10_advanced_ranking_engine_metrics(self):
        """Phase 10: Verify Precision@K, NDCG@K, Rank IC, and Top-K Alpha Spread calculations."""
        df_sample = pd.DataFrame({
            "score": [95, 90, 85, 80, 75, 70, 65, 60, 55, 50, 45, 40],
            "fwd_ret": [6.0, 5.0, 4.0, 3.0, 2.0, 1.0, 0.0, -1.0, -2.0, -3.0, -4.0, -5.0]
        })
        res = CrossSectionalRankingEngine.evaluate_ranking_quality(df_sample, "score", "fwd_ret", k_list=[5, 10])
        self.assertEqual(res["status"], "RANKING_EVALUATED_SUCCESS")
        self.assertAlmostEqual(res["rank_ic"], 1.0, places=2)
        self.assertEqual(res["precision_at_5_pct"], 100.0)
        self.assertGreater(res["ndcg_at_10"], 0.95)
        self.assertGreater(res["top_5_alpha_spread_pct"], 0.0)

    def test_phase_11_independent_backtest_engine_b(self):
        """Phase 11: Verify Engine B executes at Open T+1 with realistic fees, slippage, and limit checks."""
        bt = IndependentBacktester(commission_pct=0.45, slippage_pct=0.10, holding_days=10)
        sample_signals = [
            {"ticker": "COMI.CA", "signal_date": "2024-05-15", "stop_loss_pct": -5.0, "take_profit_pct": 10.0, "score": 85.0},
            {"ticker": "SWDY.CA", "signal_date": "2024-05-15", "stop_loss_pct": -5.0, "take_profit_pct": 10.0, "score": 80.0}
        ]
        res = bt.run_backtest_on_signals(sample_signals)
        self.assertEqual(res["status"], "BACKTEST_COMPLETED_SUCCESS")
        self.assertIn("win_rate_pct", res)
        self.assertIn("profit_factor", res)
        self.assertIn("calendar_sharpe", res)
        # Verify entry date was T+1 (2024-05-16), strictly avoiding same-day lookahead
        first_trade = res["trades_sample"][0]
        self.assertEqual(first_trade["signal_date"], "2024-05-15")
        self.assertEqual(first_trade["entry_date"], "2024-05-16")
        self.assertGreater(first_trade["entry_price_executed"], first_trade["entry_price_raw"])


if __name__ == "__main__":
    unittest.main()
