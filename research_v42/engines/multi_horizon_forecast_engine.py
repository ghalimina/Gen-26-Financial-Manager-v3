"""
research_v42/engines/multi_horizon_forecast_engine.py

Multi-Horizon Forecasting Engine — GEN-26 V42 Research Layer
Trains independent Walk-Forward models for each horizon.

Horizons: 1D, 5D, 10D, 20D, 60D

RULE:
  - No random shuffle of time series
  - Walk-Forward cross-validation only
  - Point-in-Time safe (no future leakage)
  - Calibration required per horizon
  - Results labeled as EXPERIMENTAL

STATUS: RESEARCH / SHADOW
"""
from __future__ import annotations
import sys
import os
import math
import datetime
import json
import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

try:
    import yfinance as yf
    from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
    from sklearn.calibration import CalibratedClassifierCV
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.preprocessing import RobustScaler
    from sklearn.metrics import brier_score_loss, accuracy_score, roc_auc_score
    SKLEARN_OK = True
except ImportError as e:
    SKLEARN_OK = False
    print(f"[WARN] Forecasting engine unavailable: {e}")

from dataclasses import dataclass, field
from typing import Optional

HORIZONS = [1, 5, 10, 20, 60]


@dataclass
class HorizonForecast:
    horizon: int                     # days
    probability_up: Optional[float] = None
    probability_down: Optional[float] = None
    expected_return_pct: Optional[float] = None
    expected_price: Optional[float] = None
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None
    confidence: float = 0.0
    uncertainty: float = 1.0          # 0=certain, 1=max uncertain
    brier_score: Optional[float] = None
    accuracy_oos: Optional[float] = None
    model_name: str = "NONE"
    status: str = "NOT_COMPUTED"      # COMPUTED | FAILED | INSUFFICIENT_DATA
    warnings: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "horizon_days": self.horizon,
            "probability_up": round(self.probability_up, 3) if self.probability_up is not None else None,
            "probability_down": round(self.probability_down, 3) if self.probability_down is not None else None,
            "expected_return_pct": round(self.expected_return_pct, 2) if self.expected_return_pct is not None else None,
            "expected_price": round(self.expected_price, 2) if self.expected_price is not None else None,
            "price_range": {
                "lower": round(self.lower_bound, 2) if self.lower_bound else None,
                "upper": round(self.upper_bound, 2) if self.upper_bound else None,
            },
            "confidence": round(self.confidence, 2),
            "uncertainty": round(self.uncertainty, 2),
            "brier_score_oos": round(self.brier_score, 4) if self.brier_score is not None else None,
            "accuracy_oos": round(self.accuracy_oos, 3) if self.accuracy_oos is not None else None,
            "model": self.model_name,
            "status": self.status,
            "warnings": self.warnings[:3],
        }


def _compute_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute time-series features that are safe (no future leakage).
    All features computed with shift(1) to prevent same-bar lookahead.
    """
    feat = pd.DataFrame(index=df.index)
    close = df["Close"]
    volume = df.get("Volume", pd.Series(np.nan, index=df.index))

    # Returns
    for w in [1, 3, 5, 10, 20, 60]:
        feat[f"ret_{w}d"] = close.pct_change(w).shift(1)

    # Volatility
    for w in [10, 20]:
        feat[f"vol_{w}d"] = close.pct_change().rolling(w).std().shift(1)

    # RSI proxy
    delta = close.diff().shift(1)
    gain = delta.clip(lower=0).ewm(span=14, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(span=14, adjust=False).mean()
    feat["rsi_14"] = 100 - (100 / (1 + gain / (loss + 1e-9)))

    # SMA ratios
    for w in [20, 50]:
        sma = close.rolling(w).mean().shift(1)
        feat[f"price_to_sma{w}"] = (close.shift(1) / sma) - 1

    # Volume ratio
    vol_ma = volume.rolling(20).mean().shift(1)
    feat["vol_ratio"] = (volume.shift(1) / (vol_ma + 1e-9))

    # ATR proxy
    high = df.get("High", close)
    low = df.get("Low", close)
    tr = pd.concat([
        (high - low).abs(),
        (high - close.shift()).abs(),
        (low - close.shift()).abs(),
    ], axis=1).max(axis=1)
    feat["atr_pct"] = (tr.ewm(span=14, adjust=False).mean() / close).shift(1)

    return feat


def _walk_forward_eval(
    X: pd.DataFrame, y: pd.Series, n_splits: int = 4
) -> tuple[float, float, float]:
    """
    Walk-forward cross-validation.
    Returns (mean_accuracy, mean_brier, mean_auc).
    """
    tscv = TimeSeriesSplit(n_splits=n_splits)
    accs, briers, aucs = [], [], []

    for train_idx, test_idx in tscv.split(X):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

        if len(y_train.unique()) < 2 or len(y_test) < 5:
            continue

        try:
            model = HistGradientBoostingClassifier(
                max_iter=100, learning_rate=0.05,
                max_depth=4, random_state=42
            )
            cal = CalibratedClassifierCV(model, cv=3, method="sigmoid")
            cal.fit(X_train, y_train)

            proba = cal.predict_proba(X_test)[:, 1]
            pred = (proba >= 0.5).astype(int)

            accs.append(accuracy_score(y_test, pred))
            briers.append(brier_score_loss(y_test, proba))
            try:
                aucs.append(roc_auc_score(y_test, proba))
            except Exception:
                pass
        except Exception:
            continue

    acc = np.mean(accs) if accs else 0.5
    brier = np.mean(briers) if briers else 0.25
    auc = np.mean(aucs) if aucs else 0.5
    return acc, brier, auc


class MultiHorizonForecastEngine:
    """
    Trains and evaluates walk-forward models for each horizon.
    All data fetched and processed in Point-in-Time safe manner.
    """

    def __init__(self):
        self._cache: dict[str, dict[int, HorizonForecast]] = {}

    def forecast(self, ticker: str, df: Optional[pd.DataFrame] = None) -> dict[int, HorizonForecast]:
        """Returns {horizon: HorizonForecast} for all configured horizons."""
        if ticker in self._cache:
            return self._cache[ticker]

        results: dict[int, HorizonForecast] = {}

        if not SKLEARN_OK:
            for h in HORIZONS:
                fc = HorizonForecast(horizon=h, status="FAILED")
                fc.warnings.append("sklearn not available")
                results[h] = fc
            return results

        # Fetch data
        if df is None:
            try:
                raw = yf.download(ticker, period="5y", progress=False, auto_adjust=True)
                if isinstance(raw.columns, pd.MultiIndex):
                    raw.columns = raw.columns.droplevel(1)
                df = raw.ffill().dropna(subset=["Close"])
            except Exception as e:
                for h in HORIZONS:
                    fc = HorizonForecast(horizon=h, status="FAILED")
                    fc.warnings.append(f"Data fetch: {e}")
                    results[h] = fc
                self._cache[ticker] = results
                return results

        if len(df) < 120:
            for h in HORIZONS:
                fc = HorizonForecast(horizon=h, status="INSUFFICIENT_DATA")
                fc.warnings.append(f"Only {len(df)} rows, need 120+")
                results[h] = fc
            self._cache[ticker] = results
            return results

        close = df["Close"]
        current_price = float(close.iloc[-1])

        # Compute features
        feat_df = _compute_features(df)

        for horizon in HORIZONS:
            fc = HorizonForecast(horizon=horizon, model_name="HistGBM+CalibSigmoid")
            try:
                # Target: 1 if price is higher in `horizon` days
                future_ret = close.pct_change(horizon).shift(-horizon)
                y = (future_ret > 0).astype(int)

                # Align
                valid_idx = feat_df.dropna().index.intersection(y.dropna().index)
                if len(valid_idx) < 100:
                    fc.status = "INSUFFICIENT_DATA"
                    fc.warnings.append(f"Only {len(valid_idx)} valid samples")
                    results[horizon] = fc
                    continue

                X = feat_df.loc[valid_idx].fillna(0)
                yv = y.loc[valid_idx]

                # Remove last `horizon` rows (no outcome yet)
                X = X.iloc[:-horizon]
                yv = yv.iloc[:-horizon]

                # Walk-forward evaluation
                acc, brier, auc = _walk_forward_eval(X, yv)
                fc.accuracy_oos = acc
                fc.brier_score = brier

                # Train final model on all available data for inference
                final_model = HistGradientBoostingClassifier(
                    max_iter=100, learning_rate=0.05, max_depth=4, random_state=42
                )
                final_cal = CalibratedClassifierCV(final_model, cv=3, method="sigmoid")
                final_cal.fit(X, yv)

                # Predict on latest available features (last row of feat_df, before horizon rows removed)
                latest_features = feat_df.dropna().iloc[-1:].fillna(0)
                proba = final_cal.predict_proba(latest_features)[0]
                fc.probability_up = float(proba[1])
                fc.probability_down = float(proba[0])

                # Expected return (crude proxy from historical conditional)
                pos_mask = yv == 1
                if pos_mask.sum() > 10:
                    historical_returns = future_ret.loc[X.index]
                    up_ret = float(historical_returns[pos_mask].mean() * 100)
                    down_ret = float(historical_returns[~pos_mask].mean() * 100)
                    fc.expected_return_pct = fc.probability_up * up_ret + fc.probability_down * down_ret
                else:
                    fc.expected_return_pct = (fc.probability_up - 0.5) * 10  # Simplified

                fc.expected_price = current_price * (1 + (fc.expected_return_pct or 0) / 100)

                # Price range (based on historical volatility for horizon)
                vol = float(close.pct_change().rolling(20).std().iloc[-1])
                horizon_vol = vol * math.sqrt(horizon)
                fc.lower_bound = current_price * (1 - horizon_vol * 1.65)
                fc.upper_bound = current_price * (1 + horizon_vol * 1.65)

                # Confidence: calibration quality (lower brier = better)
                calibration_quality = max(0, 1 - (brier / 0.25) * 0.5)
                accuracy_bonus = max(0, (acc - 0.5) * 2)
                fc.confidence = round(min(calibration_quality * 0.7 + accuracy_bonus * 0.3, 0.95), 2)
                fc.uncertainty = round(1.0 - fc.confidence, 2)

                # Quality warnings
                if acc < 0.52:
                    fc.warnings.append(f"Near-random accuracy ({acc:.1%}) — treat with high uncertainty")
                if brier > 0.27:
                    fc.warnings.append(f"Poor calibration (Brier={brier:.3f})")
                if horizon >= 60:
                    fc.warnings.append("Long horizon: high uncertainty, wide confidence interval")

                fc.status = "COMPUTED"

            except Exception as e:
                fc.status = "FAILED"
                fc.warnings.append(f"Computation error: {e}")

            results[horizon] = fc

        self._cache[ticker] = results
        return results


if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else "COMI.CA"
    print(f"\n{'='*70}")
    print(f"V42 Multi-Horizon Forecast: {ticker}")
    print(f"DATA MODE: YFinance PROXY | STATUS: EXPERIMENTAL")
    print(f"{'='*70}")

    engine = MultiHorizonForecastEngine()
    forecasts = engine.forecast(ticker)

    for h in HORIZONS:
        fc = forecasts[h]
        if fc.status == "COMPUTED":
            print(f"\n{h:>3}D Forecast: P(up)={fc.probability_up:.1%} | P(down)={fc.probability_down:.1%}")
            print(f"     Expected Return: {fc.expected_return_pct:+.1f}% | Expected Price: {fc.expected_price:.2f}")
            print(f"     Range: [{fc.lower_bound:.2f} – {fc.upper_bound:.2f}]")
            print(f"     Confidence: {fc.confidence:.0%} | Uncertainty: {fc.uncertainty:.0%}")
            print(f"     OOS Accuracy: {fc.accuracy_oos:.1%} | Brier: {fc.brier_score:.4f}")
        else:
            print(f"\n{h:>3}D Forecast: STATUS={fc.status} | {fc.warnings}")
