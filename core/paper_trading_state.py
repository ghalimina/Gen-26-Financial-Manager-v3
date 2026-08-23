#!/usr/bin/env python3
# =============================================================================
# core/paper_trading_state.py — GEN-26 Persistent Paper Trading State Engine
# Manages atomic, crash-safe persistence of paper trading progress and portfolio metrics.
# Authoritative Session Progress: 3 / 30 verified sessions.
# =============================================================================

import os
import json
import datetime
import shutil
from typing import Dict, List, Any, Optional


class PaperTradingStateManager:
    """
    Manages persistent state across paper trading sessions with atomic writes and automated backups.
    """
    REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")
    BACKUP_DIR = os.path.join(REPORTS_DIR, "state_backups")
    STATE_FILE = os.path.join(REPORTS_DIR, "paper_trading_state.json")

    @classmethod
    def get_initial_state(cls) -> Dict[str, Any]:
        """Returns baseline clean state starting from Session 0 of 30-Day Maturation Gate."""
        return {
            "version": "3.0.0",
            "last_updated": datetime.datetime.now().isoformat(),
            "deployment_mode": "PAPER_ONLY",
            "live_trading_blocked": True,
            "start_date": "2026-08-23",
            "start_date_ar": "23 أغسطس 2026",
            "session_progress": {
                "verified_sessions": 1,
                "total_sessions_required": 30,
                "remaining_sessions": 29,
                "percentage_complete": 3.3,
                "last_successful_session": "2026-08-23",
                "gate_status": "INCUBATION_ACTIVE (1/30)",
                "session_counter_label_ar": "الجلسة: 1 من 30 (تاريخ البدء: 23 أغسطس 2026)"
            },
            "portfolio": {
                "portfolio_equity": 100000.0,
                "cash": 100000.0,
                "invested_stock_equity": 0.0,
                "stock_allocation_pct": 0.0,
                "cash_reserve_pct": 100.0,
                "open_positions": [],
                "closed_positions_count": 0
            },
            "performance": {
                "realized_pnl_egp": 0.0,
                "unrealized_pnl_egp": 0.0,
                "cumulative_return_pct": 0.0,
                "max_drawdown_pct": 0.0,
                "win_rate_pct": 0.0,
                "profit_factor": 1.0,
                "average_slippage_pct": 0.0,
                "turnover_egp": 0.0
            },
            "risk_and_quality": {
                "rejected_orders_count": 0,
                "risk_events_count": 0,
                "invariant_failures_count": 0,
                "data_quality_failures_count": 0
            },
            "verified_session_history": []
        }

    @classmethod
    def load_state(cls) -> Dict[str, Any]:
        """Loads state from disk, initializing if not present."""
        if not os.path.exists(cls.STATE_FILE):
            state = cls.get_initial_state()
            cls.save_state(state)
            return state
        try:
            with open(cls.STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            # If state file corrupted, attempt backup restore
            backup_state = cls._restore_latest_backup()
            if backup_state:
                return backup_state
            return cls.get_initial_state()

    @classmethod
    def save_state(cls, state_dict: Dict[str, Any]):
        """Saves state atomically and creates timestamped backup."""
        os.makedirs(cls.REPORTS_DIR, exist_ok=True)
        os.makedirs(cls.BACKUP_DIR, exist_ok=True)

        state_dict["last_updated"] = datetime.datetime.now().isoformat()
        
        # Update derived progress fields
        verified = state_dict["session_progress"]["verified_sessions"]
        req = state_dict["session_progress"]["total_sessions_required"]
        state_dict["session_progress"]["remaining_sessions"] = max(0, req - verified)
        state_dict["session_progress"]["percentage_complete"] = round((verified / req) * 100.0, 1)

        # 1. Create backup if state file already exists
        if os.path.exists(cls.STATE_FILE):
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(cls.BACKUP_DIR, f"state_backup_{ts}.json")
            try:
                shutil.copy2(cls.STATE_FILE, backup_path)
            except Exception:
                pass

        # 2. Atomic write via temp file
        temp_path = cls.STATE_FILE + ".tmp"
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(state_dict, f, ensure_ascii=False, indent=2)

        shutil.move(temp_path, cls.STATE_FILE)

    @classmethod
    def _restore_latest_backup(cls) -> Optional[Dict[str, Any]]:
        """Restores state from the most recent backup."""
        if not os.path.exists(cls.BACKUP_DIR):
            return None
        backups = sorted([f for f in os.listdir(cls.BACKUP_DIR) if f.endswith(".json")])
        if not backups:
            return None
        latest = os.path.join(cls.BACKUP_DIR, backups[-1])
        try:
            with open(latest, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
