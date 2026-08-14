import os
import json
import datetime
import pandas as pd
import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

HOLDOUT_FILE = os.path.join(DATA_DIR, f"holdout_reserve_locked_{datetime.date.today().strftime('%Y%m%d')}.json")

EXPANDED_68_EGX_UNIVERSE = {
    "COMI.CA": "التجاري الدولي",
    "ADIB.CA": "مصرف أبو ظبي الإسلامي",
    "TMGH.CA": "مجموعة طلعت مصطفى",
    "FWRY.CA": "فوري للمدفوعات",
    "ESRS.CA": "حديد عز"
}

def safe_download(ticker):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=3mo"
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
                df.index = df.index.tz_localize(None).normalize()
                return df
    except Exception:
        pass
    return pd.DataFrame()

print("Locking Isolated Untouched Holdout Reserve...")
holdout_data = {}
for t in EXPANDED_68_EGX_UNIVERSE.keys():
    df = safe_download(t)
    if not df.empty:
        # Convert index to string
        df.index = df.index.astype(str)
        holdout_data[t] = df.to_dict(orient='index')

with open(HOLDOUT_FILE, "w", encoding="utf-8") as f:
    json.dump({
        "metadata": {
            "lock_date": datetime.datetime.now().isoformat(),
            "purpose": "30-Day Blind Benchmark Reserve",
            "model_version": "v3.0-frozen"
        },
        "data": holdout_data
    }, f, indent=2)

print(f"Holdout reserve successfully locked at: {HOLDOUT_FILE}")
