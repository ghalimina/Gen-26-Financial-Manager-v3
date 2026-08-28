#!/usr/bin/env python3
# =============================================================================
# tests/test_universe_expansion.py — Verification of Thndr 224-Universe & Liquidity Gate
# =============================================================================

import os
import sys
import json
import unittest
import pandas as pd
import numpy as np

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from data.universe_manager import UniverseManager, THNDR_UNIVERSE_FILE
from core.liquidity_filter import LiquidityGateEngine
from core.multi_horizon_engine import MultiHorizonEngine
from core.feature_registry import FeatureRegistry
from dashboard.app import app


class TestUniverseExpansionAndLiquidityGate(unittest.TestCase):
    """
    Exhaustive Test Suite for Universe Expansion to 224 Thndr EGX Tickers
    and the Institutional Dynamic Liquidity Gate Engine.
    """

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_01_thndr_universe_json_structure_and_count(self):
        """Verify data/thndr_egx_244_universe.json exists and contains 244 valid stocks."""
        self.assertTrue(os.path.exists(THNDR_UNIVERSE_FILE), f"Missing {THNDR_UNIVERSE_FILE}")
        with open(THNDR_UNIVERSE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIn("stocks", data)
        stocks = data["stocks"]
        self.assertGreaterEqual(len(stocks), 224, f"Expected at least 224 stocks, found {len(stocks)}")

        seen_tickers = set()
        for s in stocks:
            self.assertIn("ticker", s)
            self.assertIn("symbol", s)
            self.assertIn("name_ar", s)
            self.assertIn("name_en", s)
            self.assertIn("sector", s)
            self.assertIn("isin", s)
            self.assertTrue(s.get("thndr_available", False))
            self.assertIn("is_active", s)
            self.assertIsInstance(s["is_active"], bool)

            sym = s["ticker"].upper().strip()
            self.assertNotIn(sym, seen_tickers, f"Duplicate ticker found: {sym}")
            seen_tickers.add(sym)

    def test_02_universe_manager_loading_and_stats(self):
        """Verify UniverseManager methods load catalog and compute stats properly."""
        tickers = UniverseManager.get_all_tickers()
        self.assertGreaterEqual(len(tickers), 224)
        self.assertIn("COMI.CA", tickers)
        self.assertIn("SWDY.CA", tickers)

        meta = UniverseManager.get_ticker_metadata("COMI.CA")
        self.assertIsNotNone(meta)
        self.assertEqual(meta["symbol"], "COMI")

        stats = UniverseManager.get_universe_stats()
        self.assertGreaterEqual(stats["total_count"], 224)
        self.assertGreater(stats["sectors_count"], 5)
        self.assertGreaterEqual(stats["thndr_available_count"], 224)

    def test_03_universe_manager_batch_download_handles_delisted(self):
        """Verify batch downloading chunks with error handling for delisted tickers."""
        test_chunk = ["COMI.CA", "DELISTED_FAKE_99.CA", "HALTED_STOCK_88.CA"]
        quotes = UniverseManager.batch_download_market_data(test_chunk, batch_size=20, timeout_sec=3.0)
        self.assertIsInstance(quotes, dict)
        self.assertIn("COMI.CA", quotes)
        self.assertIn("DELISTED_FAKE_99.CA", quotes)
        self.assertIn("HALTED_STOCK_88.CA", quotes)
        self.assertGreater(quotes["COMI.CA"]["price"], 0)

    def test_04_liquidity_gate_three_rules_enforcement(self):
        """Verify strict enforcement of the 3 institutional liquidity gate rules."""
        # Case A: Passes all 3 rules (Liquid Blue-Chip)
        res_pass = LiquidityGateEngine.evaluate_stock_liquidity(
            ticker="COMI.CA",
            adv30_shares=1800000,
            turnover_30d_egp=250000000,
            zero_vol_days_20d=0
        )
        self.assertTrue(res_pass["is_liquid"])
        self.assertEqual(res_pass["status"], "TRADABLE_LIQUID")
        self.assertEqual(len(res_pass["rejection_reasons"]), 0)

        # Case B: Fails Rule 1 (Volume <= 500,000 shares)
        res_low_vol = LiquidityGateEngine.evaluate_stock_liquidity(
            ticker="LOWVOL.CA",
            adv30_shares=300000,
            turnover_30d_egp=5000000,
            zero_vol_days_20d=0
        )
        self.assertFalse(res_low_vol["is_liquid"])
        self.assertEqual(res_low_vol["status"], "ILLIQUID")
        self.assertFalse(res_low_vol["checks"]["pass_volume"])
        self.assertTrue(res_low_vol["checks"]["pass_turnover"])

        # Case C: Fails Rule 2 (Turnover <= 1,000,000 EGP)
        res_low_turnover = LiquidityGateEngine.evaluate_stock_liquidity(
            ticker="PENNY.CA",
            adv30_shares=800000,
            turnover_30d_egp=600000,
            zero_vol_days_20d=0
        )
        self.assertFalse(res_low_turnover["is_liquid"])
        self.assertEqual(res_low_turnover["status"], "ILLIQUID")
        self.assertTrue(res_low_turnover["checks"]["pass_volume"])
        self.assertFalse(res_low_turnover["checks"]["pass_turnover"])

        # Case D: Fails Rule 3 (Zero volume trading days in last 20 >= 3)
        res_zero_days = LiquidityGateEngine.evaluate_stock_liquidity(
            ticker="HALTED.CA",
            adv30_shares=1200000,
            turnover_30d_egp=15000000,
            zero_vol_days_20d=4
        )
        self.assertFalse(res_zero_days["is_liquid"])
        self.assertEqual(res_zero_days["status"], "ILLIQUID")
        self.assertFalse(res_zero_days["checks"]["pass_continuity"])

    def test_05_mock_224_universe_100_illiquid_filtering(self):
        """
        Mock a full 224-stock universe where exactly 100 are highly illiquid.
        Assert that LiquidityGateEngine drops exactly the 100 illiquid ones
        and passes only the 124 liquid stocks to the downstream feature registry.
        """
        mock_universe_tickers = [f"STOCK_{i:03d}.CA" for i in range(1, 225)]
        self.assertEqual(len(mock_universe_tickers), 224)

        # Build mock market data: 124 Liquid, 100 Illiquid
        mock_market_data = {}
        expected_liquid = set()
        expected_illiquid = set()

        for idx, sym in enumerate(mock_universe_tickers, start=1):
            if idx <= 124:
                # Liquid stock
                expected_liquid.add(sym)
                mock_market_data[sym] = {
                    "price": 50.0 + (idx % 20),
                    "volume_30d_avg": 1500000.0,
                    "turnover_egp": 75000000.0,
                    "zero_volume_days_20d": 0
                }
            else:
                # Illiquid stock (100 total)
                expected_illiquid.add(sym)
                mock_market_data[sym] = {
                    "price": 0.85,
                    "volume_30d_avg": 50000.0,      # Fails Rule 1 (< 500k)
                    "turnover_egp": 42500.0,        # Fails Rule 2 (< 1M EGP)
                    "zero_volume_days_20d": 5       # Fails Rule 3 (>= 3)
                }

        self.assertEqual(len(expected_liquid), 124)
        self.assertEqual(len(expected_illiquid), 100)

        # Run Liquidity Gate Filter
        gate_result = LiquidityGateEngine.filter_universe(
            tickers=mock_universe_tickers,
            market_data=mock_market_data
        )

        self.assertEqual(gate_result["total_universe_count"], 224)
        self.assertEqual(gate_result["liquid_count"], 124)
        self.assertEqual(gate_result["illiquid_count"], 100)
        self.assertEqual(set(gate_result["liquid_tickers"]), expected_liquid)
        self.assertEqual(set(gate_result["illiquid_tickers"]), expected_illiquid)

        # Pass only the 124 liquid stocks to the downstream FeatureRegistry
        liquid_features = {}
        for sym in gate_result["liquid_tickers"]:
            q = mock_market_data[sym]
            vec = FeatureRegistry.get_feature_vector(sym, current_price=q["price"])
            liquid_features[sym] = vec
            self.assertEqual(len(vec), 21)

        self.assertEqual(len(liquid_features), 124)

    def test_06_multi_horizon_skips_ml_inference_for_illiquid_stocks(self):
        """Verify MultiHorizonEngine skips ML inference for illiquid stocks and flags STATUS=ILLIQUID."""
        # 1. Liquid Stock
        liquid_analysis = MultiHorizonEngine.get_stock_multi_horizon_analysis("COMI.CA")
        self.assertIsNotNone(liquid_analysis)
        self.assertEqual(liquid_analysis["status"], "TRADABLE_LIQUID")
        self.assertTrue(liquid_analysis["is_liquid"])
        self.assertFalse(liquid_analysis["ai_forecast"].get("skipped", False))

        # 2. Illiquid Stock
        illiquid_analysis = MultiHorizonEngine.get_stock_multi_horizon_analysis("RTVC_P.CA")
        self.assertIsNotNone(illiquid_analysis)
        self.assertIn(illiquid_analysis["status"], ["ILLIQUID", "DATA_INSUFFICIENT"])
        self.assertFalse(illiquid_analysis["is_liquid"])
        self.assertTrue(illiquid_analysis["ai_forecast"].get("skipped", False))
        self.assertEqual(illiquid_analysis["decision"], "AVOID")
        self.assertFalse(illiquid_analysis["is_tradable"])

    def test_07_api_funnel_stats_endpoint(self):
        """Verify GET /api/universe/funnel_stats returns 200 with 224 total universe and counts."""
        resp = self.app.get("/api/universe/funnel_stats")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.get_data(as_text=True))

        self.assertIn("total_universe", data)
        self.assertIn("liquid_count", data)
        self.assertIn("opportunities_count", data)
        self.assertIn("funnel_label_ar", data)
        self.assertGreaterEqual(data["total_universe"], 224)
        self.assertGreater(data["liquid_count"], 0)
        self.assertGreater(data["opportunities_count"], 0)


if __name__ == "__main__":
    unittest.main()
