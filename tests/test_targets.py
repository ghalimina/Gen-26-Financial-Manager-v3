import unittest
import pandas as pd
import numpy as np
import sys
import os

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, WORKSPACE)

class TestTargetsAndFeatures(unittest.TestCase):

    def test_feature_lag_integrity(self):
        # Verify that rolling features at index t do not incorporate prices from t+1
        prices = [10.0, 11.0, 12.0, 13.0, 14.0, 20.0, 100.0]
        dates = pd.date_range('2026-01-01', periods=len(prices))
        df = pd.DataFrame({'Close': prices}, index=dates)
        
        # 5-day SMA
        sma5 = df['Close'].rolling(5).mean()
        
        # At index 4 (value 14.0): SMA should be mean(10, 11, 12, 13, 14) = 12.0
        self.assertEqual(sma5.iloc[4], 12.0)
        
        # Future spike to 100.0 at index 6 must NOT affect SMA at index 4 or 5
        self.assertEqual(sma5.iloc[4], 12.0)
        self.assertEqual(sma5.iloc[5], 14.0)

    def test_forward_target_alignment_and_dropna(self):
        prices = [10.0, 10.5, 11.0, 11.5, 12.0]
        dates = pd.date_range('2026-01-01', periods=len(prices))
        df = pd.DataFrame({'Close': prices}, index=dates)
        
        # Target: 1-day ahead return
        df['Tgt_Ret_1D'] = (df['Close'].shift(-1) - df['Close']) / df['Close']
        
        # Target for index 0 is (10.5 - 10.0) / 10.0 = 0.05
        self.assertAlmostEqual(df['Tgt_Ret_1D'].iloc[0], 0.05)
        
        # Target for last bar (index 4) MUST be NaN
        self.assertTrue(pd.isna(df['Tgt_Ret_1D'].iloc[-1]))
        
        # Training dataset drops the tail row
        train_df = df.dropna(subset=['Tgt_Ret_1D'])
        self.assertEqual(len(train_df), len(prices) - 1)
        self.assertNotIn(dates[-1], train_df.index)

if __name__ == '__main__':
    unittest.main()
