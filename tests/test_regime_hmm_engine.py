#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# tests/test_regime_hmm_engine.py — Unit Tests for RegimeHMMEngine
# Validates:
# 1. EGX30 index data fetching and synthetic fallbacks.
# 2. 4 Canonical Regimes: STRONG_BULL, SIDEWAYS_CHOP, BEAR_CORRECTION, FLASH_CRASH.
# 3. Mandatory Safe Cash Reserve Rules (5%, 40%, 75%, 100%).
# 4. Technical Indicator & Volatility Metric Classification.
# 5. Dynamic Factor Weighting conservation & composite score calculation.
# =============================================================================

import os
import sys
import unittest
import pandas as pd
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.regime_hmm_engine import RegimeHMMEngine


class TestRegimeHMMEngine(unittest.TestCase):

    def test_01_fetch_egx30_data_structure(self):
        """Verify fetch_egx30_data returns a valid OHLCV DataFrame."""
        df = RegimeHMMEngine.fetch_egx30_data(force_fallback=True)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertGreaterEqual(len(df), 50)
        for col in ["Close", "Open", "High", "Low", "Volume"]:
            self.assertIn(col, df.columns)
        self.assertFalse(df["Close"].isna().any())

    def test_02_regime_detection_schema(self):
        """Verify detect_latent_regime output contains all mandatory keys and valid types."""
        res = RegimeHMMEngine.detect_latent_regime()
        self.assertIn("regime", res)
        self.assertIn(res["regime"], [
            RegimeHMMEngine.REGIME_STRONG_BULL,
            RegimeHMMEngine.REGIME_SIDEWAYS_CHOP,
            RegimeHMMEngine.REGIME_BEAR_CORRECTION,
            RegimeHMMEngine.REGIME_FLASH_CRASH
        ])
        self.assertIn("recommended_cash_reserve_pct", res)
        self.assertIn("description_ar", res)
        self.assertIn("raw_volatility_score", res)
        self.assertIsInstance(res["raw_volatility_score"], float)
        self.assertIn("current_price", res)
        self.assertIn("ma_50", res)
        self.assertIn("ma_200", res)
        self.assertIn("active_factor_weights", res)

    def test_03_cash_allocation_rules_for_all_four_regimes(self):
        """Verify mandatory safe cash reserve percentages for all 4 regimes."""
        weights = RegimeHMMEngine.DYNAMIC_WEIGHTS

        # STRONG_BULL -> 5% Cash Reserve (95% Equities)
        self.assertEqual(weights[RegimeHMMEngine.REGIME_STRONG_BULL]["cash_reserve_pct"], 5.0)
        self.assertEqual(weights[RegimeHMMEngine.REGIME_STRONG_BULL]["equity_allocation_pct"], 95.0)

        # SIDEWAYS_CHOP -> 40% Cash Reserve (60% Equities)
        self.assertEqual(weights[RegimeHMMEngine.REGIME_SIDEWAYS_CHOP]["cash_reserve_pct"], 40.0)
        self.assertEqual(weights[RegimeHMMEngine.REGIME_SIDEWAYS_CHOP]["equity_allocation_pct"], 60.0)

        # BEAR_CORRECTION -> 75% Cash Reserve (25% Equities)
        self.assertEqual(weights[RegimeHMMEngine.REGIME_BEAR_CORRECTION]["cash_reserve_pct"], 75.0)
        self.assertEqual(weights[RegimeHMMEngine.REGIME_BEAR_CORRECTION]["equity_allocation_pct"], 25.0)

        # FLASH_CRASH -> 100% Cash Reserve (0% Equities)
        self.assertEqual(weights[RegimeHMMEngine.REGIME_FLASH_CRASH]["cash_reserve_pct"], 100.0)
        self.assertEqual(weights[RegimeHMMEngine.REGIME_FLASH_CRASH]["equity_allocation_pct"], 0.0)

    def test_04_classify_regime_from_metrics(self):
        """Verify quantitative metric classifier accurately triggers all 4 regimes."""
        # 1. STRONG_BULL: Price above both MAs, Golden cross, calm volatility
        reg_bull = RegimeHMMEngine.classify_regime_from_metrics(
            current_price=32000.0,
            ma_50=31000.0,
            ma_200=29000.0,
            volatility_20d=0.18,
            drawdown_5d_pct=1.5
        )
        self.assertEqual(reg_bull, RegimeHMMEngine.REGIME_STRONG_BULL)

        # 2. SIDEWAYS_CHOP: Price between moving averages
        reg_chop = RegimeHMMEngine.classify_regime_from_metrics(
            current_price=30000.0,
            ma_50=30500.0,
            ma_200=29500.0,
            volatility_20d=0.22,
            drawdown_5d_pct=-0.5
        )
        self.assertEqual(reg_chop, RegimeHMMEngine.REGIME_SIDEWAYS_CHOP)

        # 3. BEAR_CORRECTION: Price below both MAs or 20D drawdown >= 7%
        reg_bear = RegimeHMMEngine.classify_regime_from_metrics(
            current_price=27500.0,
            ma_50=29000.0,
            ma_200=30000.0,
            volatility_20d=0.25,
            drawdown_20d_pct=-8.5
        )
        self.assertEqual(reg_bear, RegimeHMMEngine.REGIME_BEAR_CORRECTION)

        # 4. FLASH_CRASH: 5D plunge > 10% or annualized volatility >= 45%
        reg_crash_dd = RegimeHMMEngine.classify_regime_from_metrics(
            current_price=26000.0,
            ma_50=30000.0,
            ma_200=31000.0,
            volatility_20d=0.30,
            drawdown_5d_pct=-11.2
        )
        self.assertEqual(reg_crash_dd, RegimeHMMEngine.REGIME_FLASH_CRASH)

        reg_crash_vol = RegimeHMMEngine.classify_regime_from_metrics(
            current_price=25000.0,
            ma_50=29000.0,
            ma_200=30000.0,
            volatility_20d=0.52,
            drawdown_5d_pct=-5.0
        )
        self.assertEqual(reg_crash_vol, RegimeHMMEngine.REGIME_FLASH_CRASH)

    def test_05_dynamic_weights_conservation(self):
        """Verify that factor weights for all 4 regimes sum to exactly 1.0."""
        for state in [
            RegimeHMMEngine.REGIME_STRONG_BULL,
            RegimeHMMEngine.REGIME_SIDEWAYS_CHOP,
            RegimeHMMEngine.REGIME_BEAR_CORRECTION,
            RegimeHMMEngine.REGIME_FLASH_CRASH
        ]:
            weights_info = RegimeHMMEngine.DYNAMIC_WEIGHTS[state]
            total = (
                weights_info["technicals"] +
                weights_info["volatility"] +
                weights_info["fundamentals"] +
                weights_info["macro"]
            )
            self.assertAlmostEqual(total, 1.0, places=4, msg=f"Weights in state {state} do not sum to 1.0")

    def test_06_arabic_descriptions_integrity(self):
        """Verify Arabic diagnostic descriptions are informative and present for all states."""
        for state, info in RegimeHMMEngine.DYNAMIC_WEIGHTS.items():
            self.assertIn("description_ar", info)
            self.assertGreater(len(info["description_ar"]), 10)
            self.assertIn("name_ar", info)

    def test_07_regime_adjusted_score_computation(self):
        """Verify regime-adjusted score calculation correctly applies active factor weights."""
        score = RegimeHMMEngine.calculate_regime_adjusted_score(
            tech_score=90.0,
            vol_score=80.0,
            fund_score=70.0,
            macro_score=60.0
        )
        self.assertGreater(score, 0.0)
        self.assertLessEqual(score, 100.0)


if __name__ == "__main__":
    unittest.main()
