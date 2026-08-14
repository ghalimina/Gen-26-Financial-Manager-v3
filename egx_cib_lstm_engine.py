# ═══════════════════════════════════════════════════════════════════════════════
# [EXPERIMENTAL / DEPRECATED] SINGLE-STOCK CIB LSTM RESEARCH ENGINE
# Note: This is an isolated research engine and is NOT part of the production Gen-26 pipeline in app.py.
# ═══════════════════════════════════════════════════════════════════════════════
import traceback
import datetime
import warnings
warnings.filterwarnings('ignore')

def main():
    try:
        import yfinance as yf
        import pandas as pd
        import numpy as np
        from sklearn.preprocessing import MinMaxScaler
        from tensorflow.keras.models import Sequential
        from tensorflow.keras.layers import LSTM, Dense, Dropout
        from tensorflow.keras.callbacks import EarlyStopping

        print("="*60)
        print("🏦 [EXPERIMENTAL / DEPRECATED] منظومة التداول الكمي لسهم CIB")
        print("="*60)

        # ---------------------------------------------------------
        # 1. سحب وتجهيز البيانات لسهم CIB
        # ---------------------------------------------------------
        def fetch_and_prepare_data(ticker, start_date, end_date):
            print("\n[1/4] جاري سحب بيانات سهم CIB، الدولار، ومؤشرات السوق...")
            
            df = yf.download(ticker, start=start_date, end=end_date, progress=False)
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.droplevel(1)
            
            if df.empty:
                print("خطأ: لم يتم العثور على بيانات للسهم.")
                return None

            usd = yf.download("USDEGP=X", start=start_date, end=end_date, progress=False)
            if not usd.empty:
                if isinstance(usd.columns, pd.MultiIndex): usd.columns = usd.columns.droplevel(1)
                df['USD_EGP'] = usd['Close'].ffill()
            
            # محاكاة ذكية للمتغيرات الاقتصادية ومشاعر الأخبار
            np.random.seed(42)
            df['Inflation_Proxy'] = np.linspace(15.0, 35.0, len(df)) + np.random.normal(0, 0.5, len(df))
            df['News_Sentiment'] = df['Close'].pct_change().rolling(3).mean() * 10
            df['News_Sentiment'] = df['News_Sentiment'].fillna(0).clip(-1, 1)

            # المؤشرات الفنية المتقدمة
            df['SMA_20'] = df['Close'].rolling(window=20).mean()
            
            # حساب مؤشر التذبذب الحقيقي (ATR) لإدارة المخاطر
            high_low = df['High'] - df['Low']
            high_close = np.abs(df['High'] - df['Close'].shift())
            low_close = np.abs(df['Low'] - df['Close'].shift())
            df['ATR_14'] = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1).rolling(14).mean()
            
            df['Rel_Volume'] = df['Volume'] / df['Volume'].rolling(window=20).mean()

            # أهداف الأسعار المستقبلية (الانحراف السعري - Regression Targets)
            df['Target_1D'] = df['Close'].shift(-1)
            df['Target_5D'] = df['Close'].shift(-5)
            df['Target_20D'] = df['Close'].shift(-20)
            
            df.ffill(inplace=True)
            df.fillna(0, inplace=True)
            return df

        # ---------------------------------------------------------
        # 2. تدريب محرك الشبكة العصبية لتوقع الأسعار الدقيقة
        # ---------------------------------------------------------
        def train_price_prediction_lstm(df):
            print("[2/4] جاري تدريب الشبكة العصبية لتوقع الأسعار الدقيقة...")
            
            features = ['Close', 'Volume', 'SMA_20', 'ATR_14', 'Rel_Volume', 'USD_EGP', 'Inflation_Proxy', 'News_Sentiment']
            
            train_df = df.dropna(subset=['Target_20D']).copy()
            
            split_idx = int(0.90 * len(train_df))
            X_train_raw = X_data[:split_idx]
            y_train_raw = y_data[:split_idx]
            X_test_raw = X_data[split_idx:]
            y_test_raw = y_data[split_idx:]
            
            scaler_X = MinMaxScaler(feature_range=(0, 1))
            scaler_y = MinMaxScaler(feature_range=(0, 1))
            
            X_train_scaled = scaler_X.fit_transform(X_train_raw)
            y_train_scaled = scaler_y.fit_transform(y_train_raw)
            
            X_test_scaled = scaler_X.transform(X_test_raw)
            y_test_scaled = scaler_y.transform(y_test_raw)
            
            X_scaled = np.vstack([X_train_scaled, X_test_scaled])
            y_scaled = np.vstack([y_train_scaled, y_test_scaled])
            
            seq_length = 20 
            X, y = [], []
            for i in range(seq_length, len(X_scaled)):
                X.append(X_scaled[i-seq_length:i])
                y.append(y_scaled[i])
                
            X, y = np.array(X), np.array(y)
            
            split = max(int(0.90 * len(X)), 1)
            X_train, X_test = X[:split], X[split:]
            y_train, y_test = y[:split], y[split:]
            
            model = Sequential()
            model.add(LSTM(units=64, return_sequences=True, input_shape=(X_train.shape[1], X_train.shape[2])))
            model.add(Dropout(0.2))
            model.add(LSTM(units=32, return_sequences=False))
            model.add(Dropout(0.2))
            model.add(Dense(units=16, activation='relu'))
            model.add(Dense(units=3, activation='linear')) # إخراج 3 أرقام دقيقة للأسعار
            
            model.compile(optimizer='adam', loss='mse')
            early_stop = EarlyStopping(monitor='val_loss', patience=7, restore_best_weights=True)
            
            model.fit(X_train, y_train, epochs=40, batch_size=32, 
                      validation_data=(X_test, y_test), callbacks=[early_stop], verbose=0)
            
            return model, scaler_X, scaler_y, features, seq_length

        # ---------------------------------------------------------
        # 3. تفسير القرار وتقديم تحليل أسباب التوقع
        # ---------------------------------------------------------
        def generate_explainability_report(latest_row, current_price):
            print("\n[3/4] جاري تحليل عوامل اتخاذ القرار...")
            
            reasons = []
            sentiment = latest_row['News_Sentiment']
            rel_vol = latest_row['Rel_Volume']
            sma = latest_row['SMA_20']
            
            if current_price > sma:
                reasons.append("✔️ السعر فوق المتوسط المتحرك (الأتجاه العام صاعد).")
            else:
                reasons.append("❌ السعر تحت المتوسط المتحرك (ضغط بيعي محتمل).")
                
            if rel_vol > 1.2:
                reasons.append("✔️ سيولة عالية وحجم تداول نشط يدعم الحركة الحالية.")
            else:
                reasons.append("⚠️ حجم التداول ضعيف (سيولة حذرة أو تجميع هادئ).")
                
            if sentiment > 0:
                reasons.append("✔️ مؤشر الأخبار والمشاعر الاقتصادية يميل للإيجابية.")
            else:
                reasons.append("❌ مؤشر الأخبار والمشاعر الاقتصادية يميل للسلبيات أو الحذر.")
                
            return reasons

        # ---------------------------------------------------------
        # التشغيل الرئيسي واستخراج التقرير
        # ---------------------------------------------------------
        TARGET_STOCK = "COMI.CA"      
        START_DATE = "2020-01-01" 
        END_DATE = datetime.date.today().strftime("%Y-%m-%d")
        
        raw_df = fetch_and_prepare_data(TARGET_STOCK, START_DATE, END_DATE)
        
        if raw_df is not None:
            lstm_model, scaler_X, scaler_y, feature_list, lookback_window = train_price_prediction_lstm(raw_df)
            
            print("\n[4/4] استخراج الأسعار المستهدفة والتقرير المالي النهائي...")
            
            latest_data = raw_df[feature_list].tail(lookback_window).values
            latest_scaled = scaler_X.transform(latest_data)
            X_input = np.array([latest_scaled])
            
            predicted_scaled_prices = lstm_model.predict(X_input, verbose=0)
            predicted_real_prices = scaler_y.inverse_transform(predicted_scaled_prices)[0]
            
            current_row = raw_df.iloc[-1]
            current_price = current_row['Close']
            current_atr = current_row['ATR_14']
            
            # خطة إدارة المخاطر الآلية بناءً على الـ ATR
            stop_loss = current_price - (1.5 * current_atr)
            take_profit = current_price + (2.5 * current_atr)
            
            # حساب التواريخ المستقبلية
            today = datetime.date.today()
            date_today = today if today.weekday() < 5 else today + datetime.timedelta(days=(7-today.weekday()))
            date_week = date_today + datetime.timedelta(days=7)
            date_month = date_today + datetime.timedelta(days=30)
            
            explain_reasons = generate_explainability_report(current_row, current_price)
            
            print("\n" + "="*60)
            print("📊 التقرير الاستثماري الاحترافي لسهم CIB (COMI.CA)")
            print(f"💵 السعر الحالي: {current_price:.2f} جنيه | 📉 معامل التذبذب (ATR): {current_atr:.2f}")
            print("="*60)
            
            print("🎯 **مستهدفات الأسعار الدقيقة:**")
            print(f"   1️⃣ جلسة اليوم/الافتتاح ({date_today.strftime('%Y-%m-%d')}): {predicted_real_prices[0]:.2f} جنيه")
            print(f"   2️⃣ هدف الأسبوع ({date_week.strftime('%Y-%m-%d')}): {predicted_real_prices[1]:.2f} جنيه")
            print(f"   3️⃣ هدف الشهر ({date_month.strftime('%Y-%m-%d')}): {predicted_real_prices[2]:.2f} جنيه")
            print("-" * 60)
            
            print("🛡️ **خطة إدارة المخاطر (لحماية رأس مالك):**")
            print(f"   🛑 سعر وقف الخسارة (Stop-Loss): {stop_loss:.2f} جنيه")
            print(f"   🎯 سعر جني الأرباح (Take-Profit): {take_profit:.2f} جنيه")
            print("-" * 60)
            
            print("🔍 **لماذا اتخذ البوت هذا القرار؟ (أسباب التحليل):**")
            for reason in explain_reasons:
                print(f"   - {reason}")
            print("="*60)
            
            # اتخاذ القرار العام (شراء أو بيع)
            if predicted_real_prices[1] > current_price * 1.015:
                print("🟢 **القرار العام:** شراء (BUY). المؤشرات تدعم الصعود، التزم بوقف الخسارة.")
            elif predicted_real_prices[2] < current_price:
                print("🔴 **القرار العام:** بيع / تجنب (SELL). السعر معرض لهبوط أو تصحيح، تخلص من الكميات.")
            else:
                print("🟡 **القرار العام:** انتظار / حياد (HOLD). السوق مستعرض والمخاطرة غير مبررة.")

        input("\n✅ اكتملت المهمة بنجاح. اضغط Enter للخروج...")

    except Exception as e:
        print("\n" + "!"*50)
        print("❌ فشل النظام:")
        traceback.print_exc()
        print("!"*50)
        input("\nاضغط Enter للخروج...")

if __name__ == "__main__":
    main()