#!/usr/bin/env python3
import pytest
from core.multi_agent_debate_system import MultiAgentDebateSystem, BullThesisAgent, BearThesisAgent, ChiefRiskArbiter


def test_debate_conduct_and_synthesis():
    debate = MultiAgentDebateSystem.conduct_debate("COMI.CA", current_price=141.0)
    assert "bull_report" in debate
    assert "bear_report" in debate
    assert "arbitration" in debate
    assert "investment_memo_ar" in debate

    arb = debate["arbitration"]
    assert "consensus_verdict" in arb
    assert "arbiter_position_multiplier" in arb
    assert arb["arbiter_position_multiplier"] >= 0.0
    assert len(arb["debate_dialogue"]) >= 3


def test_debate_resolution_branches():
    bull = {
        "agent": "BullThesisAgent",
        "conviction_score": 85.0,
        "thesis_summary_ar": "أطروحة صعود قوية",
        "key_catalysts": ["عائد مئيني مرتفع", "تدفق مؤسسي"]
    }
    bear = {
        "agent": "BearThesisAgent",
        "risk_severity_score": 35.0,
        "antithesis_summary_ar": "مخاطر طفيفة",
        "key_vulnerabilities": ["مقاومة قريبة"]
    }
    strong_buy_res = ChiefRiskArbiter.arbitrate("TEST.CA", 100.0, bull, bear)
    assert strong_buy_res["consensus_verdict"] == "CONFIRM_STRONG_BUY"
    assert strong_buy_res["arbiter_position_multiplier"] == 1.25

    # Reverse: Severe risks
    bear_severe = {
        "agent": "BearThesisAgent",
        "risk_severity_score": 90.0,
        "antithesis_summary_ar": "مخاطر هيكلية جسيمة",
        "key_vulnerabilities": ["ديون ضخمة", "علاوة تقييم مفرطة"]
    }
    reject_res = ChiefRiskArbiter.arbitrate("TEST.CA", 100.0, bull, bear_severe)
    assert reject_res["consensus_verdict"] == "REJECT_RISK_DOMINANT"
    assert reject_res["arbiter_position_multiplier"] == 0.00
