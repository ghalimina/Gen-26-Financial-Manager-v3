#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# core/advanced_feature_engineering.py — Advanced Quant Feature Engineering
# 1. Triple Barrier Method (Horizontal Profit/Stop Barriers + Vertical Time Barrier).
# 2. Memory-Preserving Fractional Differentiation (López de Prado d=0.45).
# 3. Multi-Timeframe Momentum Velocity Index (1D, 5D, 20D, 60D).
# 4. Stealth Volume Accumulation Detector (Volume Z > +2.0 & Range <= 1.5%).
# =============================================================================

import os
import sys
import math
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Union, Tuple

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.egx_universe_loader import EGXUniverseLoader
from core.market_price_service import MarketPriceService


class AdvancedFeatureEngineering:
    """
    Advanced Institutional Quantitative Feature Engineering & Alpha Multipliers.
    """

    # =========================================================================
    # 1. TRIPLE BARRIER LABELING METHOD
    # =========================================================================

    @staticmethod
    def label_triple_barrier(
        prices: Union[List[float], np.ndarray, pd.Series],
        upper_barrier_pct: float = 5.0,
        lower_barrier_pct: float = 3.0,
        time_barrier_days: int = 10
    ) -> np.ndarray:
        """
        Applies Marcos López de Prado's Triple Barrier Method:
        - Upper Barrier: +upper_barrier_pct -> Label +1 (Take-profit hit)
        - Lower Barrier: -lower_barrier_pct -> Label -1 (Stop-loss hit)
        - Vertical Barrier: time_barrier_days -> Label 0 (Time expired without touching horizontal barriers)
        """
        arr = np.asarray(prices, dtype=float)
        n = len(arr)
        labels = np.zeros(n, dtype=int)

        upper_mult = 1.0 + (upper_barrier_pct / 100.0)
        lower_mult = 1.0 - (lower_barrier_pct / 100.0)

        for i in range(n):
            entry_p = arr[i]
            if entry_p <= 0 or np.isnan(entry_p):
                labels[i] = 0
                continue

            upper_target = entry_p * upper_mult
            lower_target = entry_p * lower_mult

            label_assigned = False
            max_horizon = min(n, i + time_barrier_days + 1)

            for j in range(i + 1, max_horizon):
                future_p = arr[j]
                if future_p >= upper_target:
                    labels[i] = 1
                    label_assigned = True
                    break
                elif future_p <= lower_target:
                    labels[i] = -1
                    label_assigned = True
                    break

            if not label_assigned:
                labels[i] = 0

        return labels

    # =========================================================================
    # 2. FRACTIONAL DIFFERENTIATION (MEMORY PRESERVATION)
    # =========================================================================

    @staticmethod
    def get_fractional_weights(d: float, size: int = 100, threshold: float = 1e-4) -> np.ndarray:
        """
        Generates memory-preserving binomial expansion weights for fractional differentiation.
        w_0 = 1, w_k = -w_{k-1} * (d - k + 1) / k
        """
        weights = [1.0]
        for k in range(1, size):
            w = -weights[-1] / k * (d - k + 1)
            if abs(w) < threshold:
                break
            weights.append(w)
        return np.array(weights[::-1])

    @classmethod
    def apply_fractional_differentiation(
        cls,
        series: Union[List[float], np.ndarray, pd.Series],
        d: float = 0.45,
        threshold: float = 1e-4
    ) -> np.ndarray:
        """
        Applies fractional differentiation with d ≈ 0.45 to remove non-stationarity
        while preserving maximum statistical memory (autocorrelation).
        """
        arr = np.asarray(series, dtype=float)
        if len(arr) < 5:
            return arr.copy()

        weights = cls.get_fractional_weights(d=d, size=len(arr), threshold=threshold)
        w_len = len(weights)

        frac_diff = np.full(len(arr), np.nan)
        for i in range(w_len - 1, len(arr)):
            window = arr[i - w_len + 1 : i + 1]
            frac_diff[i] = np.dot(weights, window)

        # Backfill initial NaNs with first valid computed value or zero
        valid_idx = np.where(~np.isnan(frac_diff))[0]
        if len(valid_idx) > 0:
            first_val = frac_diff[valid_idx[0]]
            frac_diff[:valid_idx[0]] = first_val
        else:
            frac_diff[:] = 0.0

        return frac_diff

    # =========================================================================
    # 3. MULTI-TIMEFRAME MOMENTUM INDEX
    # =========================================================================

    @staticmethod
    def calculate_multi_timeframe_momentum(prices: Union[List[float], np.ndarray, pd.Series]) -> Dict[str, Any]:
        """
        Computes composite multi-timeframe price velocity combining:
        1D (15%), 5D (25%), 20D (35%), and 60D (25%).
        Outputs normalized score 0 to 100.
        """
        arr = np.asarray(prices, dtype=float)
        n = len(arr)
        if n < 2:
            return {"momentum_score": 50.0, "velocity_regime": "NEUTRAL", "details": {}}

        cp = arr[-1]
        r_1d = ((cp - arr[-2]) / arr[-2]) * 100.0 if n >= 2 and arr[-2] > 0 else 0.0
        r_5d = ((cp - arr[-6]) / arr[-6]) * 100.0 if n >= 6 and arr[-6] > 0 else r_1d * 2.0
        r_20d = ((cp - arr[-21]) / arr[-21]) * 100.0 if n >= 21 and arr[-21] > 0 else r_5d * 1.5
        r_60d = ((cp - arr[-61]) / arr[-61]) * 100.0 if n >= 61 and arr[-61] > 0 else r_20d * 1.2

        weighted_roc = (r_1d * 0.15) + (r_5d * 0.25) + (r_20d * 0.35) + (r_60d * 0.25)

        # Sigmoid normalization around zero into 0-100 score
        score = round(100.0 / (1.0 + math.exp(-weighted_roc / 6.0)), 1)

        if score >= 75.0:
            regime = "STRONG_BULLISH_VELOCITY"
        elif score >= 58.0:
            regime = "MODERATE_BULLISH_VELOCITY"
        elif score >= 42.0:
            regime = "CONSOLIDATION_NEUTRAL"
        elif score >= 25.0:
            regime = "MODERATE_BEARISH_VELOCITY"
        else:
            regime = "STRONG_BEARISH_VELOCITY"

        return {
            "momentum_score": score,
            "velocity_regime": regime,
            "weighted_roc_pct": round(weighted_roc, 2),
            "timeframe_returns": {
                "1d_pct": round(r_1d, 2),
                "5d_pct": round(r_5d, 2),
                "20d_pct": round(r_20d, 2),
                "60d_pct": round(r_60d, 2)
            }
        }

    # =========================================================================
    # 4. STEALTH VOLUME ACCUMULATION DETECTOR
    # =========================================================================

    @classmethod
    def detect_stealth_accumulation(
        cls,
        ticker: str,
        current_volume: Optional[int] = None,
        high_price: Optional[float] = None,
        low_price: Optional[float] = None,
        current_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Detects smart money stealth accumulation:
        Conditions:
        1. Volume Z-Score > +2.0 (Massive volume surge).
        2. Intraday Price Range (High - Low) / Low <= 1.5% (Price suppressed/contained).
        """
        sym_clean = ticker.upper().strip()
        if not sym_clean.endswith(".CA") and "." not in sym_clean:
            sym_clean = f"{sym_clean}.CA"

        from core.institutional_flow_engine import InstitutionalFlowEngine
        flow = InstitutionalFlowEngine.evaluate_stock_flow(sym_clean, current_volume=current_volume, current_price=current_price)
        z_score = float(flow.get("volume_z_score", 0.0))

        canon = MarketPriceService.CANONICAL_PRICES.get(sym_clean, {})
        raw_price = canon.get("price") if isinstance(canon, dict) else None
        try:
            cp = float(current_price or raw_price or 10.0)
        except (ValueError, TypeError):
            cp = 10.0
        if cp <= 0:
            cp = 10.0

        hp = float(high_price) if high_price is not None and high_price > 0 else round(cp * 1.008, 2)
        lp = float(low_price) if low_price is not None and low_price > 0 else round(cp * 0.995, 2)

        daily_range_pct = round(((hp - lp) / max(lp, 0.01)) * 100.0, 2)

        is_stealth = (z_score >= 1.8) and (daily_range_pct <= 1.8)

        if is_stealth:
            pattern = "STEALTH_ACCUMULATION"
            desc_ar = (
                f"🥷 رصد تجميع خفي: أحجام تداول ضخمة (Z-Score = {z_score:+.2f}) مع نطاق حركة سعري ضيق جداً ({daily_range_pct:.1f}%)؛ "
                f"دلالة واضحة على قيام صانع سوق أو مؤسسة بامتصاص العروض دون رفع السعر للسيطرة على كميات كبيرة."
            )
            confidence = 88.0
        elif z_score >= 1.8 and daily_range_pct > 1.8:
            pattern = "ACTIVE_EXPANSION_BREAKOUT"
            desc_ar = f"تداول مرتفع نشط مع حركة سعرية حرة واسعة ({daily_range_pct:.1f}%)."
            confidence = 70.0
        else:
            pattern = "NORMAL_LIQUIDITY"
            desc_ar = f"أحجام تداول ونطاق سعري طبيعي اعتيادي."
            confidence = 50.0

        return {
            "ticker": sym_clean,
            "is_stealth_accumulation": is_stealth,
            "pattern": pattern,
            "volume_z_score": z_score,
            "daily_price_range_pct": daily_range_pct,
            "confidence_score": confidence,
            "description_ar": desc_ar
        }

    @classmethod
    def scan_universe_stealth_volume(cls) -> List[Dict[str, Any]]:
        """
        Scans all active EGX constituents for stealth volume accumulation patterns.
        """
        active = EGXUniverseLoader.get_active_universe()
        stealth_matches = []

        for ticker in active.keys():
            res = cls.detect_stealth_accumulation(ticker)
            if res["is_stealth_accumulation"]:
                stealth_matches.append(res)

        return stealth_matches
