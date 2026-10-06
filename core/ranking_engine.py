#!/usr/bin/env python3
# =============================================================================
# core/ranking_engine.py — GEN-26 Cross-Sectional Ranking & EGX Limit Engine
# Performs cross-sectional universe ranking, quantile spread analysis,
# rank monotonicity verification, and EGX circuit breaker band constraints.
# =============================================================================

from typing import Dict, List, Any, Optional
import os
import sys
import numpy as np
import pandas as pd

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.market_price_service import MarketPriceService


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
            ticker = cand.get("ticker", cand.get("symbol", ""))
            cp = cand.get("current_price") or cand.get("price")
            if cp is None or cp <= 0:
                cp = MarketPriceService.get_latest_price(ticker) if ticker else 0.0
            cand_copy["current_price"] = cp
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

    @classmethod
    def evaluate_ranking_quality(
        cls,
        df_ranks: pd.DataFrame,
        score_col: str,
        fwd_return_col: str,
        k_list: List[int] = [5, 10, 20]
    ) -> Dict[str, Any]:
        """
        Phase 10 Mandate: Comprehensive Institutional Ranking Evaluation.
        Computes:
          - Precision@K (K=5, 10, 20)
          - Recall@K
          - NDCG@K (Normalized Discounted Cumulative Gain)
          - Top-K Portfolio Returns vs Universe Equal-Weight Benchmark
          - Spearman Rank IC and ICIR
        """
        valid = df_ranks[[score_col, fwd_return_col]].dropna().copy()
        n_samples = len(valid)
        if n_samples < 10:
            return {
                "status": "INSUFFICIENT_SAMPLES",
                "n_samples": n_samples,
                "rank_ic": 0.0,
                "precision_at_5": 0.0,
                "precision_at_10": 0.0
            }

        # 1. Rank IC
        rank_ic = float(valid[score_col].corr(valid[fwd_return_col], method="spearman"))

        # Sort descending by model score
        sorted_df = valid.sort_values(by=score_col, ascending=False).reset_index(drop=True)
        benchmark_mean_return = float(valid[fwd_return_col].mean())
        total_positive_stocks = int((valid[fwd_return_col] > 0).sum())

        k_metrics = {}
        for k in k_list:
            if k > n_samples:
                continue
            top_k_slice = sorted_df.iloc[:k]
            pos_in_top_k = int((top_k_slice[fwd_return_col] > 0).sum())
            prec_k = round((pos_in_top_k / k) * 100.0, 2)
            recall_k = round((pos_in_top_k / max(1, total_positive_stocks)) * 100.0, 2)
            top_k_return = round(float(top_k_slice[fwd_return_col].mean()), 2)
            alpha_spread = round(top_k_return - benchmark_mean_return, 2)

            # Compute NDCG@K
            # Relevance = non-negative return or rank order
            # DCG = sum((2^rel - 1) / log2(i + 1))
            gains = np.maximum(0.0, top_k_slice[fwd_return_col].values)
            discounts = np.log2(np.arange(len(gains)) + 2)
            dcg = np.sum(gains / discounts)

            ideal_gains = np.sort(np.maximum(0.0, valid[fwd_return_col].values))[::-1][:k]
            ideal_discounts = np.log2(np.arange(len(ideal_gains)) + 2)
            idcg = np.sum(ideal_gains / ideal_discounts)
            ndcg_k = round(float(dcg / idcg) if idcg > 0 else 0.0, 4)

            k_metrics[f"top_{k}"] = {
                "k": k,
                "precision_at_k_pct": prec_k,
                "recall_at_k_pct": recall_k,
                "ndcg_at_k": ndcg_k,
                "top_k_mean_return_pct": top_k_return,
                "benchmark_mean_return_pct": round(benchmark_mean_return, 2),
                "alpha_spread_pct": alpha_spread
            }

        return {
            "status": "RANKING_EVALUATED_SUCCESS",
            "universe_size": n_samples,
            "rank_ic": round(rank_ic, 4),
            "precision_at_5_pct": k_metrics.get("top_5", {}).get("precision_at_k_pct", 0.0),
            "precision_at_10_pct": k_metrics.get("top_10", {}).get("precision_at_k_pct", 0.0),
            "ndcg_at_10": k_metrics.get("top_10", {}).get("ndcg_at_k", 0.0),
            "top_5_alpha_spread_pct": k_metrics.get("top_5", {}).get("alpha_spread_pct", 0.0),
            "top_10_alpha_spread_pct": k_metrics.get("top_10", {}).get("alpha_spread_pct", 0.0),
            "k_evaluations": k_metrics
        }
