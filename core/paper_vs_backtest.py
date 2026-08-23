#!/usr/bin/env python3
# =============================================================================
# core/paper_vs_backtest.py — GEN-26 Paper Trading vs Backtest Forensic Comparator
# Measures empirical divergence between live paper trading and historical backtests.
# =============================================================================

from typing import Dict, List, Any, Optional
import numpy as np


class PaperVsBacktestComparator:
    """
    Compares live paper trading performance metrics against benchmark backtest expectations.
    """

    BACKTEST_BENCHMARK = {
        "profit_factor": 2.138,
        "win_rate_pct": 56.0,
        "mean_net_return_pct": 2.89,
        "calendar_sharpe": 1.188,
        "standard_friction_rt_pct": 0.90,
        "expected_slippage_pct": 0.10,
        "max_drawdown_pct": -18.40
    }

    @classmethod
    def evaluate_divergence(
        cls,
        paper_trades_count: int,
        paper_win_rate_pct: float,
        paper_profit_factor: float,
        paper_mean_net_return_pct: float,
        paper_realized_slippage_pct: float = 0.10,
        paper_max_drawdown_pct: float = -5.0
    ) -> Dict[str, Any]:
        """
        Calculates divergence between paper trading metrics and backtest benchmarks.
        """
        bench = cls.BACKTEST_BENCHMARK
        n = max(0, paper_trades_count)

        if n < 5:
            return {
                "sample_size": n,
                "status": "INSUFFICIENT_SAMPLE (Requires >= 5 closed trades)",
                "is_divergence_normal": True,
                "win_rate_divergence_pct": 0.0,
                "profit_factor_divergence": 0.0,
                "slippage_divergence_pct": 0.0,
                "benchmark_reference": bench
            }

        wr_div = paper_win_rate_pct - bench["win_rate_pct"]
        pf_div = paper_profit_factor - bench["profit_factor"]
        slip_div = paper_realized_slippage_pct - bench["expected_slippage_pct"]

        # Divergence warning flags
        is_normal = True
        warnings = []
        if wr_div < -15.0: # Win rate 15% below benchmark
            is_normal = False
            warnings.append("WIN_RATE_SEVERE_UNDERPERFORMANCE")
        if pf_div < -0.80:
            is_normal = False
            warnings.append("PROFIT_FACTOR_DEGRADATION")
        if slip_div > 0.15: # Realized slippage 2.5x higher than modeled
            is_normal = False
            warnings.append("EXECUTION_SLIPPAGE_EXCESS")

        return {
            "sample_size": n,
            "status": "HEALTHY_ALIGNMENT" if is_normal else "DIVERGENCE_WARNING",
            "is_divergence_normal": is_normal,
            "warnings": warnings,
            "metrics": {
                "paper_win_rate_pct": round(paper_win_rate_pct, 1),
                "benchmark_win_rate_pct": bench["win_rate_pct"],
                "win_rate_divergence_pct": round(wr_div, 1),
                "paper_profit_factor": round(paper_profit_factor, 2),
                "benchmark_profit_factor": bench["profit_factor"],
                "profit_factor_divergence": round(pf_div, 2),
                "paper_slippage_pct": round(paper_realized_slippage_pct, 3),
                "benchmark_slippage_pct": bench["expected_slippage_pct"],
                "slippage_divergence_pct": round(slip_div, 3)
            }
        }
