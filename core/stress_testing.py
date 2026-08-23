#!/usr/bin/env python3
# =============================================================================
# core/stress_testing.py — GEN-26 Institutional Stress Testing Engine
# Simulates market gap-downs, liquidity collapse, slippage spikes, and devaluation shocks
# to verify that Frozen Risk Core invariants survive extreme market conditions.
# =============================================================================

from typing import Dict, List, Any, Optional
import numpy as np
from core.frozen_invariants import FrozenRiskInvariants


class PortfolioStressEngine:
    """
    Evaluates portfolio resilience under severe macroeconomic, liquidity, and execution stress.
    """

    @classmethod
    def simulate_market_gap_shock(
        cls,
        current_portfolio_equity: float,
        current_cash: float,
        positions: Dict[str, Dict[str, Any]], # ticker -> {shares, current_price, entry_price, stop_price}
        market_gap_pct: float = -0.15 # -15% market gap-down
    ) -> Dict[str, Any]:
        """
        Simulates an overnight market gap-down (e.g. -10%, -15%, -20%) and verifies stop triggers.
        """
        initial_equity = float(current_portfolio_equity)
        cash = float(current_cash)

        stressed_positions = []
        total_stressed_stock_equity = 0.0

        for ticker, pos in positions.items():
            shares = pos.get("shares", 0)
            cp = pos.get("current_price", 10.0)
            ep = pos.get("entry_price", cp)
            stop = pos.get("stop_price", ep * 0.93)

            # Price gaps down
            gap_price = round(cp * (1.0 + market_gap_pct), 3)
            # Evaluate if stop breached
            stop_triggered = gap_price <= stop
            effective_exit_price = gap_price if stop_triggered else gap_price
            pos_equity = shares * gap_price

            total_stressed_stock_equity += pos_equity

            stressed_positions.append({
                "ticker": ticker,
                "shares": shares,
                "pre_shock_price": cp,
                "post_shock_price": gap_price,
                "stop_price": stop,
                "stop_triggered": stop_triggered,
                "stressed_equity": round(pos_equity, 2)
            })

        post_shock_total_equity = round(cash + total_stressed_stock_equity, 2)
        invested_ratio = (total_stressed_stock_equity / post_shock_total_equity) if post_shock_total_equity > 0 else 0.0
        drawdown_pct = round(((post_shock_total_equity - initial_equity) / initial_equity) * 100.0, 2)

        return {
            "initial_equity": initial_equity,
            "post_shock_equity": post_shock_total_equity,
            "drawdown_pct": drawdown_pct,
            "post_shock_cash": round(cash, 2),
            "cash_solvency_intact": cash >= 0.0,
            "allocation_ratio": round(invested_ratio, 3),
            "allocation_cap_intact": invested_ratio <= (FrozenRiskInvariants.MAX_TOTAL_STOCK_ALLOCATION_PCT + 1e-4),
            "stressed_positions": stressed_positions,
            "status": "PASS" if cash >= 0.0 and invested_ratio <= 0.65 else "FAIL"
        }

    @classmethod
    def simulate_liquidity_collapse(
        cls,
        order_shares: int,
        entry_price: float,
        normal_adv_20d_egp: float,
        liquidity_drop_factor: float = 0.80 # 80% volume collapse
    ) -> Dict[str, Any]:
        """
        Simulates 50% to 80% volume collapse in market liquidity.
        """
        stressed_adv = normal_adv_20d_egp * (1.0 - liquidity_drop_factor)
        order_val = order_shares * entry_price
        max_safe_val = FrozenRiskInvariants.MAX_ADV_PARTICIPATION_PCT * stressed_adv

        can_execute_safely = order_val <= (max_safe_val + 1e-4)
        recommended_shares = int((max_safe_val + 1e-4) // entry_price)

        return {
            "normal_adv_egp": normal_adv_20d_egp,
            "stressed_adv_egp": round(stressed_adv, 2),
            "order_value_egp": round(order_val, 2),
            "max_safe_value_egp": round(max_safe_val, 2),
            "can_execute_safely": can_execute_safely,
            "recommended_shares_under_stress": recommended_shares,
            "action": "EXECUTE_NORMAL" if can_execute_safely else "DOWNSCALE_POSITION_TO_SAFE_CAPACITY"
        }
