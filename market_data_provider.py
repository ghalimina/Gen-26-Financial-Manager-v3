import yfinance as yf
import pandas as pd
import numpy as np
import time
from datetime import datetime
import pytz
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class Quote:
    ticker: str
    last_price: Optional[float]
    bid: Optional[float]
    ask: Optional[float]
    bid_size: Optional[float]
    ask_size: Optional[float]
    open: Optional[float]
    high: Optional[float]
    low: Optional[float]
    prev_close: Optional[float]
    volume: Optional[float]
    turnover: Optional[float]
    market_time: Optional[str]
    source_timestamp: Optional[float]
    received_timestamp: float
    market_data_age_seconds: float
    fetch_latency_ms: float
    data_status: str  # FRESH, RECENT, STALE_WARNING, STALE_BLOCKED

class MarketDataProvider:
    def __init__(self):
        self.cairo_tz = pytz.timezone('Africa/Cairo')

    def get_quote(self, ticker: str) -> Quote:
        raise NotImplementedError

    def get_quotes(self, tickers: List[str]) -> Dict[str, Quote]:
        raise NotImplementedError

    def get_market_status(self) -> dict:
        now = datetime.now(self.cairo_tz)
        hour = now.hour
        minute = now.minute
        time_float = hour + minute / 60.0
        
        status = "CLOSED"
        if now.weekday() in [4, 5]: # Friday, Saturday
            status = "CLOSED"
        else:
            if 9.5 <= time_float < 10.0:
                status = "PRE-OPEN"
            elif 10.0 <= time_float < 14.5:
                status = "MARKET OPEN"
            elif 14.5 <= time_float < 14.75:
                status = "AUCTION"
        
        return {
            "status": status,
            "cairo_time": now.strftime('%H:%M:%S'),
            "date": now.strftime('%Y-%m-%d'),
            "is_open": status == "MARKET OPEN"
        }

class YFinanceDelayedProvider(MarketDataProvider):
    def __init__(self):
        super().__init__()
        self.data_mode = "DELAYED"
        self.source = "YFINANCE"
    
    def _evaluate_freshness(self, market_data_age: float) -> str:
        # Rule 6 threshold, applied strictly to market data age
        if market_data_age <= 5.0:
            return "FRESH"
        elif market_data_age <= 30.0:
            return "RECENT"
        elif market_data_age <= 120.0:
            return "STALE_WARNING"
        else:
            return "STALE_BLOCKED"

    def get_quote(self, ticker: str) -> Quote:
        return self.get_quotes([ticker]).get(ticker)

    def get_quotes(self, tickers: List[str]) -> Dict[str, Quote]:
        quotes = {}
        fetch_start = time.time()
        
        try:
            df = yf.download(tickers, period="1d", interval="1m", progress=False)
            fetch_end = time.time()
            fetch_latency_ms = (fetch_end - fetch_start) * 1000
            
            received_timestamp = time.time()
            
            if df.empty:
                for t in tickers:
                    quotes[t] = self._build_empty_quote(t, received_timestamp, fetch_latency_ms)
                return quotes
                
            for t in tickers:
                try:
                    if isinstance(df.columns, pd.MultiIndex):
                        ticker_df = df.xs(t, level=1, axis=1) if t in df.columns.get_level_values(1) else pd.DataFrame()
                    else:
                        ticker_df = df if len(tickers) == 1 else pd.DataFrame()

                    if not ticker_df.empty:
                        last_row = ticker_df.iloc[-1]
                        last_time = ticker_df.index[-1]
                        
                        last_price = float(last_row['Close']) if not pd.isna(last_row.get('Close')) else None
                        vol = float(last_row['Volume']) if not pd.isna(last_row.get('Volume')) else None
                        source_ts = last_time.timestamp()
                        
                        # Rule 1 calculation
                        market_data_age = received_timestamp - source_ts if source_ts else 999999.0
                        
                        if market_data_age < 0:
                            market_data_age = 999999.0 # Inconsistent future timestamp
                            
                        status = self._evaluate_freshness(market_data_age)
                        
                        quotes[t] = Quote(
                            ticker=t,
                            last_price=last_price,
                            bid=None, ask=None, bid_size=None, ask_size=None,
                            open=float(last_row.get('Open', np.nan)) if not pd.isna(last_row.get('Open')) else None,
                            high=float(last_row.get('High', np.nan)) if not pd.isna(last_row.get('High')) else None,
                            low=float(last_row.get('Low', np.nan)) if not pd.isna(last_row.get('Low')) else None,
                            prev_close=None,
                            volume=vol,
                            turnover=None,
                            market_time=last_time.strftime('%Y-%m-%d %H:%M:%S'),
                            source_timestamp=source_ts,
                            received_timestamp=received_timestamp,
                            market_data_age_seconds=market_data_age,
                            fetch_latency_ms=fetch_latency_ms,
                            data_status=status
                        )
                    else:
                        quotes[t] = self._build_empty_quote(t, received_timestamp, fetch_latency_ms)
                except Exception:
                    quotes[t] = self._build_empty_quote(t, received_timestamp, fetch_latency_ms)
                    
        except Exception:
            fetch_end = time.time()
            for t in tickers:
                quotes[t] = self._build_empty_quote(t, fetch_end, (fetch_end - fetch_start) * 1000)
                quotes[t].data_status = "OFFLINE"
                
        return quotes

    def _build_empty_quote(self, ticker: str, received_ts: float, latency: float) -> Quote:
        return Quote(
            ticker=ticker, last_price=None, bid=None, ask=None, bid_size=None, ask_size=None,
            open=None, high=None, low=None, prev_close=None, volume=None, turnover=None,
            market_time=None, source_timestamp=None, received_timestamp=received_ts,
            market_data_age_seconds=999999.0, fetch_latency_ms=latency, data_status="STALE_BLOCKED"
        )
