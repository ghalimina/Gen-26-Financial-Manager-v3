#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/sync_thndr_funds.py — Complete Audit and Sync of Egyptian & Thndr Mutual Funds
Hydrates major equity and Islamic Sharia funds into data/thndr_mutual_funds.json
and synchronizes SQLite mutual_funds table in data/gen26_production.db.
"""

import os
import sys
import json
import sqlite3
from collections import Counter

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_PATH = os.path.join(WORKSPACE, "data", "thndr_mutual_funds.json")
DB_PATH = os.path.join(WORKSPACE, "data", "gen26_production.db")

NEW_FUNDS = [
    {
        "fund_id": "FUND_AZ_EQUITY",
        "ticker": "AZ-EQUITY",
        "name_ar": "صندوق أزيموت للأسهم المصرية (فرص مصر - AZ Equity)",
        "name_en": "Azimut Egypt Equity Opportunities Fund (AZ Equity)",
        "category": "EQUITY",
        "category_ar": "أسهم ونمو رأسمالي",
        "manager": "أزيموت مصر (Azimut Egypt)",
        "sponsor": "أزيموت مصر / بنك القاهرة",
        "nav_egp": 39.40,
        "ytd_return_pct": 32.8,
        "annual_return_pct": 36.5,
        "risk_level": "HIGH",
        "risk_level_ar": "عالية المخاطر",
        "liquidity": "DAILY_T2",
        "liquidity_ar": "يومي (T+2)",
        "sharia_compliant": False,
        "expense_ratio_pct": 1.75,
        "min_investment_egp": 100.0,
        "description_ar": "صندوق استثمار في الأسهم المصرية يركز على اقتناص فرص النمو والقيمة الرأسمالية في كبرى شركات بورصة مصر متاح عبر منصة ثاندر."
    },
    {
        "fund_id": "FUND_CIB_EQUITY",
        "ticker": "CIB-EQUITY",
        "name_ar": "صندوق استثمار البنك التجاري الدولي للأسهم (CIB Equity - استثمار)",
        "name_en": "CIB Equity Growth Fund (Istithmar)",
        "category": "EQUITY",
        "category_ar": "أسهم ونمو رأسمالي",
        "manager": "سي آي كابيتال (CI Capital)",
        "sponsor": "البنك التجاري الدولي (CIB)",
        "nav_egp": 312.50,
        "ytd_return_pct": 31.5,
        "annual_return_pct": 35.8,
        "risk_level": "HIGH",
        "risk_level_ar": "عالية المخاطر",
        "liquidity": "WEEKLY_T2",
        "liquidity_ar": "أسبوعي (T+2)",
        "sharia_compliant": False,
        "expense_ratio_pct": 1.8,
        "min_investment_egp": 500.0,
        "description_ar": "أحد أكبر وأعرق صناديق الأسهم المصرية، يستثمر في محفظة متنوعة من كبرى أسهم مؤشر EGX30 والشركات القيادية."
    },
    {
        "fund_id": "FUND_HRM_HORUS",
        "ticker": "HRM-HORUS",
        "name_ar": "صندوق حورس للأسهم المصرية (إي إف جي هيرميس)",
        "name_en": "Horus Egyptian Equity Fund (EFG Hermes)",
        "category": "EQUITY",
        "category_ar": "أسهم ونمو رأسمالي",
        "manager": "إي إف جي هيرميس (EFG Hermes)",
        "sponsor": "المجموعة المالية هيرميس",
        "nav_egp": 78.90,
        "ytd_return_pct": 33.4,
        "annual_return_pct": 37.1,
        "risk_level": "HIGH",
        "risk_level_ar": "عالية المخاطر",
        "liquidity": "WEEKLY_T2",
        "liquidity_ar": "أسبوعي (T+2)",
        "sharia_compliant": False,
        "expense_ratio_pct": 1.85,
        "min_investment_egp": 500.0,
        "description_ar": "صندوق أسهم استثماري نشط يهدف لتحقيق نمو رأسمالي متسارع عبر اقتناص أسهم النمو والزخم المؤسسي في بورصة مصر."
    },
    {
        "fund_id": "FUND_NBE_BASH",
        "ticker": "NBE-BASH",
        "name_ar": "صندوق البنك الأهلي المصري وبنك التنمية والائتمان الزراعي للأسهم الإسلامية (بشاير)",
        "name_en": "NBE Sharia Equity Fund (Bashayer)",
        "category": "ISLAMIC_SHARIA",
        "category_ar": "أسهم إسلامية وشريعة",
        "manager": "الأهلي لإدارة الاستثمارات المالية",
        "sponsor": "البنك الأهلي المصري",
        "nav_egp": 128.40,
        "ytd_return_pct": 29.8,
        "annual_return_pct": 33.2,
        "risk_level": "HIGH",
        "risk_level_ar": "عالية المخاطر",
        "liquidity": "WEEKLY_T2",
        "liquidity_ar": "أسبوعي (T+2)",
        "sharia_compliant": True,
        "expense_ratio_pct": 1.75,
        "min_investment_egp": 200.0,
        "description_ar": "صندوق استثماري في الأسهم المصرية المتوافقة مع أحكام الشريعة الإسلامية والمعتمدة من الهيئة الشرعية للبنك الأهلي."
    },
    {
        "fund_id": "FUND_BM_HOSN",
        "ticker": "BM-HOSN",
        "name_ar": "صندوق بنك مصر للأسهم المتوافقة مع الشريعة الإسلامية (الحصن)",
        "name_en": "Banque Misr Islamic Equity Fund (Al Hosn)",
        "category": "ISLAMIC_SHARIA",
        "category_ar": "أسهم إسلامية وشريعة",
        "manager": "مصر كابيتال (Misr Capital)",
        "sponsor": "بنك مصر",
        "nav_egp": 165.20,
        "ytd_return_pct": 28.5,
        "annual_return_pct": 32.1,
        "risk_level": "HIGH",
        "risk_level_ar": "عالية المخاطر",
        "liquidity": "WEEKLY_T2",
        "liquidity_ar": "أسبوعي (T+2)",
        "sharia_compliant": True,
        "expense_ratio_pct": 1.6,
        "min_investment_egp": 250.0,
        "description_ar": "صندوق استثماري إسلامي تراكمي يستثمر في أسهم الشركات المصرية المجازة شرعياً مع توزيعات دورية للأرباح."
    },
    {
        "fund_id": "FUND_SANABEL_EQ",
        "ticker": "SANABEL-EQ",
        "name_ar": "صندوق سنابل للأسهم المتوافقة مع الشريعة الإسلامية",
        "name_en": "Sanabel Sharia Compliant Equity Fund",
        "category": "ISLAMIC_SHARIA",
        "category_ar": "أسهم إسلامية وشريعة",
        "manager": "برايم كابيتال (Prime Capital)",
        "sponsor": "بنك الشركة المصرفية العربية الدولية (saib)",
        "nav_egp": 215.30,
        "ytd_return_pct": 30.2,
        "annual_return_pct": 34.0,
        "risk_level": "HIGH",
        "risk_level_ar": "عالية المخاطر",
        "liquidity": "WEEKLY_T2",
        "liquidity_ar": "أسبوعي (T+2)",
        "sharia_compliant": True,
        "expense_ratio_pct": 1.7,
        "min_investment_egp": 200.0,
        "description_ar": "صندوق أسهم متوافق مع أحكام الشريعة الإسلامية يستثمر في محفظة منتقاة من الأسهم المصرية ذات الأداء المالي القوي."
    }
]


def sync_funds():
    if not os.path.exists(JSON_PATH):
        print(f"[ERROR] JSON file not found at {JSON_PATH}")
        return False

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    funds = data.get("funds", [])
    fund_map = {f["fund_id"]: f for f in funds}
    ticker_map = {f["ticker"]: f for f in funds}

    # 1. Update existing funds with enriched names
    if "BM-2" in ticker_map:
        ticker_map["BM-2"]["name_ar"] = "صندوق بنك مصر الثاني للنمو الرأسمالي (العمر)"
        ticker_map["BM-2"]["description_ar"] = "صندوق استثماري في الأسهم المصرية يهدف لنمو رأس المال على المدى الطويل (العمر)."
    if "NBE-5" in ticker_map:
        ticker_map["NBE-5"]["name_ar"] = "صندوق البنك الأهلي الخامس للأسهم الإسلامية (هلال)"
        ticker_map["NBE-5"]["description_ar"] = "صندوق استثمار إسلامي في الأسهم المصرية المتوافقة مع الشريعة الإسلامية (هلال)."
    if "CIB-IST" in ticker_map:
        ticker_map["CIB-IST"]["name_ar"] = "صندوق البنك التجاري الدولي للأسهم (استثمار)"

    # 2. Add new funds
    added_count = 0
    for nf in NEW_FUNDS:
        fid = nf["fund_id"]
        tick = nf["ticker"]
        if fid not in fund_map and tick not in ticker_map:
            funds.append(nf)
            fund_map[fid] = nf
            ticker_map[tick] = nf
            added_count += 1
            print(f"[ADD] Added new fund: {nf['ticker']} - {nf['name_ar']}")
        else:
            existing = fund_map.get(fid) or ticker_map.get(tick)
            existing.update(nf)
            print(f"[UPDATE] Updated fund: {existing['ticker']} - {existing['name_ar']}")

    # 3. Update category counters and metadata
    data["funds"] = funds
    data["total_funds"] = len(funds)
    cats = Counter(f.get("category") for f in funds)
    
    data["categories"] = {
        "GOLD": cats.get("GOLD", 0),
        "MONEY_MARKET": cats.get("MONEY_MARKET", 0),
        "EQUITY": cats.get("EQUITY", 0),
        "ISLAMIC_SHARIA": cats.get("ISLAMIC_SHARIA", 0),
        "BALANCED": cats.get("BALANCED", 0),
        "ETF_AND_BONDS": cats.get("ETF", 0) + cats.get("FIXED_INCOME", 0)
    }

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[SUCCESS] JSON file updated. Total funds: {len(funds)} (Added: {added_count})")
    print(f"Categories distribution: {dict(cats)}")

    # 4. Synchronize SQLite mutual_funds table
    if os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS mutual_funds (
                fund_id TEXT PRIMARY KEY,
                ticker TEXT,
                name_ar TEXT,
                name_en TEXT,
                category TEXT,
                category_ar TEXT,
                manager TEXT,
                sponsor TEXT,
                nav_egp REAL,
                ytd_return_pct REAL,
                annual_return_pct REAL,
                risk_level TEXT,
                liquidity TEXT,
                sharia_compliant INTEGER,
                expense_ratio_pct REAL,
                min_investment_egp REAL,
                description_ar TEXT
            )
        """)

        for f in funds:
            cur.execute("""
                INSERT OR REPLACE INTO mutual_funds (
                    fund_id, ticker, name_ar, name_en, category, category_ar,
                    manager, sponsor, nav_egp, ytd_return_pct, annual_return_pct,
                    risk_level, liquidity, sharia_compliant, expense_ratio_pct,
                    min_investment_egp, description_ar
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                f.get("fund_id"),
                f.get("ticker"),
                f.get("name_ar"),
                f.get("name_en"),
                f.get("category"),
                f.get("category_ar"),
                f.get("manager"),
                f.get("sponsor"),
                float(f.get("nav_egp", 0.0)),
                float(f.get("ytd_return_pct", 0.0)),
                float(f.get("annual_return_pct", 0.0)),
                f.get("risk_level"),
                f.get("liquidity"),
                1 if f.get("sharia_compliant") else 0,
                float(f.get("expense_ratio_pct", 0.0)),
                float(f.get("min_investment_egp", 0.0)),
                f.get("description_ar")
            ))

        conn.commit()
        cur.execute("SELECT COUNT(*) FROM mutual_funds")
        db_count = cur.fetchone()[0]
        cur.execute("SELECT category, COUNT(*) FROM mutual_funds GROUP BY category")
        db_cats = cur.fetchall()
        conn.close()

        print(f"[SUCCESS] SQLite mutual_funds table synchronized. Total in DB: {db_count}")
        print(f"DB Categories distribution: {db_cats}")

    return True


if __name__ == "__main__":
    sync_funds()
