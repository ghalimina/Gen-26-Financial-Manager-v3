import os
import json
import warnings
import datetime
import pandas as pd
import numpy as np
import requests

warnings.filterwarnings('ignore')

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
JOURNAL_FILE = os.path.join(BASE_DIR, "paper_trading_journal.json")
DATA_DIR = os.path.join(BASE_DIR, "data")
TELEMETRY_FILE = os.path.join(DATA_DIR, "prediction_actual_telemetry.json")
DRIFT_FILE = os.path.join(DATA_DIR, "model_drift_metrics.json")

os.makedirs(DATA_DIR, exist_ok=True)

def safe_download(ticker):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=1y"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=8)
        if res.status_code == 200:
            data = res.json()
            if 'chart' in data and data['chart']['result']:
                result = data['chart']['result'][0]
                timestamps = result['timestamp']
                quote = result['indicators']['quote'][0]
                adj = result['indicators'].get('adjclose', [{}])[0].get('adjclose', quote['close'])
                
                df = pd.DataFrame({
                    'Close': quote['close'],
                    'Adj_Close': adj,
                    'High': quote['high'],
                    'Low': quote['low']
                }, index=pd.to_datetime(timestamps, unit='s'))
                
                df.dropna(subset=['Close'], inplace=True)
                df['Adj_Close'].fillna(df['Close'], inplace=True)
                df.index = df.index.tz_localize(None).normalize()
                return df
    except Exception as e:
        pass
    return pd.DataFrame()

def run_telemetry():
    print("Running Prediction vs. Actual Telemetry Tracker...")
    if not os.path.exists(JOURNAL_FILE):
        print("No journal file found.")
        return
        
    with open(JOURNAL_FILE, "r", encoding="utf-8") as f:
        journal = json.load(f)
        
    telemetry_records = []
    
    downloaded_dfs = {}
    
    # 1. Telemetry Evaluation
    for entry in journal:
        ticker = entry.get("ticker")
        entry_date = pd.to_datetime(entry.get("entry_date"))
        pred_prob = entry.get("confidence_prob")
        
        if ticker not in downloaded_dfs:
            downloaded_dfs[ticker] = safe_download(ticker)
            
        df = downloaded_dfs[ticker]
        if df.empty:
            continue
            
        # Get forward horizon data
        df_forward = df[df.index > entry_date]
        if df_forward.empty:
            continue
            
        entry_price = entry.get("simulated_fill_price", entry.get("suggested_entry_price", entry.get("entry_price")))
        
        horizons = {"1D": 1, "5D": 5, "20D": 20, "60D": 60}
        
        record = {
            "trade_id": entry.get("trade_id"),
            "ticker": ticker,
            "entry_date": entry.get("entry_date"),
            "predicted_prob": pred_prob,
            "horizons": {}
        }
        
        peak_target = entry_price
        for h_name, h_days in horizons.items():
            if len(df_forward) >= h_days:
                actual_price = df_forward['Adj_Close'].iloc[h_days - 1]
                actual_ret = (actual_price - entry_price) / entry_price
                
                # Model predicted positive direction. So expectation is ret > 0.
                direction_correct = (actual_ret > 0)
                
                # Calculate Brier score for this single instance (actual=1 if up, 0 if down)
                actual_class = 1 if actual_ret > 0 else 0
                brier_score = (pred_prob - actual_class)**2
                
                record["horizons"][h_name] = {
                    "prediction_val": "UP",
                    "actual_val": "UP" if actual_ret > 0 else "DOWN",
                    "error_delta": actual_ret,
                    "abs_error_pct": abs(actual_ret) * 100,
                    "direction_correct": bool(direction_correct),
                    "brier_score": brier_score,
                    "actual_return": actual_ret
                }
                peak_target = max(peak_target, df_forward['High'].iloc[:h_days].max())
                
        record["peak_target_achieved"] = peak_target
        telemetry_records.append(record)
        
    with open(TELEMETRY_FILE, "w", encoding="utf-8") as f:
        json.dump(telemetry_records, f, indent=2)
        
    print(f"Telemetry saved: {TELEMETRY_FILE} ({len(telemetry_records)} records)")
    
    # 2. Drift and Calibration Metrics (Rolling 20 and 60)
    completed_trades = [t for t in journal if t.get("status") == "COMPLETED"]
    
    if len(completed_trades) > 0:
        df_comp = pd.DataFrame(completed_trades)
        df_comp['net_pnl_egp'] = pd.to_numeric(df_comp['net_pnl_egp'], errors='coerce').fillna(0)
        df_comp['is_win'] = (df_comp['net_pnl_egp'] > 0).astype(int)
        
        def calc_metrics(df_sub):
            wr = df_sub['is_win'].mean() * 100.0 if not df_sub.empty else 0.0
            gross_profit = df_sub[df_sub['net_pnl_egp'] > 0]['net_pnl_egp'].sum()
            gross_loss = abs(df_sub[df_sub['net_pnl_egp'] < 0]['net_pnl_egp'].sum())
            pf = gross_profit / gross_loss if gross_loss > 0 else (gross_profit if gross_profit > 0 else 0)
            
            # ECE & Brier calculation via telemetry if available
            brier_scores = []
            prob_preds = []
            actuals = []
            for t_id in df_sub['trade_id']:
                t_rec = next((r for r in telemetry_records if r['trade_id'] == t_id), None)
                if t_rec and "5D" in t_rec["horizons"]:
                    brier_scores.append(t_rec["horizons"]["5D"]["brier_score"])
                    prob_preds.append(t_rec["predicted_prob"])
                    actuals.append(1 if t_rec["horizons"]["5D"]["direction_correct"] else 0)
                    
            brier = np.mean(brier_scores) if brier_scores else 0.0
            
            # Simple ECE calculation
            ece = 0.0
            if prob_preds:
                df_ece = pd.DataFrame({'prob': prob_preds, 'actual': actuals})
                df_ece['bin'] = pd.cut(df_ece['prob'], bins=[0, 0.6, 0.7, 0.8, 0.9, 1.0])
                bin_stats = df_ece.groupby('bin', observed=False).agg(
                    mean_prob=('prob', 'mean'),
                    acc=('actual', 'mean'),
                    count=('actual', 'count')
                ).fillna(0)
                bin_stats['weight'] = bin_stats['count'] / len(df_ece)
                ece = (np.abs(bin_stats['mean_prob'] - bin_stats['acc']) * bin_stats['weight']).sum()
                
            return wr, pf, brier, ece
            
        metrics = {}
        # Rolling 20
        df_20 = df_comp.tail(20)
        wr20, pf20, bs20, ece20 = calc_metrics(df_20)
        metrics["rolling_20"] = {"win_rate": wr20, "profit_factor": pf20, "brier_score": bs20, "ece": ece20}
        
        # Rolling 60
        df_60 = df_comp.tail(60)
        wr60, pf60, bs60, ece60 = calc_metrics(df_60)
        metrics["rolling_60"] = {"win_rate": wr60, "profit_factor": pf60, "brier_score": bs60, "ece": ece60}
        
        with open(DRIFT_FILE, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)
            
        print(f"Drift metrics saved: {DRIFT_FILE}")
        
if __name__ == "__main__":
    run_telemetry()
