#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# core/session_manager.py — GEN-26 Session Lifecycle and Immutability Manager
# =============================================================================

import os
import json
import datetime
from typing import Dict, List, Any, Optional

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS_DIR = os.path.join(WORKSPACE, "reports")
SESSIONS_FILE = os.path.join(REPORTS_DIR, "authoritative_paper_sessions.json")


class SessionManager:
    """Manages paper trading session records and prevents duplicate runs."""

    @classmethod
    def _load(cls) -> List[Dict[str, Any]]:
        if os.path.exists(SESSIONS_FILE):
            try:
                with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    @classmethod
    def _save(cls, sessions: List[Dict[str, Any]]) -> None:
        os.makedirs(REPORTS_DIR, exist_ok=True)
        with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(sessions, f, ensure_ascii=False, indent=2)

    @classmethod
    def start_session(cls, date_str: str, bypass_weekend: bool = False) -> Optional[str]:
        sessions = cls._load()
        for s in sessions:
            if s.get("date") == date_str and s.get("status") in ["COMPLETED", "ACTIVE"]:
                return None
        sess_id = f"SESS_{date_str.replace('-', '')}_{len(sessions)+1:03d}"
        new_sess = {
            "session_id": sess_id,
            "date": date_str,
            "status": "ACTIVE",
            "start_time": datetime.datetime.now().isoformat()
        }
        sessions.append(new_sess)
        cls._save(sessions)
        return sess_id

    @classmethod
    def complete_session(cls, session_id: str, summary: Optional[Dict[str, Any]] = None, data_status: Optional[str] = None, **kwargs) -> bool:
        sessions = cls._load()
        for s in sessions:
            if s.get("session_id") == session_id:
                s["status"] = "COMPLETED"
                s["completed_at"] = datetime.datetime.now().isoformat()
                if data_status:
                    s["data_status"] = data_status
                if summary:
                    s["summary"] = summary
                cls._save(sessions)
                return True
        return False

    @classmethod
    def fail_session(cls, session_id: str, error_msg: str = "", reason: Optional[str] = None, **kwargs) -> bool:
        sessions = cls._load()
        msg = reason or error_msg or "Unknown error"
        for s in sessions:
            if s.get("session_id") == session_id:
                s["status"] = "FAILED"
                s["error"] = msg
                s["failed_at"] = datetime.datetime.now().isoformat()
                cls._save(sessions)
                return True
        return False

    @classmethod
    def get_valid_days(cls) -> int:
        sessions = cls._load()
        return sum(1 for s in sessions if s.get("status") == "COMPLETED")
