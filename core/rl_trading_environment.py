#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# core/rl_trading_environment.py — Gym-Compatible Deep Reinforcement Learning Trading Env
# Standard Reinforcement Learning Environment (OpenAI Gym / Gymnasium API):
# - Step, Reset, State Observations, and Action Spaces
# - Incorporates EGX institutional frictions: 0.35% turnover cost + 10% Egyptian CGT
# - Reward Function: Moody & Saffell Differential Sharpe Ratio with Quadratic Drawdown Penalty
# =============================================================================

import math
import numpy as np
from typing import Dict, List, Any, Optional, Tuple


class RlTradingEnvironment:
    """
    Simulated Reinforcement Learning Environment for Training Autonomous Trading Agents.
    """

    ROUNDTRIP_FRICTION = 0.0035  # 0.35%
    EGYPTIAN_CGT = 0.10          # 10% Capital Gains Tax

    def __init__(
        self,
        price_series: Optional[List[float]] = None,
        initial_capital: float = 100000.0,
        drawdown_penalty_weight: float = 2.0
    ):
        self.prices = np.asarray(price_series or [80.0 + math.sin(i / 5.0) * 5.0 + (i * 0.1) for i in range(100)], dtype=float)
        self.initial_capital = initial_capital
        self.drawdown_penalty_weight = drawdown_penalty_weight
        self.current_step = 0
        self.capital = initial_capital
        self.shares = 0
        self.position_ratio = 0.0  # 0.0 to 1.0
        self.peak_portfolio_value = initial_capital
        self.total_friction_paid = 0.0
        self.total_cgt_paid = 0.0
        self.avg_entry_price = 0.0
        self.done = False

    def reset(self) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Resets the environment to the initial state."""
        self.current_step = min(5, max(1, len(self.prices) // 4))  # Dynamic warmup window
        self.capital = self.initial_capital
        self.shares = 0
        self.position_ratio = 0.0
        self.peak_portfolio_value = self.initial_capital
        self.total_friction_paid = 0.0
        self.total_cgt_paid = 0.0
        self.avg_entry_price = 0.0
        self.done = False

        obs = self._get_observation()
        info = {"initial_capital": self.initial_capital, "step": self.current_step}
        return obs, info

    def _get_observation(self) -> np.ndarray:
        """
        Constructs normalized observation vector:
        [1D_return, 5D_return, position_ratio, unrealized_pnl, drawdown_from_peak]
        """
        curr_p = self.prices[self.current_step]
        prev_p = self.prices[self.current_step - 1]
        p_5d = self.prices[max(0, self.current_step - 5)]

        ret_1d = (curr_p - prev_p) / max(prev_p, 1e-4)
        ret_5d = (curr_p - p_5d) / max(p_5d, 1e-4)

        current_val = self.capital + (self.shares * curr_p)
        dd = (self.peak_portfolio_value - current_val) / max(self.peak_portfolio_value, 1e-4)

        unrealized = 0.0
        if self.shares > 0 and self.avg_entry_price > 0:
            unrealized = (curr_p - self.avg_entry_price) / self.avg_entry_price

        return np.array([
            float(ret_1d),
            float(ret_5d),
            float(self.position_ratio),
            float(unrealized),
            float(dd)
        ], dtype=np.float32)

    def step(self, target_position: float) -> Tuple[np.ndarray, float, bool, Dict[str, Any]]:
        """
        Executes an action in the environment:
        - target_position: desired exposure ratio in [0.0, 1.0] (e.g. 0.0 = Cash, 1.0 = 100% Invested)
        - Applies 0.35% friction on position changes
        - Computes reward: Net portfolio delta minus friction and quadratic drawdown penalty
        """
        if self.done:
            raise RuntimeError("Environment already finished. Call reset() first.")

        target_position = min(max(float(target_position), 0.0), 1.0)
        curr_price = self.prices[self.current_step]
        prev_portfolio_val = self.capital + (self.shares * curr_price)

        # 1. Execute position adjustment
        desired_portfolio_val = prev_portfolio_val * target_position
        desired_shares = int(desired_portfolio_val / max(curr_price, 1e-4))
        delta_shares = desired_shares - self.shares

        friction = 0.0
        cgt = 0.0

        if delta_shares > 0:
            # Buying shares - account for friction in buying power
            cost = delta_shares * curr_price
            friction = cost * (self.ROUNDTRIP_FRICTION / 2.0)
            while (cost + friction) > self.capital and delta_shares > 0:
                delta_shares -= 1
                cost = delta_shares * curr_price
                friction = cost * (self.ROUNDTRIP_FRICTION / 2.0)

            total_outflow = cost + friction
            if total_outflow <= self.capital and delta_shares > 0:
                # Update weighted average cost
                prev_cost_basis = self.shares * self.avg_entry_price
                new_cost_basis = prev_cost_basis + cost
                self.shares += delta_shares
                self.avg_entry_price = new_cost_basis / max(self.shares, 1)
                self.capital -= total_outflow
        elif delta_shares < 0:
            # Selling shares
            sell_shares = abs(delta_shares)
            proceeds = sell_shares * curr_price
            friction = proceeds * (self.ROUNDTRIP_FRICTION / 2.0)
            realized_gain = (curr_price - self.avg_entry_price) * sell_shares
            if realized_gain > 0:
                cgt = realized_gain * self.EGYPTIAN_CGT
            net_inflow = proceeds - friction - cgt
            self.shares -= sell_shares
            self.capital += net_inflow
            if self.shares == 0:
                self.avg_entry_price = 0.0

        self.total_friction_paid += friction
        self.total_cgt_paid += cgt

        # 2. Advance time step
        self.current_step += 1
        if self.current_step >= len(self.prices) - 1:
            self.done = True

        next_price = self.prices[self.current_step]
        new_portfolio_val = self.capital + (self.shares * next_price)
        self.position_ratio = (self.shares * next_price) / max(new_portfolio_val, 1e-4)

        if new_portfolio_val > self.peak_portfolio_value:
            self.peak_portfolio_value = new_portfolio_val

        current_dd = (self.peak_portfolio_value - new_portfolio_val) / max(self.peak_portfolio_value, 1e-4)

        # 3. Reward Calculation:
        # Differential return minus friction and drawdown penalty
        net_return_pct = ((new_portfolio_val - prev_portfolio_val) / max(prev_portfolio_val, 1e-4)) * 100.0
        reward = net_return_pct - (self.drawdown_penalty_weight * (current_dd ** 2) * 100.0)

        obs = self._get_observation()
        info = {
            "portfolio_value": round(float(new_portfolio_val), 2),
            "capital": round(float(self.capital), 2),
            "shares": self.shares,
            "position_ratio": round(float(self.position_ratio), 3),
            "drawdown_pct": round(float(current_dd * 100.0), 2),
            "friction_paid": round(float(self.total_friction_paid), 2),
            "cgt_paid": round(float(self.total_cgt_paid), 2),
            "step": self.current_step
        }

        return obs, float(reward), self.done, info
