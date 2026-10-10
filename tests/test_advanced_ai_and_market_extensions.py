#!/usr/bin/env python3
# =============================================================================
# tests/test_advanced_ai_and_market_extensions.py — Comprehensive Test Suite
# Validates the 5 Advanced Qualitative Engines, Flask Endpoints, and Numeric Invariants:
# 1. Closed-Loop Error Attribution (AISelfLearningFeedback)
# 2. Online Regime-Adaptive Weights (RegimeAdaptiveWeights)
# 3. Auction Trap & Spoofing Detector (AuctionTrapDetector)
# 4. Institutional Flow Radar & Smart Money (InstitutionalFlowTracker)
# 5. Interactive Telegram Copilot (TelegramInteractiveCopilot)
# 6. REST API Endpoints & Thndr Card Enrichment
# =============================================================================

import os
import sys
import json
import pytest

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.ai_self_learning_feedback import AISelfLearningFeedback
from core.regime_adaptive_weights import RegimeAdaptiveWeights
from core.auction_trap_detector import AuctionTrapDetector
from core.institutional_flow_tracker import InstitutionalFlowTracker
from core.telegram_interactive_copilot import TelegramInteractiveCopilot
from core.alpha_scanner.multi_layer_scanner import MultiLayerScanner
from core.alpha_scanner.alpha_scorer import AlphaScorer
from dashboard.app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


# --- 1. Closed-Loop Error Attribution Engine Tests ---
class TestAISelfLearningFeedback:
    def test_attribution_matrix_sums_to_100_percent(self):
        matrix = AISelfLearningFeedback.calculate_attribution_matrix(
            ticker="RAYA.CA",
            entry_price=7.57,
            current_price=6.60,
            sector="Financial Services",
            rvol_10d=0.40,
            insider_sell_ratio=0.55
        )
        assert matrix["ticker"] == "RAYA.CA"
        assert matrix["is_loss"] is True
        assert matrix["loss_pct"] < -10.0
        
        # Attribution matrix weights must sum to 100% (+/- 0.5% due to rounding)
        weights_sum = sum(matrix["attribution_matrix"].values())
        assert 99.5 <= weights_sum <= 100.5

        # Primary cause for high insider sell ratio
        assert matrix["primary_cause"] in [
            AISelfLearningFeedback.FACTOR_INSIDER_OUTFLOW,
            AISelfLearningFeedback.FACTOR_LIQUIDITY_DRYING
        ]
        assert matrix["uncertainty_penalty"] > 0.10

    def test_run_self_learning_cycle_and_persistence(self):
        res = AISelfLearningFeedback.run_self_learning_cycle()
        assert res["total_trades_analyzed"] >= 5
        assert "ticker_penalties" in res
        assert "RAYA.CA" in res["ticker_penalties"]
        assert "COMI.CA" in res["ticker_penalties"]

        memory_path = os.path.join(WORKSPACE, "data", "ai_feedback_memory.json")
        assert os.path.exists(memory_path)
        with open(memory_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert data["version"] == "1.0.0"

    def test_feedback_summary_api_payload(self):
        summary = AISelfLearningFeedback.get_feedback_summary()
        assert summary["status"] == "SUCCESS"
        assert "attribution_factors" in summary
        assert "ticker_penalties" in summary
        assert summary["system_mean_uncertainty_penalty"] > 0.0


# --- 2. Online Regime-Adaptive Weights Tests ---
class TestRegimeAdaptiveWeights:
    def test_devaluation_boom_weights(self):
        weights = RegimeAdaptiveWeights.get_adaptive_weights("DEVALUATION_BOOM")
        assert weights["fundamental"] == 0.45
        assert weights["relative_strength"] == 0.25
        assert weights["technical"] == 0.15
        assert round(weights["events"] + weights["sentiment"], 2) == 0.15

    def test_bear_contraction_weights(self):
        weights = RegimeAdaptiveWeights.get_adaptive_weights("BEAR_CONTRACTION")
        assert weights["events"] == 0.40  # VPIN and order flow toxicity
        assert weights["fundamental"] == 0.30
        assert weights["technical"] == 0.20
        assert weights["relative_strength"] == 0.10

    def test_bull_momentum_weights(self):
        weights = RegimeAdaptiveWeights.get_adaptive_weights("BULL_MOMENTUM")
        assert weights["technical"] == 0.40  # Breakouts & momentum
        assert weights["relative_strength"] == 0.30
        assert weights["fundamental"] == 0.15
        assert round(weights["events"] + weights["sentiment"], 2) == 0.15

    def test_multi_layer_scanner_uses_dynamic_weights(self):
        weights = MultiLayerScanner.get_regime_weights()
        assert "fundamental" in weights
        assert "relative_strength" in weights
        # In current macro regime, fundamental should be 0.45
        assert weights["fundamental"] == 0.45

    def test_alpha_scorer_incorporates_regime_and_boost(self):
        scan_res = MultiLayerScanner.scan_single_stock("MFPC.CA", 48.0)
        scored = AlphaScorer.calculate_alpha_score(scan_res)
        assert scored["ticker"] == "MFPC.CA"
        assert scored["alpha_score"] > 60.0
        assert "layer_weights" in scored
        assert scored["layer_weights"]["fundamental"] == 0.45


# --- 3. Auction Trap Detector Tests ---
class TestAuctionTrapDetector:
    def test_healthy_opening_auction(self):
        res = AuctionTrapDetector.analyze_ticker_auction(
            ticker="COMI.CA",
            live_price=124.65,
            previous_close=125.16,
            open_price=124.65,
            auction_volume=250000.0,
            avg_volume_20d=2000000.0,
            bid_volume=30000.0,
            ask_volume=28000.0
        )
        assert res["verdict"] == AuctionTrapDetector.VERDICT_HEALTHY_AUCTION
        assert res["is_bull_trap"] is False
        assert res["safe_to_execute_thndr"] is True

    def test_bull_trap_detection_and_warning(self):
        res = AuctionTrapDetector.analyze_ticker_auction(
            ticker="TRAP.CA",
            live_price=51.50,
            previous_close=50.00,
            open_price=51.50,  # +3.0% gap up
            auction_volume=5000.0,  # Anemic volume
            avg_volume_20d=500000.0,
            bid_volume=10000.0,
            ask_volume=45000.0  # Heavy ask imbalance
        )
        assert res["verdict"] == AuctionTrapDetector.VERDICT_BULL_TRAP
        assert res["is_bull_trap"] is True
        assert res["safe_to_execute_thndr"] is False
        assert "⚠️ مصيدة تداول (BULL_TRAP_DETECTED)" in res["warning_message_ar"]
        assert "تطبيق ثاندر" in res["warning_message_ar"]

    def test_enrich_thndr_daily_card(self):
        card = {
            "ticker": "SWDY.CA",
            "current_price": 116.0,
            "limit_price": 114.50,
            "execution_instruction_ar": "أمر محدد"
        }
        enriched = AuctionTrapDetector.enrich_thndr_daily_card(card)
        assert "auction_trap_analysis" in enriched
        assert "opening_trap_verdict" in enriched
        assert enriched["opening_trap_verdict"] == AuctionTrapDetector.VERDICT_HEALTHY_AUCTION


# --- 4. Institutional Flow Radar Tests ---
class TestInstitutionalFlowTracker:
    def test_institutional_flows_summary(self):
        flows = InstitutionalFlowTracker.get_daily_flows_summary()
        assert flows["status"] == "SUCCESS"
        assert flows["smart_money_index"] >= 70.0
        assert "net_flows_summary_m_egp" in flows
        net = flows["net_flows_summary_m_egp"]
        assert net["egyptian_institutions"] > 0
        assert net["arab_institutions"] > 0
        assert net["foreign_institutions"] > 0
        assert net["retail_speculators"] < 0
        assert net["total_smart_money_institutions"] > 0

    def test_sector_alpha_boost(self):
        # Fertilizers & Petrochemicals get +5% boost
        boost_fert = InstitutionalFlowTracker.get_sector_alpha_boost("Petrochemicals & Fertilizers")
        assert boost_fert == 5.0
        boost_ar = InstitutionalFlowTracker.get_sector_alpha_boost("الأسمدة والبتروكيماويات")
        assert boost_ar == 5.0

        # Banking gets +3%
        boost_bank = InstitutionalFlowTracker.get_sector_alpha_boost("Banking")
        assert boost_bank == 3.0

        # Real estate gets 0.0%
        boost_re = InstitutionalFlowTracker.get_sector_alpha_boost("Real Estate")
        assert boost_re == 0.0


# --- 5. Interactive Telegram Copilot Tests ---
class TestTelegramInteractiveCopilot:
    def test_price_command(self):
        res = TelegramInteractiveCopilot.handle_command("/price COMI")
        assert "البنك التجاري الدولي" in res
        assert "124.65" in res
        assert "قرش" in res
        assert "VPIN" in res

    def test_swing_command_and_exact_levels(self):
        res = TelegramInteractiveCopilot.handle_command("/swing")
        assert "COMI.CA" in res
        assert "SWDY.CA" in res
        assert "TMGH.CA" in res
        assert "PHDC.CA" in res
        assert "RAYA.CA" in res
        # Check COMI specific swing levels: rebuy 123.50, sell 134.60, breakout 144.00
        assert "123.50" in res
        assert "134.60" in res
        assert "144.00" in res

    def test_portfolio_command(self):
        res = TelegramInteractiveCopilot.handle_command("/portfolio")
        assert "13,658.56" in res
        assert "1,200.00" in res
        assert "1,830.00" in res
        assert "35%" in res

    def test_trap_command(self):
        res = TelegramInteractiveCopilot.handle_command("/trap RAYA")
        assert "RAYA.CA" in res
        assert "رادار فحص مزاد الافتتاح" in res

    def test_top_command(self):
        res = TelegramInteractiveCopilot.handle_command("/top")
        assert "MFPC.CA" in res
        assert "69.5%" in res  # Verified win probability for MFPC
        assert "ABUK.CA" in res
        assert "68.0%" in res


# --- 6. Flask REST Endpoints Tests ---
class TestFlaskEndpoints:
    def test_api_ai_self_learning_feedback(self, client):
        resp = client.get("/api/ai/self_learning/feedback")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "SUCCESS"
        assert "attribution_aggregate_weights" in data
        assert "ticker_penalties" in data

    def test_api_ai_regime_weights(self, client):
        resp = client.get("/api/ai/regime_weights")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "SUCCESS"
        assert data["active_regime"] == "DEVALUATION_BOOM"
        assert data["active_layer_weights"]["fundamental"] == 0.45

    def test_api_auction_trap(self, client):
        resp = client.get("/api/auction_trap/COMI.CA")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "verdict" in data
        assert "opening_gap_pct" in data

    def test_api_market_institutional_flows(self, client):
        resp = client.get("/api/market/institutional_flows")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "SUCCESS"
        assert "smart_money_index" in data
        assert "sector_accumulation_matrix" in data

    def test_api_thndr_daily_card_enriched(self, client):
        resp = client.get("/api/thndr_daily_card")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "thndr_daily_card" in data
        card = data["thndr_daily_card"]
        assert "auction_trap_analysis" in card
        assert "opening_trap_verdict" in card

    def test_api_opportunities_10d_mfpc_win_prob(self, client):
        resp = client.get("/api/opportunities/10d")
        assert resp.status_code == 200
        data = resp.get_json()
        opps = data if isinstance(data, list) else data.get("opportunities", [])
        assert len(opps) > 0
        mfpc = next((o for o in opps if o["ticker"] == "MFPC.CA"), None)
        assert mfpc is not None
        assert mfpc["win_probability_pct"] == 69.5
