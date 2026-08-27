#!/usr/bin/env python3
# =============================================================================
# core/risk_position_sizer.py — GEN-26 Quantitative Risk-Based Position Sizer
# Calculates exact position share quantities based on Account Risk (e.g. 1.0%),
# Stop-Loss Distance (Entry - Stop), Market Regime Multipliers, and Invariant Caps.
# =============================================================================

import math
from typing import Dict, List, Any, Optional
from core.frozen_invariants import FrozenRiskInvariants
from core.market_breadth_engine import MarketBreadthEngine


class RiskBasedPositionSizer:
    """
    Calculates dynamic trade position sizes based on:
    1. Fixed Account Risk % (e.g. 1.0% of Total Portfolio NAV).
    2. Dollar Risk per Share = (Entry Price - Stop Loss Price).
    3. Market Regime Multiplier (1.0x Bull, 0.75x Chop, 0.50x Distribution, 0.0x Panic Bear).
    4. Institutional Invariant Hard Caps (Max 20.0% single-stock equity cap).
    """

    DEFAULT_ACCOUNT_RISK_PCT = 1.0  # Risk exactly 1.0% of total capital per trade idea
    MAX_SINGLE_STOCK_CAP_PCT = 20.0 # Strict institutional ceiling
    MAX_EQUITY_TOTAL_CAP_PCT = 65.0 # Total portfolio equity ceiling

    @classmethod
    def get_regime_multiplier(cls, market_regime: str) -> float:
        """
        Returns position sizing scale factor based on macro market regime.
        """
        if market_regime == MarketBreadthEngine.REGIME_STRONG_BULL:
            return 1.00  # Full sizing allowed
        elif market_regime == MarketBreadthEngine.REGIME_NEUTRAL:
            return 0.70  # Balanced sizing
        elif market_regime == MarketBreadthEngine.REGIME_DISTRIBUTION:
            return 0.40  # Defensive contraction
        elif market_regime == MarketBreadthEngine.REGIME_PANIC_BEAR:
            return 0.00  # Fail-Closed: 0 shares (100% Cash Defense)
        else:
            return 0.50

    @classmethod
    def calculate_position_size(
        cls,
        entry_price: float,
        stop_loss_price: float,
        portfolio_nav_egp: float = 100000.0,
        risk_per_trade_pct: float = 1.0,
        market_regime: str = MarketBreadthEngine.REGIME_STRONG_BULL,
        confidence_multiplier: float = 1.0
    ) -> Dict[str, Any]:
        """
        Computes exact risk-adjusted position size, target allocation, and shares.
        Supports confidence_multiplier (e.g. 1.2x for high ML confidence >= 65%, 0.7x for <= 45%).
        """
        if entry_price <= 0 or stop_loss_price <= 0 or entry_price <= stop_loss_price:
            return {
                "shares": 0,
                "position_value_egp": 0.0,
                "allocation_pct": 0.0,
                "risk_amount_egp": 0.0,
                "binding_constraint": "INVALID_PRICES",
                "regime_multiplier": 0.0,
                "confidence_multiplier": float(confidence_multiplier),
                "position_size_multiplier": float(confidence_multiplier)
            }

        dollar_risk_per_share = entry_price - stop_loss_price
        account_risk_egp = portfolio_nav_egp * (risk_per_trade_pct / 100.0)

        # 1. Unconstrained Shares from Dollar Risk = Account Risk / Dollar Risk per share
        raw_risk_shares = math.floor(account_risk_egp / dollar_risk_per_share) if dollar_risk_per_share > 0 else 0

        # 2. Hard Cap Shares from 20.0% Single Stock Invariant
        max_stock_value_egp = portfolio_nav_egp * (cls.MAX_SINGLE_STOCK_CAP_PCT / 100.0)
        cap_shares = math.floor(max_stock_value_egp / entry_price) if entry_price > 0 else 0

        # 3. Market Regime Multiplier
        regime_mult = cls.get_regime_multiplier(market_regime)

        # Base optimal shares
        constrained_shares = min(raw_risk_shares, cap_shares)
        final_shares = int(math.floor(constrained_shares * regime_mult * confidence_multiplier))
        # Ensure hard 20% cap invariant is never exceeded
        final_shares = min(final_shares, cap_shares)

        position_value_egp = round(final_shares * entry_price, 2)
        allocation_pct = round((position_value_egp / portfolio_nav_egp) * 100.0, 2) if portfolio_nav_egp > 0 else 0.0
        actual_risk_egp = round(final_shares * dollar_risk_per_share, 2)
        actual_risk_pct = round((actual_risk_egp / portfolio_nav_egp) * 100.0, 2) if portfolio_nav_egp > 0 else 0.0

        binding = "RISK_FORMULA"
        if regime_mult == 0.0:
            binding = "PANIC_BEAR_CASH_LOCKOUT"
        elif final_shares == cap_shares:
            binding = "20PCT_SINGLE_STOCK_HARD_CAP"
        elif regime_mult < 1.0:
            binding = "REGIME_SCALED_CONTRACTION"
        elif confidence_multiplier != 1.0:
            binding = "ML_CONFIDENCE_SIZED"

        return {
            "shares": final_shares,
            "position_value_egp": position_value_egp,
            "allocation_pct": allocation_pct,
            "actual_risk_egp": actual_risk_egp,
            "actual_risk_pct": actual_risk_pct,
            "dollar_risk_per_share": round(dollar_risk_per_share, 2),
            "regime_multiplier": regime_mult,
            "confidence_multiplier": float(confidence_multiplier),
            "position_size_multiplier": float(confidence_multiplier),
            "binding_constraint": binding,
            "max_single_stock_cap_egp": max_stock_value_egp
        }
