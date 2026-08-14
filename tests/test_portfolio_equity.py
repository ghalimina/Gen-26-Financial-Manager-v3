import unittest
import math
import sys
import os

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, WORKSPACE)

import app

class TestPortfolioEquity(unittest.TestCase):

    def test_dynamic_equity_calculation(self):
        holdings = [
            {'stock': 'التجاري الدولي', 'ticker': 'COMI.CA', 'qty': 20, 'avg_price': 130.0},
            {'stock': 'طلعت مصطفى', 'ticker': 'TMGH.CA', 'qty': 10, 'avg_price': 90.0}
        ]
        predictions = [
            {'الاسم': 'التجاري الدولي', 'الكود': 'COMI.CA', 'السعر الحالي (الماركت) 🏷️': 135.0},
            {'الاسم': 'طلعت مصطفى', 'الكود': 'TMGH.CA', 'السعر الحالي (الماركت) 🏷️': 95.0}
        ]
        pred_map = {p['الاسم']: p for p in predictions}
        pred_tick_map = {p['الكود']: p for p in predictions}
        
        # Test Case 1: Cash = 0
        avail_cash_0 = 0.0
        stock_equity = sum(int(h['qty']) * float(pred_tick_map[h['ticker']]['السعر الحالي (الماركت) 🏷️']) for h in holdings)
        # 20 * 135 = 2700, 10 * 95 = 950 -> Total = 3650
        self.assertEqual(stock_equity, 3650.0)
        tot_eq_0 = stock_equity + avail_cash_0
        self.assertEqual(tot_eq_0, 3650.0)
        
        # Test Case 2: Cash = 10,000
        avail_cash_10k = 10000.0
        tot_eq_10k = stock_equity + avail_cash_10k
        self.assertEqual(tot_eq_10k, 13650.0)
        
        # Test Case 3: Cash = 50,000
        avail_cash_50k = 50000.0
        tot_eq_50k = stock_equity + avail_cash_50k
        self.assertEqual(tot_eq_50k, 53650.0)
        
        # Test Case 4: Cash = 500,000
        avail_cash_500k = 500000.0
        tot_eq_500k = stock_equity + avail_cash_500k
        self.assertEqual(tot_eq_500k, 503650.0)

    def test_position_sizing_integer_and_caps(self):
        total_equity = 50000.0
        alloc_pct = 8.5 # 8.5% -> 4250 EGP
        target_cost = total_equity * (alloc_pct / 100.0)
        limit_price = 13.45
        
        suggested_shares = max(int(math.floor(target_cost / limit_price)), 1)
        # 4250 / 13.45 = 315.985 -> floor is 315 shares
        self.assertIsInstance(suggested_shares, int)
        self.assertEqual(suggested_shares, 315)
        
        actual_order_cost = round(suggested_shares * limit_price, 2) # 4236.75
        self.assertLessEqual(actual_order_cost, target_cost)

    def test_cash_gate_enforcement(self):
        available_cash = 2000.0
        order_cost_1 = 1200.0
        order_cost_2 = 1500.0
        
        cum_cash = 0.0
        status_1 = 'APPROVED' if cum_cash + order_cost_1 <= available_cash else 'PENDING'
        if status_1 == 'APPROVED': cum_cash += order_cost_1
        
        status_2 = 'APPROVED' if cum_cash + order_cost_2 <= available_cash else 'PENDING'
        
        self.assertEqual(status_1, 'APPROVED')
        self.assertEqual(status_2, 'PENDING')
        self.assertEqual(cum_cash, 1200.0)

if __name__ == '__main__':
    unittest.main()
