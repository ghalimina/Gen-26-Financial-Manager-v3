#!/usr/bin/env python3
# =============================================================================
# core/news_ingestion_engine.py — GEN-26 Live EGX Financial News & Disclosures Ingestion
# Ingestion architecture for Arabic financial news feeds & official disclosures:
# 1. Multi-source RSS & Web Scraper (EGX Disclosures, Mubasher, Enterprise Egypt,
#    Hapi Journal, Al-Mal News, Asharq Bloomberg Egypt).
# 2. Dynamic 244-Ticker Entity Recognition Mapper auto-generated from EGXUniverseLoader.
# 3. Resilient MockNewsGenerator fallback for offline/sandbox testing.
# 4. Zero-Mock Production Invariant for live quant execution.
# =============================================================================

import os
import sys
import json
import re
import time
import datetime
import urllib.request
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.egx_universe_loader import EGXUniverseLoader

# Base hand-crafted high-priority keyword overrides
BASE_ENTITY_MAP = {
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
    "HELI.CA": ["مصر الجديدة للإسكان", "مصر الجديدة للتعمير", "Heliopolis Housing"],
    "ADIB.CA": ["مصرف أبوظبي الإسلامي", "أبوظبي الإسلامي مصر", "ADIB"],
    "SKPC.CA": ["سيدي كرير للبتروكيماويات", "سيدبك", "Sidpec"],
    "CERA.CA": ["العز للسيراميك", "الجوهرة", "Gemma"],
    "ORHD.CA": ["أوراسكوم للتنمية مصر", "أوراسكوم للفنادق", "Orascom Development"],
    "AMOC.CA": ["الإسكندرية للزيوت المعدنية", "أموك", "AMOC"]
}


def _build_universal_entity_map() -> Dict[str, List[str]]:
    """
    Dynamically generates entity recognition keyword aliases for all active EGX constituents.
    """
    full_map = {}
    universe = EGXUniverseLoader.get_universe("all")
    for stock in universe:
        sym = stock.get("ticker", "")
        if not sym:
            continue
        keywords = set()
        # Clean ticker code
        raw_code = sym.replace(".CA", "").strip()
        keywords.add(raw_code)
        keywords.add(sym)

        # Arabic & English Names
        name_ar = stock.get("name_ar", "")
        name_en = stock.get("name_en", "")
        if name_ar:
            keywords.add(name_ar)
            # Remove common prefixes like "شركة " or "مجموعة "
            cleaned_ar = re.sub(r"^(شركة|مجموعة|بنك|مصرف|المصرية لـ|المصرية لل)\s+", "", name_ar).strip()
            if len(cleaned_ar) >= 3:
                keywords.add(cleaned_ar)
        if name_en:
            keywords.add(name_en)
            cleaned_en = re.sub(r"\b(Holding|Company|Bank|Group|Egypt|SAE|for)\b", "", name_en, flags=re.I).strip()
            if len(cleaned_en) >= 3:
                keywords.add(cleaned_en)

        # Merge with hand-crafted overrides if available
        if sym in BASE_ENTITY_MAP:
            for kw in BASE_ENTITY_MAP[sym]:
                keywords.add(kw)

        full_map[sym] = sorted(list(keywords), key=len, reverse=True)
    return full_map


# Complete 244-Ticker Entity Map
EGX_TICKER_ENTITY_MAP = _build_universal_entity_map()

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
            raw_name = sym.replace(".CA", "")
            stock_info = EGXUniverseLoader.get_stock_info(sym)
            if stock_info and stock_info.get("name_ar"):
                raw_name = stock_info["name_ar"]
            seed_items = [
                {"title": f"شركة {raw_name} تعقد الجمعية العامة وتعتمد تقرير مجلس الإدارة عن القوائم المالية", "polarity": 0.20, "source": "إفصاح البورصة المصرية"},
                {"title": f"نمو ملحوظ في أحجام التداول والسيولة على سهم {raw_name} بدعم من مشتريات المؤسسات", "polarity": 0.45, "source": "مباشر مصر"}
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
    Features multi-source ingestion, robust fallback caching, and 244-ticker entity resolution.
    """

    PRIMARY_FEEDS = [
        {"url": "https://news.google.com/rss/search?q=%D8%A7%D9%84%D8%A8%D9%88%D8%B1%D8%B5%D8%A9+%D8%A7%D9%84%D9%85%D8%B5%D8%B1%D9%8A%D8%A9&hl=ar&gl=EG&ceid=EG:ar", "source_name": "أخبار البورصة المصرية المجمعة (Google Finance EGX)"},
        {"url": "https://news.google.com/rss/search?q=%D8%A3%D8%B3%D9%87%D9%85+%D9%85%D8%B5%D8%B1+EGX&hl=ar&gl=EG&ceid=EG:ar", "source_name": "رادار الأسهم والشركات المصرية (EGX Companies Radar)"},
        {"url": "https://www.mubasher.info/countries/eg/news/rss", "source_name": "مباشر مصر (Mubasher EGX)"},
        {"url": "https://almalnews.com/feed/", "source_name": "جريدة المال الاقتصادية (Al-Mal News)"},
        {"url": "https://www.mubasher.info/countries/eg/disclosures/rss", "source_name": "إفصاحات البورصة المصرية الرسمية (EGX Disclosures)"},
        {"url": "https://hapijournal.com/feed/", "source_name": "جريدة حابي الاقتصادية (Hapi Journal)"},
        {"url": "https://alborsaanews.com/feed", "source_name": "جريدة البورصة نيوز (Al-Borsa News)"},
        {"url": "https://enterprise.press/ar/feed/", "source_name": "إنتربرايز مصر (Enterprise Egypt)"}
    ]

    GLOBAL_GEOPOLITICAL_FEEDS = [
        {"url": "https://news.google.com/rss/search?q=%D8%AD%D8%B1%D8%A8+OR+%D8%B5%D8%B1%D8%A7%D8%B9+OR+%D8%AA%D9%88%D8%AA%D8%B1%D8%A7%D8%AA+%D8%B9%D8%B3%D9%83%D8%B1%D9%8A%D8%A9+OR+%D8%A7%D9%84%D8%B4%D8%B1%D9%82+%D8%A7%D9%84%D8%A3%D9%88%D8%B3%D8%B7&hl=ar&gl=EG&ceid=EG:ar", "source_name": "رادار النزاعات والحروب الإقليمية (Geopolitical Conflict Radar)"},
        {"url": "https://news.google.com/rss/search?q=%D8%A7%D9%84%D9%86%D9%81%D8%B7+OR+%D8%A7%D9%84%D9%81%D9%8A%D8%AF%D8%B1%D8%A7%D9%84%D9%8A+OR+%D8%A8%D8%A7%D8%A8+%D8%A7%D9%84%D9%85%D9%86%D8%AF%D8%A8+OR+%D9%82%D9%86%D8%A7%D8%A9+%D8%A7%D9%84%D8%B3%D9%88%D9%8A%D8%B3&hl=ar&gl=EG&ceid=EG:ar", "source_name": "رادار الطاقة والممرات الملاحية (Global Energy & Maritime Radar)"},
        {"url": "https://feeds.bbci.co.uk/arabic/rss.xml", "source_name": "بي بي سي عربي - شؤون العالم والأزمات (BBC World Arabic)"}
    ]

    _CACHE_NEWS: List[Dict[str, Any]] = []
    _CACHE_TIMESTAMP: float = 0.0
    _CACHE_GLOBAL_NEWS: List[Dict[str, Any]] = []
    _CACHE_GLOBAL_TIMESTAMP: float = 0.0
    CACHE_TTL_SECONDS: float = 300.0  # 5 minutes in-memory cache

    @classmethod
    def get_all_entity_mappings(cls) -> Dict[str, List[str]]:
        """Returns the full 244-ticker active entity resolution mapping."""
        return EGX_TICKER_ENTITY_MAP

    @classmethod
    def fetch_live_news_feed(cls, timeout_sec: int = 4) -> List[Dict[str, Any]]:
        """
        Attempts to fetch live financial news items across multiple redundant RSS & disclosure feeds.
        Cached for CACHE_TTL_SECONDS to avoid rate-limits.
        """
        now = time.time()
        if cls._CACHE_NEWS and (now - cls._CACHE_TIMESTAMP) < cls.CACHE_TTL_SECONDS:
            return cls._CACHE_NEWS

        news_items = []
        seen_titles = set()
        import concurrent.futures

        def _fetch_single_feed(feed):
            items = []
            try:
                req = urllib.request.Request(
                    feed["url"],
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 GEN26-NLP/3.0",
                        "Accept": "application/rss+xml, application/xml, text/xml, */*"
                    }
                )
                with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
                    xml_data = resp.read()
                    root = ET.fromstring(xml_data)
                    for item in root.findall("./channel/item")[:20]:
                        title = item.find("title").text if item.find("title") is not None else ""
                        pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""
                        if title:
                            items.append((title.strip(), pub_date, feed["source_name"]))
            except Exception:
                pass
            return items

        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(cls.PRIMARY_FEEDS), 6)) as executor:
            futures = [executor.submit(_fetch_single_feed, feed) for feed in cls.PRIMARY_FEEDS]
            for fut in concurrent.futures.as_completed(futures):
                try:
                    for title, pub_date, source_name in fut.result():
                        if title in seen_titles:
                            continue
                        seen_titles.add(title)
                        matched_tickers = cls._match_tickers_in_text(title)
                        for t in matched_tickers:
                            news_items.append({
                                "news_id": f"RSS-{len(news_items)+1:03d}",
                                "ticker": t,
                                "headline_ar": title,
                                "source": source_name,
                                "published_at": pub_date or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "is_mock": False
                            })
                except Exception:
                    continue

        if news_items:
            cls._CACHE_NEWS = news_items
            cls._CACHE_TIMESTAMP = now

        return news_items if news_items else cls._CACHE_NEWS

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
        """
        Identifies EGX tickers mentioned in Arabic headline text across all universe constituents.
        Enforces strict regex word boundaries for short keywords (<= 3 chars) to prevent false substring collisions.
        """
        if not text:
            return []
        matched = []
        for ticker, keywords in EGX_TICKER_ENTITY_MAP.items():
            for kw in keywords:
                if not kw:
                    continue
                # For short keywords (<= 3 chars, e.g. "وي", "عز", "WE", "CIB"), enforce whole-word match
                if len(kw) <= 3:
                    pattern = r'(?:\b|[^\w\u0600-\u06FF])' + re.escape(kw) + r'(?:\b|[^\w\u0600-\u06FF])'
                    if re.search(pattern, text, re.IGNORECASE):
                        matched.append(ticker)
                        break
                else:
                    if kw in text:
                        matched.append(ticker)
                        break
        return matched

    @classmethod
    def fetch_global_geopolitical_news(cls, timeout_sec: int = 5) -> List[Dict[str, Any]]:
        """
        Fetches live international, regional war, shipping, and global commodity conflict news.
        Cached for CACHE_TTL_SECONDS.
        """
        now = time.time()
        if cls._CACHE_GLOBAL_NEWS and (now - cls._CACHE_GLOBAL_TIMESTAMP) < cls.CACHE_TTL_SECONDS:
            return cls._CACHE_GLOBAL_NEWS

        WAR_KEYWORDS = ["حرب", "صراع", "ضربة", "هجوم", "صواريخ", "مسيرة", "عسكرية", "اغتيال", "توترات", "غارات", "جيش", "تصعيد"]
        SHIPPING_KEYWORDS = ["باب المندب", "قناة السويس", "البحر الأحمر", "ملاحة", "سفن", "شحن"]
        OIL_KEYWORDS = ["النفط", "برنت", "طاقة", "غاز", "أوبك"]

        import concurrent.futures
        events = []
        seen = set()

        def _fetch_feed(f_info):
            items = []
            try:
                req = urllib.request.Request(
                    f_info["url"],
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 GEN26-GlobalFeed/3.0",
                        "Accept": "application/rss+xml, application/xml, text/xml, */*"
                    }
                )
                with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
                    xml_data = resp.read()
                    root = ET.fromstring(xml_data)
                    for item in root.findall("./channel/item")[:15]:
                        title = item.find("title").text if item.find("title") is not None else ""
                        pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""
                        if title:
                            items.append((title.strip(), pub_date, f_info["source_name"]))
            except Exception:
                pass
            return items

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(_fetch_feed, feed) for feed in cls.GLOBAL_GEOPOLITICAL_FEEDS]
            for fut in concurrent.futures.as_completed(futures):
                try:
                    for title, pub_date, source_name in fut.result():
                        if title in seen:
                            continue
                        seen.add(title)
                        cats = []
                        if any(k in title for k in WAR_KEYWORDS):
                            cats.append("WAR_MILITARY")
                        if any(k in title for k in SHIPPING_KEYWORDS):
                            cats.append("SHIPPING_CANAL")
                        if any(k in title for k in OIL_KEYWORDS):
                            cats.append("OIL_ENERGY")

                        if cats:
                            severity = "HIGH" if ("WAR_MILITARY" in cats and any(w in title for w in ["تصعيد", "ضربة", "هجوم", "صواريخ", "اغتيال"])) else "MEDIUM"
                            events.append({
                                "headline_ar": title,
                                "source": source_name,
                                "categories": cats,
                                "severity": severity,
                                "published_at": pub_date or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            })
                except Exception:
                    continue

        if events:
            cls._CACHE_GLOBAL_NEWS = events
            cls._CACHE_GLOBAL_TIMESTAMP = now

        return events if events else cls._CACHE_GLOBAL_NEWS

    @classmethod
    def get_global_geopolitical_risk_state(cls) -> Dict[str, Any]:
        """
        Analyzes live global conflict & energy feeds to evaluate geopolitical risk for EGX equities.
        """
        events = cls.fetch_global_geopolitical_news()
        if not events:
            return {
                "threat_level": "LOW_STABLE",
                "threat_level_ar": "🟢 استقرار جيوسياسي نسبي",
                "threat_buffer_cash_pct": 0.0,
                "has_war_conflict": False,
                "has_shipping_disruption": False,
                "has_oil_shock": False,
                "top_geopolitical_events": []
            }

        high_severity_count = sum(1 for e in events if e.get("severity") == "HIGH")
        has_war = any("WAR_MILITARY" in e.get("categories", []) for e in events)
        has_shipping = any("SHIPPING_CANAL" in e.get("categories", []) for e in events)
        has_oil = any("OIL_ENERGY" in e.get("categories", []) for e in events)

        if high_severity_count >= 3 or (has_war and (has_shipping or has_oil)):
            threat_level = "ELEVATED_WAR_RISK"
            threat_level_ar = "🚨 توترات عسكرية وحروب إقليمية نشطة (مخاطر طاقة وملاحة)"
            buffer_cash = 15.0  # Extra cash buffer
        elif has_war or has_shipping or has_oil:
            threat_level = "MODERATE_TENSION"
            threat_level_ar = "⚠️ تصاعد في التوترات الجيوسياسية الإقليمية"
            buffer_cash = 5.0
        else:
            threat_level = "LOW_STABLE"
            threat_level_ar = "🟢 استقرار جيوسياسي نسبي"
            buffer_cash = 0.0

        return {
            "threat_level": threat_level,
            "threat_level_ar": threat_level_ar,
            "threat_buffer_cash_pct": buffer_cash,
            "has_war_conflict": has_war,
            "has_shipping_disruption": has_shipping,
            "has_oil_shock": has_oil,
            "top_geopolitical_events": events[:5]
        }


if __name__ == "__main__":
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    print(f"Total Universal Entity Mappings: {len(EGX_TICKER_ENTITY_MAP)} EGX Equities")
    sample = NewsIngestionEngine.get_news_for_ticker("COMI.CA", allow_mock=True)
    print("COMI.CA Ingested News Sample:")
    print(json.dumps(sample, ensure_ascii=False, indent=2))
