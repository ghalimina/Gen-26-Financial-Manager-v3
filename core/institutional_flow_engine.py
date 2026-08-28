#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# core/institutional_flow_engine.py — Institutional & Foreign Flow Radar
# 1. Volume Z-Score & Smart Money Block Accumulation Radar.
# 2. Daily Foreign & Institutional Net Flow Tracker (>50M EGP Blue-Chip Boost).
# 3. MSCI & FTSE Semi-Annual Rebalancing Calendar (May & November Reviews).
# 4. Equity Risk Premium (ERP) vs CBE Risk-Free Yield Benchmark.
# =============================================================================

import os
import sys
import math
import datetime
from typing import Dict, List, Any, Optional

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.market_price_service import MarketPriceService
from core.egx_universe_loader import EGXUniverseLoader


class InstitutionalFlowEngine:
    """
    Analyzes trading volume anomalies, foreign institutional net flows,
    index rebalancing catalysts (MSCI/FTSE), and Equity Risk Premium (ERP).
    """

    FLOW_INSTITUTIONAL_ACCUMULATION = "INSTITUTIONAL_ACCUMULATION"
    FLOW_RETAIL_DISTRIBUTION = "RETAIL_DISTRIBUTION"
    FLOW_MODERATE_INFLOW = "MODERATE_INFLOW"
    FLOW_MODERATE_OUTFLOW = "MODERATE_OUTFLOW"
    FLOW_ROUTINE_LIQUIDITY = "ROUTINE_LIQUIDITY"
    FLOW_ILLIQUID_DRYUP = "ILLIQUID_DRYUP"

    FLOW_ARABIC = {
        FLOW_INSTITUTIONAL_ACCUMULATION: "🟢 تجميع وتدفق مؤسسي ضخم (Institutional Accumulation)",
        FLOW_RETAIL_DISTRIBUTION: "🔴 تصريف وجني أرباح مكثف (Retail Distribution)",
        FLOW_MODERATE_INFLOW: "🟢 تدفق شرائي متوازن (Moderate Inflow)",
        FLOW_MODERATE_OUTFLOW: "🟡 تدفق بيعي هادئ (Moderate Outflow)",
        FLOW_ROUTINE_LIQUIDITY: "⚪ سيولة يومية اعتيادية (Routine Liquidity)",
        FLOW_ILLIQUID_DRYUP: "⚠️ انحسار سيولة وضعف تداول (Illiquid Dryup)"
    }

    # Reference 20-day Average Daily Volume (shares) & Volatility for EGX constituents
    _ADV_BENCHMARKS = {
        "COMI.CA": {"adv20_shares": 2500000, "sigma_ratio": 0.35, "adv20_turnover_egp": 342500000.0},
        "SWDY.CA": {"adv20_shares": 1800000, "sigma_ratio": 0.38, "adv20_turnover_egp": 208800000.0},
        "TMGH.CA": {"adv20_shares": 1650000, "sigma_ratio": 0.40, "adv20_turnover_egp": 161205000.0},
        "ORAS.CA": {"adv20_shares": 35000,   "sigma_ratio": 0.45, "adv20_turnover_egp": 26565000.0},
        "ETEL.CA": {"adv20_shares": 1050000, "sigma_ratio": 0.35, "adv20_turnover_egp": 120634500.0},
        "EGAL.CA": {"adv20_shares": 210000,  "sigma_ratio": 0.42, "adv20_turnover_egp": 69300000.0},
        "ABUK.CA": {"adv20_shares": 750000,  "sigma_ratio": 0.36, "adv20_turnover_egp": 56640000.0},
        "MFPC.CA": {"adv20_shares": 980000,  "sigma_ratio": 0.38, "adv20_turnover_egp": 47530000.0},
        "ADIB.CA": {"adv20_shares": 850000,  "sigma_ratio": 0.40, "adv20_turnover_egp": 45407000.0},
        "EAST.CA": {"adv20_shares": 1200000, "sigma_ratio": 0.32, "adv20_turnover_egp": 43224000.0},
        "JUFO.CA": {"adv20_shares": 650000,  "sigma_ratio": 0.35, "adv20_turnover_egp": 17361500.0},
        "GBCO.CA": {"adv20_shares": 1400000, "sigma_ratio": 0.42, "adv20_turnover_egp": 41048000.0},
        "AUTO.CA": {"adv20_shares": 1400000, "sigma_ratio": 0.42, "adv20_turnover_egp": 41048000.0},
        "HRHO.CA": {"adv20_shares": 3200000, "sigma_ratio": 0.36, "adv20_turnover_egp": 84160000.0},
        "EFIH.CA": {"adv20_shares": 2100000, "sigma_ratio": 0.37, "adv20_turnover_egp": 51450000.0},
        "FWRY.CA": {"adv20_shares": 4800000, "sigma_ratio": 0.38, "adv20_turnover_egp": 92208000.0},
        "DOMT.CA": {"adv20_shares": 550000,  "sigma_ratio": 0.40, "adv20_turnover_egp": 8360000.0},
        "PHDC.CA": {"adv20_shares": 5200000, "sigma_ratio": 0.40, "adv20_turnover_egp": 78780000.0},
        "ISPH.CA": {"adv20_shares": 950000,  "sigma_ratio": 0.35, "adv20_turnover_egp": 12369000.0},
        "EMFD.CA": {"adv20_shares": 4200000, "sigma_ratio": 0.40, "adv20_turnover_egp": 49602000.0},
        "AMOC.CA": {"adv20_shares": 1900000, "sigma_ratio": 0.38, "adv20_turnover_egp": 21565000.0},
        "HELI.CA": {"adv20_shares": 3800000, "sigma_ratio": 0.42, "adv20_turnover_egp": 29222000.0},
        "RAYA.CA": {"adv20_shares": 1250000, "sigma_ratio": 0.45, "adv20_turnover_egp": 8750000.0},
        "CCAP.CA": {"adv20_shares": 5800000, "sigma_ratio": 0.44, "adv20_turnover_egp": 32480000.0},
        "BTFH.CA": {"adv20_shares": 8500000, "sigma_ratio": 0.45, "adv20_turnover_egp": 25330000.0}
    }

    BLUE_CHIP_TICKERS = {"COMI.CA", "SWDY.CA", "TMGH.CA", "EKHO.CA", "ETEL.CA", "ABUK.CA"}

    # =========================================================================
    # 1. STOCK LEVEL VOLUME & FLOW EVALUATION
    # =========================================================================

    @classmethod
    def evaluate_stock_flow(
        cls,
        ticker: str,
        current_volume: Optional[int] = None,
        current_price: Optional[float] = None,
        open_price: Optional[float] = None,
        previous_close: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calculates Volume Z-Score, detects institutional accumulation/distribution,
        and provides flow alpha impact (+/- contribution).
        """
        sym_clean = ticker.upper().strip()
        if not sym_clean.endswith(".CA") and "." not in sym_clean:
            sym_clean = f"{sym_clean}.CA"

        from core.egx_universe_loader import EGXUniverseLoader
        from data.universe_manager import UniverseManager
        info = EGXUniverseLoader.get_stock_info(sym_clean) or UniverseManager.get_ticker_metadata(sym_clean)
        adv_egp = float(info.get("adv20_egp", 10000000.0)) if info else 10000000.0
        cp_nominal = float(info.get("nominal_price", 10.0)) if info else 10.0
        adv_shares = max(int(adv_egp / max(cp_nominal, 0.01)), 10000)

        bm = cls._ADV_BENCHMARKS.get(sym_clean, {
            "adv20_shares": adv_shares,
            "sigma_ratio": 0.35,
            "adv20_turnover_egp": adv_egp
        })

        adv20 = bm["adv20_shares"]
        sigma = adv20 * bm["sigma_ratio"]

        canon = MarketPriceService.CANONICAL_PRICES.get(sym_clean, {})
        cp = current_price or canon.get("price")
        if cp is None or cp <= 0:
            cp = 10.0
        op = open_price or (cp * 0.998)
        prev = previous_close or canon.get("previous_close") or (cp * 0.995)

        vol = current_volume if current_volume is not None else int(adv20 * 1.15)
        turnover = vol * cp

        z_score = round((vol - adv20) / sigma, 2) if sigma > 0 else 0.0

        daily_return_pct = round(((cp - prev) / prev) * 100.0, 2) if prev > 0 else 0.0
        intraday_return_pct = round(((cp - op) / op) * 100.0, 2) if op > 0 else 0.0

        if z_score >= 2.0 and (daily_return_pct > 0.5 or intraday_return_pct > 0.2):
            flow_regime = cls.FLOW_INSTITUTIONAL_ACCUMULATION
            flow_score = 92.0
            flow_alpha_impact = +0.18
            desc_ar = f"ارتفاع غير عادي في أحجام التداول (Z-Score = {z_score:+.2f}) مع ضغط شرائي صاعد يشير لتجميع مؤسسي قوي."
        elif z_score >= 2.0 and (daily_return_pct < -0.5 or intraday_return_pct < -0.2):
            flow_regime = cls.FLOW_RETAIL_DISTRIBUTION
            flow_score = 25.0
            flow_alpha_impact = -0.20
            desc_ar = f"ارتفاع حاد في أحجام التداول (Z-Score = {z_score:+.2f}) مصحوباً بهبوط سعري يشير لتصريف مؤسسي وجني أرباح."
        elif z_score >= 0.5 and daily_return_pct >= 0:
            flow_regime = cls.FLOW_MODERATE_INFLOW
            flow_score = 75.0
            flow_alpha_impact = +0.08
            desc_ar = f"تدفقات نقدية إيجابية معتدلة (Z-Score = {z_score:+.2f}) مع تماسك سعري مستمر."
        elif z_score >= 0.5 and daily_return_pct < 0:
            flow_regime = cls.FLOW_MODERATE_OUTFLOW
            flow_score = 45.0
            flow_alpha_impact = -0.07
            desc_ar = f"تراجعات بيعية هادئة وضغوط تسييل طفيفة (Z-Score = {z_score:+.2f})."
        elif z_score < -1.0:
            flow_regime = cls.FLOW_ILLIQUID_DRYUP
            flow_score = 40.0
            flow_alpha_impact = -0.05
            desc_ar = f"انخفاض ملحوظ في أحجام التنفيذ اليومية (Z-Score = {z_score:+.2f}) وركود مؤقت في السيولة."
        else:
            flow_regime = cls.FLOW_ROUTINE_LIQUIDITY
            flow_score = 60.0
            flow_alpha_impact = +0.02
            desc_ar = f"نشاط سيولة اعتيادي ومتوازن حول المتوسط الطبيعي (Z-Score = {z_score:+.2f})."

        return {
            "ticker": sym_clean,
            "current_volume": vol,
            "adv20_shares": adv20,
            "turnover_egp": round(turnover, 2),
            "adv20_turnover_egp": round(bm["adv20_turnover_egp"], 2),
            "volume_z_score": z_score,
            "is_volume_spike": z_score >= 2.0,
            "flow_regime": flow_regime,
            "flow_regime_label_ar": cls.FLOW_ARABIC.get(flow_regime, flow_regime),
            "flow_score": flow_score,
            "flow_alpha_impact": flow_alpha_impact,
            "description_ar": desc_ar
        }

    # =========================================================================
    # 2. MARKET-WIDE INSTITUTIONAL FLOW TELEMETRY & BLUE-CHIP BOOST
    # =========================================================================

    @classmethod
    def get_institutional_flow_telemetry(
        cls,
        foreign_net_egp: Optional[float] = None,
        arab_net_egp: Optional[float] = None,
        egyptian_inst_net_egp: Optional[float] = None,
        retail_net_egp: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Returns structured daily market flow breakdown.
        If foreign or domestic institutions are aggressive net buyers (> +50M EGP),
        flags active blue-chip composite scoring boost.
        """
        f_net = foreign_net_egp if foreign_net_egp is not None else +68_500_000.0
        a_net = arab_net_egp if arab_net_egp is not None else -12_300_000.0
        e_inst_net = egyptian_inst_net_egp if egyptian_inst_net_egp is not None else +85_400_000.0
        ret_net = retail_net_egp if retail_net_egp is not None else -(f_net + a_net + e_inst_net)

        total_inst_net = round(f_net + a_net + e_inst_net, 2)
        is_aggressive_accumulation = (f_net > 50_000_000.0) or (e_inst_net > 50_000_000.0)

        # Smart money sentiment index (0 to 100)
        smart_money_index = round(min(100.0, max(0.0, 50.0 + (total_inst_net / 3_000_000.0))), 1)

        if is_aggressive_accumulation:
            boost_status_ar = "🟢 تفعيل علاوة تدفقات المؤسسات (+5% إلى +8%) لأسهم القياديات (COMI, SWDY, TMGH, EKHO, ETEL, ABUK)"
            blue_chip_boost_factor = 1.065
        else:
            boost_status_ar = "⚪ تدفقات مؤسسية اعتيادية - لا توجد علاوة استثنائية نشطة"
            blue_chip_boost_factor = 1.000

        return {
            "foreign_net_flow_egp": f_net,
            "arab_net_flow_egp": a_net,
            "egyptian_institutions_net_flow_egp": e_inst_net,
            "retail_net_flow_egp": round(ret_net, 2),
            "total_institutions_net_flow_egp": total_inst_net,
            "smart_money_index": smart_money_index,
            "is_aggressive_accumulation": is_aggressive_accumulation,
            "blue_chip_boost_factor": blue_chip_boost_factor,
            "boosted_blue_chips": list(cls.BLUE_CHIP_TICKERS),
            "summary_ar": boost_status_ar,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    # =========================================================================
    # 3. MSCI & FTSE INDEX REBALANCING RADAR
    # =========================================================================

    @classmethod
    def get_index_rebalancing_calendar(cls, current_date_str: Optional[str] = None) -> Dict[str, Any]:
        """
        Tracks MSCI and FTSE Emerging Markets semi-annual index rebalancing cycles
        (May and November reviews) with advance accumulation warnings.
        """
        today = datetime.date.today()
        if current_date_str:
            try:
                today = datetime.date.fromisoformat(current_date_str)
            except Exception:
                pass

        year = today.year
        may_rebal = datetime.date(year, 5, 31)
        nov_rebal = datetime.date(year, 11, 30)

        # Determine next rebalancing target
        if today <= may_rebal:
            next_rebal = may_rebal
            review_name = f"May {year} Semi-Annual Index Review"
        elif today <= nov_rebal:
            next_rebal = nov_rebal
            review_name = f"November {year} Semi-Annual Index Review"
        else:
            next_rebal = datetime.date(year + 1, 5, 31)
            review_name = f"May {year + 1} Semi-Annual Index Review"

        days_remaining = (next_rebal - today).days
        is_rebalancing_window = 0 <= days_remaining <= 18
        accumulate_alert = 5 <= days_remaining <= 21

        affected_equities = [
            {"ticker": "COMI.CA", "index": "MSCI Standard & FTSE EM", "weight_trend": "INCREASE", "catalyst_ar": "زيادة الوزن النسبي لمصر"},
            {"ticker": "TMGH.CA", "index": "MSCI Standard & FTSE EM", "weight_trend": "INCREASE", "catalyst_ar": "تدفقات أجنبية متوقعة"},
            {"ticker": "SWDY.CA", "index": "MSCI Standard & FTSE EM", "weight_trend": "MAINTAIN", "catalyst_ar": "تثبيت الوزن النسبي"},
            {"ticker": "ABUK.CA", "index": "FTSE Emerging Markets", "weight_trend": "MAINTAIN", "catalyst_ar": "سيولة صندوقية مستقرة"},
            {"ticker": "FWRY.CA", "index": "MSCI Small Cap", "weight_trend": "INCREASE", "catalyst_ar": "مرشح للترقية للمؤشر القياسي"}
        ]

        if is_rebalancing_window:
            guidance_ar = (
                f"🚨 نافذة مراجعة مؤشرات MSCI / FTSE نشطة (متبقي {days_remaining} يوماً). "
                f"توقع قفزات سيولة وتداولات مزاد إغلاق ضخمة على الأسهم القيادية."
            )
        else:
            guidance_ar = (
                f"مراجعة المؤشرات الدولية القادمة: {review_name} ({next_rebal.isoformat()}) "
                f"— متبقي {days_remaining} يوماً على موعد تنفيذ المراجعة."
            )

        return {
            "next_review_name": review_name,
            "next_rebalancing_date": next_rebal.isoformat(),
            "days_remaining": days_remaining,
            "is_rebalancing_window": is_rebalancing_window,
            "accumulate_alert": accumulate_alert,
            "affected_equities": affected_equities,
            "guidance_ar": guidance_ar
        }

    # =========================================================================
    # 4. EQUITY RISK PREMIUM (ERP) VS RISK-FREE YIELD BENCHMARK
    # =========================================================================

    @classmethod
    def calculate_equity_risk_premium(
        cls,
        egx30_pe_ratio: float = 8.80,
        cbe_risk_free_rate_pct: float = 19.75
    ) -> Dict[str, Any]:
        """
        Calculates the Equity Risk Premium (ERP):
        ERP = EGX30 Earnings Yield (1 / PE) - Risk Free Rate (or Net Equivalent).
        Provides macro asset allocation guidance (Equities vs Cash / T-Bills).
        """
        earnings_yield_pct = round((1.0 / max(egx30_pe_ratio, 0.01)) * 100.0, 2)
        
        # Egyptian T-Bills / Corridor Net Equivalent Benchmark
        rf_rate = cbe_risk_free_rate_pct
        erp_pct = round(earnings_yield_pct - (rf_rate * 0.70), 2)  # Compare vs net yield after tax or real yield

        if erp_pct >= 2.0:
            regime = "EQUITY_EXPANSION_FAVORABLE"
            verdict_ar = (
                f"🟢 علاوة مخاطر الأسهم جذابة ({erp_pct:+.2f}%): العائد الربحي للأسهم ({earnings_yield_pct:.2f}%) "
                f"يتفوق على العائد الخالي من المخاطر؛ يوصى بزيادة وزن الأسهم إلى 80-90%."
            )
            recommended_equity_pct = 85.0
        elif erp_pct >= -2.0:
            regime = "BALANCED_NEUTRAL"
            verdict_ar = (
                f"🟡 علاوة مخاطر الأسهم متوازنة ({erp_pct:+.2f}%): يوصى بتوزيع استثماري متوازن 60% أسهم و 40% كاش/أذون خزانة."
            )
            recommended_equity_pct = 60.0
        else:
            regime = "CASH_PRESERVATION_FAVORABLE"
            verdict_ar = (
                f"🔴 علاوة مخاطر الأسهم سالبة ({erp_pct:+.2f}%): أسعار الفائدة المرتفعة تشكل منافسة قوية للأسهم؛ "
                f"يوصى بالتحفظ ورفع الاحتياطي النقدي إلى 50%."
            )
            recommended_equity_pct = 50.0

        return {
            "egx30_pe_ratio": egx30_pe_ratio,
            "egx30_earnings_yield_pct": earnings_yield_pct,
            "cbe_risk_free_rate_pct": rf_rate,
            "equity_risk_premium_pct": erp_pct,
            "allocation_regime": regime,
            "recommended_equity_pct": recommended_equity_pct,
            "recommended_cash_pct": round(100.0 - recommended_equity_pct, 1),
            "verdict_ar": verdict_ar
        }

    # =========================================================================
    # 5. UNIVERSE SCAN
    # =========================================================================

    @classmethod
    def scan_universe_flows(cls) -> Dict[str, Any]:
        """Scans the active universe for volume anomalies and institutional block accumulation."""
        active = EGXUniverseLoader.get_active_universe()
        results = {}
        accumulation_list = []
        distribution_list = []

        for ticker in active.keys():
            flow_data = cls.evaluate_stock_flow(ticker)
            results[ticker] = flow_data
            if flow_data["flow_regime"] == cls.FLOW_INSTITUTIONAL_ACCUMULATION:
                accumulation_list.append(ticker)
            elif flow_data["flow_regime"] == cls.FLOW_RETAIL_DISTRIBUTION:
                distribution_list.append(ticker)

        return {
            "total_scanned": len(results),
            "accumulation_count": len(accumulation_list),
            "distribution_count": len(distribution_list),
            "institutional_accumulation_tickers": accumulation_list,
            "retail_distribution_tickers": distribution_list,
            "flows": results
        }
