import sys
sys.stdout.reconfigure(encoding='utf-8')
import datetime
import os
import json
import warnings
import pandas as pd
import numpy as np
import requests
import traceback
import hashlib

warnings.filterwarnings('ignore')

from sklearn.preprocessing import RobustScaler
from sklearn.ensemble import HistGradientBoostingClassifier

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
JOURNAL_FILE = os.path.join(BASE_DIR, "paper_trading_journal.json")

# ==============================================================================
# FROZEN PRODUCTION PARAMETERS (30-DAY LOGGING WINDOW)
# ==============================================================================
HURDLE_RATE_PCT = 3.0
POSITION_CAP = 0.10
FRICTION_PCT = 0.90 # 0.45% entry + 0.45% exit
SMA50_GATE_ACTIVE = True

EXPANDED_68_EGX_UNIVERSE = {
    # 🏦 خدمات مالية وبنوك واستثمار غير مصرفي
    "COMI.CA": ("التجاري الدولي", "خدمات مالية وبنوك 🏦"),
    "ADIB.CA": ("مصرف أبو ظبي الإسلامي", "خدمات مالية وبنوك 🏦"),
    "QNBA.CA": ("قطر الوطني الأهلي", "خدمات مالية وبنوك 🏦"),
    "HRHO.CA": ("إي إف جي هيرميس القابضة", "خدمات مالية وبنوك 🏦"),
    "BTFH.CA": ("بلتون القابضة", "خدمات مالية وبنوك 🏦"),
    "CICH.CA": ("سي آي كابيتال", "خدمات مالية وبنوك 🏦"),
    "CNFN.CA": ("كونتاكت المالية القابضة", "خدمات مالية غير مصرفية 🏦"),
    "OFH.CA": ("أوراسكوم المالية القابضة", "خدمات مالية غير مصرفية 🏦"),
    "PIOH.CA": ("بايونيرز القابضة", "خدمات مالية وبنوك 🏦"),
    "EXPA.CA": ("المصري لتنمية الصادرات", "خدمات مالية وبنوك 🏦"),
    "BINV.CA": ("بي انفستمنتس القابضة", "خدمات مالية وبنوك 🏦"),
    "EGBE.CA": ("البنك المصري الخليجي", "خدمات مالية وبنوك 🏦"),
    "CIEB.CA": ("كريدي أجريكول مصر", "خدمات مالية وبنوك 🏦"),
    "FAIT.CA": ("فيصل الإسلامي بالجنيه", "خدمات مالية وبنوك 🏦"),
    "SAUD.CA": ("بنك البركة مصر", "خدمات مالية وبنوك 🏦"),

    # 🏗️ عقارات واستثمار عقاري
    "TMGH.CA": ("مجموعة طلعت مصطفى", "عقارات وإنشاءات 🏗️"),
    "PHDC.CA": ("بالم هيلز للتعمير", "عقارات وإنشاءات 🏗️"),
    "HELI.CA": ("مصر الجديدة للإسكان", "عقارات وإنشاءات 🏗️"),
    "MASR.CA": ("مدينة مصر للإسكان", "عقارات وإنشاءات 🏗️"),
    "ORAS.CA": ("أوراسكوم للإنشاءات", "عقارات وإنشاءات 🏗️"),
    "ORHD.CA": ("أوراسكوم للتنمية مصر", "عقارات وإنشاءات 🏗️"),
    "UNIT.CA": ("المتحدة للإسكان والتعمير", "عقارات وإنشاءات 🏗️"),
    "ODOD.CA": ("الشمس للإسكان والتعمير", "عقارات وإنشاءات 🏗️"),
    "EMFD.CA": ("إعمار مصر للتنمية", "عقارات وإنشاءات 🏗️"),
    "AMER.CA": ("مجموعة عامر جروب", "عقارات وإنشاءات 🏗️"),
    "UEGC.CA": ("الصعيد العامة للمقاولات", "عقارات وإنشاءات 🏗️"),
    "ACGC.CA": ("العربية لحجيج الأقطان", "عقارات وإنشاءات 🏗️"),

    # 🏭 صناعة وموارد ومواد بناء
    "SWDY.CA": ("السويدي إلكتريك", "صناعة وموارد 🏭"),
    "ESRS.CA": ("حديد عز", "صناعة وموارد 🏭"),
    "EGAL.CA": ("مصر للالومنيوم", "صناعة وموارد 🏭"),
    "ALCN.CA": ("الإسكندرية لتداول الحاويات", "خدمات لوجستية ونقل 🛳️"),
    "GBCO.CA": ("جي بي كورب (غبور)", "صناعة وتوزيع سيارات 🏭"),
    "ORWE.CA": ("النساجون الشرقيون", "صناعة وموارد 🏭"),
    "ARCC.CA": ("العربية للاسمنت", "مواد بناء 🏭"),
    "CERA.CA": ("الجوهرة / ريماس سيراميك", "مواد بناء 🏭"),
    "MCQE.CA": ("مصر لأسمنت قنا", "مواد بناء 🏭"),
    "SVCE.CA": ("جنوب الوادي للاسمنت", "مواد بناء 🏭"),
    "IRAX.CA": ("الوطنية للصناعات الحديدية", "صناعة وموارد 🏭"),
    "DSCW.CA": ("دايس للملابس الجاهزة", "غزل ونسيج 🏭"),

    # 🧪 بتروكيماويات وأسمدة وطاقة
    "ABUK.CA": ("أبو قير للأسمدة", "بتروكيماويات وأسمدة 🧪"),
    "MFPC.CA": ("موبكو للأسمدة", "بتروكيماويات وأسمدة 🧪"),
    "SKPC.CA": ("سيدي كرير للبتروكيماويات", "بتروكيماويات وأسمدة 🧪"),
    "AMOC.CA": ("أموك للبترول", "بتروكيماويات وأسمدة 🧪"),
    "EKHO.CA": ("القابضة المصرية الكويتية", "بتروكيماويات وأسمدة 🧪"),
    "PACH.CA": ("باكين للبويات والصناعات", "بتروكيماويات وأسمدة 🧪"),
    "KIMA.CA": ("الصناعات الكيماوية كيما", "بتروكيماويات وأسمدة 🧪"),

    # 🥗 أغذية ورعاية صحية وأدوية
    "JUFO.CA": ("جهينة للصناعات الغذائية", "أغذية وأدوية 🥗"),
    "DOMT.CA": ("دومتي للصناعات الغذائية", "أغذية وأدوية 🥗"),
    "ISPH.CA": ("ابن سينا فارما", "أغذية وأدوية 🥗"),
    "CLHO.CA": ("كليوباترا للمستشفيات", "رعاية صحية 🥗"),
    "RMDA.CA": ("راميدا فارما", "أغذية وأدوية 🥗"),
    "EFID.CA": ("إديتا للصناعات الغذائية", "أغذية وأدوية 🥗"),
    "AJWA.CA": ("أجواء للصناعات الغذائية", "أغذية وأدوية 🥗"),
    "CICP.CA": ("القاهرة للزيوت والصابون", "أغذية وأدوية 🥗"),
    "DAPH.CA": ("العربية للأدوية", "أغذية وأدوية 🥗"),
    "NIPH.CA": ("النيل للأدوية", "أغذية وأدوية 🥗"),
    "MPCI.CA": ("ممفيس للأدوية", "أغذية وأدوية 🥗"),

    # 📱 اتصالات وتكنولوجيا واستثمار
    "FWRY.CA": ("فوري للمدفوعات", "اتصالات وتكنولوجيا 📱"),
    "ETEL.CA": ("المصرية للاتصالات", "اتصالات وتكنولوجيا 📱"),
    "RAYA.CA": ("راية القابضة", "اتصالات وتكنولوجيا 📱"),
    "RCTC.CA": ("راية لخدمات مراكز الاتصال", "اتصالات وتكنولوجيا 📱"),
    "OIH.CA": ("أوراسكوم للاستثمار القابضة", "تكنولوجيا واستثمار 📱"),

    # 🏖️ سياحة وفنادق وخدمات تعليمية
    "EGTS.CA": ("المصرية للممنتجعات السياحية", "سياحة وترفيه 🏖️"),
    "MHOT.CA": ("مصر للفنادق", "سياحة وترفيه 🏖️"),
    "CIRA.CA": ("القاهرة للاستثمار CIRA", "خدمات تعليمية 🎓")
}

def safe_download(ticker):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=2y"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        res = requests.get(url, headers=headers, timeout=8)
        if res.status_code == 200:
            data = res.json()
            if 'chart' in data and data['chart']['result']:
                result = data['chart']['result'][0]
                timestamps = result['timestamp']
                quote = result['indicators']['quote'][0]
                adj = result['indicators'].get('adjclose', [{}])[0].get('adjclose', quote['close'])
                
                df = pd.DataFrame({
                    'Open': quote['open'],
                    'High': quote['high'],
                    'Low': quote['low'],
                    'Close': quote['close'],
                    'Adj_Close': adj,
                    'Volume': quote['volume']
                }, index=pd.to_datetime(timestamps, unit='s'))
                
                df.dropna(subset=['Close'], inplace=True)
                df['Adj_Close'].fillna(df['Close'], inplace=True)
                df.index = df.index.tz_localize(None).normalize()
                return df
    except Exception as e:
        pass
    return pd.DataFrame()

def load_journal():
    if os.path.exists(JOURNAL_FILE):
        try:
            with open(JOURNAL_FILE, "r", encoding="utf-8") as f:
                raw_journal = json.load(f)
                # Purge any invalid entries with confidence_prob <= 0.50
                valid_journal = []
                for item in raw_journal:
                    if item.get("confidence_prob", 0.0) > 0.50:
                        valid_journal.append(item)
                    else:
                        print(f"  🗑️ PURGING INVALID JOURNAL ENTRY: Ticker {item.get('ticker')} with confidence_prob {item.get('confidence_prob')} <= 0.50")
                return valid_journal
        except Exception:
            pass
    return []

def save_journal(journal):
    with open(JOURNAL_FILE, "w", encoding="utf-8") as f:
        json.dump(journal, f, ensure_ascii=False, indent=2)

def run_daily_paper_trading():
    print(f"EXECUTION_TIMESTAMP: {datetime.datetime.now().isoformat()}")
    print("==================================================================")
    print("📝 AUTOMATED DAILY PAPER TRADING LOGGER & EVALUATOR (STRICT THRESHOLD)")
    print("==================================================================")
    
    journal = load_journal()
    
    # 1. Evaluate PENDING trades whose 5-day evaluation horizon has elapsed
    today_dt = datetime.datetime.now()
    today_str = today_dt.strftime('%Y-%m-%d')
    
    for entry in journal:
        if entry.get("status") == "PENDING":
            eval_date_str = entry.get("eval_date")
            if today_str >= eval_date_str:
                ticker = entry.get("ticker")
                df_curr = safe_download(ticker)
                if not df_curr.empty:
                    latest_price = df_curr['Adj_Close'].iloc[-1]
                    entry_price = entry.get("simulated_fill_price", entry.get("suggested_entry_price", entry.get("entry_price")))
                    
                    shares = entry.get("order_shares", 100)
                    gross_proceeds = shares * latest_price
                    cost_basis = shares * entry_price
                    
                    gross_pnl = gross_proceeds - cost_basis
                    entry_fee = cost_basis * (FRICTION_PCT / 2 / 100)
                    exit_fee = gross_proceeds * (FRICTION_PCT / 2 / 100)
                    total_friction = entry_fee + exit_fee
                    net_pnl = gross_pnl - total_friction
                    
                    pnl_pct = (net_pnl / cost_basis) * 100.0 if cost_basis > 0 else 0.0
                    
                    entry["exit_price"] = round(float(latest_price), 2)
                    entry["exit_date"] = today_str
                    entry["net_pnl_pct"] = round(float(pnl_pct), 2)
                    entry["gross_pnl_egp"] = round(float(gross_pnl), 2)
                    entry["friction_costs_egp"] = round(float(total_friction), 2)
                    entry["net_pnl_egp"] = round(float(net_pnl), 2)
                    
                    if pnl_pct <= -6.0:
                        entry["exit_reason"] = "STOP_HIT"
                    elif pnl_pct >= 8.0:
                        entry["exit_reason"] = "TARGET_HIT"
                    else:
                        entry["exit_reason"] = "TIME_EXPIRY"
                        
                    entry["status"] = "COMPLETED"
                    print(f"  ✓ Updated PENDING Trade: {ticker} | Entry: {entry_price} | Exit: {latest_price:.2f} | Net PnL: {pnl_pct:+.2f}% | Reason: {entry['exit_reason']}")
    
    # 2. Fetch Market Data & Filter Out Stale Tickers (> 7 days old)
    max_date = None
    downloaded_dfs = {}
    for t in EXPANDED_68_EGX_UNIVERSE.keys():
        df = safe_download(t)
        if not df.empty and len(df) > 80:
            last_bar = df.index[-1]
            if max_date is None or last_bar > max_date:
                max_date = last_bar
            downloaded_dfs[t] = df

    active_downloaded_dfs = {}
    for t, df in downloaded_dfs.items():
        if (max_date - df.index[-1]).days <= 7:
            active_downloaded_dfs[t] = df
        else:
            print(f"  ⚠️ Excluded stale ticker {t} (Last bar: {df.index[-1].strftime('%Y-%m-%d')})")
            
    downloaded_dfs = active_downloaded_dfs

    usd_egp_df = safe_download("USDEGP=X")
    egx30_df = safe_download("EGX30.CA")
    usd_mom_5d = usd_egp_df['Close'].pct_change(5) * 100.0 if not usd_egp_df.empty else pd.Series(0.0)
    egx30_mom_10d = egx30_df['Adj_Close'].pct_change(10) * 100.0 if not egx30_df.empty else pd.Series(0.0)

    feature_cols = ['Mom_1D', 'Mom_5D', 'Mom_10D', 'Mom_20D', 'Volume_ZScore', 'RSI_14', 'ATR_Percent', 'Distance_OB', 'USD_EGP_Mom_5D', 'EGX30_Mom_10D']

    processed_dfs = []
    for t, df in downloaded_dfs.items():
        c = df['Adj_Close']
        df['Mom_1D'] = c.pct_change(1) * 100.0
        df['Mom_5D'] = c.pct_change(5) * 100.0
        df['Mom_10D'] = c.pct_change(10) * 100.0
        df['Mom_20D'] = c.pct_change(20) * 100.0
        
        vol_ma = df['Volume'].rolling(20).mean()
        vol_std = df['Volume'].rolling(20).std()
        df['Volume_ZScore'] = ((df['Volume'] - vol_ma) / (vol_std + 1e-9)).clip(-3, 3)
        
        delta = c.diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        df['RSI_14'] = 100 - (100 / (1 + (gain / (loss + 1e-9))))
        
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - c.shift())
        low_close = np.abs(df['Low'] - c.shift())
        atr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1).rolling(14).mean()
        df['ATR_Percent'] = (atr / c) * 100.0
        
        low_10 = df['Low'].rolling(10).min()
        df['Distance_OB'] = ((c - low_10) / (low_10 + 1e-9)) * 100.0
        
        df['USD_EGP_Mom_5D'] = usd_mom_5d.reindex(df.index).ffill().fillna(0.0)
        df['EGX30_Mom_10D'] = egx30_mom_10d.reindex(df.index).ffill().fillna(0.0)
        
        df['Target_5D_Dir'] = ((c.shift(-5) - c) / c > 0.006).astype(int)
        df.dropna(subset=feature_cols + ['Target_5D_Dir'], inplace=True)
        df['Ticker'] = t
        processed_dfs.append(df)

    all_data = pd.concat(processed_dfs).sort_index()

    scaler = RobustScaler()
    X_all = scaler.fit_transform(all_data[feature_cols].values)
    y_all = all_data['Target_5D_Dir'].values.astype(int)

    data_hash = hashlib.sha256(pd.util.hash_pandas_object(all_data[feature_cols]).values).hexdigest()
    config_hash = hashlib.sha256(b"HistGB_max_iter=40_lr=0.05_md=3").hexdigest()

    clf = HistGradientBoostingClassifier(max_iter=40, learning_rate=0.05, max_depth=3, random_state=42)
    clf.fit(X_all, y_all)

    # 3. Live Signal scoring with STRICT DUAL CONDITION:
    # (a) confidence_prob > 0.50 AND (b) top N highest ranked
    candidate_recs = []
    for t, df in downloaded_dfs.items():
        latest_row = df.iloc[-1:]
        X_live = scaler.transform(latest_row[feature_cols].values)
        prob = clf.predict_proba(X_live)[0, 1]
        
        if prob > 0.50: # STRICT MINIMUM ABSOLUTE THRESHOLD CONDITION (a)
            entry_price = float(latest_row['Adj_Close'].iloc[0])
            bar_date = latest_row.index[0].strftime('%Y-%m-%d')
            eval_date = (latest_row.index[0] + datetime.timedelta(days=7)).strftime('%Y-%m-%d')
            
            simulated_fill = entry_price * 1.002 # 0.2% typical slippage
            allocated_cash = 10000.0 # Mock dynamic cash allocation
            shares = int(allocated_cash / simulated_fill)
            
            candidate_recs.append({
                "trade_id": f"{t}_{bar_date}",
                "ticker": t,
                "name": EXPANDED_68_EGX_UNIVERSE[t][0],
                "sector": EXPANDED_68_EGX_UNIVERSE[t][1],
                "signal_type": "STRONG BUY" if prob > 0.70 else "BUY",
                "entry_date": bar_date,
                "suggested_entry_price": round(entry_price, 2),
                "simulated_fill_price": round(simulated_fill, 2),
                "slippage_incurred_pct": 0.20,
                "stop_loss": round(entry_price * 0.94, 2),
                "peak_target": round(entry_price * 1.12, 2),
                "order_shares": shares,
                "allocated_cash_egp": round(shares * simulated_fill, 2),
                "confidence_prob": round(float(prob), 4),
                "eval_date": eval_date,
                "status": "PENDING",
                "log_timestamp": datetime.datetime.now().isoformat(),
                "model_version": "v3.0",
                "feature_version": "1.2",
                "training_cutoff_date": all_data.index.max().strftime('%Y-%m-%d') if not all_data.empty else "N/A",
                "training_data_hash": data_hash,
                "config_hash": config_hash
            })

    candidate_recs.sort(key=lambda x: x["confidence_prob"], reverse=True)
    top_recommendations = candidate_recs[:3] # TOP RANKED CONDITION (b)

    existing_ids = {item["trade_id"] for item in journal}
    new_added = 0
    for rec in top_recommendations:
        if rec["trade_id"] not in existing_ids:
            journal.append(rec)
            new_added += 1

    save_journal(journal)
    
    print(f"\n✓ Saved {new_added} new live recommendations with confidence_prob > 0.50 into paper trading journal.")
    print("==================================================================")
    print("📋 CURRENT PAPER TRADING JOURNAL CONTENTS:")
    print("==================================================================")
    print(json.dumps(journal, ensure_ascii=False, indent=2))
    print("==================================================================")
    print("✅ Paper trading daily logger execution complete.")

if __name__ == "__main__":
    run_daily_paper_trading()
