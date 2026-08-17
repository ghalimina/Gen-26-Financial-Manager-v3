"""
research_v42/engines/market_regime_engine.py

Market Regime Engine — GEN-26 V42 Research Layer
Uses EGX30 (or proxy) to classify macro market environment.

STATUS: RESEARCH / SHADOW
"""
from __future__ import annotations
import math
import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Optional


@dataclass
class MarketRegime:
    regime: str = "UNKNOWN"         # BULL | BEAR | SIDEWAYS | HIGH_VOL | LOW_VOL | SHOCK
    trend: str = "UNKNOWN"          # UP | DOWN | FLAT
    volatility_level: str = "UNKNOWN"
    breadth_signal: str = "UNKNOWN" # EXPANDING | CONTRACTING | NEUTRAL
    egx30_return_20d: Optional[float] = None
    egx30_return_60d: Optional[float] = None
    market_atr_pct: Optional[float] = None
    confidence: float = 0.0
    data_quality: str = "PROXY"
    warnings: list = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class MarketRegimeEngine:
    """
    Classifies the current EGX market regime.
    Uses EGX30 proxy (^CASE30 or EEM as fallback).
    """

    EGX30_TICKERS = ["^CASE30", "EEM"]  # Fallback hierarchy

    def __init__(self):
        self._cached_regime: Optional[MarketRegime] = None
        self._cache_date: Optional[str] = None

    def _fetch_index(self) -> Optional[pd.DataFrame]:
        try:
            import yfinance as yf
            import datetime
            end = datetime.date.today().strftime("%Y-%m-%d")
            for ticker in self.EGX30_TICKERS:
                df = yf.download(ticker, period="1y", progress=False, auto_adjust=True)
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.droplevel(1)
                if not df.empty and len(df) > 60:
                    df["_source"] = ticker
                    return df
        except Exception:
            pass
        return None

    def classify(self) -> MarketRegime:
        import datetime
        today = datetime.date.today().isoformat()
        if self._cached_regime and self._cache_date == today:
            return self._cached_regime

        regime = MarketRegime()
        df = self._fetch_index()

        if df is None or df.empty:
            regime.warnings.append("Cannot fetch market index — regime UNKNOWN")
            regime.data_quality = "MISSING"
            self._cached_regime = regime
            self._cache_date = today
            return regime

        close = df["Close"].ffill()

        # Trend: 20d and 60d returns
        if len(close) >= 21:
            regime.egx30_return_20d = float((close.iloc[-1] / close.iloc[-21] - 1) * 100)
        if len(close) >= 61:
            regime.egx30_return_60d = float((close.iloc[-1] / close.iloc[-61] - 1) * 100)

        # Volatility: 20d rolling std
        ret = close.pct_change()
        vol20 = float(ret.rolling(20).std().iloc[-1] * math.sqrt(252) * 100)
        regime.market_atr_pct = vol20

        if vol20 > 35:
            regime.volatility_level = "EXTREME"
        elif vol20 > 20:
            regime.volatility_level = "HIGH"
        elif vol20 > 10:
            regime.volatility_level = "NORMAL"
        else:
            regime.volatility_level = "LOW"

        # SMA trend
        sma50 = float(close.rolling(50).mean().iloc[-1])
        sma200 = float(close.rolling(200).mean().iloc[-1]) if len(close) >= 200 else None
        cp = float(close.iloc[-1])

        above_sma50 = cp > sma50
        above_sma200 = cp > sma200 if sma200 else None

        r20 = regime.egx30_return_20d or 0.0
        r60 = regime.egx30_return_60d or 0.0

        if above_sma50 and r60 > 5:
            regime.trend = "UP"
        elif not above_sma50 and r60 < -5:
            regime.trend = "DOWN"
        else:
            regime.trend = "FLAT"

        # Regime classification
        if regime.volatility_level in ("EXTREME",) and abs(r20) > 10:
            regime.regime = "SHOCK"
        elif regime.trend == "UP" and regime.volatility_level in ("NORMAL", "LOW"):
            regime.regime = "BULL"
        elif regime.trend == "DOWN" and r60 < -10:
            regime.regime = "BEAR"
        elif regime.volatility_level == "HIGH":
            regime.regime = "HIGH_VOL"
        elif regime.volatility_level == "LOW":
            regime.regime = "LOW_VOL"
        else:
            regime.regime = "SIDEWAYS"

        # Confidence: higher if we have full data
        regime.confidence = 0.75 if (above_sma200 is not None) else 0.5
        regime.data_quality = "PROXY"

        self._cached_regime = regime
        self._cache_date = today
        return regime


if __name__ == "__main__":
    engine = MarketRegimeEngine()
    r = engine.classify()
    print(f"Regime: {r.regime}")
    print(f"Trend: {r.trend}, Volatility: {r.volatility_level}")
    print(f"EGX30 20d: {r.egx30_return_20d:.1f}%, 60d: {r.egx30_return_60d:.1f}%")
    print(f"Confidence: {r.confidence:.0%}")
