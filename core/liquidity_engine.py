#!/usr/bin/env python3
# =============================================================================
# core/liquidity_engine.py — GEN-26 Liquidity, Capacity & Tradability Engine
# Computes Average Trading Value (ADV), turnover, price impact, and capacity
# estimates to ensure execution feasibility and prevent illiquid traps.
# =============================================================================

from typing import Dict, Any, Optional
import pandas as pd
import numpy as np


class LiquidityEngine:
    """
    Computes liquidity metrics, execution capacity, and days to liquidate.
    """

    # Minimum average daily turnover required for full 10% portfolio allocation
    MIN_DAILY_TURNOVER_EGP = 1_000_000.0  # 1 Million EGP / day

    @staticmethod
    def evaluate_liquidity(
        df: pd.DataFrame,
        target_position_value_egp: float = 100_000.0,
        max_adv_participation_rate: float = 0.05  # 5% max of daily volume
    ) -> Dict[str, Any]:
        """
        Computes ADV (20D), Turnover, Liquidity Score (0-100), and execution safety limits.
        """
        if df is None or df.empty or len(df) < 10:
            return {
                "liquidity_score": 0.0,
                "tradability_status": "ILLIQUID",
                "adv_20d_egp": 0.0,
                "days_to_liquidate": 99.0,
                "max_safe_position_egp": 0.0,
                "can_execute": False
            }

        # Calculate daily trading value = Volume * Close
        c = df['Close']
        v = df['Volume']
        daily_val = c * v
        adv_20d = float(daily_val.rolling(20, min_periods=5).mean().iloc[-1])
        vol_z = float(((v - v.rolling(20).mean()) / (v.rolling(20).std() + 1e-9)).iloc[-1])

        # Compute max safe position that can be liquidated within 1 session at 5% ADV
        max_safe_pos = adv_20d * max_adv_participation_rate

        # Days to liquidate target position
        daily_absorption = max(adv_20d * max_adv_participation_rate, 1000.0)
        days_to_liquidate = round(target_position_value_egp / daily_absorption, 1)

        # Liquidity Score (0 - 100)
        if adv_20d >= 10_000_000.0:  # 10M+ EGP/day (e.g. COMI, TMGH)
            liq_score = 100.0
            status = "HIGH_LIQUIDITY"
        elif adv_20d >= 3_000_000.0:  # 3M - 10M
            liq_score = 85.0
            status = "STRONG_LIQUIDITY"
        elif adv_20d >= 1_000_000.0:  # 1M - 3M
            liq_score = 70.0
            status = "MODERATE_LIQUIDITY"
        elif adv_20d >= 300_000.0:    # 300k - 1M
            liq_score = 45.0
            status = "THIN_LIQUIDITY"
        else:
            liq_score = 15.0
            status = "ILLIQUID"

        can_execute = adv_20d >= 500_000.0

        return {
            "liquidity_score": liq_score,
            "tradability_status": status,
            "adv_20d_egp": round(adv_20d, 2),
            "volume_zscore": round(max(-3.0, min(3.0, vol_z)), 2),
            "days_to_liquidate": days_to_liquidate,
            "max_safe_position_egp": round(max_safe_pos, 2),
            "can_execute": can_execute
        }
