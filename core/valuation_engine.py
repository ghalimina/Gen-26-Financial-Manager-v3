#!/usr/bin/env python3
# =============================================================================
# core/valuation_engine.py — GEN-26 Valuation & Fair Value Scenario Engine
# Evaluates multi-ratio valuation, automated Discounted Free Cash Flow (DCF),
# Edwards-Bell-Ohlson Residual Income Model (RIM) for Egyptian banking & financials,
# and institutional Margin of Safety (MoS) gating.
# =============================================================================

import math
from typing import Dict, Any, Optional


class ValuationEngine:
    """
    Institutional Valuation Engine:
    1. Multi-Ratio relative valuation (P/E, P/B, Dividend Yield vs Sector benchmarks).
    2. Discounted Free Cash Flow (DCF) with Egypt-calibrated WACC (Rf=19.00%, ERP=8.5%).
    3. Edwards-Bell-Ohlson Residual Income Model (RIM) tailored for banking/financial institutions.
    4. Conservative scenario envelopes & Margin of Safety gating (>= 20%).
    """

    # SSoT Egypt Macro Parameters for Cost of Capital
    CBE_RISK_FREE_RATE_PCT = 19.00
    EQUITY_RISK_PREMIUM_PCT = 8.50
    CORPORATE_TAX_RATE_PCT = 22.50
    TERMINAL_GROWTH_RATE_PCT = 6.00  # Nominal long-term GDP growth anchor in EGP

    FINANCIAL_SECTORS = [
        "بنوك", "بنوك وتسهيلات ائتمانية", "خدمات مالية غير مصرفية",
        "مدفوعات إلكترونية وخدمات مالية", "بنوك وخدمات مالية"
    ]

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

    @classmethod
    def calculate_dcf_valuation(
        cls,
        ticker: str,
        current_price: Optional[float] = None,
        beta: Optional[float] = None,
        debt_to_equity: Optional[float] = None,
        roe_pct: Optional[float] = None,
        pe_ratio: Optional[float] = None,
        eps: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Automated 5-Year Discounted Free Cash Flow (FCFF) Model for Egyptian Non-Financial Equities:
        - Calculates WACC using CBE Risk-Free Rate + Beta * ERP.
        - Employs Gordon Growth terminal value (g=6.0%).
        - Compares Intrinsic Value against Market Price.
        """
        from core.live_fundamentals_engine import LiveFundamentalsEngine
        from core.portfolio_correlation_engine import PortfolioCorrelationEngine
        from core.market_price_service import MarketPriceService

        sym = ticker.upper().strip()
        cp = current_price or MarketPriceService.get_latest_price(sym)
        if not cp or cp <= 0:
            cp = 100.0

        fund = LiveFundamentalsEngine.get_stock_fundamentals(sym)
        b_val = beta if beta is not None else float(PortfolioCorrelationEngine.get_stock_beta(sym) or 1.10)
        de_val = debt_to_equity if debt_to_equity is not None else float(fund.get("debt_to_equity", 0.60))
        roe_val = roe_pct if roe_pct is not None else float(fund.get("roe_pct", 22.0))
        pe_val = pe_ratio if pe_ratio is not None else float(fund.get("pe_ratio", 8.5))
        eps_val = eps if eps is not None else (cp / pe_val if pe_val > 0 else cp * 0.12)

        # 1. Cost of Equity (CAPM)
        rf = cls.CBE_RISK_FREE_RATE_PCT / 100.0
        erp = cls.EQUITY_RISK_PREMIUM_PCT / 100.0
        ke = rf + (b_val * erp)

        # 2. Cost of Debt (Post-Tax)
        tax = cls.CORPORATE_TAX_RATE_PCT / 100.0
        kd = (rf + 0.02) * (1.0 - tax)  # Average corporate spread of 200 bps above corridor

        # 3. WACC Calculation
        # Capital structure weights from Debt/Equity: E/(D+E) = 1/(1+DE), D/(D+E) = DE/(1+DE)
        we = 1.0 / (1.0 + max(de_val, 0.05))
        wd = 1.0 - we
        wacc = max((we * ke) + (wd * kd), 0.14)  # Floor at 14% nominal in EGP

        # 4. Cash Flow Estimation: Initial normalized FCFF per share derived from EPS & OCF
        ocf_to_ni = float(fund.get("ocf_to_ni_ratio", 1.15))
        initial_fcff = max(eps_val * ocf_to_ni * 0.70, cp * 0.05)  # Reinvestment retention 30%

        # 5. Projection: 5-year transition from growth to terminal
        g_terminal = cls.TERMINAL_GROWTH_RATE_PCT / 100.0
        g_near = min(max((roe_val / 100.0) * 0.60, g_terminal), 0.22)  # Sustainable growth capped at 22%

        pv_cash_flows = 0.0
        cf_projection = []
        curr_cf = initial_fcff

        for yr in range(1, 6):
            # Fade growth rate linearly toward terminal growth
            fade_g = g_near - ((g_near - g_terminal) * (yr / 5.0))
            curr_cf = curr_cf * (1.0 + fade_g)
            discount_factor = 1.0 / ((1.0 + wacc) ** yr)
            pv_cf = curr_cf * discount_factor
            pv_cash_flows += pv_cf
            cf_projection.append({
                "year": yr,
                "projected_fcff": round(curr_cf, 2),
                "growth_pct": round(fade_g * 100.0, 1),
                "discount_factor": round(discount_factor, 3),
                "pv_fcff": round(pv_cf, 2)
            })

        # 6. Terminal Value (Gordon Growth Model)
        terminal_value = (curr_cf * (1.0 + g_terminal)) / max(wacc - g_terminal, 0.03)
        pv_terminal_value = terminal_value / ((1.0 + wacc) ** 5)

        # 7. Intrinsic Equity Value per Share
        intrinsic_fv = round(pv_cash_flows + pv_terminal_value, 2)
        upside_pct = round(((intrinsic_fv - cp) / cp) * 100.0, 1)

        # 8. Margin of Safety
        mos_pct = round(max(0.0, ((intrinsic_fv - cp) / intrinsic_fv) * 100.0), 1) if intrinsic_fv > 0 else 0.0
        is_safe = mos_pct >= 20.0

        return {
            "model": "DISCOUNTED_FREE_CASH_FLOW_5Y",
            "model_name_ar": "نموذج التدفقات النقدية الحرة المخصومة (Auto-DCF)",
            "ticker": sym,
            "current_price": cp,
            "intrinsic_fair_value": intrinsic_fv,
            "fair_value_per_share": intrinsic_fv,
            "wacc_pct": round(wacc * 100.0, 2),
            "cost_of_equity_pct": round(ke * 100.0, 2),
            "cost_of_debt_pct": round(kd * 100.0, 2),
            "initial_fcff_per_share": round(initial_fcff, 2),
            "terminal_growth_pct": round(g_terminal * 100.0, 1),
            "pv_5y_cash_flows": round(pv_cash_flows, 2),
            "pv_terminal_value": round(pv_terminal_value, 2),
            "terminal_value_share_pct": round((pv_terminal_value / intrinsic_fv) * 100.0, 1) if intrinsic_fv > 0 else 0.0,
            "upside_potential_pct": upside_pct,
            "margin_of_safety_pct": mos_pct,
            "is_margin_of_safety_satisfied": is_safe,
            "valuation_verdict": "UNDERVALUED_BUY" if is_safe else ("FAIRLY_VALUED" if upside_pct >= 0 else "OVERVALUED_RISK"),
            "projections": cf_projection
        }

    @classmethod
    def calculate_residual_income_valuation(
        cls,
        ticker: str,
        current_price: Optional[float] = None,
        beta: Optional[float] = None,
        bvps: Optional[float] = None,
        roe_pct: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Edwards-Bell-Ohlson Residual Income Model (RIM) Tailored for Banking & Financial Institutions:
        - Designed for CIB, QNBA, ADIB, CIEB, HRHO where DCF is structurally invalid.
        - Calculates Equity Charge: Ke = Rf + Beta * ERP.
        - Residual Income = (ROE - Ke) * Book_Value.
        """
        from core.live_fundamentals_engine import LiveFundamentalsEngine
        from core.portfolio_correlation_engine import PortfolioCorrelationEngine
        from core.market_price_service import MarketPriceService

        sym = ticker.upper().strip()
        cp = current_price or MarketPriceService.get_latest_price(sym)
        if not cp or cp <= 0:
            cp = 141.0

        fund = LiveFundamentalsEngine.get_stock_fundamentals(sym)
        b_val = beta if beta is not None else float(PortfolioCorrelationEngine.get_stock_beta(sym) or 1.15)
        roe_val = roe_pct if roe_pct is not None else float(fund.get("roe_pct", 28.5))
        
        # Estimate Book Value Per Share from P/B or fallback
        pb_val = float(fund.get("pb_ratio", 2.1))
        if bvps is not None and bvps > 0:
            book_val = bvps
        elif pb_val > 0:
            book_val = cp / pb_val
        else:
            book_val = cp * 0.45

        # 1. Cost of Equity (CAPM)
        rf = cls.CBE_RISK_FREE_RATE_PCT / 100.0
        erp = cls.EQUITY_RISK_PREMIUM_PCT / 100.0
        ke = rf + (b_val * erp)

        # 2. 5-Year Residual Income Stream
        g_terminal = cls.TERMINAL_GROWTH_RATE_PCT / 100.0
        pv_residual_incomes = 0.0
        curr_bv = book_val
        ri_projection = []

        roe_decimal = roe_val / 100.0

        for yr in range(1, 6):
            # Fade ROE towards long-term cost of capital
            fade_roe = roe_decimal - ((roe_decimal - (ke + 0.04)) * (yr / 5.0))
            ri_per_share = (fade_roe - ke) * curr_bv
            discount_factor = 1.0 / ((1.0 + ke) ** yr)
            pv_ri = ri_per_share * discount_factor
            pv_residual_incomes += pv_ri

            ri_projection.append({
                "year": yr,
                "projected_bvps": round(curr_bv, 2),
                "expected_roe_pct": round(fade_roe * 100.0, 1),
                "residual_income": round(ri_per_share, 2),
                "pv_residual_income": round(pv_ri, 2)
            })
            # Retain ~65% of net income into book value growth
            retention_rate = 0.65
            curr_bv = curr_bv + (curr_bv * fade_roe * retention_rate)

        # 3. Terminal Residual Income (Gordon Residual Model)
        last_ri = ri_projection[-1]["residual_income"]
        if last_ri > 0 and ke > g_terminal:
            terminal_ri = (last_ri * (1.0 + g_terminal)) / (ke - g_terminal)
            pv_terminal_ri = terminal_ri / ((1.0 + ke) ** 5)
        else:
            pv_terminal_ri = 0.0

        # 4. Total Intrinsic Fair Value = Beginning Book Value + PV(Residual Incomes) + PV(Terminal RI)
        intrinsic_fv = round(book_val + pv_residual_incomes + pv_terminal_ri, 2)
        upside_pct = round(((intrinsic_fv - cp) / cp) * 100.0, 1)
        mos_pct = round(max(0.0, ((intrinsic_fv - cp) / intrinsic_fv) * 100.0), 1) if intrinsic_fv > 0 else 0.0
        is_safe = mos_pct >= 20.0

        return {
            "model": "RESIDUAL_INCOME_MODEL_EBO",
            "model_name_ar": "نموذج الدخل المتبقي للقطاع المصرفي والمالي (EBO-RIM)",
            "ticker": sym,
            "current_price": cp,
            "book_value_per_share": round(book_val, 2),
            "intrinsic_fair_value": intrinsic_fv,
            "fair_value_per_share": intrinsic_fv,
            "cost_of_equity_pct": round(ke * 100.0, 2),
            "baseline_roe_pct": round(roe_val, 1),
            "pv_5y_residual_incomes": round(pv_residual_incomes, 2),
            "pv_terminal_residual_income": round(pv_terminal_ri, 2),
            "upside_potential_pct": upside_pct,
            "margin_of_safety_pct": mos_pct,
            "is_margin_of_safety_satisfied": is_safe,
            "valuation_verdict": "UNDERVALUED_BUY" if is_safe else ("FAIRLY_VALUED" if upside_pct >= 0 else "OVERVALUED_RISK"),
            "projections": ri_projection
        }

    @classmethod
    def evaluate_comprehensive_valuation(
        cls,
        ticker: str,
        current_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Unified Multi-Method Valuation Pipeline:
        - Dynamically selects RIM for banking/finance or DCF for non-financials.
        - Synthesizes Multiples, Intrinsic DCF/RIM, and Scenario Envelopes.
        """
        from core.egx_universe_loader import EGXUniverseLoader
        from core.market_price_service import MarketPriceService

        sym = ticker.upper().strip()
        cp = current_price or MarketPriceService.get_latest_price(sym)
        if not cp or cp <= 0:
            cp = 100.0

        info = EGXUniverseLoader.get_stock_info(sym) or {}
        sector = info.get("sector", "عام")

        is_financial = any(s in sector for s in cls.FINANCIAL_SECTORS) or sym in ["COMI.CA", "QNBA.CA", "ADIB.CA", "CIEB.CA", "FAIT.CA", "HRHO.CA"]

        if is_financial:
            intrinsic_res = cls.calculate_residual_income_valuation(sym, current_price=cp)
        else:
            intrinsic_res = cls.calculate_dcf_valuation(sym, current_price=cp)

        fv = intrinsic_res["intrinsic_fair_value"]
        mos_pct = intrinsic_res["margin_of_safety_pct"]

        # Arabic verdict label
        if mos_pct >= 25.0:
            verdict_ar = "🟢 فرصة استثمارية بقيمة عادلة ممتازة وهامش أمان مرتفع (> 25%)"
            badge = "DEEP_VALUE"
        elif mos_pct >= 15.0:
            verdict_ar = "🟢 سعر تداول جذاب أقل من القيمة العادلة"
            badge = "UNDERVALUED"
        elif mos_pct >= 0.0:
            verdict_ar = "🟡 تداول عند حدود القيمة العادلة المرجحة"
            badge = "FAIR_VALUE"
        else:
            verdict_ar = "🔴 السهم يتداول بعلاوة سعرية تفوق قيمته العادلة (تضخم تقييم)"
            badge = "OVERVALUED"

        return {
            "ticker": sym,
            "current_price": cp,
            "sector": sector,
            "is_financial_sector": is_financial,
            "primary_valuation_model": intrinsic_res["model"],
            "primary_model_name_ar": intrinsic_res["model_name_ar"],
            "intrinsic_fair_value": fv,
            "margin_of_safety_pct": mos_pct,
            "is_margin_of_safety_satisfied": intrinsic_res["is_margin_of_safety_satisfied"],
            "upside_potential_pct": intrinsic_res["upside_potential_pct"],
            "verdict_badge": badge,
            "verdict_ar": verdict_ar,
            "intrinsic_details": intrinsic_res,
            "scenario_bounds": {
                "bear_fair_value": round(fv * 0.85, 2),
                "base_fair_value": fv,
                "bull_fair_value": round(fv * 1.25, 2)
            }
        }
