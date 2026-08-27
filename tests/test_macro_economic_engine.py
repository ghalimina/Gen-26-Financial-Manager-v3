#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# tests/test_macro_economic_engine.py — Unit Tests for MacroEconomicEngine
# =============================================================================

import unittest
import os
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.macro_economic_engine import MacroEconomicEngine


class TestMacroEconomicEngine(unittest.TestCase):

    def setUp(self):
        # Reset cache before tests
        MacroEconomicEngine._cache.clear()
        MacroEconomicEngine._cache_timestamps.clear()

    def test_01_fetch_interest_rate(self):
        """Verify fetch_interest_rate returns a plausible rate and uses TTL cache."""
        rate1 = MacroEconomicEngine.fetch_interest_rate()
        self.assertIsInstance(rate1, float)
        self.assertGreater(rate1, 5.0)
        self.assertLess(rate1, 45.0)

        # TTL cache hit verification
        MacroEconomicEngine._cache["interest_rate"] = 28.50
        MacroEconomicEngine._cache_timestamps["interest_rate"] = time.time()
        rate_cached = MacroEconomicEngine.fetch_interest_rate(force_refresh=False)
        self.assertEqual(rate_cached, 28.50)

        # Force refresh resets cache
        rate_refreshed = MacroEconomicEngine.fetch_interest_rate(force_refresh=True)
        self.assertIsInstance(rate_refreshed, float)

    def test_02_fetch_inflation_rate(self):
        """Verify fetch_inflation_rate returns plausible CPI and respects caching."""
        inf1 = MacroEconomicEngine.fetch_inflation_rate()
        self.assertIsInstance(inf1, float)
        self.assertGreater(inf1, 5.0)
        self.assertLess(inf1, 50.0)

        # Cache check
        MacroEconomicEngine._cache["inflation_rate"] = 29.90
        MacroEconomicEngine._cache_timestamps["inflation_rate"] = time.time()
        self.assertEqual(MacroEconomicEngine.fetch_inflation_rate(force_refresh=False), 29.90)

    def test_03_fetch_usd_egp(self):
        """Verify fetch_usd_egp returns plausible exchange rate."""
        usd1 = MacroEconomicEngine.fetch_usd_egp()
        self.assertIsInstance(usd1, float)
        self.assertGreater(usd1, 20.0)
        self.assertLess(usd1, 90.0)

        # Cache check
        MacroEconomicEngine._cache["usd_egp"] = 49.25
        MacroEconomicEngine._cache_timestamps["usd_egp"] = time.time()
        self.assertEqual(MacroEconomicEngine.fetch_usd_egp(force_refresh=False), 49.25)

    def test_04_determine_macro_regime_classification(self):
        """Verify regime classification across various economic states."""
        # 1. Rate Hiking Cycle: High CBE rate
        regime_hiking = MacroEconomicEngine.determine_macro_regime(
            interest_rate=27.25, inflation=25.0, usd_egp=48.5
        )
        self.assertEqual(regime_hiking, MacroEconomicEngine.REGIME_RATE_HIKING_CYCLE)

        # 2. Stagflation: Runaway inflation exceeding interest rate
        regime_stag = MacroEconomicEngine.determine_macro_regime(
            interest_rate=18.0, inflation=35.0, usd_egp=50.0
        )
        self.assertEqual(regime_stag, MacroEconomicEngine.REGIME_STAGFLATION)

        # 3. Devaluation Boom: Depreciated currency with moderate interest rate & controlled inflation
        regime_deval = MacroEconomicEngine.determine_macro_regime(
            interest_rate=16.0, inflation=14.0, usd_egp=48.0
        )
        self.assertEqual(regime_deval, MacroEconomicEngine.REGIME_DEVALUATION_BOOM)

        # 4. Stable Growth: Low inflation, low rates, stable currency
        regime_growth = MacroEconomicEngine.determine_macro_regime(
            interest_rate=12.0, inflation=8.0, usd_egp=30.85
        )
        self.assertEqual(regime_growth, MacroEconomicEngine.REGIME_STABLE_GROWTH)

    def test_05_determine_macro_regime_edge_cases(self):
        """Verify regime classifier handles edge cases and invalid inputs gracefully."""
        self.assertIn(
            MacroEconomicEngine.determine_macro_regime(-5.0, -10.0, -50.0),
            [MacroEconomicEngine.REGIME_RATE_HIKING_CYCLE, MacroEconomicEngine.REGIME_STABLE_GROWTH]
        )
        self.assertEqual(
            MacroEconomicEngine.determine_macro_regime("invalid", None, {}),
            MacroEconomicEngine.REGIME_RATE_HIKING_CYCLE
        )

    def test_06_get_sector_biases(self):
        """Verify sector biases return proper overweight/underweight sectors for each regime."""
        # Rate Hiking Cycle -> Overweight Banks, Underweight Leveraged Real Estate
        biases_hiking = MacroEconomicEngine.get_sector_biases(MacroEconomicEngine.REGIME_RATE_HIKING_CYCLE)
        self.assertIn("overweight", biases_hiking)
        self.assertIn("underweight", biases_hiking)
        self.assertIn("sector_multipliers", biases_hiking)
        self.assertTrue(any("Bank" in s for s in biases_hiking["overweight"]))
        self.assertTrue(any("Real Estate" in s for s in biases_hiking["underweight"]))
        self.assertGreater(biases_hiking["sector_multipliers"].get("Banking", 1.0), 1.0)
        self.assertLess(biases_hiking["sector_multipliers"].get("Real Estate", 1.0), 1.0)

        # Devaluation Boom -> Overweight Fertilizers/Exporters, Underweight Import-dependent
        biases_deval = MacroEconomicEngine.get_sector_biases(MacroEconomicEngine.REGIME_DEVALUATION_BOOM)
        self.assertTrue(any("Fertilizer" in s or "Export" in s for s in biases_deval["overweight"]))
        self.assertTrue(any("Import" in s or "Auto" in s for s in biases_deval["underweight"]))
        self.assertGreater(biases_deval["sector_multipliers"].get("Fertilizers", 1.0), 1.0)

        # Stagflation -> Overweight Food/Staples & Healthcare
        biases_stag = MacroEconomicEngine.get_sector_biases(MacroEconomicEngine.REGIME_STAGFLATION)
        self.assertTrue(any("Food" in s or "Healthcare" in s for s in biases_stag["overweight"]))

        # Stable Growth -> Overweight Real Estate & Fintech
        biases_growth = MacroEconomicEngine.get_sector_biases(MacroEconomicEngine.REGIME_STABLE_GROWTH)
        self.assertTrue(any("Real Estate" in s or "Fintech" in s for s in biases_growth["overweight"]))

    def test_07_get_macro_telemetry(self):
        """Verify get_macro_telemetry compiles full structured dictionary."""
        telemetry = MacroEconomicEngine.get_macro_telemetry()
        self.assertEqual(telemetry["status"], "HEALTHY")
        self.assertIn("timestamp", telemetry)
        self.assertIn("interest_rate_pct", telemetry)
        self.assertIn("inflation_rate_pct", telemetry)
        self.assertIn("usd_egp", telemetry)
        self.assertIn("macro_regime", telemetry)
        self.assertIn("macro_regime_ar", telemetry)
        self.assertIn("sector_biases", telemetry)
        self.assertIn("summary_ar", telemetry)

    def test_08_instance_methods(self):
        """Verify instance methods mirror class methods correctly."""
        engine = MacroEconomicEngine()
        self.assertIsInstance(engine.get_interest_rate(), float)
        self.assertIsInstance(engine.get_inflation_rate(), float)
        self.assertIsInstance(engine.get_usd_egp(), float)
        self.assertIsInstance(engine.get_regime(), str)
        self.assertIsInstance(engine.get_biases(), dict)


if __name__ == "__main__":
    unittest.main()
