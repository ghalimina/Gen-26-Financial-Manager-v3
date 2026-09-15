#!/usr/bin/env python3
import pytest
from core.historical_pattern_matcher import HistoricalPatternMatcher


def test_pattern_matcher_top_twins():
    twins = HistoricalPatternMatcher.find_historical_twins("COMI.CA", top_k=5)
    assert "top_historical_twins" in twins
    assert len(twins["top_historical_twins"]) <= 5
    assert twins["pattern_window_days"] == 30
    assert twins["forward_horizon_days"] == 10
    assert 0.0 <= twins["historical_win_rate_pct"] <= 100.0
    assert "pattern_bias" in twins
    assert "pattern_verdict_ar" in twins

    first_twin = twins["top_historical_twins"][0]
    assert "matched_ticker" in first_twin
    assert "similarity_pct" in first_twin
    assert "actual_forward_10d_return_pct" in first_twin


def test_pattern_matcher_fallback():
    fallback = HistoricalPatternMatcher._generate_fallback_twins("UNKNOWN.CA", top_k=3)
    assert len(fallback["top_historical_twins"]) == 3
    assert fallback["mean_similarity_pct"] > 80.0
