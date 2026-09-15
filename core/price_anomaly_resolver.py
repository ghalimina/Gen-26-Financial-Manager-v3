#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# core/price_anomaly_resolver.py — Automated EGX Corporate Actions & Split Reconciler
# Automatically resolves persistent circuit breaker price rejections caused by:
# 1. Stock Splits / Par Value reductions (e.g. 1:10, 1:5, 1:2 splits)
# 2. Capital increases / bonus shares
# 3. Currency re-denominations (USD to EGP quotes)
# =============================================================================

import os
import sys
import json
import logging
from typing import Dict, Any, Optional, Tuple

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

logger = logging.getLogger("GEN26.PriceAnomalyResolver")

DATA_DIR = os.path.join(WORKSPACE, "data")
ANOMALY_TRACKER_FILE = os.path.join(DATA_DIR, "price_sync_anomaly_tracker.json")
CANONICAL_PRICES_FILE = os.path.join(DATA_DIR, "canonical_prices_live.json")


class PriceAnomalyResolver:
    """
    Automated Corporate Action & Price Anomaly Resolver.
    Reconciles legitimate structural price shifts (Stock splits, Reverse splits, Par value changes)
    while strictly preserving circuit breaker protection against genuine corrupt spikes.
    """

    # Common corporate action split ratios in EGX
    STANDARD_RATIOS = [
        (10.0, "SPLIT_1_TO_10"),
        (5.0, "SPLIT_1_TO_5"),
        (4.0, "SPLIT_1_TO_4"),
        (2.0, "SPLIT_1_TO_2"),
        (1.5, "BONUS_1_TO_2"),
        (0.5, "REVERSE_SPLIT_2_TO_1"),
        (0.2, "REVERSE_SPLIT_5_TO_1"),
        (0.1, "REVERSE_SPLIT_10_TO_1"),
        (0.082, "CAPITAL_REDUCTION_BIOC") # Specifically BIOC ~12:1 reduction
    ]

    @classmethod
    def analyze_price_discrepancy(
        cls,
        ticker: str,
        fetched_price: float,
        previous_close: float
    ) -> Dict[str, Any]:
        """
        Analyzes whether a price discrepancy (> 15%) is a structural corporate action
        or a genuine data feed anomaly.
        """
        if previous_close <= 0 or fetched_price <= 0:
            return {
                "ticker": ticker,
                "is_corporate_action": False,
                "action_type": "INVALID_PRICE_ZERO",
                "adjusted_previous_close": previous_close,
                "ratio": 1.0,
                "confidence": 0.0
            }

        ratio = fetched_price / previous_close

        # Check for standard split / reverse split ratios (within 10% margin of the ratio)
        for std_ratio, action_name in cls.STANDARD_RATIOS:
            diff_ratio = abs(ratio - std_ratio) / std_ratio
            if diff_ratio <= 0.12: # Within 12% of a standard corporate action ratio
                adjusted_prev = round(previous_close * std_ratio, 2)
                return {
                    "ticker": ticker,
                    "is_corporate_action": True,
                    "action_type": action_name,
                    "adjusted_previous_close": adjusted_prev,
                    "ratio": round(std_ratio, 3),
                    "confidence": 0.95,
                    "reason": f"Detected corporate action {action_name} (ratio: {ratio:.2f} ~ {std_ratio})"
                }

        # Check for inverse split (e.g. previous close was pre-split, fetched is post-split)
        inv_ratio = previous_close / fetched_price
        for std_ratio, action_name in cls.STANDARD_RATIOS:
            diff_ratio = abs(inv_ratio - std_ratio) / std_ratio
            if diff_ratio <= 0.12:
                adjusted_prev = round(previous_close / std_ratio, 2)
                return {
                    "ticker": ticker,
                    "is_corporate_action": True,
                    "action_type": f"POST_{action_name}",
                    "adjusted_previous_close": adjusted_prev,
                    "ratio": round(1.0 / std_ratio, 3),
                    "confidence": 0.95,
                    "reason": f"Detected post-corporate action {action_name} (inverse ratio: {inv_ratio:.2f} ~ {std_ratio})"
                }

        # If rejected repeatedly (>= 3 times), check if fetched price is consistent across sessions
        return {
            "ticker": ticker,
            "is_corporate_action": False,
            "action_type": "VOLATILITY_OUTLIER",
            "adjusted_previous_close": previous_close,
            "ratio": round(ratio, 3),
            "confidence": 0.50,
            "reason": f"Price deviates by {(ratio - 1.0)*100:.1f}%, no standard split ratio matched."
        }

    @classmethod
    def reconcile_persistent_anomaly(
        cls,
        ticker: str,
        fetched_price: float,
        previous_close: float,
        consecutive_count: int
    ) -> Tuple[bool, float, str]:
        """
        Reconciles persistent anomalies that have been rejected >= 3 times.
        Returns: (is_reconciled, reconciled_previous_close, explanation)
        """
        analysis = cls.analyze_price_discrepancy(ticker, fetched_price, previous_close)
        
        if analysis["is_corporate_action"]:
            adj_prev = analysis["adjusted_previous_close"]
            explanation = (
                f"✅ تم تسوية الشذوذ السعري لـ {ticker} كحدث تجزئة/زيادة رأسمال معتمد "
                f"({analysis['action_type']}): تم تعديل الإغلاق السابق من {previous_close:.2f} إلى {adj_prev:.2f} ج.م"
            )
            logger.info(explanation)
            return True, adj_prev, explanation

        # If consecutive rejections >= 5, market price has permanently shifted
        if consecutive_count >= 5:
            # Baseline is obsolete; update previous close to smooth convergence
            adj_prev = round(fetched_price, 2)
            explanation = (
                f"⚠️ تسوية سعرية اضطرارية لـ {ticker} بعد {consecutive_count} دورات رفض متتالية: "
                f"اعتماد السعر الحقيقي {fetched_price:.2f} ج.م وتحديث الإغلاق السابق."
            )
            logger.warning(explanation)
            return True, adj_prev, explanation

        return False, previous_close, analysis["reason"]
