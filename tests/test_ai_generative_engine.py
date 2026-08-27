#!/usr/bin/env python3
# =============================================================================
# tests/test_ai_generative_engine.py — Unit Tests for AIGenerativeEngine
# Validates:
# 1. Morning briefing structure and Arabic markdown generation.
# 2. Market regime dynamic contextualization in reports.
# 3. Interactive Quant Chatbot stock analysis queries.
# 4. Interactive Quant Chatbot recommendation queries.
# 5. Interactive Quant Chatbot portfolio sizing queries.
# 6. Edge-case resilience with empty queries, missing keys, and offline mode.
# =============================================================================

import os
import sys
import unittest

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.ai_generative_engine import AIGenerativeEngine


class TestAIGenerativeEngine(unittest.TestCase):

    def setUp(self):
        self.sample_stocks = [
            {"ticker": "COMI.CA", "price": 140.50, "composite_score": 93.0},
            {"ticker": "SWDY.CA", "price": 128.00, "composite_score": 88.5},
            {"ticker": "TMGH.CA", "price": 62.25, "composite_score": 86.0},
            {"ticker": "ORAS.CA", "price": 310.00, "composite_score": 84.0}
        ]
        self.context = {
            "market_regime": "BULLISH_TREND",
            "top_stocks": self.sample_stocks,
            "prices": {
                "COMI.CA": 140.50,
                "SWDY.CA": 128.00,
                "TMGH.CA": 62.25,
                "ORAS.CA": 310.00
            },
            "total_capital_egp": 250000.0
        }

    def test_01_morning_briefing_structure(self):
        """Verify generate_morning_briefing returns complete and valid payload."""
        briefing = AIGenerativeEngine.generate_morning_briefing(self.sample_stocks, market_regime="BULLISH_TREND")

        self.assertEqual(briefing["status"], "SUCCESS")
        self.assertIn("headline", briefing)
        self.assertIn("summary_markdown", briefing)
        self.assertIn("key_recommendations", briefing)
        self.assertIn("source", briefing)
        self.assertGreater(len(briefing["summary_markdown"]), 100)
        self.assertIn("COMI.CA", briefing["summary_markdown"])

    def test_02_morning_briefing_regime_customization(self):
        """Verify briefing reflects the provided market regime."""
        briefing = AIGenerativeEngine.generate_morning_briefing(self.sample_stocks, market_regime="HIGH_VOLATILITY")
        self.assertEqual(briefing["market_regime"], "HIGH_VOLATILITY")
        self.assertIn("تقلبات سعرية حادة", briefing["market_regime_ar"])
        self.assertIn("تقلبات", briefing["summary_markdown"])

    def test_03_chat_ticker_lookup(self):
        """Verify chatbot identifies specific ticker in Arabic query."""
        response = AIGenerativeEngine.chat_with_quant("ما هو وضع سهم طلعت مصطفى وسعر الشراء؟", self.context)
        self.assertIsInstance(response, str)
        self.assertIn("طلعت مصطفى", response)
        self.assertIn("62.25", response)
        self.assertIn("وقف الخسارة", response)

    def test_04_chat_recommendations_query(self):
        """Verify chatbot answers general recommendation queries."""
        response = AIGenerativeEngine.chat_with_quant("ما هي أفضل الأسهم للشراء الآن؟", self.context)
        self.assertIsInstance(response, str)
        self.assertIn("أفضل الفرص الاستثمارية", response)
        self.assertTrue("COMI.CA" in response or "البنك التجاري الدولي" in response)

    def test_05_chat_capital_allocation_query(self):
        """Verify chatbot answers portfolio allocation questions."""
        response = AIGenerativeEngine.chat_with_quant("كيف أوزع محفظتي بمبلغ 200 ألف جنيه؟", self.context)
        self.assertIsInstance(response, str)
        self.assertIn("خطة التوزيع الذكي", response)
        self.assertIn("30%", response)

    def test_06_edge_cases_and_empty_inputs(self):
        """Verify engine gracefully handles empty strings, None contexts, and missing data."""
        empty_chat = AIGenerativeEngine.chat_with_quant("", None)
        self.assertIn("مرحباً بك", empty_chat)

        empty_briefing = AIGenerativeEngine.generate_morning_briefing([], market_regime="")
        self.assertEqual(empty_briefing["status"], "SUCCESS")
        self.assertIn("التقرير الصباحي", empty_briefing["summary_markdown"])


if __name__ == "__main__":
    unittest.main()
