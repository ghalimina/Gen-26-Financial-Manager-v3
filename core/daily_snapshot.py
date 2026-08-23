#!/usr/bin/env python3
# =============================================================================
# core/daily_snapshot.py — GEN-26 Daily Immutable Market Snapshot Engine
# Generates and archives complete daily market snapshots with SHA256 integrity hashing.
# =============================================================================

import os
import json
import datetime
import hashlib
from typing import Dict, List, Any, Optional


class DailySnapshotArchive:
    """
    Generates immutable daily JSON snapshots of the entire GEN-26 market state.
    """
    DAILY_REPORTS_DIR = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "reports", "daily"
    )

    @classmethod
    def save_daily_snapshot(
        cls,
        market_date: str,
        universe_coverage: Dict[str, Any],
        rankings: List[Dict[str, Any]],
        portfolio_state: Dict[str, Any],
        risk_state: Dict[str, Any],
        paper_trades: List[Dict[str, Any]],
        data_provider: str = "Yahoo Finance + Local PIT Store"
    ) -> str:
        """
        Creates and saves an immutable daily market snapshot. Returns filepath.
        """
        os.makedirs(cls.DAILY_REPORTS_DIR, exist_ok=True)
        filepath = os.path.join(cls.DAILY_REPORTS_DIR, f"{market_date}.json")

        payload = {
            "snapshot_metadata": {
                "market_date": market_date,
                "timestamp": datetime.datetime.now().isoformat(),
                "data_provider": data_provider,
                "engine_version": "3.0.0",
                "mode": "PAPER_ONLY"
            },
            "universe_coverage": universe_coverage,
            "rankings": rankings,
            "portfolio": portfolio_state,
            "risk_state": risk_state,
            "paper_trades": paper_trades
        }

        # Calculate SHA256 Integrity Hash
        serialized = json.dumps(payload, sort_keys=True)
        payload["snapshot_metadata"]["sha256_hash"] = hashlib.sha256(serialized.encode("utf-8")).hexdigest()

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        return filepath
