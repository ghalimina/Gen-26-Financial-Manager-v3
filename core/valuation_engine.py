#!/usr/bin/env python3
# =============================================================================
# core/valuation_engine.py — GEN-26 Valuation & Fair Value Scenario Engine
# Evaluates multi-ratio valuation and computes scenario-based Fair Value
# ranges (Bear Case, Base Case, Bull Case) with Margin of Safety metrics.
# =============================================================================

from typing import Dict, Any, Optional


class ValuationEngine:
    """
    Computes relative valuation scores and scenario-based fair value price envelopes.
    """

    @staticmethod
    def evaluate_valuation(
        current_price: float,
        pe_ratio: Optional[float] = None,
        pb_ratio: Optional[float] = None,
        dividend_yield_pct: Optional[float] = None,
        sector_avg_pe: float = 12.0,
        sector_avg_pb: float = 2.0
    ) -> Dict[str, Any]:
        """
        Computes a Valuation Score (0 to 100) where higher means more attractively valued (cheaper).
        """
        pe_score = 50.0
        if pe_ratio is not None and pe_ratio > 0:
            if pe_ratio <= sector_avg_pe * 0.7:
                pe_score = 90.0
            elif pe_ratio <= sector_avg_pe:
                pe_score = 70.0 + (sector_avg_pe - pe_ratio) / (sector_avg_pe * 0.3) * 20.0
            elif pe_ratio <= sector_avg_pe * 1.5:
                pe_score = 40.0 + (sector_avg_pe * 1.5 - pe_ratio) / (sector_avg_pe * 0.5) * 30.0
            else:
                pe_score = max(10.0, 40.0 - (pe_ratio - sector_avg_pe * 1.5) * 2.0)

        pb_score = 50.0
        if pb_ratio is not None and pb_ratio > 0:
            if pb_ratio <= sector_avg_pb * 0.8:
                pb_score = 85.0
            elif pb_ratio <= sector_avg_pb:
                pb_score = 65.0
            else:
                pb_score = max(15.0, 65.0 - (pb_ratio - sector_avg_pb) * 15.0)

        div_score = 50.0
        if dividend_yield_pct is not None and dividend_yield_pct > 0:
            div_score = min(100.0, 40.0 + dividend_yield_pct * 7.5)

        composite_val_score = round((pe_score * 0.50) + (pb_score * 0.30) + (div_score * 0.20), 1)

        return {
            "valuation_score": composite_val_score,
            "pe_ratio": pe_ratio,
            "pb_ratio": pb_ratio,
            "dividend_yield_pct": dividend_yield_pct,
            "sector_pe_benchmark": sector_avg_pe,
            "sector_pb_benchmark": sector_avg_pb
        }

    @staticmethod
    def compute_fair_value_scenarios(
        current_price: float,
        eps: Optional[float] = None,
        bvps: Optional[float] = None,
        base_pe: float = 12.0
    ) -> Dict[str, Any]:
        """
        Generates conservative scenario-based fair value envelopes:
        - Bear Case: Conservative multiple (-20% discount)
        - Base Case: Sector baseline valuation
        - Bull Case: Premium multiple (+25% expansion)
        """
        cp = max(float(current_price), 0.01)

        if eps is not None and eps > 0:
            base_fv = round(eps * base_pe, 2)
            bear_fv = round(eps * (base_pe * 0.80), 2)
            bull_fv = round(eps * (base_pe * 1.25), 2)
        elif bvps is not None and bvps > 0:
            base_fv = round(bvps * 1.8, 2)
            bear_fv = round(bvps * 1.3, 2)
            bull_fv = round(bvps * 2.3, 2)
        else:
            # Fallback estimation based on price anchor
            base_fv = round(cp * 1.10, 2)
            bear_fv = round(cp * 0.85, 2)
            bull_fv = round(cp * 1.30, 2)

        upside_pct = round(((base_fv - cp) / cp) * 100.0, 1)
        downside_pct = round(((bear_fv - cp) / cp) * 100.0, 1)

        return {
            "bear_case": bear_fv,
            "base_case": base_fv,
            "bull_case": bull_fv,
            "current_price": cp,
            "base_upside_pct": upside_pct,
            "bear_downside_pct": downside_pct,
            "margin_of_safety_pct": round(max(0.0, ((base_fv - cp) / base_fv) * 100.0), 1) if base_fv > 0 else 0.0
        }
