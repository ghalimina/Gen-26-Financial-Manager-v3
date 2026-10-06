#!/usr/bin/env python3
# =============================================================================
# scripts/update_dashboard_thndr_expansion.py
# Injects Mutual Funds (67 Funds) & 270 Stocks Universe into Frontend UI
# =============================================================================

import os
import shutil

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_HTML = os.path.join(WORKSPACE, "dashboard", "templates", "index.html")

with open(SRC_HTML, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update Sidebar Navigation
sidebar_old = """            <li class="nav-item" id="nav-ranking" onclick="navigateTo('ranking')"><i class="fa-solid fa-trophy"></i> 🏆 أفضل الأسهم والترتيب (Top 100)</li>"""
sidebar_new = """            <li class="nav-item" id="nav-ranking" onclick="navigateTo('ranking')"><i class="fa-solid fa-trophy"></i> 🏆 أفضل الأسهم والترتيب (270 سهم)</li>"""
if sidebar_old in content:
    content = content.replace(sidebar_old, sidebar_new, 1)
    print("[1] Updated sidebar ranking label to 270 stocks.")

portfolio_nav_old = """            <li class="nav-item" id="nav-real_portfolio" onclick="navigateTo('real_portfolio')"><i class="fa-solid fa-wallet"></i> 💼 المحفظة الحقيقية والأرباح</li>"""
portfolio_nav_new = """            <li class="nav-item" id="nav-real_portfolio" onclick="navigateTo('real_portfolio')"><i class="fa-solid fa-wallet"></i> 💼 المحفظة الحقيقية والأرباح</li>
            <li class="nav-item" id="nav-mutual_funds" onclick="navigateTo('mutual_funds')"><i class="fa-solid fa-building-columns"></i> 🏦 صناديق الاستثمار (Thndr 67 Funds)</li>"""
if portfolio_nav_old in content and 'id="nav-mutual_funds"' not in content:
    content = content.replace(portfolio_nav_old, portfolio_nav_new, 1)
    print("[2] Added Mutual Funds item to sidebar.")

# 2. Add Tab Panel for Mutual Funds before "</div> <!-- End of content-scroll -->"
mutual_funds_panel = """
            <!-- ========================================================= -->
            <!-- 🏦 TAB: THNDR MUTUAL FUNDS DIRECTORY (67 FUNDS) -->
            <!-- ========================================================= -->
            <div class="tab-panel" id="tab-mutual_funds">
                <!-- Hero Header -->
                <div class="card hero-briefing-card" style="margin-bottom: 24px; border: 1px solid rgba(59, 130, 246, 0.3); background: linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 58, 138, 0.25) 100%);">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 16px;">
                        <div>
                            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                                <span style="font-size: 28px;">🏦</span>
                                <h2 style="font-size: 22px; font-weight: 900; color: #fff; margin: 0;">دليل صناديق الاستثمار الشامل في مصر (Thndr 67 Funds)</h2>
                                <span class="badge badge-green" style="font-size: 11px;">محدث لحظياً بالأسعار والعوائد</span>
                            </div>
                            <div style="font-size: 13.5px; color: #cbd5e1; max-width: 820px; line-height: 1.6;">
                                تغطية حصرية لكافة الـ <strong>67 صندوقاً استثمارياً</strong> المرخصة من الهيئة العامة للرقابة المالية (FRA) والمتاحة للشراء المباشر على منصة ثاندر (Thndr). تصنيف احترافي عبر 7 فئات أصول، ومتابعة فورية لصافي قيمة الوثيقة (NAV)، العائد السنوي، ومستوى المخاطرة.
                            </div>
                        </div>
                        <div style="display: flex; gap: 10px;">
                            <button class="btn btn-secondary" onclick="loadMutualFundsData()" style="padding: 9px 16px;">
                                <i class="fa-solid fa-rotate"></i> تحديث القائمة
                            </button>
                            <button class="btn btn-success" onclick="openPortfolioSizerModal()" style="padding: 9px 16px;">
                                <i class="fa-solid fa-calculator"></i> موزع الميزانية
                            </button>
                        </div>
                    </div>

                    <!-- Macro KPI Badges -->
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin-top: 20px;">
                        <div style="background: rgba(0,0,0,0.35); border: 1px solid rgba(255,255,255,0.08); border-radius: var(--radius-sm); padding: 12px 14px;">
                            <div style="font-size: 11px; color: var(--text-muted);">إجمالي الصناديق المتوفرة</div>
                            <div style="font-size: 20px; font-weight: 900; color: #fff; font-family: 'JetBrains Mono', monospace;">67 <span style="font-size: 12px; color: #94a3b8;">صندوقاً</span></div>
                        </div>
                        <div style="background: rgba(0,0,0,0.35); border: 1px solid rgba(245,158,11,0.2); border-radius: var(--radius-sm); padding: 12px 14px;">
                            <div style="font-size: 11px; color: #fbbf24;">🥇 صناديق الذهب والمعادن</div>
                            <div style="font-size: 20px; font-weight: 900; color: #fbbf24; font-family: 'JetBrains Mono', monospace;">3 <span style="font-size: 12px; color: #94a3b8;">(AZG, B-Gold, Dahab)</span></div>
                        </div>
                        <div style="background: rgba(0,0,0,0.35); border: 1px solid rgba(16,185,129,0.2); border-radius: var(--radius-sm); padding: 12px 14px;">
                            <div style="font-size: 11px; color: #34d399;">💵 أسواق النقد والسيولة اليومية</div>
                            <div style="font-size: 20px; font-weight: 900; color: #34d399; font-family: 'JetBrains Mono', monospace;">26 <span style="font-size: 12px; color: #94a3b8;">صندوقاً نقدياً</span></div>
                        </div>
                        <div style="background: rgba(0,0,0,0.35); border: 1px solid rgba(59,130,246,0.2); border-radius: var(--radius-sm); padding: 12px 14px;">
                            <div style="font-size: 11px; color: #60a5fa;">📈 صناديق الأسهم والشريعة</div>
                            <div style="font-size: 20px; font-weight: 900; color: #60a5fa; font-family: 'JetBrains Mono', monospace;">30 <span style="font-size: 12px; color: #94a3b8;">(18 أسهم + 12 شريعة)</span></div>
                        </div>
                        <div style="background: rgba(0,0,0,0.35); border: 1px solid rgba(139,92,246,0.2); border-radius: var(--radius-sm); padding: 12px 14px;">
                            <div style="font-size: 11px; color: #c084fc;">⚖️ صناديق متوازنة ومؤشرات</div>
                            <div style="font-size: 20px; font-weight: 900; color: #c084fc; font-family: 'JetBrains Mono', monospace;">8 <span style="font-size: 12px; color: #94a3b8;">(6 متوازنة + 2 سندات/مؤشر)</span></div>
                        </div>
                    </div>
                </div>

                <!-- Filter Controls & Search -->
                <div class="card" style="margin-bottom: 20px; padding: 16px 20px; border: 1px solid rgba(255,255,255,0.08);">
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 14px;">
                        <!-- Category Pills -->
                        <div style="display: flex; gap: 8px; flex-wrap: wrap;" id="funds-category-pills">
                            <button class="btn btn-sm fund-filter-chip active" onclick="filterFundsByCategory('ALL', this)">🏦 الكل (67)</button>
                            <button class="btn btn-sm fund-filter-chip" onclick="filterFundsByCategory('GOLD', this)">🥇 ذهب (3)</button>
                            <button class="btn btn-sm fund-filter-chip" onclick="filterFundsByCategory('MONEY_MARKET', this)">💵 نقدية وسيولة (26)</button>
                            <button class="btn btn-sm fund-filter-chip" onclick="filterFundsByCategory('EQUITY', this)">📈 أسهم (18)</button>
                            <button class="btn btn-sm fund-filter-chip" onclick="filterFundsByCategory('ISLAMIC_SHARIA', this)">🌙 شريعة إسلامية (12)</button>
                            <button class="btn btn-sm fund-filter-chip" onclick="filterFundsByCategory('BALANCED', this)">⚖️ متوازنة (6)</button>
                            <button class="btn btn-sm fund-filter-chip" onclick="filterFundsByCategory('ETF', this)">📊 مؤشرات وسندات (2)</button>
                        </div>

                        <!-- Search Box -->
                        <div style="display: flex; gap: 10px; align-items: center; min-width: 280px;">
                            <div style="position: relative; width: 100%;">
                                <input type="text" id="funds-search-input" class="form-control" placeholder="ابحث باسم الصندوق، الكود، أو المدير..." oninput="renderMutualFunds()" style="padding-right: 36px;">
                                <i class="fa-solid fa-magnifying-glass" style="position: absolute; right: 12px; top: 12px; color: var(--text-muted);"></i>
                            </div>
                            <span id="funds-visible-count" class="badge badge-blue" style="white-space: nowrap; font-size: 12px; padding: 6px 10px;">67 من 67</span>
                        </div>
                    </div>
                </div>

                <!-- Funds Grid -->
                <div id="funds-grid-container" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(330px, 1fr)); gap: 16px; margin-bottom: 40px;">
                    <!-- Loaded dynamically via loadMutualFundsData() -->
                </div>
            </div>
"""

scroll_end_target = "        </div> <!-- End of content-scroll -->"
if scroll_end_target in content and 'id="tab-mutual_funds"' not in content:
    content = content.replace(scroll_end_target, mutual_funds_panel + "\n" + scroll_end_target, 1)
    print("[3] Injected #tab-mutual_funds panel into content-scroll.")

# 3. Add Fund Detail Modal before </body>
fund_modal_html = """
    <!-- Fund Detail Modal -->
    <div class="modal-overlay" id="fund-detail-modal">
        <div class="modal-card" style="max-width: 580px;">
            <div class="modal-header">
                <div class="modal-title">
                    <span id="modal-fund-icon" style="margin-left: 8px;">🏦</span>
                    <span id="modal-fund-title">تفاصيل الصندوق الاستثماري</span>
                </div>
                <button type="button" class="modal-close-btn" onclick="closeFundModal()"><i class="fa-solid fa-xmark"></i></button>
            </div>
            <div id="modal-fund-content" style="padding: 10px 0; font-size: 13.5px; line-height: 1.7;"></div>
            <div style="display: flex; gap: 10px; margin-top: 18px;">
                <button class="btn btn-success btn-block" id="modal-fund-invest-btn" onclick="investInModalFund()"><i class="fa-solid fa-calculator"></i> توزيع رأس مال بهذا الصندوق</button>
                <button class="btn btn-secondary" onclick="closeFundModal()">إغلاق</button>
            </div>
        </div>
    </div>
"""
if "</body>" in content and 'id="fund-detail-modal"' not in content:
    content = content.replace("</body>", fund_modal_html + "\n</body>", 1)
    print("[4] Injected #fund-detail-modal.")

# 4. Update VALID_TABS
valid_tabs_old = """        const VALID_TABS = [
            'overview', 'alpha_scanner', 'short_term_opportunities', 'ranking', 'details', 'real_portfolio',
            'paper_portfolio', 'watchlist', 'insider_radar', 'arbitrage_monitor', 'signals', 'risk_center',
            'stress_center', 'paper_vs_bt', 'observatory', 'universe_audit', 'health', 'execution',
            'research_lab', 'research-lab', 'trading_agents', 'system_settings'
        ];"""

valid_tabs_new = """        const VALID_TABS = [
            'overview', 'alpha_scanner', 'short_term_opportunities', 'ranking', 'details', 'real_portfolio',
            'mutual_funds', 'paper_portfolio', 'watchlist', 'insider_radar', 'arbitrage_monitor', 'signals',
            'risk_center', 'stress_center', 'paper_vs_bt', 'observatory', 'universe_audit', 'health',
            'execution', 'research_lab', 'research-lab', 'trading_agents', 'system_settings'
        ];"""
if valid_tabs_old in content:
    content = content.replace(valid_tabs_old, valid_tabs_new, 1)
    print("[5] Added mutual_funds to VALID_TABS.")

# 5. Update TITLE_MAP
title_map_old = """            'real_portfolio': '💼 سجل محفظتي الحقيقية وتوصيات الذكاء الاصطناعي',"""
title_map_new = """            'real_portfolio': '💼 سجل محفظتي الحقيقية وتوصيات الذكاء الاصطناعي',
            'mutual_funds': '🏦 دليل صناديق الاستثمار في مصر (67 صندوق استثماري على منصة ثاندر Thndr)',"""
if title_map_old in content and "'mutual_funds'" not in content:
    content = content.replace(title_map_old, title_map_new, 1)
    print("[6] Added mutual_funds to TITLE_MAP.")

# 6. Update renderTab fetchers
render_tab_target = "                if (tabId === 'alpha_scanner') {"
render_tab_replacement = """                if (tabId === 'mutual_funds') {
                    loadMutualFundsData();
                } else if (tabId === 'alpha_scanner') {"""
if render_tab_target in content and "tabId === 'mutual_funds'" not in content:
    content = content.replace(render_tab_target, render_tab_replacement, 1)
    print("[7] Added loadMutualFundsData call to renderTab.")

# 7. Add Mutual Funds JavaScript logic
funds_js_logic = """
        // =====================================================================
        // 🏦 THNDR MUTUAL FUNDS JAVASCRIPT ENGINE (67 FUNDS)
        // =====================================================================
        let allFundsData = [];
        let currentFundCategory = 'ALL';
        let activeModalFund = null;

        async function loadMutualFundsData() {
            const container = document.getElementById('funds-grid-container');
            if (container && (!allFundsData || allFundsData.length === 0)) {
                container.innerHTML = '<div style="text-align: center; padding: 40px; color: var(--text-muted); grid-column: 1/-1;"><i class="fa-solid fa-spinner fa-spin fa-2x"></i><br><br>جاري تحميل بيانات الصناديق الـ 67 من الخادم...</div>';
            }

            try {
                const res = await fetch('/api/funds');
                if (!res.ok) throw new Error("HTTP " + res.status);
                const data = await res.json();
                if (data.status === 'SUCCESS' && Array.isArray(data.funds)) {
                    allFundsData = data.funds;
                    renderMutualFunds();
                }
            } catch (e) {
                console.error("Error fetching funds:", e);
                if (container) {
                    container.innerHTML = '<div style="color: #ef4444; padding: 30px; text-align: center; grid-column: 1/-1;">تعذر تحميل الصناديق. يرجى التأكد من اتصال الخادم.</div>';
                }
            }
        }

        function filterFundsByCategory(cat, btn) {
            currentFundCategory = cat;
            document.querySelectorAll('.fund-filter-chip').forEach(c => c.classList.remove('active'));
            if (btn) btn.classList.add('active');
            renderMutualFunds();
        }

        function renderMutualFunds() {
            const container = document.getElementById('funds-grid-container');
            if (!container) return;
            const searchInput = document.getElementById('funds-search-input');
            const q = searchInput ? searchInput.value.trim().toLowerCase() : '';

            let filtered = allFundsData || [];
            if (currentFundCategory !== 'ALL') {
                if (currentFundCategory === 'ETF') {
                    filtered = filtered.filter(f => f.category === 'ETF' || f.category === 'FIXED_INCOME');
                } else {
                    filtered = filtered.filter(f => f.category === currentFundCategory);
                }
            }
            if (q) {
                filtered = filtered.filter(f => 
                    (f.name_ar && f.name_ar.toLowerCase().includes(q)) ||
                    (f.name_en && f.name_en.toLowerCase().includes(q)) ||
                    (f.ticker && f.ticker.toLowerCase().includes(q)) ||
                    (f.manager && f.manager.toLowerCase().includes(q)) ||
                    (f.sponsor && f.sponsor.toLowerCase().includes(q))
                );
            }

            const countEl = document.getElementById('funds-visible-count');
            if (countEl) countEl.innerText = `${filtered.length} من 67 صندوقاً`;

            if (filtered.length === 0) {
                container.innerHTML = '<div style="text-align: center; padding: 40px; color: var(--text-muted); grid-column: 1/-1;">لا توجد صناديق مطابقة لمعايير البحث.</div>';
                return;
            }

            let html = '';
            filtered.forEach(f => {
                const riskClass = f.risk_level === 'LOW' ? 'badge-green' : (f.risk_level === 'MEDIUM' ? 'badge-yellow' : 'badge-red');
                const retColor = (f.annual_return_pct >= 20.0) ? '#34d399' : '#60a5fa';
                const shariaTag = f.sharia_compliant ? '<span class="badge" style="background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16,185,129,0.3); font-size: 10px;"><i class="fa-solid fa-moon"></i> شريعة</span>' : '';
                
                // Icon based on category
                const catIcon = f.category === 'GOLD' ? '🥇' : (f.category === 'MONEY_MARKET' ? '💵' : (f.category === 'EQUITY' ? '📈' : (f.category === 'ISLAMIC_SHARIA' ? '🌙' : '⚖️')));

                html += `
                <div class="card" style="border: 1px solid rgba(255,255,255,0.08); border-radius: var(--radius-md); padding: 18px; display: flex; flex-direction: column; justify-content: space-between; position: relative; background: linear-gradient(145deg, rgba(17,24,39,0.85) 0%, rgba(15,23,42,0.92) 100%);">
                    <div>
                        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px;">
                            <div style="display: flex; gap: 6px; align-items: center; flex-wrap: wrap;">
                                <span class="badge badge-blue font-mono" style="font-size: 11px;">${f.ticker}</span>
                                <span class="badge ${riskClass}" style="font-size: 10px;">${f.risk_level_ar || f.risk_level}</span>
                                ${shariaTag}
                            </div>
                            <span style="font-size: 12px; color: var(--text-muted);">${catIcon} ${f.category_ar}</span>
                        </div>

                        <div style="margin-bottom: 14px;">
                            <div style="font-size: 15px; font-weight: 800; color: #fff; margin-bottom: 3px; line-height: 1.4;">${f.name_ar}</div>
                            <div style="font-size: 11px; color: var(--text-dim); font-family: 'JetBrains Mono', monospace;">${f.name_en}</div>
                        </div>

                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; background: rgba(0,0,0,0.35); padding: 10px 12px; border-radius: 8px; margin-bottom: 14px; border: 1px solid rgba(255,255,255,0.04);">
                            <div>
                                <div style="font-size: 10px; color: var(--text-dim);">سعر الوثيقة (NAV)</div>
                                <div style="font-size: 15px; font-weight: 800; color: #fff; font-family: 'JetBrains Mono', monospace;">${Number(f.nav_egp).toFixed(2)} <span style="font-size: 10px; color: var(--text-muted);">ج.م</span></div>
                            </div>
                            <div>
                                <div style="font-size: 10px; color: var(--text-dim);">العائد السنوي التقديري</div>
                                <div style="font-size: 15px; font-weight: 800; color: ${retColor}; font-family: 'JetBrains Mono', monospace;">+${Number(f.annual_return_pct).toFixed(1)}%</div>
                            </div>
                            <div style="grid-column: 1 / -1; display: flex; justify-content: space-between; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 6px; margin-top: 2px;">
                                <span style="font-size: 11px; color: #cbd5e1;"><i class="fa-solid fa-building" style="margin-left: 4px; color: var(--text-muted);"></i> ${f.manager}</span>
                                <span style="font-size: 11px; color: #94a3b8;"><i class="fa-solid fa-clock" style="margin-left: 4px;"></i> ${f.liquidity_ar || f.liquidity}</span>
                            </div>
                        </div>
                    </div>

                    <div style="display: flex; gap: 8px; align-items: center; margin-top: 8px;">
                        <button class="btn btn-secondary btn-sm" style="flex: 1; font-size: 12px; padding: 7px 10px;" onclick="openFundModal('${f.fund_id}')">
                            <i class="fa-solid fa-circle-info"></i> التفاصيل
                        </button>
                        <button class="btn btn-success btn-sm" style="flex: 1; font-size: 12px; padding: 7px 10px;" onclick="openSizerForFund('${f.ticker}', '${f.name_ar.replace(/'/g, "\\\\'")}', ${f.nav_egp})">
                            <i class="fa-solid fa-calculator"></i> استثمار
                        </button>
                    </div>
                </div>
                `;
            });

            container.innerHTML = html;
        }

        function openFundModal(fundId) {
            const fund = allFundsData.find(f => f.fund_id === fundId || f.ticker === fundId);
            if (!fund) return;
            activeModalFund = fund;

            const iconEl = document.getElementById('modal-fund-icon');
            const titleEl = document.getElementById('modal-fund-title');
            const contentEl = document.getElementById('modal-fund-content');

            if (iconEl) iconEl.innerText = fund.category === 'GOLD' ? '🥇' : (fund.category === 'MONEY_MARKET' ? '💵' : '📈');
            if (titleEl) titleEl.innerText = fund.name_ar;

            if (contentEl) {
                const sharia = fund.sharia_compliant ? '✅ نعم، متوافق مع الضوابط الشرعية' : '❌ صندوق تقليدي';
                contentEl.innerHTML = `
                    <div style="margin-bottom: 12px; font-weight: 700; color: #93c5fd; font-family: 'JetBrains Mono', monospace;">${fund.name_en} (${fund.ticker})</div>
                    <div style="background: rgba(0,0,0,0.3); padding: 12px; border-radius: 8px; margin-bottom: 14px; border: 1px solid rgba(255,255,255,0.06);">
                        <p style="margin: 0; color: #e2e8f0; line-height: 1.6;">${fund.description_ar}</p>
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                        <div style="background: rgba(255,255,255,0.03); padding: 10px; border-radius: 6px;">
                            <div style="font-size: 11px; color: var(--text-muted);">سعر الوثيقة الحالي (NAV):</div>
                            <div style="font-size: 16px; font-weight: 800; color: #fff;">${fund.nav_egp} ج.م</div>
                        </div>
                        <div style="background: rgba(255,255,255,0.03); padding: 10px; border-radius: 6px;">
                            <div style="font-size: 11px; color: var(--text-muted);">العائد السنوي المتوقع:</div>
                            <div style="font-size: 16px; font-weight: 800; color: #34d399;">+${fund.annual_return_pct}%</div>
                        </div>
                        <div style="background: rgba(255,255,255,0.03); padding: 10px; border-radius: 6px;">
                            <div style="font-size: 11px; color: var(--text-muted);">شركة الإدارة:</div>
                            <div style="font-size: 13px; font-weight: 700; color: #cbd5e1;">${fund.manager}</div>
                        </div>
                        <div style="background: rgba(255,255,255,0.03); padding: 10px; border-radius: 6px;">
                            <div style="font-size: 11px; color: var(--text-muted);">البنك / المؤسسة الراعية:</div>
                            <div style="font-size: 13px; font-weight: 700; color: #cbd5e1;">${fund.sponsor}</div>
                        </div>
                        <div style="background: rgba(255,255,255,0.03); padding: 10px; border-radius: 6px;">
                            <div style="font-size: 11px; color: var(--text-muted);">شروط السيولة والاسترداد:</div>
                            <div style="font-size: 13px; font-weight: 700; color: #cbd5e1;">${fund.liquidity_ar || fund.liquidity}</div>
                        </div>
                        <div style="background: rgba(255,255,255,0.03); padding: 10px; border-radius: 6px;">
                            <div style="font-size: 11px; color: var(--text-muted);">التوافق مع الشريعة:</div>
                            <div style="font-size: 13px; font-weight: 700; color: #cbd5e1;">${sharia}</div>
                        </div>
                        <div style="background: rgba(255,255,255,0.03); padding: 10px; border-radius: 6px;">
                            <div style="font-size: 11px; color: var(--text-muted);">مصاريف الإدارة السنوية:</div>
                            <div style="font-size: 13px; font-weight: 700; color: #cbd5e1;">${fund.expense_ratio_pct}% سنوياً</div>
                        </div>
                        <div style="background: rgba(255,255,255,0.03); padding: 10px; border-radius: 6px;">
                            <div style="font-size: 11px; color: var(--text-muted);">الحد الأدنى للاستثمار:</div>
                            <div style="font-size: 13px; font-weight: 700; color: #cbd5e1;">وثيقة واحدة (${fund.nav_egp} ج.م)</div>
                        </div>
                    </div>
                `;
            }

            const modal = document.getElementById('fund-detail-modal');
            if (modal) modal.classList.add('open');
        }

        function closeFundModal() {
            const modal = document.getElementById('fund-detail-modal');
            if (modal) modal.classList.remove('open');
            activeModalFund = null;
        }

        function openSizerForFund(ticker, name, nav) {
            closeFundModal();
            openPortfolioSizer();
            showToast(`💡 يمكنك تخصيص جزء من ميزانيتك لصندوق ${name} (${ticker}) بسعر وثيقة ${nav} ج.م كأداة تحوط منخفضة المخاطر.`, "info");
        }

        function investInModalFund() {
            if (!activeModalFund) return;
            openSizerForFund(activeModalFund.ticker, activeModalFund.name_ar, activeModalFund.nav_egp);
        }
"""

if "THNDR MUTUAL FUNDS JAVASCRIPT ENGINE" not in content:
    init_marker = "        function initStocksDatalist() {"
    if init_marker in content:
        content = content.replace(init_marker, funds_js_logic + "\n" + init_marker, 1)
        print("[8] Injected Mutual Funds JavaScript engine.")

# 8. Update initStocksDatalist to fetch all 270 stocks from /api/stocks
datalist_old = """        function initStocksDatalist() {
            const datalist = document.getElementById('egx-all-stocks-datalist');
            if (!datalist) return;
            if (cachedRankings && cachedRankings.length > 0) {
                datalist.innerHTML = cachedRankings.map(s => {
                    const name = s.name_ar || s.company_name || s.ticker;
                    return `<option value="${s.ticker}">${name} (${s.ticker})</option>`;
                }).join('');
            }
        }"""

datalist_new = """        async function initStocksDatalist() {
            const datalist = document.getElementById('egx-all-stocks-datalist');
            if (!datalist) return;
            try {
                const res = await fetch('/api/stocks');
                if (res.ok) {
                    const allStocks = await res.json();
                    datalist.innerHTML = allStocks.map(s => {
                        const name = s.name_ar || s.name || s.ticker;
                        return `<option value="${s.ticker}">${name} (${s.ticker})</option>`;
                    }).join('');
                    return;
                }
            } catch (e) {
                console.warn("Failed fetching /api/stocks, fallback to cached rankings", e);
            }
            if (cachedRankings && cachedRankings.length > 0) {
                datalist.innerHTML = cachedRankings.map(s => {
                    const name = s.name_ar || s.company_name || s.ticker;
                    return `<option value="${s.ticker}">${name} (${s.ticker})</option>`;
                }).join('');
            }
        }"""

if datalist_old in content:
    content = content.replace(datalist_old, datalist_new, 1)
    print("[9] Upgraded initStocksDatalist to pull complete 270 stocks catalog.")

# Save to dashboard/templates/index.html
with open(SRC_HTML, "w", encoding="utf-8") as f:
    f.write(content)
print(f"[SUCCESS] Updated {SRC_HTML}")

# Sync to dashboard/index.html and templates/index.html
for copy_path in [os.path.join(WORKSPACE, "dashboard", "index.html"), os.path.join(WORKSPACE, "templates", "index.html")]:
    with open(copy_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[SYNC] Copied to {copy_path}")
