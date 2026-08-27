#!/usr/bin/env python3
# =============================================================================
# tests/test_fundamental_data_engine.py — Unit Tests for Fundamental Data Engine
# Validates:
# 1. Extraction of core metrics (P/E, P/B, EPS, Dividend Yield, Debt, Cash, FCF).
# 2. Financial health score calculation with Value Investing scoring.
# 3. Penalty enforcement on negative EPS, high debt, and excessive P/E.
# 4. Neutral fallback behavior (50.0 / "بيانات غير متوفرة") on missing data.
# 5. Public get_ticker_analysis endpoint resilience on valid and invalid tickers.
# =============================================================================

import os
import sys
import unittest

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.fundamental_data_engine import FundamentalDataEngine


class TestFundamentalDataEngine(unittest.TestCase):

    def test_01_fetch_fundamentals_schema(self):
        """Verify fetch_fundamentals returns all required financial keys."""
        data = FundamentalDataEngine.fetch_fundamentals("COMI.CA")
        self.assertIsInstance(data, dict)
        self.assertIn("trailingPE", data)
        self.assertIn("forwardPE", data)
        self.assertIn("trailingEps", data)
        self.assertIn("dividendYield", data)
        self.assertIn("priceToBook", data)
        self.assertIn("totalCash", data)
        self.assertIn("totalDebt", data)
        self.assertIn("freeCashflow", data)
        self.assertEqual(data["ticker"], "COMI.CA")

    def test_02_calculate_health_score_excellent_value(self):
        """Verify attractive value stock with low P/E, reasonable P/B, and dividend gets high health score."""
        mock_fundamentals = {
            "trailingPE": 6.5,
            "forwardPE": 5.8,
            "priceToBook": 1.2,
            "trailingEps": 12.5,
            "dividendYield": 0.07,  # 7% dividend yield
            "totalCash": 500000000.0,
            "totalDebt": 200000000.0,  # Net cash positive
            "freeCashflow": 150000000.0,
            "returnOnEquity": 0.22  # 22% ROE
        }
        res = FundamentalDataEngine.calculate_health_score(mock_fundamentals)
        self.assertGreaterEqual(res["health_score"], 80.0)
        self.assertIn("ممتاز", res["financial_health_label"])
        self.assertEqual(res["valuation_tier"], "UNDERVALUED")
        self.assertEqual(res["dividend_status"], "DIVIDEND_PAYING")
        self.assertEqual(res["solvency_status"], "NET_CASH")

    def test_03_calculate_health_score_poor_or_distressed(self):
        """Verify unprofitable, overleveraged company gets penalized with low health score."""
        mock_distressed = {
            "trailingPE": -5.0,  # Negative P/E (losses)
            "priceToBook": 6.5,  # Expensive book multiple
            "trailingEps": -2.40,  # Negative earnings
            "dividendYield": 0.0,
            "totalCash": 10000000.0,
            "totalDebt": 150000000.0,  # 15x debt vs cash
            "freeCashflow": -50000000.0  # Burning cash
        }
        res = FundamentalDataEngine.calculate_health_score(mock_distressed)
        self.assertLessEqual(res["health_score"], 40.0)
        self.assertTrue("سيء" in res["financial_health_label"] or "ضعيف" in res["financial_health_label"])
        self.assertEqual(res["valuation_tier"], "UNPROFITABLE")
        self.assertEqual(res["solvency_status"], "HIGH_LEVERAGE")

    def test_04_calculate_health_score_empty_missing_data(self):
        """Verify empty fundamental data returns neutral 50.0 score and 'بيانات غير متوفرة'."""
        empty_data = {
            "trailingPE": None,
            "forwardPE": None,
            "priceToBook": None,
            "trailingEps": None,
            "dividendYield": None,
            "totalCash": None,
            "totalDebt": None,
            "freeCashflow": None
        }
        res = FundamentalDataEngine.calculate_health_score(empty_data)
        self.assertEqual(res["health_score"], 50.0)
        self.assertEqual(res["financial_health_label"], "بيانات غير متوفرة")

    def test_05_get_ticker_analysis_success(self):
        """Verify get_ticker_analysis returns structured and robust payload."""
        analysis = FundamentalDataEngine.get_ticker_analysis("SWDY.CA")
        self.assertIn(analysis["status"], ["SUCCESS", "DATA_UNAVAILABLE_FALLBACK"])
        self.assertEqual(analysis["ticker"], "SWDY.CA")
        self.assertIn("health_score", analysis)
        self.assertIn("financial_health_label", analysis)
        self.assertIn("metrics", analysis)
        self.assertIsInstance(analysis["health_score"], float)

    def test_06_get_ticker_analysis_invalid_fallback(self):
        """Verify non-existent ticker falls back gracefully without raising uncaught exceptions."""
        analysis = FundamentalDataEngine.get_ticker_analysis("NON_EXISTENT_TICKER_999.CA")
        self.assertIn("health_score", analysis)
        self.assertAlmostEqual(analysis["health_score"], 50.0, places=0)
        self.assertIn(analysis["financial_health_label"], ["بيانات غير متوفرة", "مقبول (تقييم معتدل ومتوازن)"])


if __name__ == "__main__":
    unittest.main()
