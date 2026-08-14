import os

app_file = r"c:\Users\Administrator\Desktop\New folder\app.py"

with open(app_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

out_lines = []
in_tab_cal = False
tab_cal_done = False

for line in lines:
    if line.strip() == "with tab_cal:" and not tab_cal_done:
        in_tab_cal = True
        tab_cal_done = True
        out_lines.append(line)
        
        tab_cal_code = """        st.markdown("<div class='section-header'>📊 معايرة الثقة (Calibration) ومراقبة الانحراف (Drift Monitor)</div>", unsafe_allow_html=True)
        st.info("ملحوظة: هذا القسم يستخرج بيانات المعايرة من أداء النموذج على أرض الواقع عبر الـ 30-Day Paper Trading Journal.", icon="ℹ️")
        
        drift_file = os.path.join(BASE_DIR, 'data', 'model_drift_metrics.json')
        if os.path.exists(drift_file):
            try:
                import json
                with open(drift_file, 'r', encoding='utf-8') as f:
                    drift_data = json.load(f)
                    
                r20 = drift_data.get('rolling_20', {})
                r60 = drift_data.get('rolling_60', {})
                
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric("Rolling 20 Win Rate", f"{r20.get('win_rate',0):.1f}%")
                    if r20.get('win_rate',0) < 48.0 and r20.get('win_rate',0) > 0:
                        st.error("⚠️ Model Degradation Alert: Win Rate < 48%")
                with c2:
                    st.metric("Rolling 20 Profit Factor", f"{r20.get('profit_factor',0):.2f}x")
                    if r20.get('profit_factor',0) < 1.10 and r20.get('profit_factor',0) > 0:
                        st.error("⚠️ Model Degradation Alert: Profit Factor < 1.10x")
                with c3:
                    st.metric("Rolling 20 ECE", f"{r20.get('ece',0):.3f}")
                    if r20.get('ece',0) > 0.15:
                        st.error("⚠️ Model Degradation Alert: ECE > 0.15")
                        
                st.markdown("### Reliability & Calibration Bins")
                telemetry_file = os.path.join(BASE_DIR, 'data', 'prediction_actual_telemetry.json')
                if os.path.exists(telemetry_file):
                    with open(telemetry_file, 'r', encoding='utf-8') as f:
                        t_data = json.load(f)
                    st.json(t_data[:5]) # Show sample
            except Exception as e:
                st.warning(f"Error loading telemetry: {e}")
        else:
            st.warning("لم يتم العثور على بيانات Telemetry بعد. يرجى تشغيل daily_paper_trade_logger.py")
"""
        out_lines.append(tab_cal_code)
        continue
        
    if in_tab_cal:
        if line.startswith("    ") or line.strip() == "":
            pass # skip existing tab_cal content
        else:
            in_tab_cal = False
            out_lines.append(line)
    else:
        out_lines.append(line)

with open(app_file, "w", encoding="utf-8") as f:
    f.writelines(out_lines)

print("Patch applied to app.py successfully.")
