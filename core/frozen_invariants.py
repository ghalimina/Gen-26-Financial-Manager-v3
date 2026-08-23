#!/usr/bin/env python3
# =============================================================================
# core/frozen_invariants.py — GEN-26 Centralized Frozen Core Risk Invariants
# Authoritative constants and verification functions protecting platform safety.
# NEVER WEAKEN OR MODIFY THESE INVARIANTS WITHOUT MATHEMATICAL PROOF.
# =============================================================================

from typing import Dict, List, Any, Optional


class FrozenRiskInvariants:
    # 1. Allocation & Solvency Limits
    MAX_TOTAL_STOCK_ALLOCATION_PCT = 0.65  # Strict 65% ceiling on stock equity
    MANDATORY_CASH_RESERVE_PCT = 0.35      # Mandatory 35% cash buffer floor
    MAX_SINGLE_STOCK_ALLOCATION_PCT = 0.10 # 10% maximum target per individual stock
    MAX_SECTOR_ALLOCATION_PCT = 0.25       # 25% maximum ceiling per individual sector

    # 2. Execution & Feasibility Rules
    HARD_STOP_LOSS_PCT = 0.07              # -7.0% hard stop loss below entry price
    CONCENTRATION_TRIM_TRIGGER_PCT = 0.10  # >10% of portfolio equity triggers trim
    MAX_ADV_PARTICIPATION_PCT = 0.05       # Order size cannot exceed 5% of ADV20
    EGX_LIMIT_UP_BAND_PCT = 0.195          # 19.5% daily gain blocks BUY (Locked at Limit Up)
    EGX_LIMIT_DOWN_BAND_PCT = -0.195       # -19.5% daily loss blocks SELL (Locked at Limit Down)

    # 3. Friction & Fee Defaults
    ROUND_TRIP_STANDARD_FRICTION_PCT = 0.0090 # 0.90% standard friction (fees + slippage)
    BREAK_EVEN_FRICTION_THRESHOLD_PCT = 0.036041 # 3.6041% break-even boundary

    # 4. Verification Methods
    @classmethod
    def verify_cash_solvency(cls, required_cost: float, available_free_cash: float) -> bool:
        """Enforces: required_cost <= available_free_cash (Fail-Closed)."""
        return float(required_cost) <= float(available_free_cash) + 1e-6

    @classmethod
    def verify_stock_allocation_ceiling(cls, stock_equity: float, total_portfolio_equity: float) -> bool:
        """Enforces: stock_equity / total_portfolio_equity <= 0.65."""
        if total_portfolio_equity <= 0:
            return False
        return (float(stock_equity) / float(total_portfolio_equity)) <= (cls.MAX_TOTAL_STOCK_ALLOCATION_PCT + 1e-6)

    @classmethod
    def verify_pullback_invariant(cls, entry_price: float, current_price: float) -> bool:
        """Enforces: entry_price < current_price (prohibits buying at session highs)."""
        return float(entry_price) < float(current_price)

    @classmethod
    def verify_liquidity_cap(cls, requested_shares: int, entry_price: float, adv_20d_egp: float) -> bool:
        """Enforces: requested_shares * entry_price <= 0.05 * ADV20."""
        order_val = requested_shares * entry_price
        max_allowed_val = cls.MAX_ADV_PARTICIPATION_PCT * adv_20d_egp
        return order_val <= (max_allowed_val + 1e-6)

    @classmethod
    def verify_egx_circuit_breaker(cls, current_price: float, previous_close: float, side: str = "BUY") -> bool:
        """Enforces: Cannot BUY if price >= +19.5%; cannot SELL if price <= -19.5%."""
        if previous_close <= 0:
            return True
        chg = (current_price - previous_close) / previous_close
        if side.upper() == "BUY" and chg >= cls.EGX_LIMIT_UP_BAND_PCT:
            return False
        if side.upper() == "SELL" and chg <= cls.EGX_LIMIT_DOWN_BAND_PCT:
            return False
        return True
