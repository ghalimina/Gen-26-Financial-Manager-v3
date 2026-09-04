import sys
import os
import io
import json
import time
import traceback

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

trace_results = {}

print("=== STARTING END-TO-END PIPELINE TRACE ===")

# STEP 1: Data (MarketPriceService)
t0 = time.perf_counter()
try:
    from core.market_price_service import MarketPriceService
    svc = MarketPriceService()
    p_comi = svc.get_latest_price("COMI.CA")
    rec_comi = svc.get_canonical_price_record("COMI.CA")
    t1 = time.perf_counter()
    trace_results["1_data_service"] = {
        "status": "SUCCESS",
        "latency_sec": round(t1 - t0, 4),
        "price_comi": p_comi,
        "record_keys": list(rec_comi.keys()) if rec_comi else None,
        "sample_record": rec_comi
    }
    print(f"[STEP 1: DATA SERVICE] OK in {t1-t0:.4f}s - COMI.CA price = {p_comi}")
except Exception as e:
    t1 = time.perf_counter()
    trace_results["1_data_service"] = {"status": "ERROR", "latency_sec": round(t1 - t0, 4), "exception": str(e), "traceback": traceback.format_exc()}
    print(f"[STEP 1: DATA SERVICE] ERROR: {e}")

# STEP 2: Scanner (MultiHorizonEngine / Opportunity Scanning on Focus Sample)
t0 = time.perf_counter()
try:
    from core.multi_horizon_engine import MultiHorizonEngine
    sample_tickers = ["COMI.CA", "SWDY.CA", "TMGH.CA", "MFPC.CA", "ETEL.CA"]
    sample_ranks = [MultiHorizonEngine.get_stock_multi_horizon_analysis(s) for s in sample_tickers]
    sample_ranks.sort(key=lambda x: x.get("overall_score", 0.0), reverse=True)
    t1 = time.perf_counter()
    trace_results["2_scanner"] = {
        "status": "SUCCESS",
        "latency_sec": round(t1 - t0, 4),
        "stocks_scanned": len(sample_ranks),
        "top_ranked_ticker": sample_ranks[0]["ticker"] if sample_ranks else None,
        "top_ranked_score": sample_ranks[0]["overall_score"] if sample_ranks else None
    }
    print(f"[STEP 2: SCANNER] OK in {t1-t0:.4f}s - Scanned {len(sample_ranks)} focus stocks. Top: {sample_ranks[0]['ticker']} ({sample_ranks[0]['overall_score']})")
except Exception as e:
    t1 = time.perf_counter()
    trace_results["2_scanner"] = {"status": "ERROR", "latency_sec": round(t1 - t0, 4), "exception": str(e), "traceback": traceback.format_exc()}
    print(f"[STEP 2: SCANNER] ERROR: {e}")

# STEP 3: Forecast (AIPredictionModel)
t0 = time.perf_counter()
try:
    from core.ai_prediction_model import AIPredictionModel
    pred_res = AIPredictionModel.predict_stock("COMI.CA")
    t1 = time.perf_counter()
    trace_results["3_forecast"] = {
        "status": "SUCCESS",
        "latency_sec": round(t1 - t0, 4),
        "expected_alpha_10d_pct": pred_res.get("expected_alpha_10d_pct"),
        "ai_confidence_score": pred_res.get("ai_confidence_score"),
        "top_3_drivers": pred_res.get("top_3_drivers", [])
    }
    print(f"[STEP 3: FORECAST] OK in {t1-t0:.4f}s - Alpha = {pred_res.get('expected_alpha_10d_pct')}%, Confidence = {pred_res.get('ai_confidence_score')}%")
except Exception as e:
    t1 = time.perf_counter()
    trace_results["3_forecast"] = {"status": "ERROR", "latency_sec": round(t1 - t0, 4), "exception": str(e), "traceback": traceback.format_exc()}
    print(f"[STEP 3: FORECAST] ERROR: {e}")

# STEP 4: Trade Selection & Decision (MultiHorizonEngine)
t0 = time.perf_counter()
try:
    from core.multi_horizon_engine import MultiHorizonEngine
    analysis = MultiHorizonEngine.get_stock_multi_horizon_analysis("COMI.CA")
    t1 = time.perf_counter()
    trace_results["4_trade_selection"] = {
        "status": "SUCCESS",
        "latency_sec": round(t1 - t0, 4),
        "ticker": analysis.get("ticker"),
        "current_price": analysis.get("current_price"),
        "overall_score": analysis.get("overall_score"),
        "decision": analysis.get("decision"),
        "stop_loss": analysis.get("stop_loss"),
        "entry_zone": analysis.get("entry_zone"),
        "horizons": list(analysis.get("horizons", {}).keys())
    }
    print(f"[STEP 4: TRADE SELECTION] OK in {t1-t0:.4f}s - Score = {analysis.get('overall_score')}, Decision = {analysis.get('decision')}")
except Exception as e:
    t1 = time.perf_counter()
    trace_results["4_trade_selection"] = {"status": "ERROR", "latency_sec": round(t1 - t0, 4), "exception": str(e), "traceback": traceback.format_exc()}
    print(f"[STEP 4: TRADE SELECTION] ERROR: {e}")

# STEP 5: Council Deliberation (AgentCouncilOrchestrator)
t0 = time.perf_counter()
try:
    from core.multi_agent_council import AgentCouncilOrchestrator
    deliberation = AgentCouncilOrchestrator.deliberate("COMI.CA")
    t1 = time.perf_counter()
    trace_results["5_council"] = {
        "status": "SUCCESS",
        "latency_sec": round(t1 - t0, 4),
        "consensus_verdict": deliberation.get("consensus_verdict"),
        "conviction_score": deliberation.get("conviction_score"),
        "bullish_votes": deliberation.get("bullish_votes_count"),
        "bearish_votes": deliberation.get("bearish_votes_count")
    }
    print(f"[STEP 5: COUNCIL] OK in {t1-t0:.4f}s - Consensus = {deliberation.get('consensus_verdict')}, Conviction = {deliberation.get('conviction_score')}")
except Exception as e:
    t1 = time.perf_counter()
    trace_results["5_council"] = {"status": "ERROR", "latency_sec": round(t1 - t0, 4), "exception": str(e), "traceback": traceback.format_exc()}
    print(f"[STEP 5: COUNCIL] ERROR: {e}")

# STEP 6: Persistence (DatabaseEngine)
t0 = time.perf_counter()
try:
    from core.database_engine import db_engine
    init_ok = db_engine.initialize_database()
    stocks = db_engine.get_all_stocks()
    t1 = time.perf_counter()
    trace_results["6_persistence"] = {
        "status": "SUCCESS",
        "latency_sec": round(t1 - t0, 4),
        "init_status": "OK",
        "db_records_count": len(stocks)
    }
    print(f"[STEP 6: PERSISTENCE] OK in {t1-t0:.4f}s - SQLite seeded with {len(stocks)} stocks")
except Exception as e:
    t1 = time.perf_counter()
    trace_results["6_persistence"] = {"status": "ERROR", "latency_sec": round(t1 - t0, 4), "exception": str(e), "traceback": traceback.format_exc()}
    print(f"[STEP 6: PERSISTENCE] ERROR: {e}")

# STEP 7: API / REST Layer (Flask Client)
t0 = time.perf_counter()
try:
    from dashboard.app import app
    client = app.test_client()
    resp_market = client.get("/api/market")
    resp_stocks = client.get("/api/stocks/COMI.CA")
    resp_sizer = client.post("/api/portfolio/size", json={"total_capital_egp": 25000, "strategy": "risk_parity"})
    t1 = time.perf_counter()
    trace_results["7_api_layer"] = {
        "status": "SUCCESS",
        "latency_sec": round(t1 - t0, 4),
        "market_status": resp_market.status_code,
        "stock_status": resp_stocks.status_code,
        "sizer_status": resp_sizer.status_code,
        "sizer_allocations_count": len(resp_sizer.get_json().get("allocations", [])) if resp_sizer.is_json else 0
    }
    print(f"[STEP 7: API LAYER] OK in {t1-t0:.4f}s - Market: {resp_market.status_code}, Stock: {resp_stocks.status_code}, Sizer: {resp_sizer.status_code}")
except Exception as e:
    t1 = time.perf_counter()
    trace_results["7_api_layer"] = {"status": "ERROR", "latency_sec": round(t1 - t0, 4), "exception": str(e), "traceback": traceback.format_exc()}
    print(f"[STEP 7: API LAYER] ERROR: {e}")

print("\n=== COMPLETE RAW TRACE JSON ===")
print(json.dumps(trace_results, indent=2, ensure_ascii=True))
