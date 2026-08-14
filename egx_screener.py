import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
import datetime
import warnings
import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.preprocessing import RobustScaler
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import TimeSeriesSplit

warnings.filterwarnings('ignore')

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()

def main():
    print("="*140)
    print("🏛️ [الرادار الكشاف العالمي - منظومة التوقعات لـ 5 أيام قادمة] Global Pooled EGX Screener Gen-12")
    print("🌐 النموذج يتغذى على بيانات الأسهم العالمية + المؤشرات الإقليمية + اقتصاديات الكلي لحماية واستثمار رأس المال")
    print("="*140)

    # 1. قائمة الأسهم المصرية المستهدفة للفحص والتوقع
    EGX_STOCKS = {
        "التجاري الدولي": "COMI.CA",
        "طلعت مصطفى": "TMGH.CA",
        "السويدي إلكتريك": "SWDY.CA",
        "إي إف جي هيرميس": "HRHO.CA",
        "فوري": "FWRY.CA",
        "بالم هيلز": "PHDC.CA",
        "حديد عز": "ESRS.CA",
        "مصر الجديدة للإسكان": "HELI.CA",
        "أموك": "AMOC.CA",
        "ابن سينا فارما": "ISPH.CA",
        "المصرية للاتصالات": "ETEL.CA",
        "أبو قير للأسمدة": "ABUK.CA",
        "موبكو": "MFPC.CA"
    }

    # 2. حوض التدريب العالمي المجمع (Pooled Global Training Pool)
    # يحتوي على أسهم أمريكية عالمية، أسواق ناشئة، أسهم خليجية وإقليمية، بالإضافة للأسهم المصرية
    GLOBAL_TRAINING_POOL = [
        "AAPL", "MSFT", "NVDA", "JPM", "XOM", "CAT", "SPY", 
        "EEM", "TUR", "1120.SR", "EMAAR.AE"
    ] + list(EGX_STOCKS.values())

    START_DATE = "2020-01-01"
    END_DATE = datetime.date.today().strftime("%Y-%m-%d")

    print("\n[1/4] 🌐 جلب بيانات الماكرو الكلية (الذهب، النفط، الدولار، الفائدة الأمريكية، مؤشر الأسواق الناشئة S&P 500)...")

    def safe_download(ticker):
        try:
            data = yf.download(ticker, start=START_DATE, end=END_DATE, progress=False)
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.droplevel(1)
            return data
        except Exception:
            return pd.DataFrame()

    usd_df = safe_download("USDEGP=X")
    if usd_df.empty: usd_df = safe_download("EGP=X")
    gold_df = safe_download("GC=F")
    oil_df = safe_download("BZ=F")
    if oil_df.empty: oil_df = safe_download("CL=F")
    tnx_df = safe_download("^TNX")
    eem_df = safe_download("EEM")
    spy_df = safe_download("SPY")

    def extract_series(df_in):
        if not df_in.empty and 'Close' in df_in.columns:
            s = df_in['Close'].ffill()
            if isinstance(s, pd.DataFrame): s = s.iloc[:, 0]
            return s
        return None

    usd_s = extract_series(usd_df)
    gold_s = extract_series(gold_df)
    oil_s = extract_series(oil_df)
    tnx_s = extract_series(tnx_df)
    eem_s = extract_series(eem_df)
    spy_s = extract_series(spy_df)

    # جدول الفائدة للبنك المركزي المصري
    cbe_rates = [
        ("2020-01-01", 12.25), ("2020-03-17", 9.25), ("2020-09-25", 8.75), ("2020-11-13", 8.25),
        ("2022-03-21", 9.25), ("2022-05-19", 11.25), ("2022-10-27", 13.25), ("2022-12-22", 16.25),
        ("2023-03-30", 18.25), ("2023-08-03", 19.25), ("2024-02-01", 21.25), ("2024-03-06", 27.25),
        ("2025-04-17", 25.00), ("2025-05-22", 24.00), ("2025-08-28", 22.00), ("2025-10-02", 21.00),
        ("2025-12-25", 20.00), ("2026-02-12", 19.00)
    ]

    funds_file = os.path.join(BASE_DIR, 'egx_fundamentals.csv')
    funds_df = pd.read_csv(funds_file, parse_dates=['Date']) if os.path.exists(funds_file) else pd.DataFrame()

    def build_features_for_stock(ticker):
        try:
            s_df = safe_download(ticker)
            if s_df.empty or len(s_df) < 80:
                return None
            
            s_df.index = s_df.index.tz_localize(None).normalize()
            
            # المؤشرات الفنية المحايدة للحجم والتسق (Scale-Invariant Technical Features)
            s_df['Mom_1D'] = s_df['Close'].pct_change(1) * 100.0
            s_df['Mom_5D'] = s_df['Close'].pct_change(5) * 100.0
            s_df['Mom_10D'] = s_df['Close'].pct_change(10) * 100.0
            
            vol_ma_20 = s_df['Volume'].rolling(20).mean()
            vol_std_20 = s_df['Volume'].rolling(20).std()
            s_df['Volume_ZScore'] = ((s_df['Volume'] - vol_ma_20) / (vol_std_20 + 1e-9)).clip(-3, 3)
            
            price_change = s_df['Close'].diff()
            s_df['Institutional_Flow_Proxy'] = s_df['Volume_ZScore'] * np.sign(price_change.fillna(0))
            
            s_df['Price_Range_Imbalance'] = ((s_df['Close'] - s_df['Low']) - (s_df['High'] - s_df['Close'])) / ((s_df['High'] - s_df['Low']) + 1e-9)
            
            log_hl = np.log(s_df['High'] / (s_df['Low'] + 1e-9))**2
            log_co = np.log(s_df['Close'] / (s_df['Open'] + 1e-9))**2
            s_df['GK_Volatility'] = np.sqrt(np.maximum(0.0, 0.5 * log_hl - (2 * np.log(2) - 1) * log_co))
            
            high_low = s_df['High'] - s_df['Low']
            high_close = np.abs(s_df['High'] - s_df['Close'].shift())
            low_close = np.abs(s_df['Low'] - s_df['Close'].shift())
            atr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1).rolling(14).mean()
            s_df['ATR_Percent'] = (atr / s_df['Close']) * 100.0
            
            up_move = s_df['High'] - s_df['High'].shift(1)
            down_move = s_df['Low'].shift(1) - s_df['Low']
            plus_di = 100 * (pd.Series(np.where((up_move > down_move) & (up_move > 0), up_move, 0), index=s_df.index).ewm(alpha=1/14).mean() / (atr + 1e-9))
            minus_di = 100 * (pd.Series(np.where((down_move > up_move) & (down_move > 0), down_move, 0), index=s_df.index).ewm(alpha=1/14).mean() / (atr + 1e-9))
            s_df['ADX_14'] = (100 * (np.abs(plus_di - minus_di) / (plus_di + minus_di + 1e-9))).ewm(alpha=1/14).mean()
            
            ema12 = s_df['Close'].ewm(span=12, adjust=False).mean()
            ema26 = s_df['Close'].ewm(span=26, adjust=False).mean()
            macd_line = ema12 - ema26
            macd_signal = macd_line.ewm(span=9, adjust=False).mean()
            s_df['MACD_Hist_Norm'] = (macd_line - macd_signal) / s_df['Close'] * 100.0
            
            sma20 = s_df['Close'].rolling(20).mean()
            std20 = s_df['Close'].rolling(20).std()
            s_df['BB_Percent_B'] = (s_df['Close'] - (sma20 - 2 * std20)) / (4 * std20 + 1e-9)
            
            obv = (np.sign(price_change.fillna(0)) * s_df['Volume']).fillna(0).cumsum()
            s_df['OBV_Mom_5D'] = obv.pct_change(5) * 100.0
            
            low14 = s_df['Low'].rolling(14).min()
            high14 = s_df['High'].rolling(14).max()
            s_df['Stoch_K'] = 100 * ((s_df['Close'] - low14) / ((high14 - low14) + 1e-9))
            
            delta = s_df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            s_df['RSI_14'] = 100 - (100 / (1 + (gain / (loss + 1e-9))))

            # التأثيرات الكلية والعالمية (Global Macro Influence)
            s_df['Gold_Mom_5D'] = gold_s.reindex(s_df.index).ffill().pct_change(5) * 100.0 if gold_s is not None else 0.0
            s_df['Oil_Mom_5D'] = oil_s.reindex(s_df.index).ffill().pct_change(5) * 100.0 if oil_s is not None else 0.0
            s_df['EEM_Mom_5D'] = eem_s.reindex(s_df.index).ffill().pct_change(5) * 100.0 if eem_s is not None else 0.0
            s_df['SPY_Mom_5D'] = spy_s.reindex(s_df.index).ffill().pct_change(5) * 100.0 if spy_s is not None else 0.0
            s_df['US_10Y_Yield_Change'] = tnx_s.reindex(s_df.index).ffill().diff() if tnx_s is not None else 0.0
            
            # فائدة البنك المركزي المصري
            cbe_s = pd.Series(index=s_df.index, dtype=float)
            for date_str, rate in cbe_rates:
                dt = pd.to_datetime(date_str)
                cbe_s[cbe_s.index >= dt] = rate
            s_df['CBE_Interest_Rate'] = cbe_s.bfill().ffill()
            
            # مكرر الربحية الأساسي (P/E Ratio)
            s_df['PE_Ratio'] = 10.0
            if not funds_df.empty and ticker in funds_df['Ticker'].values:
                t_funds = funds_df[funds_df['Ticker'] == ticker].set_index('Date')
                if 'EPS' in t_funds.columns:
                    eps_series = t_funds['EPS'].reindex(s_df.index).ffill()
                    s_df['PE_Ratio'] = np.where(eps_series > 0, s_df['Close'] / eps_series, 10.0)
                    s_df['PE_Ratio'] = s_df['PE_Ratio'].fillna(10.0).clip(0, 100)

            return s_df
        except Exception as e:
            return None

    feature_cols = [
        'Mom_1D', 'Mom_5D', 'Mom_10D', 'Volume_ZScore', 'Institutional_Flow_Proxy',
        'Price_Range_Imbalance', 'GK_Volatility', 'ATR_Percent', 'ADX_14',
        'MACD_Hist_Norm', 'BB_Percent_B', 'OBV_Mom_5D', 'Stoch_K', 'RSI_14',
        'Gold_Mom_5D', 'Oil_Mom_5D', 'EEM_Mom_5D', 'SPY_Mom_5D', 'US_10Y_Yield_Change',
        'CBE_Interest_Rate', 'PE_Ratio'
    ]

    print(f"\n[2/4] 📚 تجميع بيانات التدريب المجمعة (Pooled Global Training) لـ {len(GLOBAL_TRAINING_POOL)} سهم ومؤشر عالمي وإقليمي...")
    
    global_dfs = []
    processed_dict = {}

    for t in GLOBAL_TRAINING_POOL:
        df_t = build_features_for_stock(t)
        if df_t is not None and not df_t.empty:
            df_t[feature_cols] = df_t[feature_cols].ffill().bfill()
            processed_dict[t] = df_t
            
            # نحسب أهداف الـ 5 أيام للتخزين في الداتا العالمية
            df_train = df_t.copy()
            for h in range(1, 6):
                df_train[f'Target_Return_{h}D'] = (df_train['Close'].shift(-h) - df_train['Close']) / df_train['Close']
            df_train['Target_Dir_5D'] = ((df_train['Close'].shift(-5) - df_train['Close']) / df_train['Close'] > 0.005).astype(int)
            
            df_train.dropna(subset=feature_cols + [f'Target_Return_{h}D' for h in range(1, 6)], inplace=True)
            if len(df_train) > 50:
                global_dfs.append(df_train)

    if not global_dfs:
        print("❌ تعذر تجميع بيانات كافية للتدريب.")
        return

    full_train_df = pd.concat(global_dfs, axis=0, ignore_index=True)
    print(f"✅ اكتمل بناء العينة العالمية المجمعة: إجمالي {len(full_train_df):,} صف تداول للتدريب!")

    print("\n[3/4] 🧠 تدريب النماذج المؤسسية المجمعة (Multi-Horizon Regressors + Calibrated Classifier)...")
    
    scaler = RobustScaler()
    X_train_global = scaler.fit_transform(full_train_df[feature_cols].values)

    # 1. تدريب 5 نماذج للتوقع السعري المباشر (Day 1..5)
    reg_models = {}
    for h in range(1, 6):
        y_h = full_train_df[f'Target_Return_{h}D'].values
        reg = HistGradientBoostingRegressor(max_iter=80, learning_rate=0.06, max_depth=4, random_state=42)
        reg.fit(X_train_global, y_h)
        reg_models[h] = reg

    # 2. تدريب نموذج الثقة والاتجاه لـ 5 أيام
    y_dir = full_train_df['Target_Dir_5D'].values
    tscv = TimeSeriesSplit(n_splits=3)
    base_clf = HistGradientBoostingClassifier(max_iter=70, learning_rate=0.06, max_depth=4, random_state=42)
    cal_clf = CalibratedClassifierCV(estimator=base_clf, cv=tscv, method='isotonic')
    cal_clf.fit(X_train_global, y_dir)

    print("\n[4/4] 🔭 اجراء الفحص السريعي الحي والتوقع للأسهم المصرية المستهدفة...")
    
    predictions = []

    for name, ticker in EGX_STOCKS.items():
        try:
            df_stock = processed_dict.get(ticker, None)
            if df_stock is None or df_stock.empty:
                df_stock = build_features_for_stock(ticker)

            if df_stock is None or df_stock.empty or len(df_stock) < 30:
                continue

            df_stock[feature_cols] = df_stock[feature_cols].ffill().bfill()
            
            # عينة آخر جلسة تداول
            live_row = df_stock.iloc[-1]
            live_feat = live_row[feature_cols].values.reshape(1, -1)
            live_scaled = scaler.transform(live_feat)
            
            live_close = float(live_row['Close'])
            live_date = df_stock.index[-1].strftime('%Y-%m-%d')

            # توقع العوائد والأسعار للأيام الـ 5 القادمة
            day_preds = {}
            for h in range(1, 6):
                pred_ret = reg_models[h].predict(live_scaled)[0]
                pred_price = live_close * (1.0 + pred_ret)
                day_preds[f'Day_{h}'] = pred_price

            final_5d_ret = (day_preds['Day_5'] - live_close) / live_close * 100.0
            
            # حساب نسبة الثقة المعايرة
            conf_prob = cal_clf.predict_proba(live_scaled)[0][1] * 100.0

            if conf_prob >= 60.0:
                action = "🟢 شراء قوي جداً (STRONG BUY)"
            elif conf_prob >= 53.0:
                action = "🟢 دخول بحجم خفيف (BUY)"
            else:
                action = "🟡 احتفاظ كاش (CASH / WAIT)"

            predictions.append({
                'الاسم': name,
                'الكود': ticker,
                'تاريخ التداول': live_date,
                'سعر الإغلاق': round(live_close, 2),
                'توقع يوم 1': round(day_preds['Day_1'], 2),
                'توقع يوم 2': round(day_preds['Day_2'], 2),
                'توقع يوم 3': round(day_preds['Day_3'], 2),
                'توقع يوم 4': round(day_preds['Day_4'], 2),
                'توقع يوم 5': round(day_preds['Day_5'], 2),
                'العائد المتوقع %': f"{final_5d_ret:+.2f}%",
                'نسبة الثقة': f"{conf_prob:.1f}%",
                'التوصية': action
            })

        except Exception as e:
            print(f"⚠️ خطأ أثناء التوقع لـ {name} ({ticker}): {e}")

    print("\n" + "="*140)
    print("📈 **جدول التوقعات الحية للأيام الخمسة القادمة للأسهم المصرية (بناءً على الذكاء الاصطناعي العالمي):**")
    print("="*140)

    if not predictions:
        print("تعذر جلب التوقعات.")
        return

    res_df = pd.DataFrame(predictions)
    # ترتيب الجدول حسب نسبة الثقة والعائد
    res_df = res_df.sort_values(by='نسبة الثقة', ascending=False)

    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    print(res_df.to_string(index=False))
    print("="*140)

if __name__ == "__main__":
    main()
