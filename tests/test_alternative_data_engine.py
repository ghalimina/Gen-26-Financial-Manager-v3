#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# tests/test_alternative_data_engine.py — Unit Tests for Alternative Data Engine
# =============================================================================

import unittest
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.alternative_data_engine import (
    AlternativeDataEngine,
    EGX_SUPPLY_CHAIN_GRAPH
)


class TestAlternativeDataEngine(unittest.TestCase):

    def test_01_supply_chain_graph_mapping_integrity(self):
        """Verify EGX_SUPPLY_CHAIN_GRAPH maps raw material dependencies accurately."""
        # 1. JUFO.CA & EFID.CA mapped to SUGR.CA
        self.assertIn("JUFO.CA", EGX_SUPPLY_CHAIN_GRAPH)
        jufo_upstream = [u["ticker"] for u in EGX_SUPPLY_CHAIN_GRAPH["JUFO.CA"]["upstream_suppliers"]]
        self.assertIn("SUGR.CA", jufo_upstream)

        self.assertIn("EFID.CA", EGX_SUPPLY_CHAIN_GRAPH)
        efid_upstream = [u["ticker"] for u in EGX_SUPPLY_CHAIN_GRAPH["EFID.CA"]["upstream_suppliers"]]
        self.assertIn("SUGR.CA", efid_upstream)

        # 2. TMGH.CA & PHDC.CA mapped to ESRS.CA (Steel) and SVCE.CA (Cement)
        self.assertIn("TMGH.CA", EGX_SUPPLY_CHAIN_GRAPH)
        tmgh_upstream = [u["ticker"] for u in EGX_SUPPLY_CHAIN_GRAPH["TMGH.CA"]["upstream_suppliers"]]
        self.assertIn("ESRS.CA", tmgh_upstream)

        # 3. Exporters mapped to port facilities
        self.assertIn("ABUK.CA", EGX_SUPPLY_CHAIN_GRAPH)
        self.assertTrue(EGX_SUPPLY_CHAIN_GRAPH["ABUK.CA"]["is_exporter"])
        self.assertIn("port_facility", EGX_SUPPLY_CHAIN_GRAPH["ABUK.CA"])

    def test_02_exporter_marine_port_traffic_signal(self):
        """Verify marine port traffic triggers BULLISH_EXPORTS signal for ABUK.CA and MFPC.CA."""
        abuk_res = AlternativeDataEngine.fetch_alternative_signals("ABUK.CA")
        self.assertEqual(abuk_res["ticker"], "ABUK.CA")
        self.assertEqual(abuk_res["signal"], AlternativeDataEngine.SIGNAL_BULLISH_EXPORTS)
        self.assertGreater(abuk_res["alt_data_score"], 50.0)
        self.assertLessEqual(abuk_res["alt_data_score"], 100.0)
        self.assertIsNotNone(abuk_res["port_traffic_telemetry"])
        self.assertIn("vessels_docked_count", abuk_res["port_traffic_telemetry"])
        self.assertTrue("ميناء" in abuk_res["description_ar"] or "تصدير" in abuk_res["description_ar"])

        # MFPC.CA (Damietta Port)
        mfpc_res = AlternativeDataEngine.fetch_alternative_signals("MFPC.CA")
        self.assertEqual(mfpc_res["signal"], AlternativeDataEngine.SIGNAL_BULLISH_EXPORTS)
        self.assertGreater(mfpc_res["alt_data_score"], 50.0)

    def test_03_fmcg_sugar_cost_headwind_signal(self):
        """Verify raw material sugar price spike creates INPUT_COST_HEADWIND signal for JUFO.CA."""
        jufo_res = AlternativeDataEngine.fetch_alternative_signals("JUFO.CA")
        self.assertEqual(jufo_res["ticker"], "JUFO.CA")
        self.assertEqual(jufo_res["signal"], AlternativeDataEngine.SIGNAL_INPUT_COST_HEADWIND)
        self.assertLess(jufo_res["alt_data_score"], 0.0)
        self.assertGreaterEqual(jufo_res["alt_data_score"], -100.0)
        self.assertEqual(jufo_res["primary_catalyst"], "RAW_MATERIAL_SUGAR_PRICE_SPIKE")
        self.assertIn("السكر", jufo_res["description_ar"])

    def test_04_real_estate_material_margin_expansion(self):
        """Verify steel/cement cost moderation creates positive margin signal for TMGH.CA."""
        tmgh_res = AlternativeDataEngine.fetch_alternative_signals("TMGH.CA")
        self.assertEqual(tmgh_res["ticker"], "TMGH.CA")
        self.assertEqual(tmgh_res["signal"], AlternativeDataEngine.SIGNAL_MARGIN_EXPANSION)
        self.assertGreater(tmgh_res["alt_data_score"], 0.0)
        self.assertIn("حديد", tmgh_res["description_ar"])

    def test_05_unknown_and_empty_ticker_fallback(self):
        """Verify unmapped or invalid tickers safely return NEUTRAL baseline."""
        unknown_res = AlternativeDataEngine.fetch_alternative_signals("UNKNOWN.CA")
        self.assertEqual(unknown_res["ticker"], "UNKNOWN.CA")
        self.assertEqual(unknown_res["signal"], AlternativeDataEngine.SIGNAL_NEUTRAL)
        self.assertEqual(unknown_res["alt_data_score"], 0.0)
        self.assertEqual(len(unknown_res["supply_chain_dependencies"]), 0)

        none_res = AlternativeDataEngine.fetch_alternative_signals(None)
        self.assertEqual(none_res["signal"], AlternativeDataEngine.SIGNAL_NEUTRAL)

    def test_06_score_bounds_and_graph_export(self):
        """Verify that all mapped tickers return scores bounded within [-100, +100]."""
        graph = AlternativeDataEngine.get_all_supply_chain_relationships()
        self.assertIsInstance(graph, dict)

        for ticker in graph.keys():
            res = AlternativeDataEngine.fetch_alternative_signals(ticker)
            self.assertGreaterEqual(res["alt_data_score"], -100.0)
            self.assertLessEqual(res["alt_data_score"], 100.0)
            self.assertIn("description_ar", res)
            self.assertGreater(len(res["description_ar"]), 10)


if __name__ == "__main__":
    unittest.main()
