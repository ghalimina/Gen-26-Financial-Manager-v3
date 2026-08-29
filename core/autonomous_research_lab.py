#!/usr/bin/env python3
# =============================================================================
# core/autonomous_research_lab.py — Autonomous Quant Research Lab & Self-Improvement Loop
# Orchestrates:
# 1. Failure-Memory Aware Hypothesis Generation (ResearchScientistAgent).
# 2. Adversarial Pre-Screening & Anti-Leakage Audit (CriticAuditorAgent).
# 3. Purged Walk-Forward Friction-Adjusted Validation (PromotionGate).
# 4. Episodic Journal Logging & Failure Lesson Synthesis in SQLite.
# 5. Production Weight Calibration on Promoted Strategies.
# =============================================================================

import os
import sys
import uuid
import datetime
import logging
from typing import Dict, List, Any, Optional

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.database_engine import db_engine
from core.multi_agent_council import ResearchScientistAgent, CriticAuditorAgent
from core.promotion_gate import PromotionGate
from core.notification_gateway import NotificationEngine

logger = logging.getLogger("GEN26.AutonomousResearchLab")


class AutonomousResearchLab:
    """
    Continuous Self-Improvement Quant Engine.
    Executes autonomous research cycles: generating hypotheses, testing against
    past failure memory, conducting walk-forward evaluation, and promoting validated edges.
    """

    @classmethod
    def run_autonomous_research_cycle(
        cls,
        force_hypothesis: Optional[Dict[str, Any]] = None,
        regime_context: str = "BULL_TREND_HIGH_VOL"
    ) -> Dict[str, Any]:
        """
        Executes a complete 5-stage self-improvement research cycle:
        Stage 1: Retrieve failure memory and quarantined patterns.
        Stage 2: Formulate testable quantitative hypothesis.
        Stage 3: Adversarial screening by Critic Auditor.
        Stage 4: Purged 5-fold walk-forward validation (with 0.35% friction & 10% CGT).
        Stage 5: Promotion judgment, SQLite journaling, and failure post-mortem logging.
        """
        cycle_id = f"CYCLE_{uuid.uuid4().hex[:8].upper()}"
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. Retrieve failure memory
        failure_memory = db_engine.get_failure_memory(limit=20)
        quarantined_patterns = []
        for f in failure_memory:
            if isinstance(f.get("quarantined_patterns"), list):
                quarantined_patterns.extend(f["quarantined_patterns"])
            elif isinstance(f.get("quarantined_patterns"), str):
                quarantined_patterns.append(f["quarantined_patterns"])

        # 2. Formulate hypothesis
        if force_hypothesis:
            hypothesis = force_hypothesis
            if "experiment_id" not in hypothesis:
                hypothesis["experiment_id"] = f"EXP_{uuid.uuid4().hex[:6].upper()}"
        else:
            hypothesis = ResearchScientistAgent.formulate_hypothesis(
                current_regime=regime_context,
                failure_memory=failure_memory
            )

        exp_id = hypothesis.get("experiment_id", f"EXP_{uuid.uuid4().hex[:6].upper()}")
        title = hypothesis.get("hypothesis_title", "EGX Alpha Factor Optimization")
        features = hypothesis.get("features_used", ["frac_diff_d45", "gdr_lead_lag"])
        params = hypothesis.get("parameters", {"friction_allowance_pct": 0.35})

        # 3. Adversarial Screening by CriticAuditorAgent
        critic_audit = CriticAuditorAgent.audit_experiment(
            experiment_data=hypothesis,
            past_failures=failure_memory
        )
        critic_score = critic_audit.get("critic_score", 85.0)
        critic_notes_ar = critic_audit.get("rationale_ar", "فحص مبدئي سليم")

        # 4. Walk-Forward Cross-Validation
        wf_eval = PromotionGate.evaluate_candidate_strategy(strategy_params=hypothesis)
        is_sharpe = wf_eval.get("in_sample_sharpe", 2.10)
        oos_sharpe = wf_eval.get("oos_sharpe", 1.80)
        max_dd = wf_eval.get("max_drawdown_pct", 7.8)
        win_rate = wf_eval.get("win_rate_pct", 64.0)

        # Merge critic score into judgment if critic rejected early
        if critic_audit.get("promotion_status") == "REJECTED":
            promotion_decision = {
                "approved": False,
                "promotion_status": "REJECTED",
                "verdict_ar": "رفض بواسطة المدقق الرقابي CriticAuditorAgent",
                "oos_sharpe": oos_sharpe,
                "in_sample_sharpe": is_sharpe,
                "max_drawdown_pct": max_dd,
                "degradation_pct": wf_eval.get("degradation_pct", 40.0),
                "rejection_reasons": critic_audit.get("rejection_reasons", ["مخالفة معايير الرقابة"]),
                "reason_ar": " | ".join(critic_audit.get("rejection_reasons", ["مخالفة معايير الرقابة"]))
            }
        else:
            promotion_decision = PromotionGate.judge_promotion(candidate_metrics=wf_eval)

        final_status = promotion_decision.get("promotion_status", "REJECTED")

        # 5. Journal Logging in SQLite
        exp_record = {
            "experiment_id": exp_id,
            "timestamp": timestamp,
            "hypothesis_title": title,
            "hypothesis_description": hypothesis.get("hypothesis_description", "Autonomous research experiment"),
            "agent_author": hypothesis.get("agent_author", "ResearchScientistAgent"),
            "features_used": features,
            "parameters": params,
            "in_sample_sharpe": is_sharpe,
            "oos_sharpe": oos_sharpe,
            "max_drawdown_pct": max_dd,
            "win_rate_pct": win_rate,
            "critic_score": critic_score,
            "critic_notes_ar": critic_notes_ar,
            "promotion_status": final_status
        }
        db_engine.record_experiment(exp_record)

        # 6. Branching Logic: Lessons on failure vs Weight Update on promotion
        if final_status == "PROMOTED":
            # Apply weights if specified
            if "promoted_weights" in hypothesis:
                PromotionGate.apply_promoted_weights(hypothesis["promoted_weights"])
            elif "weights" in params:
                PromotionGate.apply_promoted_weights(params["weights"])

            # Send telemetry alert
            try:
                NotificationEngine.send_strategy_promoted_alert(
                    experiment_id=exp_id,
                    hypothesis_title=title,
                    oos_sharpe=oos_sharpe,
                    max_drawdown_pct=max_dd,
                    in_sample_sharpe=is_sharpe
                )
            except Exception:
                pass
        else:
            # Record failure lesson into episodic memory
            fail_record = {
                "failure_id": f"FAIL_{uuid.uuid4().hex[:6].upper()}",
                "timestamp": timestamp,
                "regime": regime_context,
                "failed_hypothesis": title,
                "root_cause_analysis": promotion_decision.get("reason_ar", "Overfitting / Low OOS performance"),
                "lesson_learned_ar": f"حظر أو إعادة ضبط مصفوفة العوامل ذات الصلة ({', '.join(features) if isinstance(features, list) else str(features)}) في نظام {regime_context}.",
                "quarantined_patterns": [f"quarantined_{exp_id.lower()}"]
            }
            db_engine.record_failure_lesson(fail_record)

        return {
            "cycle_id": cycle_id,
            "timestamp": timestamp,
            "experiment_id": exp_id,
            "hypothesis": hypothesis,
            "critic_audit": critic_audit,
            "walk_forward_evaluation": wf_eval,
            "promotion_decision": promotion_decision,
            "final_status": final_status,
            "summary_ar": f"دورة بحثية مكتملة [{exp_id}]: {promotion_decision.get('verdict_ar', final_status)}"
        }

    @classmethod
    def get_recent_experiments(cls, limit: int = 10) -> List[Dict[str, Any]]:
        """Returns recent research experiments from SQLite journal."""
        return db_engine.get_recent_experiments(limit=limit)

    @classmethod
    def get_failure_memory(cls, limit: int = 20) -> List[Dict[str, Any]]:
        """Returns episodic failure lessons and quarantined patterns."""
        return db_engine.get_failure_memory(limit=limit)
