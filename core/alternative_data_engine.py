#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# core/alternative_data_engine.py — GEN-26 Alternative Data & Supply Chain Graph
# Phase 3 Quant Masterplan:
# 1. Supply Chain Dependency Graph (e.g., SUGR.CA -> JUFO.CA/EFID.CA input cost).
# 2. Real-Time Simulated Marine Port & Export Traffic Radar (ABUK.CA, MFPC.CA, SWDY.CA).
# 3. Raw Material & Commodity Inflation Tracker (Steel, Sugar, Cement, Copper).
# 4. Quantitative Alternative Data Scoring (-100.0 to +100.0) with Arabic catalysts.
# =============================================================================

import os
import sys
import json
import logging
import datetime
from typing import Dict, List, Any, Optional

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

logger = logging.getLogger("GEN26.AlternativeDataEngine")

# Canonical EGX Supply Chain & Commodity Dependency Knowledge Graph
EGX_SUPPLY_CHAIN_GRAPH: Dict[str, Dict[str, Any]] = {
    # 1. Food & Beverage / FMCG Downstream Users
    "JUFO.CA": {
        "company_name_ar": "جهينة للصناعات الغذائية",
        "sector": "Food & Beverage",
        "sector_ar": "الأغذية والمشروبات",
        "is_exporter": False,
        "upstream_suppliers": [
            {
                "ticker": "SUGR.CA",
                "name_ar": "الدلتا للسكر",
                "commodity": "Refined Sugar (السكر المكرر)",
                "cost_share_pct": 18.5,
                "correlation_type": "INPUT_COST_NEGATIVE",
                "status": "ELEVATED_PRICE_ALERT",
                "recent_price_change_pct": +14.2
            },
            {
                "ticker": "PACKAGING",
                "name_ar": "مواد التعبئة والتغليف والبوليمرات",
                "commodity": "Tetra Pak & Polymers",
                "cost_share_pct": 12.0,
                "correlation_type": "INPUT_COST_NEGATIVE",
                "status": "STABLE",
                "recent_price_change_pct": +1.5
            }
        ],
        "supply_chain_risk": "MEDIUM_HIGH",
        "primary_catalyst": "RAW_MATERIAL_SUGAR_SPIKE",
        "default_description_ar": "ارتفاع تكلفة المواد الخام (السكر المكرر بنسبة +14.2%) يضغط مؤقتاً على هوامش الربحية الإجمالية."
    },
    "EFID.CA": {
        "company_name_ar": "إيديتا للصناعات الغذائية",
        "sector": "Packaged Foods & Bakery",
        "sector_ar": "الأغذية الخفيفة والمخبوزات",
        "is_exporter": False,
        "upstream_suppliers": [
            {
                "ticker": "SUGR.CA",
                "name_ar": "الدلتا للسكر",
                "commodity": "Industrial Sugar",
                "cost_share_pct": 22.0,
                "correlation_type": "INPUT_COST_NEGATIVE",
                "status": "ELEVATED_PRICE_ALERT",
                "recent_price_change_pct": +14.2
            }
        ],
        "supply_chain_risk": "HIGH",
        "primary_catalyst": "RAW_MATERIAL_SUGAR_SPIKE",
        "default_description_ar": "ارتفاع أسعار السكر الصناعي يرفع تكلفة الإنتاج على إيديتا مع مرونة سعرية جيدة لتمرير التكلفة للمستهلك."
    },
    "DOMT.CA": {
        "company_name_ar": "الصناعات الغذائية العربية (دومتي)",
        "sector": "Dairy & Juice",
        "sector_ar": "الألبان والعصائر",
        "is_exporter": False,
        "upstream_suppliers": [
            {
                "ticker": "SUGR.CA",
                "name_ar": "الدلتا للسكر",
                "commodity": "Sugar",
                "cost_share_pct": 15.0,
                "correlation_type": "INPUT_COST_NEGATIVE",
                "status": "MODERATE",
                "recent_price_change_pct": +8.5
            }
        ],
        "supply_chain_risk": "MEDIUM",
        "primary_catalyst": "BENIGN_DAIRY_INPUTS",
        "default_description_ar": "استقرار نسبي في مدخلات بودرة الحليب مع ضغط محدود من مشتقات السكر."
    },

    # 2. Real Estate Developers Impacted by Steel & Cement
    "TMGH.CA": {
        "company_name_ar": "مجموعة طلعت مصطفى القابضة",
        "sector": "Real Estate & Urban Development",
        "sector_ar": "التطوير العقاري",
        "is_exporter": False,
        "upstream_suppliers": [
            {
                "ticker": "ESRS.CA",
                "name_ar": "حديد عز",
                "commodity": "Rebar & Structural Steel (حديد التسليح)",
                "cost_share_pct": 25.0,
                "correlation_type": "INPUT_COST_NEGATIVE",
                "status": "HIGH_COST_MODERATING",
                "recent_price_change_pct": -3.5
            },
            {
                "ticker": "SVCE.CA",
                "name_ar": "جنوب الوادي للأسمنت",
                "commodity": "Grey Cement & Aggregates (الأسمنت)",
                "cost_share_pct": 14.0,
                "correlation_type": "INPUT_COST_NEGATIVE",
                "status": "STABLE",
                "recent_price_change_pct": +2.0
            }
        ],
        "supply_chain_risk": "LOW_MODERATE",
        "primary_catalyst": "STABILIZING_CONSTRUCTION_COSTS",
        "default_description_ar": "استقرار وتراجع أسعار حديد التسليح (-3.5%) يدعم هوامش ربحية مشروعات طلعت مصطفى (مدينتي وبنان)."
    },
    "PHDC.CA": {
        "company_name_ar": "بالم هيلز للتعمير",
        "sector": "Real Estate & Construction",
        "sector_ar": "التطوير العقاري",
        "is_exporter": False,
        "upstream_suppliers": [
            {
                "ticker": "ESRS.CA",
                "name_ar": "حديد عز",
                "commodity": "Steel Rebar",
                "cost_share_pct": 22.0,
                "correlation_type": "INPUT_COST_NEGATIVE",
                "status": "STABLE",
                "recent_price_change_pct": -2.8
            }
        ],
        "supply_chain_risk": "LOW",
        "primary_catalyst": "BENIGN_BUILDING_MATERIALS",
        "default_description_ar": "انفراجة في تكاليف البناء والتشييد تدعم التدفقات النقدية وهوامش تسليم الوحدات."
    },

    # 3. Export Giants with Marine Port Traffic Feeds
    "ABUK.CA": {
        "company_name_ar": "أبو قير للأسمدة والصناعات الكيماوية",
        "sector": "Fertilizers & Chemicals",
        "sector_ar": "الأسمدة والبتروكيماويات",
        "is_exporter": True,
        "port_facility": "Abu Qir Port Terminal (ميناء أبو قير التصديري)",
        "export_share_pct": 72.0,
        "upstream_suppliers": [
            {
                "ticker": "EGAS",
                "name_ar": "الغاز الطبيعي الصناعي (إيجاس)",
                "commodity": "Natural Gas Feedstock",
                "cost_share_pct": 45.0,
                "correlation_type": "FEEDSTOCK_STABLE",
                "status": "STEADY_SUPPLY",
                "recent_price_change_pct": 0.0
            }
        ],
        "primary_catalyst": "MARINE_PORT_EXPORT_SURGE",
        "default_description_ar": "تكدس سفن التصدير في الميناء يبشر بأرباح ربع سنوية قوية وتدفقات دولارية متزايدة."
    },
    "MFPC.CA": {
        "company_name_ar": "مصر لإنتاج الأسمدة (موبكو)",
        "sector": "Fertilizers & Petrochemicals",
        "sector_ar": "الأسمدة والبتروكيماويات",
        "is_exporter": True,
        "port_facility": "Damietta Port Chemical Pier (رصيف ميناء دمياط التصديري)",
        "export_share_pct": 85.0,
        "upstream_suppliers": [
            {
                "ticker": "EGAS",
                "name_ar": "الغاز الطبيعي للتغذية الصناعية",
                "commodity": "Natural Gas Feedstock",
                "cost_share_pct": 50.0,
                "correlation_type": "FEEDSTOCK_STABLE",
                "status": "STEADY_SUPPLY",
                "recent_price_change_pct": 0.0
            }
        ],
        "primary_catalyst": "DAMIETTA_PORT_DOCKING_SURGE",
        "default_description_ar": "ارتفاع وتيرة شحنات اليوريا المصدرة عبر ميناء دمياط بنسبة +28% يدعم نمو الإيرادات بالعملة الصعبة."
    },

    # 4. Heavy Industrials & Global Exporters
    "SWDY.CA": {
        "company_name_ar": "السويدي إليكتريك",
        "sector": "Electrical Equipment & Cables",
        "sector_ar": "الكابلات والمعدات الكهربائية",
        "is_exporter": True,
        "port_facility": "Ain Sokhna & Alexandria Ports",
        "export_share_pct": 62.0,
        "upstream_suppliers": [
            {
                "ticker": "LME_COPPER",
                "name_ar": "النحاس والألومنيوم الخام (بورصة لندن للمعادن)",
                "commodity": "Raw Copper / Aluminum Cathodes",
                "cost_share_pct": 40.0,
                "correlation_type": "HEDGED_RAW_MATERIAL",
                "status": "HEDGED_PASS_THROUGH",
                "recent_price_change_pct": +3.2
            }
        ],
        "primary_catalyst": "GLOBAL_GRID_INFRASTRUCTURE_DEMAND",
        "default_description_ar": "طلبيات تصدير كابلات ضخمة لمشروعات الربط الكهربائي بالخليج وأوروبا مع تحوط كامل ضد تقلبات أسعار النحاس."
    }
}


class AlternativeDataEngine:
    """
    Alternative Data & Corporate Supply Chain Graph Engine for the Egyptian Stock Exchange.
    Provides informational edge through commodity dependencies, marine port shipping telemetry,
    and input-cost margin impact analysis.
    """

    SIGNAL_BULLISH_EXPORTS: str = "BULLISH_EXPORTS"
    SIGNAL_INPUT_COST_HEADWIND: str = "INPUT_COST_HEADWIND"
    SIGNAL_MARGIN_EXPANSION: str = "MARGIN_EXPANSION"
    SIGNAL_NEUTRAL: str = "NEUTRAL"

    # In-memory TTL Cache (1 Hour)
    CACHE_TTL_SECONDS: int = 3600
    _cache: Dict[str, Any] = {}
    _cache_timestamps: Dict[str, float] = {}

    # =========================================================================
    # 1. MARINE PORT & VESSEL TRAFFIC SIMULATED API CONNECTOR
    # =========================================================================

    @classmethod
    def fetch_marine_port_traffic(cls, port_name: str, terminal_type: str = "FERTILIZERS") -> Dict[str, Any]:
        """
        Connects to (or realistically simulates) Marine Port AIS tracking and vessel dwell times
        at major Egyptian commercial export harbors (Damietta, Abu Qir, Ain Sokhna, Alexandria).
        """
        # Deterministic simulation based on port name
        is_damietta = "damietta" in port_name.lower() or "دمياط" in port_name
        is_abu_qir = "abu qir" in port_name.lower() or "أبو قير" in port_name

        if is_abu_qir:
            vessels_docked = 12
            waiting_anchorage = 7
            monthly_tonnage_mt = 210_000
            traffic_density_score = 88.5  # High traffic
            status = "HIGH_EXPORT_SURGE"
            yoy_growth_pct = 24.8
        elif is_damietta:
            vessels_docked = 15
            waiting_anchorage = 9
            monthly_tonnage_mt = 285_000
            traffic_density_score = 92.0  # Very high export traffic
            status = "HIGH_EXPORT_SURGE"
            yoy_growth_pct = 28.2
        else:
            vessels_docked = 8
            waiting_anchorage = 4
            monthly_tonnage_mt = 140_000
            traffic_density_score = 72.0
            status = "MODERATE_EXPORT_ACTIVITY"
            yoy_growth_pct = 11.5

        return {
            "port_name": port_name,
            "terminal_type": terminal_type,
            "vessels_docked_count": vessels_docked,
            "vessels_waiting_anchorage": waiting_anchorage,
            "export_volume_mt": monthly_tonnage_mt,
            "traffic_density_score": traffic_density_score,
            "status": status,
            "yoy_traffic_growth_pct": yoy_growth_pct,
            "telemetry_timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    # =========================================================================
    # 2. ALTERNATIVE SIGNALS & SUPPLY CHAIN EVALUATION
    # =========================================================================

    @classmethod
    def fetch_alternative_signals(cls, ticker: str) -> Dict[str, Any]:
        """
        Fetches multi-dimensional alternative data and supply chain telemetry for a stock:
        - Downstream FMCG input costs (e.g. Sugar price spikes impacting JUFO/EFID).
        - Marine Port Traffic for Exporters (ABUK/MFPC).
        - Construction raw material price moderation (Steel/Cement impacting TMGH/PHDC).
        """
        if not ticker or not isinstance(ticker, str):
            return cls._get_neutral_fallback("UNKNOWN.CA")

        sym = ticker.upper().strip()
        if not sym.endswith(".CA") and "." not in sym:
            sym += ".CA"

        # Check in knowledge graph
        info = EGX_SUPPLY_CHAIN_GRAPH.get(sym)

        if not info:
            return cls._get_neutral_fallback(sym)

        is_exporter = bool(info.get("is_exporter", False))
        port_facility = info.get("port_facility")
        upstream = info.get("upstream_suppliers", [])

        # 1. Evaluate Exporter Port Signals (ABUK, MFPC, SWDY)
        port_telemetry = None
        if is_exporter and port_facility:
            port_telemetry = cls.fetch_marine_port_traffic(port_facility)
            density = port_telemetry.get("traffic_density_score", 70.0)

            if density >= 80.0:
                alt_score = round(min(95.0, 50.0 + (density - 80.0) * 3.5), 1)
                signal = cls.SIGNAL_BULLISH_EXPORTS
                catalyst = info.get("primary_catalyst", "MARINE_PORT_EXPORT_SURGE")
                desc_ar = info.get("default_description_ar", "تكدس سفن التصدير في الميناء يبشر بأرباح ربع سنوية قوية.")
            else:
                alt_score = 45.0
                signal = cls.SIGNAL_BULLISH_EXPORTS
                catalyst = "MODERATE_EXPORT_ACTIVITY"
                desc_ar = "نشاط تصديري مستقر مع تدفقات شحن منتظمة عبر الموانئ."

            return {
                "ticker": sym,
                "company_name_ar": info.get("company_name_ar", sym),
                "sector_ar": info.get("sector_ar", "عام"),
                "alt_data_score": alt_score,
                "signal": signal,
                "primary_catalyst": catalyst,
                "is_actionable": True,
                "conviction_badge_ar": "🟢 تدفقات تصدير قياسية",
                "description_ar": desc_ar,
                "port_traffic_telemetry": port_telemetry,
                "supply_chain_dependencies": upstream,
                "supply_chain_risk": info.get("supply_chain_risk", "LOW"),
                "model": "EGX Marine AIS & Export Shipping Radar"
            }

        # 2. Evaluate Input Cost Pressure (e.g. SUGR -> JUFO, EFID)
        has_sugar_inflation = any(
            u.get("ticker") == "SUGR.CA" and u.get("status") == "ELEVATED_PRICE_ALERT"
            for u in upstream
        )

        if has_sugar_inflation:
            sugar_chg = next((u.get("recent_price_change_pct", 10.0) for u in upstream if u.get("ticker") == "SUGR.CA"), 14.2)
            alt_score = round(max(-90.0, -40.0 - (sugar_chg * 1.5)), 1)
            signal = cls.SIGNAL_INPUT_COST_HEADWIND
            catalyst = "RAW_MATERIAL_SUGAR_PRICE_SPIKE"
            desc_ar = info.get(
                "default_description_ar",
                f"ارتفاع تكلفة المواد الخام (السكر المكرر بنسبة +{sugar_chg:.1f}%) يضغط على هوامش الربح."
            )

            return {
                "ticker": sym,
                "company_name_ar": info.get("company_name_ar", sym),
                "sector_ar": info.get("sector_ar", "عام"),
                "alt_data_score": alt_score,
                "signal": signal,
                "primary_catalyst": catalyst,
                "is_actionable": True,
                "conviction_badge_ar": "🔴 ضغوط تكاليف مدخلات الإنتاج",
                "description_ar": desc_ar,
                "port_traffic_telemetry": None,
                "supply_chain_dependencies": upstream,
                "supply_chain_risk": info.get("supply_chain_risk", "HIGH"),
                "model": "EGX Corporate Supply Chain & Input Cost Graph"
            }

        # 3. Evaluate Real Estate Material Costs (TMGH, PHDC)
        has_steel_moderation = any(
            u.get("ticker") == "ESRS.CA" and u.get("status") in ["HIGH_COST_MODERATING", "STABLE"]
            for u in upstream
        )

        if has_steel_moderation:
            alt_score = 65.0
            signal = cls.SIGNAL_MARGIN_EXPANSION
            catalyst = info.get("primary_catalyst", "STABILIZING_CONSTRUCTION_COSTS")
            desc_ar = info.get(
                "default_description_ar",
                "استقرار وتراجع أسعار حديد التسليح يدعم هوامش ربحية المشروعات العقارية."
            )

            return {
                "ticker": sym,
                "company_name_ar": info.get("company_name_ar", sym),
                "sector_ar": info.get("sector_ar", "عام"),
                "alt_data_score": alt_score,
                "signal": signal,
                "primary_catalyst": catalyst,
                "is_actionable": True,
                "conviction_badge_ar": "🟢 تحسن هوامش التشييد والبناء",
                "description_ar": desc_ar,
                "port_traffic_telemetry": None,
                "supply_chain_dependencies": upstream,
                "supply_chain_risk": info.get("supply_chain_risk", "LOW"),
                "model": "EGX Real Estate Materials Cost Graph"
            }

        # 4. Default Mapped Neutral State
        return {
            "ticker": sym,
            "company_name_ar": info.get("company_name_ar", sym),
            "sector_ar": info.get("sector_ar", "عام"),
            "alt_data_score": 10.0,
            "signal": cls.SIGNAL_NEUTRAL,
            "primary_catalyst": "BENIGN_SUPPLY_CHAIN",
            "is_actionable": False,
            "conviction_badge_ar": "⚪ سلاسل إمداد مستقرة",
            "description_ar": info.get("default_description_ar", "سلاسل الإمداد وتكاليف الإنتاج تتحرك ضمن النطاق الطبيعي."),
            "port_traffic_telemetry": None,
            "supply_chain_dependencies": upstream,
            "supply_chain_risk": info.get("supply_chain_risk", "LOW"),
            "model": "EGX Alternative Data Engine"
        }

    @classmethod
    def _get_neutral_fallback(cls, ticker: str) -> Dict[str, Any]:
        """Returns standard neutral telemetry for unmapped tickers."""
        return {
            "ticker": ticker,
            "company_name_ar": ticker,
            "sector_ar": "قطاع عام",
            "alt_data_score": 0.0,
            "signal": cls.SIGNAL_NEUTRAL,
            "primary_catalyst": "STANDARD_DATA_BASELINE",
            "is_actionable": False,
            "conviction_badge_ar": "⚪ لا توجد بيانات بديلة شاذة",
            "description_ar": "لا توجد إشارات بيانات بديلة استثنائية حالياً؛ الاعتماد على مؤشرات التحليل المالي والكمي المعتادة.",
            "port_traffic_telemetry": None,
            "supply_chain_dependencies": [],
            "supply_chain_risk": "LOW",
            "model": "EGX Alternative Data Engine"
        }

    # =========================================================================
    # 3. GRAPH QUERY HELPERS
    # =========================================================================

    @classmethod
    def get_all_supply_chain_relationships(cls) -> Dict[str, Any]:
        """Returns the full mapped corporate dependency knowledge graph."""
        return EGX_SUPPLY_CHAIN_GRAPH


if __name__ == "__main__":
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    import json
    print("JUFO.CA (FMCG Input Cost Shock):")
    print(json.dumps(AlternativeDataEngine.fetch_alternative_signals("JUFO.CA"), ensure_ascii=False, indent=2))

    print("\nABUK.CA (Marine Port Export Surge):")
    print(json.dumps(AlternativeDataEngine.fetch_alternative_signals("ABUK.CA"), ensure_ascii=False, indent=2))
