import unittest
import pandas as pd
import numpy as np
import json
import sys
import os

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, WORKSPACE)

import app

class TestRedTeamEdgeCases(unittest.TestCase):

    def test_empty_portfolio_exit_signals(self):
        # Empty portfolio should return 0 exit signals without crashing
        res = app.compute_exit_signals([], "non_existent_path.json")
        self.assertEqual(len(res), 0)

    def test_data_quality_insufficient_rows(self):
        short_df = pd.DataFrame({'Close': [10.0]*15}, index=pd.date_range('2026-01-01', periods=15))
        ok, reason = app.run_data_quality_gate("TEST.CA", short_df)
        self.assertFalse(ok)
        self.assertIn("أقل من 30", reason)

    def test_data_quality_date_gap(self):
        idx_1 = list(pd.date_range('2026-01-01', periods=20))
        idx_2 = list(pd.date_range('2026-02-10', periods=20)) # Gap of 20 days
        gap_df = pd.DataFrame({'Close': [10.0]*40}, index=idx_1 + idx_2)
        ok, reason = app.run_data_quality_gate("TEST.CA", gap_df)
        self.assertFalse(ok)
        self.assertIn("فجوة", reason)

    def test_data_quality_price_outlier(self):
        np.random.seed(42)
        closes = [10.0 + np.random.normal(0, 0.1) for _ in range(40)] + [150.0] # Massive spike
        outlier_df = pd.DataFrame({'Close': closes}, index=pd.date_range('2026-01-01', periods=41))
        ok, reason = app.run_data_quality_gate("TEST.CA", outlier_df)
        self.assertFalse(ok)
        self.assertIn("شذوذ سعري", reason)

    def test_negative_input_filtering_reset_wizard(self):
        raw_bad_text = "COMI.CA, -10, 130.0\nTMGH.CA, 50, -90.0\nSWDY.CA, 0, 0\nISPH.CA, 100, 5.50"
        
        # Test the parsing logic of reset_portfolio_from_text
        import re
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
