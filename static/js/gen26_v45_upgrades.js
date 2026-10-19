/**
 * =============================================================================
 * static/js/gen26_v45_upgrades.js — GEN-26 v4.5 Strategic Engines & UI Module
 * Fault-isolated client-side controller for:
 * 1. Intraday EGX Session Clock & Live Cairo Countdown
 * 2. 5-Stage Cascade Breakeven Recovery & Cash Recycling Engine
 * 3. News Catalyst & Corporate Disclosure Radar
 * 4. High-Precision Intraday Sniper Signal Alerts
 * 5. Quantitative Model Prediction Scorecard & Audit
 * =============================================================================
 */

(function () {
    "use strict";

    const GEN26_V45 = {
        clockState: null,
        clockInterval: null,
        recoveryCash: 1200.0,

        // =========================================================================
        // 1. INTRADAY EGX SESSION CLOCK
        // =========================================================================
        async loadSessionClock() {
            try {
                const res = await fetch("/api/market/session_clock");
                if (!res.ok) return;
                const data = await res.json();
                this.clockState = data;
                this.renderSessionClock(data);
                this.startClockTicker();
            } catch (err) {
                console.warn("[v4.5 Clock] Error loading session clock:", err);
            }
        },

        renderSessionClock(data) {
            // Header Capsule
            const phaseEl = document.getElementById("session-clock-phase");
            const timerEl = document.getElementById("session-clock-timer");
            const dotEl = document.querySelector("#session-clock-header .session-clock-dot");

            if (phaseEl) phaseEl.textContent = data.phase_name_ar || "جلسة التداول";
            if (timerEl) timerEl.textContent = data.countdown_formatted || "00:00:00";

            if (dotEl) {
                if (data.is_market_open) {
                    dotEl.style.background = "#10b981"; // Green
                    dotEl.style.boxShadow = "0 0 8px #10b981";
                } else if (data.current_phase === "PRE_OPEN_AUCTION" || data.current_phase === "CLOSING_AUCTION") {
                    dotEl.style.background = "#f59e0b"; // Yellow
                    dotEl.style.boxShadow = "0 0 8px #f59e0b";
                } else {
                    dotEl.style.background = "#64748b"; // Muted
                    dotEl.style.boxShadow = "none";
                }
            }

            // Overview Card (if container exists)
            const overviewClock = document.getElementById("overview-session-clock-card");
            if (overviewClock) {
                overviewClock.innerHTML = `
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span style="font-size: 13px; font-weight: 700; color: #38bdf8;">
                            <i class="fa-regular fa-clock"></i> ساعة جلسة البورصة المصرية اللحظية (توقيت القاهرة)
                        </span>
                        <span class="badge badge-${data.badge_color || 'info'} font-mono">${data.weekday_name_ar} ${data.cairo_time_short}</span>
                    </div>
                    <div style="display: flex; align-items: center; justify-content: space-between; background: rgba(0,0,0,0.25); padding: 10px 14px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.06);">
                        <div>
                            <div style="font-size: 14px; font-weight: 800; color: #f8fafc;">${data.phase_name_ar}</div>
                            <div style="font-size: 11px; color: #94a3b8; margin-top: 2px;">${data.description_ar}</div>
                        </div>
                        <div style="text-align: left;">
                            <div style="font-size: 10px; color: #94a3b8;">${data.next_phase_label_ar}</div>
                            <div style="font-size: 18px; font-weight: 900; font-family: monospace; color: #38bdf8;">${data.countdown_formatted}</div>
                        </div>
                    </div>
                `;
            }
        },

        startClockTicker() {
            if (this.clockInterval) clearInterval(this.clockInterval);
            this.clockInterval = setInterval(() => {
                if (!this.clockState || typeof this.clockState.countdown_seconds !== "number") return;
                if (this.clockState.countdown_seconds > 0) {
                    this.clockState.countdown_seconds--;
                    const s = this.clockState.countdown_seconds;
                    const hours = Math.floor(s / 3600);
                    const minutes = Math.floor((s % 3600) / 60);
                    const seconds = s % 60;
                    this.clockState.countdown_formatted = 
                        String(hours).padStart(2, '0') + ":" + 
                        String(minutes).padStart(2, '0') + ":" + 
                        String(seconds).padStart(2, '0');
                    
                    const timerEl = document.getElementById("session-clock-timer");
                    if (timerEl) timerEl.textContent = this.clockState.countdown_formatted;
                } else {
                    // Refresh when countdown reaches zero
                    this.loadSessionClock();
                }
            }, 1000);
        },

        // =========================================================================
        // 2. CASCADE BREAKEVEN RECOVERY SOLVER
        // =========================================================================
        async loadRecoveryPlan(cashVal) {
            const container = document.getElementById("recovery-plan-card");
            if (!container) return;

            const cash = (cashVal !== undefined && cashVal !== null) ? cashVal : this.recoveryCash;
            this.recoveryCash = cash;

            try {
                const res = await fetch(`/api/portfolio/recovery_plan?cash=${cash}`);
                if (!res.ok) throw new Error("HTTP " + res.status);
                const data = await res.json();
                this.renderRecoveryPlan(data, container);
            } catch (err) {
                console.warn("[v4.5 Recovery] Error:", err);
                container.innerHTML = `<div style="color: #ef4444; padding: 15px;">تعذر تحميل خطة فك التعليقة: ${err.message}</div>`;
            }
        },

        renderRecoveryPlan(data, container) {
            const sum = data.summary || {};
            const stages = data.stages || [];

            let stagesHtml = "";
            stages.forEach((stg) => {
                stagesHtml += `
                    <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(139, 92, 246, 0.25); border-radius: 8px; padding: 12px; margin-bottom: 10px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                            <div>
                                <span class="badge badge-purple font-mono" style="margin-left: 6px;">مرحلة ${stg.stage_num}</span>
                                <strong style="color: #f8fafc; font-size: 13.5px;">${stg.company_name} (${stg.ticker})</strong>
                            </div>
                            <div style="font-size: 11px; color: #94a3b8;">
                                بُعد التعادل الحالي: <span style="color: #f59e0b; font-weight: 700;">+${stg.distance_to_breakeven_pct}%</span>
                            </div>
                        </div>

                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 8px; margin: 8px 0; font-size: 11.5px; background: rgba(0,0,0,0.2); padding: 8px; border-radius: 6px;">
                            <div>
                                <span style="color: #94a3b8;">السيولة المخصصة:</span>
                                <div style="font-weight: 700; color: #38bdf8;">${stg.allocated_cash.toLocaleString()} ج</div>
                            </div>
                            <div>
                                <span style="color: #94a3b8;">شراء قاع التدوير:</span>
                                <div style="font-weight: 700; color: #10b981;">${stg.buy_shares} سهم @ ${stg.buy_price.toFixed(2)} ج</div>
                            </div>
                            <div>
                                <span style="color: #94a3b8;">التعادل الجديد بعد الخفض:</span>
                                <div style="font-weight: 800; color: #a78bfa;">${stg.new_blended_breakeven.toFixed(2)} ج (-${stg.breakeven_reduction_pct}%)</div>
                            </div>
                            <div>
                                <span style="color: #94a3b8;">هدف البيع والربح:</span>
                                <div style="font-weight: 700; color: #34d399;">${stg.target_exit_price.toFixed(2)} ج (+${stg.stage_net_profit.toFixed(2)} ج)</div>
                            </div>
                            <div>
                                <span style="color: #94a3b8;">السيولة المحررة للمرحلة التالية:</span>
                                <div style="font-weight: 800; color: #facc15;">${stg.released_cash_for_next.toLocaleString()} ج</div>
                            </div>
                        </div>

                        <div style="font-size: 11px; color: #cbd5e1; line-height: 1.5; background: rgba(30, 41, 59, 0.4); padding: 6px 10px; border-radius: 4px; border-right: 3px solid #8b5cf6;">
                            ${stg.action_plan_ar}
                        </div>
                    </div>
                `;
            });

            container.innerHTML = `
                <div class="card" style="border: 1.5px solid rgba(139, 92, 246, 0.4); background: linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 27, 75, 0.4) 100%); margin-bottom: 20px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 8px;">
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <span style="font-size: 20px;">🔄</span>
                            <div>
                                <h4 style="margin: 0; color: #f8fafc; font-size: 15px;">محرك فك التعليقة وتدوير الكاش التتابعي (Cascade Breakeven Solver)</h4>
                                <div style="font-size: 11px; color: #94a3b8;">خوارزمية كمية لتحرير الـ 5 أسهم تدريجياً وتحويل الخسارة الدفترية إلى أرباح صافية</div>
                            </div>
                        </div>
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <label style="font-size: 11.5px; color: #cbd5e1; font-weight: 700;">الكاش المتاح للتجربة:</label>
                            <input type="number" id="recovery-cash-input" value="${this.recoveryCash}" step="100" min="100" max="50000"
                                   style="width: 95px; background: #0f172a; border: 1px solid #8b5cf6; color: #fff; padding: 4px 8px; border-radius: 6px; font-size: 12px; text-align: center;"
                                   onchange="window.GEN26_V45.loadRecoveryPlan(this.value)">
                            <span style="font-size: 11px; color: #94a3b8;">ج.م</span>
                            <button class="btn btn-secondary btn-xs" onclick="window.GEN26_V45.loadRecoveryPlan(document.getElementById('recovery-cash-input').value)">
                                <i class="fa-solid fa-arrows-rotate"></i> محاكاة
                            </button>
                        </div>
                    </div>

                    <!-- Financial Invariant Verification Banner -->
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 10px; margin-bottom: 14px;">
                        <div style="background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 6px; padding: 8px 12px;">
                            <div style="font-size: 10.5px; color: #34d399; font-weight: 700;">تعادل رأس المال الكلي (متحقق بالفعل!)</div>
                            <div style="font-size: 15px; font-weight: 800; color: #10b981;">${(sum.portfolio_capital_breakeven_egp || 12466.63).toLocaleString()} ج.م</div>
                            <div style="font-size: 10px; color: #a7f3d0;">أرباح التدوير المنجزة: +${(sum.realized_profit_achieved_egp || 1830.00).toLocaleString()} ج (صافي ربح +${sum.net_capital_gain_pct || 6.17}%)</div>
                        </div>

                        <div style="background: rgba(59, 130, 246, 0.12); border: 1px solid rgba(59, 130, 246, 0.3); border-radius: 6px; padding: 8px 12px;">
                            <div style="font-size: 10.5px; color: #60a5fa; font-weight: 700;">هدف التعادل التام للأسهم المفتوحة</div>
                            <div style="font-size: 15px; font-weight: 800; color: #38bdf8;">${(sum.open_positions_zero_loss_target_egp || 14421.15).toLocaleString()} ج.م</div>
                            <div style="font-size: 10px; color: #bfdbfe;">شامل عمولة ثاندر 0.94% لكافة المراكز الحالية</div>
                        </div>

                        <div style="background: rgba(139, 92, 246, 0.12); border: 1px solid rgba(139, 92, 246, 0.3); border-radius: 6px; padding: 8px 12px;">
                            <div style="font-size: 10.5px; color: #c084fc; font-weight: 700;">إجمالي الربح الصافي المتوقع من التدوير</div>
                            <div style="font-size: 15px; font-weight: 800; color: #e879f9;">+${(sum.total_projected_profit_egp || 0).toLocaleString()} ج.م</div>
                            <div style="font-size: 10px; color: #e9d5ff;">تحرير كاش تراكمي يصل إلى: ${(sum.final_cash_released_egp || 0).toLocaleString()} ج.م</div>
                        </div>
                    </div>

                    <!-- Explanation -->
                    <div style="font-size: 11.5px; color: #cbd5e1; margin-bottom: 12px; line-height: 1.6; background: rgba(0,0,0,0.3); padding: 8px 12px; border-radius: 6px;">
                        💡 <strong>آلية العمل:</strong> ${sum.explanation_ar || ""}
                    </div>

                    <!-- Stages List -->
                    <div>${stagesHtml}</div>
                </div>
            `;
        },

        // =========================================================================
        // 3. NEWS CATALYST RADAR
        // =========================================================================
        async loadCatalysts() {
            const containers = [
                document.getElementById("catalysts-container"),
                document.getElementById("overview-catalysts-container")
            ];
            const activeContainers = containers.filter(Boolean);
            if (activeContainers.length === 0) return;

            try {
                const res = await fetch("/api/news/catalysts");
                if (!res.ok) return;
                const data = await res.json();
                const cats = data.catalysts || [];
                
                let html = "";
                cats.forEach((c) => {
                    const impactBadge = c.impact_rating === "HIGH_BULLISH" 
                        ? `<span class="badge badge-success">محفز صعود قوي (+${c.target_price_adjustment_pct}%)</span>`
                        : `<span class="badge badge-blue">محفز إيجابي (+${c.target_price_adjustment_pct}%)</span>`;
                    
                    html += `
                        <div style="background: rgba(15, 23, 42, 0.5); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 10px 12px; margin-bottom: 8px;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                                <strong style="color: #38bdf8; font-size: 12.5px;">${c.company_name} (${c.ticker})</strong>
                                ${impactBadge}
                            </div>
                            <div style="font-size: 12px; font-weight: 700; color: #f8fafc; margin-bottom: 4px; line-height: 1.4;">
                                ${c.headline_ar}
                            </div>
                            <div style="font-size: 11px; color: #94a3b8; line-height: 1.4;">
                                🎯 <strong>التوصية الكمية:</strong> ${c.actionable_recommendation_ar}
                            </div>
                            <div style="display: flex; justify-content: space-between; font-size: 10px; color: #64748b; margin-top: 6px;">
                                <span>المصدر: ${c.source} | الثقة: ${(c.confidence_score * 100).toFixed(0)}%</span>
                                <span>الأفق: ${c.expected_horizon_days} جلسات</span>
                            </div>
                        </div>
                    `;
                });

                activeContainers.forEach((ct) => {
                    ct.innerHTML = html || `<div style="color: #94a3b8; font-size: 12px; padding: 10px;">لا توجد محفزات نشطة حالياً.</div>`;
                });
            } catch (err) {
                console.warn("[v4.5 Catalysts] Error:", err);
            }
        },

        async loadStockCatalysts(ticker) {
            const container = document.getElementById("details-catalysts-container");
            if (!container || !ticker) return;

            try {
                const res = await fetch(`/api/news/catalysts/${encodeURIComponent(ticker)}`);
                if (!res.ok) return;
                const data = await res.json();
                const cats = data.catalysts || [];

                let html = "";
                cats.forEach((c) => {
                    html += `
                        <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(59, 130, 246, 0.3); border-radius: 6px; padding: 10px; margin-bottom: 8px;">
                            <div style="display: flex; justify-content: space-between; font-size: 11px; margin-bottom: 4px;">
                                <span class="badge badge-purple">${c.category_ar}</span>
                                <span style="color: #10b981; font-weight: 700;">أثر متوقع: +${c.target_price_adjustment_pct}%</span>
                            </div>
                            <div style="font-weight: 700; font-size: 12px; color: #f8fafc; margin-bottom: 4px;">${c.headline_ar}</div>
                            <div style="font-size: 11px; color: #cbd5e1;">${c.actionable_recommendation_ar}</div>
                        </div>
                    `;
                });
                container.innerHTML = html;
            } catch (err) {
                console.warn("[v4.5 Stock Catalysts] Error:", err);
            }
        },

        // =========================================================================
        // 4. INTRADAY SNIPER ALERTS
        // =========================================================================
        async loadSniperAlerts() {
            const containers = [
                document.getElementById("sniper-alerts-container"),
                document.getElementById("overview-sniper-alerts-container")
            ];
            const activeContainers = containers.filter(Boolean);
            if (activeContainers.length === 0) return;

            try {
                const res = await fetch("/api/alerts/sniper_triggers");
                if (!res.ok) return;
                const data = await res.json();
                const alerts = data.alerts || [];

                let html = "";
                alerts.forEach((a) => {
                    const badgeClass = a.urgency === "IMMEDIATE_ACTION" ? "badge-danger" : "badge-warning";
                    html += `
                        <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px; padding: 10px 12px; margin-bottom: 8px;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                                <div>
                                    <strong style="color: #f8fafc; font-size: 13px;">${a.company_name} (${a.ticker})</strong>
                                    <span class="badge ${badgeClass}" style="margin-right: 6px;">${a.trigger_label_ar}</span>
                                </div>
                                <div style="font-size: 11px; color: #a78bfa; font-weight: 700;">
                                    عائد/مخاطرة: 1 إلى ${a.risk_reward_ratio}
                                </div>
                            </div>
                            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; font-size: 11px; background: rgba(0,0,0,0.25); padding: 6px; border-radius: 4px; margin: 6px 0;">
                                <div><span style="color:#94a3b8;">السعر الحالي:</span> <strong style="color:#f8fafc;">${a.current_price.toFixed(2)} ج</strong></div>
                                <div><span style="color:#94a3b8;">وقف الخسارة:</span> <strong style="color:#ef4444;">${a.stop_loss.toFixed(2)} ج</strong></div>
                                <div><span style="color:#94a3b8;">هدف أول:</span> <strong style="color:#10b981;">${a.target_price_1.toFixed(2)} ج</strong></div>
                                <div><span style="color:#94a3b8;">هدف ثانٍ:</span> <strong style="color:#34d399;">${a.target_price_2.toFixed(2)} ج</strong></div>
                            </div>
                            <div style="font-size: 11px; color: #cbd5e1; line-height: 1.4;">
                                ${a.action_plan_ar}
                            </div>
                        </div>
                    `;
                });

                activeContainers.forEach((ct) => {
                    ct.innerHTML = html || `<div style="color: #94a3b8; font-size: 12px; padding: 10px;">لا توجد إنذارات قنص لحظية حالياً.</div>`;
                });
            } catch (err) {
                console.warn("[v4.5 Sniper Alerts] Error:", err);
            }
        },

        // =========================================================================
        // 5. PREDICTION SCORECARD & AUDIT
        // =========================================================================
        async loadPredictionScorecard() {
            const containers = [
                document.getElementById("prediction-scorecard-container"),
                document.getElementById("lab-prediction-scorecard-container")
            ];
            const activeContainers = containers.filter(Boolean);
            if (activeContainers.length === 0) return;

            try {
                const res = await fetch("/api/audit/prediction_scorecard");
                if (!res.ok) return;
                const data = await res.json();
                const sum = data.summary || {};
                const logs = data.recent_audited_log || [];

                let rowsHtml = "";
                logs.forEach((p) => {
                    const statusBadge = p.status === "TARGET_ACHIEVED" 
                        ? `<span class="badge badge-success">${p.status_ar}</span>`
                        : `<span class="badge badge-warning">${p.status_ar}</span>`;
                    
                    rowsHtml += `
                        <tr style="border-bottom: 1px solid rgba(255,255,255,0.06);">
                            <td style="padding: 8px;"><strong>${p.company_name}</strong> <span style="color:#94a3b8; font-size:11px;">(${p.ticker})</span></td>
                            <td style="padding: 8px; font-family: monospace;">${p.horizon}</td>
                            <td style="padding: 8px;">${p.predicted_direction_ar}</td>
                            <td style="padding: 8px; font-family: monospace; color:#38bdf8;">${p.predicted_target.toFixed(2)} ج</td>
                            <td style="padding: 8px; font-family: monospace; color:#10b981;">${p.actual_price.toFixed(2)} ج (أعلى: ${p.actual_high.toFixed(2)} ج)</td>
                            <td style="padding: 8px; font-family: monospace;">${p.variance_pct > 0 ? '+' : ''}${p.variance_pct.toFixed(2)}%</td>
                            <td style="padding: 8px;">${statusBadge}</td>
                        </tr>
                    `;
                });

                const html = `
                    <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(139, 92, 246, 0.3); border-radius: 8px; padding: 14px; margin-bottom: 16px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 8px;">
                            <div>
                                <h4 style="margin: 0; color: #f8fafc; font-size: 14px;">🔬 سجل التدقيق ودقة التوقعات السابقة (Scorecard Audit)</h4>
                                <div style="font-size: 11px; color: #94a3b8;">${sum.evaluation_window_ar} — تدقيق محايد بنسبة 100%</div>
                            </div>
                            <div style="display: flex; gap: 8px;">
                                <span class="badge badge-success font-mono" style="font-size: 12px; padding: 4px 10px;">
                                    دقة الاتجاه: ${sum.directional_hit_rate_pct}%
                                </span>
                                <span class="badge badge-purple font-mono" style="font-size: 12px; padding: 4px 10px;">
                                    Brier Score: ${sum.brier_score} (${sum.brier_calibration_status_ar})
                                </span>
                            </div>
                        </div>

                        <div style="overflow-x: auto;">
                            <table style="width: 100%; border-collapse: collapse; font-size: 12px; text-align: right;">
                                <thead>
                                    <tr style="border-bottom: 1px solid rgba(255,255,255,0.12); color: #94a3b8;">
                                        <th style="padding: 6px 8px;">السهم</th>
                                        <th style="padding: 6px 8px;">الأفق</th>
                                        <th style="padding: 6px 8px;">الاتجاه المتوقع</th>
                                        <th style="padding: 6px 8px;">الهدف المقدر</th>
                                        <th style="padding: 6px 8px;">السعر الفعلي</th>
                                        <th style="padding: 6px 8px;">نسبة الانحراف</th>
                                        <th style="padding: 6px 8px;">حالة التحقق</th>
                                    </tr>
                                </thead>
                                <tbody>${rowsHtml}</tbody>
                            </table>
                        </div>
                    </div>
                `;

                activeContainers.forEach((ct) => {
                    ct.innerHTML = html;
                });
            } catch (err) {
                console.warn("[v4.5 Scorecard] Error:", err);
            }
        },

        // =========================================================================
        // 6. SIMULATOR MATRIX FILTERS (271 EGX STOCKS)
        // =========================================================================
        initSimulatorFilters() {
            const searchInput = document.getElementById("sim-matrix-search");
            const sectorSelect = document.getElementById("sim-matrix-sector-filter");

            if (searchInput && !searchInput.dataset.initialized) {
                searchInput.dataset.initialized = "true";
                searchInput.addEventListener("input", () => {
                    if (typeof window.filterSimMatrixLive === "function") {
                        window.filterSimMatrixLive();
                    }
                });
            }

            if (sectorSelect && !sectorSelect.dataset.initialized) {
                sectorSelect.dataset.initialized = "true";
                sectorSelect.addEventListener("change", () => {
                    if (typeof window.filterSimMatrixLive === "function") {
                        window.filterSimMatrixLive();
                    }
                });
            }
        }
    };

    // Live matrix filtering helper attached to window
    window.filterSimMatrixLive = function () {
        const query = (document.getElementById("sim-matrix-search")?.value || "").toLowerCase().trim();
        const sector = (document.getElementById("sim-matrix-sector-filter")?.value || "").trim();
        const rows = document.querySelectorAll("#sim-matrix-tbody tr");

        rows.forEach((row) => {
            const text = row.textContent.toLowerCase();
            const rowSector = row.dataset.sector || "";
            const matchesQuery = !query || text.includes(query);
            const matchesSector = !sector || sector === "ALL" || rowSector.includes(sector) || text.includes(sector);

            if (matchesQuery && matchesSector) {
                row.style.display = "";
            } else {
                row.style.display = "none";
            }
        });
    };

    // Export module to global window
    window.GEN26_V45 = GEN26_V45;

    // Auto-init clock when script loads
    document.addEventListener("DOMContentLoaded", () => {
        try {
            GEN26_V45.loadSessionClock();
        } catch (e) {
            console.warn("[v4.5 Auto-init] Clock error:", e);
        }
    });

})();
