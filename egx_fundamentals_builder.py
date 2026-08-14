import yfinance as yf
import pandas as pd
import numpy as np
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

tickers = ["COMI.CA", "PHDC.CA", "TMGH.CA", "HRHO.CA", "FWRY.CA", "SWDY.CA", "ESRS.CA", "HELI.CA", "AMOC.CA", "ISPH.CA"]
results = []

print("=========================================================")
print("🧠 بناء محرك الأساسيات المؤسسية للبورصة المصرية (Gen-12)")
print("=========================================================")
print("جاري سحب الأرباح الربع سنوية واستنتاج تواريخ الإفصاح لكسر التسريب...")

for symbol in tickers:
    print(f"🔍 تحليل شركة: {symbol}...")
    try:
        stock = yf.Ticker(symbol)
        
        # الاعتماد على القوائم السنوية والربع سنوية
        qf = stock.quarterly_financials
        if qf is None or qf.empty:
            qf = stock.financials 
            
        if qf is None or qf.empty:
            print(f"⚠️ {symbol}: لا توجد قوائم مالية معلنة.")
            continue
            
        dates = qf.columns
        for d in dates:
            # 🛡️ الحماية من التسريب العظمى:
            # اليوم الذي انتهى فيه الربع + 45 يوماً (المهلة القانونية لنشر الميزانية في مصر)
            # حتى لا يقرأ الموديل أرباح شركة يوم 31 مارس وهي لم تُعلن إلا في مايو!
            pub_date = d + pd.Timedelta(days=45)
            
            eps = np.nan
            try:
                eps = float(qf.loc['Basic EPS', d])
            except Exception:
                pass
            
            if pd.isna(eps):
                try:
                    net_in = float(qf.loc['Net Income', d])
                    shares = float(qf.loc['Basic Average Shares', d])
                    if shares > 0:
                        eps = net_in / shares
                except Exception:
                    pass

            rev = np.nan
            try:
                rev = float(qf.loc['Total Revenue', d])
            except Exception:
                pass

            if pd.isna(eps) and pd.isna(rev):
                continue
                
            results.append({
                'Date': pub_date.strftime('%Y-%m-%d'),
                'Ticker': symbol,
                'EPS': eps,
                'Revenue': rev
            })
    except Exception as e:
        print(f"⚠️ خطأ في سحب {symbol}: {e}")

if results:
    df = pd.DataFrame(results)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values(by=['Date', 'Ticker'])
    
    out_path = os.path.join(BASE_DIR, 'egx_fundamentals.csv')
    df.to_csv(out_path, index=False)
    print("\n✅ تم بنجاح بناء محرك الأساسيات المحكم زمنياً (Point-in-Time)!")
    print(f"📂 تم تصدير الملف إلى: {out_path}")
else:
    print("\n❌ فشل استخراج البيانات. قد يكون هناك حظر مؤقت من Yahoo.")
