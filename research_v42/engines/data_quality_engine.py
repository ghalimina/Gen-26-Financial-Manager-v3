"""
research_v42/engines/data_quality_engine.py

Data Quality Engine — GEN-26 V42 Research Layer
STATUS: RESEARCH / SHADOW — Does NOT affect V4.1 execution
"""
from __future__ import annotations
import datetime
import math
import pytz
from dataclasses import dataclass, field
from typing import Optional, Any

CAIRO_TZ = pytz.timezone("Africa/Cairo")


@dataclass
class DataPoint:
    """
    Standardized wrapper for every data value in V42.
    Prevents silent failures on missing, stale, or proxy data.
    """
    metric: str
    value: Any
    source: str = "UNKNOWN"
    source_timestamp: Optional[str] = None
    received_timestamp: Optional[str] = None
    period: Optional[str] = None          # e.g. "2026-Q1"
    availability_date: Optional[str] = None   # Point-in-time: when was this actually public?
    data_mode: str = "UNKNOWN"           # REALTIME | NEAR_REALTIME | DELAYED | EOD | PROXY
    quality: str = "UNKNOWN"             # VERIFIED | PROXY | PARTIAL | STALE | MISSING | INVALID
    confidence: float = 0.0              # 0..1

    def is_usable(self) -> bool:
        return (
            self.quality in ("VERIFIED", "PROXY", "PARTIAL")
            and self.value is not None
            and not (isinstance(self.value, float) and math.isnan(self.value))
        )

    def to_dict(self) -> dict:
        return {
            "metric": self.metric,
            "value": self.value if self.is_usable() else None,
            "source": self.source,
            "source_timestamp": self.source_timestamp,
            "data_mode": self.data_mode,
            "quality": self.quality,
            "confidence": self.confidence,
            "is_usable": self.is_usable(),
        }


class DataQualityResult:
    PASS = "PASS"
    WARN = "WARN"
    BLOCK = "BLOCK"

    def __init__(self, status: str, quality_score: float, issues: list[str]):
        self.status = status          # PASS | WARN | BLOCK
        self.quality_score = quality_score  # 0..100
        self.issues = issues

    def __repr__(self):
        return f"DataQualityResult({self.status}, score={self.quality_score:.1f}, issues={self.issues})"


class DataQualityEngine:
    """
    Validates data points before they enter any model or decision.
    Returns PASS / WARN / BLOCK with quality score and issue list.
    """

    MAX_PRICE_AGE_MINUTES = 60        # For intraday sessions
    MIN_VOLUME_THRESHOLD = 100_000    # EGP traded volume minimum

    @staticmethod
    def check_price_freshness(
        market_time_str: Optional[str],
        max_age_minutes: int = 60
    ) -> tuple[str, float]:
        """
        Returns (status, age_minutes).
        status: FRESH | STALE_WARNING | STALE_BLOCKED | UNKNOWN
        """
        if not market_time_str:
            return "UNKNOWN", 999_999.0

        try:
            formats = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"]
            dt = None
            for fmt in formats:
                try:
                    dt = datetime.datetime.strptime(market_time_str, fmt)
                    break
                except ValueError:
                    continue

            if dt is None:
                return "UNKNOWN", 999_999.0

            if dt.tzinfo is None:
                dt = CAIRO_TZ.localize(dt)

            now = datetime.datetime.now(CAIRO_TZ)
            age_minutes = (now - dt).total_seconds() / 60.0

            if age_minutes <= max_age_minutes:
                return "FRESH", age_minutes
            elif age_minutes <= max_age_minutes * 4:
                return "STALE_WARNING", age_minutes
            else:
                return "STALE_BLOCKED", age_minutes

        except Exception:
            return "UNKNOWN", 999_999.0

    @staticmethod
    def validate_price(price: Any, ticker: str = "") -> DataQualityResult:
        issues = []
        if price is None:
            return DataQualityResult(DataQualityResult.BLOCK, 0.0, [f"{ticker}: Price is None"])
        try:
            p = float(price)
        except (TypeError, ValueError):
            return DataQualityResult(DataQualityResult.BLOCK, 0.0, [f"{ticker}: Price not numeric ({price})"])

        if math.isnan(p) or math.isinf(p):
            return DataQualityResult(DataQualityResult.BLOCK, 0.0, [f"{ticker}: Price is NaN/Inf"])
        if p <= 0:
            return DataQualityResult(DataQualityResult.BLOCK, 0.0, [f"{ticker}: Price <= 0 ({p})"])
        if p > 100_000:
            issues.append(f"{ticker}: Price suspiciously high ({p})")

        score = 100.0 if not issues else 70.0
        status = DataQualityResult.WARN if issues else DataQualityResult.PASS
        return DataQualityResult(status, score, issues)

    @staticmethod
    def validate_dataframe(df, required_cols: list[str], ticker: str = "") -> DataQualityResult:
        import pandas as pd
        issues = []

        if df is None or (hasattr(df, 'empty') and df.empty):
            return DataQualityResult(DataQualityResult.BLOCK, 0.0, [f"{ticker}: DataFrame is empty/None"])

        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            issues.append(f"{ticker}: Missing columns: {missing}")

        nan_pct = df[required_cols].isnull().mean().mean() * 100 if not missing else 100.0
        if nan_pct > 50:
            issues.append(f"{ticker}: >50% NaN in price data ({nan_pct:.1f}%)")
        elif nan_pct > 10:
            issues.append(f"{ticker}: >10% NaN in price data ({nan_pct:.1f}%)")

        if len(df) < 60:
            issues.append(f"{ticker}: Insufficient history ({len(df)} rows, need 60+)")

        # Future timestamp check
        try:
            now = datetime.datetime.now(CAIRO_TZ)
            latest = pd.to_datetime(df.index[-1])
            if hasattr(latest, 'tzinfo') and latest.tzinfo is None:
                latest = CAIRO_TZ.localize(latest)
            if hasattr(latest, 'tzinfo'):
                future_rows = (df.index > latest).sum()
                if future_rows > 0:
                    issues.append(f"{ticker}: LEAKAGE RISK — {future_rows} future timestamps detected!")
        except Exception:
            pass

        if any("LEAKAGE" in i for i in issues):
            return DataQualityResult(DataQualityResult.BLOCK, 0.0, issues)

        score = max(0.0, 100.0 - nan_pct - (len(issues) * 10))
        status = (DataQualityResult.BLOCK if score < 30
                  else DataQualityResult.WARN if score < 70
                  else DataQualityResult.PASS)
        return DataQualityResult(status, score, issues)

    @classmethod
    def validate_fundamental(cls, metric_name: str, value: Any) -> DataPoint:
        """Wraps a fundamental value in DataPoint with quality label."""
        if value is None:
            return DataPoint(metric=metric_name, value=None, quality="MISSING", source="YFinance")

        try:
            v = float(value)
            import math
            if math.isnan(v) or math.isinf(v):
                return DataPoint(metric=metric_name, value=None, quality="INVALID", source="YFinance")
            return DataPoint(
                metric=metric_name, value=v,
                quality="PROXY",  # YFinance fundamentals are always PROXY for EGX
                data_mode="EOD",
                source="YFinance",
                confidence=0.6
            )
        except (TypeError, ValueError):
            return DataPoint(metric=metric_name, value=None, quality="INVALID", source="YFinance")
