#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# core/trading_agents/orchestrator.py — Master TradingAgents Pipeline Orchestrator
# Inspired by TauricResearch/TradingAgents (UCLA & MIT)
#
# Coordinates the full hierarchical multi-agent workflow:
# 1. Analyst Team (4 Specialists)
# 2. Bull vs Bear Dialectical Debate
# 3. Quant Trader Synthesis & Net Edge Gating
# 4. Risk Committee & Fund Manager Executive Decision
# 5. SQLite Persistence & Report Generation
# =============================================================================

from typing import Dict, Any, List, Optional
import json
import datetime
import sqlite3
import os

from .analyst_team import AnalystTeamOrchestrator, AnalystTeamReport
from .debate_engine import DebateModerator, DebateTranscript
from .trader_agent import TraderAgent, TradeProposal
from .risk_and_fund_manager import RiskManagerAgent, FundManagerAgent, ExecutionDecision
from core.database_engine import DatabaseEngine


class TradingAgentsOrchestrator:
    """
    Coordinates full end-to-end multi-agent trading sessions on EGX equities.
    """

    @classmethod
    def run_stock_deliberation(
        cls,
        ticker: str,
        custom_fundamentals: Optional[Dict[str, Any]] = None,
        persist: bool = True
    ) -> Dict[str, Any]:
        """
        Executes a complete 4-tier TradingAgents deliberation session on a single stock.
        """
        sym = ticker.upper().strip()
        if not sym.endswith(".CA") and "." not in sym:
            sym = f"{sym}.CA"

        # Step 1: Specialist Analysts
        analyst_report: AnalystTeamReport = AnalystTeamOrchestrator.run_all(sym, custom_fundamentals)

        # Step 2: Bull vs Bear Debate
        debate_transcript: DebateTranscript = DebateModerator.conduct_debate(analyst_report)

        # Step 3: Quant Trader Proposal
        trade_proposal: TradeProposal = TraderAgent.construct_proposal(analyst_report, debate_transcript)

        # Step 4: Risk Review
        risk_evaluation = RiskManagerAgent.evaluate_risk(trade_proposal)

        # Step 5: Fund Manager Executive Decision
        execution_decision: ExecutionDecision = FundManagerAgent.review_and_decide(trade_proposal, risk_evaluation)

        # Structure complete output
        session_result = {
            "session_id": f"TA_SESS_{sym}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "ticker": sym,
            "timestamp": datetime.datetime.now().isoformat(),
            "market_price": analyst_report.market_price,
            "analyst_team": {
                "composite_bias": analyst_report.composite_bias,
                "average_conviction": analyst_report.average_conviction,
                "fundamental": {
                    "stance": analyst_report.fundamental.stance,
                    "conviction": analyst_report.fundamental.conviction,
                    "summary_ar": analyst_report.fundamental.summary_ar,
                    "findings": analyst_report.fundamental.detailed_findings
                },
                "technical": {
                    "stance": analyst_report.technical.stance,
                    "conviction": analyst_report.technical.conviction,
                    "summary_ar": analyst_report.technical.summary_ar,
                    "findings": analyst_report.technical.detailed_findings
                },
                "macro_news": {
                    "stance": analyst_report.macro_news.stance,
                    "conviction": analyst_report.macro_news.conviction,
                    "summary_ar": analyst_report.macro_news.summary_ar,
                    "findings": analyst_report.macro_news.detailed_findings
                },
                "sentiment": {
                    "stance": analyst_report.sentiment.stance,
                    "conviction": analyst_report.sentiment.conviction,
                    "summary_ar": analyst_report.sentiment.summary_ar,
                    "findings": analyst_report.sentiment.detailed_findings
                }
            },
            "debate": {
                "winner": debate_transcript.debate_winner,
                "bull_score": debate_transcript.bull_conviction_score,
                "bear_score": debate_transcript.bear_skepticism_score,
                "consensus_ar": debate_transcript.consensus_summary_ar,
                "rounds": [
                    {
                        "round": r.round_number,
                        "point": r.key_contested_point,
                        "bull_argument_ar": r.bull_argument_ar,
                        "bear_argument_ar": r.bear_counter_argument_ar
                    }
                    for r in debate_transcript.rounds
                ],
                "residual_risks": debate_transcript.residual_risks
            },
            "proposal": {
                "action": trade_proposal.action,
                "action_ar": trade_proposal.action_label_ar,
                "expected_gross_return_pct": trade_proposal.expected_gross_return_pct,
                "roundtrip_friction_pct": trade_proposal.roundtrip_friction_pct,
                "estimated_slippage_pct": trade_proposal.estimated_slippage_pct,
                "uncertainty_penalty_pct": trade_proposal.uncertainty_penalty_pct,
                "net_edge_pct": trade_proposal.net_edge_pct,
                "meets_edge_hurdle": trade_proposal.meets_edge_hurdle,
                "entry_zone": [trade_proposal.entry_zone_low, trade_proposal.entry_zone_high],
                "hard_stop_loss": trade_proposal.hard_stop_loss,
                "profit_targets": [trade_proposal.profit_target_1, trade_proposal.profit_target_2],
                "horizon_days": trade_proposal.recommended_horizon_days,
                "sizing_weight": trade_proposal.sizing_weight,
                "rationale_ar": trade_proposal.rationale_ar
            },
            "risk_review": risk_evaluation,
            "executive_decision": {
                "status": execution_decision.decision_status,
                "status_ar": execution_decision.decision_status_ar,
                "is_executable": execution_decision.is_executable,
                "allocated_nav_pct": execution_decision.allocated_nav_pct,
                "mandate_ar": execution_decision.final_mandate_ar,
                "execution_blotter": execution_decision.execution_blotter
            }
        }

        if persist:
            cls._persist_session(session_result)

        return session_result

    @classmethod
    def _persist_session(cls, session: Dict[str, Any]):
        """Persists deliberation record into SQLite."""
        try:
            from core.database_engine import SQLiteDatabaseEngine
            db_path = SQLiteDatabaseEngine.DEFAULT_DB_PATH
            if not os.path.exists(db_path):
                return
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS trading_agents_debates (
                    session_id TEXT PRIMARY KEY,
                    ticker TEXT,
                    timestamp TEXT,
                    market_price REAL,
                    debate_winner TEXT,
                    action TEXT,
                    net_edge_pct REAL,
                    decision_status TEXT,
                    allocated_nav_pct REAL,
                    full_payload JSON
                )
            """)
            cur.execute("""
                INSERT OR REPLACE INTO trading_agents_debates
                (session_id, ticker, timestamp, market_price, debate_winner, action, net_edge_pct, decision_status, allocated_nav_pct, full_payload)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session["session_id"],
                session["ticker"],
                session["timestamp"],
                session["market_price"],
                session["debate"]["winner"],
                session["proposal"]["action"],
                session["proposal"]["net_edge_pct"],
                session["executive_decision"]["status"],
                session["executive_decision"]["allocated_nav_pct"],
                json.dumps(session, ensure_ascii=False)
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[WARN] Failed to persist TradingAgents session: {e}")

    @classmethod
    def run_universe_scan(cls, tickers: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Runs multi-agent scan across focus equities."""
        target_list = tickers or ["COMI.CA", "SWDY.CA", "TMGH.CA", "MFPC.CA", "ETEL.CA", "FWRY.CA"]
        results = []
        for sym in target_list:
            res = cls.run_stock_deliberation(sym, persist=True)
            results.append(res)
        return results


if __name__ == "__main__":
    import sys
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    print("Testing TradingAgentsOrchestrator on COMI.CA...")
    res = TradingAgentsOrchestrator.run_stock_deliberation("COMI.CA")
    print(f"Session ID: {res['session_id']}")
    print(f"Debate Winner: {res['debate']['winner']}")
    print(f"Action: {res['proposal']['action']} ({res['proposal']['action_ar']})")
    print(f"Net Edge: +{res['proposal']['net_edge_pct']}%")
    print(f"Decision: {res['executive_decision']['status_ar']}")
    print(f"Mandate: {res['executive_decision']['mandate_ar']}")
