import os, sys, json
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if '__file__' in globals() else os.getcwd()
sys.path.insert(0, BASE_DIR)

# Read app.py source and extract build_final_decision_objects and export_decision_log
with open(os.path.join(BASE_DIR, "app.py"), "r", encoding="utf-8") as f:
    app_code = f.read()

# Verify key functions exist in app.py
assert "def build_final_decision_objects(" in app_code, "build_final_decision_objects missing!"
assert "def export_decision_log(" in app_code, "export_decision_log missing!"
assert "DATA MODE = DELAYED" in app_code, "Persistent banner text missing!"
assert "SessionManager.get_valid_days()" in app_code, "SessionManager integration missing!"
assert "breadth_adv" in app_code, "Market breadth proxy missing!"

print("--- 1. Testing Decision Logic & Risk Gate Invariants ---")

# Let's run a sandbox execution of build_final_decision_objects
import math

def test_decision_logic():
    # Execute function in isolated namespace
    ns = {'math': math, 'hashlib': __import__('hashlib'), 'DECISION_LOG_CSV': 'gen_decision_log.csv', 'json': json, 'pd': pd, 'os': os}
    
    # Extract build_final_decision_objects code
    start = app_code.find("def build_final_decision_objects(")
    end = app_code.find("def export_decision_log(")
    exec(app_code[start:end], ns)
    
    # Extract export_decision_log code
    exp_start = app_code.find("def export_decision_log(")
    exp_end = app_code.find("def export_daily_ranking(")
    exec(app_code[exp_start:exp_end], ns)
    
    fn = ns['build_final_decision_objects']
    exp_fn = ns['export_decision_log']
    
    sample_preds = [
        {
            'الكود': 'COMI.CA', 'الاسم': 'التجاري الدولي',
            'درجة الترتيب الاستثماري ⭐': 85.0,
            'السعر الحالي (الماركت) 🏷️': 90.0,
            'سعر الدخول المقترح (شراء بدعم) 📥': 87.5,
            'Entry Distance %': '-2.8%',
            'وقف الخسارة 🛑': 84.0, 'أعلى قمة متوقعة 🏔️': 98.0,
            'تخصيص المحفظة %': '15.0%',
            'التوصية الحية': '🟢 اقتناص القمة (STRONG BUY)',
            '_dq_status': 'OK', '_liquidity_flag': 'OK'
        },
        {
            'الكود': 'TMGH.CA', 'الاسم': 'طلعت مصطفى',
            'درجة الترتيب الاستثماري ⭐': 80.0,
            'السعر الحالي (الماركت) 🏷️': 60.0,
            'سعر الدخول المقترح (شراء بدعم) 📥': 60.0, # Invalid pullback: entry >= current
            'Entry Distance %': '0.0%',
            'وقف الخسارة 🛑': 56.0, 'أعلى قمة متوقعة 🏔️': 68.0,
            'تخصيص المحفظة %': '15.0%',
            'التوصية الحية': '🟢 دخول خفيف (BUY)',
            '_dq_status': 'OK', '_liquidity_flag': 'OK'
        }
    ]
    
    sample_holdings = [{'stock': 'التجاري الدولي', 'ticker': 'COMI.CA', 'qty': 100, 'avg_price': 85.0}]
    sample_cash = 50000.0
    sample_exec_status = {'orders': {}}
    sample_exit_signals = [{'الكود': 'COMI.CA', 'action_on_existing_position': 'HOLD 🟢', 'reason': 'السهم في النطاق الآمن'}]
    sample_ts = "2026-08-18 10:00:00"
    
    d_objs = fn(sample_preds, sample_holdings, sample_cash, sample_exec_status, sample_exit_signals, sample_ts)
    
    assert len(d_objs) == 2
    assert d_objs[0]['signal']['action'] == 'HOLD'
    assert d_objs[1]['signal']['action'] == 'NO_TRADE'
    assert "INVALID_PULLBACK_ENTRY" in d_objs[1]['signal']['reason']
    
    # Test export
    exp_fn(d_objs, sample_ts)
    df = pd.read_csv("gen_decision_log.csv")
    assert len(df) == 2
    print("Exported decision log rows:", len(df))
    print("Columns:", list(df.columns))

test_decision_logic()
print("✅ ISOLATED REGRESSION & INVARIANT TESTS PASSED 100%.")
