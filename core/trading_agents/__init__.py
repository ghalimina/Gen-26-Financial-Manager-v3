#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# core/trading_agents/__init__.py — TradingAgents Multi-Agent Framework for EGX
# Inspired by TauricResearch/TradingAgents (UCLA & MIT)
# Adapted specifically for the Egyptian Exchange (EGX) and GEN-26 Architecture.
# =============================================================================

from .analyst_team import (
    FundamentalAnalystAgent,
    TechnicalAnalystAgent,
    MacroNewsAnalystAgent,
    ArabicSentimentAnalystAgent,
    AnalystTeamReport
)
from .debate_engine import (
    BullResearcherAgent,
    BearResearcherAgent,
    DebateModerator,
    DebateTranscript
)
from .trader_agent import TraderAgent, TradeProposal
from .risk_and_fund_manager import (
    RiskManagerAgent,
    FundManagerAgent,
    ExecutionDecision
)
from .llm_router import LLMRouter
from .orchestrator import TradingAgentsOrchestrator

__all__ = [
    "FundamentalAnalystAgent",
    "TechnicalAnalystAgent",
    "MacroNewsAnalystAgent",
    "ArabicSentimentAnalystAgent",
    "AnalystTeamReport",
    "BullResearcherAgent",
    "BearResearcherAgent",
    "DebateModerator",
    "DebateTranscript",
    "TraderAgent",
    "TradeProposal",
    "RiskManagerAgent",
    "FundManagerAgent",
    "ExecutionDecision",
    "LLMRouter",
    "TradingAgentsOrchestrator",
]
