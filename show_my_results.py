import sys
sys.stdout.reconfigure(encoding='utf-8')
import datetime
import os
import json
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
JOURNAL_FILE = os.path.join(BASE_DIR, "paper_trading_journal.json")
REPORT_FILE = os.path.join(BASE_DIR, "dashboard_report.txt")
WEEKLY_SUMMARY_FILE = os.path.join(BASE_DIR, "weekly_summary.txt")

def load_journal():
    if os.path.exists(JOURNAL_FILE):
        try:
            with open(JOURNAL_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def calculate_streaks(eval_records):
    max_win_streak = 0
    max_loss_streak = 0
    curr_win_streak = 0
    curr_loss_streak = 0
    
    for r in eval_records:
        is_win = r.get("net_pnl_pct", 0.0) > 0
        if is_win:
            curr_win_streak += 1
            curr_loss_streak = 0
            if curr_win_streak > max_win_streak:
                max_win_streak = curr_win_streak
        else:
            curr_loss_streak += 1
            curr_win_streak = 0
            if curr_loss_streak > max_loss_streak:
                max_loss_streak = curr_loss_streak
                
    return max_win_streak, max_loss_streak

def update_weekly_summary(eval_records):
    if not eval_records:
        return
    
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tot_eval = len(eval_records)
    wins = sum(1 for r in eval_records if r.get("net_pnl_pct", 0.0) > 0)
    acc = (wins / tot_eval * 100.0) if tot_eval > 0 else 0.0
    avg_pnl = sum(r.get("net_pnl_pct", 0.0) for r in eval_records) / tot_eval if tot_eval > 0 else 0.0
    
    summary_line = f"[{now_str}] Evaluated Trades: {tot_eval} | Wins: {wins} | Accuracy: {acc:.1f}% | Avg PnL: {avg_pnl:+.2f}%\n"
    
    with open(WEEKLY_SUMMARY_FILE, "a", encoding="utf-8") as f:
        f.write(summary_line)

def run_dashboard():
    journal = load_journal()
    report_lines = []
    
    def rprint(text=""):
        print(text)
        report_lines.append(str(text))
        
    rprint("==================================================================")
    rprint("📊 DAILY PAPER TRADING ACCURACY & PERFORMANCE DASHBOARD")
    rprint(f"Report Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    rprint("==================================================================")
    
    pending_records = [r for r in journal if r.get("status") == "PENDING"]
    evaluated_records = [r for r in journal if r.get("status") == "COMPLETED"]
    
    today_dt = datetime.datetime.now().date()
    
    # 1. PENDING SECTION
    rprint("\n⏳ [SECTION 1] PENDING RECOMMENDATIONS (تحت التقييم)")
    rprint("-" * 90)
    if pending_records:
        rprint(f"{'Ticker':<10} | {'Name':<22} | {'Entry Date':<10} | {'Price (EGP)':<11} | {'Prob %':<7} | {'Eval Date':<10} | {'Days Left':<9}")
        rprint("-" * 90)
        for r in pending_records:
            t = r.get("ticker", "")
            name = r.get("name", "")[:20]
            edate = r.get("entry_date", "")
            eprice = r.get("entry_price", 0.0)
            prob = r.get("confidence_prob", 0.0) * 100.0
            evdate = r.get("eval_date", "")
            
            try:
                ev_dt = datetime.datetime.strptime(evdate, "%Y-%m-%d").date()
                days_left = max(0, (ev_dt - today_dt).days)
            except Exception:
                days_left = "?"
                
            rprint(f"{t:<10} | {name:<22} | {edate:<10} | ${eprice:<10.2f} | {prob:<6.1f}% | {evdate:<10} | {days_left:<9}")
    else:
        rprint("لا توجد توصيات قيد الانتظار حالياً.")
        
    # 2. EVALUATED SECTION
    rprint("\n✅ [SECTION 2] EVALUATED RECOMMENDATIONS (تم تقييمها بالفعل)")
    rprint("-" * 90)
    if evaluated_records:
        rprint(f"{'Ticker':<10} | {'Entry Date':<10} | {'Entry Price':<11} | {'Exit Price':<11} | {'Net PnL %':<10} | {'Result':<8}")
        rprint("-" * 90)
        for r in evaluated_records:
            t = r.get("ticker", "")
            edate = r.get("entry_date", "")
            eprice = r.get("entry_price", 0.0)
            exprice = r.get("exit_price", 0.0)
            pnl = r.get("net_pnl_pct", 0.0)
            icon = "✅ WIN" if pnl > 0 else "❌ LOSS"
            rprint(f"{t:<10} | {edate:<10} | ${eprice:<10.2f} | ${exprice:<10.2f} | {pnl:<+9.2f}% | {icon:<8}")
    else:
        rprint("لم تكتمل أي توصية حتى الآن (تحتاج 5 أيام تداول من تاريخ الدخول).")
        
    # 3. OVERALL METRICS
    rprint("\n==================================================================")
    rprint("📈 OVERALL PERFORMANCE SUMMARY (إحصائيات الأداء الكلية)")
    rprint("==================================================================")
    
    tot_eval = len(evaluated_records)
    wins = sum(1 for r in evaluated_records if r.get("net_pnl_pct", 0.0) > 0)
    losses = tot_eval - wins
    acc = (wins / tot_eval * 100.0) if tot_eval > 0 else 0.0
    avg_pnl = sum(r.get("net_pnl_pct", 0.0) for r in evaluated_records) / tot_eval if tot_eval > 0 else 0.0
    max_win_s, max_loss_s = calculate_streaks(evaluated_records)
    
    rprint(f"  • Total Evaluated Trades (إجمالي الصفقات المقيّمة): {tot_eval}")
    rprint(f"  • Successful Trades (الصفقات الناجحة ✅): {wins}")
    rprint(f"  • Failed Trades (الصفقات الخاسرة ❌): {losses}")
    rprint(f"  • Actual Realized Accuracy (نسبة الدقة الفعلية): {acc:.2f}%")
    rprint(f"  • Average Net PnL / Trade (متوسط الربح/الخسارة الصافي لكل صفقة): {avg_pnl:+.2f}%")
    rprint(f"  • Longest Win Streak (أطول تتابع أرباح متتالي): {max_win_s} صفقات")
    rprint(f"  • Longest Loss Streak (أطول تتابع خسائر متتالي): {max_loss_s} صفقات")
    rprint("==================================================================")
    
    # Save full report read-only output to disk
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines) + "\n")
        
    update_weekly_summary(evaluated_records)
    
    # Print Quick Top 3 / Bottom 3 summary to terminal
    print(f"\n📄 Full Report saved to: {REPORT_FILE}")
    print(f"📝 Weekly Summary log appended to: {WEEKLY_SUMMARY_FILE}")

if __name__ == "__main__":
    run_dashboard()
