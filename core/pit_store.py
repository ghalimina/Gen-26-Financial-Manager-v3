#!/usr/bin/env python3
# =============================================================================
# core/pit_store.py — GEN-26 Point-in-Time (PIT) Data Store & Historical Universe
# Strictly enforces Point-in-Time discipline, tracking publication timestamps
# and historical tradable eligibility to eliminate look-ahead leakage.
# =============================================================================

import os
import json
import datetime
from typing import Dict, List, Any, Optional
import pandas as pd


class PointInTimeRecord:
    def __init__(
        self,
        entity_id: str,
        metric_name: str,
        value: Any,
        period_end: str,
        publication_time: str,
        available_time: Optional[str] = None,
        source: str = "EGX_DISCLOSURE",
        version: str = "1.0"
    ):
        self.entity_id = entity_id
        self.metric_name = metric_name
        self.value = value
        self.period_end = period_end
        self.publication_time = publication_time
        self.available_time = available_time or publication_time
        self.source = source
        self.version = version

    def is_known_at(self, query_time: str) -> bool:
        """Returns True if this record was publicly known and available at or before query_time."""
        return self.available_time <= query_time

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "metric_name": self.metric_name,
            "value": self.value,
            "period_end": self.period_end,
            "publication_time": self.publication_time,
            "available_time": self.available_time,
            "source": self.source,
            "version": self.version
        }


class PointInTimeDataStore:
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path
        self.records: List[PointInTimeRecord] = []
        if storage_path and os.path.exists(storage_path):
            self.load()

    def add_record(
        self,
        entity_id: str,
        metric_name: str,
        value: Any,
        period_end: str,
        publication_time: str,
        available_time: Optional[str] = None,
        source: str = "EGX_DISCLOSURE",
        version: str = "1.0"
    ) -> PointInTimeRecord:
        record = PointInTimeRecord(
            entity_id=entity_id,
            metric_name=metric_name,
            value=value,
            period_end=period_end,
            publication_time=publication_time,
            available_time=available_time,
            source=source,
            version=version
        )
        self.records.append(record)
        return record

    def get_as_of(self, entity_id: str, metric_name: str, as_of_time: str) -> Optional[Any]:
        """
        Retrieves the latest value of a metric known STRICTLY at or before as_of_time.
        Prevents lookahead leakage by filtering out anything published after as_of_time.
        """
        valid_records = [
            r for r in self.records
            if r.entity_id == entity_id and r.metric_name == metric_name and r.is_known_at(as_of_time)
        ]
        if not valid_records:
            return None
        # Sort by publication_time ascending, take the most recent available
        valid_records.sort(key=lambda r: r.available_time)
        return valid_records[-1].value

    def get_full_state_as_of(self, entity_id: str, as_of_time: str) -> Dict[str, Any]:
        """Reconstructs the full known feature/metric snapshot for an entity as of a specific timestamp."""
        state = {}
        for r in self.records:
            if r.entity_id == entity_id and r.is_known_at(as_of_time):
                state[r.metric_name] = r.value
        return state

    def save(self, path: Optional[str] = None) -> bool:
        p = path or self.storage_path
        if not p:
            return False
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump([r.to_dict() for r in self.records], f, ensure_ascii=False, indent=2)
        return True

    def load(self, path: Optional[str] = None) -> bool:
        p = path or self.storage_path
        if not p or not os.path.exists(p):
            return False
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.records = [PointInTimeRecord(**d) for d in data]
        return True


class HistoricalTradableUniverse:
    """
    Manages the universe of eligible stocks across historical dates.
    Tracks listing status, suspension status, and trading eligibility to eliminate survivorship bias.
    Delegates to HistoricalUniverseManager for full point-in-time accuracy.
    """
    @classmethod
    def get_core_universe(cls) -> List[str]:
        from core.historical_universe_manager import HistoricalUniverseManager
        reg = HistoricalUniverseManager.load_registry()
        return sorted(list(reg.keys()))

    @property
    def CORE_EGX_UNIVERSE(self) -> List[str]:
        return self.get_core_universe()

    DEFAULT_DELISTING_CAPITAL_LOSS_PCT = -100.0  # Full capital loss assumption per quant guidelines

    def __init__(self):
        # Maps date -> set of tradable tickers or custom corporate actions
        self.universe_events: List[Dict[str, Any]] = []

    def register_corporate_action(
        self,
        ticker: str,
        action_type: str,
        effective_date: str,
        announcement_date: str,
        details: Dict[str, Any]
    ):
        """
        Records a corporate action (SPLIT, DIVIDEND, BONUS_SHARES, SUSPENSION, DELISTING).
        """
        self.universe_events.append({
            "ticker": ticker.upper(),
            "action_type": action_type.upper(),
            "effective_date": effective_date,
            "announcement_date": announcement_date,
            "details": details or {}
        })

    def is_tradable_on(self, ticker: str, date: str) -> bool:
        """
        Returns True if the ticker was active and tradable on the given date (Survivorship-free).
        Checks registered dynamic actions (e.g. temporary suspensions, emergency delistings)
        and historical Point-in-Time registry.
        """
        sym = ticker.upper().strip()
        d_str = str(date)[:10]

        # 1. Evaluate registered instance events (suspensions & delistings)
        for ev in self.universe_events:
            if ev.get("ticker") == sym:
                act = ev.get("action_type")
                eff = str(ev.get("effective_date", ""))[:10]
                details = ev.get("details", {})
                if act == "SUSPENSION":
                    end_d = str(details.get("end_date") or details.get("suspension_end") or "9999-12-31")[:10]
                    if eff <= d_str <= end_d:
                        return False
                elif act == "DELISTING":
                    if d_str >= eff:
                        return False

        # 2. Query centralized Point-in-Time Universe Manager
        from core.historical_universe_manager import HistoricalUniverseManager
        return HistoricalUniverseManager.is_tradable_on(sym, d_str)

    def get_tradable_universe(self, date: str) -> List[str]:
        """Returns the list of all tradable tickers on a specific date."""
        from core.historical_universe_manager import HistoricalUniverseManager
        base_universe = HistoricalUniverseManager.get_tradable_universe(date)
        return [t for t in base_universe if self.is_tradable_on(t, date)]

    def get_delisting_terminal_loss_pct(self, ticker: str) -> float:
        """
        Returns terminal capital loss percentage for delisted equities to correct survivorship bias.
        Defaults to -100.0% (total wipeout) unless tender offer / MBO terms exist.
        """
        sym = ticker.upper().strip()
        for ev in self.universe_events:
            if ev.get("ticker") == sym and ev.get("action_type") == "DELISTING":
                return float(ev.get("details", {}).get("capital_loss_pct", self.DEFAULT_DELISTING_CAPITAL_LOSS_PCT))
        return self.DEFAULT_DELISTING_CAPITAL_LOSS_PCT
