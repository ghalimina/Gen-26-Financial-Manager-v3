"""
research_v42/engines/technical_timing_engine.py

Technical Timing Engine — GEN-26 V42 Research Layer
Purpose: Timing signals only. Does NOT determine fundamental quality.
Features: Momentum, RSI, ATR, ADX, Volume, Trend, Pullback, Volatility Regime

STATUS: RESEARCH / SHADOW
"""
from __future__ import annotations
import math
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Optional

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

from data_quality_engine import DataQualityEngine, DataQualityResult


@dataclass
class TechnicalProfile:
    ticker: str
    current_price: Optional[float] = None

    # Indicators
    rsi_14: Optional[float] = None
    atr_14: Optional[float] = None
    adx_14: Optional[float] = None
    momentum_20: Optional[float] = None   # 20-day return %
    momentum_60: Optional[float] = None   # 60-day return %
    volume_ratio: Optional[float] = None  # today vol / 20d avg vol

    # Trend
    above_sma20: Optional[bool] = None
    above_sma50: Optional[bool] = None
    above_sma200: Optional[bool] = None
    trend_direction: str = "UNKNOWN"  # UP | DOWN | SIDEWAYS

    # Pullback quality
    pullback_pct: Optional[float] = None   # How far below SMA20
    is_valid_pullback: bool = False        # Entry < Current

    # Volatility regime
    volatility_regime: str = "UNKNOWN"    # LOW | NORMAL | HIGH | EXTREME
    atr_pct: Optional[float] = None       # ATR as % of price

    # Scores
    timing_score: float = 50.0            # 0–100
    data_quality: str = "PROXY"
    warnings: list = field(default_factory=list)
    history_rows: int = 0


class TechnicalTimingEngine:
    """
    Computes technical timing indicators.
    Returns a score 0–100 where 100 = ideal entry timing.
    """

    def __init__(self, lookback_days: int = 252):
        self.lookback_days = lookback_days
        self._cache: dict[str, TechnicalProfile] = {}

    def _compute_rsi(self, close: pd.Series, period: int = 14) -> float:
        delta = close.diff()
        gain = delta.clip(lower=0).ewm(span=period, adjust=False).mean()
        loss = (-delta.clip(upper=0)).ewm(span=period, adjust=False).mean()
        rs = gain / (loss + 1e-9)
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1]) if not rsi.empty else 50.0

    def _compute_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        high = df["High"]
        low = df["Low"]
        close = df["Close"]
        tr1 = high - low
        tr2 = (high - close.shift()).abs()
        tr3 = (low - close.shift()).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.ewm(span=period, adjust=False).mean()
        return float(atr.iloc[-1]) if not atr.empty else 0.0

    def _compute_adx(self, df: pd.DataFrame, period: int = 14) -> float:
        """Simplified ADX."""
        try:
            high, low, close = df["High"], df["Low"], df["Close"]
            up = high.diff()
            down = -low.diff()
            plus_dm = up.where((up > down) & (up > 0), 0.0)
            minus_dm = down.where((down > up) & (down > 0), 0.0)
            tr = pd.concat([
                high - low,
                (high - close.shift()).abs(),
                (low - close.shift()).abs()
            ], axis=1).max(axis=1)
            atr = tr.ewm(span=period, adjust=False).mean()
            plus_di = 100 * plus_dm.ewm(span=period, adjust=False).mean() / (atr + 1e-9)
            minus_di = 100 * minus_dm.ewm(span=period, adjust=False).mean() / (atr + 1e-9)
            dx = (plus_di - minus_di).abs() / (plus_di + minus_di + 1e-9) * 100
            adx = dx.ewm(span=period, adjust=False).mean()
            return float(adx.iloc[-1])
        except Exception:
            return 25.0

    def compute(self, ticker: str, df: Optional[pd.DataFrame] = None) -> TechnicalProfile:
        if ticker in self._cache:
            return self._cache[ticker]

        profile = TechnicalProfile(ticker=ticker)

        if df is None:
            if not YFINANCE_AVAILABLE:
                profile.warnings.append("yfinance not available")
                return profile
            try:
                import datetime
                end = datetime.date.today().strftime("%Y-%m-%d")
                raw = yf.download(ticker, period="2y", progress=False, auto_adjust=True)
                if isinstance(raw.columns, pd.MultiIndex):
                    raw.columns = raw.columns.droplevel(1)
                df = raw
            except Exception as e:
                profile.warnings.append(f"Data fetch failed: {e}")
                return profile

        # Validate
        dq = DataQualityEngine()
        check = dq.validate_dataframe(df, ["Open", "High", "Low", "Close", "Volume"], ticker)
        if check.status == DataQualityResult.BLOCK:
            profile.warnings.extend(check.issues)
            profile.data_quality = "MISSING"
            return profile

        profile.history_rows = len(df)
        close = df["Close"].ffill()
        volume = df["Volume"].ffill() if "Volume" in df else None

        # Current price
        profile.current_price = float(close.iloc[-1])

        # SMAs
        sma20 = close.rolling(20).mean().iloc[-1]
        sma50 = close.rolling(50).mean().iloc[-1]
        sma200 = close.rolling(200).mean().iloc[-1] if len(close) >= 200 else None

        cp = profile.current_price
        profile.above_sma20 = cp > sma20 if not math.isnan(sma20) else None
        profile.above_sma50 = cp > sma50 if not math.isnan(sma50) else None
        profile.above_sma200 = (cp > sma200 if sma200 and not math.isnan(float(sma200)) else None)

        # Trend
        trending_up = sum(filter(None, [profile.above_sma20, profile.above_sma50, profile.above_sma200]))
        total_sma = sum([1 for x in [profile.above_sma20, profile.above_sma50, profile.above_sma200] if x is not None])
        if total_sma > 0:
            ratio = trending_up / total_sma
            profile.trend_direction = "UP" if ratio >= 0.67 else ("DOWN" if ratio <= 0.33 else "SIDEWAYS")

        # Momentum
        if len(close) >= 21:
            profile.momentum_20 = float((close.iloc[-1] / close.iloc[-21] - 1) * 100)
        if len(close) >= 61:
            profile.momentum_60 = float((close.iloc[-1] / close.iloc[-61] - 1) * 100)

        # RSI
        if len(close) >= 15:
            profile.rsi_14 = self._compute_rsi(close)

        # ATR
        if len(df) >= 15:
            profile.atr_14 = self._compute_atr(df)
            if profile.atr_14 and cp > 0:
                profile.atr_pct = (profile.atr_14 / cp) * 100

        # ADX
        if len(df) >= 20:
            profile.adx_14 = self._compute_adx(df)

        # Volume ratio
        if volume is not None and len(volume) >= 21:
            avg_vol = volume.iloc[-21:-1].mean()
            today_vol = volume.iloc[-1]
            if avg_vol > 0:
                profile.volume_ratio = float(today_vol / avg_vol)

        # Pullback from SMA20
        if not math.isnan(sma20) and sma20 > 0:
            profile.pullback_pct = float((cp / sma20 - 1) * 100)

        # Volatility regime
        if profile.atr_pct is not None:
            if profile.atr_pct > 5:
                profile.volatility_regime = "EXTREME"
            elif profile.atr_pct > 3:
                profile.volatility_regime = "HIGH"
            elif profile.atr_pct > 1.5:
                profile.volatility_regime = "NORMAL"
            else:
                profile.volatility_regime = "LOW"

        # Pullback validity (entry < current — V4.1 rule preserved)
        if profile.pullback_pct is not None and profile.pullback_pct < -1.5:
            profile.is_valid_pullback = True  # Below SMA20 = pullback territory

        # === TIMING SCORE ===
        score = 50.0
        warns = []

        # Trend alignment
        if profile.trend_direction == "UP":
            score += 20
        elif profile.trend_direction == "DOWN":
            score -= 20
            warns.append("Downtrend detected")

        # RSI: oversold range for pullback entry
        if profile.rsi_14 is not None:
            if 30 <= profile.rsi_14 <= 50:
                score += 15  # Ideal pullback zone
            elif profile.rsi_14 < 30:
                score += 5   # Oversold (caution)
                warns.append(f"RSI oversold: {profile.rsi_14:.1f}")
            elif profile.rsi_14 > 70:
                score -= 15
                warns.append(f"RSI overbought: {profile.rsi_14:.1f}")

        # Momentum
        if profile.momentum_20 is not None:
            if 0 < profile.momentum_20 < 10:
                score += 10  # Moderate positive momentum
            elif profile.momentum_20 > 20:
                score -= 5   # Possibly extended
            elif profile.momentum_20 < -15:
                score -= 10
                warns.append(f"Strong negative momentum: {profile.momentum_20:.1f}%")

        # ADX (trend strength)
        if profile.adx_14 is not None:
            if profile.adx_14 > 25:
                score += 5   # Trending market

        # Volume confirmation
        if profile.volume_ratio is not None:
            if profile.volume_ratio > 1.5:
                score += 5   # Above-average volume
            elif profile.volume_ratio < 0.5:
                score -= 5   # Low interest

        # Volatility regime penalty
        if profile.volatility_regime == "EXTREME":
            score -= 15
            warns.append("Extreme volatility regime — wider uncertainty")
        elif profile.volatility_regime == "HIGH":
            score -= 5

        # Pullback quality
        if profile.is_valid_pullback:
            score += 10
        else:
            warns.append("No valid pullback condition currently (Entry must be < Current)")

        profile.timing_score = round(min(max(score, 0.0), 100.0), 1)
        profile.warnings = warns

        self._cache[ticker] = profile
        return profile


if __name__ == "__main__":
    import sys
    tickers = sys.argv[1:] if len(sys.argv) > 1 else ["COMI.CA"]
    engine = TechnicalTimingEngine()
    for t in tickers:
        p = engine.compute(t)
        print(f"\n{t}: TimingScore={p.timing_score:.1f}/100")
        print(f"  Price={p.current_price}, Trend={p.trend_direction}")
        print(f"  RSI={p.rsi_14:.1f if p.rsi_14 else 'N/A'}, ADX={p.adx_14:.1f if p.adx_14 else 'N/A'}")
        print(f"  VolatilityRegime={p.volatility_regime}, ValidPullback={p.is_valid_pullback}")
        for w in p.warnings[:4]:
            print(f"  WARN: {w}")
