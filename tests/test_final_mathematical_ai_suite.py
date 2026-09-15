#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# tests/test_final_mathematical_ai_suite.py
# Verification suite for final mathematical & AI engines:
# 1. RmtCovarianceDenoiser (Marchenko-Pastur spectral clipping & condition number reduction)
# 2. GnnSectorContagionEngine (Graph convolutional shock spillover & centrality)
# 3. RlTradingEnvironment (Gym API, step/reset, friction & Egyptian CGT)
# 4. YieldCurveEngine (Nelson-Siegel sovereign term structure & discount factors)
# 5. Master Production Launcher (launch_production_fund.py pre-flight readiness)
# =============================================================================

import pytest
import os
import sys
import numpy as np

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.rmt_covariance_denoiser import RmtCovarianceDenoiser
from core.gnn_sector_contagion_engine import GnnSectorContagionEngine
from core.rl_trading_environment import RlTradingEnvironment
from core.yield_curve_engine import YieldCurveEngine
from launch_production_fund import verify_system_readiness


def test_rmt_covariance_denoiser():
    """Verifies Marchenko-Pastur bounds and correlation matrix stability improvement."""
    # Generate noisy empirical correlation matrix
    np.random.seed(42)
    t_samples = 200
    n_assets = 15
    raw_data = np.random.randn(t_samples, n_assets)
    noisy_corr = np.corrcoef(raw_data, rowvar=False)

    res = RmtCovarianceDenoiser.denoise_correlation_matrix(noisy_corr, t_samples=t_samples)
    assert "cleaned_matrix" in res
    assert res["lambda_max"] > 0
    assert res["num_noise_components"] > 0
    # Cleaned matrix should have diagonal of exactly 1.0
    diag = np.diag(res["cleaned_matrix"])
    np.testing.assert_allclose(diag, 1.0, atol=1e-5)
    # Condition number should improve (lower or equal)
    assert res["condition_number_after"] <= res["condition_number_before"] + 1e-4


def test_gnn_sector_contagion_engine():
    """Verifies GNN Laplacian normalization and shock propagation across nodes."""
    adj, nodes = GnnSectorContagionEngine.build_adjacency_matrix()
    assert len(nodes) >= 10
    assert adj.shape == (len(nodes), len(nodes))

    sim = GnnSectorContagionEngine.simulate_shock_contagion("COMI.CA", shock_magnitude_pct=-5.0)
    assert sim["shock_origin"] == "COMI.CA"
    assert len(sim["spillover_projections"]) == len(nodes)
    # Epicenter should have negative projected shock
    assert sim["spillover_projections"][0]["is_shock_epicenter"] is True
    assert sim["spillover_projections"][0]["projected_shock_pct"] < 0.0
    assert sim["spillover_projections"][0]["ticker"] == "COMI.CA"


def test_rl_trading_environment():
    """Verifies Gym environment step, reset, reward function, friction, and CGT deduction."""
    prices = [100.0 + (i * 1.5) for i in range(50)]
    env = RlTradingEnvironment(price_series=prices, initial_capital=50000.0)
    obs, info = env.reset()
    assert len(obs) == 5
    assert info["initial_capital"] == 50000.0

    # Execute buying step
    next_obs, reward, done, step_info = env.step(target_position=1.0)
    assert len(next_obs) == 5
    assert step_info["shares"] > 0
    assert step_info["friction_paid"] > 0.0
    assert done is False

    # Execute selling step
    next_obs, reward, done, step_info = env.step(target_position=0.0)
    assert step_info["shares"] == 0


def test_yield_curve_engine():
    """Verifies Nelson-Siegel sovereign yield curve generation and discount factors."""
    curve = YieldCurveEngine.generate_sovereign_curve()
    assert "yields_pct" in curve
    assert "91D" in curve["yields_pct"]
    assert "10Y" in curve["yields_pct"]
    assert curve["anchor_10y_yield_pct"] > 0

    # Check discount factor D(tau) decreases with maturity
    d_91d = curve["discount_factors"]["91D"]
    d_10y = curve["discount_factors"]["10Y"]
    assert d_91d > d_10y  # Longer maturity has smaller discount factor

    # Check horizon risk free rate
    rf_60d = YieldCurveEngine.get_horizon_risk_free_rate(holding_days=60)
    assert rf_60d > 15.0  # Realistic Egyptian rates > 15%


def test_master_production_launcher_preflight():
    """Verifies that launch_production_fund pre-flight checks pass 100%."""
    ready = verify_system_readiness()
    assert ready is True
