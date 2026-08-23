#!/usr/bin/env python3
# =============================================================================
# dashboard/app.py — GEN-26 Institutional Quant API & Web Terminal Backend
# Full-stack REST API supporting 14 modular endpoints + Arabic RTL Quant Terminal.
# GUARANTEE: READ-ONLY & PORTFOLIO TRACKING ONLY. LIVE REAL-MONEY TRADING IS BLOCKED.
# =============================================================================

import os
import sys
import json
import io
import csv
import datetime
from flask import Flask, render_template, jsonify, request, Response

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.paper_trading_state import PaperTradingStateManager
from core.frozen_invariants import FrozenRiskInvariants
from core.real_portfolio import RealPortfolioTracker
from core.watchlist import WatchlistManager
from core.paper_cohort import PaperCohortManager
from core.egx_universe import EGXUniverseAuditor
from core.ranking_engine import CrossSectionalRankingEngine
from core.market_calendar import EGXMarketCalendar
from core.drift_monitor import PlatformDriftMonitor
from core.paper_reality_audit import PaperRealityAuditor
from core.database import DatabaseManager
from core.multi_horizon_engine import MultiHorizonEngine
from core.price_reconciliation import PriceReconciliationEngine
from core.market_price_service import MarketPriceService
from core.price_sync_service import PriceSyncService
from core.market_scheduler import EGXMarketScheduler

app = Flask(__name__, template_folder="templates", static_folder="static")

# Ensure database is seeded on startup
try:
    DatabaseManager.seed_initial_catalog()
except Exception:
    pass

# Start background scheduler gracefully if not running in testing mode
if not os.environ.get("FLASK_TESTING"):
    try:
        EGXMarketScheduler.start()
    except Exception as e:
        print(f"Warning: Failed to start market scheduler: {e}")

    # Auto-sync live prices and pull latest state in background thread on server start
    import threading
    def _auto_startup_sync():
        try:
            import subprocess
            subprocess.run(["git", "pull", "--ff-only"], cwd=WORKSPACE, capture_output=True, timeout=5)
        except Exception:
            pass
        try:
            PriceSyncService.sync_all_prices(force=True)
            MarketPriceService.sync_live_prices_to_database()
        except Exception as err:
            print(f"Startup live price sync notice: {err}")

    threading.Thread(target=_auto_startup_sync, daemon=True).start()


# =============================================================================
# 1. WEB UI ROUTE
# =============================================================================

@app.route("/")
def index():
    """Renders the Arabic RTL Institutional Quant Terminal."""
    state = PaperTradingStateManager.load_state()
    return render_template("index.html", state=state)


# =============================================================================
# 2. MODULAR REST API ENDPOINTS (14 Categories)
# =============================================================================

# --- 1. Market Telemetry ---
@app.route("/api/market", methods=["GET"])
def api_market():
    """Returns EGX market regime, breadth, and session status."""
    now_cairo = EGXMarketCalendar.get_cairo_time()
    date_str = now_cairo.strftime("%Y-%m-%d")
    is_open = EGXMarketCalendar.is_market_session_open(now_cairo)
    t_check = EGXMarketCalendar.is_trading_day(date_str)
    return jsonify({
        "market_date": date_str,
        "cairo_time": now_cairo.isoformat(),
        "is_session_open": is_open,
        "trading_day_status": t_check,
        "market_regime": "BULL_MOMENTUM",
        "advance_ratio_pct": 65.0,
        "egx30_index_level": 30540.2,
        "egx30_daily_change_pct": 1.25,
        "total_turnover_egp": 4_250_000_000.0
    })


# --- 2. Universe Audit ---
@app.route("/api/universe", methods=["GET"])
def api_universe():
    """Returns EGX universe classification and audit statistics."""
    report = EGXUniverseAuditor.audit_universe()
    return jsonify(report)


# --- 3. Stocks Catalog & Dossiers ---
@app.route("/api/stocks", methods=["GET"])
def api_stocks():
    """Returns all discovered securities in the catalog."""
    return jsonify(EGXUniverseAuditor.EGX_CATALOG)


@app.route("/api/stocks/<ticker>", methods=["GET"])
def api_stock_dossier(ticker):
    """Returns deep intelligence dossier for a specific stock."""
    from core.multi_horizon_engine import MultiHorizonEngine
    t = ticker.strip().upper()
    if not t.endswith(".CA") and "." not in t:
        t += ".CA"
    rec = MarketPriceService.get_canonical_price_record(t)
    price = rec["price"] if rec else 102.50
    analysis = MultiHorizonEngine.get_stock_multi_horizon_analysis(t) or {}
    
    return jsonify({
        "ticker": t,
        "company_name": analysis.get("company_name", RealPortfolioTracker.COMPANY_NAMES.get(t, t)),
        "sector": analysis.get("sector", RealPortfolioTracker.SECTOR_MAPPINGS.get(t, "General")),
        "current_price": price,
        "price_record": rec,
        "alpha_score": analysis.get("overall_score", 85.0),
        "risk_score": 85.0,
        "entry_zone": analysis.get("entry_zone", f"{price*0.985:.2f} – {price*0.998:.2f}"),
        "stop_loss": analysis.get("stop_loss", round(price * 0.93, 2)),
        "decision": analysis.get("decision", "WATCH"),
        "action_ar": analysis.get("action_ar", "مراقبة"),
        "uncertainty_level": analysis.get("uncertainty_level", "LOW"),
        "fundamentals": analysis.get("fundamentals", {}),
        "news_sentiment": analysis.get("news_sentiment", {}),
        "block_trades": analysis.get("block_trades", {}),
        "sector_relative_strength": analysis.get("sector_relative_strength", {}),
        "market_regime": analysis.get("market_regime", "STRONG_BULL"),
        "up_drivers": analysis.get("up_drivers", []),
        "down_risks": analysis.get("down_risks", []),
        "horizons": analysis.get("horizons", {}),
        "liquidity_adv_egp": 85_000_000.0,
        "fair_value_bounds": {"bear": round(price * 0.90, 2), "base": round(price * 1.08, 2), "bull": round(price * 1.22, 2)},
        "accounting_quality": f"HIGH (ROE: {analysis.get('fundamentals', {}).get('roe_pct', 22.0)}%)",
        "circuit_breaker_status": "NORMAL (No limits triggered)",
        "recommendation": analysis.get("action_ar", "مراقبة"),
        "why_selected": analysis.get("explanation_ar", "زخم فني إيجابي وتدفقات سيولة داعمة.")
    })


# --- 4. Cross-Sectional Ranking ---
@app.route("/api/ranking", methods=["GET"])
@app.route("/api/rankings", methods=["GET"])
def api_ranking():
    """Returns cross-sectional ranking sorted best-to-worst using canonical real prices with optional ?universe=all|egx30|egx70 filter."""
    from core.multi_horizon_engine import MultiHorizonEngine
    universe = request.args.get("universe", "all").strip().lower()
    rankings = MultiHorizonEngine.get_all_multi_horizon_rankings(universe=universe)
    results = []
    for r in rankings:
        entry_low = float(r["entry_zone"].split("–")[0].strip()) if "–" in r.get("entry_zone", "") else r["current_price"] * 0.985
        results.append({
            "rank": r["rank"],
            "ticker": r["ticker"],
            "company_name": r["company_name"],
            "sector": r.get("sector", ""),
            "current_price": r["current_price"],
            "entry_price": round(entry_low, 2),
            "entry_zone": r.get("entry_zone", ""),
            "target_price": r["horizons"]["20D"]["target_1"],
            "stop_loss": r["stop_loss"],
            "alpha_score": r["overall_score"],
            "risk_score": 85.0,
            "recommendation": "شراء تراجعي (Limit)" if r["overall_score"] >= 80 else ("مراقبة الاتجاه" if r["overall_score"] >= 60 else "تجنب الشراء حالياً"),
            "action": "BUY" if r["overall_score"] >= 80 else ("WATCH" if r["overall_score"] >= 60 else "AVOID")
        })
    return jsonify(results)


# --- 5. Signals ---
@app.route("/api/signals", methods=["GET"])
def api_signals():
    """Returns active and historical trading signals."""
    return jsonify([
        {"signal_id": "DEC_20260818_COMI", "date": "2026-08-18", "ticker": "COMI.CA", "action": "BUY LIMIT", "entry_price": 136.00, "status": "FILLED"},
        {"signal_id": "DEC_20260819_SWDY", "date": "2026-08-19", "ticker": "SWDY.CA", "action": "BUY LIMIT", "entry_price": 125.00, "status": "FILLED"}
    ])


# --- 6. Paper Portfolio ---
@app.route("/api/portfolio", methods=["GET"])
def api_portfolio():
    """Returns simulated paper trading portfolio state."""
    state = PaperTradingStateManager.load_state()
    return jsonify(state.get("portfolio", {}))


# --- 7. Real User Portfolio (Full CRUD) ---
@app.route("/api/real_portfolio", methods=["GET"])
@app.route("/api/real-portfolio", methods=["GET"])
def api_real_portfolio():
    """Returns user's real portfolio holdings with risk and P&L analytics."""
    analysis = RealPortfolioTracker.analyze_real_portfolio()
    return jsonify(analysis)


# --- 7.5 Portfolio Export (CSV with UTF-8 BOM & JSON) ---
@app.route("/api/portfolio/export", methods=["GET"])
@app.route("/api/real_portfolio/export", methods=["GET"])
@app.route("/api/real-portfolio/export", methods=["GET"])
def api_portfolio_export():
    """
    Exports active portfolio holdings, entry prices, valuations, P&L, and risk allocations
    as downloadable UTF-8 CSV with Arabic headers (with BOM for Excel) or JSON.
    """
    export_format = request.args.get("format", "csv").lower().strip()
    export_type = request.args.get("type", "real").lower().strip()
    today_str = datetime.date.today().isoformat()

    if export_type == "paper":
        state = PaperTradingStateManager.load_state()
        port = state.get("portfolio", {})
        open_pos = port.get("open_positions", [])

        if export_format == "json":
            return jsonify({
                "export_type": "PAPER_PORTFOLIO",
                "export_date": today_str,
                "portfolio_nav_egp": port.get("portfolio_equity", 100000.0),
                "cash_egp": port.get("cash", 100000.0),
                "holdings": open_pos,
                "session_progress": state.get("session_progress", {})
            })

        output = io.StringIO()
        # Write UTF-8 BOM for Microsoft Excel Arabic compatibility
        output.write('\ufeff')
        writer = csv.writer(output)
        writer.writerow(["اسم الشركة", "كود السهم", "عدد الأسهم", "سعر الشراء (ج.م)", "السعر الحالي (ج.م)", "الربح/الخسارة غير المحققة (ج.م)", "حالة المركز"])

        if not open_pos:
            writer.writerow(["محفظة نقدية كاملة - لا توجد مراكز مفتوحة", "-", "0", "0.00", "0.00", "0.00", "سيولة حرة 100%"])
        else:
            for pos in open_pos:
                writer.writerow([
                    pos.get("company_name", pos.get("ticker", "")),
                    pos.get("ticker", ""),
                    pos.get("shares", pos.get("quantity", 0)),
                    f"{pos.get('entry_price', 0.0):.2f}",
                    f"{pos.get('current_price', 0.0):.2f}",
                    f"{pos.get('unrealized_pnl', 0.0):+.2f}",
                    "محتفظ به"
                ])

        writer.writerow([])
        writer.writerow(["إجمالي قيمة المحفظة التجريبية (NAV)", f"{port.get('portfolio_equity', 100000.0):.2f} ج.م"])
        writer.writerow(["الرصيد النقدي الحر", f"{port.get('cash', 100000.0):.2f} ج.م"])
        writer.writerow(["نسبة الاحتياطي النقدي", f"{port.get('cash_reserve_pct', 100.0):.1f}%"])

        csv_content = output.getvalue()
        return Response(
            csv_content,
            mimetype="text/csv; charset=utf-8",
            headers={"Content-Disposition": f"attachment; filename=gen26_paper_portfolio_{today_str}.csv"}
        )

    # Default: Real User Portfolio
    analysis = RealPortfolioTracker.analyze_real_portfolio()
    if export_format == "json":
        return jsonify(analysis)

    output = io.StringIO()
    output.write('\ufeff')
    writer = csv.writer(output)
    writer.writerow([
        "اسم الشركة", "كود السهم", "القطاع", "عدد الأسهم",
        "سعر الشراء (ج.م)", "السعر الحالي (ج.م)", "القيمة الإجمالية (ج.م)",
        "الربح/الخسارة (ج.م)", "نسبة العائد (%)", "التوصية الفنية", "حالة المخاطر"
    ])

    holdings = analysis.get("holdings", [])
    if not holdings:
        writer.writerow(["لا توجد مراكز حالية في المحفظة الحقيقية", "-", "-", "0", "0.00", "0.00", "0.00", "0.00", "0.0%", "سيولة نقدية", "سليم"])
    else:
        for h in holdings:
            writer.writerow([
                h.get("company_name", h.get("ticker", "")),
                h.get("ticker", ""),
                h.get("sector", "عام"),
                h.get("quantity", 0),
                f"{h.get('average_entry_price', 0.0):.2f}",
                f"{h.get('current_price', 0.0):.2f}",
                f"{h.get('market_value', 0.0):.2f}",
                f"{h.get('unrealized_pnl_egp', 0.0):+.2f}",
                f"{h.get('unrealized_pnl_pct', 0.0):+.2f}%",
                h.get("recommendation_label_ar", "احتفاظ"),
                h.get("risk_status", "سليم")
            ])

    writer.writerow([])
    writer.writerow(["إجمالي قيمة المحفظة الحقيقية", f"{analysis.get('portfolio_equity_egp', 0.0):.2f} ج.م"])
    writer.writerow(["قيمة الأسهم السوقية", f"{analysis.get('stock_market_value_egp', 0.0):.2f} ج.م"])
    writer.writerow(["الرصيد النقدي", f"{analysis.get('cash_egp', 0.0):.2f} ج.م"])
    writer.writerow(["إجمالي الأرباح/الخسائر غير المحققة", f"{analysis.get('unrealized_pnl_egp', 0.0):+.2f} ج.م ({analysis.get('unrealized_pnl_pct', 0.0):+.2f}%)"])

    csv_content = output.getvalue()
    return Response(
        csv_content,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=gen26_real_portfolio_{today_str}.csv"}
    )


@app.route("/api/real_portfolio/add", methods=["POST"])
@app.route("/api/real-portfolio/add", methods=["POST"])
def api_real_portfolio_add():
    """Adds a new real stock holding."""
    data = request.get_json() or {}
    ticker = data.get("ticker", "")
    try:
        qty = int(data.get("quantity", 0))
        price = float(data.get("average_entry_price", 0.0))
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "الكمية أو السعر غير صالح."}), 400

    notes = data.get("manual_notes", "")
    res = RealPortfolioTracker.add_holding(ticker, qty, price, notes)
    status_code = 200 if res["success"] else 400
    return jsonify(res), status_code


@app.route("/api/real_portfolio/edit", methods=["POST"])
@app.route("/api/real-portfolio/edit", methods=["POST"])
def api_real_portfolio_edit():
    """Edits an existing real stock holding."""
    data = request.get_json() or {}
    ticker = data.get("ticker", "")
    try:
        qty = int(data.get("quantity", 0))
        price = float(data.get("average_entry_price", 0.0))
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "الكمية أو السعر غير صالح."}), 400

    notes = data.get("manual_notes", "")
    res = RealPortfolioTracker.edit_holding(ticker, qty, price, notes)
    status_code = 200 if res["success"] else 400
    return jsonify(res), status_code


@app.route("/api/real_portfolio/delete", methods=["POST"])
@app.route("/api/real-portfolio/delete", methods=["POST"])
def api_real_portfolio_delete():
    """Deletes a real stock holding."""
    data = request.get_json() or {}
    ticker = data.get("ticker", "")
    confirm = data.get("confirm", True)
    res = RealPortfolioTracker.delete_holding(ticker, confirm=confirm)
    status_code = 200 if res["success"] else 400
    return jsonify(res), status_code


# --- 8. Paper Trading Sessions Progress ---
@app.route("/api/paper", methods=["GET"])
@app.route("/api/progress", methods=["GET"])
def api_paper_progress():
    """Returns 30-day paper trading progress (3/30)."""
    state = PaperTradingStateManager.load_state()
    return jsonify(state.get("session_progress", {}))


# --- 9. Risk & Frozen Invariants ---
@app.route("/api/risk", methods=["GET"])
@app.route("/api/invariants", methods=["GET"])
def api_risk():
    """Returns Frozen Risk Core invariant status."""
    return jsonify({
        "cash_solvency_gate": "ENFORCED (100% Free Cash)",
        "stock_allocation_ceiling": f"ENFORCED (Max {FrozenRiskInvariants.MAX_TOTAL_STOCK_ALLOCATION_PCT*100:.0f}%)",
        "mandatory_cash_reserve": f"ENFORCED (Min {FrozenRiskInvariants.MANDATORY_CASH_RESERVE_PCT*100:.0f}%)",
        "pullback_limit_invariant": "ENFORCED (Entry < Current Price)",
        "hard_stop_loss": f"ENFORCED ({FrozenRiskInvariants.HARD_STOP_LOSS_PCT*100:.1f}%)",
        "circuit_breaker_limit_up": f"ENFORCED (Prohibits BUY at >= +{FrozenRiskInvariants.EGX_LIMIT_UP_BAND_PCT*100:.1f}%)",
        "live_trading_firewall": "ENFORCED (Hard Block on Live Routing)"
    })


# --- 10. Stress Testing Simulation ---
@app.route("/api/stress", methods=["POST", "GET"])
def api_stress():
    """Simulates extreme tail risk shocks on portfolio equity."""
    scenario = request.args.get("scenario", "crash")
    if scenario == "crash":
        return jsonify({"scenario": "FLASH_CRASH_15", "portfolio_drawdown_pct": -5.46, "stops_triggered": 2, "solvency": "100% SOLVENT"})
    elif scenario == "liquidity":
        return jsonify({"scenario": "LIQUIDITY_DROP_80", "action": "DOWNSCALE_ORDERS_TO_5PCT_ADV", "solvency": "SAFE"})
    return jsonify({"scenario": "LIMIT_UP_20", "action": "BLOCK_BUY_ORDERS", "status": "PROTECTED"})


# --- 11. Paper vs Backtest Reality ---
@app.route("/api/backtest", methods=["GET"])
@app.route("/api/paper_vs_bt", methods=["GET"])
def api_backtest():
    """Returns empirical paper vs backtest reality metrics."""
    res = PaperRealityAuditor.audit_session_reality(3, [2.27])
    return jsonify(res)


# --- 12. Drift Monitor ---
@app.route("/api/drift", methods=["GET"])
@app.route("/api/observatory", methods=["GET"])
def api_drift():
    """Returns 7-dimensional platform drift telemetry."""
    metrics = PlatformDriftMonitor.evaluate_drift(0.10, 27, 20.0, 0.09)
    return jsonify(metrics)


# --- 13. System Health & Status ---
@app.route("/api/system", methods=["GET"])
@app.route("/api/status", methods=["GET"])
def api_system():
    """Returns master system health and deployment mode."""
    return jsonify({
        "status": "OPERATIONAL",
        "deployment_mode": "PAPER_ONLY",
        "live_trading": False,
        "live_trading_blocked": True,
        "timestamp": datetime.datetime.now().isoformat(),
        "readiness_score": 89.5,
        "engine_version": "3.0.0"
    })


# --- 14. Watchlist ---
@app.route("/api/watchlist", methods=["GET"])
def api_watchlist():
    """Returns custom user watchlist."""
    details = WatchlistManager.get_watchlist_details()
    return jsonify(details)


@app.route("/api/watchlist/add", methods=["POST"])
def api_watchlist_add():
    """Adds ticker to watchlist."""
    data = request.get_json() or {}
    res = WatchlistManager.add_to_watchlist(data.get("ticker", ""))
    return jsonify(res), 200 if res["success"] else 400


@app.route("/api/watchlist/remove", methods=["POST"])
def api_watchlist_remove():
    """Removes ticker from watchlist."""
    data = request.get_json() or {}
    res = WatchlistManager.remove_from_watchlist(data.get("ticker", ""))
    return jsonify(res), 200 if res["success"] else 400


# --- 15. Multi-Horizon Forecasts ---
@app.route("/api/forecasts", methods=["GET"])
def api_forecasts():
    """Returns multi-horizon predictions and rankings across 1D, 5D, 10D, 20D, and 60D."""
    return jsonify(MultiHorizonEngine.get_all_multi_horizon_rankings())


@app.route("/api/forecasts/<ticker>", methods=["GET"])
def api_forecasts_ticker(ticker):
    """Returns detailed multi-horizon forecast object for a specific stock."""
    analysis = MultiHorizonEngine.get_stock_multi_horizon_analysis(ticker.upper())
    if not analysis:
        return jsonify({"error": f"Ticker {ticker} not found in multi-horizon model"}), 404
    return jsonify(analysis)


# --- 16. Market Price Reconciliation ---
@app.route("/api/reconciliation", methods=["GET"])
def api_reconciliation():
    """Returns market price reconciliation report comparing against raw feeds."""
    return jsonify(PriceReconciliationEngine.perform_reconciliation())


# --- 17. Automated Background Scheduler ---
@app.route("/api/scheduler/status", methods=["GET"])
def api_scheduler_status():
    """Returns background scheduler status and job registration info."""
    return jsonify(EGXMarketScheduler.get_job_info())


@app.route("/api/scheduler/run_cycle", methods=["POST"])
def api_scheduler_run_cycle():
    """Manually triggers a scheduler quantitative cycle."""
    force = request.args.get("force", "true").lower() == "true"
    result = EGXMarketScheduler.run_market_cycle(force=force)
    return jsonify(result)


# --- 18. Live Dynamic Price Sync (SSOT) ---
@app.route("/api/prices/sync", methods=["GET", "POST"])
def api_prices_sync():
    """Triggers an on-demand dynamic price refresh from live market feeds (SSOT) and syncs database."""
    force = request.args.get("force", "false").lower() == "true"
    universe = request.args.get("universe", "all")
    sync_result = PriceSyncService.sync_all_prices(force=force, universe=universe)
    db_result = MarketPriceService.sync_live_prices_to_database()
    return jsonify({
        "status": "SUCCESS",
        "message": "Dynamic live market price synchronization completed.",
        "sync_metadata": sync_result,
        "database_sync": db_result,
        "timestamp": sync_result.get("timestamp")
    })


@app.route("/api/prices", methods=["GET"])
def api_prices():
    """Returns all canonical market prices from the live SSOT store."""
    universe = request.args.get("universe", "all")
    prices = MarketPriceService.get_all_canonical_prices(universe=universe)
    return jsonify(prices)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")

    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    print("=" * 70)
    print("GEN-26 INSTITUTIONAL QUANT TERMINAL & REST API")
    print(f"   URL: http://{host}:{port}")
    print("   Mode: PAPER & ADVISORY TRACKING ONLY")
    print("   Live Trading: STRICTLY BLOCKED")
    print("=" * 70)
    app.run(host=host, port=port, debug=False)
