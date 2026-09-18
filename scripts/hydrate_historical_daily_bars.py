#!/usr/bin/env python3
"""
scripts/hydrate_historical_daily_bars.py
Hydrates SQLite table historical_daily_bars in data/gen26_production.db
with the authentic 5-year historical clean bars (2020–2026) from Parquet files.
Eliminates data starvation without modifying production risk gates.
"""

import os
import glob
import sqlite3
import pandas as pd

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(WORKSPACE, "data", "gen26_production.db")
CLEAN_PARQUET_DIR = os.path.join(WORKSPACE, "scratch", "clean_room", "research_v43", "data")

def hydrate_bars():
    print(f"Connecting to database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Count before
    cur.execute("SELECT COUNT(*) FROM historical_daily_bars")
    count_before = cur.fetchone()[0]
    print(f"Historical bars before hydration: {count_before}")

    # Ensure unique index exists to allow INSERT OR IGNORE / REPLACE
    cur.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_hist_bars_ticker_date 
        ON historical_daily_bars(ticker, market_date)
    """)

    parquet_files = sorted(glob.glob(os.path.join(CLEAN_PARQUET_DIR, "*_clean.parquet")))
    print(f"Found {len(parquet_files)} clean Parquet files to hydrate.")

    total_inserted = 0
    for p_file in parquet_files:
        basename = os.path.basename(p_file)
        ticker = basename.replace("_clean.parquet", "")
        df = pd.read_parquet(p_file)
        
        # Determine date format
        dates = pd.to_datetime(df.index).strftime("%Y-%m-%d")
        
        rows_to_insert = []
        for i, date_str in enumerate(dates):
            open_p = float(df["Open"].iloc[i]) if "Open" in df.columns else 0.0
            high_p = float(df["High"].iloc[i]) if "High" in df.columns else 0.0
            low_p = float(df["Low"].iloc[i]) if "Low" in df.columns else 0.0
            # Use Adj Close for backward-adjusted analytical consistency
            close_p = float(df["Adj Close"].iloc[i]) if "Adj Close" in df.columns else float(df["Close"].iloc[i])
            vol = float(df["Volume"].iloc[i]) if "Volume" in df.columns else 0.0
            
            rows_to_insert.append((
                ticker, date_str, open_p, high_p, low_p, close_p, vol,
                "PARQUET_HISTORICAL_SSOT", "2026-09-17T00:00:00Z"
            ))

        cur.executemany("""
            INSERT OR REPLACE INTO historical_daily_bars 
            (ticker, market_date, open_price, high_price, low_price, close_price, volume, source, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, rows_to_insert)
        total_inserted += len(rows_to_insert)

    conn.commit()

    cur.execute("SELECT COUNT(*), MIN(market_date), MAX(market_date), COUNT(DISTINCT ticker) FROM historical_daily_bars")
    count_after, min_d, max_d, n_tkr = cur.fetchone()
    conn.close()

    print(f"Successfully processed {total_inserted} records across {len(parquet_files)} tickers.")
    print(f"Historical bars after hydration: {count_after}")
    print(f"Date Range: {min_d} to {max_d} across {n_tkr} distinct tickers.")

if __name__ == "__main__":
    hydrate_bars()
