#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/ingest_daily_news_rss.py
================================
GEN-26 Robust Live EGX News & Disclosures RSS Ingestion Pipeline.
1. Scrapes authoritative live Arabic financial news and corporate disclosures via open RSS feeds:
   - Mubasher Egypt (مباشر مصر)
   - Al-Borsa News (جريدة البورصة)
   - Enterprise Egypt (إنتربرايز مصر)
   - Hapi Journal (جريدة حابي الاقتصادية)
   - Google Finance EGX (رادار البورصة المصرية)
2. Uses standard urllib.request and xml.etree.ElementTree with robust headers and error resilience.
3. Enforces strict timestamp normalization (published_at YYYY-MM-DD HH:MM:SS).
4. Matches company entities across active EGX tickers (COMI, SWDY, TMGH, ABUK, PHDC, RAYA, etc.).
5. Computes Arabic financial NLP sentiment polarity and event taxonomy.
6. Persists into news_events table in data/gen26_production.db with deduplication.
"""

import os
import sys
import re
import json
import time
import email.utils
import datetime
import hashlib
import sqlite3
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional, Tuple

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

DATA_DIR = os.path.join(WORKSPACE, "data")
DB_PATH = os.path.join(DATA_DIR, "gen26_production.db")
NEWS_JSON_FILE = os.path.join(DATA_DIR, "news_events.json")

# -----------------------------------------------------------------------------
# 1. Authoritative RSS Feeds Configuration
# -----------------------------------------------------------------------------
RSS_FEEDS = [
    {
        "name": "جريدة البورصة",
        "url": "https://www.alborsaanews.com/feed/",
        "fallback_url": "https://alborsaanews.com/feed",
        "default_source": "Al-Borsa News"
    },
    {
        "name": "إنتربرايز مصر",
        "url": "https://enterprise.news/feed/",
        "fallback_url": "https://enterprise.press/feed",
        "default_source": "Enterprise Egypt"
    },
    {
        "name": "مباشر مصر",
        "url": "https://news.google.com/rss/search?q=site:mubasher.info+%D8%A7%D9%84%D8%A8%D9%88%D8%B1%D8%B5%D8%A9+%D8%A7%D9%84%D9%85%D8%B5%D8%B1%D9%8A%D8%A9&hl=ar&gl=EG&ceid=EG:ar",
        "fallback_url": "https://www.mubasher.info/countries/eg/news/rss",
        "default_source": "Mubasher Egypt"
    },
    {
        "name": "جريدة حابي الاقتصادية",
        "url": "https://hapijournal.com/feed/",
        "fallback_url": None,
        "default_source": "Hapi Journal"
    },
    {
        "name": "رادار البورصة المصرية",
        "url": "https://news.google.com/rss/search?q=%D8%A7%D9%84%D8%A8%D9%88%D8%B1%D8%B5%D8%A9+%D8%A7%D9%84%D9%85%D8%B5%D8%B1%D9%8A%D8%A9&hl=ar&gl=EG&ceid=EG:ar",
        "fallback_url": None,
        "default_source": "Google Finance EGX"
    }
]

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36 GEN26-NewsIngestion/3.0"
)

# -----------------------------------------------------------------------------
# 2. Entity Mapping & Keywords Aliases
# -----------------------------------------------------------------------------
BASE_PRIORITY_ENTITIES: Dict[str, Dict[str, Any]] = {
    "COMI.CA": {
        "company": "البنك التجاري الدولي",
        "sector": "Banking",
        "keywords": ["البنك التجاري الدولي", "التجاري الدولي", "CIB", "سي آي بي"]
    },
    "SWDY.CA": {
        "company": "السويدي إليكتريك",
        "sector": "Industrial",
        "keywords": ["السويدي إليكتريك", "السويدي اليكتريك", "السويدي للكابلات", "Elsewedy", "السويدي"]
    },
    "TMGH.CA": {
        "company": "مجموعة طلعت مصطفى القابضة",
        "sector": "Real Estate",
        "keywords": ["طلعت مصطفى", "مجموعة طلعت مصطفى", "بنان", "SouthMED", "ساوث ميد", "TMG"]
    },
    "ABUK.CA": {
        "company": "أبو قير للأسمدة والصناعات الكيماوية",
        "sector": "Chemicals",
        "keywords": ["أبو قير للأسمدة", "ابو قير للاسمدة", "أبوقير للأسمدة", "ابوقير للاسمدة", "أبو قير", "ابو قير"]
    },
    "PHDC.CA": {
        "company": "بالم هيلز للتعمير",
        "sector": "Real Estate",
        "keywords": ["بالم هيلز", "بالم هيلز للتعمير", "Palm Hills"]
    },
    "RAYA.CA": {
        "company": "راية القابضة للاستثمارات المالية",
        "sector": "Technology",
        "keywords": ["راية القابضة", "راية لخدمات مراكز الاتصالات", "راية للتجارة", "Raya", "شركة راية"]
    },
    "BTFH.CA": {
        "company": "بلتون القابضة",
        "sector": "Financial Services",
        "keywords": ["بلتون", "بلتون القابضة", "بلتون المالية", "Beltone"]
    },
    "FWRY.CA": {
        "company": "فوري لتكنولوجيا البنوك والمدفوعات الإلكترونية",
        "sector": "Technology",
        "keywords": ["فوري", "فوري لتكنولوجيا البنوك", "Fawry"]
    },
    "ESRS.CA": {
        "company": "حديد عز",
        "sector": "Industrial",
        "keywords": ["حديد عز", "عز للصلب", "Ezz Steel"]
    },
    "MFPC.CA": {
        "company": "مصر لإنتاج الأسمدة - موبكو",
        "sector": "Chemicals",
        "keywords": ["موبكو", "مصر لإنتاج الأسمدة", "MOPCO"]
    },
    "SKPC.CA": {
        "company": "سيدي كرير للبتروكيماويات",
        "sector": "Petrochemicals",
        "keywords": ["سيدي كرير للبتروكيماويات", "سيدبك", "Sidpec", "سيدي كرير"]
    },
    "EGAL.CA": {
        "company": "مصر للألومنيوم",
        "sector": "Industrial",
        "keywords": ["مصر للألومنيوم", "مصر للالومنيوم", "Egypt Aluminum"]
    },
    "HRHO.CA": {
        "company": "إي إف جي القابضة (هيرميس)",
        "sector": "Financial Services",
        "keywords": ["إي إف جي القابضة", "هيرميس", "المجموعة المالية هيرميس", "EFG"]
    },
    "ETEL.CA": {
        "company": "المصرية للاتصالات",
        "sector": "Telecommunications",
        "keywords": ["المصرية للاتصالات", "وي", "Telecom Egypt"]
    },
    "CCAP.CA": {
        "company": "شركة القلعة للاستشارات المالية",
        "sector": "Financial Services",
        "keywords": ["شركة القلعة", "القلعة للاستشارات", "Qalaa", "المصرية للتكرير"]
    },
    "ISPH.CA": {
        "company": "ابن سينا فارما",
        "sector": "Healthcare",
        "keywords": ["ابن سينا فارما", "ابن سينا", "Ibnsina Pharma"]
    },
    "JUFO.CA": {
        "company": "جهينة للصناعات الغذائية",
        "sector": "Food & Beverage",
        "keywords": ["جهينة للصناعات الغذائية", "جهينة", "Juhayna"]
    },
    "GBCO.CA": {
        "company": "جي بي كورب",
        "sector": "Automotive",
        "keywords": ["جي بي كورب", "غبور أوتو", "جي بي أوتو", "GB Corp", "غبور"]
    },
    "AMOC.CA": {
        "company": "الإسكندرية للزيوت المعدنية",
        "sector": "Petrochemicals",
        "keywords": ["الإسكندرية للزيوت المعدنية", "أموك", "AMOC"]
    },
    "ORAS.CA": {
        "company": "أوراسكوم للإنشاء",
        "sector": "Construction",
        "keywords": ["أوراسكوم للإنشاء", "اوراسكوم للانشاء", "Orascom Construction", "أوراسكوم"]
    },
    "ALCN.CA": {
        "company": "الإسكندرية لتداول الحاويات والبضائع",
        "sector": "Logistics",
        "keywords": ["الإسكندرية لتداول الحاويات", "اسكندرية للحاويات", "حاويات الإسكندرية", "حاويات اسكندرية"]
    },
    "MASR.CA": {
        "company": "مدينة مصر للإسكان والتعمير",
        "sector": "Real Estate",
        "keywords": ["مدينة مصر للإسكان", "مدينة مصر", "مدينة نصر للإسكان", "Madinet Masr"]
    },
    "EMFD.CA": {
        "company": "إعمار مصر للتنمية",
        "sector": "Real Estate",
        "keywords": ["إعمار مصر", "إعمار مصر للتنمية", "Emaar Misr"]
    },
    "EAST.CA": {
        "company": "الشرقية - إيسترن كومباني",
        "sector": "Consumer Goods",
        "keywords": ["الشرقية للدخان", "إيسترن كومباني", "Eastern Company", "ايسترن كومباني"]
    },
    "ADIB.CA": {
        "company": "مصرف أبوظبي الإسلامي مصر",
        "sector": "Banking",
        "keywords": ["مصرف أبوظبي الإسلامي", "أبوظبي الإسلامي مصر", "ADIB"]
    },
    "TAQA.CA": {
        "company": "طاقة عربية",
        "sector": "Energy",
        "keywords": ["طاقة عربية", "شركة طاقة عربية", "Taqa Arabia"]
    },
    "HELI.CA": {
        "company": "مصر الجديدة للإسكان والتعمير",
        "sector": "Real Estate",
        "keywords": ["مصر الجديدة للإسكان", "مصر الجديدة للتعمير", "Heliopolis Housing"]
    },
    "EKHO.CA": {
        "company": "القابضة المصرية الكويتية",
        "sector": "Investment",
        "keywords": ["القابضة المصرية الكويتية", "المصرية الكويتية", "EKHO"]
    },
    "CERA.CA": {
        "company": "العربية للخزف - سيراميكا ريماس",
        "sector": "Building Materials",
        "keywords": ["العربية للخزف", "سيراميكا ريماس", "ريماس", "CERA"]
    },
    "ORHD.CA": {
        "company": "أوراسكوم للتنمية مصر",
        "sector": "Real Estate & Tourism",
        "keywords": ["أوراسكوم للتنمية", "أوراسكوم للتنمية مصر", "Orascom Development"]
    },
    "CICH.CA": {
        "company": "سي آي كابيتال القابضة للاستثمارات المالية",
        "sector": "Financial Services",
        "keywords": ["سي آي كابيتال", "CI Capital"]
    },
    "ORWE.CA": {
        "company": "النساجون الشرقيون للسجاد",
        "sector": "Consumer Durables",
        "keywords": ["النساجون الشرقيون", "Oriental Weavers"]
    },
    "EFID.CA": {
        "company": "إيديتا للصناعات الغذائية",
        "sector": "Food & Beverage",
        "keywords": ["إيديتا للصناعات الغذائية", "إيديتا", "Edita"]
    },
    "DOMT.CA": {
        "company": "الصناعات الغذائية العربية - دومتي",
        "sector": "Food & Beverage",
        "keywords": ["دومتي", "الصناعات الغذائية العربية دومتي", "Domty"]
    },
    "MFSC.CA": {
        "company": "مصر للأسواق الحرة",
        "sector": "Retail",
        "keywords": ["مصر للأسواق الحرة", "مصر للاسواق الحرة", "MFSC"]
    },
    "AJWA.CA": {
        "company": "أجواء للصناعات الغذائية - مصر",
        "sector": "Food & Beverage",
        "keywords": ["أجواء للصناعات الغذائية", "اجواء للصناعات الغذائية", "أجواء مصر", "AJWA"]
    },
    "EXPA.CA": {
        "company": "بنك تنمية الصادرات",
        "sector": "Banking",
        "keywords": ["بنك تنمية الصادرات", "تنمية الصادرات", "EBank"]
    },
    "CNFN.CA": {
        "company": "كونتكت المالية القابضة",
        "sector": "Financial Services",
        "keywords": ["كونتكت المالية", "كونتكت القابضة", "Contact Financial"]
    }
}

# -----------------------------------------------------------------------------
# 3. Arabic Financial Sentiment Lexicon & Taxonomy
# -----------------------------------------------------------------------------
POSITIVE_KEYWORDS = [
    "أرباح", "نمو", "توزيع نقدي", "كوبون", "قفزة", "صعود", "ارتفاع",
    "توسع", "فوز بعقد", "استحواذ", "فائض", "استثمار", "تدفقات",
    "ترقية", "توصية بشراء", "ربحية", "زيادة رأس مال", "اتفاقية",
    "إيرادات قياسية", "مبيعات قياسية", "انتعاش", "مكاسب", "تمويل",
    "شراكة", "أرباح قياسية", "توزيعات", "شراء أسهم خزينة", "سهم خزينة",
    "تجديد ترخيص", "تسوية مديونيات", "تخارج رابح", "رفع تصنيف"
]

NEGATIVE_KEYWORDS = [
    "خسائر", "تراجع", "غرامة", "هبوط", "انخفاض", "عجز", "تحقيق",
    "عقوبات", "شطب", "بيع مكثف", "هبوط حاد", "خسارة", "تعثر",
    "ديون", "ضغوط بيعية", "إلغاء", "نزاع", "دعوى قضائية", "خلاف",
    "توقف", "تخفيض تصنيف", "تراجع الأرباح", "تآكل", "إفلاس", "شبهة",
    "تراجع الإيرادات", "هبوط حاد", "حجز إداري", "وقف تداول"
]


def init_database() -> sqlite3.Connection:
    """Initializes news_events table and required indexes in gen26_production.db."""
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS news_events (
            news_id TEXT PRIMARY KEY,
            source TEXT NOT NULL,
            url TEXT,
            published_at TEXT NOT NULL,
            retrieved_at TEXT NOT NULL,
            company TEXT NOT NULL,
            ticker TEXT NOT NULL,
            sector TEXT NOT NULL,
            country TEXT DEFAULT 'EG',
            event_type TEXT NOT NULL,
            sentiment TEXT NOT NULL,
            sentiment_confidence REAL NOT NULL,
            importance TEXT NOT NULL,
            language TEXT DEFAULT 'ar',
            headline TEXT NOT NULL,
            alpha_shock_pct REAL DEFAULT 0.0,
            created_at TEXT NOT NULL
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_news_ticker_pub ON news_events(ticker, published_at)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_news_url ON news_events(url)")
    conn.commit()
    return conn


def parse_rfc_or_iso_datetime(date_str: Optional[str]) -> str:
    """
    Parses RSS pubDate (RFC 2822 or ISO 8601) to strict format YYYY-MM-DD HH:MM:SS.
    Falls back to current local/Cairo time if parsing fails.
    """
    if not date_str or not date_str.strip():
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cleaned = date_str.strip()
    # 1. Try RFC 2822
    try:
        dt = email.utils.parsedate_to_datetime(cleaned)
        if dt:
            return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        pass

    # 2. Try ISO 8601
    try:
        iso_clean = cleaned.replace("Z", "+00:00")
        dt = datetime.datetime.fromisoformat(iso_clean)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        pass

    # 3. Try standard formats
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y"):
        try:
            dt = datetime.datetime.strptime(cleaned, fmt)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            continue

    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def analyze_arabic_sentiment(text: str) -> Tuple[str, float, float, str, str]:
    """
    Analyzes Arabic text sentiment and event taxonomy.
    Returns: (sentiment, confidence, score, event_type, importance)
    """
    pos_count = sum(1 for kw in POSITIVE_KEYWORDS if kw in text)
    neg_count = sum(1 for kw in NEGATIVE_KEYWORDS if kw in text)

    # Event Type
    event_type = "MARKET_UPDATE"
    if any(k in text for k in ("أرباح", "خسائر", "نتائج أعمال", "قوائم مالية", "صافي ربح", "صافي أرباح")):
        event_type = "EARNINGS"
    elif any(k in text for k in ("توزيع", "كوبون", "أرباح مرحلية", "عائد نقدي")):
        event_type = "DIVIDEND"
    elif any(k in text for k in ("رأس مال", "اكتتاب", "أسهم مجانية", "زيادة رأسمال")):
        event_type = "CAPITAL_INCREASE"
    elif any(k in text for k in ("استحواذ", "شراء حصة", "اندماج", "عرض شراء")):
        event_type = "ACQUISITION"
    elif any(k in text for k in ("عقد", "اتفاقية", "مناقصة", "مشروع ضخم", "شراكة استراتيجية")):
        event_type = "CONTRACT"
    elif any(k in text for k in ("الرقابة المالية", "الهيئة العامة", "البورصة", "قيد", "شطب", "موافقة")):
        event_type = "REGULATORY"
    elif any(k in text for k in ("توسع", "افتتاح", "مصنع جديد", "خط إنتاج")):
        event_type = "EXPANSION"
    elif any(k in text for k in ("مجلس إدارة", "استقالة", "تعيين", "رئيس مجلس", "عضو منتدب")):
        event_type = "MANAGEMENT_CHANGE"

    # Polarity & Score
    if pos_count > neg_count:
        sentiment = "POSITIVE"
        diff = pos_count - neg_count
        confidence = min(0.95, 0.75 + diff * 0.05)
        score = min(1.0, 0.45 + diff * 0.20)
        alpha_shock = round(score * 2.2, 2)
    elif neg_count > pos_count:
        sentiment = "NEGATIVE"
        diff = neg_count - pos_count
        confidence = min(0.95, 0.75 + diff * 0.05)
        score = max(-1.0, -0.45 - diff * 0.20)
        alpha_shock = round(score * 2.2, 2)
    else:
        sentiment = "NEUTRAL"
        confidence = 0.70
        score = 0.0
        alpha_shock = 0.0

    # Importance
    if abs(score) >= 0.75 or event_type in ("EARNINGS", "DIVIDEND", "ACQUISITION"):
        importance = "HIGH"
    elif abs(score) >= 0.40 or event_type in ("CONTRACT", "CAPITAL_INCREASE"):
        importance = "MEDIUM"
    else:
        importance = "LOW"

    return sentiment, confidence, alpha_shock, event_type, importance


def match_entities_in_text(text: str) -> List[Tuple[str, str, str]]:
    """
    Identifies all EGX tickers mentioned in the news headline or description.
    Returns: List of tuples (ticker, company_name, sector)
    """
    matched = []
    seen_tickers = set()

    for ticker, info in BASE_PRIORITY_ENTITIES.items():
        if ticker in seen_tickers:
            continue
        keywords = info["keywords"]
        for kw in keywords:
            if not kw:
                continue
            if len(kw) <= 3:
                pattern = r'(?:\b|[^\w\u0600-\u06FF])' + re.escape(kw) + r'(?:\b|[^\w\u0600-\u06FF])'
                if re.search(pattern, text, re.IGNORECASE):
                    matched.append((ticker, info["company"], info["sector"]))
                    seen_tickers.add(ticker)
                    break
            else:
                if kw in text:
                    matched.append((ticker, info["company"], info["sector"]))
                    seen_tickers.add(ticker)
                    break

    # If no specific company matched, check if it's general market / EGX30 index news
    if not matched:
        index_keywords = ["البورصة المصرية", "مؤشر البورصة", "إيجي إكس", "EGX30", "EGX 30", "ايجي اكس"]
        if any(ik in text for ik in index_keywords):
            matched.append(("EGX30.CA", "المؤشر الرئيسي للبورصة المصرية EGX30", "Index & Macro"))

    return matched


def fetch_rss_feed_items(feed_cfg: Dict[str, Any], timeout_sec: int = 10) -> List[Dict[str, Any]]:
    """Fetches and parses items from an RSS feed URL with fallback."""
    items_out = []
    urls_to_try = [feed_cfg["url"]]
    if feed_cfg.get("fallback_url"):
        urls_to_try.append(feed_cfg["fallback_url"])

    for feed_url in urls_to_try:
        try:
            req = urllib.request.Request(
                feed_url,
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "application/rss+xml, application/xml, text/xml, */*"
                }
            )
            with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
                xml_data = resp.read()
                root = ET.fromstring(xml_data)
                channel = root.find("channel")
                raw_items = channel.findall("item") if channel is not None else root.findall(".//item")

                for it in raw_items:
                    t_elem = it.find("title")
                    l_elem = it.find("link")
                    d_elem = it.find("description")
                    p_elem = it.find("pubDate")

                    title = t_elem.text.strip() if (t_elem is not None and t_elem.text) else ""
                    link = l_elem.text.strip() if (l_elem is not None and l_elem.text) else ""
                    desc = d_elem.text.strip() if (d_elem is not None and d_elem.text) else ""
                    pub = p_elem.text.strip() if (p_elem is not None and p_elem.text) else ""

                    if title:
                        items_out.append({
                            "title": title,
                            "link": link,
                            "description": desc,
                            "pub_date_raw": pub,
                            "source_name": feed_cfg["name"]
                        })

                if items_out:
                    # Successfully fetched items from this URL
                    break
        except Exception as e:
            # Try fallback URL if available
            continue

    return items_out


def run_news_ingestion() -> Dict[str, Any]:
    """
    Orchestrates the entire RSS ingestion, sentiment scoring, and database persistence.
    """
    print("=" * 75)
    print("📰 GEN-26 REAL-TIME EGX RSS NEWS & SENTIMENT INGESTION PIPELINE")
    print("=" * 75)

    conn = init_database()
    cur = conn.cursor()
    retrieved_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    total_scraped = 0
    total_matched = 0
    inserted_count = 0
    duplicate_count = 0

    all_scraped_items = []
    seen_headline_urls = set()

    # Step 1: Scrape all feeds
    for feed in RSS_FEEDS:
        print(f"[*] جاري الاتصال بخلاصة: {feed['name']}...")
        feed_items = fetch_rss_feed_items(feed)
        print(f"    • تم سحب {len(feed_items)} خبراً من {feed['name']}.")
        total_scraped += len(feed_items)
        for it in feed_items:
            key = (it["title"], it["link"])
            if key not in seen_headline_urls:
                seen_headline_urls.add(key)
                all_scraped_items.append(it)

    print(f"\n[*] إجمالي الأخبار المجمعة الفريدة: {len(all_scraped_items)} خبراً.")
    print("[*] جاري مطابقة الكيانات والأسهم المقيدة وحساب درجات المشاعر...")

    # Step 2: Entity matching & Sentiment scoring
    matched_records = []
    for item in all_scraped_items:
        title = item["title"]
        desc = item["description"]
        full_text = f"{title} {desc}"

        matches = match_entities_in_text(full_text)
        if not matches:
            continue

        total_matched += 1
        published_at = parse_rfc_or_iso_datetime(item.get("pub_date_raw"))
        sentiment, conf, alpha_shock, event_type, importance = analyze_arabic_sentiment(full_text)

        for ticker, comp_name, sector in matches:
            # Deterministic News ID for deduplication
            id_hash = hashlib.md5(f"{ticker}_{title}_{published_at}".encode("utf-8")).hexdigest()[:12]
            news_id = f"RSS_{ticker.replace('.CA', '')}_{id_hash}"

            matched_records.append({
                "news_id": news_id,
                "source": item["source_name"],
                "url": item.get("link", ""),
                "published_at": published_at,
                "retrieved_at": retrieved_at,
                "company": comp_name,
                "ticker": ticker,
                "sector": sector,
                "country": "EG",
                "event_type": event_type,
                "sentiment": sentiment,
                "sentiment_confidence": conf,
                "importance": importance,
                "language": "ar",
                "headline": title,
                "alpha_shock_pct": alpha_shock,
                "created_at": retrieved_at
            })

    # Step 3: Insert into gen26_production.db
    print(f"[*] تم التعرف على {len(matched_records)} إشارة مطابقة للأسهم المقيدة.")
    print("[*] جاري التخزين الدائم في SQLite (news_events)...")

    for rec in matched_records:
        try:
            cur.execute("""
                INSERT OR IGNORE INTO news_events (
                    news_id, source, url, published_at, retrieved_at,
                    company, ticker, sector, country, event_type,
                    sentiment, sentiment_confidence, importance, language,
                    headline, alpha_shock_pct, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rec["news_id"], rec["source"], rec["url"], rec["published_at"], rec["retrieved_at"],
                rec["company"], rec["ticker"], rec["sector"], rec["country"], rec["event_type"],
                rec["sentiment"], rec["sentiment_confidence"], rec["importance"], rec["language"],
                rec["headline"], rec["alpha_shock_pct"], rec["created_at"]
            ))
            if cur.rowcount > 0:
                inserted_count += 1
            else:
                duplicate_count += 1
        except Exception as e:
            print(f"[WARN] Error inserting news record: {e}")

    conn.commit()

    # Step 4: Export to news_events.json cache
    cur.execute("SELECT COUNT(*) FROM news_events")
    total_db_rows = cur.fetchone()[0]

    cur.execute("SELECT * FROM news_events ORDER BY published_at DESC LIMIT 50")
    recent_rows = cur.fetchall()
    cols = [col[0] for col in cur.description]
    json_export = [dict(zip(cols, r)) for r in recent_rows]

    try:
        with open(NEWS_JSON_FILE, "w", encoding="utf-8") as jf:
            json.dump({
                "last_sync": retrieved_at,
                "total_events": total_db_rows,
                "events": json_export
            }, jf, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[WARN] Failed to write news_events.json: {e}")

    conn.close()

    print("\n" + "=" * 75)
    print("✅ تم اكتمال دورة سحب الأخبار الحية بنجاح تام!")
    print(f"    • إجمالي الأخبار المسحوبة: {total_scraped}")
    print(f"    • الأخبار المطابقة للشركات: {total_matched}")
    print(f"    • سجلات جديدة أُضيفت:     {inserted_count}")
    print(f"    • سجلات مكررة تم تجاهلها:  {duplicate_count}")
    print(f"    • إجمالي السجلات في القاعدة: {total_db_rows} خبر")
    print("=" * 75)

    return {
        "status": "SUCCESS",
        "total_scraped": total_scraped,
        "total_matched": total_matched,
        "inserted_count": inserted_count,
        "duplicate_count": duplicate_count,
        "total_db_rows": total_db_rows
    }


if __name__ == "__main__":
    res = run_news_ingestion()
    sys.exit(0 if res.get("status") == "SUCCESS" else 1)
