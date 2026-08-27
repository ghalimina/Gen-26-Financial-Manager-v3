import json, time, sys
import yfinance as yf
import pandas as pd
from datetime import datetime

try:
    from data.universe_manager import THNDR_TO_YFINANCE_MAP
except ImportError:
    THNDR_TO_YFINANCE_MAP = {}

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

print("=" * 80)
print("🔍 GEN-26 — أداة التحقق من صحة البيانات")
print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

# 1. جلب الأسعار من النظام (SSOT)
with open('data/canonical_prices_live.json', 'r', encoding='utf-8') as f:
    canonical = json.load(f)

# 2. الأسهم النشطة فقط (CROSS_VERIFIED + SINGLE_SOURCE)
active = {
    ticker: data for ticker, data in canonical.items()
    if data.get('classification') in ['CROSS_VERIFIED_REAL_DATA', 'SINGLE_SOURCE_ONLY']
}
print(f"\n📊 أسهم نشطة في النظام: {len(active)}")

# 3. جلب أسعار yfinance للمقارنة
print("\n📡 جلب أسعار yfinance للمقارنة...")
results = []

for ticker, system_data in active.items():
    system_price = system_data.get('price', 0)
    system_source = system_data.get('source', 'N/A')
    
    try:
        time.sleep(0.2)  # تجنب Rate Limit
        target_sym = THNDR_TO_YFINANCE_MAP.get(ticker, ticker)
        stock = yf.Ticker(target_sym)
        
        yf_price = None
        # استخراج سعر الإغلاق الفعلي من yfinance
        try:
            info = stock.fast_info
            yf_price = getattr(info, 'previous_close', None) or \
                       getattr(info, 'regular_market_previous_close', None) or \
                       getattr(info, 'last_price', None)
        except Exception:
            pass
            
        if not yf_price or yf_price <= 0:
            try:
                hist = stock.history(period="5d")
                if not hist.empty and 'Close' in hist.columns:
                    yf_price = float(hist['Close'].dropna().iloc[-1])
            except Exception:
                pass
                
        # محاولة أخيرة بالرمز الأصلي لو كان هناك تحويل
        if (not yf_price or yf_price <= 0) and target_sym != ticker:
            try:
                stk_fb = yf.Ticker(ticker)
                hist_fb = stk_fb.history(period="5d")
                if not hist_fb.empty and 'Close' in hist_fb.columns:
                    yf_price = float(hist_fb['Close'].dropna().iloc[-1])
            except Exception:
                pass
        
        if yf_price and yf_price > 0 and system_price > 0:
            diff_pct = abs(yf_price - system_price) / system_price * 100
            status = "✅ متطابق" if diff_pct <= 5 else \
                     "⚠️ فرق متوسط" if diff_pct <= 15 else \
                     "🔴 فرق كبير"
            results.append({
                'ticker': ticker,
                'system_price': round(system_price, 2),
                'yfinance_price': round(yf_price, 2),
                'diff_pct': round(diff_pct, 2),
                'status': status,
                'source': system_source
            })
        else:
            results.append({
                'ticker': ticker,
                'system_price': round(system_price, 2),
                'yfinance_price': None,
                'diff_pct': None,
                'status': '❓ yfinance لا يجيب',
                'source': system_source
            })
    except Exception as e:
        results.append({
            'ticker': ticker,
            'system_price': round(system_price, 2),
            'yfinance_price': None,
            'diff_pct': None,
            'status': f'❌ خطأ: {str(e)[:30]}',
            'source': system_source
        })

# 4. تصنيف النتائج
df = pd.DataFrame(results)

if not df.empty and 'status' in df.columns:
    matched = df[df['status'] == '✅ متطابق']
    warning = df[df['status'] == '⚠️ فرق متوسط']
    critical = df[df['status'] == '🔴 فرق كبير']
    no_data = df[df['yfinance_price'].isna()]
else:
    matched = pd.DataFrame()
    warning = pd.DataFrame()
    critical = pd.DataFrame()
    no_data = pd.DataFrame()

print(f"\n{'='*80}")
print(f"📊 ملخص التحقق:")
print(f"  ✅ متطابق (فرق < 5%):      {len(matched)} سهم")
print(f"  ⚠️ فرق متوسط (5-15%):     {len(warning)} سهم")
print(f"  🔴 فرق كبير (> 15%):       {len(critical)} سهم")
print(f"  ❓ yfinance مش بيجيب:      {len(no_data)} سهم")
print(f"{'='*80}")

# 5. عرض المشاكل الكبيرة
if len(critical) > 0:
    print("\n🔴 أسهم بها فرق كبير — تحتاج مراجعة عاجلة:")
    print(f"{'Ticker':<12} {'System':>10} {'yfinance':>10} {'Diff%':>8}")
    print("-" * 45)
    for _, row in critical.iterrows():
        print(f"{row['ticker']:<12} {row['system_price']:>10.2f} {row['yfinance_price']:>10.2f} {row['diff_pct']:>7.1f}%")

# 6. عرض الأسهم اللي مش بتجيب بيانات
if len(no_data) > 0:
    print(f"\n❓ أسهم مش بتجيب بيانات من yfinance ({len(no_data)} سهم):")
    for _, row in no_data.iterrows():
        print(f"  - {row['ticker']}: {row['status']}")

# 7. حفظ التقرير
valid_count = max(len(df) - len(no_data), 1)
report = {
    'timestamp': datetime.now().isoformat(),
    'total_active': len(active),
    'matched_count': len(matched),
    'warning_count': len(warning),
    'critical_count': len(critical),
    'no_data_count': len(no_data),
    'accuracy_pct': round(len(matched) / valid_count * 100, 1),
    'critical_tickers': critical['ticker'].tolist() if len(critical) > 0 else [],
    'warning_tickers': warning['ticker'].tolist() if len(warning) > 0 else [],
    'all_results': results
}

with open('data/data_verification_report.json', 'w', encoding='utf-8') as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

print(f"\n✅ دقة البيانات الإجمالية: {report['accuracy_pct']}%")
print(f"💾 التقرير محفوظ في: data/data_verification_report.json")
