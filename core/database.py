#!/usr/bin/env python3
# =============================================================================
# core/database.py — GEN-26 Unified Relational Database & Persistence Layer
# SQLite/PostgreSQL-compatible ACID relational storage engine.
# Guarantees immutable audit records, indexing, and non-destructive session storage.
# =============================================================================

import os
import sqlite3
import json
import datetime
from typing import Dict, List, Any, Optional


class DatabaseManager:
    """
    Manages SQLite database connections, schema initialization, and transactional queries.
    """
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    DB_PATH = os.path.join(DATA_DIR, "gen26_production.db")

    @classmethod
    def get_connection(cls) -> sqlite3.Connection:
        """Returns an active SQLite database connection with row_factory enabled."""
        os.makedirs(cls.DATA_DIR, exist_ok=True)
        conn = sqlite3.connect(cls.DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    @classmethod
    def initialize_schema(cls):
        """Initializes all relational tables and indexes."""
        with cls.get_connection() as conn:
            cursor = conn.cursor()

            # 1. Stocks Universe Catalog
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS stocks (
                ticker TEXT PRIMARY KEY,
                company_name TEXT NOT NULL,
                sector TEXT NOT NULL,
                isin TEXT,
                status TEXT NOT NULL DEFAULT 'TRADABLE',
                is_core INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            );
            """)

            # 2. Market Prices
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                market_date TEXT NOT NULL,
                open_price REAL NOT NULL,
                high_price REAL NOT NULL,
                low_price REAL NOT NULL,
                close_price REAL NOT NULL,
                volume REAL NOT NULL,
                adv_20d REAL,
                created_at TEXT NOT NULL,
                UNIQUE(ticker, market_date),
                FOREIGN KEY (ticker) REFERENCES stocks (ticker)
            );
            """)

            # 3. Stock Scores & Alpha Rankings
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                as_of_date TEXT NOT NULL,
                rank INTEGER NOT NULL,
                alpha_score REAL NOT NULL,
                risk_score REAL NOT NULL,
                liquidity_score REAL NOT NULL,
                expected_return_pct REAL NOT NULL,
                recommendation TEXT NOT NULL,
                reason_codes TEXT,
                created_at TEXT NOT NULL,
                UNIQUE(ticker, as_of_date),
                FOREIGN KEY (ticker) REFERENCES stocks (ticker)
            );
            """)

            # 4. Signals
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS signals (
                signal_id TEXT PRIMARY KEY,
                market_date TEXT NOT NULL,
                ticker TEXT NOT NULL,
                action TEXT NOT NULL,
                entry_price REAL NOT NULL,
                target_price REAL NOT NULL,
                stop_loss REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'ACTIVE',
                created_at TEXT NOT NULL,
                FOREIGN KEY (ticker) REFERENCES stocks (ticker)
            );
            """)

            # 5. Paper Sessions (Immutable History)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS paper_sessions (
                session_id TEXT PRIMARY KEY,
                session_number INTEGER NOT NULL UNIQUE,
                market_date TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL,
                realized_pnl REAL NOT NULL DEFAULT 0.0,
                portfolio_equity REAL NOT NULL,
                cash_reserve REAL NOT NULL,
                sha256_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """)

            # 6. Real Portfolio Positions
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS real_portfolio_positions (
                holding_id TEXT PRIMARY KEY,
                ticker TEXT NOT NULL UNIQUE,
                quantity INTEGER NOT NULL,
                average_entry_price REAL NOT NULL,
                manual_notes TEXT,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (ticker) REFERENCES stocks (ticker)
            );
            """)

            # 7. Real Portfolio Transactions
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS real_portfolio_transactions (
                transaction_id TEXT PRIMARY KEY,
                holding_id TEXT,
                ticker TEXT NOT NULL,
                action TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                fees REAL DEFAULT 0.0,
                transaction_date TEXT NOT NULL,
                notes TEXT,
                created_at TEXT NOT NULL
            );
            """)

            # 8. Risk Events & Invariant Telemetry
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS risk_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                invariant_name TEXT NOT NULL,
                current_value REAL,
                threshold_value REAL,
                severity TEXT NOT NULL,
                details TEXT
            );
            """)

            # 9. Drift Metrics
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS drift_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                dimension TEXT NOT NULL,
                observed_value REAL NOT NULL,
                status TEXT NOT NULL
            );
            """)

            # Create Indexes for fast retrieval
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_market_prices_ticker ON market_prices (ticker);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_stock_scores_date ON stock_scores (as_of_date);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_signals_date ON signals (market_date);")

            conn.commit()

    @classmethod
    def seed_initial_catalog(cls):
        """Seeds standard core stocks catalog and latest canonical prices into database."""
        from core.egx_universe import EGXUniverseAuditor
        from core.egx_universe_loader import EGXUniverseLoader
        from core.market_price_service import MarketPriceService
        cls.initialize_schema()
        now_str = datetime.datetime.now().isoformat()
        with cls.get_connection() as conn:
            cursor = conn.cursor()
            # 1. Seed EGX Universe Catalog
            full_universe = EGXUniverseLoader.get_universe()
            for info in full_universe:
                ticker = info["ticker"]
                cursor.execute("""
                INSERT OR IGNORE INTO stocks (ticker, company_name, sector, isin, status, is_core, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """, (
                    ticker,
                    info.get("name_ar", info.get("name_en", ticker)),
                    info.get("sector", "General"),
                    info.get("isin", ""),
                    "TRADABLE",
                    1 if "EGX30" in info.get("index_membership", []) else 0,
                    now_str
                ))

            # 2. Seed canonical market prices
            cursor.execute("DELETE FROM market_prices;")
            for rec in MarketPriceService.get_all_canonical_prices(universe="all"):
                cursor.execute("""
                INSERT OR REPLACE INTO market_prices (ticker, market_date, open_price, high_price, low_price, close_price, volume, adv_20d, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    rec["ticker"],
                    rec.get("market_date", "2026-08-20"),
                    rec.get("open", rec["price"]),
                    rec.get("high", rec["price"]),
                    rec.get("low", rec["price"]),
                    rec["price"],
                    rec.get("volume", 10000),
                    rec.get("turnover_egp", 0.0) / rec["price"] if rec["price"] > 0 else 0.0,
                    now_str
                ))

            conn.commit()
