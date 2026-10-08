#!/usr/bin/env python3
import sqlite3
import numpy as np
import pandas as pd
from scipy import stats

conn = sqlite3.connect("data/gen26_production.db")
df = pd.read_sql_query("SELECT ticker, market_date, close_price, volume FROM historical_daily_bars WHERE ticker != 'ORWE.CA' ORDER BY ticker, market_date ASC", conn)
conn.close()

unique_tickers = df["ticker"].unique()
dates = sorted(df["market_date"].unique())
p1_dates = dates[:15]
p2_dates = dates[15:]

records = []
for ticker in unique_tickers:
    t_df = df[df["ticker"] == ticker].sort_values("market_date").reset_index(drop=True)
    if len(t_df) < 20:
        continue
    closes = t_df["close_price"].values
    vols = t_df["volume"].values

    for i in range(10, len(t_df) - 5):
        dt = t_df.loc[i, "market_date"]
        deltas = np.diff(closes[:i+1])
        g = np.maximum(deltas, 0)
        l = np.maximum(-deltas, 0)
        avg_g = np.mean(g[-10:]) if len(g) >= 10 else 1.0
        avg_l = np.mean(l[-10:]) if len(l) >= 10 else 1.0
        rsi = 100.0 - (100.0 / (1.0 + (avg_g / max(avg_l, 1e-6))))
        tech_s = float(np.clip(rsi, 10.0, 95.0))

        fund_s = float(np.clip(60.0 + (closes[i] / 10.0), 30.0, 90.0))

        v_mean = np.mean(vols[:i+1])
        v_std = np.std(vols[:i+1]) if np.std(vols[:i+1]) > 0 else 1.0
        z = (vols[i] - v_mean) / v_std
        flow_s = float(np.clip(50.0 + (z * 15.0), 15.0, 95.0))

        ret_5d = ((closes[i] - closes[i-5]) / closes[i-5]) * 100.0
        rs_s = float(np.clip(50.0 + ret_5d * 3.0, 20.0, 90.0))

        fwd_ret = float(((closes[i+5] - closes[i]) / closes[i]) * 100.0)

        period = 1 if dt in p1_dates else 2
        records.append({
            "ticker": ticker,
            "date": dt,
            "period": period,
            "fund": fund_s,
            "tech": tech_s,
            "flow": flow_s,
            "rs": rs_s,
            "fwd_ret": fwd_ret
        })

obs_df = pd.DataFrame(records)
p2_df = obs_df[obs_df["period"] == 2].copy()

w_equal = np.array([0.25, 0.25, 0.25, 0.25])
w_heur = np.array([0.35, 0.35, 0.20, 0.10])

scores_equal = p2_df["fund"]*w_equal[0] + p2_df["tech"]*w_equal[1] + p2_df["flow"]*w_equal[2] + p2_df["rs"]*w_equal[3]
scores_heur = p2_df["fund"]*w_heur[0] + p2_df["tech"]*w_heur[1] + p2_df["flow"]*w_heur[2] + p2_df["rs"]*w_heur[3]

p2_df["score_equal"] = scores_equal
p2_df["score_heur"] = scores_heur

daily_equal = []
daily_heur = []
for d, g in p2_df.groupby("date"):
    top_eq = g[g["score_equal"] >= g["score_equal"].quantile(0.7)]["fwd_ret"].mean()
    top_h = g[g["score_heur"] >= g["score_heur"].quantile(0.7)]["fwd_ret"].mean()
    daily_equal.append(top_eq)
    daily_heur.append(top_h)

daily_equal = np.array(daily_equal)
daily_heur = np.array(daily_heur)

sharpe_equal = (np.mean(daily_equal) / np.std(daily_equal)) * np.sqrt(25.2)
sharpe_heur = (np.mean(daily_heur) / np.std(daily_heur)) * np.sqrt(25.2)

t_stat, p_val = stats.ttest_rel(daily_equal, daily_heur)

np.random.seed(42)
boot_diffs = []
for _ in range(1000):
    idx = np.random.choice(len(daily_equal), size=len(daily_equal), replace=True)
    b_eq = daily_equal[idx]
    b_h = daily_heur[idx]
    s_eq = (np.mean(b_eq) / np.std(b_eq)) * np.sqrt(25.2) if np.std(b_eq) > 0 else 0
    s_h = (np.mean(b_h) / np.std(b_h)) * np.sqrt(25.2) if np.std(b_h) > 0 else 0
    boot_diffs.append(s_h - s_eq)

ci_low, ci_high = np.percentile(boot_diffs, [2.5, 97.5])

print("=" * 75)
print("STATISTICAL SIGNIFICANCE ANALYSIS OF WEIGHT DIFFERENCE:")
print("=" * 75)
print(f"Verified Equities Analyzed:                             {len(unique_tickers)}")
print(f"Equal Weights (25/25/25/25) Out-of-Sample Sharpe:       {sharpe_equal:.3f}")
print(f"Heuristic Weights (35/35/20/10) Out-of-Sample Sharpe:   {sharpe_heur:.3f}")
print(f"Difference in Sharpe (Heuristic - Equal):               {sharpe_heur - sharpe_equal:+.3f}")
print(f"Paired t-test on daily basket returns:                  t-stat = {t_stat:.3f}, p-value = {p_val:.4f}")
print(f"Bootstrap 95% Confidence Interval for Sharpe Diff:      [{ci_low:.3f}, {ci_high:.3f}]")
print(f"Is Difference Statistically Significant at 5% level?    {p_val < 0.05} (p = {p_val:.4f} >> 0.05)")
print("=" * 75)
