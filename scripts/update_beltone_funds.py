#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/update_beltone_funds.py
================================
Enriches Thndr mutual funds catalog with Beltone Asset Management funds
and synchronizes to SQLite production database.
"""

import os
import sys
import json
import sqlite3

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(WORKSPACE, "data")
JSON_PATH = os.path.join(DATA_DIR, "thndr_mutual_funds.json")
DB_PATH = os.path.join(DATA_DIR, "gen26_production.db")

NEW_BELTONE_FUNDS = [
    {
        "fund_id": "FUND_BELTONE_CASH",
        "ticker": "BELTONE-CASH",
        "name_ar": "صندوق بيلتون للسيولة النقدية اليومية (Beltone Cash Fund)",
        "name_en": "Beltone Daily Cash Liquidity Fund",
        "category": "MONEY_MARKET",
        "category_ar": "أسواق نقد ودخل ثابت",
        "manager": "بيلتون لإدارة صناديق الاستثمار (Beltone Asset Management)",
        "sponsor": "بيلتون المالية القابضة / ثاندر توفير",
        "nav_egp": 12.15,
        "ytd_return_pct": 20.5,
        "annual_return_pct": 21.2,
        "risk_level": "LOW",
        "risk_level_ar": "منخفضة جداً",
        "liquidity": "DAILY_T0",
        "liquidity_ar": "يومي فوري (T+0)",
        "sharia_compliant": False,
        "expense_ratio_pct": 0.75,
        "min_investment_egp": 50.0,
        "description_ar": "صندوق نقد يومي مركب معفى من الضرائب يستثمر في أذون وسندات الخزانة وسوق النقد، متاح عبر تطبيق ثاندر مع سيولة سحب وإيداع يومية فورية T+0 وعائد يقارب فائدة البنك المركزي (21.2%)."
    },
    {
        "fund_id": "FUND_BELTONE_EQUITY",
        "ticker": "BELTONE-EQUITY",
        "name_ar": "صندوق بيلتون للأسهم المصرية (Beltone Equity Fund)",
        "name_en": "Beltone Egyptian Equity Fund",
        "category": "EQUITY",
        "category_ar": "أسهم ونمو رأسمالي",
        "manager": "بيلتون لإدارة صناديق الاستثمار (Beltone Asset Management)",
        "sponsor": "بيلتون المالية القابضة",
        "nav_egp": 45.60,
        "ytd_return_pct": 41.5,
        "annual_return_pct": 45.2,
        "risk_level": "HIGH",
        "risk_level_ar": "مرتفعة",
        "liquidity": "WEEKLY",
        "liquidity_ar": "أسبوعي (T+2)",
        "sharia_compliant": False,
        "expense_ratio_pct": 1.75,
        "min_investment_egp": 100.0,
        "description_ar": "صندوق استثمار نشط في الأسهم المصرية يستهدف تحقيق أعلى نمو رأسمالي عبر الاستثمار في كبرى الشركات القيادية وأسهم القيمة والنمو بالبورصة المصرية."
    },
    {
        "fund_id": "FUND_BELTONE_SUKUK",
        "ticker": "BELTONE-SUKUK",
        "name_ar": "صندوق بيلتون للصكوك والدخل الثابت الإسلامي",
        "name_en": "Beltone Islamic Sukuk & Fixed Income Fund",
        "category": "ISLAMIC_SHARIA",
        "category_ar": "إسلامي متوافق مع الشريعة",
        "manager": "بيلتون لإدارة صناديق الاستثمار (Beltone Asset Management)",
        "sponsor": "بيلتون المالية القابضة",
        "nav_egp": 16.80,
        "ytd_return_pct": 21.2,
        "annual_return_pct": 22.0,
        "risk_level": "LOW",
        "risk_level_ar": "منخفضة",
        "liquidity": "DAILY_T1",
        "liquidity_ar": "يومي (T+1)",
        "sharia_compliant": True,
        "expense_ratio_pct": 0.95,
        "min_investment_egp": 50.0,
        "description_ar": "صندوق استثمار متوافق تماماً مع الشريعة الإسلامية يستثمر في الصكوك الحكومية وصكوك الشركات وأدوات السيولة ذات العائد الدوري الحلال."
    }
]


def update_funds():
    if not os.path.exists(JSON_PATH):
        print(f"Error: {JSON_PATH} not found.")
        return

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    funds = data.get("funds", [])
    existing_ids = {f["fund_id"] for f in funds}
    added_count = 0

    for nf in NEW_BELTONE_FUNDS:
        if nf["fund_id"] not in existing_ids:
            funds.append(nf)
            existing_ids.add(nf["fund_id"])
            added_count += 1
            print(f"[+] Added Beltone fund: {nf['ticker']} - {nf['name_ar']}")
        else:
            # Update existing
            for idx, existing in enumerate(funds):
                if existing["fund_id"] == nf["fund_id"]:
                    funds[idx] = nf
                    print(f"[*] Updated Beltone fund: {nf['ticker']}")

    # Enhance search keywords for existing Beltone Sabaek Gold fund
    for f in funds:
        if f.get("fund_id") == "FUND_BELTONE_SABAEK":
            f["name_ar"] = "صندوق بيلتون سبائك للذهب (Beltone Sabaek Gold)"
            f["manager"] = "بيلتون لإدارة الأصول (Beltone Asset Management)"
        elif f.get("fund_id") == "FUND_BELTONE_BCASH":
            f["name_ar"] = "صندوق بيلتون كاش للسيولة (B-Cash)"
            f["manager"] = "بيلتون لإدارة الأصول (Beltone Asset Management)"
        elif f.get("fund_id") == "FUND_BELTONE_BSECURE":
            f["name_ar"] = "صندوق بيلتون بي سيكيور للدخل الثابت (B-Secure)"
            f["manager"] = "بيلتون لإدارة الأصول (Beltone Asset Management)"

    data["funds"] = funds
    data["total_funds"] = len(funds)
    cats = data.get("categories", {})
    cats["GOLD"] = sum(1 for f in funds if f.get("category") == "GOLD")
    cats["MONEY_MARKET"] = sum(1 for f in funds if f.get("category") == "MONEY_MARKET")
    cats["EQUITY"] = sum(1 for f in funds if f.get("category") == "EQUITY")
    cats["ISLAMIC_SHARIA"] = sum(1 for f in funds if f.get("category") == "ISLAMIC_SHARIA")
    cats["BALANCED"] = sum(1 for f in funds if f.get("category") == "BALANCED")
    cats["ETF_AND_BONDS"] = sum(1 for f in funds if f.get("category") in ("ETF", "FIXED_INCOME"))
    data["categories"] = cats

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[SUCCESS] JSON updated: total {len(funds)} funds saved to {JSON_PATH}")

    # Synchronize to SQLite
    if os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS mutual_funds (
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
        )""")
        for f in funds:
            cur.execute("""INSERT OR REPLACE INTO mutual_funds VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )""", (
                f["fund_id"], f["ticker"], f["name_ar"], f["name_en"],
                f["category"], f["category_ar"], f["manager"], f["sponsor"],
                f["nav_egp"], f["ytd_return_pct"], f["annual_return_pct"],
                f["risk_level"], f["liquidity"], 1 if f["sharia_compliant"] else 0,
                f["expense_ratio_pct"], f["min_investment_egp"], f["description_ar"]
            ))
        conn.commit()
        conn.close()
        print(f"[SUCCESS] Synchronized {len(funds)} funds into SQLite database table 'mutual_funds'")


if __name__ == "__main__":
    update_funds()
