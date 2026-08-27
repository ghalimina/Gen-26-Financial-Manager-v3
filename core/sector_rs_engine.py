#!/usr/bin/env python3
# =============================================================================
# core/sector_rs_engine.py — GEN-26 Dynamic Sector Relative Strength (RS) Engine
# Aggregates EGX sector indices, computes stock-vs-sector Relative Strength (RS),
# and identifies Sector Leaders (قائد القطاع) vs Sector Laggards (متراجع عن القطاع).
# =============================================================================

from typing import Dict, List, Any, Optional
from core.market_price_service import MarketPriceService
from core.egx_universe_loader import EGXUniverseLoader


class SectorRelativeStrengthEngine:
    """
    Computes real-time sector indices, individual equity relative strength ratios,
    and identifies sector leadership vs lagging momentum.
    """

    SECTOR_LEADER = "SECTOR_LEADER"
    SECTOR_PERFORMER = "SECTOR_PERFORMER"
    SECTOR_LAGGARD = "SECTOR_LAGGARD"

    LEADERSHIP_ARABIC = {
        SECTOR_LEADER: "🟢 قائد القطاع وزخم صاعد (Leader)",
        SECTOR_PERFORMER: "🟡 متوافق مع أداء القطاع (Performer)",
        SECTOR_LAGGARD: "🔴 متراجع عن أداء القطاع (Laggard)"
    }

    # Macro EGX Sector Clustering
    SECTORS_TAXONOMY = {
        "BANKING_FINTECH": {
            "name_ar": "البنوك والخدمات المالية",
            "name_en": "Banking & Financial Services",
            "tickers": ["COMI.CA", "ADIB.CA", "HRHO.CA", "CICH.CA", "BTFH.CA"]
        },
        "INDUSTRIAL_MATERIALS": {
            "name_ar": "الصناعة والموارد الأساسية",
            "name_en": "Industrial & Materials",
            "tickers": ["SWDY.CA", "EGAL.CA", "ABUK.CA", "MFPC.CA", "ESRS.CA"]
        },
        "REAL_ESTATE_CONSTRUCTION": {
            "name_ar": "التطوير العقاري والإنشاءات",
            "name_en": "Real Estate & Construction",
            "tickers": ["TMGH.CA", "ORAS.CA", "PHDC.CA", "EMFD.CA", "HELI.CA"]
        },
        "TECH_TELECOM_FINTECH": {
            "name_ar": "الاتصالات وتكنولوجيا المدفوعات",
            "name_en": "Telecom, Tech & Fintech",
            "tickers": ["ETEL.CA", "FWRY.CA", "EFIH.CA", "RAYA.CA"]
        },
        "CONSUMER_FOOD": {
            "name_ar": "الأغذية والاستهلاك",
            "name_en": "Consumer & Food",
            "tickers": ["EAST.CA", "JUFO.CA", "DOMT.CA", "GBCO.CA", "POUL.CA", "ISPH.CA"]
        },
        "ENERGY_LOGISTICS": {
            "name_ar": "الطاقة واللوجستيات",
            "name_en": "Energy & Logistics",
            "tickers": ["AMOC.CA", "ALCN.CA", "MOIL.CA", "EKHO.CA"]
        }
    }

    @classmethod
    def analyze_sector_relative_strength(
        cls,
        current_prices: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Calculates sector performance, stock relative strength spreads,
        and classifies all constituents into Leaders, Performers, or Laggards.
        """
        prices = current_prices or {}
        active_stocks = EGXUniverseLoader.get_active_universe()

        # Step 1: Calculate individual stock returns
        stock_returns = {}
        for sym, meta in active_stocks.items():
            sym_clean = sym.upper().strip()
            try:
                cp = prices.get(sym_clean) if prices else MarketPriceService.get_latest_price(sym_clean)
            except Exception:
                canon = MarketPriceService.CANONICAL_PRICES.get(sym_clean, {})
                cp = canon.get("price")

            if cp is None or cp <= 0:
                continue

            canon = MarketPriceService.CANONICAL_PRICES.get(sym_clean, {})
            prev_close = canon.get("previous_close") or (cp * 0.995)
            ret_pct = ((cp - prev_close) / prev_close) * 100.0 if (prev_close and prev_close > 0) else 0.0
            
            stock_returns[sym_clean] = {
                "price": cp,
                "prev_close": prev_close,
                "return_pct": ret_pct,
                "name_ar": meta.get("name_ar", sym_clean),
                "sector_cluster": None
            }

        # Step 2: Aggregate Sector Performance
        sectors_summary = {}
        ticker_to_sector = {}

        for sec_key, sec_data in cls.SECTORS_TAXONOMY.items():
            sec_tickers = sec_data["tickers"]
            valid_returns = []
            advances = 0
            declines = 0

            for t in sec_tickers:
                ticker_to_sector[t] = sec_key
                if t in stock_returns:
                    stock_returns[t]["sector_cluster"] = sec_key
                    r = stock_returns[t]["return_pct"]
                    valid_returns.append(r)
                    if r > 0.10:
                        advances += 1
                    elif r < -0.10:
                        declines += 1

            avg_return = sum(valid_returns) / len(valid_returns) if valid_returns else 0.0
            sec_breadth_score = (advances / max(len(valid_returns), 1)) * 100.0

            sectors_summary[sec_key] = {
                "sector_id": sec_key,
                "name_ar": sec_data["name_ar"],
                "name_en": sec_data["name_en"],
                "constituents_count": len(sec_tickers),
                "average_return_pct": round(avg_return, 2),
                "advances": advances,
                "declines": declines,
                "sector_breadth_pct": round(sec_breadth_score, 1),
                "is_sector_bullish": avg_return > 0.10
            }

        # Rank Sectors by Performance
        ranked_sectors = sorted(
            sectors_summary.values(),
            key=lambda s: s["average_return_pct"],
            reverse=True
        )
        for idx, sec in enumerate(ranked_sectors, 1):
            sec["rank"] = idx

        # Step 3: Compute Relative Strength for each stock vs its Sector
        stock_analysis = {}
        leaders_list = []
        laggards_list = []

        for sym, data in stock_returns.items():
            sec_key = ticker_to_sector.get(sym, "BANKING_FINTECH")
            sec_info = sectors_summary.get(sec_key, {
                "name_ar": "عام",
                "average_return_pct": 0.0
            })
            sec_ret = sec_info["average_return_pct"]
            stock_ret = data["return_pct"]

            rs_ratio = (1.0 + stock_ret / 100.0) / (1.0 + sec_ret / 100.0) if (1.0 + sec_ret / 100.0) > 0 else 1.0
            rs_spread = round(stock_ret - sec_ret, 2)

            if rs_spread >= 1.0 or rs_ratio >= 1.01:
                leadership = cls.SECTOR_LEADER
                rs_score = round(min(75.0 + rs_spread * 10.0, 98.0), 1)
                leaders_list.append(sym)
            elif rs_spread <= -1.0 or rs_ratio <= 0.99:
                leadership = cls.SECTOR_LAGGARD
                rs_score = round(max(50.0 + rs_spread * 8.0, 15.0), 1)
                laggards_list.append(sym)
            else:
                leadership = cls.SECTOR_PERFORMER
                rs_score = round(65.0 + rs_spread * 5.0, 1)

            stock_analysis[sym] = {
                "ticker": sym,
                "name_ar": data["name_ar"],
                "sector_name_ar": sec_info["name_ar"],
                "stock_return_pct": round(stock_ret, 2),
                "sector_return_pct": round(sec_ret, 2),
                "rs_spread_pct": rs_spread,
                "rs_ratio": round(rs_ratio, 4),
                "leadership_tier": leadership,
                "leadership_label_ar": cls.LEADERSHIP_ARABIC.get(leadership, leadership),
                "relative_strength_score": rs_score,
                "is_leader": leadership == cls.SECTOR_LEADER
            }

        return {
            "sectors_count": len(cls.SECTORS_TAXONOMY),
            "top_performing_sector": ranked_sectors[0]["name_ar"] if ranked_sectors else "عام",
            "bottom_performing_sector": ranked_sectors[-1]["name_ar"] if ranked_sectors else "عام",
            "sectors_ranking": ranked_sectors,
            "leaders_count": len(leaders_list),
            "laggards_count": len(laggards_list),
            "leaders": leaders_list,
            "laggards": laggards_list,
            "stocks_relative_strength": stock_analysis
        }

    @classmethod
    def get_stock_sector_rs(cls, ticker: str) -> Dict[str, Any]:
        """Convenience query for a single stock's relative strength profile."""
        clean = ticker.upper().strip()
        if not clean.endswith(".CA") and "." not in clean:
            clean = f"{clean}.CA"
        full = cls.analyze_sector_relative_strength()
        return full["stocks_relative_strength"].get(clean, {
            "ticker": clean,
            "sector_name_ar": "عام",
            "rs_spread_pct": 0.0,
            "rs_ratio": 1.0,
            "leadership_tier": cls.SECTOR_PERFORMER,
            "leadership_label_ar": cls.LEADERSHIP_ARABIC[cls.SECTOR_PERFORMER],
            "relative_strength_score": 65.0,
            "is_leader": False
        })
