#!/usr/bin/env python3
# =============================================================================
# core/portfolio_constructor.py — GEN-26 Institutional Portfolio Construction Engine
# Converts ranked candidates into an executable, risk-budgeted, liquidity-capped portfolio
# while strictly enforcing all Frozen Risk Core invariants.
# =============================================================================

from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd
from core.frozen_invariants import FrozenRiskInvariants
from core.portfolio_risk import PortfolioRiskEngine


class InstitutionalPortfolioConstructor:
    """
    Allocates available portfolio capital across ranked candidates considering
    alpha, volatility, stop distance, liquidity limits, and sector correlation.
    """

    @classmethod
    def construct_target_portfolio(
        cls,
        ranked_candidates: List[Dict[str, Any]],
        total_portfolio_equity: float,
        available_free_cash: float,
        existing_positions: Dict[str, Dict[str, Any]], # ticker -> {shares, price, equity, sector}
        sector_mapping: Dict[str, str],
        correlation_matrix: Optional[pd.DataFrame] = None,
        target_risk_per_trade_pct: float = 0.0075 # 0.75% portfolio risk budget per position
    ) -> Dict[str, Any]:
        """
        Builds the target allocation plan for ranked candidates.
        """
        equity = float(total_portfolio_equity)
        cash = float(available_free_cash)

        # 1. Evaluate current invested equity and sector allocations
        current_allocations: Dict[str, float] = {}
        for t, pos in existing_positions.items():
            pos_eq = pos.get("shares", 0) * pos.get("price", 0.0)
            current_allocations[t] = pos_eq / equity if equity > 0 else 0.0

        current_invested_pct = sum(current_allocations.values())
        max_additional_investment = max(0.0, (FrozenRiskInvariants.MAX_TOTAL_STOCK_ALLOCATION_PCT - current_invested_pct) * equity)
        deployable_cash = min(cash, max_additional_investment)

        allocated_orders: List[Dict[str, Any]] = []
        remaining_deployable_cash = deployable_cash
        simulated_allocations = dict(current_allocations)

        # 2. Iterate through ranked candidates (Top down)
        for cand in ranked_candidates:
            ticker = cand.get("ticker")
            if not ticker or ticker in existing_positions:
                continue # Already in portfolio

            alpha_score = cand.get("alpha_score", 50.0)
            ep = cand.get("entry_price", cand.get("price", 10.0))
            cp = cand.get("current_price", ep)
            stop = cand.get("stop_price", ep * (1.0 - FrozenRiskInvariants.HARD_STOP_LOSS_PCT))
            adv_egp = cand.get("adv_20d_egp", cand.get("adv", 10_000_000))
            sector = sector_mapping.get(ticker, "General")

            # Check if eligible to buy (not locked at limit-up, positive entry)
            cb = cand.get("circuit_breaker", {"can_buy": True})
            if not cb.get("can_buy", True) or ep <= 0 or remaining_deployable_cash <= 1000.0:
                continue

            # Sizing Step A: Base 10% Capital Cap
            max_capital_cap = equity * FrozenRiskInvariants.MAX_SINGLE_STOCK_ALLOCATION_PCT

            # Sizing Step B: Risk Budget Sizing (Risk Amount / Stop Distance)
            stop_distance_pct = max(0.02, (ep - stop) / ep)
            risk_budget_egp = equity * target_risk_per_trade_pct
            risk_based_capital = risk_budget_egp / stop_distance_pct

            # Sizing Step C: Liquidity Cap (5% ADV20)
            max_liquidity_capital = FrozenRiskInvariants.MAX_ADV_PARTICIPATION_PCT * adv_egp

            # Sizing Step D: Correlation & Sector Penalty
            corr_eval = PortfolioRiskEngine.calculate_correlation_penalty(
                target_ticker=ticker,
                target_sector=sector,
                existing_allocations=simulated_allocations,
                sector_mapping=sector_mapping,
                correlation_matrix=correlation_matrix
            )
            penalty = corr_eval["penalty_multiplier"]

            # Blended raw target capital
            raw_target_capital = min(max_capital_cap, risk_based_capital, max_liquidity_capital) * penalty
            final_target_capital = min(raw_target_capital, remaining_deployable_cash)

            # Integer share conversion
            suggested_shares = int(final_target_capital // ep)
            if suggested_shares <= 0:
                continue

            order_cost = suggested_shares * ep
            target_weight = order_cost / equity if equity > 0 else 0.0

            # Update simulated state
            remaining_deployable_cash -= order_cost
            simulated_allocations[ticker] = target_weight

            allocated_orders.append({
                "ticker": ticker,
                "sector": sector,
                "entry_price": round(ep, 2),
                "stop_price": round(stop, 2),
                "target_shares": suggested_shares,
                "target_capital_egp": round(order_cost, 2),
                "target_weight_pct": round(target_weight * 100.0, 2),
                "penalty_multiplier": penalty,
                "correlation_reason": corr_eval["reason_codes"],
                "max_allowed_capital_egp": round(max_capital_cap, 2),
                "liquidity_cap_egp": round(max_liquidity_capital, 2),
                "sizing_reason": f"Risk-Budgeted {penalty*100:.0f}% Sizing ({', '.join(corr_eval['reason_codes'])})"
            })

        # 3. Comprehensive concentration and sanity check (allows 1.5% drift buffer for winning positions)
        concentration_audit = PortfolioRiskEngine.evaluate_portfolio_concentration(
            current_allocations=simulated_allocations,
            sector_mapping=sector_mapping,
            max_stock_weight=FrozenRiskInvariants.MAX_SINGLE_STOCK_ALLOCATION_PCT + 0.015
        )

        return {
            "total_portfolio_equity": round(equity, 2),
            "initial_cash": round(cash, 2),
            "allocated_cash": round(deployable_cash - remaining_deployable_cash, 2),
            "remaining_free_cash": round(cash - (deployable_cash - remaining_deployable_cash), 2),
            "new_order_count": len(allocated_orders),
            "allocated_orders": allocated_orders,
            "projected_portfolio_concentration": concentration_audit,
            "is_plan_valid": concentration_audit["is_concentration_safe"]
        }
