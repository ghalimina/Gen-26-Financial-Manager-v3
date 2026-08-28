#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# tests/test_market_intelligence_scraper.py — Unit Tests for Market Intelligence Scraper
# =============================================================================

import unittest
from unittest.mock import patch, MagicMock
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.market_intelligence_scraper import MarketIntelligenceScraper


class TestMarketIntelligenceScraper(unittest.TestCase):

    def setUp(self):
        MarketIntelligenceScraper._cache.clear()
        MarketIntelligenceScraper._cache_timestamps.clear()

    def test_01_session_and_headers_configuration(self):
        """Verify HTTP session configures rotating User-Agents and headers."""
        session = MarketIntelligenceScraper.get_session()
        self.assertIsNotNone(session)
        self.assertIn("User-Agent", session.headers)
        self.assertIn("Mozilla", session.headers["User-Agent"])

    @patch("requests.Session.get")
    def test_02_scrape_mubasher_news_parsing(self, mock_get):
        """Verify BeautifulSoup correctly parses Mubasher HTML news feed."""
        html_content = """
        <html>
            <body>
                <div class="news-item">
                    <h2><a href="/news/12345/egypt-cib-profits-q2">البنك التجاري الدولي يحقق أرباحاً قياسية في الربع الثاني</a></h2>
                </div>
                <div class="news-item">
                    <h2><a href="/news/12346/elsewedy-new-contracts">السويدي إليكتريك تفوز بعقد ربط كهربائي جديد</a></h2>
                </div>
            </body>
        </html>
        """
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = html_content
        mock_get.return_value = mock_resp

        articles = MarketIntelligenceScraper.scrape_mubasher_news(limit=5)
        self.assertEqual(len(articles), 2)
        self.assertIn("البنك التجاري الدولي", articles[0]["title"])
        self.assertIn("السويدي إليكتريك", articles[1]["title"])
        self.assertEqual(articles[0]["source"], "Mubasher EGX")

    @patch("requests.Session.get")
    def test_03_scrape_macro_indicators_parsing(self, mock_get):
        """Verify macro indicators parser extracts interest rate or uses exact verified real numbers."""
        html_content = """
        <html>
            <body>
                <p>The Central Bank of Egypt overnight deposit rate is 27.25 % and lending rate 28.25 %.</p>
            </body>
        </html>
        """
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = html_content
        mock_get.return_value = mock_resp

        res = MarketIntelligenceScraper.scrape_macro_indicators()
        self.assertEqual(res["interest_rate_pct"], 27.25)
        self.assertEqual(res["inflation_rate_pct"], 14.90)
        self.assertTrue("Central Bank of Egypt" in res["source"] or "CBE" in res["source"])

    @patch("core.market_intelligence_scraper.MarketIntelligenceScraper.scrape_mubasher_news")
    def test_04_scrape_market_catalysts_categorization(self, mock_news):
        """Verify catalyst scraper flags M&A, earnings, and dividends correctly."""
        mock_news.return_value = [
            {"title": "عرض شراء إجباري للاستحواذ على حصة 30% في شركة مصرية", "source": "Mubasher", "url": "/m1", "scraped_at": "2026-08-27"},
            {"title": "الجمعية العمومية تقر توزيع كوبون نقدي بقيمة 2.5 جنيه", "source": "Mubasher", "url": "/m2", "scraped_at": "2026-08-27"},
            {"title": "قفزة في الأرباح الصافية بنسبة 45% لشركة أبو قير للأسمدة", "source": "Mubasher", "url": "/m3", "scraped_at": "2026-08-27"}
        ]

        catalysts = MarketIntelligenceScraper.scrape_market_catalysts(limit=10)
        self.assertEqual(len(catalysts), 3)
        categories = [c["category"] for c in catalysts]
        self.assertIn("MERGERS_ACQUISITIONS", categories)
        self.assertIn("DIVIDENDS", categories)
        self.assertIn("EARNINGS_GROWTH", categories)

    def test_05_fetch_global_commodities_schema(self):
        """Verify commodities fetcher returns structured dictionary for sugar, gas, brent, gold, copper."""
        commodities = MarketIntelligenceScraper.fetch_global_commodities()
        self.assertIsInstance(commodities, dict)
        self.assertIn("sugar", commodities)
        self.assertIn("natural_gas", commodities)
        self.assertIn("brent_crude", commodities)
        self.assertIn("gold", commodities)
        self.assertIn("copper", commodities)
        for k, v in commodities.items():
            self.assertIn("symbol", v)
            self.assertIn("current_price", v)
            self.assertIn("change_1m_pct", v)
            self.assertGreater(v["current_price"], 0.0)

    @patch("core.market_intelligence_scraper.MarketIntelligenceScraper.scrape_mubasher_news")
    @patch("core.market_intelligence_scraper.MarketIntelligenceScraper.scrape_macro_indicators")
    def test_06_get_live_market_pulse_aggregation(self, mock_macro, mock_news):
        """Verify live market pulse compiles full multi-dimensional payload."""
        mock_macro.return_value = {"interest_rate_pct": 27.25, "inflation_rate_pct": 26.50, "source": "CBE"}
        mock_news.return_value = [{"title": "EGX30 صعود جماعي لمؤشرات البورصة", "source": "Mubasher"}]

        pulse = MarketIntelligenceScraper.get_live_market_pulse()
        self.assertEqual(pulse["status"], "LIVE_INGESTION")
        self.assertIn("macro_environment", pulse)
        self.assertIn("global_commodities", pulse)
        self.assertIn("breaking_news", pulse)
        self.assertIn("corporate_catalysts", pulse)
        self.assertIn("sources", pulse)


if __name__ == "__main__":
    unittest.main()
