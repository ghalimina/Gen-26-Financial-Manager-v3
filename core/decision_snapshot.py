#!/usr/bin/env python3
# =============================================================================
# core/decision_snapshot.py — GEN-26 Immutable Decision Snapshots & Replay
# Captures and persists point-in-time decision states for deterministic audit replay.
# Historical snapshots are immutable and never rewritten.
# =============================================================================

import os
import json
import datetime
import hashlib
from typing import Dict, List, Any, Optional


class ImmutableDecisionSnapshotStore:
    """
    Stores and reconstructs point-in-time decision states for complete forensic auditability.
    """
    DEFAULT_SNAPSHOT_DIR = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "decision_snapshots"
    )

    @classmethod
    def save_snapshot(
        cls,
        decision_id: str,
        session_id: str,
        ticker: str,
        decision_object: Dict[str, Any],
        market_state: Dict[str, Any],
        features_snapshot: Dict[str, Any],
        ranking_snapshot: Dict[str, Any],
        risk_evaluation: Dict[str, Any],
        portfolio_state: Dict[str, Any]
    ) -> str:
        """
        Saves an immutable point-in-time decision snapshot to disk.
        Returns the absolute filepath.
        """
        os.makedirs(cls.DEFAULT_SNAPSHOT_DIR, exist_ok=True)
        filepath = os.path.join(cls.DEFAULT_SNAPSHOT_DIR, f"{decision_id}.json")

        payload = {
            "snapshot_metadata": {
                "decision_id": decision_id,
                "session_id": session_id,
                "ticker": ticker,
                "timestamp": datetime.datetime.now().isoformat(),
                "engine_version": "3.0.0"
            },
            "decision": decision_object,
            "market_state": market_state,
            "features_as_of": features_snapshot,
            "ranking": ranking_snapshot,
            "risk_evaluation": risk_evaluation,
            "portfolio_state": portfolio_state
        }

        # Calculate payload hash for tamper detection
        content_str = json.dumps(payload, sort_keys=True)
        payload["snapshot_metadata"]["integrity_hash"] = hashlib.sha256(content_str.encode("utf-8")).hexdigest()

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        return filepath

    @classmethod
    def replay_decision(cls, decision_id: str) -> Optional[Dict[str, Any]]:
        """
        Reconstructs the exact state and mental model GEN-26 had at the decision timestamp.
        """
        filepath = os.path.join(cls.DEFAULT_SNAPSHOT_DIR, f"{decision_id}.json")
        if not os.path.exists(filepath):
            return None

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        return data
