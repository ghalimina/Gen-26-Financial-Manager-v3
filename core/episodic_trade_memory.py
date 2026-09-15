#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# core/episodic_trade_memory.py — Hierarchical Episodic Memory & Case-Based Retrieval
# Stores trade experiences, forensic post-mortems, and vector representations.
# Retrieves similar historical failures via Cosine Similarity to prevent repeated mistakes.
# =============================================================================

import os
import sys
import math
import json
import logging
from typing import Dict, List, Any, Optional, Tuple

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.database_engine import db_engine
from core.trade_post_mortem_engine import PostMortemReport

logger = logging.getLogger("GEN26.EpisodicTradeMemory")


class EpisodicTradeMemory:
    """
    Episodic Memory Engine for Self-Improving Trading Agents.
    Encodes trade contexts, computes similarity across historical failure cases,
    and applies proactive safety vetoes to prevent repeating known past mistakes.
    """

    FEATURE_KEYS = ["vol_ratio", "cmf", "mfi", "adx", "spread_pct"]

    @classmethod
    def encode_feature_vector(cls, features: Dict[str, Any]) -> List[float]:
        """
        Normalizes continuous features into a compact vector representation:
        - vol_ratio: normalized around 1.0 (clamped [0, 3])
        - cmf: [-1.0, 1.0]
        - mfi: [0, 100] -> scaled to [0, 1]
        - adx: [0, 100] -> scaled to [0, 1]
        - spread_pct: scaled around 0.5% (clamped [0, 5%])
        """
        v_vol = min(max(float(features.get("volume_ratio", 1.0)) / 2.0, 0.0), 1.5)
        v_cmf = min(max(float(features.get("cmf", 0.0)), -1.0), 1.0)
        v_mfi = min(max(float(features.get("mfi", 50.0)) / 100.0, 0.0), 1.0)
        v_adx = min(max(float(features.get("adx", 25.0)) / 100.0, 0.0), 1.0)
        v_spread = min(max(float(features.get("spread_pct", 0.30)) / 2.0, 0.0), 1.5)

        return [v_vol, v_cmf, v_mfi, v_adx, v_spread]

    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Computes cosine similarity between two feature vectors."""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        dot = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        if norm1 <= 1e-9 or norm2 <= 1e-9:
            return 0.0
        return dot / (norm1 * norm2)

    @classmethod
    def record_post_mortem(cls, report: PostMortemReport, regime: str = "BULL_TREND") -> bool:
        """Persists a forensic post-mortem report into SQLite episodic memory."""
        fail_dict = {
            "failure_id": report.report_id,
            "regime": regime,
            "failed_hypothesis": f"{report.ticker} Long Trade [{report.failure_category}]",
            "root_cause_analysis": f"Realized PnL: {report.realized_pnl_pct}%. {report.diagnosis_ar}",
            "lesson_learned_ar": report.actionable_rule_ar,
            "quarantined_patterns": [report.quarantine_tag, report.actionable_code_filter]
        }
        return db_engine.record_failure_lesson(fail_dict)

    @classmethod
    def retrieve_similar_failures(
        cls,
        current_features: Dict[str, Any],
        regime: Optional[str] = None,
        top_k: int = 5,
        min_similarity: float = 0.70
    ) -> List[Dict[str, Any]]:
        """
        Scans SQLite failure memory and returns top-k most similar failure cases.
        """
        raw_failures = db_engine.get_failure_memory(limit=50, regime=regime)
        query_vec = cls.encode_feature_vector(current_features)

        scored = []
        for fail in raw_failures:
            # Reconstruct feature vector from stored patterns or fallback defaults
            q_pats = fail.get("quarantined_patterns", [])
            if isinstance(q_pats, str):
                try:
                    q_pats = json.loads(q_pats)
                except Exception:
                    q_pats = [q_pats]

            # Synthesize approximate vector based on root cause tags
            root_cause = str(fail.get("root_cause_analysis", ""))
            sample_feats = {
                "volume_ratio": 0.60 if "low_vol" in str(q_pats) or "CMF" in root_cause else 1.10,
                "cmf": -0.15 if "CMF" in root_cause or "سالب" in root_cause else 0.10,
                "mfi": 82.0 if "exhaustion" in str(q_pats) or "MFI" in root_cause else 48.0,
                "adx": 16.0 if "tight_stop" in str(q_pats) or "ADX" in root_cause else 28.0,
                "spread_pct": 1.40 if "spread" in str(q_pats) else 0.25
            }
            cand_vec = cls.encode_feature_vector(sample_feats)
            sim = cls.cosine_similarity(query_vec, cand_vec)

            if sim >= min_similarity:
                scored.append({
                    "failure_id": fail.get("failure_id"),
                    "similarity": round(sim, 4),
                    "regime": fail.get("regime"),
                    "lesson_learned_ar": fail.get("lesson_learned_ar"),
                    "quarantined_patterns": q_pats,
                    "root_cause": root_cause
                })

        scored.sort(key=lambda x: x["similarity"], reverse=True)
        return scored[:top_k]

    @classmethod
    def evaluate_trade_candidate(
        cls,
        ticker: str,
        current_features: Dict[str, Any],
        regime: str = "BULL_TREND"
    ) -> Dict[str, Any]:
        """
        Screening guard: Checks if proposed trade context closely matches a historical failure pattern.
        Returns safety verdict, confidence penalty, and arabic advisory notes.
        """
        similar_fails = cls.retrieve_similar_failures(
            current_features=current_features,
            regime=regime,
            top_k=3,
            min_similarity=0.82
        )

        if not similar_fails:
            return {
                "safe_to_trade": True,
                "confidence_penalty": 0.0,
                "status_ar": "سياق تداول آمن — لا توجد إخفاقات سابقة متطابقة",
                "matched_failures_count": 0,
                "top_similarity": 0.0
            }

        top_match = similar_fails[0]
        top_sim = top_match["similarity"]

        # If extremely high similarity (> 90%), veto trade
        if top_sim >= 0.90:
            return {
                "safe_to_trade": False,
                "confidence_penalty": 0.50,
                "status_ar": f"حظر وقائي: تطابق بنسبة {top_sim*100:.1f}% مع سابقة فشل [{top_match['failure_id']}]. {top_match['lesson_learned_ar']}",
                "matched_failures_count": len(similar_fails),
                "top_similarity": top_sim,
                "veto_reason": top_match["lesson_learned_ar"]
            }

        # Moderate similarity (82% - 90%): Apply haircut penalty
        return {
            "safe_to_trade": True,
            "confidence_penalty": round((top_sim - 0.80) * 1.5, 3),
            "status_ar": f"تحذير سياقي: تشابه جزئي ({top_sim*100:.1f}%) مع إخفاق سابق. تم تطبيق خصم احترازي على الثقة.",
            "matched_failures_count": len(similar_fails),
            "top_similarity": top_sim
        }
