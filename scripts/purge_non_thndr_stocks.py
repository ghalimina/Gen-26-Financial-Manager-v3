#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# scripts/purge_non_thndr_stocks.py
# Reconciles and synchronizes the entire database universe strictly with Thndr.
# Removes all artificial/preferred/bond suffixes (_P.CA, _B.CA, DELIST1.CA)
# and ensures all 181 real active EGX common equities on Thndr are present.
# =============================================================================

import os
import sys
import json
import sqlite3
import datetime

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

THNDR_UNIVERSE_FILE = os.path.join(WORKSPACE, "data", "thndr_egx_244_universe.json")
CANONICAL_PRICES_FILE = os.path.join(WORKSPACE, "data", "canonical_prices_live.json")
MARKET_DB = os.path.join(WORKSPACE, "data", "gen26_market.db")
PRODUCTION_DB = os.path.join(WORKSPACE, "data", "gen26_production.db")


def purge_and_sync_thndr_universe():
    print("=" * 80)
    print("GEN-26: PURGING NON-THNDR STOCKS & RECONCILING WITH OFFICIAL THNDR UNIVERSE")
    print("=" * 80)

    # 1. Load verified Thndr universe
    with open(THNDR_UNIVERSE_FILE, "r", encoding="utf-8") as f:
        thndr_data = json.load(f)

    thndr_stocks = thndr_data.get("stocks", [])
    thndr_tickers = set(s["ticker"].upper().strip() for s in thndr_stocks)
    print(f"Verified Thndr Active Tickers Catalog: {len(thndr_tickers)} equities.")

    # 2. Clean data/gen26_market.db
    if os.path.exists(MARKET_DB):
        conn_m = sqlite3.connect(MARKET_DB)
        cur_m = conn_m.cursor()

        # Delete non-Thndr stocks from stocks_universe
        cur_m.execute("SELECT ticker FROM stocks_universe;")
        existing_mkt = [r[0] for r in cur_m.fetchall()]
        to_delete_mkt = [t for t in existing_mkt if t not in thndr_tickers]
        if to_delete_mkt:
            cur_m.execute(f"DELETE FROM stocks_universe WHERE ticker IN ({','.join(['?']*len(to_delete_mkt))})", to_delete_mkt)
            print(f"gen26_market.db: Purged {len(to_delete_mkt)} non-Thndr tickers from stocks_universe.")

        # Ensure all 181 stocks exist in stocks_universe
        for s in thndr_stocks:
            cur_m.execute("""
                INSERT OR REPLACE INTO stocks_universe (
                    ticker, symbol, name_ar, name_en, sector, sector_en, isin,
                    market_cap_tier, thndr_available, is_active, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, 1, ?);
            """, (
                s["ticker"], s["symbol"], s["name_ar"], s["name_en"], s["sector"],
                s.get("sector_en", s["sector"]), s["isin"], s.get("market_cap_tier", "MID_CAP"),
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))

        # Delete non-Thndr stocks from live_prices
        cur_m.execute(f"DELETE FROM live_prices WHERE ticker NOT IN ({','.join(['?']*len(thndr_tickers))})", list(thndr_tickers))

        # Delete non-Thndr stocks from prediction_vs_actual
        cur_m.execute(f"DELETE FROM prediction_vs_actual WHERE ticker NOT IN ({','.join(['?']*len(thndr_tickers))})", list(thndr_tickers))

        conn_m.commit()
        conn_m.close()
        print("gen26_market.db: Successfully reconciled and updated all tables with Thndr.")

    # 3. Clean data/gen26_production.db
    if os.path.exists(PRODUCTION_DB):
        conn_p = sqlite3.connect(PRODUCTION_DB)
        cur_p = conn_p.cursor()

        # Delete non-Thndr stocks from stocks
        cur_p.execute("SELECT ticker FROM stocks;")
        existing_prod = [r[0] for r in cur_p.fetchall()]
        to_delete_prod = [t for t in existing_prod if t not in thndr_tickers]
        if to_delete_prod:
            cur_p.execute(f"DELETE FROM stocks WHERE ticker IN ({','.join(['?']*len(to_delete_prod))})", to_delete_prod)
            print(f"gen26_production.db: Purged {len(to_delete_prod)} non-Thndr tickers from stocks.")

        # Ensure all 181 stocks exist in stocks
        for s in thndr_stocks:
            cur_p.execute("""
                INSERT OR REPLACE INTO stocks (
                    ticker, company_name, sector, isin, status, is_core, created_at
                ) VALUES (?, ?, ?, ?, 'ACTIVE', 1, ?);
            """, (
                s["ticker"], s["name_ar"], s["sector"], s["isin"],
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))

        # Delete non-Thndr stocks from market_prices
        cur_p.execute(f"DELETE FROM market_prices WHERE ticker NOT IN ({','.join(['?']*len(thndr_tickers))})", list(thndr_tickers))

        conn_p.commit()
        conn_p.close()
        print("gen26_production.db: Successfully reconciled stocks table with Thndr.")

    # 4. Clean data/canonical_prices_live.json
    if os.path.exists(CANONICAL_PRICES_FILE):
        with open(CANONICAL_PRICES_FILE, "r", encoding="utf-8") as f:
            prices = json.load(f)

        purged_prices = {k: v for k, v in prices.items() if k in thndr_tickers}
        removed_count = len(prices) - len(purged_prices)
        with open(CANONICAL_PRICES_FILE, "w", encoding="utf-8") as f:
            json.dump(purged_prices, f, indent=2, ensure_ascii=False)
        print(f"canonical_prices_live.json: Purged {removed_count} non-Thndr prices, kept {len(purged_prices)} active.")

    print("=" * 80)
    print("THNDR UNIVERSE PURGE & RECONCILIATION COMPLETE!")
    print("=" * 80)


if __name__ == "__main__":
    purge_and_sync_thndr_universe()
