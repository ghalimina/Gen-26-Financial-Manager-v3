#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_v45_strategic_engines.py — Test Suite for GEN-26 v4.5 Strategic Engines:
1. Breakeven Recovery Solver (Waterfall cash injection & breakeven reduction)
2. EGX Intraday Cairo Session Clock
3. Live News Catalyst Engine
4. Intraday Sniper Alerts Radar
5. Prediction Scorecard & Real-World Accuracy Auditor
6. Startup Cloud Price Sync (Hermetic check)
"""

import pytest
import os
import sys

# Ensure project root is in sys.path
WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.breakeven_recovery_solver import BreakevenRecoverySolver
from core.intraday_session_clock import IntradaySessionClock
from core.live_news_catalyst_engine import LiveNewsCatalystEngine
from core.intraday_sniper_alerts import IntradaySniperAlerts
from core.prediction_scorecard_auditor import PredictionScorecardAuditor
from core.price_sync_service import PriceSyncService
from core.quantum_time_simulator import QuantumTimeSimulator


class TestBreakevenRecoverySolver:
    """Tests for BreakevenRecoverySolver and cascading cash allocation."""

    def test_solve_recovery_default_cash(self):
        plan = BreakevenRecoverySolver.solve_recovery(available_cash=1200.0)
        assert plan["status"] == "success"
        assert plan["available_cash_egp"] == 1200.0
        assert plan["total_stages"] >= 3
        assert "stages" in plan
        assert len(plan["stages"]) > 0

        # Check Stage 1 SWDY
        s1 = plan["stages"][0]
        assert s1["stage_num"] == 1
        assert s1["ticker"] == "SWDY.CA"
        assert s1["new_breakeven_price"] < s1["current_breakeven_price"]
        assert s1["expected_profit_egp"] > 0

    def test_zero_cash_handling(self):
        plan = BreakevenRecoverySolver.solve_recovery(available_cash=0.0)
        assert plan["status"] == "success"
        assert plan["available_cash_egp"] == 0.0
        assert len(plan["stages"]) > 0

    def test_summary_metrics(self):
        plan = BreakevenRecoverySolver.solve_recovery(available_cash=1500.0)
        summary = plan["summary"]
        assert "starting_paper_unrealized_egp" in summary
        assert "total_recycled_profit_generated_egp" in summary
        assert "final_expected_portfolio_profit_egp" in summary
        assert summary["total_recycled_profit_generated_egp"] > 0


class TestIntradaySessionClock:
    """Tests for IntradaySessionClock in Cairo timezone."""

    def test_clock_status_payload(self):
        clock = IntradaySessionClock.get_session_status()
        assert clock["status"] == "SUCCESS"
        assert "Africa/Cairo" in clock["timezone"]
        assert "current_phase" in clock
        assert "phase_name_ar" in clock
        assert "cairo_time" in clock
        assert "countdown_seconds" in clock
        assert isinstance(clock["is_market_open"], bool)

    def test_phase_badges(self):
        clock = IntradaySessionClock.get_session_status()
        assert "badge_color" in clock
        assert "description_ar" in clock


class TestLiveNewsCatalystEngine:
    """Tests for LiveNewsCatalystEngine."""

    def test_get_all_catalysts(self):
        data = LiveNewsCatalystEngine.get_latest_catalysts()
        assert data["status"].upper() == "SUCCESS"
        assert "catalysts" in data
        assert len(data["catalysts"]) > 0

        item = data["catalysts"][0]
        assert "headline_ar" in item
        assert "impact_rating" in item
        assert "impact_score" in item
        assert "actionable_recommendation_ar" in item

    def test_filter_by_ticker(self):
        data = LiveNewsCatalystEngine.get_latest_catalysts(ticker="SWDY.CA")
        assert data["status"].upper() == "SUCCESS"
        assert data["filtered_ticker"] == "SWDY.CA"
        for item in data["catalysts"]:
            assert item["ticker"] == "SWDY.CA"


class TestIntradaySniperAlerts:
    """Tests for IntradaySniperAlerts."""

    def test_get_sniper_triggers(self):
        data = IntradaySniperAlerts.get_active_triggers()
        assert data["status"].upper() == "SUCCESS"
        assert "triggers" in data
        assert len(data["triggers"]) > 0

        trigger = data["triggers"][0]
        assert "ticker" in trigger
        assert "trigger_type" in trigger
        assert "entry_low" in trigger or "current_price" in trigger
        assert "target_price" in trigger
        assert "stop_loss" in trigger
        assert trigger["risk_reward_ratio"] >= 1.5


class TestPredictionScorecardAuditor:
    """Tests for PredictionScorecardAuditor."""

    def test_audit_scorecard_generation(self):
        data = PredictionScorecardAuditor.get_audit_scorecard()
        assert data["status"].upper() == "SUCCESS"
        assert "kpis" in data
        assert "records" in data
        assert len(data["records"]) > 0

        kpis = data["kpis"]
        assert kpis["total_audited_calls"] > 0
        assert 0.0 <= kpis["overall_win_rate_pct"] <= 100.0
        assert kpis["brier_score"] <= 0.30

        rec = data["records"][0]
        assert "ticker" in rec
        assert "status" in rec
        assert "confidence_pct" in rec


class TestQuantumSimulatorV45:
    """Tests for Quantum Simulator v4.5 enhancements."""

    def test_simulator_breakeven_and_all_filter(self):
        res = QuantumTimeSimulator.simulate_trajectory("PORTFOLIO", 20, filter_mode="ALL")
        assert res["status"].upper() == "SUCCESS"
        assert "capital_breakeven_egp" in res["kpis"]
        assert res["kpis"]["capital_breakeven_egp"] == 12466.63
        assert res["kpis"]["open_positions_zero_loss_target_egp"] == 14421.15
        assert len(res["matrix_rows"]) >= 250

    def test_simulator_sector_filter(self):
        res = QuantumTimeSimulator.simulate_trajectory("PORTFOLIO", 20, filter_mode="ALL", sector="العقارات")
        assert res["status"].upper() == "SUCCESS"
        for row in res["matrix_rows"]:
            assert row["sector"] == "العقارات"


class TestStartupPriceSync:
    """Tests for PriceSyncService cloud startup sync."""

    def test_sync_latest_cloud_snapshots_on_startup(self):
        result = PriceSyncService.sync_latest_cloud_snapshots_on_startup()
        assert "status" in result
        assert result["status"] in ["CACHED_READY", "SUCCESS", "NOOP", "FAILED", "success", "noop", "failed"]


class TestImmutableForecastVault:
    """Tests for ImmutableForecastVault and Anti-Lookahead pre-session lock."""

    def test_vault_ledger_batches_and_sha256(self):
        from core.immutable_forecast_vault import ImmutableForecastVault
        ledger = ImmutableForecastVault.load_ledger()
        assert "batches" in ledger
        assert "BATCH_20261023_PRE_SESSION_OCT25" in ledger["batches"]
        b2 = ledger["batches"]["BATCH_20261023_PRE_SESSION_OCT25"]
        assert b2["total_forecasts"] >= 270
        assert "batch_root_hash" in b2
        assert len(b2["batch_root_hash"]) == 64

    def test_stock_vault_card_integrity(self):
        from core.immutable_forecast_vault import ImmutableForecastVault
        card = ImmutableForecastVault.get_stock_vault_card("COMI.CA")
        assert card["ticker"] == "COMI.CA"
        assert card["vault_active"] is True
        assert card["active_batch"]["baseline_price"] == 129.00
        assert card["active_batch"]["predicted_target_5d"] > 129.00
        assert "sha256_hash" in card["active_batch"]
        assert len(card["active_batch"]["sha256_hash"]) == 64

    def test_vault_api_endpoints(self):
        from dashboard.app import app
        client = app.test_client()
        r1 = client.get("/api/audit/immutable_vault")
        assert r1.status_code == 200
        data1 = r1.get_json()
        assert data1["total_batches"] >= 2

        r2 = client.get("/api/audit/immutable_vault/MFPC.CA")
        assert r2.status_code == 200
        data2 = r2.get_json()
        assert data2["ticker"] == "MFPC.CA"
        assert data2["active_batch"]["baseline_price"] == 47.60

