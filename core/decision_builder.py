#!/usr/bin/env python3
# =============================================================================
# core/decision_builder.py — GEN-26 Decision Builder, Explainability & Replay
# Single Source of Truth (SSoT) decision generator, explainable reasoning (Why/Why Not),
# Global Kill Switch, and Decision Replay audit engine.
# =============================================================================

import os
import json
import datetime
import hashlib
from typing import Dict, List, Any, Optional


class DecisionReplayEngine:
    """
    Persists complete state snapshots for all generated decisions to enable
    deterministic reconstruction and forensic auditing of any historic decision.
    """
    DEFAULT_SNAPSHOT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "decision_snapshots")

    @classmethod
    def save_snapshot(cls, decision_object: Dict[str, Any], full_state_snapshot: Dict[str, Any]):
        """Persists decision and input state to disk."""
        os.makedirs(cls.DEFAULT_SNAPSHOT_DIR, exist_ok=True)
        dec_id = decision_object["decision_id"]
        path = os.path.join(cls.DEFAULT_SNAPSHOT_DIR, f"{dec_id}.json")
        payload = {
            "decision": decision_object,
            "state_snapshot": full_state_snapshot,
            "saved_at": datetime.datetime.now().isoformat()
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    @classmethod
    def replay_decision(cls, decision_id: str) -> Optional[Dict[str, Any]]:
        """Reconstructs the exact state and rationale for a given decision ID."""
        path = os.path.join(cls.DEFAULT_SNAPSHOT_DIR, f"{decision_id}.json")
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)


class RiskReasonCode:
    CASH_SOLVENCY_VIOLATION = "CASH_SOLVENCY_VIOLATION"
    ALLOCATION_CAP_EXCEEDED = "ALLOCATION_CAP_EXCEEDED"
    PULLBACK_INVARIANT_VIOLATION = "PULLBACK_INVARIANT_VIOLATION"
    LIQUIDITY_INSUFFICIENT = "LIQUIDITY_INSUFFICIENT"
    ACCOUNTING_HIGH_RISK = "ACCOUNTING_HIGH_RISK"
    DATA_QUALITY_FAIL = "DATA_QUALITY_FAIL"
    GLOBAL_KILL_SWITCH = "GLOBAL_KILL_SWITCH"


class CanonicalDecisionBuilder:
    """
    Builds canonical decision objects adhering to all Frozen Core risk gates.
    """

    # Global Kill Switch Flag
    KILL_SWITCH_ACTIVE = False

    @classmethod
    def set_kill_switch(cls, active: bool):
        cls.KILL_SWITCH_ACTIVE = active

    @classmethod
    def build_decision(
        cls,
        ticker: str,
        company_name: str,
        current_price: float,
        entry_price: float,
        stop_price: float,
        target_price: float,
        alpha_data: Dict[str, Any],
        quality_data: Dict[str, Any],
        valuation_data: Dict[str, Any],
        liquidity_data: Dict[str, Any],
        data_health: str,
        available_free_cash: float,
        current_stock_equity: float,
        total_portfolio_equity: float,
        existing_position_qty: int = 0
    ) -> Dict[str, Any]:
        """
        Generates a canonical decision object with explainable rationale and risk reason codes.
        """
        timestamp = datetime.datetime.now().isoformat()
        cp = max(float(current_price), 0.01)
        ep = max(float(entry_price), 0.01)
        stop = max(float(stop_price), 0.0)
        target = max(float(target_price), 0.0)

        # 1. Deterministic Decision ID Hash
        hash_seed = f"{ticker}_{timestamp[:10]}_{cp}_{ep}_{alpha_data.get('alpha_score', 0)}"
        dec_hash = hashlib.md5(hash_seed.encode('utf-8')).hexdigest()[:8]
        decision_id = f"{ticker}_{timestamp[:10]}_{dec_hash}"

        # 2. Risk Gate Evaluations
        cash_gate = "PASS"
        alloc_gate = "PASS"
        pullback_gate = "PASS"
        quality_gate = "PASS"

        rejection_reasons = []
        risk_reason_codes = []
        positive_reasons = []
        negative_reasons = []

        # Global Kill Switch Check
        if cls.KILL_SWITCH_ACTIVE:
            status = "BLOCKED"
            action = "NO_TRADE"
            rejection_reasons.append("GLOBAL_KILL_SWITCH_ACTIVE")
            risk_reason_codes.append(RiskReasonCode.GLOBAL_KILL_SWITCH)

        # Data Quality Gate
        elif data_health == "FAIL":
            quality_gate = "FAIL"
            status = "BLOCKED"
            action = "NO_TRADE"
            rejection_reasons.append("DATA_QUALITY_FAILURE (Fail-Closed)")
            risk_reason_codes.append(RiskReasonCode.DATA_QUALITY_FAIL)

        # Pullback Limit Invariant Check (ep < cp)
        elif ep >= cp:
            pullback_gate = "FAIL"
            status = "BLOCKED"
            action = "NO_TRADE"
            rejection_reasons.append("INVALID_PULLBACK_ENTRY (Entry >= Current Price)")
            risk_reason_codes.append(RiskReasonCode.PULLBACK_INVARIANT_VIOLATION)

        else:
            # 65% Portfolio Allocation Cap Gate
            invested_weight = (current_stock_equity / total_portfolio_equity) if total_portfolio_equity > 0 else 0.0
            if invested_weight > 0.65:
                alloc_gate = "FAIL"
                status = "BLOCKED"
                action = "NO_TRADE"
                rejection_reasons.append("PORTFOLIO_OVER_CAP (>65% Stock Equity Ceiling)")
                risk_reason_codes.append(RiskReasonCode.ALLOCATION_CAP_EXCEEDED)
                negative_reasons.append(f"سقف الاستثمار مكتمل ({invested_weight*100:.1f}%)")

            # Cash Solvency Gate
            target_cost = total_portfolio_equity * 0.10  # 10% max allocation
            suggested_shares = int(target_cost // ep)
            actual_order_cost = suggested_shares * ep

            if actual_order_cost > available_free_cash:
                cash_gate = "FAIL"
                status = "PENDING"
                action = "WAIT FOR PULLBACK"
                rejection_reasons.append("INSUFFICIENT_FREE_CASH (Pending Liquidation)")
                risk_reason_codes.append(RiskReasonCode.CASH_SOLVENCY_VIOLATION)
                negative_reasons.append("السيولة النقدية المتاحة حالياً أقل من تكلفة الأمر")
            else:
                status = "APPROVED"
                action = "BUY LIMIT (PULLBACK)" if existing_position_qty == 0 else "HOLD"

        # Unified Risk Score Calculation (0-100, where higher is safer)
        base_risk_score = 75.0
        if quality_data.get("accounting_risk") == "HIGH":
            base_risk_score -= 25.0
            risk_reason_codes.append(RiskReasonCode.ACCOUNTING_HIGH_RISK)
        if liquidity_data.get("liquidity_score", 50.0) < 50.0:
            base_risk_score -= 15.0
            risk_reason_codes.append(RiskReasonCode.LIQUIDITY_INSUFFICIENT)
        if alloc_gate == "FAIL":
            base_risk_score -= 20.0
        if cash_gate == "FAIL":
            base_risk_score -= 15.0
        unified_risk_score = round(max(10.0, min(100.0, base_risk_score)), 1)

        # Build Explainability Details
        alpha_score = alpha_data.get("alpha_score", 50.0)
        q_score = quality_data.get("quality_score", 50.0)
        val_score = valuation_data.get("valuation_score", 50.0)
        liq_score = liquidity_data.get("liquidity_score", 50.0)

        if alpha_score >= 70.0:
            positive_reasons.append(f"ألفا استثمارية قوية ({alpha_score}/100)")
        if q_score >= 75.0:
            positive_reasons.append(f"جودة تشغيلية ومالية ممتازة ({q_score}/100)")
        if val_score >= 70.0:
            positive_reasons.append(f"تقييم مغري ومضاعفات عادلة ({val_score}/100)")
        if ep < cp:
            dist_pct = ((cp - ep) / cp) * 100.0
            positive_reasons.append(f"دخول تراجعي آمن بخصم {dist_pct:.1f}% عن سعر السوق")

        if quality_data.get("accounting_risk") == "HIGH":
            negative_reasons.append("مخاطر محاسبية مرتفعة في جودة التدفقات النقدية")
        if liq_score < 50.0:
            negative_reasons.append("سيولة متوسطة تتطلب الحذر في حجم الأمر")

        reason_str = " | ".join(rejection_reasons) if rejection_reasons else (" | ".join(positive_reasons) if positive_reasons else "APPROVED_FOR_EXECUTION")

        decision_obj = {
            "decision_id": decision_id,
            "timestamp": timestamp,
            "ticker": ticker,
            "name": company_name,
            "market_data": {
                "current_price": round(cp, 2),
                "price_timestamp": timestamp
            },
            "portfolio": {
                "equity": round(total_portfolio_equity, 2),
                "cash": round(available_free_cash, 2),
                "allocation_pct": 10.0,
                "position_qty": existing_position_qty
            },
            "signal": {
                "action": action,
                "status": status,
                "reason": reason_str,
                "confidence_pct": alpha_data.get("confidence_pct", 75.0)
            },
            "entry": {
                "price": round(ep, 2),
                "type": "PULLBACK_LIMIT",
                "distance_pct": round(((cp - ep) / cp) * 100.0, 2)
            },
            "risk": {
                "stop": round(stop, 2),
                "target": round(target, 2),
                "risk_score": unified_risk_score,
                "risk_reason_codes": risk_reason_codes,
                "risk_reward": f"1:{round((target - cp) / max(cp - stop, 0.01), 1)}" if stop > 0 and target > cp else "1:2.0"
            },
            "explainability": {
                "why": positive_reasons,
                "why_not": negative_reasons,
                "alpha_score": alpha_score,
                "quality_score": q_score,
                "valuation_score": val_score,
                "liquidity_score": liq_score,
                "risk_score": unified_risk_score,
                "accounting_risk": quality_data.get("accounting_risk", "LOW"),
                "risk_reason_codes": risk_reason_codes
            },
            "gates": {
                "cash_gate": cash_gate,
                "allocation_gate": alloc_gate,
                "pullback_gate": pullback_gate,
                "quality_gate": quality_gate
            }
        }

        # Save Snapshot for Decision Replay
        state_snap = {
            "alpha": alpha_data,
            "quality": quality_data,
            "valuation": valuation_data,
            "liquidity": liquidity_data,
            "portfolio_equity": total_portfolio_equity,
            "cash": available_free_cash
        }
        DecisionReplayEngine.save_snapshot(decision_obj, state_snap)

        return decision_obj


Tuple_Dict = Dict[str, Any]
