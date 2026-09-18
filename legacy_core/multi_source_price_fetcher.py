import sys, json, time, os
from datetime import datetime

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

print("=" * 70)
print("🔍 GEN-26 — سحب بيانات من 4 مصادر مستقلة")
print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

# الأسهم اللي هنختبر عليها
TICKERS = {
    "COMI": "Commercial International Bank",
    "SWDY": "Elsewedy Electric",
    "TMGH": "Talaat Mostafa",
    "ADIB": "Abu Dhabi Islamic Bank Egypt",
    "AMOC": "Alexandria Mineral Oils",
    "HRHO": "EFG Hermes",
    "ORAS": "Orascom Construction",
    "ETEL": "Telecom Egypt",
    "ABUK": "Abu Qir Fertilizers",
    "FWRY": "Fawry",
}

all_results = {}

# ============================================================
# المصدر 1: yfinance (الحالي)
# ============================================================
print("\n📡 [1/3] yfinance...")
import yfinance as yf

yf_prices = {}
for sym in TICKERS:
    try:
        t = yf.Ticker(f"{sym}.CA")
        info = t.fast_info
        p = getattr(info, 'previous_close', None) or \
            getattr(info, 'regular_market_previous_close', None) or \
            getattr(info, 'last_price', None)
        
        if not p or p <= 0:
            hist = t.history(period="5d")
            if not hist.empty and 'Close' in hist.columns:
                p = float(hist['Close'].dropna().iloc[-1])
                
        if p and p > 0:
            yf_prices[sym] = round(float(p), 2)
            print(f"  ✅ {sym}: {float(p):.2f}")
        else:
            print(f"  ❓ {sym}: N/A")
        time.sleep(0.3)
    except Exception as e:
        print(f"  ❌ {sym}: {e}")
        
all_results['yfinance'] = yf_prices

# ============================================================
# المصدر 2: investpy (Investing.com)
# ============================================================
print("\n📡 [2/3] investpy (Investing.com)...")
try:
    import investpy
    
    investpy_prices = {}
    EGX_NAMES = {
        "COMI": "commercial-international-bank",
        "SWDY": "elsewedy-electric",
        "TMGH": "talaat-moustafa-group",
        "ADIB": "abu-dhabi-islamic-bank-egypt",
        "AMOC": "alexandria-mineral-oils",
        "HRHO": "efg-hermes",
        "ETEL": "telecom-egypt",
        "ABUK": "abu-qir-fertilizers",
        "FWRY": "fawry-for-banking",
    }
    
    for sym, inv_name in EGX_NAMES.items():
        try:
            data = investpy.get_stock_recent_data(
                stock=inv_name,
                country='egypt'
            )
            if not data.empty and 'Close' in data.columns:
                price = data['Close'].iloc[-1]
                investpy_prices[sym] = round(float(price), 2)
                print(f"  ✅ {sym}: {price:.2f}")
            else:
                print(f"  ❓ {sym}: فارغ")
            time.sleep(0.5)
        except Exception as e:
            err_msg = str(e)
            print(f"  ❌ {sym}: {err_msg[:60]}")
            
    all_results['investpy'] = investpy_prices
    
except ImportError:
    print("  ⚠️ investpy مش مثبت — بيتثبت دلوقتي...")
    import subprocess
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'investpy', '-q'])
    print("  تم التثبيت — أعد تشغيل السكريبت")
    all_results['investpy'] = {}

# ============================================================
# المصدر 3: Selenium لـ EGX.com.eg
# ============================================================
print("\n📡 [3/3] Selenium → egx.com.eg...")
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        srv = Service(ChromeDriverManager().install())
    except Exception:
        srv = None
    
    opts = Options()
    opts.add_argument('--headless=new')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-dev-shm-usage')
    opts.add_argument('--disable-gpu')
    opts.add_argument('--disable-blink-features=AutomationControlled')
    opts.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    if srv:
        driver = webdriver.Chrome(service=srv, options=opts)
    else:
        driver = webdriver.Chrome(options=opts)
        
    egx_prices = {}
    
    try:
        driver.set_page_load_timeout(30)
        driver.get("https://www.egx.com.eg/en/equities.aspx")
        time.sleep(5)
        
        print(f"  EGX Page Status: {driver.title or 'Loaded'}")
        
        # محاولة إيجاد الجدول
        rows = driver.find_elements(By.CSS_SELECTOR, "table tr, .stock-row, .equity-row")
        print(f"  Rows found: {len(rows)}")
        
        for row in rows[:80]:
            try:
                cols = row.find_elements(By.TAG_NAME, "td")
                if len(cols) >= 4:
                    ticker_text = cols[0].text.strip()
                    price_text = cols[3].text.strip().replace(',', '')
                    for sym in TICKERS:
                        if sym in ticker_text:
                            try:
                                price = float(price_text)
                                egx_prices[sym] = round(price, 2)
                                print(f"  ✅ {sym}: {price:.2f}")
                            except Exception:
                                pass
            except Exception:
                pass
                
        # لو مش لاقي بيانات — جرب فحص مصادر بديلة في البورصة
        if not egx_prices:
            print("  ⚠️ لم يتم استخراج أسعار من جدول equities.aspx (حماية Cloudflare/JS)")
            
    finally:
        try:
            driver.quit()
        except Exception:
            pass
        
    all_results['egx_selenium'] = egx_prices
    
except Exception as e:
    print(f"  ❌ Selenium Error: {e}")
    all_results['egx_selenium'] = {}

# ============================================================
# مقارنة النتائج مع النظام الحالي
# ============================================================
print("\n" + "=" * 70)
print("📊 مقارنة الأسعار:")
print(f"{'Ticker':<8} {'System':>10} {'yfinance':>10} {'investpy':>10} {'EGX':>10}")
print("-" * 55)

canonical = {}
if os.path.exists('data/canonical_prices_live.json'):
    with open('data/canonical_prices_live.json', 'r', encoding='utf-8') as f:
        canonical = json.load(f)

comparison = []
for sym in TICKERS:
    ca = f"{sym}.CA"
    sys_p = canonical.get(ca, {}).get('price')
    yf_p = all_results.get('yfinance', {}).get(sym)
    inv_p = all_results.get('investpy', {}).get(sym)
    egx_p = all_results.get('egx_selenium', {}).get(sym)
    
    # حساب الفروق
    prices = [p for p in [sys_p, yf_p, inv_p, egx_p] if p is not None]
    max_diff = 0
    if len(prices) >= 2:
        max_diff = (max(prices) - min(prices)) / min(prices) * 100
    
    status = "✅" if max_diff <= 5 else ("⚠️" if max_diff <= 15 else "🔴")
    
    s = f"{sys_p:.2f}" if sys_p is not None else "N/A"
    y = f"{yf_p:.2f}" if yf_p is not None else "N/A"
    i = f"{inv_p:.2f}" if inv_p is not None else "N/A"
    e = f"{egx_p:.2f}" if egx_p is not None else "N/A"
    
    print(f"{sym:<8} {s:>10} {y:>10} {i:>10} {e:>10}  {status}")
    comparison.append({"ticker": ca, "system": sys_p, "yfinance": yf_p,
                       "investpy": inv_p, "egx": egx_p, "max_diff_pct": round(max_diff, 1)})

# حفظ التقرير
os.makedirs('data', exist_ok=True)
with open('data/multi_source_verification.json', 'w', encoding='utf-8') as f:
    json.dump({"timestamp": datetime.now().isoformat(),
               "comparison": comparison}, f, ensure_ascii=False, indent=2)

print("\n💾 محفوظ في: data/multi_source_verification.json")
