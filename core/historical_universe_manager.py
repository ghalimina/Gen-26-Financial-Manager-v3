#!/usr/bin/env python3
# =============================================================================
# core/historical_universe_manager.py — GEN-26 Point-in-Time (PIT) Universe Engine
# Manages historical tradable universe, listing/delisting dates, ticker transitions,
# and temporary trading suspensions to completely eliminate Survivorship Bias.
# =============================================================================

import os
import sys
import json
import sqlite3
import datetime
from typing import Dict, List, Any, Optional

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

DATA_DIR = os.path.join(WORKSPACE, "data")
DB_PATH = os.path.join(DATA_DIR, "gen26_production.db")
REGISTRY_JSON = os.path.join(DATA_DIR, "historical_universe_registry.json")


class HistoricalUniverseManager:
    """
    Point-in-Time Universe Authority for the Egyptian Exchange (EGX).
    Ensures that for any historical date t, the eligible tradable universe contains ONLY
    equities that were actively listed, not delisted, and not suspended on date t.
    """

    _registry_cache: Optional[Dict[str, Dict[str, Any]]] = None

    @classmethod
    def init_db(cls):
        """Initializes historical_universe_registry table in gen26_production.db."""
        os.makedirs(DATA_DIR, exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS historical_universe_registry (
                ticker TEXT PRIMARY KEY,
                company_name TEXT NOT NULL,
                listing_date TEXT NOT NULL,
                delisting_date TEXT NOT NULL,
                suspension_start TEXT,
                suspension_end TEXT,
                ticker_old TEXT,
                ticker_new TEXT,
                sector TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    @classmethod
    def load_registry(cls, force_reload: bool = False) -> Dict[str, Dict[str, Any]]:
        """Loads all historical stock records from SQLite or JSON cache."""
        if cls._registry_cache is not None and not force_reload:
            return cls._registry_cache

        cls.init_db()
        records: Dict[str, Dict[str, Any]] = {}

        # 1. Try SQLite
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("""
                SELECT ticker, company_name, listing_date, delisting_date,
                       suspension_start, suspension_end, ticker_old, ticker_new,
                       sector, status FROM historical_universe_registry
            """)
            rows = cur.fetchall()
            conn.close()
            if rows:
                for r in rows:
                    records[r[0]] = {
                        "ticker": r[0],
                        "company_name": r[1],
                        "listing_date": r[2],
                        "delisting_date": r[3],
                        "suspension_start": r[4],
                        "suspension_end": r[5],
                        "ticker_old": r[6],
                        "ticker_new": r[7],
                        "sector": r[8],
                        "status": r[9]
                    }
        except Exception:
            pass

        # 2. If SQLite empty, check JSON file
        if not records and os.path.exists(REGISTRY_JSON):
            try:
                with open(REGISTRY_JSON, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    records = {item["ticker"]: item for item in data}
            except Exception:
                pass

        cls._registry_cache = records
        return records

    @classmethod
    def save_registry_item(cls, item: Dict[str, Any]) -> bool:
        """Persists a stock record into SQLite and updates memory cache."""
        cls.init_db()
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            INSERT OR REPLACE INTO historical_universe_registry
            (ticker, company_name, listing_date, delisting_date, suspension_start, suspension_end, ticker_old, ticker_new, sector, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item["ticker"].upper(),
            item.get("company_name", item["ticker"]),
            item.get("listing_date", "2010-01-01"),
            item.get("delisting_date", "9999-12-31"),
            item.get("suspension_start"),
            item.get("suspension_end"),
            item.get("ticker_old"),
            item.get("ticker_new"),
            item.get("sector", "General"),
            item.get("status", "ACTIVE"),
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        conn.commit()
        conn.close()

        if cls._registry_cache is not None:
            cls._registry_cache[item["ticker"].upper()] = item
        return True

    @classmethod
    def is_tradable_on(cls, ticker: str, date: str) -> bool:
        """
        Point-in-Time Eligibility Gate:
        Returns True ONLY IF ticker was:
        1. Listed on or before date (listing_date <= date)
        2. Not delisted on or before date (date < delisting_date)
        3. Not suspended during this date
        """
        registry = cls.load_registry()
        t = ticker.upper().strip()
        rec = registry.get(t)

        if not rec:
            # Check if this ticker transitioned from or to another symbol
            for item in registry.values():
                if item.get("ticker_old") == t or item.get("ticker_new") == t:
                    rec = item
                    break

        if not rec:
            return False

        listing = rec.get("listing_date", "2000-01-01")
        delisting = rec.get("delisting_date", "9999-12-31")

        if date < listing:
            return False
        if date >= delisting:
            return False

        # Suspension checks
        susp_start = rec.get("suspension_start")
        susp_end = rec.get("suspension_end") or "9999-12-31"
        if susp_start and (susp_start <= date <= susp_end):
            return False

        return True

    @classmethod
    def get_tradable_universe(cls, date: str) -> List[str]:
        """
        Returns the exact Point-in-Time universe of tradable tickers on a specific calendar date.
        Completely eliminates Survivorship Bias.
        """
        registry = cls.load_registry()
        tradable = []
        for t in sorted(registry.keys()):
            if cls.is_tradable_on(t, date):
                tradable.append(t)
        return tradable

    @classmethod
    def get_universe_by_year(cls, year: int) -> List[str]:
        """Returns the midpoint tradable universe for a given historical year (July 1st)."""
        mid_date = f"{year}-07-01"
        return cls.get_tradable_universe(mid_date)
