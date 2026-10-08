#!/usr/bin/env python3
# =============================================================================
# core/incubation_gate_engine.py — GEN-26 30-Day Incubation Evaluation & Gating Engine
# Authoritative Independent Forensic Auditor & Quantitative Gatekeeper.
# Evaluates 6 mandatory criteria on September 22, 2026 (or >= 20 closed paper trades):
# 1. Annualized Sharpe Ratio >= 1.05
# 2. Cumulative Alpha vs EGX30 >= +2.50%
# 3. Maximum Drawdown <= 6.50%
# 4. Win Rate Percentage >= 52.0%
# 5. Profit Factor >= 1.30
# 6. Minimum Closed Trades Sample Size >= 20
#
# Computes Bootstrap 95% CI (1,000 resamples), t-Statistic, Statistical Confidence,
# and triggers automated fail-closed circuit breaker (FROZEN_FAIL_CLOSED vs GRADUATED_PRODUCTION_READY).
# =============================================================================

import os
import sys
import json
import math
import sqlite3
import datetime
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

REPORTS_DIR = os.path.join(WORKSPACE, "reports")
DATA_DIR = os.path.join(WORKSPACE, "data")
VERDICT_MD_FILE = os.path.join(REPORTS_DIR, "INCUBATION_FINAL_VERDICT.md")
VERDICT_JSON_FILE = os.path.join(REPORTS_DIR, "incubation_verdict.json")


class IncubationGateEngine:
    """
    Automated Quantitative Risk & Forensic Maturation Gatekeeper for GEN-26.
    """

    # --- 6 Mandatory Production Gating Thresholds ---
    MIN_SHARPE_RATIO = 1.05
    MIN_CUMULATIVE_ALPHA_PCT = 2.50      # Target >= +2.50% vs EGX30 Total Return
    MAX_DRAWDOWN_LIMIT_PCT = 6.50        # Hard Limit <= 6.50% peak-to-trough
    MIN_WIN_RATE_PCT = 52.00             # Target >= 52.0%
    MIN_PROFIT_FACTOR = 1.30             # Gross Profits / Gross Losses >= 1.30
    MIN_SAMPLE_SIZE_TRADES = 20          # >= 20 completed round-trip trades

    # Decision Modes
    STATUS_GRADUATED = "GRADUATED_PRODUCTION_READY"
    STATUS_FAIL_CLOSED = "FROZEN_FAIL_CLOSED"
    STATUS_INCUBATION_ACTIVE = "INCUBATION_IN_PROGRESS"

    FALLBACK_MODEL_TIER1 = "TIER1_PRICE_MOMENTUM_OR_100_CASH"
    PROD_MODEL_MULTI_HORIZON = "MULTI_HORIZON_QUANT_ALPHA"

    @classmethod
    def evaluate_incubation_state(
        cls,
        custom_trades: Optional[List[Dict[str, Any]]] = None,
        custom_daily_nav: Optional[List[float]] = None,
        benchmark_egx30_return_pct: float = 3.50,
        evaluation_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes complete multi-criterion forensic audit on paper trading closed trades.
        """
        eval_date = evaluation_date or datetime.date.today().isoformat()

        # 1. Ingest Trades
        trades = custom_trades if custom_trades is not None else cls._ingest_closed_trades()
        nav_series = custom_daily_nav if custom_daily_nav is not None else cls._ingest_nav_series()

        n_trades = len(trades)
        trade_returns = [float(t.get("pnl_pct", 0.0)) for t in trades]

        # 2. Calculate the 6 Gating Metrics
        # Metric 1: Annualized Sharpe Ratio
        sharpe_ratio, daily_returns = cls._calculate_sharpe_ratio(nav_series)

        # Metric 2: Cumulative Alpha vs EGX30 Total Return
        strategy_total_return_pct = ((nav_series[-1] - nav_series[0]) / nav_series[0] * 100.0) if len(nav_series) >= 2 and nav_series[0] > 0 else 0.0
        cumulative_alpha_pct = round(strategy_total_return_pct - benchmark_egx30_return_pct, 2)

        # Metric 3: Max Peak-to-Trough Drawdown
        max_drawdown_pct = cls._calculate_max_drawdown(nav_series)

        # Metric 4: Win Rate Percentage
        winning_trades = [r for r in trade_returns if r > 0.0]
        losing_trades = [r for r in trade_returns if r < 0.0]
        win_rate_pct = round((len(winning_trades) / n_trades * 100.0), 1) if n_trades > 0 else 0.0

        # Metric 5: Profit Factor
        gross_profit = sum(float(t.get("pnl_egp", 0.0)) for t in trades if float(t.get("pnl_egp", 0.0)) > 0)
        gross_loss = abs(sum(float(t.get("pnl_egp", 0.0)) for t in trades if float(t.get("pnl_egp", 0.0)) < 0))
        if gross_loss > 0:
            profit_factor = round(gross_profit / gross_loss, 2)
        elif gross_profit > 0:
            profit_factor = 99.0  # Perfect profit factor
        else:
            profit_factor = 0.0

        # Metric 6: Sample Size Requirement
        sample_size_pass = n_trades >= cls.MIN_SAMPLE_SIZE_TRADES

        # 3. Dynamic Statistical Confidence Score & Bootstrap 95% CI (1,000 resamples)
        bootstrap_ci, t_stat, p_val = cls._compute_bootstrap_ci_and_tstat(trade_returns)
        statistical_confidence_score = cls._compute_confidence_score(t_stat, win_rate_pct, n_trades)

        # 4. Gate Evaluations Matrix
        gates = {
            "gate_1_sharpe_ratio": {
                "name": "Annualized Sharpe Ratio",
                "name_ar": "معامل شارب السنوي",
                "target": f"≥ {cls.MIN_SHARPE_RATIO:.2f}",
                "actual": round(sharpe_ratio, 2),
                "passed": sharpe_ratio >= cls.MIN_SHARPE_RATIO,
                "gap": round(sharpe_ratio - cls.MIN_SHARPE_RATIO, 2)
            },
            "gate_2_cumulative_alpha": {
                "name": "Cumulative Alpha vs EGX30",
                "name_ar": "العائد الإضافي التراكمي (ألفا) فوق المؤشر",
                "target": f"≥ +{cls.MIN_CUMULATIVE_ALPHA_PCT:.2f}%",
                "actual": f"{cumulative_alpha_pct:+.2f}%",
                "passed": cumulative_alpha_pct >= cls.MIN_CUMULATIVE_ALPHA_PCT,
                "gap_pct": round(cumulative_alpha_pct - cls.MIN_CUMULATIVE_ALPHA_PCT, 2)
            },
            "gate_3_max_drawdown": {
                "name": "Maximum Peak-to-Trough Drawdown",
                "name_ar": "أقصى تراجع تراكمي للمحفظة",
                "target": f"≤ {cls.MAX_DRAWDOWN_LIMIT_PCT:.2f}%",
                "actual": f"{max_drawdown_pct:.2f}%",
                "passed": max_drawdown_pct <= cls.MAX_DRAWDOWN_LIMIT_PCT,
                "gap_pct": round(max_drawdown_pct - cls.MAX_DRAWDOWN_LIMIT_PCT, 2)
            },
            "gate_4_win_rate": {
                "name": "Win Rate Percentage",
                "name_ar": "نسبة الصفقات الرابحة",
                "target": f"≥ {cls.MIN_WIN_RATE_PCT:.1f}%",
                "actual": f"{win_rate_pct:.1f}%",
                "passed": win_rate_pct >= cls.MIN_WIN_RATE_PCT,
                "gap_pct": round(win_rate_pct - cls.MIN_WIN_RATE_PCT, 1)
            },
            "gate_5_profit_factor": {
                "name": "Profit Factor",
                "name_ar": "معامل الربحية (الأرباح / الخسائر)",
                "target": f"≥ {cls.MIN_PROFIT_FACTOR:.2f}",
                "actual": round(profit_factor, 2),
                "passed": profit_factor >= cls.MIN_PROFIT_FACTOR,
                "gap": round(profit_factor - cls.MIN_PROFIT_FACTOR, 2)
            },
            "gate_6_sample_size": {
                "name": "Minimum Closed Trades Sample Size",
                "name_ar": "الحد الأدنى لحجم العينة المغلقة",
                "target": f"≥ {cls.MIN_SAMPLE_SIZE_TRADES} صفقات",
                "actual": f"{n_trades} صفقات",
                "passed": sample_size_pass,
                "gap_count": n_trades - cls.MIN_SAMPLE_SIZE_TRADES
            }
        }

        all_passed = all(g["passed"] for g in gates.values())
        failed_gates = [g["name_ar"] for g in gates.values() if not g["passed"]]

        # 5. Fail-Closed Circuit Breaker Protocol
        if all_passed:
            verdict_status = cls.STATUS_GRADUATED
            verdict_status_ar = "🟢 اعتماد الترقية للإنتاج الحقيقي (GRADUATED_PRODUCTION_READY)"
            authorized_capital_scale_pct = 25.0
            real_money_authorized = True
            active_model = cls.PROD_MODEL_MULTI_HORIZON
            action_mandate_ar = "تم اعتماد النظام للتشغيل الفعلي بمقياس رأس مال أولي 25% مع الالتزام الصارم بقواعد وقف الخسارة وإدارة المخاطر."
        else:
            verdict_status = cls.STATUS_FAIL_CLOSED
            verdict_status_ar = "🔴 تفعيل صمام الأمان والإغلاق الإلزامي (FROZEN_FAIL_CLOSED)"
            authorized_capital_scale_pct = 0.0
            real_money_authorized = False
            active_model = cls.FALLBACK_MODEL_TIER1
            action_mandate_ar = "تم تعليق الترقية الفورية والرجوع الإلزامي لنموذج الزخم الأساسي Tier-1 أو الاحتفاظ بالسيولة 100% كاش لحماية رأس المال."

        statistical_caveats = []
        if n_trades < 100:
            statistical_caveats.append(
                f"[PRELIMINARY_SAMPLE_SIZE_WARNING: N={n_trades} < 100] — القدرة الإحصائية أولية ومحدودة لحين الوصول لـ 100 صفقة مغلقة."
            )

        # Dynamic Session Counting & Date Span
        state_file = os.path.join(REPORTS_DIR, "paper_trading_state.json")
        start_date = "2026-08-23"
        latest_session_date = eval_date
        verified_sessions_count = max(n_trades, 30)
        if os.path.exists(state_file):
            try:
                with open(state_file, "r", encoding="utf-8") as sf:
                    st_data = json.load(sf)
                prog = st_data.get("session_progress", {})
                start_date = st_data.get("start_date") or "2026-08-23"
                latest_session_date = prog.get("last_successful_session") or eval_date
                v_count = prog.get("verified_sessions") or len(st_data.get("verified_session_history", []))
                if v_count:
                    verified_sessions_count = v_count
            except Exception:
                pass

        incubation_period_str = f"فترة الحضانة التشغيلية الموثقة: {verified_sessions_count} من 30 جلسة ({start_date} – {latest_session_date})"

        verdict_payload = {
            "evaluation_date": eval_date,
            "incubation_period": incubation_period_str,
            "verified_sessions": verified_sessions_count,
            "total_sessions_required": 30,
            "start_date": start_date,
            "last_session_date": latest_session_date,
            "verdict_status": verdict_status,
            "verdict_status_ar": verdict_status_ar,
            "all_gates_passed": all_passed,
            "real_money_authorized": real_money_authorized,
            "authorized_capital_scale_pct": authorized_capital_scale_pct,
            "active_model_policy": active_model,
            "action_mandate_ar": action_mandate_ar,
            "failed_gates_count": len(failed_gates),
            "failed_gates": failed_gates,
            "gating_matrix": gates,
            "performance_summary": {
                "total_closed_trades": n_trades,
                "winning_trades_count": len(winning_trades),
                "losing_trades_count": len(losing_trades),
                "strategy_total_return_pct": round(strategy_total_return_pct, 2),
                "egx30_benchmark_return_pct": benchmark_egx30_return_pct,
                "cumulative_alpha_pct": cumulative_alpha_pct,
                "annualized_sharpe_ratio": round(sharpe_ratio, 2),
                "max_drawdown_pct": round(max_drawdown_pct, 2),
                "win_rate_pct": win_rate_pct,
                "profit_factor": profit_factor,
                "gross_profit_egp": round(gross_profit, 2),
                "gross_loss_egp": round(gross_loss, 2)
            },
            "statistical_validation": {
                "confidence_score_pct": statistical_confidence_score,
                "t_statistic": round(t_stat, 2),
                "p_value_one_tailed": round(p_val, 4),
                "bootstrap_resamples_count": 1000,
                "bootstrap_95_ci_pct": {
                    "lower": round(bootstrap_ci[0], 2),
                    "mean": round(bootstrap_ci[1], 2),
                    "upper": round(bootstrap_ci[2], 2)
                },
                "statistical_caveats": statistical_caveats
            }
        }

        # Persist Final Verdict Artifacts
        cls._emit_verdict_artifacts(verdict_payload)

        return verdict_payload

    @classmethod
    def _calculate_sharpe_ratio(cls, nav_series: List[float]) -> Tuple[float, List[float]]:
        """Calculates annualized Sharpe Ratio from daily NAV sequence."""
        if len(nav_series) < 3:
            return 0.0, []
        returns = []
        for i in range(1, len(nav_series)):
            if nav_series[i-1] > 0:
                ret = (nav_series[i] - nav_series[i-1]) / nav_series[i-1]
                returns.append(ret)
        if not returns or np.std(returns) == 0:
            return 0.0, returns
        mean_ret = np.mean(returns)
        std_ret = np.std(returns, ddof=1)
        annualized_sharpe = (mean_ret / std_ret) * math.sqrt(252) if std_ret > 0 else 0.0
        return float(annualized_sharpe), returns

    @classmethod
    def _calculate_max_drawdown(cls, nav_series: List[float]) -> float:
        """Calculates maximum peak-to-trough percentage drawdown."""
        if not nav_series:
            return 0.0
        peak = nav_series[0]
        max_dd = 0.0
        for val in nav_series:
            if val > peak:
                peak = val
            dd = ((peak - val) / peak * 100.0) if peak > 0 else 0.0
            if dd > max_dd:
                max_dd = dd
        return round(max_dd, 2)

    @classmethod
    def _compute_bootstrap_ci_and_tstat(cls, returns: List[float]) -> Tuple[Tuple[float, float, float], float, float]:
        """Computes 1,000 bootstrap resamples for 95% Confidence Interval and t-statistic."""
        if not returns or len(returns) < 2:
            return (-2.0, 0.0, 2.0), 0.0, 0.50

        arr = np.array(returns)
        n = len(arr)
        mean_val = float(np.mean(arr))
        std_val = float(np.std(arr, ddof=1)) if n > 1 else 1.0

        t_stat = (mean_val / (std_val / math.sqrt(n))) if std_val > 0 else 0.0
        # Normal approximation p-value
        p_val = 0.5 * math.erfc(t_stat / math.sqrt(2))

        # Bootstrap 1,000 iterations
        rng = np.random.default_rng(seed=42)
        boot_means = []
        for _ in range(1000):
            resample = rng.choice(arr, size=n, replace=True)
            boot_means.append(float(np.mean(resample)))

        ci_lower = float(np.percentile(boot_means, 2.5))
        ci_mean = float(np.mean(boot_means))
        ci_upper = float(np.percentile(boot_means, 97.5))

        return (ci_lower, ci_mean, ci_upper), t_stat, p_val

    @classmethod
    def _compute_confidence_score(cls, t_stat: float, win_rate: float, n_trades: int) -> float:
        """Computes 0-100% statistical confidence score."""
        if n_trades == 0:
            return 50.0
        score = 50.0 + (t_stat * 12.0) + ((win_rate - 50.0) * 0.4)
        sample_penalty = max((20 - n_trades) * 2.0, 0.0)
        score -= sample_penalty
        return round(min(max(score, 10.0), 99.0), 1)

    @classmethod
    def _ingest_closed_trades(cls) -> List[Dict[str, Any]]:
        """Ingests closed trades from paper portfolio database, journal, or state file."""
        trades = []
        seen_keys = set()

        # 1. Primary Source: reports/paper_trading_state.json
        state_file = os.path.join(REPORTS_DIR, "paper_trading_state.json")
        if os.path.exists(state_file):
            try:
                with open(state_file, "r", encoding="utf-8") as f:
                    st = json.load(f)
                hist = (st.get("portfolio", {}).get("closed_positions_history", []) or 
                        st.get("portfolio", {}).get("closed_positions", []))
                for h in hist:
                    key = (h.get("ticker"), float(h.get("entry_price", 0.0)))
                    if key not in seen_keys:
                        seen_keys.add(key)
                        trades.append({
                            "ticker": h.get("ticker"),
                            "entry_price": float(h.get("entry_price", 0.0)),
                            "exit_price": float(h.get("exit_price", 0.0)),
                            "pnl_pct": float(h.get("return_pct") or h.get("pnl_pct") or 0.0),
                            "pnl_egp": float(h.get("net_pnl_egp") or h.get("pnl_egp") or 0.0),
                            "status": "CLOSED"
                        })
            except Exception:
                pass

        # 2. Secondary Source: data/paper_trading_journal.json
        journal_file = os.path.join(DATA_DIR, "paper_trading_journal.json")
        if os.path.exists(journal_file):
            try:
                with open(journal_file, "r", encoding="utf-8") as f:
                    jd = json.load(f)
                j_trades = jd.get("closed_trades", [])
                for jt in j_trades:
                    key = (jt.get("ticker"), float(jt.get("entry_price", 0.0)))
                    if key not in seen_keys:
                        seen_keys.add(key)
                        trades.append({
                            "ticker": jt.get("ticker"),
                            "entry_price": float(jt.get("entry_price", 0.0)),
                            "exit_price": float(jt.get("exit_price", 0.0)),
                            "pnl_pct": float(jt.get("return_pct", 0.0)),
                            "pnl_egp": float(jt.get("realized_pnl_egp", 0.0)),
                            "status": "CLOSED"
                        })
            except Exception:
                pass

        # 3. Tertiary Source: data/gen26_production.db
        db_path = os.path.join(DATA_DIR, "gen26_production.db")
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='paper_trades'")
                if cursor.fetchone():
                    cursor.execute("SELECT ticker, entry_price, exit_price, pnl_pct, pnl_egp, status FROM paper_trades WHERE status='CLOSED'")
                    for r in cursor.fetchall():
                        key = (r[0], float(r[1]))
                        if key not in seen_keys:
                            seen_keys.add(key)
                            trades.append({
                                "ticker": r[0],
                                "entry_price": float(r[1]),
                                "exit_price": float(r[2]),
                                "pnl_pct": float(r[3]),
                                "pnl_egp": float(r[4]),
                                "status": r[5]
                            })
                conn.close()
            except Exception:
                pass

        return trades

    @classmethod
    def _ingest_nav_series(cls) -> List[float]:
        """Ingests NAV sequence from verified session history."""
        navs = [100000.0]
        state_file = os.path.join(REPORTS_DIR, "paper_trading_state.json")
        if os.path.exists(state_file):
            try:
                with open(state_file, "r", encoding="utf-8") as f:
                    st = json.load(f)
                sessions = st.get("verified_session_history", [])
                accum_nav = 100000.0
                for s in sessions:
                    if "nav_egp" in s:
                        navs.append(float(s["nav_egp"]))
                    elif "pnl" in s:
                        accum_nav += float(s["pnl"])
                        navs.append(round(accum_nav, 2))
            except Exception:
                pass
        return navs

    @classmethod
    def _emit_verdict_artifacts(cls, verdict: Dict[str, Any]):
        """Emits final audit markdown and JSON artifacts."""
        os.makedirs(REPORTS_DIR, exist_ok=True)

        with open(VERDICT_JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(verdict, f, ensure_ascii=False, indent=2)

        md = []
        md.append("# التقرير النهائي لاعتماد ترقية الإنتاج وانتهاء فترة الحضانة (GEN-26 Incubation Verdict)")
        md.append(f"\n**تاريخ التقييم:** `{verdict['evaluation_date']}` | **فترة الحضانة:** `{verdict['incubation_period']}`")
        md.append(f"\n## 1. القرار النهائي للجنة المخاطر (Official Maturation Verdict)\n")
        md.append(f"> ### {verdict['verdict_status_ar']}")
        md.append(f"> **التفويض المالي:** `{verdict['authorized_capital_scale_pct']}% من رأس المال الأولي` | **النموذج المعتمد:** `{verdict['active_model_policy']}`")
        md.append(f"> \n> **التوجيه الإلزامي:** {verdict['action_mandate_ar']}\n")

        md.append("## 2. مصفوفة المعايير الستة الإلزامية (Mandatory Gating Matrix)\n")
        md.append("| # | المعيار الكمي | المستهدف الإلزامي | المحقق الفعلي | النتيجة |")
        md.append("|---|---|---|---|---|")
        for idx, (k, g) in enumerate(verdict["gating_matrix"].items(), start=1):
            status_icon = "🟢 PASS" if g["passed"] else "🔴 FAIL"
            md.append(f"| {idx} | **{g['name_ar']}** | `{g['target']}` | **{g['actual']}** | **{status_icon}** |")

        md.append("\n## 3. نتائج التحقق الإحصائي وفترات الثقة (Statistical Bootstrap Bounds)\n")
        stat = verdict["statistical_validation"]
        md.append(f"- **نسبة الثقة الإحصائية المركبة:** `{stat['confidence_score_pct']}%`")
        md.append(f"- **معامل t-Statistic:** `{stat['t_statistic']}` (p-value: `{stat['p_value_one_tailed']}`)")
        md.append(f"- **نطاق الثقة 95% للعائد المتوقع (1,000 Bootstrap Resamples):** `[{stat['bootstrap_95_ci_pct']['lower']}%, {stat['bootstrap_95_ci_pct']['upper']}%]`")
        for c in stat.get("statistical_caveats", []):
            md.append(f"- ⚠️ `{c}`")

        with open(VERDICT_MD_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(md) + "\n")


if __name__ == "__main__":
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    res = IncubationGateEngine.evaluate_incubation_state()
    print("Incubation Evaluation State:")
    print(json.dumps(res, ensure_ascii=False, indent=2))
