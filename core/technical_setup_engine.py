#!/usr/bin/env python3
# =============================================================================
# core/technical_setup_engine.py — GEN-26 Quantitative Technical Setup Engine
# Evaluates Trend Structure, Support/Resistance, Moving Average Alignment,
# RSI14/ADX14 Momentum, and Price-Volume Confirmation for EGX Constituents.
# =============================================================================

import math
from typing import Dict, List, Any, Optional
from core.market_price_service import MarketPriceService


class TechnicalSetupEngine:
    """
    Quantitative technical setup and price-action engine.
    Calculates technical factor score (0 - 100), trend structure,
    and entry setups (e.g. Pullback to MA20, Breakout Expansion).
    """

    SETUP_PULLBACK_UPTREND = "PULLBACK_UPTREND"
    SETUP_BREAKOUT_EXPANSION = "BREAKOUT_EXPANSION"
    SETUP_RANGE_CONSOLIDATION = "RANGE_CONSOLIDATION"
    SETUP_DOWNTREND_PULLBACK = "DOWNTREND_PULLBACK"
    SETUP_OVERSOLD_REVERSAL = "OVERSOLD_REVERSAL"

    SETUP_ARABIC = {
        SETUP_PULLBACK_UPTREND: "تراجع تصحيحي هادئ داخل اتجاه صاعد رئيسي (Pullback to MA Support)",
        SETUP_BREAKOUT_EXPANSION: "اختراق مقاومة فنية مع توسع في نطاق التداول والسيولة (Breakout)",
        SETUP_RANGE_CONSOLIDATION: "تجميع جانبي متوازن بين مستويات الدعم والمقاومة (Consolidation)",
        SETUP_DOWNTREND_PULLBACK: "ارتداد تصحيحي مؤقت داخل مسار هابط (Downtrend Rebound)",
        SETUP_OVERSOLD_REVERSAL: "ارتداد إيجابي من مناطق تشبع بيعي حاد (Oversold Reversal)"
    }

    # Reference technical indicators for active EGX 24 universe
    _TECHNICAL_PROFILES = {
        "COMI.CA": {
            "ema20": 133.50, "ema50": 128.00, "rsi14": 58.5, "adx14": 28.5, "support_1": 134.50, "resistance_1": 142.00,
            "trend": "STRONG_UPTREND", "vol_price_confirm": True, "setup": SETUP_PULLBACK_UPTREND
        },
        "SWDY.CA": {
            "ema20": 112.00, "ema50": 105.50, "rsi14": 56.0, "adx14": 26.0, "support_1": 113.50, "resistance_1": 122.00,
            "trend": "STRONG_UPTREND", "vol_price_confirm": True, "setup": SETUP_PULLBACK_UPTREND
        },
        "TMGH.CA": {
            "ema20": 94.20, "ema50": 89.00, "rsi14": 55.0, "adx14": 24.5, "support_1": 95.00, "resistance_1": 102.50,
            "trend": "UPTREND", "vol_price_confirm": True, "setup": SETUP_PULLBACK_UPTREND
        },
        "ORAS.CA": {
            "ema20": 740.00, "ema50": 715.00, "rsi14": 54.0, "adx14": 22.0, "support_1": 742.00, "resistance_1": 780.00,
            "trend": "UPTREND", "vol_price_confirm": False, "setup": SETUP_RANGE_CONSOLIDATION
        },
        "ETEL.CA": {
            "ema20": 111.50, "ema50": 108.00, "rsi14": 51.5, "adx14": 20.0, "support_1": 112.00, "resistance_1": 118.50,
            "trend": "UPTREND", "vol_price_confirm": False, "setup": SETUP_RANGE_CONSOLIDATION
        },
        "EGAL.CA": {
            "ema20": 318.00, "ema50": 298.00, "rsi14": 62.0, "adx14": 31.0, "support_1": 322.00, "resistance_1": 345.00,
            "trend": "STRONG_UPTREND", "vol_price_confirm": True, "setup": SETUP_BREAKOUT_EXPANSION
        },
        "ABUK.CA": {
            "ema20": 73.00, "ema50": 69.50, "rsi14": 53.5, "adx14": 21.0, "support_1": 74.00, "resistance_1": 78.50,
            "trend": "UPTREND", "vol_price_confirm": False, "setup": SETUP_PULLBACK_UPTREND
        },
        "MFPC.CA": {
            "ema20": 37.80, "ema50": 36.20, "rsi14": 52.6, "adx14": 20.2, "support_1": 38.00, "resistance_1": 41.00,
            "trend": "UPTREND", "vol_price_confirm": False, "setup": SETUP_RANGE_CONSOLIDATION
        },
        "ADIB.CA": {
            "ema20": 51.50, "ema50": 48.00, "rsi14": 52.2, "adx14": 20.0, "support_1": 52.00, "resistance_1": 56.00,
            "trend": "UPTREND", "vol_price_confirm": False, "setup": SETUP_RANGE_CONSOLIDATION
        },
        "EAST.CA": {
            "ema20": 34.80, "ema50": 33.00, "rsi14": 57.0, "adx14": 23.5, "support_1": 35.20, "resistance_1": 38.00,
            "trend": "UPTREND", "vol_price_confirm": True, "setup": SETUP_PULLBACK_UPTREND
        },
        "JUFO.CA": {
            "ema20": 25.80, "ema50": 24.50, "rsi14": 51.0, "adx14": 18.5, "support_1": 26.00, "resistance_1": 28.00,
            "trend": "SIDEWAYS", "vol_price_confirm": False, "setup": SETUP_RANGE_CONSOLIDATION
        },
        "GBCO.CA": {
            "ema20": 28.20, "ema50": 27.00, "rsi14": 50.5, "adx14": 19.0, "support_1": 28.50, "resistance_1": 30.50,
            "trend": "SIDEWAYS", "vol_price_confirm": False, "setup": SETUP_RANGE_CONSOLIDATION
        },
        "HRHO.CA": {
            "ema20": 25.20, "ema50": 24.00, "rsi14": 55.5, "adx14": 22.5, "support_1": 25.80, "resistance_1": 27.50,
            "trend": "UPTREND", "vol_price_confirm": True, "setup": SETUP_PULLBACK_UPTREND
        },
        "EFIH.CA": {
            "ema20": 23.50, "ema50": 22.00, "rsi14": 58.0, "adx14": 25.0, "support_1": 24.00, "resistance_1": 26.00,
            "trend": "STRONG_UPTREND", "vol_price_confirm": True, "setup": SETUP_PULLBACK_UPTREND
        },
        "FWRY.CA": {
            "ema20": 18.40, "ema50": 17.50, "rsi14": 56.5, "adx14": 24.0, "support_1": 18.80, "resistance_1": 20.20,
            "trend": "UPTREND", "vol_price_confirm": True, "setup": SETUP_PULLBACK_UPTREND
        },
        "DOMT.CA": {
            "ema20": 27.20, "ema50": 26.00, "rsi14": 50.0, "adx14": 18.0, "support_1": 27.50, "resistance_1": 29.50,
            "trend": "SIDEWAYS", "vol_price_confirm": False, "setup": SETUP_RANGE_CONSOLIDATION
        },
        "PHDC.CA": {
            "ema20": 14.60, "ema50": 14.00, "rsi14": 49.5, "adx14": 17.5, "support_1": 14.80, "resistance_1": 15.80,
            "trend": "SIDEWAYS", "vol_price_confirm": False, "setup": SETUP_RANGE_CONSOLIDATION
        },
        "ISPH.CA": {
            "ema20": 12.60, "ema50": 12.00, "rsi14": 48.0, "adx14": 16.5, "support_1": 12.70, "resistance_1": 13.60,
            "trend": "SIDEWAYS", "vol_price_confirm": False, "setup": SETUP_RANGE_CONSOLIDATION
        },
        "EMFD.CA": {
            "ema20": 11.30, "ema50": 10.60, "rsi14": 57.0, "adx14": 24.5, "support_1": 11.50, "resistance_1": 12.50,
            "trend": "UPTREND", "vol_price_confirm": True, "setup": SETUP_PULLBACK_UPTREND
        },
        "AMOC.CA": {
            "ema20": 11.00, "ema50": 10.50, "rsi14": 50.0, "adx14": 18.0, "support_1": 11.10, "resistance_1": 12.00,
            "trend": "SIDEWAYS", "vol_price_confirm": False, "setup": SETUP_RANGE_CONSOLIDATION
        },
        "HELI.CA": {
            "ema20": 7.40, "ema50": 7.00, "rsi14": 53.0, "adx14": 21.0, "support_1": 7.50, "resistance_1": 8.00,
            "trend": "UPTREND", "vol_price_confirm": True, "setup": SETUP_PULLBACK_UPTREND
        },
        "RAYA.CA": {
            "ema20": 6.85, "ema50": 6.70, "rsi14": 46.0, "adx14": 15.0, "support_1": 6.80, "resistance_1": 7.30,
            "trend": "SIDEWAYS", "vol_price_confirm": False, "setup": SETUP_RANGE_CONSOLIDATION
        },
        "CCAP.CA": {
            "ema20": 5.45, "ema50": 5.30, "rsi14": 45.0, "adx14": 14.5, "support_1": 5.40, "resistance_1": 5.90,
            "trend": "WEAK", "vol_price_confirm": False, "setup": SETUP_DOWNTREND_PULLBACK
        },
        "BTFH.CA": {
            "ema20": 2.92, "ema50": 2.85, "rsi14": 44.0, "adx14": 14.0, "support_1": 2.90, "resistance_1": 3.15,
            "trend": "WEAK", "vol_price_confirm": False, "setup": SETUP_DOWNTREND_PULLBACK
        }
    }

    @classmethod
    def evaluate_technical_setup(
        cls,
        ticker: str,
        current_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calculates multi-indicator technical subscore (0 - 100) and actionable setup classification.
        """
        sym = ticker.upper().strip()
        if not sym.endswith(".CA") and "." not in sym:
            sym = f"{sym}.CA"

        prof = cls._TECHNICAL_PROFILES.get(sym, {
            "ema20": 10.0, "ema50": 9.5, "rsi14": 50.0, "adx14": 20.0,
            "support_1": 9.8, "resistance_1": 10.5, "trend": "SIDEWAYS",
            "vol_price_confirm": False, "setup": cls.SETUP_RANGE_CONSOLIDATION
        })

        canon = MarketPriceService.CANONICAL_PRICES.get(sym, {})
        p = current_price or canon.get("price", prof["ema20"] * 1.02)
        ema20 = prof["ema20"]
        ema50 = prof["ema50"]
        rsi = prof["rsi14"]
        adx = prof["adx14"]
        s1 = prof["support_1"]
        r1 = prof["resistance_1"]

        # 1. Moving Average Alignment Score (0 - 30 pts)
        ma_score = 0.0
        if p >= ema20 >= ema50:
            ma_score = 30.0  # Perfect bullish stack
        elif p >= ema20:
            ma_score = 22.0
        elif p >= ema50:
            ma_score = 14.0
        else:
            ma_score = 5.0   # Below major moving averages

        # 2. Trend & ADX Strength Score (0 - 25 pts)
        trend_score = 0.0
        if adx >= 25.0 and prof["trend"] in ["STRONG_UPTREND", "UPTREND"]:
            trend_score = 25.0
        elif adx >= 20.0 and prof["trend"] in ["UPTREND"]:
            trend_score = 18.0
        elif prof["trend"] == "SIDEWAYS":
            trend_score = 10.0
        else:
            trend_score = 4.0

        # 3. RSI Momentum Zone (0 - 25 pts)
        # Optimal bullish pullback momentum zone is 50 - 65
        rsi_score = 0.0
        if 50.0 <= rsi <= 62.0:
            rsi_score = 25.0  # Sweet spot: strong momentum without overbought exhaustion
        elif 62.0 < rsi <= 70.0:
            rsi_score = 20.0
        elif 40.0 <= rsi < 50.0:
            rsi_score = 12.0
        elif rsi > 70.0:
            rsi_score = 10.0  # Overbought penalty
        else:
            rsi_score = 5.0   # Weak / Oversold drag

        # 4. Support Proximity & Volume Confirmation (0 - 20 pts)
        supp_score = 0.0
        # Distance to support in %
        dist_to_supp = ((p - s1) / p) * 100.0 if p > 0 else 5.0
        if 0.0 <= dist_to_supp <= 2.5:
            supp_score += 10.0  # High reward-to-risk near key support
        elif dist_to_supp <= 5.0:
            supp_score += 6.0
        else:
            supp_score += 3.0

        if prof["vol_price_confirm"]:
            supp_score += 10.0  # Volume expands on up-moves, dries up on pullbacks
        else:
            supp_score += 4.0

        technical_score = round(ma_score + trend_score + rsi_score + supp_score, 1)
        technical_score = min(max(technical_score, 10.0), 98.0)

        return {
            "ticker": sym,
            "current_price": p,
            "ema20": ema20,
            "ema50": ema50,
            "rsi14": rsi,
            "adx14": adx,
            "support_level": s1,
            "resistance_level": r1,
            "trend_regime": prof["trend"],
            "setup_classification": prof["setup"],
            "setup_label_ar": cls.SETUP_ARABIC.get(prof["setup"], "تداول فني اعتيادي"),
            "volume_price_confirmed": prof["vol_price_confirm"],
            "technical_score": technical_score,
            "is_above_ema20": p >= ema20,
            "is_above_ema50": p >= ema50,
            "adx_trend_strength": "STRONG" if adx >= 25.0 else ("MODERATE" if adx >= 20.0 else "WEAK")
        }
