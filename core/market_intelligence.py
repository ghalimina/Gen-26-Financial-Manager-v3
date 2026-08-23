#!/usr/bin/env python3
# =============================================================================
# core/market_intelligence.py — GEN-26 Market Regime, Breadth & Relative Strength
# Classifies macro regimes (BULL, BEAR, SIDEWAYS, RISK_ON/OFF) and evaluates
# multi-horizon relative strength across 1D, 5D, 20D, and 60D horizons.
# =============================================================================

from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np


class MarketIntelligenceEngine:
    """
    Computes trailing breadth indicators, classifies market regimes, and evaluates relative strength.
    """

    @staticmethod
    def compute_trailing_breadth(stock_dfs: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Computes Point-in-Time clean trailing market breadth across all available assets.
        Uses exclusively trailing 1-day returns to eliminate lookahead bias (BUG-04 fix).
        """
        advances = 0
        declines = 0
        unchanged = 0
        returns_list = []

        for ticker, df in stock_dfs.items():
            if df is not None and not df.empty and 'Close' in df.columns and len(df) >= 2:
                c_curr = float(df['Close'].iloc[-1])
                c_prev = float(df['Close'].iloc[-2])
                ret = (c_curr - c_prev) / c_prev if c_prev > 0 else 0.0
                returns_list.append(ret)
                if ret > 0.002:
                    advances += 1
                elif ret < -0.002:
                    declines += 1
                else:
                    unchanged += 1

        total = max(1, advances + declines + unchanged)
        adv_ratio = round(advances / total, 3)
        ad_ratio = round(advances / max(declines, 1), 2)
        dispersion = round(float(np.std(returns_list) * 100.0), 2) if returns_list else 0.0

        return {
            "advances": advances,
            "declines": declines,
            "unchanged": unchanged,
            "total_stocks": total,
            "advance_ratio": adv_ratio,
            "ad_ratio": ad_ratio,
            "market_dispersion_pct": dispersion
        }

    @staticmethod
    def classify_market_regime(
        egx30_df: Optional[pd.DataFrame],
        breadth_data: Dict[str, Any],
        usd_egp_mom_5d: float = 0.0
    ) -> Dict[str, Any]:
        """
        Classifies market regime into BULL, BEAR, SIDEWAYS, HIGH_VOL, RISK_ON, RISK_OFF.
        """
        regime_label = "SIDEWAYS"
        risk_sentiment = "NEUTRAL"
        trend_strength = 50.0

        if egx30_df is not None and not egx30_df.empty and len(egx30_df) >= 50:
            c = egx30_df['Close']
            sma20 = float(c.rolling(20).mean().iloc[-1])
            sma50 = float(c.rolling(50).mean().iloc[-1])
            curr_c = float(c.iloc[-1])
            mom_20d = float(c.pct_change(20).iloc[-1] * 100.0)

            # Regime Logic
            if curr_c > sma50 and curr_c > sma20 and mom_20d > 1.5:
                regime_label = "BULL"
                trend_strength = min(100.0, 70.0 + mom_20d * 2.0)
            elif curr_c < sma50 and curr_c < sma20 and mom_20d < -1.5:
                regime_label = "BEAR"
                trend_strength = max(10.0, 30.0 + mom_20d * 2.0)
            else:
                regime_label = "SIDEWAYS"
                trend_strength = 50.0

        # Sentiment integration with Breadth and FX stability
        adv_ratio = breadth_data.get("advance_ratio", 0.5)
        if adv_ratio > 0.55 and usd_egp_mom_5d < 2.0:
            risk_sentiment = "RISK_ON"
        elif adv_ratio < 0.40 or usd_egp_mom_5d > 5.0:
            risk_sentiment = "RISK_OFF"
        else:
            risk_sentiment = "NEUTRAL"

        return {
            "regime": regime_label,
            "sentiment": risk_sentiment,
            "trend_strength": round(trend_strength, 1),
            "breadth_advance_ratio": breadth_data.get("advance_ratio", 0.5),
            "market_dispersion_pct": breadth_data.get("market_dispersion_pct", 0.0)
        }

    @staticmethod
    def compute_multi_horizon_relative_strength(
        stock_df: pd.DataFrame,
        benchmark_df: Optional[pd.DataFrame]
    ) -> Dict[str, Any]:
        """
        Computes Relative Strength vs Benchmark across 1D, 5D, 20D, and 60D horizons.
        """
        rs_results = {"1D": 0.0, "5D": 0.0, "20D": 0.0, "60D": 0.0}

        if stock_df is None or stock_df.empty or benchmark_df is None or benchmark_df.empty:
            return rs_results

        for horizon, days in [("1D", 1), ("5D", 5), ("20D", 20), ("60D", 60)]:
            if len(stock_df) > days and len(benchmark_df) > days:
                s_ret = float(stock_df['Close'].pct_change(days).iloc[-1] * 100.0)
                b_ret = float(benchmark_df['Close'].pct_change(days).iloc[-1] * 100.0)
                rs_results[horizon] = round(s_ret - b_ret, 2)

        return rs_results
