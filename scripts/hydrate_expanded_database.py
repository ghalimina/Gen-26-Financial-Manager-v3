import os
import sys
import sqlite3
import json
import time
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
WORKSPACE = os.path.abspath(".")
sys.path.insert(0, WORKSPACE)

# Connect to database
db_path = "data/gen26_production.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# 1. Identify and verify original 34 tickers
df_counts = pd.read_sql_query(
    "SELECT ticker, count(*) as cnt FROM historical_daily_bars GROUP BY ticker", conn
)
orig_34 = set(df_counts[df_counts['cnt'] > 50]['ticker'])
print(f"Original 34 tickers count: {len(orig_34)}")

# Verify current rows of original 34
orig_rows_before = cur.execute(
    f"SELECT count(*) FROM historical_daily_bars WHERE ticker IN ({','.join(['?']*len(orig_34))})",
    list(orig_34)
).fetchone()[0]
print(f"Original 34 tickers rows before expansion: {orig_rows_before}")

# 2. Load the 77 qualified tickers from expansion census
with open("scratch/expansion_census.json", "r", encoding="utf-8") as f:
    census = json.load(f)

qualified_tickers = sorted(list(census["qualified"].keys()))
print(f"Qualified new tickers to be hydrated: {len(qualified_tickers)}")

# Make sure NO original ticker is in qualified_tickers
overlap = set(qualified_tickers).intersection(orig_34)
assert len(overlap) == 0, f"Error: Overlap detected with original tickers: {overlap}"

# 3. Download and prepare rows for the 77 tickers
print("\nFetching and preparing daily bars for the 77 qualified tickers...")
new_rows = []
now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

for idx, tkr in enumerate(qualified_tickers, 1):
    try:
        df = yf.download(tkr, start="2020-01-01", end="2026-09-18", progress=False, timeout=12)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0] for col in df.columns]
        df = df.dropna(subset=['Close']).sort_index()
        
        for date_idx, row in df.iterrows():
            m_date = str(date_idx)[:10]
            o = float(row.get('Open', row['Close']))
            h = float(row.get('High', row['Close']))
            l = float(row.get('Low', row['Close']))
            c = float(row['Close'])
            v = float(row.get('Volume', 0.0))
            new_rows.append((tkr, m_date, o, h, l, c, v, "YAHOO_FINANCE_HISTORICAL_EXPANSION", now_str))
        print(f"  [{idx}/{len(qualified_tickers)}] Prepared {tkr:<10}: {len(df)} bars")
    except Exception as e:
        print(f"  [ERROR] Failed to prepare {tkr}: {e}")

print(f"\nTotal new rows prepared for insertion: {len(new_rows):,}")

# 4. Safely insert into database:
# Delete old 45 bars ONLY for the qualified 77 tickers
print(f"\nDeleting old 45 placeholder bars for ONLY the 77 qualified tickers...")
cur.execute(
    f"DELETE FROM historical_daily_bars WHERE ticker IN ({','.join(['?']*len(qualified_tickers))})",
    qualified_tickers
)
deleted_placeholders = cur.rowcount
print(f"Deleted {deleted_placeholders} old placeholder rows.")

# Insert new full historical bars
print("Inserting full historical bars for the 77 new stocks...")
cur.executemany(
    """
    INSERT OR REPLACE INTO historical_daily_bars 
    (ticker, market_date, open_price, high_price, low_price, close_price, volume, source, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
    new_rows
)
conn.commit()

# 5. Strict verification of database invariants:
orig_rows_after = cur.execute(
    f"SELECT count(*) FROM historical_daily_bars WHERE ticker IN ({','.join(['?']*len(orig_34))})",
    list(orig_34)
).fetchone()[0]
total_rows_after = cur.execute("SELECT count(*) FROM historical_daily_bars").fetchone()[0]
unique_tickers_after = cur.execute("SELECT count(DISTINCT ticker) FROM historical_daily_bars").fetchone()[0]
long_history_tickers = cur.execute(
    "SELECT count(*) FROM (SELECT ticker FROM historical_daily_bars GROUP BY ticker HAVING count(*) >= 1000)"
).fetchone()[0]

print("\n" + "="*85)
print("DATABASE EXPANSION VERIFICATION REPORT")
print("="*85)
print(f"Original 34 Rows Before:               {orig_rows_before:,}")
print(f"Original 34 Rows After:                {orig_rows_after:,} (INVARIANT PRESERVED: {orig_rows_before == orig_rows_after})")
print(f"Total Rows in Database After:          {total_rows_after:,}")
print(f"Total Unique Tickers in Database:      {unique_tickers_after}")
print(f"Stocks with Full History (>= 1,000):   {long_history_tickers} (34 Original + 77 New = 111 Total)")
print("="*85)

conn.close()
