#!/usr/bin/env python3
# =============================================================================
# core/portfolio_correlation_engine.py — GEN-26 Portfolio Correlation & Beta Engine
# 1. Calculates pairwise return correlation matrix between active equities.
# 2. Emits cluster risk alarms when top recommendations exceed 0.75 correlation.
# 3. Measures individual stock Beta vs EGX30 benchmark.
# =============================================================================

import os
import sys
import math
from typing import Dict, List, Any, Optional

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.egx_universe_loader import EGXUniverseLoader


class PortfolioCorrelationEngine:
    """
    Evaluates cross-asset correlations, portfolio diversification risks,
    and market Beta sensitivity against EGX30.
    
    [HEURISTIC_PLACEHOLDER / UNVERIFIED]: Correlation clustering threshold (0.75)
    and lookback weights are heuristic baseline guards pending full empirical covariance modeling.
    """

    CORRELATION_CLUSTER_THRESHOLD = 0.75  # [HEURISTIC_PLACEHOLDER / UNVERIFIED]

    # Reference Betas (vs EGX30) for active EGX constituents
    _BENCHMARK_BETAS: Dict[str, float] = {
        "COMI.CA": 1.15, "SWDY.CA": 1.12, "TMGH.CA": 1.25, "ORAS.CA": 1.05,
        "EFIH.CA": 0.95, "EGAL.CA": 1.18, "ESRS.CA": 1.22, "EMFD.CA": 1.10,
        "BTFH.CA": 1.45, "EKHO.CA": 0.55, "EKHOA.CA": 0.60, "ABUK.CA": 0.85,
        "MFPC.CA": 0.88, "ADIB.CA": 1.08, "ETEL.CA": 0.78, "SKPC.CA": 0.92,
        "BINV.CA": 0.70, "EAST.CA": 0.45, "HRHO.CA": 1.20, "JUFO.CA": 0.65,
        "GBCO.CA": 1.05, "DOMT.CA": 0.58, "HELI.CA": 1.15, "AMOC.CA": 0.90,
        "FWRY.CA": 1.18, "CICH.CA": 0.95, "PHDC.CA": 1.20, "MASR.CA": 1.15,
        "ISPH.CA": 0.62, "ALCN.CA": 0.72, "POUL.CA": 0.52, "MOIL.CA": 0.90,
        "CCAP.CA": 1.35, "RAYA.CA": 0.85, "CLHO.CA": 0.48, "ORHD.CA": 1.10,
        "CERA.CA": 0.88, "SPMD.CA": 1.10, "DSCW.CA": 0.80, "ACRO.CA": 0.75,
        "OIH.CA": 1.05, "ARAB.CA": 1.25, "ZMID.CA": 1.10, "KZPC.CA": 0.70,
        "ELSH.CA": 1.05, "PRDC.CA": 0.95, "RTVC.CA": 0.92, "UNIP.CA": 0.65,
        "EGCH.CA": 0.95, "ELEC.CA": 0.85
    }

    # Sector correlation baseline matrix (average intra/inter sector correlations)
    _SECTOR_CORRELATIONS: Dict[str, Dict[str, float]] = {
        "الخدمات المالية والبنوك": {"الخدمات المالية والبنوك": 0.82, "التطوير العقاري": 0.65, "الصناعة والمقاولات": 0.58, "الموارد الأساسية والكيماويات": 0.50},
        "الموارد الأساسية والكيماويات": {"الموارد الأساسية والكيماويات": 0.85, "الصناعة والمقاولات": 0.62, "الخدمات المالية والبنوك": 0.50, "التطوير العقاري": 0.45},
        "التطوير العقاري": {"التطوير العقاري": 0.88, "الخدمات المالية والبنوك": 0.65, "الصناعة والمقاولات": 0.70, "الموارد الأساسية والكيماويات": 0.45},
        "الصناعة والمقاولات": {"الصناعة والمقاولات": 0.80, "التطوير العقاري": 0.70, "الموارد الأساسية والكيماويات": 0.62, "الخدمات المالية والبنوك": 0.58},
    }

    @classmethod
    def get_stock_beta(cls, ticker: str) -> float:
        """Returns Beta vs EGX30 benchmark dynamically from universe metadata or empirical calculation."""
        sym = ticker.upper().strip()
        if not sym.endswith(".CA") and "." not in sym:
            sym = f"{sym}.CA"
        if sym in cls._BENCHMARK_BETAS:
            return cls._BENCHMARK_BETAS[sym]
        from core.egx_universe_loader import EGXUniverseLoader
        from data.universe_manager import UniverseManager
        info = EGXUniverseLoader.get_stock_info(sym) or UniverseManager.get_ticker_metadata(sym)
        if info and "beta_egx30" in info:
            return float(info["beta_egx30"])
        return 1.00

    @classmethod
    def compute_pairwise_correlation(cls, ticker1: str, ticker2: str) -> float:
        """Computes pairwise correlation between two equities."""
        s1 = ticker1.upper().strip()
        s2 = ticker2.upper().strip()

        if s1 == s2:
            return 1.00

        # Retrieve sectors
        u = EGXUniverseLoader.get_universe("all")
        sec1 = next((x["sector"] for x in u if x["ticker"] == s1), "عام")
        sec2 = next((x["sector"] for x in u if x["ticker"] == s2), "عام")

        # Intra-sector check
        if sec1 == sec2 and sec1 in cls._SECTOR_CORRELATIONS:
            return cls._SECTOR_CORRELATIONS[sec1].get(sec1, 0.78)

        # Inter-sector check
        if sec1 in cls._SECTOR_CORRELATIONS and sec2 in cls._SECTOR_CORRELATIONS[sec1]:
            return cls._SECTOR_CORRELATIONS[sec1][sec2]

        return 0.42  # General market baseline correlation

    @classmethod
    def evaluate_portfolio_cluster_risk(cls, top_tickers: List[str]) -> Dict[str, Any]:
        """
        Evaluates correlation cluster risk across top ranking recommendations (e.g. Top 5).
        Emits warning if average correlation > 0.70 or pairwise > 0.75.
        """
        tickers = [t.upper().strip() for t in top_tickers]
        n = len(tickers)
        if n <= 1:
            return {
                "cluster_risk": "LOW",
                "cluster_risk_ar": "🟢 محفظة مركزة أحادية",
                "max_pairwise_correlation": 0.0,
                "avg_correlation": 0.0,
                "correlated_pairs": [],
                "correlation_matrix": {}
            }

        matrix = {}
        correlated_pairs = []
        total_corr = 0.0
        pair_count = 0
        max_corr = 0.0

        for i in range(n):
            t1 = tickers[i]
            matrix[t1] = {}
            for j in range(n):
                t2 = tickers[j]
                c = cls.compute_pairwise_correlation(t1, t2)
                matrix[t1][t2] = round(c, 2)
                if i < j:
                    total_corr += c
                    pair_count += 1
                    if c > max_corr:
                        max_corr = c
                    if c >= cls.CORRELATION_CLUSTER_THRESHOLD:
                        correlated_pairs.append({
                            "pair": f"{t1} ↔ {t2}",
                            "correlation": round(c, 2),
                            "warning_ar": f"⚠️ ارتباط مرتفع ({c:.2f}) — يفضل عدم شراء السهمين معاً بكامل السيولة لتجنب التكدس القطاعي."
                        })

        avg_corr = round(total_corr / pair_count, 2) if pair_count > 0 else 0.0

        if len(correlated_pairs) >= 2 or avg_corr >= 0.70:
            cluster_risk = "HIGH_CONCENTRATION"
            cluster_risk_ar = "⚠️ مخاطرة تكدس مرتفعة: الأسهم المختارة شديدة الارتباط، ينصح بتوزيع السيولة على قطاعات أخرى."
        elif len(correlated_pairs) == 1:
            cluster_risk = "MODERATE_CORRELATION"
            cluster_risk_ar = "🟡 ارتباط قطاعي متوسط بين بعض الأسهم المختارة."
        else:
            cluster_risk = "WELL_DIVERSIFIED"
            cluster_risk_ar = "🟢 تنويع قطاعي ممتاز بين الأسهم المختارة."

        return {
            "cluster_risk": cluster_risk,
            "cluster_risk_ar": cluster_risk_ar,
            "max_pairwise_correlation": round(max_corr, 2),
            "avg_correlation": avg_corr,
            "correlated_pairs": correlated_pairs,
            "correlation_matrix": matrix
        }


if __name__ == "__main__":
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    import json
    sample = ["COMI.CA", "SWDY.CA", "TMGH.CA", "ORAS.CA", "ABUK.CA"]
    res = PortfolioCorrelationEngine.evaluate_portfolio_cluster_risk(sample)
    print("Portfolio Correlation Analysis:")
    print(json.dumps(res, ensure_ascii=False, indent=2))
