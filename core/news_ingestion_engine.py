#!/usr/bin/env python3
# =============================================================================
# core/news_ingestion_engine.py — GEN-26 Live EGX Financial News & Disclosures Ingestion
# Ingestion architecture for Arabic financial news feeds & official disclosures:
# 1. RSS & Web Parser (EGX disclosures, Mubasher RSS, Enterprise Egypt).
# 2. Resilient MockNewsGenerator fallback for offline/sandbox testing.
# 3. Entity recognition & ticker mapping for EGX universe constituents.
# =============================================================================

import os
import sys
import json
import re
import datetime
import urllib.request
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

# Ticker Arabic Name / Keyword mapping for Entity Recognition
EGX_TICKER_ENTITY_MAP = {
    "COMI.CA": ["البنك التجاري الدولي", "سي آي بي", "CIB", "التجاري الدولي"],
    "SWDY.CA": ["السويدي إليكتريك", "السويدي اليكتريك", "السويدي للكابلات", "Elsewedy"],
    "TMGH.CA": ["طلعت مصطفى", "مجموعة طلعت مصطفى", "بنان", "SouthMED", "TMG"],
    "ORAS.CA": ["أوراسكوم للإنشاء", "اوراسكوم للانشاء", "Orascom Construction"],
    "ABUK.CA": ["أبو قير للأسمدة", "ابو قير للاسمدة", "أبوقير"],
    "ALCN.CA": ["الإسكندرية لتداول الحاويات", "اسكندرية للحاويات", "حاويات الإسكندرية"],
    "EKHO.CA": ["القابضة المصرية الكويتية", "المصرية الكويتية", "EKHO"],
    "ETEL.CA": ["المصرية للاتصالات", "وي", "Telecom Egypt", "WE"],
    "FWRY.CA": ["فوري", "فوري لتكنولوجيا البنوك", "Fawry"],
    "HRHO.CA": ["إي إف جي القابضة", "هيرميس", "المجموعة المالية هيرميس", "EFG"],
    "JUFO.CA": ["جهينة", "جهينة للصناعات الغذائية", "Juhayna"],
    "GBCO.CA": ["جي بي كورب", "غبور أوتو", "جي بي أوتو", "GB Corp"],
    "CCAP.CA": ["القلعة", "شركة القلعة", "القلعة للاستشارات", "Qalaa"],
    "ISPH.CA": ["ابن سينا فارما", "ابن سينا", "Ibnsina Pharma"],
    "ESRS.CA": ["حديد عز", "عز للصلب", "Ezz Steel"],
    "PHDC.CA": ["بالم هيلز", "بالم هيلز للتعمير", "Palm Hills"],
    "BTFH.CA": ["بلتون", "بلتون القابضة", "بلتون المالية", "Beltone"],
    "EGAL.CA": ["مصر للألومنيوم", "مصر للالومنيوم", "Egypt Aluminum"],
    "MFPC.CA": ["موبكو", "مصر لإنتاج الأسمدة", "MOPCO"],
    "HELI.CA": ["مصر الجديدة للإسكان", "مصر الجديدة للتعمير", "Heliopolis Housing"]
}

# Seed realistic Arabic financial headlines for MockNewsGenerator fallback
REALISTIC_ARABIC_HEADLINES_SEEDS = {
    "COMI.CA": [
        {"title": "البنك التجاري الدولي (CIB) يعلن عن نمو صافي الأرباح بنسبة 48% وتوزيعات كوبونات نقدية استثنائية", "polarity": 0.88, "source": "إفصاح البورصة المصرية"},
        {"title": "سي آي بي يوقع اتفاقية تمويل مستدام بقيمة 150 مليون دولار لدعم مشروعات الطاقة الخضراء", "polarity": 0.72, "source": "مباشر مصر"},
        {"title": "ارتفاع ودائع العملاء بالبنك التجاري الدولي لتتجاوز 800 مليار جنيه بنهاية الربع الثاني", "polarity": 0.65, "source": "البورصة نيوز"}
    ],
    "SWDY.CA": [
        {"title": "السويدي إليكتريك توقع عقود محطات تحويل كهرباء وطاقة كبرى بالخليج وإفريقيا بقيمة 400 مليون دولار", "polarity": 0.85, "source": "إفصاح البورصة المصرية"},
        {"title": "السويدي تعلن توزيع كوبون نقدي بقيمة 3.50 جنيه للسهم الواحد لدعم المساهمين", "polarity": 0.80, "source": "مباشر مصر"}
    ],
    "TMGH.CA": [
        {"title": "مجموعة طلعت مصطفى تحقق مبيعات تعاقدية غير مسبوقة لمشروع بنان بالرياض ومبيعات الساحل الشمالي", "polarity": 0.82, "source": "إنتربرايز مصر"},
        {"title": "طلعت مصطفى تعلن قفزة في الإيرادات الفندقية بنسبة 65% مع ارتفاع معدلات الإشغال الدولي", "polarity": 0.75, "source": "إفصاح البورصة المصرية"}
    ],
    "ETEL.CA": [
        {"title": "المصرية للاتصالات تسجل نمواً قوياً في إيرادات خدمات البيانات والإنترنت الثابت بنسبة 35%", "polarity": 0.70, "source": "مباشر مصر"},
        {"title": "المصرية للاتصالات توقع اتفاقيات كوابل بحرية دولية تدر عوائد دولارية متنامية", "polarity": 0.68, "source": "إنتربرايز مصر"}
    ],
    "CCAP.CA": [
        {"title": "شركة القلعة تعلن عن استكمال تسوية جزء كبير من المديونيات المصرفية وفوائض تدفقات التكرير", "polarity": 0.55, "source": "إفصاح البورصة المصرية"},
        {"title": "تراجع هوامش تكرير البترول العالمية يضغط مؤقتاً على أرباح الربع الثالث للشركة المصرية للتكرير", "polarity": -0.45, "source": "مباشر مصر"}
    ],
    "BTFH.CA": [
        {"title": "بلتون القابضة تعلن عن زيادة محفظة التمويل غير المصرفي والاستحواذ على شركات تأجير تمويلي", "polarity": 0.70, "source": "البورصة نيوز"}
    ]
}


class MockNewsGenerator:
    """
    Generates realistic, timely Egyptian Arabic financial news headlines for test and sandbox mode.
    """

    @classmethod
    def generate_news_for_ticker(cls, ticker: str, limit: int = 3) -> List[Dict[str, Any]]:
        sym = ticker.upper().strip()
        if not sym.endswith(".CA") and "." not in sym:
            sym += ".CA"

        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        seed_items = REALISTIC_ARABIC_HEADLINES_SEEDS.get(sym, [])

        if not seed_items:
            # Synthetic realistic fallback based on corporate patterns
            seed_items = [
                {"title": f"شركة {sym.replace('.CA','')} تعقد الجمعية العامة وتعتمد تقرير مجلس الإدارة عن القوائم المالية", "polarity": 0.20, "source": "إفصاح البورصة المصرية"},
                {"title": f"نمو ملحوظ في أحجام التداول والسيولة على سهم {sym.replace('.CA','')} بدعم من مشتريات المؤسسات", "polarity": 0.45, "source": "مباشر مصر"}
            ]

        results = []
        for i, item in enumerate(seed_items[:limit]):
            results.append({
                "news_id": f"NEWS-{sym[:4]}-{i+1:02d}",
                "ticker": sym,
                "headline_ar": item["title"],
                "source": item.get("source", "إفصاح البورصة الرسمية"),
                "published_at": now_str,
                "polarity_hint": item.get("polarity", 0.50),
                "is_mock": True
            })
        return results


class NewsIngestionEngine:
    """
    Live Ingestion Engine for EGX Disclosures and Egyptian Financial News feeds.
    """

    PRIMARY_FEEDS = [
        {"url": "https://www.mubasher.info/countries/eg/news/rss", "source_name": "مباشر مصر (Mubasher EGX)"},
        {"url": "https://almalnews.com/feed/", "source_name": "جريدة المال الاقتصادية (Al-Mal News)"},
        {"url": "https://www.mubasher.info/countries/eg/disclosures/rss", "source_name": "إفصاحات البورصة المصرية الرسمية (EGX Disclosures)"}
    ]

    @classmethod
    def fetch_live_news_feed(cls, timeout_sec: int = 3) -> List[Dict[str, Any]]:
        """
        Attempts to fetch live financial news items across multiple redundant RSS feeds.
        Falls back smoothly to Mock generator if offline.
        """
        news_items = []
        seen_titles = set()

        for feed in cls.PRIMARY_FEEDS:
            try:
                req = urllib.request.Request(
                    feed["url"],
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) GEN26-NLP/3.0"}
                )
                with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
                    xml_data = resp.read()
                    root = ET.fromstring(xml_data)
                    for item in root.findall("./channel/item")[:15]:
                        title = item.find("title").text if item.find("title") is not None else ""
                        pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""
                        if not title or title in seen_titles:
                            continue
                        seen_titles.add(title)
                        matched_tickers = cls._match_tickers_in_text(title)
                        for t in matched_tickers:
                            news_items.append({
                                "news_id": f"RSS-{len(news_items)+1:03d}",
                                "ticker": t,
                                "headline_ar": title.strip(),
                                "source": feed["source_name"],
                                "published_at": pub_date or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "is_mock": False
                            })
            except Exception:
                continue

        return news_items

    @classmethod
    def get_news_for_ticker(cls, ticker: str, max_items: int = 5, allow_mock: bool = False) -> List[Dict[str, Any]]:
        """
        Retrieves news items for a specific stock.
        PRODUCTION INVARIANT: Never returns mock news in production unless explicitly allowed for unit tests.
        """
        sym = ticker.upper().strip()
        if not sym.endswith(".CA") and "." not in sym:
            sym += ".CA"

        # 1. Try live feed first
        live_items = [n for n in cls.fetch_live_news_feed() if n.get("ticker") == sym]
        if live_items:
            return live_items[:max_items]

        # 2. Check if Mock is explicitly permitted (e.g. in test sandbox environment)
        env_allow_mock = os.environ.get("GEN26_ALLOW_MOCK_NEWS", "false").lower() in ["true", "1", "yes"]
        if allow_mock or env_allow_mock:
            return MockNewsGenerator.generate_news_for_ticker(sym, limit=max_items)

        # 3. Fail-safe production state: Return empty list (NO FAKE HEADLINES)
        return []

    @classmethod
    def _match_tickers_in_text(cls, text: str) -> List[str]:
        """Identifies EGX tickers mentioned in Arabic headline text."""
        matched = []
        for ticker, keywords in EGX_TICKER_ENTITY_MAP.items():
            for kw in keywords:
                if kw in text:
                    matched.append(ticker)
                    break
        return matched


if __name__ == "__main__":
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    sample = NewsIngestionEngine.get_news_for_ticker("COMI.CA")
    print("COMI.CA Ingested News:")
    print(json.dumps(sample, ensure_ascii=False, indent=2))
