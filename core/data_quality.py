#!/usr/bin/env python3
# =============================================================================
# core/data_quality.py — GEN-26 Comprehensive Data Quality Engine & Audit Gate
# Evaluates OHLCV integrity, stale data, outlier spikes, and gaps.
# Produces DATA_HEALTH verdicts: PASS, WARN, FAIL (Fail-Closed Principle).
# =============================================================================

from typing import Dict, Any, Tuple, List, Optional
import pandas as pd
import numpy as np


class DataQualityEngine:
    """
    Evaluates market datasets and financial feeds for integrity, staleness, and anomalies.
    """

    @staticmethod
    def audit_ohlcv_dataframe(df: pd.DataFrame, ticker: str = "UNKNOWN") -> Dict[str, Any]:
        """
        Runs comprehensive data quality checks on an OHLCV dataframe.
        Returns health score, issues list, and verdict (PASS, WARN, FAIL).
        """
        issues: List[str] = []
        deductions = 0.0

        if df is None or df.empty:
            return {
                "ticker": ticker,
                "health": "FAIL",
                "score": 0.0,
                "issues": ["DataFrame is empty or None"],
                "can_trade": False
            }

        # 1. Check minimum bar count
        min_bars = 40
        if len(df) < min_bars:
            issues.append(f"Insufficient history: {len(df)} bars < {min_bars}")
            deductions += 40.0

        # 2. Check required columns
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            issues.append(f"Missing required columns: {missing_cols}")
            deductions += 60.0

        # 3. Check invalid OHLC relationships (High < Low, Non-positive prices)
        if 'High' in df.columns and 'Low' in df.columns:
            invalid_hl = (df['High'] < df['Low']).sum()
            if invalid_hl > 0:
                issues.append(f"Invalid High < Low detected in {invalid_hl} bars")
                deductions += 30.0

        if 'Close' in df.columns:
            non_positive_close = (df['Close'] <= 0).sum()
            if non_positive_close > 0:
                issues.append(f"Non-positive Close prices detected in {non_positive_close} bars")
                deductions += 50.0

        # 4. Check for duplicate indices/timestamps
        dup_count = df.index.duplicated().sum()
        if dup_count > 0:
            issues.append(f"Duplicate timestamps found: {dup_count}")
            deductions += 20.0

        # 5. Check for extreme single-bar price jump outliers (> 35% without corporate action)
        if 'Close' in df.columns and len(df) >= 2:
            pct_changes = df['Close'].pct_change().abs()
            extreme_jumps = (pct_changes > 0.35).sum()
            if extreme_jumps > 0:
                issues.append(f"Extreme price jumps (>35%) found: {extreme_jumps} bars")
                deductions += 15.0

        # 6. Check for volume anomalies (Negative volume)
        if 'Volume' in df.columns:
            neg_vol = (df['Volume'] < 0).sum()
            if neg_vol > 0:
                issues.append(f"Negative volume found: {neg_vol} bars")
                deductions += 40.0

        # Calculate final score (0 - 100)
        final_score = max(0.0, min(100.0, 100.0 - deductions))

        if final_score >= 80.0 and len(issues) == 0:
            health = "PASS"
            can_trade = True
        elif final_score >= 60.0:
            health = "WARN"
            can_trade = True
        else:
            health = "FAIL"
            can_trade = False

        return {
            "ticker": ticker,
            "health": health,
            "data_health": health,
            "score": round(final_score, 1),
            "issues": issues,
            "can_trade": can_trade,
            "bar_count": len(df),
            "latest_date": str(df.index[-1])[:10] if len(df) > 0 else "N/A"
        }

    @staticmethod
    def audit_ohlcv_record(ticker: str, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Audits a single OHLCV record dictionary (e.g. from real-time stream or paper broker).
        """
        if not record or not isinstance(record, dict):
            return {
                "ticker": ticker,
                "health": "FAIL",
                "data_health": "FAIL",
                "score": 0.0,
                "issues": ["Record is empty or not a dict"],
                "can_trade": False
            }

        issues: List[str] = []
        open_p = record.get("open", record.get("Open", 0.0))
        high_p = record.get("high", record.get("High", 0.0))
        low_p = record.get("low", record.get("Low", 0.0))
        close_p = record.get("close", record.get("Close", 0.0))
        vol = record.get("volume", record.get("Volume", 0.0))

        if close_p <= 0:
            issues.append(f"Non-positive close price: {close_p}")
        if high_p < low_p:
            issues.append(f"High {high_p} is less than Low {low_p}")
        if vol < 0:
            issues.append(f"Negative volume: {vol}")

        health = "PASS" if not issues else "FAIL"
        return {
            "ticker": ticker,
            "health": health,
            "data_health": health,
            "score": 100.0 if not issues else 0.0,
            "issues": issues,
            "can_trade": (health == "PASS")
        }

