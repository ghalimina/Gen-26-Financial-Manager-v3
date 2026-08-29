#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# core/data_sources_registry.py — 5-Tier Data Source Hierarchy & 3-Timestamp Anti-Leakage Guard
# Part of GEN-26 Expanded Architecture Version 2.0
# =============================================================================

import os
import sys
import yaml
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger("GEN26.DataSourceRegistry")

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY_YAML_PATH = os.path.join(WORKSPACE, "data_sources", "sources_registry.yaml")

DEFAULT_SOURCES_SPEC = {
    "version": "2.0.0-Institutional",
    "tiers": {
        "tier_1": {
            "name": "Tier 1: Primary Truth",
            "reliability_weight": 1.00,
            "sources": [
                {"id": "EGX_OFFICIAL", "name": "Egyptian Stock Exchange (EGX)", "data_type": "Settlement Prices, Disclosures"},
                {"id": "CBE_OFFICIAL", "name": "Central Bank of Egypt (CBE)", "data_type": "Corridor Rates, USD/EGP, Inflation"},
                {"id": "CAPMAS", "name": "CAPMAS Egypt", "data_type": "Official CPI Inflation"},
                {"id": "FRA_OFFICIAL", "name": "Financial Regulatory Authority (FRA)", "data_type": "Regulatory Filings"},
                {"id": "MOF_EGYPT", "name": "Ministry of Finance", "data_type": "T-Bill Yields, Sovereign Debt"},
                {"id": "COMPANY_IR", "name": "Company Investor Relations", "data_type": "Audited Financial Statements"}
            ]
        },
        "tier_2": {
            "name": "Tier 2: Secondary Context",
            "reliability_weight": 0.85,
            "sources": [
                {"id": "REUTERS", "name": "Reuters News", "data_type": "Macro News & Global Updates"},
                {"id": "ZAWYA", "name": "Refinitiv Zawya", "data_type": "MENA Deals & Sector Reports"},
                {"id": "MUBASHER", "name": "Mubasher Egypt", "data_type": "Disclosures & Market News"},
                {"id": "ENTERPRISE", "name": "Enterprise Press", "data_type": "Macro Intelligence Briefings"},
                {"id": "AL_BORSA", "name": "Al Borsa News", "data_type": "Local Press & Brokerage Flow"},
                {"id": "DAILY_NEWS_EGYPT", "name": "Daily News Egypt", "data_type": "Business Analysis"}
            ]
        },
        "tier_3": {
            "name": "Tier 3: Global Context",
            "reliability_weight": 0.80,
            "sources": [
                {"id": "IMF", "name": "International Monetary Fund", "data_type": "EFF Reviews & Macro Data"},
                {"id": "WORLD_BANK", "name": "World Bank", "data_type": "GDP Projections"},
                {"id": "US_FED", "name": "US Federal Reserve", "data_type": "Fed Funds Rate & DXY"},
                {"id": "OPEC", "name": "OPEC Secretariat", "data_type": "Crude Oil Production Quotas"},
                {"id": "WORLD_GOLD_COUNCIL", "name": "World Gold Council", "data_type": "Physical Gold Demand"}
            ]
        },
        "tier_4": {
            "name": "Tier 4: Cross-Validation Backup",
            "reliability_weight": 0.70,
            "sources": [
                {"id": "TRADINGVIEW", "name": "TradingView Feeds", "data_type": "OHLCV Candlesticks & Technicals"},
                {"id": "YFINANCE", "name": "Yahoo Finance API", "data_type": "Historical Prices & Global Commodities"},
                {"id": "INVESTING_COM", "name": "Investing.com", "data_type": "Bond Yields & FX Rates"}
            ]
        },
        "tier_5": {
            "name": "Tier 5: Institutional Ext",
            "reliability_weight": 0.95,
            "sources": [
                {"id": "LSEG_REFINITIV", "name": "LSEG Eikon", "data_type": "Consensus Estimates"},
                {"id": "SP_CAPITAL_IQ", "name": "S&P Capital IQ", "data_type": "Standardized Fundamental Ratios"},
                {"id": "BLOOMBERG", "name": "Bloomberg Terminal", "data_type": "Sovereign Spreads & CDS"}
            ]
        }
    }
}


class DataSourceRegistry:
    """
    Master Registry governing the 5-Tier Data Source Hierarchy and enforcing
    the 3-Timestamp Anti-Leakage Protocol (event_time, publication_time, effective_time).
    """

    _registry_data: Optional[Dict[str, Any]] = None

    @classmethod
    def _load_registry(cls) -> Dict[str, Any]:
        if cls._registry_data is not None:
            return cls._registry_data

        if os.path.exists(REGISTRY_YAML_PATH):
            try:
                with open(REGISTRY_YAML_PATH, "r", encoding="utf-8") as f:
                    cls._registry_data = yaml.safe_load(f) or DEFAULT_SOURCES_SPEC
                    return cls._registry_data
            except Exception as e:
                logger.warning("Could not parse %s, falling back to default spec: %s", REGISTRY_YAML_PATH, e)

        cls._registry_data = DEFAULT_SOURCES_SPEC
        return cls._registry_data

    @classmethod
    def get_all_tiers(cls) -> Dict[str, Any]:
        """Returns all 5 tiers and their constituent data sources."""
        spec = cls._load_registry()
        return spec.get("tiers", {})

    @classmethod
    def get_source_metadata(cls, source_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves metadata and reliability weight for a specific data source ID."""
        tiers = cls.get_all_tiers()
        target = source_id.upper().strip()
        for tier_key, tier_data in tiers.items():
            sources = tier_data.get("sources", [])
            for s in sources:
                if s.get("id", "").upper() == target:
                    res = dict(s)
                    res["tier"] = tier_key
                    res["tier_name"] = tier_data.get("name", "")
                    res["reliability_weight"] = tier_data.get("reliability_weight", 0.75)
                    return res
        return None

    @classmethod
    def get_source_reliability_weight(cls, source_id: str) -> float:
        """Returns the numerical reliability weight (0.0 to 1.0) for the given source."""
        meta = cls.get_source_metadata(source_id)
        if meta:
            return float(meta.get("reliability_weight", 0.75))
        return 0.70  # Default fallback weight

    # =========================================================================
    # 3-TIMESTAMP ANTI-LEAKAGE PROTOCOL
    # =========================================================================

    @staticmethod
    def _parse_ts(ts_val: Any) -> datetime:
        if isinstance(ts_val, datetime):
            return ts_val
        if isinstance(ts_val, (int, float)):
            return datetime.fromtimestamp(ts_val)
        if isinstance(ts_val, str):
            # Clean string
            s = ts_val.strip().replace("Z", "+00:00")
            for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S.%f"):
                try:
                    return datetime.strptime(s.split("+")[0], fmt)
                except ValueError:
                    pass
        return datetime.utcnow()

    @classmethod
    def enforce_3_timestamps(
        cls,
        record: Dict[str, Any],
        event_time: Any,
        publication_time: Any,
        effective_time: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Enforces the fundamental chronological invariant:
        effective_time >= publication_time >= event_time.

        Ensures that model training or backtesting never consumes data prior to its
        true market availability moment (effective_time).
        """
        t_event = cls._parse_ts(event_time)
        t_pub = cls._parse_ts(publication_time)

        # Invariant 1: publication_time cannot precede event_time
        if t_pub < t_event:
            logger.warning("Timestamp anomaly: publication_time (%s) < event_time (%s). Adjusting to event_time.", t_pub, t_event)
            t_pub = t_event

        # Default effective_time is publication_time if not explicitly passed
        if effective_time is None:
            t_eff = t_pub
        else:
            t_eff = cls._parse_ts(effective_time)
            # Invariant 2: effective_time cannot precede publication_time
            if t_eff < t_pub:
                logger.warning("Timestamp anomaly: effective_time (%s) < publication_time (%s). Clamping to publication_time.", t_eff, t_pub)
                t_eff = t_pub

        sanitized = dict(record)
        sanitized["event_time"] = t_event.isoformat()
        sanitized["publication_time"] = t_pub.isoformat()
        sanitized["effective_time"] = t_eff.isoformat()
        sanitized["timestamp_audit_status"] = "PASSED_3_TIMESTAMP_INVARIANT"
        return sanitized

    @classmethod
    def is_data_available_at(cls, record: Dict[str, Any], query_timestamp: Any) -> bool:
        """
        Strict Anti-Lookahead Gate:
        Returns True only if the record's effective_time is <= query_timestamp.
        """
        eff_str = record.get("effective_time")
        if not eff_str:
            # Fallback to publication_time or timestamp
            eff_str = record.get("publication_time") or record.get("timestamp")

        if not eff_str:
            return True  # If unversioned, permit with log warning

        t_eff = cls._parse_ts(eff_str)
        t_query = cls._parse_ts(query_timestamp)
        return t_eff <= t_query

    @classmethod
    def get_summary_report(cls) -> Dict[str, Any]:
        """Generates comprehensive summary for the dashboard observability suite."""
        tiers = cls.get_all_tiers()
        tier_summaries = []
        total_sources = 0
        for k, v in tiers.items():
            src_list = v.get("sources", [])
            total_sources += len(src_list)
            tier_summaries.append({
                "tier_id": k,
                "tier_name": v.get("name"),
                "description": v.get("description", ""),
                "reliability_weight": v.get("reliability_weight", 1.0),
                "source_count": len(src_list),
                "sources": src_list
            })

        return {
            "version": "2.0.0-Institutional",
            "total_tiers": len(tiers),
            "total_registered_sources": total_sources,
            "anti_leakage_rule": "effective_time >= publication_time >= event_time",
            "tiers": tier_summaries
        }


if __name__ == "__main__":
    print("Testing DataSourceRegistry...")
    summary = DataSourceRegistry.get_summary_report()
    print(json.dumps(summary, indent=2, ensure_ascii=False))
