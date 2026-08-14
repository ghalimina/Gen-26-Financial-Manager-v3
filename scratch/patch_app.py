import os
import re

app_file = r"c:\Users\Administrator\Desktop\New folder\app.py"

with open(app_file, "r", encoding="utf-8") as f:
    content = f.read()

# ---------------------------------------------------------
# 1. Patch check_circuit_breaker()
# ---------------------------------------------------------
circuit_breaker_new = """def check_circuit_breaker():
    # 1. Drawdown Failsafe
    journal = load_paper_journal()
    if journal:
        closed = [t for t in journal if t.get('status','PENDING') != 'PENDING']
        if len(closed) >= 3:
            gains = []
            for t in closed[-10:]:
                ep = t.get('entry_price', 0)
                if ep > 0:
                    dfc = safe_download_multisource(t.get('ticker',''),"1m")
                    if not dfc.empty:
                        gains.append((float(dfc['Close'].iloc[-1])-ep)/ep*100)
            if gains:
                cumul = float(np.sum(gains)/max(len(gains),1))
                if cumul <= -10.0:  # Failsafe Threshold
                    return True, round(cumul, 2)
    
    # 2. Market Staleness Failsafe
    df_egx = safe_download_multisource("EGX30.CA", "1d")
    if not df_egx.empty:
        last_date = df_egx.index[-1]
        today = datetime.datetime.now().replace(tzinfo=None)
        if today.weekday() < 5 and (today - last_date).days > 1:
            return True, -99.9  # Stale data
            
    return False, 0.0"""

content = re.sub(
    r"def check_circuit_breaker\(\):.*?(?=\n# ═══════════════════════════════════════════════════════════════════════════════\n# PORTFOLIO CONSTRUCTION)",
    circuit_breaker_new + "\n",
    content,
    flags=re.DOTALL
)

# ---------------------------------------------------------
# 2. Patch Portfolio Cash State Management
# ---------------------------------------------------------
portfolio_new = """def load_my_portfolio():
    if os.path.exists(PORTFOLIO_FILE):
        try:
            with open(PORTFOLIO_FILE,'r',encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data.get('holdings', [])
                elif isinstance(data, list):
                    return data
        except Exception: return []
    return []

def get_portfolio_cash():
    if os.path.exists(PORTFOLIO_FILE):
        try:
            with open(PORTFOLIO_FILE,'r',encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    # Return Buying Power T+0 by default for active trading
                    bp = data.get('buying_power_t0')
                    if bp is not None:
                        return float(bp)
                    return float(data.get('cash_egp', 2000.0))
        except Exception: pass
    return 2000.0

def load_execution_status():
    if os.path.exists(EXECUTION_STATUS_FILE):
        try:
            with open(EXECUTION_STATUS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception: pass
    return {"last_updated": datetime.datetime.now().isoformat(), "orders": {}}

def save_execution_status(data):
    try:
        with open(EXECUTION_STATUS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception: pass

def save_my_portfolio(h, cash=None):
    current_cash = get_portfolio_cash() if cash is None else float(cash)
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    clean_holdings = []
    
    withdrawable = current_cash * 0.8
    unsettled = current_cash * 0.2
    
    if isinstance(h, list):
        for item in h:
            stk = item.get('stock', '')
            tick = item.get('ticker', '')
            if not tick:
                for n, sym in EGX_STOCKS.items():
                    if n == stk: tick = sym; break
            clean_holdings.append({
                "stock": stk,
                "ticker": tick,
                "qty": int(item.get('qty', 0)),
                "avg_price": float(item.get('avg_price', 0.0)),
                "data_verification_status": item.get('data_verification_status', 'CONFIRMED_BY_USER'),
                "confirmed_date": item.get('confirmed_date', today_str)
            })
    elif isinstance(h, dict):
        clean_holdings = h.get('holdings', [])
        current_cash = float(h.get('cash_egp', current_cash))
        withdrawable = float(h.get('withdrawable_cash_t2', withdrawable))
        unsettled = float(h.get('unsettled_cash', unsettled))
        current_cash = float(h.get('buying_power_t0', current_cash))
        
    portfolio_obj = {
        "cash_egp": current_cash,
        "buying_power_t0": current_cash,
        "unsettled_cash": unsettled,
        "withdrawable_cash_t2": withdrawable,
        "last_confirmed_date": today_str,
        "holdings": clean_holdings
    }
    with open(PORTFOLIO_FILE, 'w', encoding='utf-8') as f:
        json.dump(portfolio_obj, f, ensure_ascii=False, indent=2)"""

content = re.sub(
    r"def load_my_portfolio\(\):.*?(?=def reset_portfolio_from_text\()",
    portfolio_new + "\n\n",
    content,
    flags=re.DOTALL
)

# ---------------------------------------------------------
# 3. Patch export_decision_log (JSON Structured Reason)
# ---------------------------------------------------------
export_decision_new = """def export_decision_log(predictions, ts):
    rows = []
    for p in predictions:
        reason_json = {
            "ticker": p.get('الكود',''),
            "signal": p.get('التوصية الحية',''),
            "ml_direction_prob": float(p.get('نسبة الثقة الحية','0').replace('%','')) / 100.0 if isinstance(p.get('نسبة الثقة الحية'), str) else p.get('نسبة الثقة الحية', 0),
            "calibrated_confidence": float(p.get('درجة الترتيب الاستثماري ⭐', 0)),
            "peak_expected_return": p.get('أعلى قمة متوقعة 🏔️',''),
            "hurdle_cleared": True,
            "market_regime": p.get('حالة السوق','BULL_ABOVE_SMA50'),
            "liquidity_status": p.get('_liquidity_flag','APPROVED'),
            "risk_parity_weight": p.get('تخصيص المحفظة %',''),
            "primary_catalysts": [p.get('المحفز الرئيسي 🔑','')]
        }
        
        rows.append({
            'date':ts,
            'ticker':p.get('الكود',''),
            'name':p.get('الاسم',''),
            'signal':p.get('التوصية الحية',''),
            'score':p.get('درجة الترتيب الاستثماري ⭐',''),
            'entry_price':p.get('سعر الدخول المقترح (شراء بدعم) 📥',''),
            'peak_target':p.get('أعلى قمة متوقعة 🏔️',''),
            'stop_loss':p.get('وقف الخسارة 🛑',''),
            'confidence_pct':p.get('نسبة الثقة الحية',''),
            'ret_5d':p.get('عائد 5D صافي %',''),
            'ret_20d':p.get('عائد 20D صافي %',''),
            'ret_60d':p.get('عائد 60D صافي %',''),
            'model_agreement':p.get('اتفاق النماذج 🤝',''),
            'top_driver': json.dumps(reason_json, ensure_ascii=False),
            'allocation_pct':p.get('تخصيص المحفظة %',''),
            'liquidity_flag':p.get('_liquidity_flag','OK'),
            'data_quality':p.get('_dq_status','OK'),
            'sector':p.get('القطاع',''),
            'model_version': 'v3.0-frozen'
        })
    try: pd.DataFrame(rows).to_csv(DECISION_LOG_CSV, index=False, encoding='utf-8-sig')
    except Exception: pass"""

content = re.sub(
    r"def export_decision_log\(predictions, ts\):.*?(?=def export_daily_ranking\()",
    export_decision_new + "\n\n",
    content,
    flags=re.DOTALL
)

# ---------------------------------------------------------
# 4. Patch export_daily_ranking to include version
# ---------------------------------------------------------
export_ranking_new = """def export_daily_ranking(predictions, ts):
    rows = [{'date':ts,'rank':p.get('الترتيب 🏆',''),'ticker':p.get('الكود',''),
              'name':p.get('الاسم',''),'sector':p.get('القطاع',''),
              'score':p.get('درجة الترتيب الاستثماري ⭐',''),'signal':p.get('التوصية الحية',''),
              'confidence':p.get('نسبة الثقة الحية',''),'market_regime':p.get('حالة السوق',''),
              'model_agreement':p.get('اتفاق النماذج 🤝',''),'alpha_vs_egx30':p.get('Alpha vs EGX30 📊',''),
              'data_quality':p.get('_dq_status','OK'), 'model_version': 'v3.0-frozen'} for p in predictions]
    try: pd.DataFrame(rows).to_csv(RANKING_CSV, index=False, encoding='utf-8-sig')
    except Exception: pass"""

content = re.sub(
    r"def export_daily_ranking\(predictions, ts\):.*?(?=def export_portfolio_state\()",
    export_ranking_new + "\n\n",
    content,
    flags=re.DOTALL
)

# ---------------------------------------------------------
# 5. Patch Snapshot Engine inside run_engine_pipeline
# ---------------------------------------------------------
# Find "return predictions_out, list(exit_signals.values())" and inject snapshot logic right before it
snapshot_logic = """
    # -------------------------------------------------------------------------
    # DAILY POINT-IN-TIME SNAPSHOT ENGINE
    # -------------------------------------------------------------------------
    try:
        if processed_dict:
            snapshot_dir = os.path.join(BASE_DIR, 'data', 'snapshots')
            os.makedirs(snapshot_dir, exist_ok=True)
            snapshot_ts = datetime.datetime.now().strftime("%Y%m%d_%H%M")
            snapshot_path = os.path.join(snapshot_dir, f"snapshot_{snapshot_ts}.json")
            
            # Combine latest row of all processed dicts
            snap_data = []
            for t, df in processed_dict.items():
                if not df.empty:
                    last_row = df.iloc[-1].to_dict()
                    last_row['Ticker'] = t
                    # Ensure JSON serialization for timestamps
                    for k,v in last_row.items():
                        if isinstance(v, pd.Timestamp):
                            last_row[k] = str(v)
                    snap_data.append(last_row)
                    
            with open(snapshot_path, "w", encoding="utf-8") as f:
                json.dump({"timestamp": snapshot_ts, "model_version": "v3.0-frozen", "data": snap_data}, f, indent=2)
    except Exception as e:
        print(f"Snapshot Error: {e}")
        
    return predictions_out, list(exit_signals.values())"""

content = content.replace("return predictions_out, list(exit_signals.values())", snapshot_logic)

# Write patched app.py
with open(app_file, "w", encoding="utf-8") as f:
    f.write(content)

print("Patch applied to app.py successfully.")
