#!/usr/bin/env python3
# =============================================================================
# core/portfolio_risk.py — GEN-26 Institutional Portfolio Risk & Correlation Engine
# Evaluates pairwise correlation, sector concentration, volatility scaling,
# and penalizes redundant exposure to maintain optimal diversification.
# =============================================================================

from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd
from core.frozen_invariants import FrozenRiskInvariants


class PortfolioRiskEngine:
    """
    Computes portfolio-level risk metrics, correlation penalties, and sector concentration.
    """

    @staticmethod
    def compute_correlation_matrix(returns_df: pd.DataFrame) -> pd.DataFrame:
        """Computes pairwise Spearman / Pearson correlation matrix for portfolio assets."""
        if returns_df.empty or len(returns_df.columns) < 2:
            return pd.DataFrame()
        return returns_df.corr(method="pearson").round(3)

    @classmethod
    def evaluate_portfolio_concentration(
        cls,
        current_allocations: Dict[str, float], # ticker -> weight (0.0 to 1.0)
        sector_mapping: Dict[str, str],        # ticker -> sector
        max_sector_weight: float = FrozenRiskInvariants.MAX_SECTOR_ALLOCATION_PCT,
        max_stock_weight: float = FrozenRiskInvariants.MAX_SINGLE_STOCK_ALLOCATION_PCT
    ) -> Dict[str, Any]:
        """
        Evaluates single-stock and sector concentration against risk ceilings.
        """
        sector_totals: Dict[str, float] = {}
        stock_violations = []
        sector_violations = []

        total_invested_weight = sum(current_allocations.values())

        for ticker, weight in current_allocations.items():
            if weight > (max_stock_weight + 1e-4):
                stock_violations.append({
                    "ticker": ticker,
                    "weight": round(weight, 3),
                    "max_allowed": max_stock_weight,
                    "code": "POSITION_CONCENTRATION"
                })

            sec = sector_mapping.get(ticker, "General")
            sector_totals[sec] = sector_totals.get(sec, 0.0) + weight

        for sec, sec_w in sector_totals.items():
            if sec_w > (max_sector_weight + 1e-4):
                sector_violations.append({
                    "sector": sec,
                    "weight": round(sec_w, 3),
                    "max_allowed": max_sector_weight,
                    "code": "SECTOR_CONCENTRATION"
                })

        hhi = sum((w * 100.0) ** 2 for w in current_allocations.values())

        return {
            "total_invested_weight": round(total_invested_weight, 3),
            "cash_reserve_weight": round(max(0.0, 1.0 - total_invested_weight), 3),
            "herfindahl_hirschman_index": round(hhi, 1),
            "sector_exposures": {k: round(v, 3) for k, v in sector_totals.items()},
            "stock_violations": stock_violations,
            "sector_violations": sector_violations,
            "is_concentration_safe": len(stock_violations) == 0 and len(sector_violations) == 0 and total_invested_weight <= FrozenRiskInvariants.MAX_TOTAL_STOCK_ALLOCATION_PCT + 1e-4
        }

    @staticmethod
    def calculate_correlation_penalty(
        target_ticker: str,
        target_sector: str,
        existing_allocations: Dict[str, float],
        sector_mapping: Dict[str, str],
        correlation_matrix: Optional[pd.DataFrame] = None
    ) -> Dict[str, Any]:
        """
        Calculates correlation penalty factor (0.0 to 1.0) to scale down redundant positions.
        """
        if not existing_allocations:
            return {"penalty_multiplier": 1.0, "reason_codes": ["NO_EXISTING_POSITIONS"]}

        # 1. Sector redundancy check
        existing_sector_weight = sum(
            weight for t, weight in existing_allocations.items()
            if sector_mapping.get(t) == target_sector
        )

        penalty = 1.0
        reason_codes = []

        if existing_sector_weight >= 0.20:
            penalty *= 0.60
            reason_codes.append("SECTOR_CONCENTRATION_HIGH")
        elif existing_sector_weight >= 0.10:
            penalty *= 0.85
            reason_codes.append("SECTOR_EXPOSURE_MODERATE")

        # 2. Pairwise correlation check if matrix available
        if correlation_matrix is not None and target_ticker in correlation_matrix.columns:
            for ex_ticker, weight in existing_allocations.items():
                if ex_ticker in correlation_matrix.index and ex_ticker != target_ticker:
                    corr = float(correlation_matrix.loc[target_ticker, ex_ticker])
                    if corr >= 0.75:
                        penalty *= 0.75
                        reason_codes.append(f"HIGH_CORRELATION_WITH_{ex_ticker}_({corr:.2f})")
                        break

        penalty = round(max(0.20, min(1.0, penalty)), 2)
        return {
            "penalty_multiplier": penalty,
            "reason_codes": reason_codes if reason_codes else ["DIVERSIFICATION_HEALTHY"]
        }

    @staticmethod
    def estimate_portfolio_volatility(
        weights: np.ndarray,
        cov_matrix: np.ndarray,
        annualization_factor: float = np.sqrt(252)
    ) -> float:
        """Estimates annualized portfolio volatility: sqrt(w^T Cov w) * sqrt(252)."""
        if len(weights) == 0 or cov_matrix.shape[0] != len(weights):
            return 0.20  # Baseline 20% volatility
        p_var = float(np.dot(weights.T, np.dot(cov_matrix, weights)))
        return round(float(np.sqrt(max(1e-6, p_var)) * annualization_factor), 4)
