#!/usr/bin/env python3
# =============================================================================
# tests/test_nlp_sentiment_engine.py — Master Unit Tests for Arabic NLP Sentiment
# Validates:
# 1. Arabic financial headline polarity scoring (Positive > 0.5, Negative < -0.5, Neutral ~ 0.0).
# 2. Bounded sentiment score guarantees [-1.0, +1.0].
# 3. News ingestion pipeline & entity recognition with Mock fallback.
# 4. Feature registry & Meta-Labeling XGBoost feature integration.
# 5. REST API endpoint /api/sentiment/<ticker> and UI element integrity.
# =============================================================================

import os
import sys
import unittest
import json

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.nlp_sentiment_engine import ArabicFinancialSentimentAnalyzer, NLPSentimentEngine, evaluate_ticker_sentiment
from core.news_ingestion_engine import NewsIngestionEngine, MockNewsGenerator
from core.meta_labeling_engine import MetaLabelingEngine
from dashboard.app import app


class TestNLPSentimentEngine(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_01_arabic_financial_polarity_positive_scoring(self):
        """Verify positive Arabic financial headlines score > 0.50."""
        positive_headlines = [
            "البنك التجاري الدولي يعلن عن قفزة في الأرباح بنسبة 48% وتوزيعات نقدية استثنائية للمساهمين",
            "السويدي إليكتريك تحقق مبيعات غير مسبوقة وتوقع عقود كبرى بالخليج وإفريقيا",
            "مجموعة طلعت مصطفى تسجل نمو صافي الأرباح بنسبة 60% مع فائض تدفقات نقدية قوية"
        ]
        for h in positive_headlines:
            res = ArabicFinancialSentimentAnalyzer.score_headline(h)
            self.assertGreaterEqual(res["sentiment_score"], 0.50, f"Failed for headline: {h}")
            self.assertIn("إيجابي", res["sentiment_label_ar"])
            self.assertLessEqual(res["sentiment_score"], 1.0)

    def test_02_arabic_financial_polarity_negative_scoring(self):
        """Verify negative Arabic financial headlines score < -0.50."""
        negative_headlines = [
            "الشركة تعلن تراجع الأرباح بنسبة 45% وتكبد خسائر صافية بسبب فروق العملة",
            "تراجع الإيرادات وانخفاض المبيعات يضغطان بشدة على هوامش ربحية الشركة",
            "تحقيق خسائر حادة نتيجة غرامات ودعوى قضائية على الشركة"
        ]
        for h in negative_headlines:
            res = ArabicFinancialSentimentAnalyzer.score_headline(h)
            self.assertLessEqual(res["sentiment_score"], -0.50, f"Failed for headline: {h}")
            self.assertIn("سلبي", res["sentiment_label_ar"])
            self.assertGreaterEqual(res["sentiment_score"], -1.0)

    def test_03_arabic_financial_polarity_neutral_scoring(self):
        """Verify neutral Arabic financial headlines score in bounded range [-0.25, +0.35]."""
        neutral_headlines = [
            "انعقاد الجمعية العامة العادية لمناقشة تقرير مجلس الإدارة واعتماد القوائم",
            "الشركة تنشر تقرير الإفصاح الدوري للبورصة المصرية عن هيكل المساهمين"
        ]
        for h in neutral_headlines:
            res = ArabicFinancialSentimentAnalyzer.score_headline(h)
            self.assertGreaterEqual(res["sentiment_score"], -0.25)
            self.assertLessEqual(res["sentiment_score"], 0.35)

    def test_04_evaluate_ticker_sentiment_structure(self):
        """Verify evaluate_ticker_sentiment returns complete bounded telemetry."""
        res = evaluate_ticker_sentiment("COMI.CA")
        self.assertEqual(res["ticker"], "COMI.CA")
        self.assertIn("sentiment_score", res)
        self.assertGreaterEqual(res["sentiment_score"], -1.0)
        self.assertLessEqual(res["sentiment_score"], 1.0)
        self.assertIn("most_impactful_headline_ar", res)
        self.assertIsInstance(res["recent_headlines"], list)

    def test_05_news_ingestion_and_mock_fallback(self):
        """Verify NewsIngestionEngine behavior in mock test vs production lockdown mode."""
        # 1. Test explicit mock mode for test harnesses
        mock_news = NewsIngestionEngine.get_news_for_ticker("SWDY.CA", max_items=3, allow_mock=True)
        self.assertGreater(len(mock_news), 0)
        self.assertEqual(mock_news[0]["ticker"], "SWDY.CA")
        self.assertIn("headline_ar", mock_news[0])

        # 2. Test strict production lockdown when offline
        prod_news = NewsIngestionEngine.get_news_for_ticker("UNKNOWN_TICKER_XYZ.CA", max_items=3, allow_mock=False)
        self.assertIsInstance(prod_news, list)

    def test_06_meta_labeling_finbert_feature_integration(self):
        """Verify MetaLabelingEngine dynamically ingests finbert_sentiment_score."""
        vec, feat_dict = MetaLabelingEngine.extract_meta_feature_vector("COMI.CA")
        self.assertIn("finbert_sentiment_score", feat_dict)
        self.assertGreaterEqual(feat_dict["finbert_sentiment_score"], -1.0)
        self.assertLessEqual(feat_dict["finbert_sentiment_score"], 1.0)

    def test_07_api_endpoint_sentiment(self):
        """Verify GET /api/sentiment/<ticker> returns HTTP 200 OK."""
        r = self.app.get("/api/sentiment/COMI.CA")
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertEqual(data["ticker"], "COMI.CA")
        self.assertIn("sentiment_score", data)
        self.assertIn("most_impactful_headline_ar", data)

    def test_08_ui_sentiment_elements_exist(self):
        """Verify UI index.html contains News Sentiment Radar card elements."""
        html_path = os.path.join(WORKSPACE, "dashboard", "index.html")
        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()

        self.assertIn('id="detail-sentiment-badge"', html)
        self.assertIn('id="detail-sentiment-score-val"', html)
        self.assertIn('id="detail-sentiment-headline"', html)


if __name__ == "__main__":
    unittest.main()
