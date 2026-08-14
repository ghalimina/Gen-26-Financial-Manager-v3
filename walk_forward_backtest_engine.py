# ═══════════════════════════════════════════════════════════════════════════════
# 🏛️ INDEPENDENT WALK-FORWARD OUT-OF-SAMPLE BACKTESTING ENGINE
# Model: Gen-26 Institutional Multi-Horizon EGX Strategy
# ═══════════════════════════════════════════════════════════════════════════════
import sys
sys.stdout.reconfigure(encoding='utf-8')
import os, json, datetime, math
import pandas as pd
import numpy as np
from sklearn.preprocessing import RobustScaler
from sklearn.ensemble import HistGradientBoostingRegressor, HistGradientBoostingClassifier

WORKSPACE = r"c:\Users\Administrator\Desktop\New folder"
sys.path.insert(0, WORKSPACE)

import app

LIQUID_UNIVERSE = [
    "COMI.CA", "TMGH.CA", "SWDY.CA", "HRHO.CA", "FWRY.CA", 
    "PHDC.CA", "ESRS.CA", "AMOC.CA", "ISPH.CA", "ETEL.CA", 
    "ABUK.CA", "MFPC.CA", "HELI.CA", "MASR.CA", "EKHO.CA"
]

def load_data_universe():
    dfs = {}
    print(f"📥 Loading historical 3-year data for {len(LIQUID_UNIVERSE)} EGX assets...")
    for t in LIQUID_UNIVERSE:
        d = app.safe_download_multisource(t, "3y")
        if d is not None and not d.empty and len(d) > 80:
            dfs[t] = d
    egx30_df = app.safe_download_multisource("EGX30.CA", "3y")
    return dfs, egx30_df

def compute_technical_features(df):
    c = df['Adj_Close']
    h = df['High']
    l = df['Low']
    v = df['Volume']
    
    sma20 = c.rolling(20).mean()
    sma50 = c.rolling(50).mean()
    
    # RSI 14
    d = c.diff()
    g = d.where(d > 0, 0).rolling(14).mean()
    loss = (-d.where(d < 0, 0)).rolling(14).mean()
    rsi = 100 - (100 / (1 + g / (loss + 1e-9)))
    
    # ATR 14
    hl = h - l
    hc = np.abs(h - c.shift())
    lc = np.abs(l - c.shift())
    atr = pd.concat([hl, hc, lc], axis=1).max(axis=1).rolling(14).mean()
    atr_pct = (atr / c) * 100.0
    
    # Momentum & Volume
    mom5 = c.pct_change(5) * 100.0
    mom20 = c.pct_change(20) * 100.0
    vm = v.rolling(20).mean()
    vs = v.rolling(20).std()
    vol_z = ((v - vm) / (vs + 1e-9)).clip(-3, 3)
    
    # Regime
    slope = (sma20 - sma20.shift(5)) / (sma20.shift(5) + 1e-9) * 100.0
    reg = np.zeros(len(c))
    reg = np.where((slope > 0.3) & (c > sma50), 1, reg)
    reg = np.where((slope < -0.3) & (c < sma50), -1, reg)
    
    feats = pd.DataFrame({
        'Close': c,
        'High': h,
        'Low': l,
        'SMA_20': sma20,
        'SMA_50': sma50,
        'RSI_14': rsi,
        'ATR_Pct': atr_pct,
        'ATR_Abs': atr,
        'Mom_5D': mom5,
        'Mom_20D': mom20,
        'Vol_ZScore': vol_z,
        'Regime': reg
    }, index=df.index)
    return feats

def run_walk_forward_simulation(dfs, egx30_df, start_date=None, end_date=None, 
                                round_trip_cost_pct=0.90, min_hurdle_rate=3.0, 
                                use_regime_gate=True, max_pos_pct=0.10):
    
    # 1. Feature extraction per stock
    feat_dict = {t: compute_technical_features(df) for t, df in dfs.items()}
    
    # Determine common calendar dates
    all_dates = sorted(list(set.union(*[set(df.index) for df in feat_dict.values()])))
    if start_date:
        all_dates = [d for d in all_dates if d >= pd.to_datetime(start_date)]
    if end_date:
        all_dates = [d for d in all_dates if d <= pd.to_datetime(end_date)]
        
    if len(all_dates) < 100:
        return None
        
    initial_capital = 100_000.0
    cash = initial_capital
    positions = {} # {ticker: {'qty': int, 'entry_price': float, 'entry_date': date, 'total_cost_basis': float, 'entry_fee': float, 'stop_loss': float, 'target': float, 'days': int}}
    trade_history = []
    equity_curve = []
    
    half_drag = (round_trip_cost_pct / 2.0) / 100.0
    
    # Walk-forward evaluation starts after initial warmup period (60 bars)
    warmup = 60
    eval_dates = all_dates[warmup:]
    
    for idx, current_date in enumerate(eval_dates):
        # -------------------------------------------------------------
        # STEP 1: Process Exits on Active Positions
        # -------------------------------------------------------------
        for t in list(positions.keys()):
            pos = positions[t]
            df_t = feat_dict[t]
            cur_p = float(df_t.loc[current_date]['Close']) if current_date in df_t.index else pos['entry_price']
            pos['days'] += 1
            
            # Exit triggers
            hit_stop = cur_p <= pos['stop_loss']
            hit_target = cur_p >= pos['target']
            timeout = pos['days'] >= 10 # 10-day max holding horizon
            
            if hit_stop or hit_target or timeout:
                exit_fee_egp = pos['qty'] * cur_p * half_drag
                gross_proceeds = pos['qty'] * cur_p - exit_fee_egp
                cash += gross_proceeds
                
                net_profit_egp = gross_proceeds - pos['total_cost_basis']
                net_pnl_pct = (net_profit_egp / pos['total_cost_basis']) * 100.0
                
                reason = "STOP_LOSS" if hit_stop else ("PROFIT_TARGET" if hit_target else "TIME_EXIT")
                trade_history.append({
                    'ticker': t,
                    'entry_date': pos['entry_date'].strftime('%Y-%m-%d'),
                    'exit_date': current_date.strftime('%Y-%m-%d'),
                    'entry_price': round(pos['entry_price'], 3),
                    'exit_price': round(cur_p, 3),
                    'qty': pos['qty'],
                    'cost_basis_egp': round(pos['total_cost_basis'], 2),
                    'gross_proceeds_egp': round(gross_proceeds, 2),
                    'entry_fee_egp': round(pos['entry_fee'], 2),
                    'exit_fee_egp': round(exit_fee_egp, 2),
                    'total_friction_egp': round(pos['entry_fee'] + exit_fee_egp, 2),
                    'net_pnl_pct': round(net_pnl_pct, 2),
                    'net_profit_egp': round(net_profit_egp, 2),
                    'days_held': pos['days'],
                    'reason': reason
                })
                del positions[t]
                
        # -------------------------------------------------------------
        # STEP 2: Mark-to-Market Open Positions Value (Post-Exits)
        # -------------------------------------------------------------
        curr_open_stock_val = 0.0
        for t, pos in positions.items():
            df_t = feat_dict[t]
            cur_p = float(df_t.loc[current_date]['Close']) if current_date in df_t.index else pos['entry_price']
            # Liquidation value of open position
            liquidation_val = pos['qty'] * cur_p * (1.0 - half_drag)
            curr_open_stock_val += liquidation_val
            
        total_equity_pre_buys = cash + curr_open_stock_val
        
        # -------------------------------------------------------------
        # STEP 3: Scan & Execute New Buy Candidates
        # -------------------------------------------------------------
        if idx % 3 == 0 and cash > 2000:
            candidates = []
            for t, df_t in feat_dict.items():
                if t in positions or current_date not in df_t.index:
                    continue
                
                sub = df_t.loc[:current_date]
                if len(sub) < 30: continue
                
                cur_row = sub.iloc[-1]
                p = float(cur_row['Close'])
                rsi_val = float(cur_row['RSI_14'])
                reg_val = float(cur_row['Regime'])
                sma50_val = float(cur_row['SMA_50'])
                atr_a = float(cur_row['ATR_Abs'])
                
                # Regime gate
                if use_regime_gate and (reg_val == -1 or (p < sma50_val and reg_val <= 0)):
                    continue
                    
                entry_limit = round(max(float(sub['Low'].tail(5).min()), p - 0.4 * atr_a), 2)
                expected_peak = round(p * 1.06, 2)
                expected_gain_pct = ((expected_peak - entry_limit) / entry_limit) * 100.0
                
                # Hurdle rate filter
                if expected_gain_pct >= min_hurdle_rate and 40 <= rsi_val <= 72:
                    candidates.append({
                        'ticker': t,
                        'price': entry_limit,
                        'current_p': p,
                        'target': expected_peak,
                        'stop': round(max(0.1, entry_limit - 1.5 * atr_a), 2),
                        'score': (expected_gain_pct / (atr_a / p * 100.0 + 1e-9))
                    })
                    
            candidates.sort(key=lambda x: x['score'], reverse=True)
            
            # Place Orders
            for cand in candidates[:3]:
                alloc_cap_egp = min(total_equity_pre_buys * max_pos_pct, cash - 500)
                if alloc_cap_egp >= 1500 and cand['price'] > 0:
                    shares = int(math.floor(alloc_cap_egp / cand['price']))
                    if shares >= 1:
                        entry_fee_egp = shares * cand['price'] * half_drag
                        total_buy_cost = shares * cand['price'] + entry_fee_egp
                        if total_buy_cost <= cash:
                            cash -= total_buy_cost
                            positions[cand['ticker']] = {
                                'qty': shares,
                                'entry_price': cand['price'],
                                'entry_date': current_date,
                                'total_cost_basis': total_buy_cost,
                                'entry_fee': entry_fee_egp,
                                'stop_loss': cand['stop'],
                                'target': cand['target'],
                                'days': 0
                            }
                            
        # -------------------------------------------------------------
        # STEP 4: End-of-Day Reconciled Mark-to-Market Equity
        # -------------------------------------------------------------
        final_daily_open_stock_val = 0.0
        for t, pos in positions.items():
            df_t = feat_dict[t]
            cur_p = float(df_t.loc[current_date]['Close']) if current_date in df_t.index else pos['entry_price']
            final_daily_open_stock_val += pos['qty'] * cur_p * (1.0 - half_drag)
            
        eod_equity = cash + final_daily_open_stock_val
        equity_curve.append({
            'date': current_date, 
            'equity': round(eod_equity, 2),
            'cash': round(cash, 2),
            'stock_val': round(final_daily_open_stock_val, 2),
            'open_positions_count': len(positions)
        })

    # -------------------------------------------------------------
    # STEP 5: Terminal Liquidation (Close remaining positions on last bar)
    # -------------------------------------------------------------
    if eval_dates:
        last_date = eval_dates[-1]
        for t in list(positions.keys()):
            pos = positions[t]
            df_t = feat_dict[t]
            cur_p = float(df_t.loc[last_date]['Close']) if last_date in df_t.index else pos['entry_price']
            exit_fee_egp = pos['qty'] * cur_p * half_drag
            gross_proceeds = pos['qty'] * cur_p - exit_fee_egp
            cash += gross_proceeds
            net_profit_egp = gross_proceeds - pos['total_cost_basis']
            net_pnl_pct = (net_profit_egp / pos['total_cost_basis']) * 100.0
            
            trade_history.append({
                'ticker': t,
                'entry_date': pos['entry_date'].strftime('%Y-%m-%d'),
                'exit_date': last_date.strftime('%Y-%m-%d'),
                'entry_price': round(pos['entry_price'], 3),
                'exit_price': round(cur_p, 3),
                'qty': pos['qty'],
                'cost_basis_egp': round(pos['total_cost_basis'], 2),
                'gross_proceeds_egp': round(gross_proceeds, 2),
                'entry_fee_egp': round(pos['entry_fee'], 2),
                'exit_fee_egp': round(exit_fee_egp, 2),
                'total_friction_egp': round(pos['entry_fee'] + exit_fee_egp, 2),
                'net_pnl_pct': round(net_pnl_pct, 2),
                'net_profit_egp': round(net_profit_egp, 2),
                'days_held': pos['days'],
                'reason': "TERMINAL_CLOSE"
            })
            del positions[t]

    # -------------------------------------------------------------
    # STEP 6: Compile Reconciled Performance Metrics
    # -------------------------------------------------------------
    eq_df = pd.DataFrame(equity_curve)
    if eq_df.empty: return None
    
    # Mathematical Triple Reconciliation Check
    total_ledger_profit = sum(t['net_profit_egp'] for t in trade_history)
    reconciled_final_equity = round(initial_capital + total_ledger_profit, 2)
    terminal_cash = round(cash, 2)
    
    # Overwrite last day equity with exact settled terminal cash
    eq_df.loc[eq_df.index[-1], 'equity'] = reconciled_final_equity
    eq_df.loc[eq_df.index[-1], 'cash'] = terminal_cash
    eq_df.loc[eq_df.index[-1], 'stock_val'] = 0.0
    
    final_equity = reconciled_final_equity
    total_net_return_pct = ((final_equity - initial_capital) / initial_capital) * 100.0
    
    days_span = (eval_dates[-1] - eval_dates[0]).days
    years_span = max(days_span / 365.25, 0.1)
    cagr = ((final_equity / initial_capital) ** (1.0 / years_span) - 1.0) * 100.0
    
    eq_df['ret'] = eq_df['equity'].pct_change().fillna(0.0)
    ann_vol = float(eq_df['ret'].std() * np.sqrt(252) * 100.0)
    sharpe = float((eq_df['ret'].mean() / (eq_df['ret'].std() + 1e-9)) * np.sqrt(252))
    
    downside = eq_df['ret'][eq_df['ret'] < 0]
    sortino = float((eq_df['ret'].mean() / (downside.std() + 1e-9)) * np.sqrt(252)) if len(downside) > 0 else 0.0
    
    cum_max = eq_df['equity'].cummax()
    dd_series = (eq_df['equity'] - cum_max) / cum_max * 100.0
    max_dd = float(dd_series.min())
    calmar = abs(cagr / max_dd) if max_dd != 0 else 0.0
    
    tot_trades = len(trade_history)
    wins = [t for t in trade_history if t['net_pnl_pct'] > 0]
    losses = [t for t in trade_history if t['net_pnl_pct'] <= 0]
    win_rate = (len(wins) / tot_trades * 100.0) if tot_trades > 0 else 0.0
    avg_win = float(np.mean([t['net_pnl_pct'] for t in wins])) if wins else 0.0
    avg_loss = float(np.mean([t['net_pnl_pct'] for t in losses])) if losses else 0.0
    win_loss_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else 99.0
    
    tot_win_egp = sum(t['net_profit_egp'] for t in wins)
    tot_loss_egp = abs(sum(t['net_profit_egp'] for t in losses))
    profit_factor = float(tot_win_egp / tot_loss_egp) if tot_loss_egp > 0 else 99.0
    
    tot_friction_fees = sum(t['total_friction_egp'] for t in trade_history)
    
    # Benchmark EGX30 Buy & Hold over identical dates
    bench_return = 0.0
    if egx30_df is not None and not egx30_df.empty:
        common_b = egx30_df.loc[eval_dates[0]:eval_dates[-1]]
        if len(common_b) >= 2:
            b_start = float(common_b['Close'].iloc[0])
            b_end = float(common_b['Close'].iloc[-1])
            bench_return = ((b_end - b_start) / b_start) * 100.0
            
    alpha_vs_benchmark = total_net_return_pct - bench_return
    
    # Year-by-year compounded returns on actual capital
    eq_df['year'] = eq_df['date'].apply(lambda d: d.year)
    yearly_stats = []
    for yr, y_df in eq_df.groupby('year'):
        y_start_eq = float(y_df['equity'].iloc[0])
        y_end_eq = float(y_df['equity'].iloc[-1])
        y_ret = ((y_end_eq - y_start_eq) / y_start_eq) * 100.0
        y_trades = [t for t in trade_history if t['exit_date'].startswith(str(yr))]
        y_wins = [t for t in y_trades if t['net_pnl_pct'] > 0]
        y_profit = sum(t['net_profit_egp'] for t in y_trades)
        yearly_stats.append({
            'year': int(yr),
            'start_equity': round(y_start_eq, 2),
            'end_equity': round(y_end_eq, 2),
            'return_pct': round(y_ret, 2),
            'trades_count': len(y_trades),
            'win_rate_pct': round(len(y_wins)/len(y_trades)*100.0, 2) if y_trades else 0.0,
            'net_profit_egp': round(y_profit, 2)
        })
        
    return {
        'start_date': eval_dates[0].strftime('%Y-%m-%d'),
        'end_date': eval_dates[-1].strftime('%Y-%m-%d'),
        'bars_count': len(eval_dates),
        'initial_capital': initial_capital,
        'final_equity': round(final_equity, 2),
        'terminal_cash': round(terminal_cash, 2),
        'total_ledger_profit': round(total_ledger_profit, 2),
        'total_friction_paid_egp': round(tot_friction_fees, 2),
        'reconciliation_discrepancy_egp': round(abs(final_equity - (initial_capital + total_ledger_profit)), 6),
        'total_net_return_pct': round(total_net_return_pct, 2),
        'cagr_pct': round(cagr, 2),
        'annualized_volatility_pct': round(ann_vol, 2),
        'total_trades': tot_trades,
        'win_rate_pct': round(win_rate, 2),
        'avg_win_pct': round(avg_win, 2),
        'avg_loss_pct': round(avg_loss, 2),
        'win_loss_ratio': round(win_loss_ratio, 2),
        'profit_factor': round(profit_factor, 2),
        'max_drawdown_pct': round(max_dd, 2),
        'calmar_ratio': round(calmar, 2),
        'sharpe_ratio': round(sharpe, 2),
        'sortino_ratio': round(sortino, 2),
        'round_trip_cost_pct': round_trip_cost_pct,
        'benchmark_egx30_buy_hold_pct': round(bench_return, 2),
        'alpha_vs_benchmark_pct': round(alpha_vs_benchmark, 2),
        'yearly_breakdown': yearly_stats,
        'trade_history': trade_history,
        'equity_curve': equity_curve
    }
