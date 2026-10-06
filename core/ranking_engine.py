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

    @classmethod
    def detect_pullback_setup(
        cls,
        df_bars: pd.DataFrame,
        current_idx: int,
        is_market_bull: bool = True
    ) -> Dict[str, Any]:
        """
        Engine 1: Pullback Dip-Buyer Engine
        Entry Conditions:
          1. EGX30 Index > SMA50 (is_market_bull is True).
          2. Stock in Uptrend: Close >= SMA50 or Close >= SMA100.
          3. Calm Pullback: 30 <= RSI14 <= 48 OR Close <= Lower BB(20, 2) * 1.01.
          4. Volume Dry-Up: Volume < ADV20.
        Exit & Risk Rules:
          - Stop-Loss: -3.5% below pullback low (low_price * (1.0 - 0.035)).
          - Target: Rebound to channel mean (+7.0% to +9.0%, default +8.0%).
          - Horizon: 10 sessions.
          - Strategy Type: 'STRATEGY_PULLBACK'.
        """
        if not is_market_bull or df_bars.empty or current_idx < 50:
            return {"is_valid": False, "reason": "MARKET_BEAR_OR_INSUFFICIENT_BARS"}

        c = df_bars["close_price"].values
        v = df_bars["volume"].values
        h = df_bars["high_price"].values
        l = df_bars["low_price"].values

        cur_c = float(c[current_idx])
        cur_v = float(v[current_idx])
        cur_l = float(l[current_idx])

        # 1. Uptrend Check (Close >= SMA50 or Close >= SMA100)
        sma50 = float(np.mean(c[current_idx - 49 : current_idx + 1]))
        sma100_start = max(0, current_idx - 99)
        sma100 = float(np.mean(c[sma100_start : current_idx + 1]))
        in_uptrend = (cur_c >= sma50) or (cur_c >= sma100)
        if not in_uptrend:
            return {"is_valid": False, "reason": "NOT_IN_UPTREND"}

        # 2. Volume Dry-Up Check (Volume < ADV20)
        adv20 = float(np.mean(v[max(0, current_idx - 19) : current_idx + 1]))
        is_vol_dryup = cur_v < adv20
        if not is_vol_dryup:
            return {"is_valid": False, "reason": "NO_VOLUME_DRYUP"}

        # 3. RSI 14
        delta = pd.Series(c[current_idx - 20 : current_idx + 1]).diff()
        gain = delta.where(delta > 0, 0.0).tail(14).mean()
        loss = (-delta.where(delta < 0, 0.0)).tail(14).mean()
        rs = gain / max(loss, 1e-6)
        rsi14 = float(100.0 - (100.0 / (1.0 + rs)))

        # 4. Bollinger Bands (20, 2)
        bb_mid = float(np.mean(c[max(0, current_idx - 19) : current_idx + 1]))
        bb_std = float(np.std(c[max(0, current_idx - 19) : current_idx + 1]))
        bb_lower = bb_mid - 2.0 * bb_std

        is_calm_pullback = (30.0 <= rsi14 <= 48.0) or (cur_c <= bb_lower * 1.01)
        if not is_calm_pullback:
            return {"is_valid": False, "reason": "RSI_OR_BB_NOT_IN_PULLBACK_ZONE"}

        # ATR 14
        tr = np.maximum(
            h[current_idx - 13 : current_idx + 1] - l[current_idx - 13 : current_idx + 1],
            np.abs(h[current_idx - 13 : current_idx + 1] - c[current_idx - 14 : current_idx])
        )
        atr_14 = float(np.mean(tr))

        # Risk parameters: stop at -3.5% below pullback low
        stop_loss_price = round(cur_l * (1.0 - 0.035), 2)
        target_pct = 8.0  # Rebound to channel mean (+7.0% to +9.0%)
        stop_pct = -3.5

        sig_date = df_bars.iloc[current_idx]["market_date"]
        sig_date_str = sig_date.strftime("%Y-%m-%d") if hasattr(sig_date, "strftime") else str(sig_date)[:10]

        return {
            "is_valid": True,
            "strategy_type": "STRATEGY_PULLBACK",
            "signal_date": sig_date_str,
            "ticker": df_bars.iloc[current_idx].get("ticker", ""),
            "pullback_low": cur_l,
            "stop_loss_price": stop_loss_price,
            "stop_loss_pct": stop_pct,
            "take_profit_pct": target_pct,
            "holding_days": 10,
            "rsi_14": round(rsi14, 2),
            "atr_14": round(atr_14, 2),
            "is_vol_dryup": True,
            "volume_z_score": round((cur_v - adv20) / max(float(np.std(v[max(0, current_idx - 19) : current_idx + 1])), 1.0), 2),
            "score": round(50.0 + (48.0 - rsi14) * 2.0, 1)
        }

    @classmethod
    def detect_trend_breakout_setup(
        cls,
        df_bars: pd.DataFrame,
        current_idx: int,
        is_market_bull: bool = True
    ) -> Dict[str, Any]:
        """
        Engine 2: Asymmetric Trend Rider Engine
        Entry Conditions:
          1. EGX30 Index > SMA50 (is_market_bull is True).
          2. Stock in Trend: Close > BB_Mid (SMA20) and Close > SMA50.
          3. Momentum: 50 <= RSI14 <= 72.
          4. Volume Surge: Volume Z-Score > 1.5.
        Exit & Risk Rules:
          - Dynamic Trailing Stop: Trailing Stop = Peak High - (1.5 * ATR14) at +8.0%.
          - Break-even Lock: Stop raised to Entry + 0.50% at +4.0%.
          - Target: Asymmetric extension (+15% to +25%, default +20.0%).
          - Horizon: extended to 25 sessions.
          - Strategy Type: 'STRATEGY_TREND_BREAKOUT'.
        """
        if not is_market_bull or df_bars.empty or current_idx < 50:
            return {"is_valid": False, "reason": "MARKET_BEAR_OR_INSUFFICIENT_BARS"}

        c = df_bars["close_price"].values
        v = df_bars["volume"].values
        h = df_bars["high_price"].values
        l = df_bars["low_price"].values

        cur_c = float(c[current_idx])
        cur_v = float(v[current_idx])

        # 1. Trend and Moving Averages
        sma50 = float(np.mean(c[current_idx - 49 : current_idx + 1]))
        bb_mid = float(np.mean(c[max(0, current_idx - 19) : current_idx + 1]))
        if not (cur_c > bb_mid and cur_c > sma50):
            return {"is_valid": False, "reason": "NOT_ABOVE_SMA50_AND_BB_MID"}

        # 2. Volume Surge Check (Z > 1.5)
        adv20 = float(np.mean(v[max(0, current_idx - 19) : current_idx + 1]))
        v_std = float(np.std(v[max(0, current_idx - 19) : current_idx + 1]))
        vol_z = float((cur_v - adv20) / max(v_std, 1.0))
        if vol_z <= 1.5:
            return {"is_valid": False, "reason": "VOLUME_Z_NOT_ABOVE_1_5"}

        # 3. RSI 14
        delta = pd.Series(c[current_idx - 20 : current_idx + 1]).diff()
        gain = delta.where(delta > 0, 0.0).tail(14).mean()
        loss = (-delta.where(delta < 0, 0.0)).tail(14).mean()
        rs = gain / max(loss, 1e-6)
        rsi14 = float(100.0 - (100.0 / (1.0 + rs)))
        if not (50.0 <= rsi14 <= 72.0):
            return {"is_valid": False, "reason": "RSI_NOT_IN_BREAKOUT_MOMENTUM_ZONE"}

        # ATR 14
        tr = np.maximum(
            h[current_idx - 13 : current_idx + 1] - l[current_idx - 13 : current_idx + 1],
            np.abs(h[current_idx - 13 : current_idx + 1] - c[current_idx - 14 : current_idx])
        )
        atr_14 = float(np.mean(tr))

        sig_date = df_bars.iloc[current_idx]["market_date"]
        sig_date_str = sig_date.strftime("%Y-%m-%d") if hasattr(sig_date, "strftime") else str(sig_date)[:10]

        return {
            "is_valid": True,
            "strategy_type": "STRATEGY_TREND_BREAKOUT",
            "signal_date": sig_date_str,
            "ticker": df_bars.iloc[current_idx].get("ticker", ""),
            "stop_loss_pct": -5.0,
            "take_profit_pct": 20.0,
            "holding_days": 25,
            "rsi_14": round(rsi14, 2),
            "atr_14": round(atr_14, 2),
            "volume_z_score": round(vol_z, 2),
            "score": round(50.0 + vol_z * 10.0, 1)
        }

    @classmethod
    def select_top_k_candidates(
        cls,
        candidates: List[Dict[str, Any]],
        k: int = 3,
        min_dqs: float = 85.0,
        min_volume_zscore: float = 1.5,
        min_expected_net_return: float = 0.50,
        market_mode: str = "SELECTIVE_TRADING"
    ) -> List[Dict[str, Any]]:
        """
        Mission 3 & Dual-Engine Mandate: Strict Top-3 Selection & Over-Selectivity Gate:
        - If market_mode == 'CASH_PRESERVATION': Returns [] (0 signals, 100% Cash).
        - Filters candidates strictly:
          * DQS >= 85.0 (Data Quality Score).
          * Strategy-specific liquidity gate:
            - STRATEGY_PULLBACK: Volume Dry-up verified (Volume < ADV20 or is_vol_dryup=True).
            - STRATEGY_TREND_BREAKOUT: Volume Z-Score > 1.5 (Abnormal institutional surge).
          * Calibrated E[R_net] > 0.50% (Hard Ban cleared).
        - Ranks remaining candidates descending by calibrated E[R_net] or score.
        - Returns at most Top K (default k=3) stocks for execution.
        """
        if market_mode == "CASH_PRESERVATION":
            return []

        if not candidates:
            return []

        filtered = []
        for cand in candidates:
            cand_copy = dict(cand)
            strat = cand_copy.get("strategy_type", "STRATEGY_TREND_BREAKOUT")

            # 1. Data Quality Gate (DQS >= 85)
            dqs = float(cand_copy.get("dqs", cand_copy.get("data_quality_score", 100.0)))
            if dqs < min_dqs:
                continue

            # 2. Strategy Liquidity Gate
            vol_z = float(cand_copy.get("volume_z_score", cand_copy.get("sector_neutral_volume_zscore", cand_copy.get("vol_z", 0.0))))
            if strat == "STRATEGY_PULLBACK":
                is_dryup = cand_copy.get("is_vol_dryup", vol_z < 0.0)
                if not is_dryup:
                    continue
            else:
                if vol_z <= min_volume_zscore:
                    continue

            # 3. Calibrated Expected Net Return Gate (E[R_net] > 0.50%)
            e_net = cand_copy.get("expected_net_return_pct")
            if e_net is None:
                from core.meta_labeling_engine import MetaLabelingEngine
                p_cal = float(cand_copy.get("p_calibrated_up", cand_copy.get("probability_of_success_pct", 50.0)))
                tgt = float(cand_copy.get("take_profit_pct", cand_copy.get("target_pct", 5.0)))
                sl = abs(float(cand_copy.get("stop_loss_pct", 5.0)))
                ticker = cand_copy.get("ticker", cand_copy.get("symbol", ""))
                res = MetaLabelingEngine.calculate_expected_net_return(p_cal, tgt, sl, ticker)
                e_net = res["expected_net_return_pct"]
                cand_copy["expected_net_return_pct"] = e_net
                cand_copy["is_hard_banned"] = res["is_banned"]

            if float(e_net) <= min_expected_net_return:
                continue

            cand_copy["dqs"] = dqs
            cand_copy["volume_z_score"] = vol_z
            cand_copy["expected_net_return_pct"] = float(e_net)
            filtered.append(cand_copy)

        # Sort descending by expected net return (or score)
        sorted_cand = sorted(filtered, key=lambda x: float(x.get("expected_net_return_pct", x.get("score", 0.0))), reverse=True)
        top_k = sorted_cand[:k]
        for idx, item in enumerate(top_k):
            item["selection_rank"] = idx + 1
            item["selection_badge_ar"] = f"الترتيب الانتقائي #{idx + 1} (Top-{k})"

        return top_k
