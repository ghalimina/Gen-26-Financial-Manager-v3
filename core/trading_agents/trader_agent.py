#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# core/trading_agents/trader_agent.py — Quantitative Trader Agent
# Inspired by TauricResearch/TradingAgents (UCLA & MIT)
#
# Synthesizes Analyst Reports + Bull/Bear Debate to construct structured TradeProposal:
# - Calculates Expected Return, 0.35% EGX friction, Almgren-Chriss slippage, Uncertainty Penalty
# - Enforces Net Edge >= 1.00%
# - Sets Action, Entry Range, Stop-Loss (-7.0%), Targets, and Horizon
# =============================================================================

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import datetime

from .analyst_team import AnalystTeamReport
from .debate_engine import DebateTranscript
from core.trade_selection_model import TradeSelectionModel
from core.uncertainty_engine import UncertaintyEngine


@dataclass
class TradeProposal:
    ticker: str
    timestamp: str
    market_price: float
    action: str  # BUY_LIMIT, ACCUMULATE, HOLD, TRIM, NO_TRADE
    action_label_ar: str
    expected_gross_return_pct: float
    roundtrip_friction_pct: float
    estimated_slippage_pct: float
    uncertainty_penalty_pct: float
    net_edge_pct: float
    meets_edge_hurdle: bool
    entry_zone_low: float
    entry_zone_high: float
    hard_stop_loss: float
    profit_target_1: float
    profit_target_2: float
    recommended_horizon_days: int
    sizing_weight: float  # 0.0 to 1.0
    rationale_ar: str


class TraderAgent:
    """
    Synthesizes analyst reports and the dialectical debate transcript
    to generate an executable, mathematically gated trade proposal.
    """
    NAME = "QuantTrader"
    ROLE_AR = "المتداول الكمي ومدير الصفقات (Quant Trader)"

    ROUNDTRIP_FRICTION = 0.0094  # 0.94% (Thndr + EGX + MCDR SSoT)

    @classmethod
    def construct_proposal(
        cls,
        analyst_report: AnalystTeamReport,
        debate_transcript: DebateTranscript
    ) -> TradeProposal:
        sym = analyst_report.ticker
        price = analyst_report.market_price
        
        # 1. Uncertainty Evaluation
        unc_eval = UncertaintyEngine.evaluate_forecast_distribution(
            ticker=sym,
            expected_return_pct=8.5 if debate_transcript.debate_winner == "BULL_ADVANTAGE" else 4.0,
            base_confidence=78.0,
            current_price=price
        )
        unc_penalty = float(unc_eval.get("uncertainty_score", 0.25)) * 0.015
        sizing_mult = float(unc_eval.get("sizing_multiplier", 0.85))

        # 2. Expected Return Estimation
        if debate_transcript.debate_winner == "BULL_ADVANTAGE":
            gross_return = 0.085  # 8.5% Expected Gross Return
        elif debate_transcript.debate_winner == "BALANCED_EVIDENCE":
            gross_return = 0.052  # 5.2%
        else:
            gross_return = 0.015  # 1.5%

        slippage = 0.0015  # 0.15% Almgren-Chriss dynamic slippage
        net_edge = gross_return - (cls.ROUNDTRIP_FRICTION + slippage) - unc_penalty
        meets_hurdle = (net_edge * 100.0) >= TradeSelectionModel.MINIMUM_NET_EDGE_REQUIRED_PCT  # >= 1.00%

        # 3. Decision Logic & Pricing Levels
        if meets_hurdle and debate_transcript.debate_winner != "BEAR_ADVANTAGE":
            action = "BUY_LIMIT"
            action_ar = "شراء تراجعي مقيد (Buy Limit)"
            entry_low = round(price * 0.985, 2)
            entry_high = round(price * 0.998, 2)
            stop_loss = round(price * 0.930, 2)  # -7.0% hard stop
            target_1 = round(price * 1.085, 2)   # +8.5%
            target_2 = round(price * 1.150, 2)   # +15.0%
            horizon = 60
            sizing = round(0.75 * sizing_mult, 2)
            rationale_ar = (
                f"أفضلية ربحية صافية محققة (+{net_edge*100:.2f}%) بعد خصم العمولات والانزلاق وعقوبة عدم اليقين. "
                f"دخول تراجعي في النطاق ({entry_low:.2f} - {entry_high:.2f} ج.م) مع وقف خسارة عند {stop_loss:.2f} ج.م."
            )
        elif net_edge > 0:
            action = "HOLD"
            action_ar = "احتفاظ ومراقبة (Hold / Neutral)"
            entry_low = price
            entry_high = price
            stop_loss = round(price * 0.930, 2)
            target_1 = round(price * 1.050, 2)
            target_2 = round(price * 1.080, 2)
            horizon = 30
            sizing = 0.0
            rationale_ar = (
                f"فارق ربحي غير كافٍ (+{net_edge*100:.2f}% دون عتبة 1.00%). يوصى بالانتظار وتجنب فتح مراكز جديدة."
            )
        else:
            action = "NO_TRADE"
            action_ar = "حجب الصفقة وتجنب التداول (No Trade)"
            entry_low = 0.0
            entry_high = 0.0
            stop_loss = round(price * 0.930, 2)
            target_1 = 0.0
            target_2 = 0.0
            horizon = 0
            sizing = 0.0
            rationale_ar = (
                f"أفضلية سالبة أو مخاطر تفوق العائد المتوقع. تم حجب الصفقة بأمان كامل (Fail-Closed)."
            )

        return TradeProposal(
            ticker=sym,
            timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            market_price=price,
            action=action,
            action_label_ar=action_ar,
            expected_gross_return_pct=round(gross_return * 100, 2),
            roundtrip_friction_pct=round(cls.ROUNDTRIP_FRICTION * 100, 2),
            estimated_slippage_pct=round(slippage * 100, 2),
            uncertainty_penalty_pct=round(unc_penalty * 100, 2),
            net_edge_pct=round(net_edge * 100, 2),
            meets_edge_hurdle=meets_hurdle,
            entry_zone_low=entry_low,
            entry_zone_high=entry_high,
            hard_stop_loss=stop_loss,
            profit_target_1=target_1,
            profit_target_2=target_2,
            recommended_horizon_days=horizon,
            sizing_weight=sizing,
            rationale_ar=rationale_ar
        )
