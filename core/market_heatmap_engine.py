#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# core/market_heatmap_engine.py — EGX 244 Sector Treemap Heatmap Engine
# Calculates hierarchical sector weights, performance distributions, and color maps.
# =============================================================================

import os
import sys
import json
import logging
from typing import Dict, List, Any, Optional

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.egx_universe_loader import EGXUniverseLoader
from core.market_price_service import MarketPriceService

logger = logging.getLogger("GEN26.MarketHeatmapEngine")


class MarketHeatmapEngine:
    """
    Computes hierarchical Treemap Heatmap data for all 244 Egyptian Equities.
    """

    SECTOR_AR_MAP = {
        # English to Canonical Arabic
        "Banking": "الخدمات المالية والبنوك",
        "Financial Services": "الخدمات المالية والبنوك",
        "Real Estate": "التطوير العقاري",
        "Industrial": "الصناعة والمقاولات",
        "Fertilizers": "الموارد الأساسية والكيماويات",
        "Petrochemicals": "الموارد الأساسية والكيماويات",
        "Basic Materials": "الموارد الأساسية والكيماويات",
        "Telecom": "الاتصالات وتكنولوجيا المعلومات",
        "FinTech": "تكنولوجيا المدفوعات",
        "Consumer Staples": "الأغذية والمشروبات والتبغ",
        "Healthcare": "الرعاية الصحية والأدوية",
        "Energy": "الطاقة والخدمات البترولية",
        "Automotive": "السيارات والسلع المعمرة",
        "Tourism": "السياحة والترفيه",
        "General": "قطاعات أخرى متنوعة",

        # Arabic Harmonization & Consolidation
        "الأغذية والمشروبات": "الأغذية والمشروبات والتبغ",
        "السلع الاستهلاكية": "المنسوجات والسلع الاستهلاكية",
        "المنسوجات والسلع المعمرة": "المنسوجات والسلع الاستهلاكية",
        "السيارات والصناعة": "السيارات والسلع المعمرة",
        "الخدمات المالية والاستثمار": "الخدمات المالية والبنوك",
        "الخدمات المالية غير المصرفية": "الخدمات المالية والبنوك",
        "البتروكيماويات والطاقة": "الطاقة والخدمات البترولية",
        "النقل واللوجستيات": "خدمات النقل والشحن واللوجستيات",
        "مواد وبلاستيك": "مواد البناء والتشييد",
        "العقارات والإنشاءات": "التطوير العقاري",
        "الصناعة ومواد البناء": "الصناعة والمقاولات",
        "الموارد الأساسية والأسمدة": "الموارد الأساسية والكيماويات",
        "الأغذية والسلع الاستهلاكية": "الأغذية والمشروبات والتبغ",
        "الطاقة والزيوت المعدنية": "الطاقة والخدمات البترولية"
    }

    @classmethod
    def get_color_for_change(cls, change_pct: float) -> str:
        """Returns HEX / CSS color tailored for financial heatmaps."""
        if change_pct >= 4.0:
            return "#059669"  # Emerald 600
        elif change_pct >= 2.0:
            return "#10b981"  # Green 500
        elif change_pct >= 0.5:
            return "#34d399"  # Light Green 400
        elif change_pct > -0.5:
            return "#475569"  # Slate 600 (Neutral / Flat)
        elif change_pct > -2.0:
            return "#f87171"  # Light Red 400
        elif change_pct > -4.0:
            return "#ef4444"  # Red 500
        else:
            return "#dc2626"  # Dark Red 600

    @classmethod
    def generate_sector_heatmap(cls, include_preferred: bool = False) -> Dict[str, Any]:
        """
        Builds complete hierarchical sector heatmap tree across active Egyptian Equities.
        Consolidates into official EGX 18 sectors and filters duplicate preferred shares.
        """
        from core.price_sync_service import PriceSyncService
        canonical_data = PriceSyncService.load_canonical_prices()
        universe_tickers = EGXUniverseLoader.get_tickers("all")

        sectors_dict: Dict[str, List[Dict[str, Any]]] = {}
        processed_count = 0

        for ticker in universe_tickers:
            # Filter non-tradable preferred / bonus issues unless explicitly requested
            if not include_preferred and ('_P.CA' in ticker or '_B.CA' in ticker):
                continue

            processed_count += 1
            rec = canonical_data.get(ticker)
            if not rec:
                price = 25.0
                prev_close = 25.0
                name_ar = ticker
                sec = "قطاعات أخرى متنوعة"
                chg_pct = 0.0
            else:
                price = float(rec.get("price", 25.0))
                prev_close = float(rec.get("previous_close", price))
                name_ar = rec.get("company_name") or rec.get("name_ar", ticker)
                sec = rec.get("sector") or "قطاعات أخرى متنوعة"
                volume = float(rec.get("volume", 0.0) or 0.0)
                turnover = float(rec.get("turnover_egp", 0.0) or 0.0)
                raw_chg = round(((price - prev_close) / prev_close) * 100.0, 2) if prev_close > 0 else 0.0

                # Mandatory Safety Filter & EGX Circuit Breaker (Cap +-20.0%):
                if abs(raw_chg) > 20.0:
                    logger.warning("Excluding unadjusted/anomalous stock %s (raw_chg=%.2f%%) from heatmap", ticker, raw_chg)
                    continue

                # Exclude untraded stocks with zero volume and zero turnover if price hasn't moved
                if volume <= 0 and turnover <= 0 and price == prev_close:
                    continue

                # Strict mathematical circuit breaker clamp
                chg_pct = max(-20.0, min(20.0, raw_chg))

            sec_ar = cls.SECTOR_AR_MAP.get(sec, sec)
            weight = max(1.0, round(price * 100.0, 1))

            stock_item = {
                "ticker": ticker,
                "name_ar": name_ar,
                "price": price,
                "previous_close": prev_close,
                "change_pct": chg_pct,
                "weight": weight,
                "color": cls.get_color_for_change(chg_pct),
                "is_positive": chg_pct >= 0
            }

            sectors_dict.setdefault(sec_ar, []).append(stock_item)

        # Build sector summary cards
        sector_nodes = []
        advancers_total = 0
        decliners_total = 0
        unchanged_total = 0

        for sec_name, stocks in sectors_dict.items():
            stocks.sort(key=lambda s: s["weight"], reverse=True)
            adv = sum(1 for s in stocks if s["change_pct"] > 0.0)
            dec = sum(1 for s in stocks if s["change_pct"] < 0.0)
            unc = sum(1 for s in stocks if s["change_pct"] == 0.0)
            advancers_total += adv
            decliners_total += dec
            unchanged_total += unc

            mean_return = round(sum(s["change_pct"] for s in stocks) / len(stocks), 2) if stocks else 0.0
            sector_weight = sum(s["weight"] for s in stocks)

            sector_nodes.append({
                "name": sec_name,
                "constituents_count": len(stocks),
                "advancers": adv,
                "decliners": dec,
                "unchanged": unc,
                "mean_return_pct": mean_return,
                "sector_color": cls.get_color_for_change(mean_return),
                "total_weight": sector_weight,
                "stocks": stocks
            })

        sector_nodes.sort(key=lambda x: x["total_weight"], reverse=True)

        return {
            "market": "Egyptian Exchange (EGX)",
            "total_stocks_count": len(universe_tickers),
            "advancers_count": advancers_total,
            "decliners_count": decliners_total,
            "unchanged_count": unchanged_total,
            "advance_decline_ratio": round(advancers_total / max(1, decliners_total), 2),
            "sectors_count": len(sector_nodes),
            "sectors": sector_nodes
        }

    @classmethod
    def calculate_sector_capital_rotation(cls) -> Dict[str, Any]:
        """
        Calculates Institutional Sector Capital Rotation across the last 5 and 10 trading sessions.
        Determines:
        - Each sector's share of total EGX turnover over 5d vs 10d.
        - Flow momentum: INFLOW_ACCUMULATION vs OUTFLOW_COOLING vs STABLE_ROTATION.
        - Spotlight on the user's portfolio pillars (COMI, SWDY, TMGH, PHDC, RAYA).
        """
        import sqlite3
        from core.real_portfolio import RealPortfolioTracker

        db_path = os.path.join(WORKSPACE, "data", "gen26_production.db")
        if not os.path.exists(db_path):
            return {"status": "ERROR", "error": "Database file not found"}

        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        # 1. Fetch the latest 10 distinct market dates
        cur.execute("""
            SELECT DISTINCT market_date 
            FROM historical_daily_bars 
            ORDER BY market_date DESC 
            LIMIT 10
        """)
        dates_rows = cur.fetchall()
        if not dates_rows:
            conn.close()
            return {"status": "ERROR", "error": "No trading bars found"}

        all_dates = [r[0] for r in dates_rows]
        dates_5d = set(all_dates[:5])
        dates_10d = set(all_dates)

        # 2. Fetch bars for these 10 dates
        placeholders = ",".join("?" for _ in all_dates)
        cur.execute(f"""
            SELECT ticker, market_date, close_price, volume 
            FROM historical_daily_bars 
            WHERE market_date IN ({placeholders})
        """, all_dates)
        bars = cur.fetchall()
        conn.close()

        # 3. Aggregate turnover per sector
        sector_turnover_5d: Dict[str, float] = {}
        sector_turnover_10d: Dict[str, float] = {}
        sector_leaders: Dict[str, Dict[str, float]] = {}

        total_market_turnover_5d = 0.0
        total_market_turnover_10d = 0.0

        for ticker, m_date, close_p, vol in bars:
            turnover = float(close_p or 0.0) * float(vol or 0.0)
            if turnover <= 0:
                continue

            sec_raw = RealPortfolioTracker.get_sector(ticker)
            sec_ar = cls.SECTOR_AR_MAP.get(sec_raw, sec_raw)

            # 10d aggregation
            sector_turnover_10d[sec_ar] = sector_turnover_10d.get(sec_ar, 0.0) + turnover
            total_market_turnover_10d += turnover

            # 5d aggregation
            if m_date in dates_5d:
                sector_turnover_5d[sec_ar] = sector_turnover_5d.get(sec_ar, 0.0) + turnover
                total_market_turnover_5d += turnover

                # Track leading stock turnover per sector
                leaders = sector_leaders.setdefault(sec_ar, {})
                leaders[ticker] = leaders.get(ticker, 0.0) + turnover

        # 4. Synthesize rotation telemetry per sector
        sectors_report = []
        portfolio_pillar_sectors = {
            "الخدمات المالية والبنوك": "COMI (CIB)",
            "الصناعة والمقاولات": "SWDY (السويدي إليكتريك)",
            "التطوير العقاري": "TMGH & PHDC (طلعت مصطفى وبالم هيلز)",
            "الاتصالات وتكنولوجيا المعلومات": "RAYA (راية القابضة)"
        }

        for sec_name, t_10d in sector_turnover_10d.items():
            t_5d = sector_turnover_5d.get(sec_name, 0.0)
            share_5d = round((t_5d / max(total_market_turnover_5d, 1.0)) * 100.0, 2)
            share_10d = round((t_10d / max(total_market_turnover_10d, 1.0)) * 100.0, 2)
            momentum_delta = round(share_5d - share_10d, 2)

            if momentum_delta >= 1.5 and share_5d >= 8.0:
                flow_regime = "INFLOW_ACCUMULATION"
                badge_ar = "🟢 تدفق مؤسسي متصاعد (تجميع)"
                action_advice_ar = "القطاع يستقبل سيولة مؤسسية متسارعة؛ يُنصح بالتمسك بالمراكز والتركيز على قادة القطاع."
            elif momentum_delta <= -1.5:
                flow_regime = "OUTFLOW_COOLING"
                badge_ar = "🟡 تراجع مؤقت للسيولة (تبريد / جني أرباح)"
                action_advice_ar = "هدوء في السيولة الداخلة؛ مناسب للتمركز الهادئ أو انتظار إشارات ارتداد."
            else:
                flow_regime = "STABLE_ROTATION"
                badge_ar = "⚪ دوران سيولة متزن"
                action_advice_ar = "حركة السيولة مستقرة ومتوازنة مع المعدلات المعتادة."

            # Top leader stock
            sec_ldrs = sector_leaders.get(sec_name, {})
            top_stock = max(sec_ldrs.items(), key=lambda x: x[1])[0] if sec_ldrs else "N/A"
            top_stock_name = RealPortfolioTracker.get_company_name(top_stock)

            sectors_report.append({
                "sector_name_ar": sec_name,
                "turnover_5d_egp": round(t_5d, 2),
                "turnover_10d_egp": round(t_10d, 2),
                "turnover_share_5d_pct": share_5d,
                "turnover_share_10d_pct": share_10d,
                "momentum_delta_pct": momentum_delta,
                "flow_regime": flow_regime,
                "badge_ar": badge_ar,
                "action_advice_ar": action_advice_ar,
                "leading_stock_ticker": top_stock,
                "leading_stock_name_ar": top_stock_name,
                "portfolio_pillar_note": portfolio_pillar_sectors.get(sec_name, None)
            })

        # Sort by 5d turnover share descending
        sectors_report.sort(key=lambda s: s["turnover_share_5d_pct"], reverse=True)

        top_inflow_sector = next((s for s in sectors_report if s["flow_regime"] == "INFLOW_ACCUMULATION"), sectors_report[0] if sectors_report else None)
        headline_summary = (
            f"⚡ السيولة المؤسسية تتركز هذا الأسبوع في: قطاع {top_inflow_sector['sector_name_ar']} "
            f"بنسبة {top_inflow_sector['turnover_share_5d_pct']:.1f}% من سيولة السوق (بقيادة {top_inflow_sector['leading_stock_name_ar']})"
            if top_inflow_sector else "سيولة البورصة تدور بنمط متوازن عبر القطاعات القيادية."
        )

        return {
            "status": "SUCCESS",
            "as_of": all_dates[0] if all_dates else datetime.date.today().isoformat(),
            "lookback_sessions": {"recent": 5, "baseline": 10},
            "dates_evaluated": all_dates,
            "total_market_turnover_5d_egp": round(total_market_turnover_5d, 2),
            "total_market_turnover_10d_egp": round(total_market_turnover_10d, 2),
            "headline_summary_ar": headline_summary,
            "top_accumulated_sector": top_inflow_sector["sector_name_ar"] if top_inflow_sector else "",
            "sectors_count": len(sectors_report),
            "sectors_rotation": sectors_report
        }
