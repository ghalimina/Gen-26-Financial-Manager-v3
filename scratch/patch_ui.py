import os
import re

app_file = r"c:\Users\Administrator\Desktop\New folder\app.py"
with open(app_file, "r", encoding="utf-8") as f:
    content = f.read()

# ---------------------------------------------------------
# 1. Input Validation & Edge Cases
# ---------------------------------------------------------
# Fix wizard_cash_input
content = content.replace(
    'cash_input = st.number_input("💵 الكاش الحر المتاح في المحفظة (ج.م):", min_value=0.0, value=float(get_portfolio_cash()), step=500.0, key="wizard_cash_input")',
    'cash_input = st.number_input("💵 الكاش الحر المتاح في المحفظة (ج.م):", min_value=0.0, max_value=1e9, value=float(get_portfolio_cash()), step=500.0, key="wizard_cash_input")'
)

# Fix qt_single and ag_single to have max values to prevent overflow
content = content.replace(
    'qt_single = st.number_input("الكمية:", min_value=1, value=50, step=10, key="single_q")',
    'qt_single = st.number_input("الكمية:", min_value=1, max_value=100000000, value=50, step=10, key="single_q")'
)
content = content.replace(
    'ag_single = st.number_input("متوسط سعر الشراء:", min_value=0.1, value=15.0, step=0.5, key="single_a")',
    'ag_single = st.number_input("متوسط سعر الشراء:", min_value=0.1, max_value=100000.0, value=15.0, step=0.5, key="single_a")'
)

# ---------------------------------------------------------
# 2. Resiliency & Exception Handling (Empty DataFrames)
# ---------------------------------------------------------
# Fix check_circuit_breaker empty df crash
circuit_breaker_old = """                    dfc = safe_download_multisource(t.get('ticker',''),"1m")
                    if not dfc.empty:
                        gains.append((float(dfc['Close'].iloc[-1])-ep)/ep*100)"""

circuit_breaker_new = """                    dfc = safe_download_multisource(t.get('ticker',''),"1m")
                    if not dfc.empty and len(dfc) > 0 and 'Close' in dfc.columns:
                        gains.append((float(dfc['Close'].iloc[-1])-ep)/ep*100)"""
content = content.replace(circuit_breaker_old, circuit_breaker_new)

# Fix estimate_slippage empty df crash
slippage_old = """    df = safe_download_multisource(ticker, "1mo")
    if len(df) < 5: return 0.005
    last_close = float(df['Close'].iloc[-1])"""
    
slippage_new = """    df = safe_download_multisource(ticker, "1mo")
    if df.empty or len(df) < 5 or 'Close' not in df.columns: return 0.005
    last_close = float(df['Close'].iloc[-1])"""
content = content.replace(slippage_old, slippage_new)

# Fix run_portfolio_equity_holdout_test empty df crash
holdout_old = """        if not dfc.empty:
            ap = round(float(dfc['High'].iloc[-5:].max()),2)"""
holdout_new = """        if not dfc.empty and 'High' in dfc.columns and len(dfc) >= 1:
            ap = round(float(dfc['High'].iloc[-5:].max()),2)"""
content = content.replace(holdout_old, holdout_new)

# Fix run_data_quality_gate empty df crash
dq_old = """    lr = dfs.iloc[-1]"""
dq_new = """    if dfs.empty or len(dfs) == 0: return "REJECT", "Empty DataFrame"
    lr = dfs.iloc[-1]"""
content = content.replace(dq_old, dq_new)


# ---------------------------------------------------------
# 3. Session State & Navigation (Refresh Data)
# ---------------------------------------------------------
# Wait, let's find the refresh button
# We'll just replace 'st.experimental_rerun()' with 'st.rerun()' globally if exists
content = content.replace("st.experimental_rerun()", "st.rerun()")

# ---------------------------------------------------------
# 4. Visuals, Formatting & Exports
# ---------------------------------------------------------
# Fix download buttons utf-8 encoding
dl_trade_old = 'st.download_button("⬇️ تحميل أوامر الشراء كملف Excel / CSV", f_tr.read(), "gen_trade_orders.csv", "text/csv", key="dl_trades_csv")'
dl_trade_new = 'st.download_button("⬇️ تحميل أوامر الشراء كملف Excel / CSV", f_tr.read().encode("utf-8-sig"), "gen_trade_orders.csv", "text/csv", key="dl_trades_csv")'
content = content.replace(dl_trade_old, dl_trade_new)

dl_exit_old = 'st.download_button("⬇️ تحميل أوامر البيع كملف Excel / CSV", f_ex.read(), "gen_exit_orders.csv", "text/csv", key="dl_exits_csv")'
dl_exit_new = 'st.download_button("⬇️ تحميل أوامر البيع كملف Excel / CSV", f_ex.read().encode("utf-8-sig"), "gen_exit_orders.csv", "text/csv", key="dl_exits_csv")'
content = content.replace(dl_exit_old, dl_exit_new)

# Also fix the 3 metric displays formatting (if possible without breaking too much)
# EGP formatting is mostly covered by f"{...:,.2f}"
# Let's search and replace common misformatted metric calls.
content = content.replace('st.metric("إجمالي قيمة المحفظة (EGP)", f"{pf_total}")', 'st.metric("إجمالي قيمة المحفظة (EGP)", f"{pf_total:,.2f}")')
content = content.replace('st.metric("الكاش المتاح", f"{cash}")', 'st.metric("الكاش المتاح", f"{cash:,.2f}")')

# ---------------------------------------------------------
# 5. Failsafe UI Presentation
# ---------------------------------------------------------
# Inject global kill-switch banner after the page config
# The app structure usually has st.set_page_config at top.
failsafe_banner = """
# --- GLOBAL FAILSAFE BANNER ---
is_safe, cb_metric = check_circuit_breaker()
if is_safe:
    if cb_metric == -99.9:
        st.error("🚨 **SYSTEM IN HOLD/SAFE MODE** 🚨\\n\\n**Reason:** Market Data Staleness Detected (> 24h). All new buy orders are BLOCKED until fresh data arrives.")
    else:
        st.error(f"🚨 **SYSTEM IN HOLD/SAFE MODE** 🚨\\n\\n**Reason:** Maximum Drawdown Threshold Breached (Portfolio DD: {cb_metric}%). All new buy orders are BLOCKED.")
"""

# Let's inject it right after `st.title("🏛️ Gen-26 Financial Manager v3.0")`
if "st.title(\"🏛️ Gen-26 Financial Manager v3.0\")" in content:
    content = content.replace("st.title(\"🏛️ Gen-26 Financial Manager v3.0\")", "st.title(\"🏛️ Gen-26 Financial Manager v3.0\")" + failsafe_banner)

with open(app_file, "w", encoding="utf-8") as f:
    f.write(content)

print("UI Patch applied successfully.")
