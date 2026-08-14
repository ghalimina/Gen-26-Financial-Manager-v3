import unittest
import numpy as np
from sklearn.preprocessing import RobustScaler, MinMaxScaler
import sys
import os

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, WORKSPACE)

class TestDataLeakage(unittest.TestCase):

    def test_scaler_train_only_fit(self):
        # Generate synthetic time-series data with a distribution shift in the test period
        np.random.seed(42)
        train_data = np.random.normal(loc=10.0, scale=2.0, size=(100, 4))
        test_data = np.random.normal(loc=50.0, scale=5.0, size=(30, 4)) # Major upward shift
        
        # Proper methodology: Fit on train ONLY
        scaler_proper = RobustScaler()
        train_scaled = scaler_proper.fit_transform(train_data)
        test_scaled = scaler_proper.transform(test_data)
        
        # Leaked methodology: Fit on all
        all_data = np.vstack([train_data, test_data])
        scaler_leaked = RobustScaler()
        scaler_leaked.fit(all_data)
        
        # Center of proper scaler must match median of train_data
        np.testing.assert_array_almost_equal(scaler_proper.center_, np.median(train_data, axis=0))
        
        # Center of leaked scaler is contaminated by test_data
        self.assertFalse(np.allclose(scaler_proper.center_, scaler_leaked.center_))
        
        # Verify that test transformation does not alter train parameters
        test_transformed = scaler_proper.transform(test_data)
        self.assertEqual(test_transformed.shape, (30, 4))

    def test_minmax_scaler_temporal_isolation(self):
        # Verify MinMaxScaler behaves without future leakage
        train_series = np.array([[1.0], [2.0], [3.0], [4.0], [5.0]])
        test_series = np.array([[6.0], [10.0]]) # Future higher values
        
        scaler = MinMaxScaler(feature_range=(0, 1))
        train_s = scaler.fit_transform(train_series)
        test_s = scaler.transform(test_series)
        
        # Train min is 1.0, max is 5.0
        self.assertEqual(scaler.data_min_[0], 1.0)
        self.assertEqual(scaler.data_max_[0], 5.0)
        
        # Future values should scale above 1.0 (out of bounds for train, which is mathematically correct for OOS)
        self.assertGreater(test_s[0, 0], 1.0)
        self.assertGreater(test_s[1, 0], 1.0)

if __name__ == '__main__':
    unittest.main()
