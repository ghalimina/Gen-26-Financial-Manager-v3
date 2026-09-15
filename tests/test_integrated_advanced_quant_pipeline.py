#!/usr/bin/env python3
import pytest
from core.deep_quant_fusion_engine import DeepQuantFusionEngine
from core.multi_horizon_engine import MultiHorizonEngine
from dashboard.app import app


def test_deep_quant_fusion_dcf_dynamic():
    feats = DeepQuantFusionEngine.extract_48_features("COMI.CA", current_price=141.0)
    raw = feats["raw_features"]
    assert "dcf_margin_of_safety_pct" in raw
    assert "dcf_fair_value_ratio" in raw
    assert isinstance(raw["dcf_margin_of_safety_pct"], (int, float))
    assert isinstance(raw["dcf_fair_value_ratio"], (int, float))
    assert raw["dcf_fair_value_ratio"] > 0


def test_multi_horizon_integrated_quant_layer():
    analysis = MultiHorizonEngine.get_stock_multi_horizon_analysis("COMI.CA")
    assert analysis is not None
    assert "comprehensive_valuation" in analysis
    assert "conformal_quantiles" in analysis
    assert "multi_agent_debate" in analysis
    assert "historical_twins" in analysis
    assert "advanced_quant_summary" in analysis

    summary = analysis["advanced_quant_summary"]
    assert "intrinsic_fair_value" in summary
    assert "quantile_risk_to_reward" in summary
    assert "conformal_envelope" in summary
    assert "debate_verdict_ar" in summary
    assert "historical_twin_win_rate_pct" in summary


def test_flask_advanced_quant_endpoints():
    client = app.test_client()

    # 1. Standard stock dossier enriched
    resp1 = client.get("/api/stocks/COMI.CA")
    assert resp1.status_code == 200
    data1 = resp1.get_json()
    assert "comprehensive_valuation" in data1
    assert "conformal_quantiles" in data1
    assert "multi_agent_debate" in data1

    # 2. Dedicated advanced quant endpoint
    resp2 = client.get("/api/stocks/COMI.CA/advanced-quant")
    assert resp2.status_code == 200
    data2 = resp2.get_json()
    assert data2["status"] == "SUCCESS"
    assert "valuation" in data2
    assert "conformal_quantiles" in data2
    assert "multi_agent_debate" in data2
    assert "historical_twins" in data2
    assert data2["ticker"] == "COMI.CA"
