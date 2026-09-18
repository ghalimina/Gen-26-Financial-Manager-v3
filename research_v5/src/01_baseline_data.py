import os
import yfinance as yf
import pandas as pd
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data_copies')
os.makedirs(DATA_DIR, exist_ok=True)

EGX_TICKERS = [
    "COMI.CA", "HRHO.CA", "TMGH.CA", "SWDY.CA", "FWRY.CA", "EKHO.CA", "CIRA.CA", "ABUK.CA", "HELI.CA", "AMOC.CA"
]

def fetch_and_save_baseline_data():
    print(f"Fetching historical baseline data for {len(EGX_TICKERS)} EGX tickers...")
    all_data = []
    
    for ticker in EGX_TICKERS:
        try:
            df = yf.download(ticker, start="2020-01-01", progress=False)
            if df.empty:
                continue
            
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
                
            df = df.reset_index()
            df['Ticker'] = ticker
            all_data.append(df)
            print(f"Loaded {len(df)} rows for {ticker}")
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
            
    if all_data:
        master_df = pd.concat(all_data, ignore_index=True)
        master_df.rename(columns={'Date': 'date'}, inplace=True)
        
        output_path = os.path.join(DATA_DIR, 'egx_historical_snapshot.csv')
        master_df.to_csv(output_path, index=False)
        print(f"Saved {len(master_df)} rows to {output_path}")
        print("PHASE 1 (DATA BASELINE) COMPLETE.")

if __name__ == "__main__":
    fetch_and_save_baseline_data()
