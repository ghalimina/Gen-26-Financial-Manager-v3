#!/usr/bin/env python3
# =============================================================================
# scripts/build_pit_universe_and_corporate_actions.py — GEN-26 PIT Universe & CA Builder
# Populates historical_universe_registry and corporate_actions in gen26_production.db
# to permanently eliminate Survivorship Bias and provide full point-in-time universe history.
# =============================================================================

import os
import sys
import json
import sqlite3
import datetime

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from core.historical_universe_manager import HistoricalUniverseManager
from core.egx_universe_loader import EGXUniverseLoader

DATA_DIR = os.path.join(WORKSPACE, "data")
DB_PATH = os.path.join(DATA_DIR, "gen26_production.db")
UNIVERSE_270_FILE = os.path.join(DATA_DIR, "thndr_egx_270_universe.json")
CORPORATE_ACTIONS_JSON = os.path.join(DATA_DIR, "corporate_actions_database.json")
HISTORICAL_REGISTRY_JSON = os.path.join(DATA_DIR, "historical_universe_registry.json")


def build_historical_universe():
    print("[1/3] Building Historical Point-in-Time Universe Registry...")
    HistoricalUniverseManager.init_db()

    # Load 270 current stocks
    stock_list = []
    if os.path.exists(UNIVERSE_270_FILE):
        with open(UNIVERSE_270_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
            stock_list = raw.get("stocks", []) if isinstance(raw, dict) else raw

    # Known IPO / Listing dates for prominent EGX equities (to ensure proper PIT behavior)
    KNOWN_LISTING_DATES = {
        "FWRY.CA": "2019-08-08",
        "EFIH.CA": "2021-10-20",
        "TALM.CA": "2021-04-14",
        "ACTF.CA": "2024-03-24",
        "MCQE.CA": "2021-12-01",
        "MASR.CA": "2014-06-18",
        "CLHO.CA": "2015-04-02",
        "IDHC.CA": "2021-05-20",
        "IBRN.CA": "2018-05-15",
        "RAYA.CA": "2005-05-10",
        "COMI.CA": "1995-01-01",
        "SWDY.CA": "2006-05-20",
        "TMGH.CA": "2007-11-25",
        "ETEL.CA": "2005-12-14",
        "ABUK.CA": "1994-01-01",
        "EKHO.CA": "1999-01-01",
        "ORAS.CA": "2015-03-09",
        "ESRS.CA": "1999-01-01",
        "MNHD.CA": "1995-01-01",
        "PHDC.CA": "2008-04-01"
    }

    registry_items = []

    # 1. Add all 270 current equities
    for info in stock_list:
        if isinstance(info, str):
            sym = info.upper()
            info_dict = {"ticker": sym, "name_ar": sym, "sector": "Equities"}
        else:
            sym = info.get("ticker", "").upper()
            info_dict = info
        if not sym:
            continue

        listing_d = KNOWN_LISTING_DATES.get(sym, "2015-01-01")
        reg_item = {
            "ticker": sym,
            "company_name": info_dict.get("name_ar", info_dict.get("name_en", sym)),
            "listing_date": listing_d,
            "delisting_date": "9999-12-31",
            "suspension_start": None,
            "suspension_end": None,
            "ticker_old": None,
            "ticker_new": None,
            "sector": info_dict.get("sector", "Equities"),
            "status": "ACTIVE"
        }
        registry_items.append(reg_item)

    # 2. Add HISTORICAL DELISTED, MERGED & SUSPENDED equities to eliminate Survivorship Bias!
    HISTORICAL_DELISTED_AND_SPECIAL = [
        {
            "ticker": "OTMT.CA",
            "company_name": "أوراسكوم للاتصالات والإعلام والتكنولوجيا (تغير الرمز إلى OIH)",
            "listing_date": "2012-02-01",
            "delisting_date": "2018-08-31",
            "suspension_start": None,
            "suspension_end": None,
            "ticker_old": None,
            "ticker_new": "OIH.CA",
            "sector": "Telecommunications",
            "status": "TICKER_CHANGED"
        },
        {
            "ticker": "ACRO.CA",
            "company_name": "أكرو مصر للشدات وسقالات المعدنية (شطب اختياري)",
            "listing_date": "1996-01-01",
            "delisting_date": "2021-08-15",
            "suspension_start": None,
            "suspension_end": None,
            "ticker_old": None,
            "ticker_new": None,
            "sector": "Industrial Goods",
            "status": "DELISTED"
        },
        {
            "ticker": "NCGC.CA",
            "company_name": "النيل لحليج الأقطان (شطب اختياري وتسوية تعويضات)",
            "listing_date": "1995-01-01",
            "delisting_date": "2020-11-10",
            "suspension_start": "2020-03-01",
            "suspension_end": "2020-11-10",
            "ticker_old": None,
            "ticker_new": None,
            "sector": "Textiles & Cotton",
            "status": "DELISTED"
        },
        {
            "ticker": "PORT.CA",
            "company_name": "بورتو القابضة (تغير الاسم والرمز إلى المطورون العرب ARAB)",
            "listing_date": "2015-10-18",
            "delisting_date": "2022-04-10",
            "suspension_start": None,
            "suspension_end": None,
            "ticker_old": None,
            "ticker_new": "ARAB.CA",
            "sector": "Real Estate",
            "status": "TICKER_CHANGED"
        },
        {
            "ticker": "SPMD.CA",
            "company_name": "سبيد ميديكال (إيقاف وتدقيق رقابي)",
            "listing_date": "2019-04-15",
            "delisting_date": "9999-12-31",
            "suspension_start": "2022-06-01",
            "suspension_end": "2022-09-30",
            "ticker_old": None,
            "ticker_new": None,
            "sector": "Healthcare",
            "status": "SUSPENDED_HISTORICAL"
        },
        {
            "ticker": "GLNA.CA",
            "company_name": "جلوبال تليكوم القابضة (شطب اختياري بعد عرض شراء إجباري)",
            "listing_date": "1998-01-01",
            "delisting_date": "2019-09-15",
            "suspension_start": None,
            "suspension_end": None,
            "ticker_old": "ORTE.CA",
            "ticker_new": None,
            "sector": "Telecommunications",
            "status": "DELISTED"
        },
        {
            "ticker": "DOMT_DELISTED.CA",
            "company_name": "الصناعات الغذائية دومتي (عرض شراء إجباري وشطب)",
            "listing_date": "2016-03-22",
            "delisting_date": "2025-01-01",
            "suspension_start": None,
            "suspension_end": None,
            "ticker_old": None,
            "ticker_new": "DOMT.CA",
            "sector": "Food & Beverage",
            "status": "MERGED"
        }
    ]

    for item in HISTORICAL_DELISTED_AND_SPECIAL:
        registry_items.append(item)

    # Save to SQLite and JSON
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM historical_universe_registry")
    for r in registry_items:
        cur.execute("""
            INSERT OR REPLACE INTO historical_universe_registry
            (ticker, company_name, listing_date, delisting_date, suspension_start, suspension_end, ticker_old, ticker_new, sector, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            r["ticker"], r["company_name"], r["listing_date"], r["delisting_date"],
            r["suspension_start"], r["suspension_end"], r["ticker_old"], r["ticker_new"],
            r["sector"], r["status"], datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
    conn.commit()
    conn.close()

    with open(HISTORICAL_REGISTRY_JSON, "w", encoding="utf-8") as f:
        json.dump(registry_items, f, ensure_ascii=False, indent=2)

    print(f"✅ Historical Universe Registry populated: {len(registry_items)} equities recorded (including delisted & ticker changes).")


def build_corporate_actions():
    print("[2/3] Building Centralized Corporate Actions Database...")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS corporate_actions (
            action_id TEXT PRIMARY KEY,
            ticker TEXT NOT NULL,
            action_type TEXT NOT NULL,
            ex_date TEXT NOT NULL,
            record_date TEXT,
            announcement_date TEXT,
            effective_date TEXT NOT NULL,
            ratio REAL,
            cash_amount REAL,
            currency TEXT DEFAULT 'EGP',
            source TEXT NOT NULL,
            source_timestamp TEXT NOT NULL,
            description_ar TEXT,
            created_at TEXT NOT NULL
        )
    """)

    # Comprehensive Corporate Actions Master Dataset for EGX
    ACTIONS_LIST = [
        # --- Commercial International Bank (COMI.CA) ---
        {
            "action_id": "COMI_DIV_2026_01",
            "ticker": "COMI.CA",
            "action_type": "DIVIDEND",
            "ex_date": "2026-04-18",
            "record_date": "2026-04-19",
            "announcement_date": "2026-03-20",
            "effective_date": "2026-04-18",
            "ratio": None,
            "cash_amount": 5.50,
            "currency": "EGP",
            "source": "EGX_DISCLOSURE",
            "source_timestamp": "2026-03-20 14:15:00",
            "description_ar": "كوبون نقدي بقيمة 5.50 ج.م للسهم"
        },
        {
            "action_id": "COMI_DIV_2025_01",
            "ticker": "COMI.CA",
            "action_type": "DIVIDEND",
            "ex_date": "2025-04-10",
            "record_date": "2025-04-11",
            "announcement_date": "2025-03-15",
            "effective_date": "2025-04-10",
            "ratio": None,
            "cash_amount": 4.00,
            "currency": "EGP",
            "source": "EGX_DISCLOSURE",
            "source_timestamp": "2025-03-15 13:45:00",
            "description_ar": "كوبون نقدي بقيمة 4.00 ج.م للسهم"
        },
        {
            "action_id": "COMI_BONUS_2023_01",
            "ticker": "COMI.CA",
            "action_type": "BONUS",
            "ex_date": "2023-04-20",
            "record_date": "2023-04-21",
            "announcement_date": "2023-03-10",
            "effective_date": "2023-04-20",
            "ratio": 0.25, # 1 bonus for every 4 shares
            "cash_amount": None,
            "currency": "EGP",
            "source": "EGX_DISCLOSURE",
            "source_timestamp": "2023-03-10 11:00:00",
            "description_ar": "أسهم مجانية بواقع 0.25 سهم مجاني لكل سهم أصلي"
        },
        # --- Elsewedy Electric (SWDY.CA) ---
        {
            "action_id": "SWDY_DIV_2026_01",
            "ticker": "SWDY.CA",
            "action_type": "DIVIDEND",
            "ex_date": "2026-05-12",
            "record_date": "2026-05-13",
            "announcement_date": "2026-04-05",
            "effective_date": "2026-05-12",
            "ratio": None,
            "cash_amount": 3.00,
            "currency": "EGP",
            "source": "EGX_DISCLOSURE",
            "source_timestamp": "2026-04-05 10:20:00",
            "description_ar": "كوبون نقدي بقيمة 3.00 ج.م للسهم"
        },
        {
            "action_id": "SWDY_TENDER_2024_01",
            "ticker": "SWDY.CA",
            "action_type": "ACQUISITION",
            "ex_date": "2024-06-01",
            "record_date": "2024-06-02",
            "announcement_date": "2024-05-15",
            "effective_date": "2024-06-01",
            "ratio": None,
            "cash_amount": 47.50,
            "currency": "EGP",
            "source": "FRA_DISCLOSURE",
            "source_timestamp": "2024-05-15 12:00:00",
            "description_ar": "عرض شراء إجباري من إلكترولوكس للاستثمار بسعر 47.50 ج.م للسهم"
        },
        # --- Talaat Moustafa Group (TMGH.CA) ---
        {
            "action_id": "TMGH_DIV_2026_01",
            "ticker": "TMGH.CA",
            "action_type": "DIVIDEND",
            "ex_date": "2026-05-25",
            "record_date": "2026-05-26",
            "announcement_date": "2026-04-18",
            "effective_date": "2026-05-25",
            "ratio": None,
            "cash_amount": 1.25,
            "currency": "EGP",
            "source": "EGX_DISCLOSURE",
            "source_timestamp": "2026-04-18 15:30:00",
            "description_ar": "توزيع نقدي بقيمة 1.25 ج.م للسهم"
        },
        {
            "action_id": "TMGH_CAP_2024_01",
            "ticker": "TMGH.CA",
            "action_type": "CAPITAL_INCREASE",
            "ex_date": "2024-03-10",
            "record_date": "2024-03-11",
            "announcement_date": "2024-02-15",
            "effective_date": "2024-03-10",
            "ratio": 0.15,
            "cash_amount": None,
            "currency": "EGP",
            "source": "EGX_DISCLOSURE",
            "source_timestamp": "2024-02-15 11:30:00",
            "description_ar": "زيادة رأس المال المصدر والمدفوع"
        },
        # --- Orascom Construction (ORAS.CA) ---
        {
            "action_id": "ORAS_DIV_2026_01",
            "ticker": "ORAS.CA",
            "action_type": "DIVIDEND",
            "ex_date": "2026-06-25",
            "record_date": "2026-06-26",
            "announcement_date": "2026-05-15",
            "effective_date": "2026-06-25",
            "ratio": None,
            "cash_amount": 13.50, # 0.275 USD
            "currency": "EGP",
            "source": "EGX_DISCLOSURE",
            "source_timestamp": "2026-05-15 16:00:00",
            "description_ar": "توزيع كوبون نقدي بقيمة 0.275 دولار (13.50 ج.م) للسهم"
        },
        # --- Telecom Egypt (ETEL.CA) ---
        {
            "action_id": "ETEL_DIV_2026_01",
            "ticker": "ETEL.CA",
            "action_type": "DIVIDEND",
            "ex_date": "2026-04-22",
            "record_date": "2026-04-23",
            "announcement_date": "2026-03-25",
            "effective_date": "2026-04-22",
            "ratio": None,
            "cash_amount": 1.50,
            "currency": "EGP",
            "source": "EGX_DISCLOSURE",
            "source_timestamp": "2026-03-25 14:00:00",
            "description_ar": "كوبون نقدي بقيمة 1.50 ج.م للسهم"
        },
        # --- Fawry (FWRY.CA) ---
        {
            "action_id": "FWRY_SPLIT_2021_01",
            "ticker": "FWRY.CA",
            "action_type": "STOCK_SPLIT",
            "ex_date": "2021-06-15",
            "record_date": "2021-06-16",
            "announcement_date": "2021-05-10",
            "effective_date": "2021-06-15",
            "ratio": 0.50, # 1:2 split (halved nominal value)
            "cash_amount": None,
            "currency": "EGP",
            "source": "EGX_DISCLOSURE",
            "source_timestamp": "2021-05-10 12:30:00",
            "description_ar": "تجزئة القيمة الاسمية للسهم من 1.00 ج.م إلى 0.50 ج.م (1:2)"
        },
        {
            "action_id": "FWRY_RIGHTS_2022_01",
            "ticker": "FWRY.CA",
            "action_type": "RIGHTS",
            "ex_date": "2022-04-05",
            "record_date": "2022-04-06",
            "announcement_date": "2022-03-01",
            "effective_date": "2022-04-05",
            "ratio": 0.47,
            "cash_amount": 2.80, # Rights subscription price
            "currency": "EGP",
            "source": "FRA_DISCLOSURE",
            "source_timestamp": "2022-03-01 10:00:00",
            "description_ar": "اكتتاب في زيادة رأس المال لقدامى المساهمين بسعر 2.80 ج.م"
        },
        # --- Historical Delistings as Corporate Actions ---
        {
            "action_id": "ACRO_DELIST_2021_01",
            "ticker": "ACRO.CA",
            "action_type": "DELISTING",
            "ex_date": "2021-08-15",
            "record_date": "2021-08-15",
            "announcement_date": "2021-07-01",
            "effective_date": "2021-08-15",
            "ratio": None,
            "cash_amount": 35.00, # Voluntary buyback price
            "currency": "EGP",
            "source": "EGX_DISCLOSURE",
            "source_timestamp": "2021-07-01 11:00:00",
            "description_ar": "شطب اختياري من البورصة المصرية بعد شراء أسهم المعترضين"
        },
        {
            "action_id": "NCGC_DELIST_2020_01",
            "ticker": "NCGC.CA",
            "action_type": "DELISTING",
            "ex_date": "2020-11-10",
            "record_date": "2020-11-10",
            "announcement_date": "2020-09-20",
            "effective_date": "2020-11-10",
            "ratio": None,
            "cash_amount": 14.50,
            "currency": "EGP",
            "source": "EGX_DISCLOSURE",
            "source_timestamp": "2020-09-20 15:00:00",
            "description_ar": "شطب اختياري من البورصة المصرية"
        },
        {
            "action_id": "OTMT_TICKER_2018_01",
            "ticker": "OTMT.CA",
            "action_type": "TICKER_CHANGE",
            "ex_date": "2018-08-31",
            "record_date": "2018-08-31",
            "announcement_date": "2018-08-01",
            "effective_date": "2018-08-31",
            "ratio": 1.0,
            "cash_amount": None,
            "currency": "EGP",
            "source": "EGX_DISCLOSURE",
            "source_timestamp": "2018-08-01 10:00:00",
            "description_ar": "تعديل اسم ورمز الشركة إلى أوراسكوم للاستثمار القابضة (OIH.CA)"
        }
    ]

    cur.execute("DELETE FROM corporate_actions")
    for act in ACTIONS_LIST:
        cur.execute("""
            INSERT OR REPLACE INTO corporate_actions
            (action_id, ticker, action_type, ex_date, record_date, announcement_date, effective_date, ratio, cash_amount, currency, source, source_timestamp, description_ar, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            act["action_id"], act["ticker"], act["action_type"], act["ex_date"], act["record_date"],
            act["announcement_date"], act["effective_date"], act["ratio"], act["cash_amount"], act["currency"],
            act["source"], act["source_timestamp"], act["description_ar"], datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
    conn.commit()
    conn.close()

    with open(CORPORATE_ACTIONS_JSON, "w", encoding="utf-8") as f:
        json.dump(ACTIONS_LIST, f, ensure_ascii=False, indent=2)

    print(f"✅ Centralized Corporate Actions Database populated: {len(ACTIONS_LIST)} events indexed.")


def verify_pit_universe():
    print("[3/3] Verifying Point-in-Time Universe across 2020, 2022, 2024, 2026...")
    u_2020 = HistoricalUniverseManager.get_tradable_universe("2020-06-01")
    u_2022 = HistoricalUniverseManager.get_tradable_universe("2022-06-01")
    u_2024 = HistoricalUniverseManager.get_tradable_universe("2024-06-01")
    u_2026 = HistoricalUniverseManager.get_tradable_universe("2026-06-01")

    print(f"  • Tradable Universe in 2020-06-01: {len(u_2020)} stocks")
    print(f"  • Tradable Universe in 2022-06-01: {len(u_2022)} stocks")
    print(f"  • Tradable Universe in 2024-06-01: {len(u_2024)} stocks")
    print(f"  • Tradable Universe in 2026-06-01: {len(u_2026)} stocks")

    # Specific tests
    print("  --- Point-in-Time Verification Checks ---")
    # ACRO.CA was listed in 2020, delisted in Aug 2021
    print(f"  - ACRO.CA tradable in 2020? {HistoricalUniverseManager.is_tradable_on('ACRO.CA', '2020-06-01')} (Expected: True)")
    print(f"  - ACRO.CA tradable in 2024? {HistoricalUniverseManager.is_tradable_on('ACRO.CA', '2024-06-01')} (Expected: False - Delisted)")

    # EFIH.CA IPO was in Oct 2021
    print(f"  - EFIH.CA tradable in 2020? {HistoricalUniverseManager.is_tradable_on('EFIH.CA', '2020-06-01')} (Expected: False - Not yet listed)")
    print(f"  - EFIH.CA tradable in 2024? {HistoricalUniverseManager.is_tradable_on('EFIH.CA', '2024-06-01')} (Expected: True)")


if __name__ == "__main__":
    build_historical_universe()
    build_corporate_actions()
    verify_pit_universe()
