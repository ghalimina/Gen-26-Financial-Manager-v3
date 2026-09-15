#!/usr/bin/env python3
import pytest
from core.conformal_prediction_engine import ConformalPredictionEngine


def test_conformal_training_and_monotonicity():
    train_res = ConformalPredictionEngine.train_conformal_models(force_retrain=False)
    assert train_res["is_trained"] is True

    preds = ConformalPredictionEngine.predict_conformal_quantiles("COMI.CA", current_price=141.0)
    assert "quantile_10_downside_pct" in preds
    assert "quantile_50_median_pct" in preds
    assert "quantile_90_upside_pct" in preds

    q10 = preds["quantile_10_downside_pct"]
    q50 = preds["quantile_50_median_pct"]
    q90 = preds["quantile_90_upside_pct"]

    # Monotonicity check
    assert q10 <= q50 <= q90

    # Bounds check
    env = preds["conformal_price_envelope"]
    assert env["pessimistic_q10_price"] <= env["median_q50_price"] <= env["optimistic_q90_price"]
    assert preds["quantile_risk_to_reward"] > 0
    assert "conformal_verdict_ar" in preds


def test_conformal_gating_swdy():
    preds = ConformalPredictionEngine.predict_conformal_quantiles("SWDY.CA", current_price=130.0)
    assert preds["coverage_confidence_pct"] == 90.0
    assert preds["is_conformal_favorable"] in [True, False]
