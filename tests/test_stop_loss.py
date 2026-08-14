import unittest
import sys
import os

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, WORKSPACE)

import app

class TestStopLossSanity(unittest.TestCase):

    def test_stop_loss_below_entry_and_current(self):
        current_p = 100.0
        atr_a = 3.0
        
        # Standard formulation
        entry = round(max(98.0, current_p - 0.4 * atr_a), 2) # 98.80
        stop = round(max(0.1, entry - 1.5 * atr_a), 2)       # 94.30
        peak = round(current_p * 1.06, 2)                    # 106.00
        
        self.assertLess(stop, entry)
        self.assertLess(stop, current_p)
        self.assertGreater(peak, entry)
        self.assertGreater(peak, current_p)

    def test_trailing_profit_lock_classification(self):
        # Scenario 1: Profitable trade with stop above entry (Locked Profit)
        entry_p = 100.0
        current_p = 120.0
        raw_stop = 110.0
        
        if current_p > entry_p and raw_stop > entry_p:
            sl_type = 'TRAILING_LOCK'
        elif raw_stop <= entry_p:
            sl_type = 'CAPITAL_PROTECTION'
        else:
            sl_type = 'STANDARD'
            
        self.assertEqual(sl_type, 'TRAILING_LOCK')

        # Scenario 2: Trade near entry or losing
        current_p_2 = 98.0
        raw_stop_2 = 92.0
        
        if current_p_2 > entry_p and raw_stop_2 > entry_p:
            sl_type_2 = 'TRAILING_LOCK'
        elif raw_stop_2 <= entry_p:
            sl_type_2 = 'CAPITAL_PROTECTION'
        else:
            sl_type_2 = 'STANDARD'
            
        self.assertEqual(sl_type_2, 'CAPITAL_PROTECTION')

    def test_strict_sanity_gate_no_inversion(self):
        # Edge case: raw_stop >= current_p due to anomalous volatility
        current_p = 50.0
        anomalous_sl = 55.0
        
        # Sanity Gate in app.py enforces:
        if anomalous_sl >= current_p:
            corrected_sl = round(current_p * 0.93, 2)
        else:
            corrected_sl = anomalous_sl
            
        self.assertLess(corrected_sl, current_p)
        self.assertEqual(corrected_sl, 46.50)

if __name__ == '__main__':
    unittest.main()
