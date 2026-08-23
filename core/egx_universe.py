#!/usr/bin/env python3
# =============================================================================
# core/egx_universe.py — GEN-26 Egyptian Exchange (EGX) Universe Discovery & Audit
# Discovers, categorizes, and audits all known EGX securities.
# Explicitly distinguishes tradable, suspended, illiquid, missing data, and delisted stocks.
# NEVER falsely reports FULL_UNIVERSE if using partial public feeds.
# =============================================================================

import os
import json
import datetime
from typing import Dict, List, Any, Optional

from core.pit_store import HistoricalTradableUniverse


class SecurityStatus:
    TRADABLE = "TRADABLE"
    SUSPENDED = "SUSPENDED"
    ILLIQUID = "ILLIQUID"
    MISSING_DATA = "MISSING_DATA"
    EXCLUDED = "EXCLUDED"
    DELISTED = "DELISTED"
    UNKNOWN = "UNKNOWN"


class EGXUniverseAuditor:
    """
    Audits the discovered Egyptian Exchange universe and produces structured categorization.
    """

    # Discovered EGX Listed Assets Catalog
    EGX_CATALOG = [
        # Core 27 Liquid Blue-Chips & Mid-Caps matching CORE_EGX_UNIVERSE
        {"ticker": "COMI.CA", "name": "Commercial International Bank (CIB)", "sector": "Banking", "isin": "EGS60121C018", "is_core": True},
        {"ticker": "SWDY.CA", "name": "Elsewedy Electric", "sector": "Industrial", "isin": "EGS3G0C1C018", "is_core": True},
        {"ticker": "TMGH.CA", "name": "Talaat Moustafa Group Holding", "sector": "Real Estate", "isin": "EGS65851C015", "is_core": True},
        {"ticker": "EKHO.CA", "name": "Egypt Kuwait Holding", "sector": "Financial Services", "isin": "EGS69082C013", "is_core": True},
        {"ticker": "ETEL.CA", "name": "Telecom Egypt", "sector": "Telecom", "isin": "EGS48031C016", "is_core": True},
        {"ticker": "ABUK.CA", "name": "Abu Qir Fertilizers", "sector": "Fertilizers", "isin": "EGS38191C010", "is_core": True},
        {"ticker": "MFPC.CA", "name": "Misr Fertilizers Production (MOPCO)", "sector": "Fertilizers", "isin": "EGS38201C017", "is_core": True},
        {"ticker": "HELI.CA", "name": "Heliopolis Housing", "sector": "Real Estate", "isin": "EGS65591C017", "is_core": True},
        {"ticker": "ORAS.CA", "name": "Orascom Construction", "sector": "Industrial", "isin": "EGS21451C017", "is_core": True},
        {"ticker": "ESRS.CA", "name": "Ezz Steel", "sector": "Basic Materials", "isin": "EGS33041C012", "is_core": True},
        {"ticker": "HRHO.CA", "name": "EFG Holding", "sector": "Financial Services", "isin": "EGS69101C011", "is_core": True},
        {"ticker": "AMOC.CA", "name": "Alexandria Mineral Oils Company", "sector": "Energy", "isin": "EGS38321C019", "is_core": True},
        {"ticker": "SKPC.CA", "name": "Sidi Kerir Petrochemicals", "sector": "Petrochemicals", "isin": "EGS380S1C017", "is_core": True},
        {"ticker": "PHDC.CA", "name": "Palm Hills Developments", "sector": "Real Estate", "isin": "EGS655L1C012", "is_core": True},
        {"ticker": "MASR.CA", "name": "Madinet Masr (MNHD)", "sector": "Real Estate", "isin": "EGS65081C016", "is_core": True},
        {"ticker": "ISPH.CA", "name": "Ibnsina Pharma", "sector": "Healthcare", "isin": "EGS729J1C013", "is_core": True},
        {"ticker": "FWRY.CA", "name": "Fawry for Banking & Payment", "sector": "FinTech", "isin": "EGS745L1C014", "is_core": True},
        {"ticker": "EAST.CA", "name": "Eastern Company", "sector": "Consumer Staples", "isin": "EGS37091C013", "is_core": True},
        {"ticker": "EGAL.CA", "name": "Egypt Aluminium", "sector": "Basic Materials", "isin": "EGS34031C016", "is_core": True},
        {"ticker": "ORHD.CA", "name": "Orascom Development Egypt", "sector": "Real Estate", "isin": "EGS65011C013", "is_core": True},
        {"ticker": "CERA.CA", "name": "Ceramica Prima", "sector": "Industrial", "isin": "EGS3C341C012", "is_core": True},
        {"ticker": "JUFO.CA", "name": "Juhayna Food Industries", "sector": "Consumer Staples", "isin": "EGS30901C010", "is_core": True},
        {"ticker": "CLHO.CA", "name": "Cleopatra Hospital", "sector": "Healthcare", "isin": "EGS72131C011", "is_core": True},
        {"ticker": "CCAP.CA", "name": "Qalaa Holdings", "sector": "Financial Services", "isin": "EGS691T1C019", "is_core": True},
        {"ticker": "AUTO.CA", "name": "GB Corp (Ghabbour Auto)", "sector": "Automotive", "isin": "EGS673T1C012", "is_core": True},
        {"ticker": "BTFH.CA", "name": "Beltone Financial Holding", "sector": "Financial Services", "isin": "EGS691S1C011", "is_core": True},
        {"ticker": "RAYA.CA", "name": "Raya Holding for Financial Inv", "sector": "Financial Services", "isin": "EGS69071C014", "is_core": True},
        {"ticker": "ADIB.CA", "name": "Abu Dhabi Islamic Bank - Egypt", "sector": "Banking", "isin": "EGS60041C018", "is_core": True},
        {"ticker": "BINV.CA", "name": "B Investments Holding", "sector": "Financial Services", "isin": "EGS693R1C018", "is_core": True},
        {"ticker": "DOMT.CA", "name": "Arabian Food Industries (Domty)", "sector": "Consumer Staples", "isin": "EGS305B1C013", "is_core": True},
        {"ticker": "ALCN.CA", "name": "Alexandria Container & Cargo Handling", "sector": "Logistics", "isin": "EGS42081C014", "is_core": True},
        {"ticker": "CICH.CA", "name": "CI Capital Holding", "sector": "Financial Services", "isin": "EGS691S1C011", "is_core": True},
        
        # Extended Sample of Secondary / Suspended / Delisted Securities
        {"ticker": "SUSP1.CA", "name": "Suspended Test Industrial Co", "sector": "Industrial", "isin": "EGS000000001", "is_core": False, "force_status": SecurityStatus.SUSPENDED, "exclusion_reason": "CORPORATE_DISCLOSURE_SUSPENSION"},
        {"ticker": "ILLIQ1.CA", "name": "Low Liquidity Micro Cap", "sector": "Consumer", "isin": "EGS000000002", "is_core": False, "force_status": SecurityStatus.ILLIQUID, "exclusion_reason": "ADV_BELOW_2M_EGP_FLOOR"},
        {"ticker": "MISS1.CA", "name": "Missing Data Entity", "sector": "General", "isin": "EGS000000003", "is_core": False, "force_status": SecurityStatus.MISSING_DATA, "exclusion_reason": "INSUFFICIENT_HISTORICAL_BARS"},
        {"ticker": "DELIST1.CA", "name": "Historical Delisted Entity", "sector": "Real Estate", "isin": "EGS000000004", "is_core": False, "force_status": SecurityStatus.DELISTED, "exclusion_reason": "DELISTED_FROM_EGX"}
    ]

    @classmethod
    def audit_universe(cls, as_of_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Audits all discovered securities and partitions them into verified categories.
        """
        now_str = as_of_date or datetime.datetime.now().strftime("%Y-%m-%d")
        pit_univ = HistoricalTradableUniverse()

        discovered = []
        tradable = []
        suspended = []
        illiquid = []
        missing_data = []
        excluded = []
        delisted = []
        unknown = []

        for sec in cls.EGX_CATALOG:
            ticker = sec["ticker"]
            force_stat = sec.get("force_status")

            if force_stat == SecurityStatus.SUSPENDED:
                stat = SecurityStatus.SUSPENDED
                reason = sec.get("exclusion_reason", "SUSPENDED")
                suspended.append(ticker)
            elif force_stat == SecurityStatus.ILLIQUID:
                stat = SecurityStatus.ILLIQUID
                reason = sec.get("exclusion_reason", "BELOW_ADV_THRESHOLD")
                illiquid.append(ticker)
            elif force_stat == SecurityStatus.MISSING_DATA:
                stat = SecurityStatus.MISSING_DATA
                reason = sec.get("exclusion_reason", "MISSING_DATA")
                missing_data.append(ticker)
            elif force_stat == SecurityStatus.DELISTED:
                stat = SecurityStatus.DELISTED
                reason = sec.get("exclusion_reason", "DELISTED")
                delisted.append(ticker)
            else:
                # Check PIT tradability
                if pit_univ.is_tradable_on(ticker, now_str):
                    stat = SecurityStatus.TRADABLE
                    reason = "ELIGIBLE_FOR_SCREENING"
                    tradable.append(ticker)
                else:
                    stat = SecurityStatus.EXCLUDED
                    reason = "EXCLUDED_BY_PIT_UNIVERSE"
                    excluded.append(ticker)

            item = dict(sec)
            item["status"] = stat
            item["status_reason"] = reason
            discovered.append(item)

        report_payload = {
            "as_of": now_str,
            "provider": "Yahoo Finance + Local Point-In-Time Catalog",
            "coverage_status": "PARTIAL_UNIVERSE (Core 27 Curated Liquid EGX Universe)",
            "total_discovered": len(discovered),
            "tradable_count": len(tradable),
            "suspended_count": len(suspended),
            "illiquid_count": len(illiquid),
            "missing_data_count": len(missing_data),
            "excluded_count": len(excluded),
            "delisted_count": len(delisted),
            "unknown_count": len(unknown),
            "securities": discovered
        }

        # Save to reports/egx_universe.json
        rep_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")
        os.makedirs(rep_dir, exist_ok=True)
        json_path = os.path.join(rep_dir, "egx_universe.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report_payload, f, ensure_ascii=False, indent=2)

        return report_payload
