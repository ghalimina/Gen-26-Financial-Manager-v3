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
        "Banking": "الخدمات المالية والبنوك",
        "Financial Services": "الخدمات المالية والبنوك",
        "Real Estate": "العقارات والإنشاءات",
        "Industrial": "الصناعة ومواد البناء",
        "Fertilizers": "الموارد الأساسية والأسمدة",
        "Petrochemicals": "الموارد الأساسية والأسمدة",
        "Basic Materials": "الموارد الأساسية والأسمدة",
        "Telecom": "الاتصالات وتكنولوجيا المعلومات",
        "FinTech": "الاتصالات وتكنولوجيا المعلومات",
        "Consumer Staples": "الأغذية والسلع الاستهلاكية",
        "Healthcare": "الرعاية الصحية والأدوية",
        "Energy": "الطاقة والزيوت المعدنية",
        "Automotive": "السيارات والسلع المعمرة",
        "Tourism": "السياحة والترفيه",
        "General": "قطاعات أخرى متنوعة"
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
    def generate_sector_heatmap(cls) -> Dict[str, Any]:
        """
        Builds complete hierarchical sector heatmap tree across the 244 EGX universe.
        """
        from core.price_sync_service import PriceSyncService
        canonical_data = PriceSyncService.load_canonical_prices()
        universe_tickers = EGXUniverseLoader.get_tickers("all")

        sectors_dict: Dict[str, List[Dict[str, Any]]] = {}

        for ticker in universe_tickers:
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
                chg_pct = round(((price - prev_close) / prev_close) * 100.0, 2) if prev_close > 0 else 0.0

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
