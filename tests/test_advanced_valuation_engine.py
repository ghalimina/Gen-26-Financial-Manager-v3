#!/usr/bin/env python3
import pytest
from core.valuation_engine import ValuationEngine


def test_legacy_valuation_methods():
    val = ValuationEngine.evaluate_valuation(current_price=100.0, pe_ratio=8.0, pb_ratio=1.5, dividend_yield_pct=5.0)
    assert "valuation_score" in val
    assert val["valuation_score"] > 50.0

    scenarios = ValuationEngine.compute_fair_value_scenarios(current_price=100.0, eps=12.0)
    assert scenarios["base_case"] == round(12.0 * 12.0, 2)
    assert scenarios["bear_case"] < scenarios["base_case"] < scenarios["bull_case"]


def test_dcf_valuation_industrial():
    # Test DCF on a non-financial stock
    dcf = ValuationEngine.calculate_dcf_valuation(ticker="SWDY.CA", current_price=130.0)
    assert dcf["model"] == "DISCOUNTED_FREE_CASH_FLOW_5Y"
    assert dcf["intrinsic_fair_value"] > 0
    assert dcf["wacc_pct"] >= 14.0
    assert len(dcf["projections"]) == 5
    assert "margin_of_safety_pct" in dcf


def test_residual_income_valuation_banking():
    # Test RIM on a banking stock
    rim = ValuationEngine.calculate_residual_income_valuation(ticker="COMI.CA", current_price=141.0)
    assert rim["model"] == "RESIDUAL_INCOME_MODEL_EBO"
    assert rim["intrinsic_fair_value"] > 0
    assert rim["cost_of_equity_pct"] >= 19.0
    assert len(rim["projections"]) == 5


def test_comprehensive_valuation_routing():
    # Banking routing check
    res_comi = ValuationEngine.evaluate_comprehensive_valuation("COMI.CA", current_price=141.0)
    assert res_comi["is_financial_sector"] is True
    assert "EBO" in res_comi["primary_valuation_model"]

    # Industrial routing check
    res_swdy = ValuationEngine.evaluate_comprehensive_valuation("SWDY.CA", current_price=130.0)
    assert res_swdy["is_financial_sector"] is False
    assert "DISCOUNTED_FREE_CASH_FLOW" in res_swdy["primary_valuation_model"]
    assert "scenario_bounds" in res_swdy
