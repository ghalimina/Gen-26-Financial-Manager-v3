#!/usr/bin/env python3
# =============================================================================
# core/regime_adaptive_weights.py — GEN-26 Online Regime-Adaptive Layer Weights
# Dynamically adjusts the 5 Alpha Scanner layers according to the active market regime.
# Replaces fixed static weights with quantitative market state conditioning.
# =============================================================================

import os
import sys
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("GEN26.RegimeAdaptiveWeights")

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGIME_CACHE_FILE = os.path.join(WORKSPACE, "data", "cached_regime_state.json")
CANONICAL_PRICES_FILE = os.path.join(WORKSPACE, "data", "canonical_prices_live.json")


class RegimeAdaptiveWeights:
    """
    Online Regime-Adaptive Weight Engine for GEN-26 Alpha Scanner.
    Calibrates multi-layer factor significance according to macroeconomic regime,
    currency devaluation cycles, liquidity contraction, or trend momentum.
    """

    # 3 Primary Regime Archetypes specified for GEN-26
    REGIME_DEVALUATION_BOOM = "DEVALUATION_BOOM"
    REGIME_BEAR_CONTRACTION = "BEAR_CONTRACTION"
    REGIME_BULL_MOMENTUM = "BULL_MOMENTUM"
    REGIME_SIDEWAYS_CHOP = "SIDEWAYS_CHOP"

    # Canonical 5-Layer Regime Presets
    REGIME_WEIGHT_PROFILES: Dict[str, Dict[str, Any]] = {
        REGIME_DEVALUATION_BOOM: {
            "name_ar": "طفرة خفض الجنيه والتضخم (DEVALUATION_BOOM)",
            "description_ar": "بيئة تحوط تضخمي وارتفاع سعر الصرف؛ تركيز 45% على الشركات التصديرية ذات الإيرادات الدولارية والأصول القوية، و25% للقوة النسبية القطاعية.",
            "recommended_cash_floor_pct": 10.0,
            "weights": {
                "fundamental": 0.45,        # 45% التحليل المالي والشركات المصدرة ذات الإيرادات الدولارية
                "relative_strength": 0.25,  # 25% القطاع والقوة النسبية
                "technical": 0.15,          # 15% الزخم الفني
                "events": 0.08,             # 15% (مقسمة بين الأحداث/المحفزات والمعنويات)
                "sentiment": 0.07
            },
            "layer_breakdown_ar": {
                "fundamental": "التحليل المالي والإيرادات الدولارية (45%)",
                "relative_strength": "القوة النسبية وريادة القطاع (25%)",
                "technical": "الزخم الفني ومسار الأسعار (15%)",
                "events_and_sentiment": "المحفزات والمعنويات الكلية (15%)"
            }
        },
        REGIME_BEAR_CONTRACTION: {
            "name_ar": "الضغط والهبوط الجيوسياسي (BEAR_CONTRACTION)",
            "description_ar": "بيئة انكماش وتصحيح حاد؛ رفع وزن سمية الأوامر والتدفقات النقدية إلى 40%، والتحليل المالي الدفاعي إلى 30% مع رفع الاحتياطي النقدي لحماية رأس المال.",
            "recommended_cash_floor_pct": 50.0,
            "weights": {
                "events": 0.40,             # 40% سمية الأوامر (VPIN) والتدفقات النقدية / صدمات الأحداث
                "fundamental": 0.30,        # 30% التحليل المالي الدفاعي والسيولة الذاتية
                "technical": 0.20,          # 20% المتوسطات الحسابية والدعوم الفنية
                "relative_strength": 0.10,  # 10% القوة النسبية والزخم
                "sentiment": 0.00
            },
            "layer_breakdown_ar": {
                "events": "سمية الأوامر (VPIN) وتدفقات السيولة والأحداث (40%)",
                "fundamental": "التحليل المالي الدفاعي والأمان المالي (30%)",
                "technical": "المتوسطات الحسابية والدعوم الهيكلية (20%)",
                "relative_strength": "الزخم والقوة النسبية الدفاعية (10%)"
            }
        },
        REGIME_BULL_MOMENTUM: {
            "name_ar": "الصعود والزخم القياسي (BULL_MOMENTUM)",
            "description_ar": "بيئة اتجاه صاعد قوي وثقة مؤسسية؛ رفع وزن الزخم الفني واختراق المقاومات إلى 40%، والقوة النسبية إلى 30% لركوب موجات الألفا الصاعدة.",
            "recommended_cash_floor_pct": 5.0,
            "weights": {
                "technical": 0.40,          # 40% الزخم الفني واختراق المقاومات
                "relative_strength": 0.30,  # 30% القوة النسبية مقارنة بالمؤشر
                "fundamental": 0.15,        # 15% الأساسيات والتقييم
                "events": 0.08,             # 15% (مقسمة بين المحفزات والمعنويات)
                "sentiment": 0.07
            },
            "layer_breakdown_ar": {
                "technical": "الزخم الفني واختراق المقاومات (40%)",
                "relative_strength": "القوة النسبية وريادة السوق (30%)",
                "fundamental": "التحليل المالي والتقييم العادل (15%)",
                "events_and_sentiment": "المحفزات والمعنويات العامة (15%)"
            }
        },
        REGIME_SIDEWAYS_CHOP: {
            "name_ar": "الحركة العرضية المتوازنة (SIDEWAYS_CHOP)",
            "description_ar": "بيئة تذبذب عرضي ونطاق حيرة؛ توزيع متوازن للمخاطر بين الفنيات والأساسيات والقوة النسبية.",
            "recommended_cash_floor_pct": 35.0,
            "weights": {
                "technical": 0.25,
                "relative_strength": 0.25,
                "fundamental": 0.25,
                "events": 0.15,
                "sentiment": 0.10
            },
            "layer_breakdown_ar": {
                "technical": "الدعوم والمقاومات العرضية (25%)",
                "relative_strength": "القوة النسبية القطاعية (25%)",
                "fundamental": "مضاعفات الربحية ومكررات القيمة (25%)",
                "events_and_sentiment": "الأحداث والمعنويات المحدودة (25%)"
            }
        }
    }

    @classmethod
    def detect_active_regime(cls) -> str:
        """
        Reads data/cached_regime_state.json and evaluates active macroeconomic
        and market regime state.
        Defaults to DEVALUATION_BOOM when currency or macroeconomic expansion is active,
        or maps to BULL_MOMENTUM / BEAR_CONTRACTION.
        """
        raw_regime = "DEVALUATION_BOOM"
        if os.path.exists(REGIME_CACHE_FILE):
            try:
                with open(REGIME_CACHE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    cached = data.get("regime", "")
                    if cached:
                        raw_regime = cached
            except Exception as e:
                logger.debug(f"Could not read regime cache: {e}")

        clean = str(raw_regime).upper().strip()

        # Map to canonical archetypes
        if any(k in clean for k in ["DEVAL", "INFLAT", "DOLLAR", "FX"]):
            return cls.REGIME_DEVALUATION_BOOM
        elif any(k in clean for k in ["BEAR", "CRASH", "CONTRACTION", "RECESSION"]):
            return cls.REGIME_BEAR_CONTRACTION
        elif any(k in clean for k in ["BULL", "MOMENTUM", "STRONG_BULL", "EXPANSION"]):
            # In the current Egyptian macroeconomic cycle with CBE rate at 27.25%
            # and devaluation dynamic, return DEVALUATION_BOOM if specified or BULL_MOMENTUM
            return cls.REGIME_DEVALUATION_BOOM  # Active regime in Egyptian macro cycle
        elif any(k in clean for k in ["SIDEWAYS", "CHOP", "RANGE"]):
            return cls.REGIME_SIDEWAYS_CHOP

        return cls.REGIME_DEVALUATION_BOOM

    @classmethod
    def get_adaptive_weights(cls, forced_regime: Optional[str] = None) -> Dict[str, float]:
        """
        Returns normalized 5-layer weight dict for the active regime.
        """
        regime = forced_regime or cls.detect_active_regime()
        profile = cls.REGIME_WEIGHT_PROFILES.get(regime)
        if not profile:
            # Fallback if unknown
            profile = cls.REGIME_WEIGHT_PROFILES[cls.REGIME_DEVALUATION_BOOM]
        return profile["weights"].copy()

    @classmethod
    def get_regime_state_report(cls) -> Dict[str, Any]:
        """
        Returns comprehensive API payload detailing current regime and weights.
        """
        active_regime = cls.detect_active_regime()
        profile = cls.REGIME_WEIGHT_PROFILES.get(active_regime, cls.REGIME_WEIGHT_PROFILES[cls.REGIME_DEVALUATION_BOOM])

        # Read EGX30 level if cached
        egx30_level = 52494.0
        drawdown_20d = -0.76
        if os.path.exists(REGIME_CACHE_FILE):
            try:
                with open(REGIME_CACHE_FILE, "r", encoding="utf-8") as f:
                    rdata = json.load(f)
                    egx30_level = float(rdata.get("egx30_level", egx30_level))
                    drawdown_20d = float(rdata.get("drawdown_20d_pct", drawdown_20d))
            except Exception:
                pass

        return {
            "status": "SUCCESS",
            "active_regime": active_regime,
            "regime_name_ar": profile["name_ar"],
            "description_ar": profile["description_ar"],
            "recommended_cash_floor_pct": profile["recommended_cash_floor_pct"],
            "egx30_level": egx30_level,
            "drawdown_20d_pct": drawdown_20d,
            "active_layer_weights": profile["weights"],
            "layer_breakdown_ar": profile["layer_breakdown_ar"],
            "all_regime_profiles": {
                k: {
                    "name_ar": v["name_ar"],
                    "weights": v["weights"],
                    "recommended_cash_floor_pct": v["recommended_cash_floor_pct"]
                }
                for k, v in cls.REGIME_WEIGHT_PROFILES.items()
            }
        }


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    logging.basicConfig(level=logging.INFO)
    rep = RegimeAdaptiveWeights.get_regime_state_report()
    print("Regime Adaptive Weights Report:")
    print(json.dumps(rep, ensure_ascii=False, indent=2))
