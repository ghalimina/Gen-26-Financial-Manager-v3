#!/usr/bin/env python3
# =============================================================================
# tests/test_promotion_gate_and_research_lab.py — Sprint 3 STLC Research & Promotion Gate Tests
# Validates the Autonomous Self-Improvement & Promotion Gate Engine:
# - TC-C01: Autonomous research cycle execution and SQLite logging.
# - TC-C02: Critic Auditor rejection on severe OOS degradation (>35%).
# - TC-C03: Purged Walk-Forward metrics calculation with 0.35% friction & 10% tax.
# - TC-C04: Promoted strategy calibration updates.
# - TC-C05: Quarantined pattern avoidance from failure memory.
# =============================================================================

import os
import sys
import unittest
import datetime

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.database_engine import db_engine
from core.promotion_gate import PromotionGate
from core.autonomous_research_lab import AutonomousResearchLab
from core.multi_agent_council import ResearchScientistAgent, CriticAuditorAgent
from core.weight_calibrator import WeightCalibrator
from dashboard.app import app


class TestPromotionGateAndResearchLab(unittest.TestCase):

    def setUp(self):
        """Initialize database before each test case."""
        self.app = app.test_client()
        self.app.testing = True
        db_engine.initialize_database()

    def test_tc_c01_autonomous_research_cycle_execution(self):
        """
        TC-C01: Autonomous research cycle execution and SQLite logging.
        Verifies that running a research cycle executes all 5 stages and records in SQLite.
        """
        result = AutonomousResearchLab.run_autonomous_research_cycle(regime_context="BULL_MOMENTUM")
        
        self.assertIsNotNone(result)
        self.assertIn("cycle_id", result)
        self.assertIn("experiment_id", result)
        self.assertIn("hypothesis", result)
        self.assertIn("critic_audit", result)
        self.assertIn("walk_forward_evaluation", result)
        self.assertIn("promotion_decision", result)
        self.assertIn(result["final_status"], ["PROMOTED", "REJECTED"])

        # Verify SQLite Journal Persistence
        recent_exps = db_engine.get_recent_experiments(limit=5)
        self.assertGreaterEqual(len(recent_exps), 1)
        self.assertTrue(any(e["experiment_id"] == result["experiment_id"] for e in recent_exps))

        # Test Flask API Endpoints
        resp_exp = self.app.get("/api/research/experiments")
        self.assertEqual(resp_exp.status_code, 200)
        data_exp = resp_exp.get_json()
        self.assertEqual(data_exp["status"], "SUCCESS")
        self.assertGreater(len(data_exp["experiments"]), 0)

    def test_tc_c02_critic_auditor_rejection_severe_degradation(self):
        """
        TC-C02: Critic Auditor rejection on severe OOS degradation (>35%).
        """
        past_failures = db_engine.get_failure_memory()
        
        overfitted_hypo = {
            "experiment_id": "EXP_OVERFIT_SEVERE",
            "hypothesis_title": "Overfitted Neural Strategy",
            "features_used": ["frac_diff_d45", "stochastic_momentum"],
            "parameters": {"friction_allowance_pct": 0.35},
            "in_sample_sharpe": 3.80,
            "oos_sharpe": 1.20, # Degradation = 68.4% > 35%
            "max_drawdown_pct": 14.5,
            "win_rate_pct": 52.0
        }
        
        audit_res = CriticAuditorAgent.audit_experiment(overfitted_hypo, past_failures)
        self.assertEqual(audit_res["promotion_status"], "REJECTED")
        self.assertLess(audit_res["critic_score"], 80.0)
        self.assertTrue(any("تدهور" in r or "Overfitting" in r for r in audit_res["rejection_reasons"]))

        # Judge promotion gate directly
        judge_res = PromotionGate.judge_promotion({
            "in_sample_sharpe": 3.80,
            "oos_sharpe": 1.20,
            "max_drawdown_pct": 14.5,
            "degradation_pct": 68.4
        })
        self.assertFalse(judge_res["approved"])
        self.assertEqual(judge_res["promotion_status"], "REJECTED")

    def test_tc_c03_purged_walk_forward_metrics_and_friction(self):
        """
        TC-C03: Purged Walk-Forward metrics calculation with 0.35% friction & 10% tax.
        Verifies 5-fold evaluation, deflation ratio, and friction penalties.
        """
        hypo = {
            "experiment_id": "EXP_WF_EVAL",
            "in_sample_sharpe": 2.40,
            "oos_sharpe": 1.90,
            "max_drawdown_pct": 8.0,
            "win_rate_pct": 65.0,
            "num_trials": 15
        }
        
        wf_res = PromotionGate.evaluate_candidate_strategy(hypo)
        
        self.assertEqual(wf_res["folds_evaluated"], 5)
        self.assertEqual(wf_res["friction_applied_pct"], 0.35)
        self.assertEqual(wf_res["tax_applied_pct"], 10.0)
        self.assertGreater(wf_res["in_sample_sharpe"], 0.0)
        self.assertGreater(wf_res["oos_sharpe"], 0.0)
        self.assertGreater(wf_res["deflated_sharpe_ratio"], 0.50)
        self.assertGreaterEqual(wf_res["degradation_pct"], 0.0)

    def test_tc_c04_promoted_strategy_calibration_updates(self):
        """
        TC-C04: Promoted strategy calibration updates.
        Verifies that winning strategy weights are verified against invariants and saved.
        """
        valid_weights = {
            "w_fundamental": 0.30,
            "w_technical": 0.35,
            "w_flow": 0.20,
            "w_rs": 0.15
        }
        
        success = PromotionGate.apply_promoted_weights(valid_weights)
        self.assertTrue(success)

        # Verify active weights from WeightCalibrator
        active_w = WeightCalibrator.get_calibrated_weights()
        self.assertAlmostEqual(active_w["w_fundamental"], 0.30, places=2)
        self.assertAlmostEqual(active_w["w_technical"], 0.35, places=2)

        # Test invariant rejection on degenerate/negative weights (< 5% floor)
        invalid_weights = {
            "w_fundamental": 0.98,
            "w_technical": 0.01, # Violates 5% floor
            "w_flow": 0.005,
            "w_rs": 0.005
        }
        rej_success = PromotionGate.apply_promoted_weights(invalid_weights)
        self.assertFalse(rej_success)

    def test_tc_c05_quarantined_pattern_avoidance(self):
        """
        TC-C05: Quarantined pattern avoidance from failure memory.
        Ensures ResearchScientistAgent checks failure memory and does not reuse quarantined features.
        """
        # 1. Insert a mock quarantined pattern into failure memory
        fail_data = {
            "failure_id": "FAIL_TC_C05",
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "regime": "BEAR_CORRECTION",
            "failed_hypothesis": "Raw 14-period RSI Dip Buying without Trend Filter",
            "root_cause_analysis": "Severe whipsaw and catching falling knives",
            "lesson_learned_ar": "حظر التداول بمؤشر RSI المنفرد دون فلتر اتجاه ADX",
            "quarantined_patterns": ["quarantined_raw_rsi14_dip"]
        }
        db_engine.record_failure_lesson(fail_data)

        # 2. Formulate hypothesis
        failure_mem = db_engine.get_failure_memory()
        hypo = ResearchScientistAgent.formulate_hypothesis(
            current_regime="BEAR_CORRECTION",
            failure_memory=failure_mem
        )
        
        # Verify formulated hypothesis avoids quarantined patterns
        for feat in hypo.get("features_used", []):
            self.assertNotIn("quarantined_raw_rsi14_dip", feat)

        # Test Flask API Endpoint for failure memory
        resp_fail = self.app.get("/api/research/memory/failures")
        self.assertEqual(resp_fail.status_code, 200)
        data_fail = resp_fail.get_json()
        self.assertEqual(data_fail["status"], "SUCCESS")
        self.assertGreater(len(data_fail["failure_memory"]), 0)


if __name__ == "__main__":
    unittest.main()
