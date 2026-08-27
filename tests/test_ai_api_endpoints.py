#!/usr/bin/env python3
# =============================================================================
# tests/test_ai_api_endpoints.py — Unit Tests for AI Flask REST API Endpoints
# Validates:
# 1. POST /api/chat with valid queries and dynamic system context.
# 2. POST /api/chat with empty query (400 Bad Request error handling).
# 3. GET /api/morning_briefing with default and custom regime parameters.
# 4. GET /api/fundamentals/<ticker> for EGX stocks.
# 5. GET /api/fundamentals/<invalid_ticker> fallback response.
# =============================================================================

import os
import sys
import json
import unittest

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from dashboard.app import app


class TestAIApiEndpoints(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_01_api_chat_success(self):
        """Verify POST /api/chat returns structured Arabic AI response."""
        payload = {
            "query": "ما هو وضع سهم طلعت مصطفى اليوم؟",
            "context": {
                "user_name": "مستثمر تجريبي"
            }
        }
        response = self.app.post(
            "/api/chat",
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "SUCCESS")
        self.assertIn("response", data)
        self.assertIn("query", data)
        self.assertIn("طلعت مصطفى", data["response"])

    def test_02_api_chat_empty_query_400(self):
        """Verify POST /api/chat returns 400 when query is empty."""
        payload = {"query": ""}
        response = self.app.post(
            "/api/chat",
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data["status"], "ERROR")
        self.assertIn("error", data)

    def test_03_api_morning_briefing_success(self):
        """Verify GET /api/morning_briefing returns complete Arabic morning report."""
        response = self.app.get("/api/morning_briefing?universe=core")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "SUCCESS")
        self.assertIn("headline", data)
        self.assertIn("summary_markdown", data)
        self.assertIn("key_recommendations", data)
        self.assertIn("market_regime", data)

    def test_04_api_morning_briefing_custom_regime(self):
        """Verify GET /api/morning_briefing respects custom regime parameter."""
        response = self.app.get("/api/morning_briefing?regime=HIGH_VOLATILITY")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["market_regime"], "HIGH_VOLATILITY")
        self.assertIn("تقلبات", data["market_regime_ar"])

    def test_05_api_fundamentals_ticker_success(self):
        """Verify GET /api/fundamentals/COMI.CA returns health score and valuation metrics."""
        response = self.app.get("/api/fundamentals/COMI.CA")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn(data["status"], ["SUCCESS", "DATA_UNAVAILABLE_FALLBACK"])
        self.assertEqual(data["ticker"], "COMI.CA")
        self.assertIn("health_score", data)
        self.assertIn("financial_health_label", data)
        self.assertIn("metrics", data)
        self.assertIsInstance(data["health_score"], float)

    def test_06_api_fundamentals_fallback_on_invalid_ticker(self):
        """Verify GET /api/fundamentals/<invalid> returns graceful 200 fallback without crashing."""
        response = self.app.get("/api/fundamentals/INVALID_SYMBOL_XYZ")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["ticker"], "INVALID_SYMBOL_XYZ.CA")
        self.assertIn("health_score", data)
        self.assertAlmostEqual(data["health_score"], 50.0, delta=5.0)


if __name__ == "__main__":
    unittest.main()
