import os
import sys
import datetime

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.market_calendar import EGXMarketCalendar

start_date = datetime.date(2026, 8, 31)
end_date = datetime.date(2026, 10, 12)

cur = start_date
total_calendar_days = 0
weekend_days = []
holidays = []
trading_sessions = []

while cur <= end_date:
    total_calendar_days += 1
    ds = cur.strftime("%Y-%m-%d")
    status = EGXMarketCalendar.is_trading_day(ds)
    
    if status.get("is_trading_day"):
        trading_sessions.append((ds, cur.strftime("%A")))
    else:
        reason = status.get("reason", "")
        if "WEEKEND" in reason or cur.weekday() in [4, 5]:
            weekend_days.append((ds, cur.strftime("%A"), reason))
        elif "HOLIDAY" in reason:
            holiday_name = status.get("holiday_name", EGXMarketCalendar.EGX_HOLIDAYS.get(ds, "Market Holiday"))
            holidays.append((ds, cur.strftime("%A"), holiday_name))
        else:
            holidays.append((ds, cur.strftime("%A"), reason))

    cur += datetime.timedelta(days=1)

print(f"=== EGX TRADING CALENDAR AUDIT ({start_date} to {end_date}) ===")
print(f"Total Calendar Days: {total_calendar_days}")
print(f"EGX Weekends (Fri & Sat): {len(weekend_days)}")
print(f"Official Market Holidays: {len(holidays)}")
for h in holidays:
    print(f"  - Holiday: {h[0]} ({h[1]}): {h[2]}")
print(f"Active EGX Trading Sessions: {len(trading_sessions)}")
print("\nSession Details (Chronological):")
for idx, (dt, day_name) in enumerate(trading_sessions, 1):
    print(f"  Session #{idx:02d}: {dt} ({day_name})")
