import json, time, sys
import yfinance as yf
from datetime import datetime, timezone

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

with open('data/canonical_prices_live.json', 'r', encoding='utf-8') as f:
    canonical = json.load(f)

with open('data/data_verification_report.json', 'r', encoding='utf-8') as f:
    report = json.load(f)

print('='*65)
print('1. الأسهم بفرق كبير (> 15%) — يحتاج إصلاح عاجل')
print('='*65)
for r in report.get('all_results', []):
    if r.get('diff_pct') and r['diff_pct'] > 15:
        t = r['ticker']
        sys_p = r['system_price']
        yf_p = r['yfinance_price']
        
        # فحص العملة والتفاصيل
        try:
            s = yf.Ticker(t)
            fi = s.fast_info
            currency = getattr(fi, 'currency', 'N/A')
            exchange = getattr(fi, 'exchange', 'N/A')
            h = s.history(period='5d')
            closes = list(h['Close'].round(2)) if not h.empty else []
        except Exception:
            currency, exchange, closes = 'Error', 'Error', []
            
        print(f"{t}: sys={sys_p} | yf={yf_p} | diff={r['diff_pct']}%")
        print(f"  currency={currency} | exchange={exchange}")
        print(f"  Last 5 closes: {closes}")
        print()

print('='*65)
print('2. الأسهم بفرق متوسط (5-15%) — فحص')
print('='*65)
for r in report.get('all_results', []):
    if r.get('diff_pct') and 5 < r['diff_pct'] <= 15:
        print(f"{r['ticker']:10} | sys={r['system_price']:7.2f} | yf={r['yfinance_price']:7.2f} | diff={r['diff_pct']:.1f}%")

print()
print('='*65)
print('3. الأسهم مش في yfinance — فحص TradingView source')
print('='*65)
for r in report.get('all_results', []):
    if r.get('yfinance_price') is None:
        t = r['ticker']
        sys_data = canonical.get(t, {})
        upd = sys_data.get('updated_at', '')
        upd_str = upd[:10] if upd else 'N/A'
        print(f"{t:10} | sys_price={sys_data.get('price')} | source={sys_data.get('source')} | updated={upd_str}")

print()
print('='*65)
print('4. ملخص الأسعار القديمة (آخر تحديث قديم)')
print('='*65)
now = datetime.now(timezone.utc)
for ticker, data in canonical.items():
    updated = data.get('updated_at') or data.get('timestamp') or data.get('last_updated')
    if updated and data.get('classification') != 'DATA_UNAVAILABLE':
        try:
            upd_dt = datetime.fromisoformat(updated.replace('Z', '+00:00'))
            if upd_dt.tzinfo is None:
                upd_dt = upd_dt.replace(tzinfo=timezone.utc)
            days_old = (now - upd_dt).days
            if days_old > 3:
                print(f"{ticker:10} | price={data.get('price')} | آخر تحديث: {days_old} يوم")
        except Exception:
            pass
