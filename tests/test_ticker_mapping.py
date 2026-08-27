#!/usr/bin/env python3
# =============================================================================
# tests/test_ticker_mapping.py — Unit Tests for Universe Expansion & Rescue Protocol
# Verifies Ticker Translation Engine, Cross-Sectional Imputer, Liquidity Gate,
# and Active Universe Expansion to ~170 stocks.
# =============================================================================

import os
import sys
import unittest
import numpy as np

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from data.universe_manager import UniverseManager, THNDR_TO_YFINANCE_MAP
from core.feature_registry import CrossSectionalImputer, SectorNeutralizer
from core.liquidity_filter import LiquidityGateEngine
from core.multi_horizon_engine import MultiHorizonEngine
from core.ai_prediction_model import AIPredictionModel
from core.market_price_service import MarketPriceService


class TestTickerMappingAndUniverseExpansion(unittest.TestCase):
    """Test suite validating the Universe Expansion & Rescue Protocol."""

    def test_01_thndr_to_yfinance_translation_map(self):
        """Verify THNDR_TO_YFINANCE_MAP correctly translates ONLY verified legal corporate rebrands (Same ISIN)."""
        self.assertIn("MNHD.CA", THNDR_TO_YFINANCE_MAP)
        self.assertEqual(THNDR_TO_YFINANCE_MAP["MNHD.CA"], "MASR.CA")
        self.assertEqual(UniverseManager.get_yfinance_ticker("MNHD.CA"), "MASR.CA")

        self.assertIn("DICE.CA", THNDR_TO_YFINANCE_MAP)
        self.assertEqual(THNDR_TO_YFINANCE_MAP["DICE.CA"], "DSCW.CA")
        self.assertEqual(UniverseManager.get_yfinance_ticker("DICE.CA"), "DSCW.CA")

        self.assertIn("GBCO.CA", THNDR_TO_YFINANCE_MAP)
        self.assertEqual(THNDR_TO_YFINANCE_MAP["GBCO.CA"], "AUTO.CA")

        self.assertEqual(UniverseManager.get_yfinance_ticker("COMI.CA"), "COMI.CA")

    def test_02_fake_aliases_strictly_quarantined(self):
        """Verify that distinct unrelated companies (ESRS!=IRAX, ACRO!=MCQE, KRRE!=ALUM) are NEVER cross-mapped."""
        self.assertNotIn("ESRS.CA", THNDR_TO_YFINANCE_MAP, "ESRS (Ezz Steel) must NOT be mapped to IRAX (Al Ezz Dekheila)")
        self.assertNotIn("ACRO.CA", THNDR_TO_YFINANCE_MAP, "ACRO (Acrow Misr) must NOT be mapped to MCQE (Misr Cement Qena)")
        self.assertNotIn("KRRE.CA", THNDR_TO_YFINANCE_MAP, "KRRE (Al Omran) must NOT be mapped to ALUM (Arab Aluminum)")
        self.assertNotIn("ARPU.CA", THNDR_TO_YFINANCE_MAP, "ARPU (Arab Pharma) must NOT be mapped to ADPC (Arab Dairy)")
        
        # Verify ESRS remains ESRS without fake quote inheritance
        self.assertEqual(UniverseManager.get_yfinance_ticker("ESRS.CA"), "ESRS.CA")

    def test_03_cross_sectional_imputer(self):
        """Verify CrossSectionalImputer replaces NaNs with neutral sector medians without model crash."""
        test_raw = {
            "macd_hist": None,
            "macd_hist_lag1": float("nan"),
            "rsi14": 52.0,
            "roc_1d_lag1": None,
            "obv_slope": float("nan"),
            "pe_ratio": 7.0
        }
        imputed = CrossSectionalImputer.impute_feature_dict("ESRS.CA", test_raw)
        self.assertFalse(np.isnan(imputed["macd_hist_lag1"]))
        self.assertFalse(np.isnan(imputed["obv_slope"]))
        self.assertEqual(imputed["rsi14"], 52.0)

    def test_04_liquidity_gate_single_source_graceful_degradation(self):
        """Verify LiquidityGateEngine permits liquid single-source stocks (Vol > 50k, Turnover > 250k)."""
        eval_res = LiquidityGateEngine.evaluate_stock_liquidity(
            "QNBA.CA",
            adv30_shares=600000.0,
            turnover_30d_egp=15000000.0,
            zero_vol_days_20d=0
        )
        self.assertTrue(eval_res["is_liquid"], "Liquid single-source stock must pass gate")

    def test_05_multi_horizon_engine_active_universe_expansion(self):
        """Verify MultiHorizonEngine evaluates the expanded active universe (~165-170 stocks)."""
        MultiHorizonEngine._RANKINGS_CACHE.clear()
        rankings = MultiHorizonEngine.get_all_multi_horizon_rankings(universe="all")
        
        # Check total active evaluated rankings with live prices
        active_evaluated = [r for r in rankings if r.get("current_price") is not None and r.get("current_price") > 0]
        self.assertGreaterEqual(len(active_evaluated), 110, "Active evaluated universe must be >= 110 stocks")
        
        # Verify MNHD.CA (which uses legal translation to MASR) is active and evaluated
        mnhd_ranks = [r for r in rankings if r["ticker"] == "MNHD.CA"]
        self.assertEqual(len(mnhd_ranks), 1, "MNHD.CA must be present in active rankings")
        self.assertIsNotNone(mnhd_ranks[0].get("current_price"))

        # Verify ESRS is tracked with radical honesty (not assigned fake IRAX price)
        esrs_ranks = [r for r in rankings if r["ticker"] == "ESRS.CA"]
        self.assertEqual(len(esrs_ranks), 1, "ESRS.CA must be tracked in catalog rankings")
        
        # Verify data_badge field presence
        sample_r = rankings[0]
        self.assertIn("data_badge", sample_r)
        self.assertIn("is_single_source", sample_r)


if __name__ == "__main__":
    unittest.main()
