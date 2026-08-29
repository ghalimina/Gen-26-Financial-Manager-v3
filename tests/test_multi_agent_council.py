#!/usr/bin/env python3
# =============================================================================
# tests/test_multi_agent_council.py — GEN-26 Multi-Agent Quant Council Tests
# Validates the 7-Agent Council, consensus voting rules, Mark Douglas risk sizing,
# research hypothesis generation, anti-overfitting auditor, and episodic memory persistence.
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
        db_engine.initialize_database()

    def test_01_market_analyst_agent_evaluation(self):
        """Verify MarketAnalystAgent returns structured macro and flow bias analysis."""
        res = MarketAnalystAgent.evaluate("COMI.CA")
        self.assertEqual(res["agent_name"], "MarketAnalystAgent")
        self.assertIn(res["vote"], ["BULLISH", "BEARISH", "NEUTRAL"])
        self.assertGreaterEqual(res["conviction"], 0.0)
        self.assertLessEqual(res["conviction"], 100.0)
        self.assertIn("cbe_corridor_rate", res)
        self.assertIn("inflation_rate", res)
        self.assertIn("usd_egp", res)
        self.assertTrue(len(res["rationale_ar"]) > 10)

    def test_02_fundamentalist_agent_evaluation_and_piotroski_f_score(self):
        """Verify FundamentalistAgent calculates DCF fair value, Piotroski F-Score (0-9), and PEG."""
        res = FundamentalistAgent.evaluate("COMI.CA", market_price=139.28)
        self.assertEqual(res["agent_name"], "FundamentalistAgent")
        self.assertIn(res["vote"], ["BULLISH", "BEARISH", "NEUTRAL"])
        self.assertGreaterEqual(res["piotroski_f_score"], 0)
        self.assertLessEqual(res["piotroski_f_score"], 9)
        self.assertGreater(res["fair_value_dcf"], 0.0)
        self.assertIn("margin_of_safety_pct", res)
        self.assertIn("peg_ratio", res)
        self.assertTrue(len(res["rationale_ar"]) > 10)

    def test_03_technician_agent_evaluation_and_candlesticks(self):
        """Verify TechnicianAgent evaluates ADX, RSI, Support/Resistance, and Candlestick patterns."""
        res = TechnicianAgent.evaluate("SWDY.CA", market_price=116.00)
        self.assertEqual(res["agent_name"], "TechnicianAgent")
        self.assertIn(res["vote"], ["BULLISH", "BEARISH", "NEUTRAL"])
        self.assertGreaterEqual(res["rsi_14"], 0.0)
        self.assertLessEqual(res["rsi_14"], 100.0)
        self.assertGreaterEqual(res["adx_strength"], 0.0)
        self.assertGreater(res["support_level"], 0.0)
        self.assertGreater(res["resistance_level"], res["support_level"] * 0.90)
        self.assertIsInstance(res["candlestick_patterns"], list)
        self.assertTrue(len(res["rationale_ar"]) > 10)

    def test_04_quant_modeler_agent_evaluation(self):
        """Verify QuantModelerAgent evaluates GDR parity, pairs arbitrage, and fractional diff momentum."""
        res = QuantModelerAgent.evaluate("COMI.CA", market_price=139.28)
        self.assertEqual(res["agent_name"], "QuantModelerAgent")
        self.assertIn(res["vote"], ["BULLISH", "BEARISH", "NEUTRAL"])
        self.assertIn("gdr_spread_pct", res)
        self.assertIn("pair_zscore", res)
        self.assertIn("frac_diff_momentum", res)
        self.assertIn("stealth_volume_detected", res)
        self.assertTrue(len(res["rationale_ar"]) > 10)

    def test_05_risk_sizer_agent_approvals_and_caps(self):
        """Verify RiskSizerAgent enforces Mark Douglas / Kelly sizing, max 30% cap, and R:R >= 2.5."""
        # Case A: Favorable setup with R:R = 3.0 (Target +15%, Stop -5%)
        res_a = RiskSizerAgent.evaluate("COMI.CA", current_price=100.0, target_price=115.0, stop_loss=95.0, portfolio_equity=100_000.0)
        self.assertTrue(res_a["approved"])
        self.assertEqual(res_a["vote"], "APPROVE")
        self.assertGreaterEqual(res_a["risk_reward_ratio"], 2.5)
        self.assertLessEqual(res_a["recommended_allocation_egp"], 30_000.0) # 30% cap
        self.assertLessEqual(res_a["portfolio_risk_pct"], 1.55) # 1.5% risk

        # Case B: Poor setup with R:R = 1.0 (Target +5%, Stop -5%)
        res_b = RiskSizerAgent.evaluate("COMI.CA", current_price=100.0, target_price=105.0, stop_loss=95.0, portfolio_equity=100_000.0)
        self.assertFalse(res_b["approved"])
        self.assertEqual(res_b["vote"], "REJECT")
        self.assertIn("أقل من الحد الأدنى", res_b["rationale_ar"])

    def test_06_research_scientist_hypothesis_generation(self):
        """Verify ResearchScientistAgent formulates testable quantitative hypotheses."""
        hyp = ResearchScientistAgent.formulate_hypothesis("STRONG_BULL")
        self.assertTrue(hyp["experiment_id"].startswith("EXP_"))
        self.assertEqual(hyp["agent_author"], "ResearchScientistAgent")
        self.assertIn("features_used", hyp)
        self.assertGreater(len(hyp["features_used"]), 0)
        self.assertGreater(hyp["in_sample_sharpe"], 0.0)
        self.assertGreater(hyp["oos_sharpe"], 0.0)

    def test_07_critic_auditor_agent_overfitting_and_promotion(self):
        """Verify CriticAuditorAgent promotes robust hypotheses and rejects overfitted ones."""
        # Case A: Robust hypothesis (IS Sharpe 2.4, OOS Sharpe 2.1)
        good_hyp = {
            "experiment_id": "EXP_TEST_GOOD",
            "features_used": ["frac_diff_d45", "gdr_spread"],
            "in_sample_sharpe": 2.4,
            "oos_sharpe": 2.1,
            "max_drawdown_pct": 8.0,
            "win_rate_pct": 65.0
        }
        audit_good = CriticAuditorAgent.audit_experiment(good_hyp)
        self.assertEqual(audit_good["promotion_status"], "PROMOTED")
        self.assertGreaterEqual(audit_good["critic_score"], 85.0)

        # Case B: Severe Overfitting (IS Sharpe 3.8, OOS Sharpe 1.0 -> 73% degradation)
        overfit_hyp = {
            "experiment_id": "EXP_TEST_OVERFIT",
            "features_used": ["frac_diff_d45"],
            "in_sample_sharpe": 3.8,
            "oos_sharpe": 1.0,
            "max_drawdown_pct": 18.0,
            "win_rate_pct": 45.0
        }
        audit_bad = CriticAuditorAgent.audit_experiment(overfit_hyp)
        self.assertEqual(audit_bad["promotion_status"], "REJECTED")
        self.assertTrue(len(audit_bad["rejection_reasons"]) >= 1)

    def test_08_council_deliberation_and_sqlite_persistence(self):
        """Verify full AgentCouncilOrchestrator deliberation on blue-chips and SQLite recording."""
        for ticker in ["COMI.CA", "SWDY.CA", "TMGH.CA"]:
            dossier = AgentCouncilOrchestrator.deliberate(ticker)
            self.assertEqual(dossier["ticker"], ticker)
            self.assertIn(dossier["consensus_verdict"], ["STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL", "REJECTED_BY_RISK_MANAGER"])
            self.assertGreaterEqual(dossier["conviction_score"], 0.0)
            self.assertLessEqual(dossier["conviction_score"], 100.0)
            self.assertIn("market_analyst_vote", dossier)
            self.assertIn("fundamentalist_vote", dossier)
            self.assertIn("technician_vote", dossier)
            self.assertIn("quant_modeler_vote", dossier)
            self.assertIn("risk_sizer_vote", dossier)

        # Check SQLite persistence
        votes = db_engine.get_recent_council_votes(limit=5)
        self.assertGreaterEqual(len(votes), 3)

    def test_09_autonomous_research_cycle_and_episodic_memory(self):
        """Verify autonomous research cycle records experiments and logs failure lessons."""
        res = AgentCouncilOrchestrator.run_autonomous_research_cycle()
        self.assertIn("experiment_id", res)
        self.assertIn(res["status"], ["PROMOTED", "REJECTED", "QUARANTINED"])
        
        # Verify persistence in research_experiments_journal
        exps = db_engine.get_recent_experiments(limit=5)
        self.assertGreaterEqual(len(exps), 1)

        # Manually record a failure case and verify retrieval
        fail_id = db_engine.record_failure_lesson({
            "failure_id": "FAIL_TEST_001",
            "regime": "BEAR_CORRECTION",
            "failed_hypothesis": "Test Reversal Hypothesis",
            "root_cause_analysis": "Look-ahead bias in price channel breakout",
            "lesson_learned_ar": "لا يجب الدخول قبل إغلاق شمعة اليوم لتأكيد الكسر",
            "quarantined_patterns": ["overfit_rsi_3d"]
        })
        self.assertEqual(fail_id, "FAIL_TEST_001")
        
        failures = db_engine.get_failure_memory(limit=5)
        self.assertTrue(any(f["failure_id"] == "FAIL_TEST_001" for f in failures))


if __name__ == "__main__":
    unittest.main()
