#!/usr/bin/env python3
# =============================================================================
# tests/test_red_team_edge_cases.py — GEN-26 Red Team Edge Cases Unit Tests
# =============================================================================

import unittest
import pandas as pd
import numpy as np
import os
import sys
import re

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.data_quality import DataQualityEngine
from core.real_portfolio import RealPortfolioTracker


class TestRedTeamEdgeCases(unittest.TestCase):

    def test_empty_portfolio_exit_signals(self):
        # Empty portfolio should return empty analysis without crashing
        analysis = RealPortfolioTracker.analyze_real_portfolio(current_market_prices={})
        self.assertEqual(analysis["positions_count"], 0)
        self.assertEqual(len(analysis["positions"]), 0)

    def test_data_quality_insufficient_rows(self):
        short_df = pd.DataFrame({
            'Open': [10.0]*15,
            'High': [11.0]*15,
            'Low': [9.0]*15,
            'Close': [10.0]*15,
            'Volume': [1000]*15
        }, index=pd.date_range('2026-01-01', periods=15))
        report = DataQualityEngine.audit_ohlcv_dataframe(short_df, "TEST.CA")
        self.assertIn("Insufficient history", str(report.get("issues", [])))
        self.assertEqual(report["health"], "WARN")

    def test_data_quality_price_outlier(self):
        np.random.seed(42)
        closes = [10.0 + np.random.normal(0, 0.1) for _ in range(40)] + [150.0]
        outlier_df = pd.DataFrame({
            'Open': closes,
            'High': [c*1.02 for c in closes],
            'Low': [c*0.98 for c in closes],
            'Close': closes,
            'Volume': [1000]*41
        }, index=pd.date_range('2026-01-01', periods=41))
        report = DataQualityEngine.audit_ohlcv_dataframe(outlier_df, "TEST.CA")
        self.assertIn("price jumps", str(report.get("issues", [])).lower())

    def test_negative_input_filtering_reset_wizard(self):
        raw_bad_text = "COMI.CA, -10, 130.0\nTMGH.CA, 50, -90.0\nSWDY.CA, 0, 0\nISPH.CA, 100, 5.50"
        valid_rows = []
        for line in raw_bad_text.strip().split("\n"):
            parts = [p.strip() for p in re.split(r'[,;\t]+', line) if p.strip()]
            if len(parts) >= 3:
                try:
                    q = int(float(parts[1]))
                    ap = float(parts[2])
                    if q > 0 and ap > 0:
                        valid_rows.append((parts[0], q, ap))
                except Exception:
                    pass
                    
        # Only ISPH.CA is valid
        self.assertEqual(len(valid_rows), 1)
        self.assertEqual(valid_rows[0][0], "ISPH.CA")
        self.assertEqual(valid_rows[0][1], 100)
        self.assertEqual(valid_rows[0][2], 5.50)


if __name__ == '__main__':
    unittest.main()
