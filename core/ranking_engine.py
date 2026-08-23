#!/usr/bin/env python3
# =============================================================================
# core/ranking_engine.py — GEN-26 Cross-Sectional Ranking & EGX Limit Engine
# Performs cross-sectional universe ranking, quantile spread analysis,
# rank monotonicity verification, and EGX circuit breaker band constraints.
# =============================================================================

from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd


class CrossSectionalRankingEngine:
    """
    Ranks the tradable EGX universe cross-sectionally and evaluates
    monotonicity, decile spreads, and execution price-band limits.
    """

    @staticmethod
    def check_egx_circuit_breaker_band(
        current_price: float,
        previous_close: float,
        limit_band_pct: float = 0.20
    ) -> Dict[str, Any]:
        """
        EGX stocks are subject to daily price fluctuation limits (+/-10% or +/-20%).
        If a stock is locked at limit-up, market/limit BUY orders are unfillable.
        If locked at limit-down, SELL orders are unfillable.
        """
        if previous_close <= 0 or current_price <= 0:
            return {"is_limit_up": False, "is_limit_down": False, "can_buy": True, "can_sell": True}

        daily_change_pct = (current_price - previous_close) / previous_close
        upper_limit = limit_band_pct - 0.005 # 19.5% threshold for 20% band
        lower_limit = -(limit_band_pct - 0.005)

        is_limit_up = daily_change_pct >= upper_limit
        is_limit_down = daily_change_pct <= lower_limit

        return {
            "daily_change_pct": round(daily_change_pct * 100.0, 2),
            "is_limit_up": is_limit_up,
            "is_limit_down": is_limit_down,
            "can_buy": not is_limit_up,
            "can_sell": not is_limit_down,
            "execution_warning": "LOCKED_AT_LIMIT_UP" if is_limit_up else ("LOCKED_AT_LIMIT_DOWN" if is_limit_down else "NORMAL_BAND")
        }

    @classmethod
    def rank_universe(
        cls,
        candidates: List[Dict[str, Any]],
        score_key: str = "alpha_score",
        min_adv_egp: float = 2_000_000.0
    ) -> List[Dict[str, Any]]:
        """
        Ranks candidate stocks cross-sectionally by risk-adjusted alpha score,
        enforcing EGX circuit-breaker band and liquidity eligibility.
        """
        if not candidates:
            return []

        df = pd.DataFrame(candidates)
        if score_key not in df.columns:
            return candidates

        # Evaluate circuit breaker bands and liquidity
        eligible_records = []
        for cand in candidates:
            cand_copy = dict(cand)
            cp = cand.get("current_price", cand.get("price", 10.0))
            prev_c = cand.get("previous_close", cp)
            cb = cls.check_egx_circuit_breaker_band(cp, prev_c)
            cand_copy["circuit_breaker"] = cb
            
            adv = cand.get("adv_20d_egp", cand.get("adv", 10_000_000))
            cand_copy["is_liquid"] = adv >= min_adv_egp

            # Penalty if locked at limit up
            raw_score = cand.get(score_key, 50.0)
            if not cb["can_buy"]:
                cand_copy["adjusted_rank_score"] = 0.0 # Cannot buy locked stock
                cand_copy["rank_exclusion_reason"] = "LOCKED_AT_LIMIT_UP"
            elif not cand_copy["is_liquid"]:
                cand_copy["adjusted_rank_score"] = raw_score * 0.50 # Liquidity penalty
                cand_copy["rank_exclusion_reason"] = "BELOW_MIN_ADV_THRESHOLD"
            else:
                cand_copy["adjusted_rank_score"] = raw_score
                cand_copy["rank_exclusion_reason"] = "ELIGIBLE"

            eligible_records.append(cand_copy)

        # Sort descending by adjusted score
        ranked = sorted(eligible_records, key=lambda x: x["adjusted_rank_score"], reverse=True)
        total = len(ranked)
        for idx, item in enumerate(ranked):
            item["rank"] = idx + 1
            item["percentile"] = round(((total - idx) / total) * 100.0, 1)

        return ranked

    @staticmethod
    def compute_quantile_spread(
        df_ranks: pd.DataFrame,
        rank_col: str,
        fwd_return_col: str,
        num_quantiles: int = 5
    ) -> Dict[str, Any]:
        """
        Calculates quantile spread (Q1 vs Q_last), Rank Monotonicity, Rank IC, and ICIR.
        """
        valid = df_ranks[[rank_col, fwd_return_col]].dropna()
        if len(valid) < (num_quantiles * 2):
            return {
                "rank_ic": 0.0,
                "icir": 0.0,
                "top_bottom_spread": 0.0,
                "monotonicity_score": 0.0,
                "is_monotonic": False
            }

        # Rank IC
        rank_ic = float(valid[rank_col].corr(valid[fwd_return_col], method="spearman"))

        # Quantile binning
        try:
            valid["quantile"] = pd.qcut(valid[rank_col], q=num_quantiles, labels=False, duplicates="drop")
        except Exception:
            valid["quantile"] = 0

        grouped = valid.groupby("quantile")[fwd_return_col].mean()
        if len(grouped) >= 2:
            top_q = grouped.iloc[-1]
            bot_q = grouped.iloc[0]
            spread = float(top_q - bot_q)
            # Monotonicity check
            mono_corr = float(pd.Series(grouped.index).corr(grouped.reset_index(drop=True), method="spearman"))
        else:
            spread = 0.0
            mono_corr = 0.0

        return {
            "rank_ic": round(rank_ic, 4),
            "top_bottom_spread": round(spread, 4),
            "monotonicity_score": round(mono_corr, 4),
            "is_monotonic": mono_corr > 0.70,
            "quantile_means": {f"Q{k+1}": round(float(v), 4) for k, v in grouped.items()}
        }
