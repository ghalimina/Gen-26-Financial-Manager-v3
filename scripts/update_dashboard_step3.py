#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# scripts/update_dashboard_step3.py

import os
import shutil

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_TEMPLATE = os.path.join(WORKSPACE, "dashboard", "templates", "index.html")

with open(INDEX_TEMPLATE, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update renderTab to include short_term_opportunities
old_render_tab = """                } else if (tabId === 'research_lab' || tabId === 'research-lab') {
                    loadResearchLabTab();
                }"""

new_render_tab = """                } else if (tabId === 'research_lab' || tabId === 'research-lab') {
                    loadResearchLabTab();
                } else if (tabId === 'short_term_opportunities') {
                    fetchShortTermOpportunities();
                }"""

if old_render_tab in content:
    content = content.replace(old_render_tab, new_render_tab)

# 2. Add fetchShortTermOpportunities implementation
fetch_short_term_js = """
        // =====================================================================
        // ⚡ SHORT-TERM OPPORTUNITIES & CORRELATION MATRIX INTEGRATION
        // =====================================================================
        async function fetchShortTermOpportunities() {
            const grid = document.getElementById('short-term-opps-grid');
            const matrixContainer = document.getElementById('correlation-matrix-container');
            const clusterBanner = document.getElementById('cluster-risk-banner');
            const clusterDetails = document.getElementById('cluster-risk-details');

            // 1. Fetch 10D Opportunities
            try {
                const res = await fetch('/api/opportunities/10d');
                if (!res.ok) throw new Error("HTTP " + res.status);
                const data = await res.json();
                const opps = data.opportunities || [];

                if (grid) {
                    if (opps.length === 0) {
                        grid.innerHTML = `<div style="grid-column: span 3; text-align: center; color: var(--text-muted); padding: 30px;">${data.fallback_message_ar || 'لا توجد فرص قصيرة المدى تستوفي معايير الجودة والسيولة حالياً.'}</div>`;
                    } else {
                        const top3 = opps.slice(0, 3);
                        grid.innerHTML = top3.map((s, idx) => {
                            const rankBadges = [
                                { badge: '🥇 المركز #1', color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.15)', border: '#f59e0b' },
                                { badge: '🥈 المركز #2', color: '#94a3b8', bg: 'rgba(148, 163, 184, 0.15)', border: '#94a3b8' },
                                { badge: '🥉 المركز #3', color: '#d97706', bg: 'rgba(217, 119, 6, 0.15)', border: '#d97706' }
                            ];
                            const rb = rankBadges[idx] || { badge: `#${idx+1}`, color: '#60a5fa', bg: 'rgba(59, 130, 246, 0.15)', border: '#3b82f6' };
                            const curPrice = parseFloat(s.current_price || 0.0);
                            const targetVal = parseFloat(s.target_price_10d || (curPrice * 1.085));
                            const stopVal = parseFloat(s.stop_loss || (curPrice * 0.94));
                            const upsidePct = parseFloat(s.expected_upside_10d_pct || (((targetVal - curPrice)/curPrice)*100)).toFixed(1);
                            const downsidePct = Math.abs(parseFloat(s.expected_downside_10d_pct || (((curPrice - stopVal)/curPrice)*100))).toFixed(1);
                            const rrRatio = s.reward_to_downside_ratio || (upsidePct / (downsidePct || 1.0)).toFixed(1);

                            return `
                                <div class="card" style="background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(255, 255, 255, 0.12); border-radius: var(--radius-md); padding: 18px; display: flex; flex-direction: column; justify-content: space-between; position: relative;">
                                    <div>
                                        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
                                            <div>
                                                <span class="badge" style="background: ${rb.bg}; color: ${rb.color}; border: 1px solid ${rb.border}; font-weight: 800; font-size: 11px;">${rb.badge}</span>
                                                <div style="font-size: 15px; font-weight: 800; color: #ffffff; margin-top: 4px;">${s.company_name || s.ticker}</div>
                                                <div class="ltr-text text-blue font-bold font-mono" style="font-size: 12px;">${s.ticker}</div>
                                            </div>
                                            <div style="text-align: left;">
                                                <div class="ltr-text font-bold font-mono" style="font-size: 18px; color: #34d399;">${curPrice.toFixed(2)} <span style="font-size: 11px; color: var(--text-muted);">ج.م</span></div>
                                                <span class="badge badge-green" style="font-size: 10px; padding: 2px 6px;">⚡ زخم 10 أيام</span>
                                            </div>
                                        </div>

                                        <div style="background: rgba(0,0,0,0.3); border-radius: var(--radius-sm); padding: 10px 12px; margin-bottom: 12px; border: 1px solid rgba(255,255,255,0.06);">
                                            <div style="display: flex; justify-content: space-between; font-size: 11.5px; margin-bottom: 6px;">
                                                <span style="color: var(--text-muted);">نطاق الدخول المقترح:</span>
                                                <span class="ltr-text text-blue font-bold font-mono">${s.entry_zone || (curPrice * 0.985).toFixed(2) + ' – ' + curPrice.toFixed(2)} ج.م</span>
                                            </div>
                                            <div style="display: flex; justify-content: space-between; font-size: 11.5px; margin-bottom: 6px;">
                                                <span style="color: var(--text-muted);">🎯 مستهدف الـ 10 أيام (+Upside):</span>
                                                <span class="ltr-text text-green font-bold font-mono">${targetVal.toFixed(2)} ج.م (+${upsidePct}%)</span>
                                            </div>
                                            <div style="display: flex; justify-content: space-between; font-size: 11.5px;">
                                                <span style="color: var(--text-muted);">🛑 وقف الخسارة الديناميكي:</span>
                                                <span class="ltr-text text-red font-bold font-mono">${stopVal.toFixed(2)} ج.م (-${downsidePct}%)</span>
                                            </div>
                                        </div>

                                        <div style="display: flex; justify-content: space-between; align-items: center; background: rgba(59, 130, 246, 0.08); padding: 6px 10px; border-radius: 6px; margin-bottom: 14px; font-size: 11px;">
                                            <span style="color: #93c5fd;">⚖️ نسبة العائد للمخاطرة (R:R):</span>
                                            <span class="badge badge-green font-bold ltr-text font-mono">${rrRatio}x Reward</span>
                                        </div>
                                    </div>

                                    <div style="display: flex; gap: 8px; margin-top: auto;">
                                        <button class="btn btn-primary btn-sm btn-block" onclick="openPortfolioSizer('${s.ticker}')">
                                            <i class="fa-solid fa-wallet"></i> 💼 توزيع الميزانية والشراء
                                        </button>
                                        <button class="btn btn-secondary btn-sm" onclick="loadStockDetails('${s.ticker}')" title="ملف السهم">
                                            <i class="fa-solid fa-chart-line"></i>
                                        </button>
                                    </div>
                                </div>
                            `;
                        }).join('');
                    }
                }
            } catch (err) {
                console.warn("10D Opportunities fetch failed:", err);
            }

            // 2. Fetch Correlation Matrix & Cluster Risk
            try {
                const resCorr = await fetch('/api/correlation');
                if (!resCorr.ok) throw new Error("HTTP " + resCorr.status);
                const corrData = await resCorr.json();

                // Cluster Risk Banner Check
                if (clusterBanner && clusterDetails) {
                    if (corrData.cluster_risk === "HIGH_CONCENTRATION" || (corrData.max_pairwise_correlation && corrData.max_pairwise_correlation > 0.75)) {
                        clusterBanner.style.display = 'block';
                        clusterDetails.innerText = corrData.cluster_risk_ar || 'تم رصد تركز قطاعي مرتفع بين بعض الأسهم المتصدرة تفوق 0.75.';
                    } else {
                        clusterBanner.style.display = 'none';
                    }
                }

                // Render Correlation Matrix Table
                if (matrixContainer && corrData.correlation_matrix) {
                    const matrix = corrData.correlation_matrix;
                    const tickers = Object.keys(matrix);
                    if (tickers.length === 0) return;

                    let tableHtml = `
                        <table class="table" style="font-size: 12px; text-align: center; width: 100%;">
                            <thead>
                                <tr style="background: rgba(0,0,0,0.4);">
                                    <th style="text-align: right;">السهم / الارتباط</th>
                                    ${tickers.map(t => `<th class="font-mono">${t.replace('.CA', '')}</th>`).join('')}
                                </tr>
                            </thead>
                            <tbody>
                    `;

                    tickers.forEach(t1 => {
                        tableHtml += `<tr><td style="text-align: right; font-weight: 800; color: #93c5fd;" class="font-mono">${t1}</td>`;
                        tickers.forEach(t2 => {
                            const val = matrix[t1]?.[t2] ?? (t1 === t2 ? 1.0 : 0.45);
                            let bg = 'rgba(16, 185, 129, 0.15)'; // Green <= 0.40
                            let textCol = '#34d399';
                            if (val > 0.70) {
                                bg = 'rgba(239, 68, 68, 0.25)'; // Red > 0.70
                                textCol = '#f87171';
                            } else if (val > 0.40) {
                                bg = 'rgba(245, 158, 11, 0.20)'; // Yellow 0.40 - 0.70
                                textCol = '#fbbf24';
                            }
                            tableHtml += `
                                <td style="background: ${bg}; color: ${textCol}; font-weight: 700;" class="font-mono">
                                    ${val.toFixed(2)}
                                </td>
                            `;
                        });
                        tableHtml += `</tr>`;
                    });

                    tableHtml += `</tbody></table>`;
                    matrixContainer.innerHTML = tableHtml;
                }
            } catch (corrErr) {
                console.warn("Correlation fetch failed:", corrErr);
            }
        }
"""

if "fetchShortTermOpportunities" not in content:
    # Insert right before toggleMobileMenu or start of ranking loader
    content = content.replace(
        "        function toggleMobileMenu() {",
        fetch_short_term_js + "\n        function toggleMobileMenu() {"
    )

# Write to dashboard/templates/index.html
with open(INDEX_TEMPLATE, "w", encoding="utf-8") as f:
    f.write(content)

# Mirror to templates/index.html and dashboard/index.html
for target_rel in ["templates/index.html", "dashboard/index.html"]:
    target_path = os.path.join(WORKSPACE, target_rel)
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    shutil.copyfile(INDEX_TEMPLATE, target_path)

print("Step 3 Dashboard updates mirrored successfully!")
