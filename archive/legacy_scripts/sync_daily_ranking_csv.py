#!/usr/bin/env python3
import os
import sys
import datetime
import pandas as pd

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.multi_horizon_engine import MultiHorizonEngine
from core.market_price_service import MarketPriceService

def sync_daily_ranking_csv():
    rankings = MultiHorizonEngine.get_all_multi_horizon_rankings(universe="all")
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    csv_path = os.path.join(WORKSPACE, "gen_daily_ranking.csv")

    rows = []
    for r in rankings:
        rk = r.get("rank", 0)
        score = r.get("overall_score", 80.0)
        sig = "🟢 شراء تراجعي (BUY)" if score >= 80 else ("🟡 مراقبة الاتجاه (WATCH)" if score >= 60 else "🔴 تجنب الشراء (AVOID)")
        rows.append({
            "date": now_str,
            "rank": f"#{rk}",
            "ticker": r["ticker"],
            "name": r["company_name"],
            "sector": r.get("sector", ""),
            "current_price": r["current_price"],
            "score": score,
            "signal": sig,
            "confidence": f"{round(float(r.get('confidence', 0.85))*100, 1)}%",
            "entry_zone": r.get("entry_zone", ""),
            "target_20d": r["horizons"]["20D"]["target_1"],
            "stop_loss": r["stop_loss"],
            "data_quality": "OK",
            "model_version": "v3.0-ssot"
        })

    df = pd.DataFrame(rows)
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"Exported {len(df)} rows to gen_daily_ranking.csv.")
    for rec in df[df["ticker"] == "ORAS.CA"].to_dict("records"):
        print(f"Ticker: {rec['ticker']}, Price: {rec['current_price']}, Entry: {rec['entry_zone']}, Stop: {rec['stop_loss']}, Target: {rec['target_20d']}")

if __name__ == "__main__":
    sync_daily_ranking_csv()
