#!/usr/bin/env python3
# =============================================================================
# core/data_freshness.py — GEN-26 Data Freshness Hard Gate Engine
# Validates market data recency and fails closed if data is stale, missing, or corrupt.
# =============================================================================

import datetime
from typing import Dict, Any, Optional

from core.market_calendar import EGXMarketCalendar


class DataFreshnessGate:
    """
    Evaluates whether ingested market data is sufficiently fresh for decision generation.
    """
    MAX_ALLOWABLE_DATA_AGE_HOURS = 72.0 # Allows for weekend gap (Fri-Sat)

    @classmethod
    def evaluate_data_freshness(
        cls,
        last_data_timestamp_iso: Optional[str] = None,
        data_record_count: int = 27
    ) -> Dict[str, Any]:
        """
        Validates data timestamp against Cairo current time.
        """
        now = EGXMarketCalendar.get_cairo_time()

        if data_record_count <= 0:
            return {
                "is_fresh": False,
                "reason_code": "NO_VALID_UNIVERSE",
                "message": "Zero records found in candidate data feed."
            }

        if not last_data_timestamp_iso:
            return {
                "is_fresh": False,
                "reason_code": "DATA_INCOMPLETE",
                "message": "Missing data timestamp metadata."
            }

        try:
            # Parse ISO or YYYY-MM-DD
            if "T" in last_data_timestamp_iso:
                dt_data = datetime.datetime.fromisoformat(last_data_timestamp_iso)
            else:
                dt_data = datetime.datetime.strptime(last_data_timestamp_iso[:10], "%Y-%m-%d")
        except Exception:
            return {
                "is_fresh": False,
                "reason_code": "DATA_PROVIDER_FAILURE",
                "message": "Corrupt data timestamp format."
            }

        # Normalize tz
        dt_data_naive = dt_data.replace(tzinfo=None)
        now_naive = now.replace(tzinfo=None)
        age_hours = (now_naive - dt_data_naive).total_seconds() / 3600.0

        if age_hours < 0:
            # Timestamp in future -> Lookahead leakage risk!
            return {
                "is_fresh": False,
                "reason_code": "LOOKAHEAD_TEMPORAL_VIOLATION",
                "message": f"Data timestamp ({last_data_timestamp_iso}) is in the future!"
            }

        if age_hours > cls.MAX_ALLOWABLE_DATA_AGE_HOURS:
            return {
                "is_fresh": False,
                "reason_code": "DATA_STALE",
                "message": f"Data is {age_hours:.1f} hours old, exceeding {cls.MAX_ALLOWABLE_DATA_AGE_HOURS}h threshold."
            }

        return {
            "is_fresh": True,
            "reason_code": "DATA_FRESH_AND_VALID",
            "data_age_hours": round(age_hours, 1),
            "message": "Market data is fresh and eligible for trading."
        }
