#!/usr/bin/env python3
# =============================================================================
# tests/test_corporate_actions.py — Tests for Corporate Actions & Latency/TTL Protocol
# =============================================================================

import os
import sys
import unittest
import datetime
import pandas as pd
import numpy as np

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.corporate_actions import CorporateActionsAdjuster
from core.multi_horizon_engine import MultiHorizonEngine
from core.notification_gateway import NotificationEngine


class TestCorporateActionsAndTTLProtocol(unittest.TestCase):
    """
    Validates:
    1. Corporate Actions Adjuster backward adjustment for splits and dividends.
    2. ATR stability across stock split events without artificial volatility spikes.
    3. Signal Time-To-Live (TTL = 30 minutes) and expiration evaluation.
    4. Hard price bounds (+0.5% max entry price).
    5. Arabic Telegram Notification templates with TTL and entry guardrails.
    """

    def test_01_stock_split_backward_adjustment_and_atr_stability(self):
        """
        Verify that a 2-for-1 stock split is backward adjusted, preventing ATR spikes.
        """
        # Create 40 days of synthetic trading data
        # Day 1-20: Price ~ 100.0 EGP (+/- 1 EGP noise)
        # Day 21 (Split date): 2-for-1 Split -> Price becomes 50.0 EGP (+/- 1 EGP noise)
        dates = pd.date_range(start="2026-06-01", periods=40, freq="B")
        
        np.random.seed(42)
        raw_prices = []
        for i in range(40):
            base_p = 100.0 if i < 20 else 50.0
            noise = np.random.uniform(-0.5, 0.5)
            p = base_p + noise
            raw_prices.append({
                "Open": p - 0.2,
                "High": p + 0.5,
                "Low": p - 0.5,
                "Close": p,
                "Volume": 100000 if i < 20 else 200000
            })

        df_raw = pd.DataFrame(raw_prices, index=dates)

        # Unadjusted ATR calculation (shows artificial crash spike on Day 21)
        tr_raw = np.maximum(
            df_raw["High"] - df_raw["Low"],
            np.maximum(
                abs(df_raw["High"] - df_raw["Close"].shift(1)),
                abs(df_raw["Low"] - df_raw["Close"].shift(1))
            )
        )
        raw_atr_at_split = tr_raw.iloc[20]
        # Raw jump is around ~50 EGP due to split gap
        self.assertGreater(raw_atr_at_split, 40.0, "Raw unadjusted data should show massive false gap")

        # Create actions DataFrame: 2-for-1 split on Day 21 (dates[20])
        actions_df = pd.DataFrame({
            "Stock Splits": [2.0],
            "Dividends": [0.0]
        }, index=[dates[20]])

        # Apply CorporateActionsAdjuster
        df_adj = CorporateActionsAdjuster.adjust_ohlcv_dataframe(df_raw, actions_df=actions_df)

        # Adjusted ATR calculation
        tr_adj = np.maximum(
            df_adj["High"] - df_adj["Low"],
            np.maximum(
                abs(df_adj["High"] - df_adj["Close"].shift(1)),
                abs(df_adj["Low"] - df_adj["Close"].shift(1))
            )
        )
        adj_atr_at_split = tr_adj.iloc[20]

        # Prior prices (Day 1-20) should now be ~50.0 EGP instead of 100.0 EGP
        self.assertAlmostEqual(df_adj["Close"].iloc[0], 50.0, delta=1.0)
        self.assertAlmostEqual(df_adj["Close"].iloc[19], 50.0, delta=1.0)
        self.assertAlmostEqual(df_adj["Close"].iloc[20], 50.0, delta=1.0)

        # ATR at split date should be smooth (< 2.0 EGP, matching normal volatility)
        self.assertLess(adj_atr_at_split, 2.5, "Adjusted ATR must remain smooth without split spike")

    def test_02_cash_dividend_backward_adjustment(self):
        """
        Verify that a cash dividend adjusts prior historical bars backward by (1 - D / P_prior).
        """
        dates = pd.date_range(start="2026-07-01", periods=10, freq="B")
        prices = [100.0] * 10
        df = pd.DataFrame({
            "Open": prices,
            "High": prices,
            "Low": prices,
            "Close": prices,
            "Volume": [50000] * 10
        }, index=dates)

        # 5.00 EGP Dividend on Day 6 (dates[5]) -> Prior close is 100.0 -> Factor = 1.0 - 5/100 = 0.95
        actions_df = pd.DataFrame({
            "Stock Splits": [0.0],
            "Dividends": [5.0]
        }, index=[dates[5]])

        adj_df = CorporateActionsAdjuster.adjust_ohlcv_dataframe(df, actions_df=actions_df)

        # Prior bars (0-4) must be adjusted to 95.0 EGP
        for i in range(5):
            self.assertAlmostEqual(adj_df["Close"].iloc[i], 95.0, places=2)

        # Post-dividend bars (5-9) must remain at 100.0 EGP
        for i in range(5, 10):
            self.assertAlmostEqual(adj_df["Close"].iloc[i], 100.0, places=2)

    def test_03_signal_ttl_and_expiration_logic(self):
        """
        Verify Signal Time-To-Live (30 min) and is_signal_expired helper method.
        """
        analysis = MultiHorizonEngine.get_stock_multi_horizon_analysis("COMI.CA")
        self.assertIsNotNone(analysis)
        self.assertIn("valid_until", analysis)
        self.assertIn("signal_timestamp", analysis)
        self.assertEqual(analysis.get("ttl_minutes"), 30)
        self.assertIn("max_entry_price", analysis)

        # Test fresh signal (now) -> Should NOT be expired
        self.assertFalse(MultiHorizonEngine.is_signal_expired(analysis))

        # Test simulated past signal (> 30 min old) -> Should be expired
        past_time = datetime.datetime.now() + datetime.timedelta(minutes=35)
        self.assertTrue(MultiHorizonEngine.is_signal_expired(analysis, current_time=past_time))

        # Test within TTL (e.g. 15 min later) -> Should NOT be expired
        intermediate_time = datetime.datetime.now() + datetime.timedelta(minutes=15)
        self.assertFalse(MultiHorizonEngine.is_signal_expired(analysis, current_time=intermediate_time))

    def test_04_max_entry_price_bound_enforcement(self):
        """
        Verify that max_entry_price is strictly bounded at +0.5% above trigger price.
        """
        analysis = MultiHorizonEngine.get_stock_multi_horizon_analysis("COMI.CA")
        curr_price = analysis["current_price"]
        max_entry = analysis["max_entry_price"]

        expected_max = round(curr_price * 1.005, 2)
        self.assertAlmostEqual(max_entry, expected_max, delta=0.05)
        self.assertGreater(max_entry, curr_price)
        self.assertLessEqual((max_entry - curr_price) / curr_price, 0.0055)

    def test_05_notification_engine_buy_signal_alert_template(self):
        """
        Verify Arabic Telegram buy signal alert template includes TTL and Max Entry guardrails.
        """
        sample_signal = {
            "ticker": "COMI.CA",
            "company_name": "البنك التجاري الدولي",
            "current_price": 140.00,
            "entry_low": 138.00,
            "max_entry_price": 140.70,
            "stop_loss": 130.20,
            "target_price": 148.50,
            "confidence_score": 89.5,
            "valid_until": "14:30:00"
        }

        res = NotificationEngine.send_buy_signal_alert(sample_signal)
        self.assertIn("status", res)
        self.assertTrue(res.get("delivered", False))
        
        log_rec = res.get("log_record", {})
        msg_text = log_rec.get("message", "")

        # Strict assert on required Arabic regulatory & risk guardrails
        self.assertIn("صلاحية الإشارة", msg_text)
        self.assertIn("30 دقيقة", msg_text)
        self.assertIn("النطاق الآمن للدخول", msg_text)
        self.assertIn("140.70", msg_text)
        self.assertIn("يُمنع الشراء إذا تجاوز السعر", msg_text)


if __name__ == "__main__":
    unittest.main()
