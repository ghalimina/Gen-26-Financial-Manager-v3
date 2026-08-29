#!/usr/bin/env python3
# =============================================================================
# tests/test_multi_agent_council.py — Sprint 1 STLC Multi-Agent Council Test Suite
# Implements strict STLC verification covering all 5 test cases in the test matrix:
# - TC-01: Valid council synthesis on COMI.CA
# - TC-02: Risk & Friction bounds calculation (Mark Douglas / Kelly sizing, R:R >= 2.5)
# - TC-03: Fail-safe handling on unknown/invalid tickers
# - TC-04: Database persistence and retrieval of failure memory
# - TC-05: Critic Auditor rejection of overfitted/leaked hypotheses
# =============================================================================

import os
import sys
import unittest
import datetime

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.multi_agent_council import (
    MarketAnalystAgent,
    FundamentalistAgent,
    TechnicianAgent,
    QuantModelerAgent,
    RiskSizerAgent,
    ResearchScientistAgent,
    CriticAuditorAgent,
    AgentCouncilOrchestrator
)
from core.database_engine import db_engine


class TestMultiAgentCouncil(unittest.TestCase):

    def setUp(self):
        """Initialize database before each test case."""
        db_engine.initialize_database()

    def test_tc01_valid_council_synthesis_comi(self):
        """
        TC-01: Valid council synthesis on COMI.CA.
        Verifies that all 5 analytical voting agents deliberate properly,
        consensus strength is calculated, and vote is recorded in SQLite.
        """
        dossier = AgentCouncilOrchestrator.deliberate("COMI.CA")
        
        self.assertIsNotNone(dossier)
        self.assertEqual(dossier["ticker"], "COMI.CA")
        self.assertIn(dossier["consensus_verdict"], [
            "STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL", "REJECTED_BY_RISK_MANAGER"
        ])
        self.assertGreaterEqual(dossier["conviction_score"], 0.0)
        self.assertLessEqual(dossier["conviction_score"], 100.0)
        
        # Verify 5 voting agents participate
        self.assertIn("market_analyst_vote", dossier)
        self.assertIn("fundamentalist_vote", dossier)
        self.assertIn("technician_vote", dossier)
        self.assertIn("quant_modeler_vote", dossier)
        self.assertIn("risk_sizer_vote", dossier)

        # Verify votes persistence in SQLite
        votes = db_engine.get_recent_council_votes(limit=5, ticker="COMI.CA")
        self.assertGreaterEqual(len(votes), 1)
        self.assertEqual(votes[0]["ticker"], "COMI.CA")

    def test_tc02_risk_and_friction_bounds_calculation(self):
        """
        TC-02: Risk & Friction bounds calculation.
        Verifies Mark Douglas / Kelly sizing rules:
        - Max 1.5% portfolio risk per trade
        - Max 30% single-stock allocation cap
        - Minimum 1:2.5 Risk/Reward ratio for full approval
        - Rejection if R:R < 1.8
        """
        portfolio_equity = 100_000.0

        # Scenario A: Favorable setup with R:R = 3.0 (Target +15%, Stop -5%)
        res_approved = RiskSizerAgent.evaluate(
            ticker="COMI.CA",
            current_price=100.0,
            target_price=115.0,
            stop_loss=95.0,
            portfolio_equity=portfolio_equity
        )
        self.assertTrue(res_approved["approved"])
        self.assertEqual(res_approved["vote"], "APPROVE")
        self.assertGreaterEqual(res_approved["risk_reward_ratio"], 2.5)
        self.assertLessEqual(res_approved["recommended_allocation_egp"], portfolio_equity * 0.30)
        self.assertLessEqual(res_approved["portfolio_risk_pct"], 1.55)

        # Scenario B: Unfavorable setup with R:R = 1.0 (Target +5%, Stop -5%)
        res_rejected = RiskSizerAgent.evaluate(
            ticker="COMI.CA",
            current_price=100.0,
            target_price=105.0,
            stop_loss=95.0,
            portfolio_equity=portfolio_equity
        )
        self.assertFalse(res_rejected["approved"])
        self.assertEqual(res_rejected["vote"], "REJECT")
        self.assertLess(res_rejected["risk_reward_ratio"], 1.8)
        self.assertIn("أقل من الحد الأدنى", res_rejected["rationale_ar"])

    def test_tc03_failsafe_handling_on_unknown_or_invalid_tickers(self):
        """
        TC-03: Fail-safe handling on unknown/invalid tickers.
        Ensures orchestrator does not crash on empty strings, None, or invalid ticker names,
        and returns a clean DATA_UNAVAILABLE_HOLD fallback dossier.
        """
        for invalid_sym in ["", None, "INVALID_XYZ", "UNKNOWN.CA", "NULL"]:
            dossier = AgentCouncilOrchestrator.deliberate(invalid_sym)
            self.assertIsNotNone(dossier)
            self.assertEqual(dossier["consensus_verdict"], "DATA_UNAVAILABLE_HOLD")
            self.assertEqual(dossier["conviction_score"], 0.0)
            self.assertFalse(dossier["risk_sizer_vote"]["approved"])

    def test_tc04_database_persistence_and_failure_memory(self):
        """
        TC-04: Database persistence and retrieval of failure memory.
        Validates recording and retrieval of:
        - Research experiments in `research_experiments_journal`
        - Failure post-mortems and quarantined patterns in `failure_cases_memory`
        """
        # 1. Record an experiment
        exp_data = {
            "experiment_id": "EXP_STLC_TC04",
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "hypothesis_title": "EGX30 Volatility Breakout with Fractional Diff",
            "hypothesis_description": "Testing d=0.45 memory preservation on breakout signals",
            "agent_author": "ResearchScientistAgent",
            "features_used": ["frac_diff_d45", "atr14_normalized"],
            "parameters": {"frac_diff_d": 0.45, "friction_allowance_pct": 0.35},
            "in_sample_sharpe": 2.20,
            "oos_sharpe": 1.95,
            "max_drawdown_pct": 7.5,
            "win_rate_pct": 64.0,
            "critic_score": 92.0,
            "critic_notes_ar": "فرضية مجازة رقابياً",
            "promotion_status": "PROMOTED"
        }
        exp_success = db_engine.record_experiment(exp_data)
        self.assertTrue(exp_success)

        recent_exps = db_engine.get_recent_experiments(limit=100)
        self.assertTrue(any(e["experiment_id"] == "EXP_STLC_TC04" for e in recent_exps))

        # 2. Record a failure lesson
        fail_data = {
            "failure_id": "FAIL_STLC_TC04",
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "regime": "BEAR_CORRECTION",
            "failed_hypothesis": "Unfiltered Penny Stock Momentum",
            "root_cause_analysis": "Illiquidity dryup and wide bid-ask spread slippage",
            "lesson_learned_ar": "حظر التداول على الأسهم ذات متوسط سيولة يومية أقل من 5 مليون ج.م",
            "quarantined_patterns": ["penny_stock_unfiltered_momentum"]
        }
        fail_success = db_engine.record_failure_lesson(fail_data)
        self.assertTrue(fail_success)

        failure_memory = db_engine.get_failure_memory(limit=100)
        self.assertTrue(any(f["failure_id"] == "FAIL_STLC_TC04" for f in failure_memory))

    def test_tc05_critic_auditor_rejection_of_overfitted_and_leaked_hypotheses(self):
        """
        TC-05: Critic Auditor rejection of overfitted/leaked hypotheses.
        Tests 3 critical auditor filters:
        1. Overfitting (Sharpe degradation > 35%)
        2. Look-ahead bias / Data leakage (Leaked target in features)
        3. Low friction allowance (< 0.25%)
        """
        past_failures = db_engine.get_failure_memory()

        # Case 1: Overfitted hypothesis (IS Sharpe 3.6, OOS Sharpe 1.1 -> 69% degradation)
        overfit_exp = {
            "experiment_id": "EXP_OVERFIT_TEST",
            "features_used": ["frac_diff_d45"],
            "parameters": {"friction_allowance_pct": 0.35},
            "in_sample_sharpe": 3.6,
            "oos_sharpe": 1.1,
            "max_drawdown_pct": 16.0,
            "win_rate_pct": 48.0
        }
        audit_overfit = CriticAuditorAgent.audit_experiment(overfit_exp, past_failures)
        self.assertEqual(audit_overfit["promotion_status"], "REJECTED")
        self.assertLess(audit_overfit["critic_score"], 80.0)
        self.assertTrue(any("Overfitting" in r or "تدهور" in r for r in audit_overfit["rejection_reasons"]))

        # Case 2: Data leakage / Look-ahead bias hypothesis
        leaked_exp = {
            "experiment_id": "EXP_LEAK_TEST",
            "features_used": ["frac_diff_d45", "future_target_return_t1"],
            "parameters": {"friction_allowance_pct": 0.35},
            "in_sample_sharpe": 2.5,
            "oos_sharpe": 2.2,
            "max_drawdown_pct": 6.0,
            "win_rate_pct": 70.0
        }
        audit_leaked = CriticAuditorAgent.audit_experiment(leaked_exp, past_failures)
        self.assertEqual(audit_leaked["promotion_status"], "REJECTED")
        self.assertTrue(any("تسريب" in r for r in audit_leaked["rejection_reasons"]))

        # Case 3: Low friction allowance (< 0.25%)
        frictionless_exp = {
            "experiment_id": "EXP_NO_FRICTION_TEST",
            "features_used": ["frac_diff_d45", "gdr_spread"],
            "parameters": {"friction_allowance_pct": 0.05},
            "in_sample_sharpe": 2.5,
            "oos_sharpe": 2.2,
            "max_drawdown_pct": 6.0,
            "win_rate_pct": 70.0
        }
        audit_friction = CriticAuditorAgent.audit_experiment(frictionless_exp, past_failures)
        self.assertEqual(audit_friction["promotion_status"], "REJECTED")
        self.assertTrue(any("تكاليف التداول" in r for r in audit_friction["rejection_reasons"]))


if __name__ == "__main__":
    unittest.main()
