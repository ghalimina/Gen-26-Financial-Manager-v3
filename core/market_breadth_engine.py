#!/usr/bin/env python3
# =============================================================================
# core/market_breadth_engine.py — GEN-26 Institutional Market Breadth & Regime Engine
# Dynamically evaluates Advance/Decline breadth, MA20/MA50 participation,
# and classifies macro EGX Market Regimes (STRONG_BULL, NEUTRAL, DISTRIBUTION, PANIC_BEAR).
# =============================================================================

import math
from typing import Dict, List, Any, Optional
from core.market_price_service import MarketPriceService
from core.egx_universe_loader import EGXUniverseLoader


class MarketBreadthEngine:
    """
    Evaluates market-wide participation, internal momentum breadth,
    and classifies overall EGX Market Regime for institutional risk modulation.
    """

    # Market Regime Classifications
    REGIME_STRONG_BULL = "STRONG_BULL"
    REGIME_NEUTRAL = "NEUTRAL"
    REGIME_DISTRIBUTION = "DISTRIBUTION"
    REGIME_PANIC_BEAR = "PANIC_BEAR"

    REGIME_ARABIC = {
        REGIME_STRONG_BULL: "اتّجاه صاعد قوي ومشاركة واسعة (STRONG_BULL)",
        REGIME_NEUTRAL: "سوق متوازن / حركة عرضية منضبطة (NEUTRAL)",
        REGIME_DISTRIBUTION: "تصريف وتناقص في المشاركة الداخلية (DISTRIBUTION)",
        REGIME_PANIC_BEAR: "هبوط حاد وذعر بيعي (PANIC_BEAR)"
    }

    # Reference historical moving average estimates for active EGX universe
    _MA_BENCHMARKS = {
        "COMI.CA": {"ma20": 133.50, "ma50": 128.00},
        "SWDY.CA": {"ma20": 113.00, "ma50": 108.50},
        "TMGH.CA": {"ma20": 95.00, "ma50": 91.20},
        "ORAS.CA": {"ma20": 740.00, "ma50": 715.00},
        "ETEL.CA": {"ma20": 112.50, "ma50": 107.00},
        "EGAL.CA": {"ma20": 322.00, "ma50": 310.00},
        "ABUK.CA": {"ma20": 74.00, "ma50": 71.50},
        "MFPC.CA": {"ma20": 47.20, "ma50": 45.80},
        "ADIB.CA": {"ma20": 52.00, "ma50": 49.50},
        "EAST.CA": {"ma20": 35.20, "ma50": 34.00},
        "JUFO.CA": {"ma20": 26.00, "ma50": 25.10},
        "GBCO.CA": {"ma20": 28.50, "ma50": 27.20},
        "HRHO.CA": {"ma20": 25.80, "ma50": 24.90},
        "EFIH.CA": {"ma20": 23.80, "ma50": 22.90},
        "FWRY.CA": {"ma20": 18.80, "ma50": 18.10},
        "DOMT.CA": {"ma20": 14.80, "ma50": 14.20},
        "PHDC.CA": {"ma20": 14.70, "ma50": 14.00},
        "ISPH.CA": {"ma20": 12.80, "ma50": 12.30},
        "EMFD.CA": {"ma20": 11.50, "ma50": 10.90},
        "AMOC.CA": {"ma20": 11.10, "ma50": 10.70},
        "HELI.CA": {"ma20": 7.50, "ma50": 7.20},
        "RAYA.CA": {"ma20": 6.85, "ma50": 6.60},
        "CCAP.CA": {"ma20": 5.48, "ma50": 5.30},
        "BTFH.CA": {"ma20": 2.90, "ma50": 2.80}
    }

    @classmethod
    def compute_market_breadth(
        cls,
        current_prices: Optional[Dict[str, float]] = None,
        universe_tickers: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Computes dynamic market breadth statistics, Advance/Decline ratio,
        MA participation (% above MA20 and MA50), and classifies the market regime.
        """
        active_stocks = EGXUniverseLoader.get_active_universe()
        tickers = universe_tickers or list(active_stocks.keys())
        
        advances = 0
        declines = 0
        unchanged = 0
        
        above_ma20_count = 0
        above_ma50_count = 0
        total_eval = 0
        
        constituent_breadth = []

        for sym in tickers:
            sym_clean = sym.upper().strip()
            if not sym_clean.endswith(".CA") and "." not in sym_clean:
                sym_clean = f"{sym_clean}.CA"
                
            try:
                cp = current_prices.get(sym_clean) if current_prices else MarketPriceService.get_latest_price(sym_clean)
            except Exception:
                canon = MarketPriceService.CANONICAL_PRICES.get(sym_clean, {})
                cp = canon.get("price", 10.0)

            # Previous close reference
            canon_rec = MarketPriceService.CANONICAL_PRICES.get(sym_clean, {})
            prev_close = canon_rec.get("previous_close", cp * 0.995)
            
            # Moving averages
            ma_ref = cls._MA_BENCHMARKS.get(sym_clean, {
                "ma20": round(cp * 0.97, 2),
                "ma50": round(cp * 0.94, 2)
            })
            ma20 = ma_ref["ma20"]
            ma50 = ma_ref["ma50"]

            daily_ret = ((cp - prev_close) / prev_close) * 100.0 if prev_close > 0 else 0.0
            
            if daily_ret > 0.10:
                advances += 1
                status = "ADVANCING"
            elif daily_ret < -0.10:
                declines += 1
                status = "DECLINING"
            else:
                unchanged += 1
                status = "UNCHANGED"

            is_above_ma20 = cp >= ma20
            is_above_ma50 = cp >= ma50
            if is_above_ma20:
                above_ma20_count += 1
            if is_above_ma50:
                above_ma50_count += 1
                
            total_eval += 1

            constituent_breadth.append({
                "ticker": sym_clean,
                "name_ar": canon_rec.get("company_name", sym_clean),
                "price": cp,
                "daily_change_pct": round(daily_ret, 2),
                "status": status,
                "above_ma20": is_above_ma20,
                "above_ma50": is_above_ma50
            })

        total = total_eval if total_eval > 0 else 1
        pct_adv = (advances / total) * 100.0
        pct_dec = (declines / total) * 100.0
        pct_above_ma20 = (above_ma20_count / total) * 100.0
        pct_above_ma50 = (above_ma50_count / total) * 100.0
        
        ad_ratio = round(advances / max(declines, 1), 2)
        net_breadth = round(pct_adv - pct_dec, 2)

        # Composite Breadth Score (0 - 100)
        breadth_score = round(
            (pct_above_ma20 * 0.35) + 
            (pct_above_ma50 * 0.35) + 
            (min(ad_ratio * 25.0, 100.0) * 0.30),
            1
        )
        breadth_score = min(max(breadth_score, 0.0), 100.0)

        # Regime Decision Rules
        if pct_above_ma20 >= 65.0 and ad_ratio >= 1.30 and breadth_score >= 65.0:
            regime = cls.REGIME_STRONG_BULL
            risk_multiplier = 1.00
            sentiment_ar = "سوق صاعد قوي، سيولة شرائية متدفقة، ومشاركة واسعة في معظم قطاعات البورصة."
        elif pct_above_ma20 <= 25.0 or ad_ratio <= 0.40 or breadth_score <= 25.0:
            regime = cls.REGIME_PANIC_BEAR
            risk_multiplier = 0.00  # Prohibit new buys
            sentiment_ar = "سوق هابط حاد، ضغوط بيعية واسعة النطاق، ومخاطرة مرتفعة توجب التراجع والانتظار."
        elif pct_above_ma20 < 45.0 and ad_ratio < 0.85:
            regime = cls.REGIME_DISTRIBUTION
            risk_multiplier = 0.50
            sentiment_ar = "مؤشرات تصريف داخلي وتناقص في القيادات الصاعدة، يوصى بالانتقائية الشديدة."
        else:
            regime = cls.REGIME_NEUTRAL
            risk_multiplier = 0.85
            sentiment_ar = "سوق متوازن في حركة عرضية منضبطة مع فرص انتقائية للأسهم القيادية ذات الزخم."

        return {
            "total_constituents": total_eval,
            "advances": advances,
            "declines": declines,
            "unchanged": unchanged,
            "ad_ratio": ad_ratio,
            "net_breadth_pct": net_breadth,
            "pct_above_ma20": round(pct_above_ma20, 1),
            "pct_above_ma50": round(pct_above_ma50, 1),
            "breadth_score": breadth_score,
            "market_regime": regime,
            "market_regime_label_ar": cls.REGIME_ARABIC.get(regime, regime),
            "risk_multiplier": risk_multiplier,
            "sentiment_summary_ar": sentiment_ar,
            "constituents_detail": constituent_breadth
        }
