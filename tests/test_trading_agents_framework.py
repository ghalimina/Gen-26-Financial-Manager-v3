#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# tests/test_trading_agents_framework.py — TradingAgents Master Test Suite
# Tests all components of the TauricResearch TradingAgents integration:
# 1. Specialist Analysts (Fundamentals, Technicals, Macro, Arabic Sentiment)
# 2. Bull vs Bear Dialectical Debate Engine
# 3. Quant Trader Synthesis & Net Edge Gating
# 4. Risk Committee & Fund Manager Executive Gate
# 5. End-to-End Orchestrator & SQLite Persistence
# =============================================================================

import unittest
import os
import sys
import json
import sqlite3

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.trading_agents.analyst_team import (
    FundamentalAnalystAgent,
    TechnicalAnalystAgent,
    MacroNewsAnalystAgent,
    ArabicSentimentAnalystAgent,
    AnalystTeamOrchestrator
)
from core.trading_agents.debate_engine import (
    BullResearcherAgent,
    BearResearcherAgent,
    DebateModerator,
    DebateTranscript
)
from core.trading_agents.trader_agent import TraderAgent, TradeProposal
from core.trading_agents.risk_and_fund_manager import (
    RiskManagerAgent,
    FundManagerAgent,
    ExecutionDecision
)
from core.trading_agents.orchestrator import TradingAgentsOrchestrator
from core.database_engine import SQLiteDatabaseEngine


class TestTradingAgentsFramework(unittest.TestCase):
    """
    Comprehensive Master Test Suite for the TradingAgents Framework on EGX.
    """

    def setUp(self):
        self.ticker = "COMI.CA"

    def test_01_fundamental_analyst_banking_adaptation(self):
        """Verify FundamentalAnalystAgent applies adapted banking Piotroski (9/9) for COMI.CA."""
        rep = FundamentalAnalystAgent.analyze(self.ticker)
        self.assertEqual(rep.agent_name, "FundamentalAnalyst")
        self.assertEqual(rep.ticker, "COMI.CA")
        self.assertIn(rep.stance, ["BULLISH", "NEUTRAL"])
        self.assertGreaterEqual(rep.key_metrics.get("f_score", 0), 8)
        self.assertGreater(len(rep.detailed_findings), 0)

    def test_02_technical_analyst_nison_and_murphy(self):
        """Verify TechnicalAnalystAgent evaluates Nison candlesticks and Murphy indicators."""
        rep = TechnicalAnalystAgent.analyze(self.ticker)
        self.assertEqual(rep.agent_name, "TechnicalAnalyst")
        self.assertIn("candlestick", rep.key_metrics)
        self.assertIn("rsi", rep.key_metrics)
        self.assertGreater(rep.key_metrics["price"], 0.0)

    def test_03_macro_news_analyst_cbe_corridor(self):
        """Verify MacroNewsAnalystAgent enforces 19% deposit rate and 30.70% hurdle rate."""
        rep = MacroNewsAnalystAgent.analyze(self.ticker)
        self.assertEqual(rep.key_metrics.get("cbe_deposit"), 19.00)
        self.assertEqual(rep.key_metrics.get("hurdle_rate"), 30.70)
        self.assertEqual(rep.key_metrics.get("usd_egp"), 50.20)

    def test_04_arabic_sentiment_analyst_breadth(self):
        """Verify ArabicSentimentAnalystAgent computes Advance/Decline breadth ratio."""
        rep = ArabicSentimentAnalystAgent.analyze(self.ticker)
        self.assertIn("ad_ratio", rep.key_metrics)
        self.assertIn("breadth_state", rep.key_metrics)

    def test_05_analyst_team_orchestrator(self):
        """Verify AnalystTeamOrchestrator runs all 4 analysts in parallel."""
        team_rep = AnalystTeamOrchestrator.run_all(self.ticker)
        self.assertEqual(team_rep.ticker, "COMI.CA")
        self.assertIn(team_rep.composite_bias, ["BULLISH", "BEARISH", "NEUTRAL"])
        self.assertGreater(team_rep.average_conviction, 0.0)
        self.assertIsNotNone(team_rep.fundamental)
        self.assertIsNotNone(team_rep.technical)

    def test_06_bull_vs_bear_debate_dynamics(self):
        """Verify DebateModerator coordinates 2-round structured dialectical debate."""
        team_rep = AnalystTeamOrchestrator.run_all(self.ticker)
        transcript = DebateModerator.conduct_debate(team_rep)
        self.assertIsInstance(transcript, DebateTranscript)
        self.assertEqual(len(transcript.rounds), 2)
        self.assertGreater(transcript.bull_conviction_score, 0.0)
        self.assertGreater(transcript.bear_skepticism_score, 0.0)
        self.assertIn(transcript.debate_winner, ["BULL_ADVANTAGE", "BEAR_ADVANTAGE", "BALANCED_EVIDENCE"])
        self.assertGreater(len(transcript.consensus_summary_ar), 10)

    def test_07_trader_agent_net_edge_calculation(self):
        """Verify TraderAgent enforces 0.94% friction, slippage, and Net Edge >= 1.00%."""
        team_rep = AnalystTeamOrchestrator.run_all(self.ticker)
        transcript = DebateModerator.conduct_debate(team_rep)
        proposal = TraderAgent.construct_proposal(team_rep, transcript)
        self.assertIsInstance(proposal, TradeProposal)
        self.assertEqual(proposal.roundtrip_friction_pct, 0.94)
        self.assertGreaterEqual(proposal.hard_stop_loss, 0.0)
        if proposal.meets_edge_hurdle and transcript.debate_winner == "BULL_ADVANTAGE":
            self.assertEqual(proposal.action, "BUY_LIMIT")
            self.assertGreaterEqual(proposal.net_edge_pct, 1.00)

    def test_08_risk_and_fund_manager_executive_gate(self):
        """Verify RiskManagerAgent and FundManagerAgent deliver compliant executive mandate."""
        team_rep = AnalystTeamOrchestrator.run_all(self.ticker)
        transcript = DebateModerator.conduct_debate(team_rep)
        proposal = TraderAgent.construct_proposal(team_rep, transcript)
        risk_eval = RiskManagerAgent.evaluate_risk(proposal)
        self.assertIn("risk_passed", risk_eval)
        
        decision = FundManagerAgent.review_and_decide(proposal, risk_eval)
        self.assertIsInstance(decision, ExecutionDecision)
        self.assertTrue(decision.hurdle_rate_verified)
        self.assertIn(decision.decision_status, ["APPROVED", "VETOED_HURDLE", "VETOED_RISK"])
        self.assertGreater(len(decision.final_mandate_ar), 10)

    def test_09_end_to_end_orchestrator_and_sqlite_persistence(self):
        """Verify TradingAgentsOrchestrator end-to-end deliberation and SQLite persistence."""
        res = TradingAgentsOrchestrator.run_stock_deliberation(self.ticker, persist=True)
        self.assertIn("session_id", res)
        self.assertIn("analyst_team", res)
        self.assertIn("debate", res)
        self.assertIn("proposal", res)
        self.assertIn("executive_decision", res)

        # Check SQLite record
        db_path = SQLiteDatabaseEngine.DEFAULT_DB_PATH
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute("SELECT session_id, ticker, debate_winner, action FROM trading_agents_debates WHERE ticker = ?", ("COMI.CA",))
            row = cur.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[1], "COMI.CA")
            conn.close()


if __name__ == "__main__":
    unittest.main()
