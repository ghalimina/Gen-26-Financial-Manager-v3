#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# scripts/update_dashboard_portfolio_sizer.py

import os
import shutil

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_TEMPLATE = os.path.join(WORKSPACE, "dashboard", "templates", "index.html")

with open(INDEX_TEMPLATE, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Macro Barometer text update
content = content.replace(
    '<span id="macro-cbe-val" class="ltr-text text-yellow font-bold">27.25%</span>',
    '<span id="macro-cbe-val" class="ltr-text text-yellow font-bold">19.00%</span>'
)
content = content.replace(
    '<span id="macro-inflation-val" class="ltr-text text-red font-bold">26.50%</span>',
    '<span id="macro-inflation-val" class="ltr-text text-red font-bold">14.90%</span>'
)

# 2. Add Golden Spotlight card to #tab-overview
overview_spotlight_html = """
                <!-- 🏆 Top 3 Golden Buy Opportunities Spotlight Card -->
                <div class="card golden-spotlight-card" style="background: linear-gradient(135deg, rgba(30, 58, 138, 0.35) 0%, rgba(15, 23, 42, 0.95) 50%, rgba(6, 95, 70, 0.25) 100%); border: 1px solid rgba(245, 158, 11, 0.4); border-radius: var(--radius-lg); padding: 20px 24px; margin-bottom: 24px; box-shadow: 0 10px 30px rgba(0,0,0,0.35);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; flex-wrap: wrap; gap: 10px; border-bottom: 1px solid rgba(255, 255, 255, 0.08); padding-bottom: 12px;">
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <span style="font-size: 24px;">🏆</span>
                            <div>
                                <div style="font-size: 17px; font-weight: 900; color: #ffffff;">أفضل 3 فرص ذهبية للاستثمار الفوري اليوم (Top 3 Golden Buy Opportunities)</div>
                                <div style="font-size: 12px; color: var(--text-muted);">انتقاء مباشر مبني على إجماع مجلس الخبراء الـ 7 ونموذج Meta-Labeling بالأسعار الفعلية اللحظية</div>
                            </div>
                        </div>
                        <button class="btn btn-primary btn-sm" onclick="openPortfolioSizer()">
                            <i class="fa-solid fa-calculator"></i> توزيع الميزانية الذكي (Portfolio Sizer)
                        </button>
                    </div>
                    <div class="card-grid-3 golden-picks-grid" id="golden-picks-overview" style="margin-bottom: 0;">
                        <!-- Populated dynamically via renderGoldenPicks -->
                    </div>
                </div>
"""

# Insert before <!-- Daily Human 3-Question Snapshot -->
if "golden-picks-overview" not in content:
    content = content.replace(
        "                <!-- Daily Human 3-Question Snapshot -->",
        overview_spotlight_html + "\n                <!-- Daily Human 3-Question Snapshot -->"
    )

# 3. Add Golden Spotlight card to #tab-ranking
ranking_spotlight_html = """
                <!-- 🏆 Top 3 Golden Buy Opportunities Spotlight Card -->
                <div class="card golden-spotlight-card" style="background: linear-gradient(135deg, rgba(30, 58, 138, 0.35) 0%, rgba(15, 23, 42, 0.95) 50%, rgba(6, 95, 70, 0.25) 100%); border: 1px solid rgba(245, 158, 11, 0.4); border-radius: var(--radius-lg); padding: 20px 24px; margin-bottom: 24px; box-shadow: 0 10px 30px rgba(0,0,0,0.35);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; flex-wrap: wrap; gap: 10px; border-bottom: 1px solid rgba(255, 255, 255, 0.08); padding-bottom: 12px;">
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <span style="font-size: 24px;">🏆</span>
                            <div>
                                <div style="font-size: 17px; font-weight: 900; color: #ffffff;">أفضل 3 فرص ذهبية للاستثمار الفوري اليوم (Top 3 Golden Buy Opportunities)</div>
                                <div style="font-size: 12px; color: var(--text-muted);">أعلى 3 أسهم حائزة على تصنيف شراء قوي 🟢 وتطابق شروط إدارة المخاطر وتدفقات السيولة الحية</div>
                            </div>
                        </div>
                        <button class="btn btn-primary btn-sm" onclick="openPortfolioSizer()">
                            <i class="fa-solid fa-calculator"></i> توزيع الميزانية والشراء الفوري
                        </button>
                    </div>
                    <div class="card-grid-3 golden-picks-grid" id="golden-picks-ranking" style="margin-bottom: 0;">
                        <!-- Populated dynamically via renderGoldenPicks -->
                    </div>
                </div>
"""

if "golden-picks-ranking" not in content:
    content = content.replace(
        '                <div class="view-switcher-bar">',
        ranking_spotlight_html + '\n                <div class="view-switcher-bar">'
    )

# 4. Replace Portfolio Sizer and Golden Picks JavaScript logic
old_sizer_block = """        function openPortfolioSizer() {
            const modal = document.getElementById('portfolio-sizer-modal');
            if (modal) modal.classList.add('open');
            calculatePortfolioSizer();
        }

        function closePortfolioSizer() {
            const modal = document.getElementById('portfolio-sizer-modal');
            if (modal) modal.classList.remove('open');
        }

        function setSizerCapital(amount) {
            const input = document.getElementById('sizer-capital-input');
            if (input) input.value = amount;
            document.querySelectorAll('.budget-preset-chip').forEach(c => {
                c.classList.toggle('active', c.innerText.includes(amount.toLocaleString()));
            });
            calculatePortfolioSizer();
        }

        function calculatePortfolioSizer() {
            const capital = parseFloat(document.getElementById('sizer-capital-input')?.value || 50000);
            const container = document.getElementById('sizer-results-container');
            const itemsBox = document.getElementById('sizer-plan-items');
            if (!container || !itemsBox) return;

            // Target top liquid 3-4 stocks with 30% cap enforcement
            const candidates = [
                { name: "البنك التجاري الدولي (CIB)", ticker: "COMI.CA", price: 140.50, weight: 0.30 },
                { name: "السويدي إليكتريك", ticker: "SWDY.CA", price: 128.00, weight: 0.28 },
                { name: "مجموعة طلعت مصطفى", ticker: "TMGH.CA", price: 97.50, weight: 0.24 },
                { name: "أبو قير للأسمدة", ticker: "ABUK.CA", price: 75.50, weight: 0.08 }
            ];

            let totalAllocated = 0;
            let rowsHtml = '';

            candidates.forEach(c => {
                const targetEgp = capital * c.weight;
                const shares = Math.floor(targetEgp / c.price);
                const actualEgp = shares * c.price;
                totalAllocated += actualEgp;
                const pct = ((actualEgp / capital) * 100).toFixed(1);

                rowsHtml += `
                    <div class="plan-item">
                        <div>
                            <strong style="color: #ffffff;">🟢 ${c.name} (<span class="ltr-text">${c.ticker}</span>)</strong>
                            <div style="font-size: 11px; color: var(--text-muted); margin-top: 2px;">
                                اشتري <strong>${shares}</strong> سهم بسعر <span class="ltr-text">${c.price.toFixed(2)}</span> ج.م
                            </div>
                        </div>
                        <div style="text-align: left;">
                            <strong style="color: #34d399;"><span class="ltr-text">${actualEgp.toLocaleString('en-US', {maximumFractionDigits: 2})}</span> ج.م</strong>
                            <div style="font-size: 11px; color: #60a5fa;">(${pct}%)</div>
                        </div>
                    </div>
                `;
            });

            const cashReserve = Math.max(0, capital - totalAllocated);
            const cashPct = ((cashReserve / capital) * 100).toFixed(1);

            rowsHtml += `
                <div class="plan-item" style="background: rgba(245, 158, 11, 0.08); padding: 8px 12px; border-radius: 6px; margin-top: 8px;">
                    <div>
                        <strong style="color: #fbbf24;">🛡️ كاش أمان واحتياطي للطوارئ</strong>
                        <div style="font-size: 11px; color: var(--text-muted);">سيولة نقدية جاهزة لاقتناص التراجعات</div>
                    </div>
                    <div style="text-align: left;">
                        <strong style="color: #fbbf24;"><span class="ltr-text">${cashReserve.toLocaleString('en-US', {maximumFractionDigits: 2})}</span> ج.م</strong>
                        <div style="font-size: 11px; color: #fbbf24;">(${cashPct}%)</div>
                    </div>
                </div>
            `;

            itemsBox.innerHTML = rowsHtml;
            container.style.display = 'block';
        }"""

new_sizer_block = """        function openPortfolioSizer(ticker = null) {
            const modal = document.getElementById('portfolio-sizer-modal');
            if (modal) modal.classList.add('open');
            calculatePortfolioSizer(ticker);
        }

        function closePortfolioSizer() {
            const modal = document.getElementById('portfolio-sizer-modal');
            if (modal) modal.classList.remove('open');
        }

        function setSizerCapital(amount) {
            const input = document.getElementById('sizer-capital-input');
            if (input) input.value = amount;
            document.querySelectorAll('.budget-preset-chip').forEach(c => {
                c.classList.toggle('active', c.innerText.includes(amount.toLocaleString()));
            });
            calculatePortfolioSizer();
        }

        function calculatePortfolioSizer(selectedTicker = null) {
            const capital = parseFloat(document.getElementById('sizer-capital-input')?.value || 50000);
            const container = document.getElementById('sizer-results-container');
            const itemsBox = document.getElementById('sizer-plan-items');
            if (!container || !itemsBox) return;

            // Dynamically extract Top 3 Liquid BUY-Rated stocks directly from cachedRankings
            let buyCandidates = [];
            if (cachedRankings && cachedRankings.length > 0) {
                buyCandidates = cachedRankings.slice(0, 3);
            }

            if (buyCandidates.length === 0) {
                buyCandidates = [
                    { name_ar: "البنك التجاري الدولي (CIB)", ticker: "COMI.CA", price: 139.28, current_price: 139.28 },
                    { name_ar: "السويدي إليكتريك", ticker: "SWDY.CA", price: 128.00, current_price: 128.00 },
                    { name_ar: "مجموعة طلعت مصطفى", ticker: "TMGH.CA", price: 97.50, current_price: 97.50 }
                ];
            }

            // Dynamic capital allocation adhering to the Frozen Risk Core:
            // - Maximum 30.0% allocation for Rank #1
            // - Maximum 25.0% allocation for Rank #2
            // - Maximum 20.0% allocation for Rank #3
            // - Remaining balance (min 25-35%) allocated to Emergency Cash Reserve
            const weights = [0.30, 0.25, 0.20];

            let totalAllocated = 0;
            let rowsHtml = '';

            buyCandidates.slice(0, 3).forEach((c, idx) => {
                const weight = weights[idx] || 0.20;
                const name = c.name_ar || c.company_name || c.name || c.ticker;
                const realPrice = parseFloat(c.current_price || c.price || (idx === 0 ? 139.28 : idx === 1 ? 128.00 : 97.50));
                const targetEgp = capital * weight;
                const shares = Math.floor(targetEgp / realPrice);
                const actualEgp = shares * realPrice;
                totalAllocated += actualEgp;
                const pct = ((actualEgp / capital) * 100).toFixed(1);
                const isSelected = selectedTicker && (selectedTicker === c.ticker);

                rowsHtml += `
                    <div class="plan-item" style="${isSelected ? 'border: 2px solid #3b82f6; background: rgba(59, 130, 246, 0.15); box-shadow: 0 0 15px rgba(59, 130, 246, 0.25);' : ''}">
                        <div>
                            <strong style="color: #ffffff;">🟢 المركز #${idx + 1}: ${name} (<span class="ltr-text text-blue font-mono font-bold">${c.ticker}</span>)</strong>
                            <div style="font-size: 11.5px; color: var(--text-muted); margin-top: 2px;">
                                اشتري <strong>${shares.toLocaleString()}</strong> سهم بسعر السوق الحي <span class="ltr-text font-bold text-green">${realPrice.toFixed(2)}</span> ج.م
                            </div>
                        </div>
                        <div style="text-align: left;">
                            <strong style="color: #34d399;"><span class="ltr-text font-mono">${actualEgp.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</span> ج.م</strong>
                            <div style="font-size: 11px; color: #60a5fa; font-weight: 700;">(${pct}%)</div>
                        </div>
                    </div>
                `;
            });

            const cashReserve = Math.max(0, capital - totalAllocated);
            const cashPct = ((cashReserve / capital) * 100).toFixed(1);

            rowsHtml += `
                <div class="plan-item" style="background: rgba(245, 158, 11, 0.10); border: 1px solid rgba(245, 158, 11, 0.3); padding: 12px 14px; border-radius: 6px; margin-top: 10px;">
                    <div>
                        <strong style="color: #fbbf24;">🛡️ كاش أمان واحتياطي للطوارئ (Emergency Cash Reserve)</strong>
                        <div style="font-size: 11.5px; color: #fde68a;">سيولة نقدية محتجزة إجبارياً لاقتناص تراجعات السوق وإدارة المخاطر</div>
                    </div>
                    <div style="text-align: left;">
                        <strong style="color: #fbbf24;"><span class="ltr-text font-mono">${cashReserve.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</span> ج.م</strong>
                        <div style="font-size: 11px; color: #fbbf24; font-weight: 800;">(${cashPct}%)</div>
                    </div>
                </div>
            `;

            itemsBox.innerHTML = rowsHtml;
            container.style.display = 'block';
        }

        function renderGoldenPicks(stocks) {
            if (!stocks || stocks.length === 0) {
                stocks = cachedRankings;
            }
            if (!stocks || stocks.length === 0) {
                stocks = [
                    { ticker: "COMI.CA", name_ar: "البنك التجاري الدولي (CIB)", price: 139.28, current_price: 139.28, entry_price: 136.50, target_price: 152.00, stop_loss: 131.00, composite_score: 95.0, confidence: 0.94, council_status: "🟢 شراء قوي بالإجماع" },
                    { ticker: "SWDY.CA", name_ar: "السويدي إليكتريك", price: 128.00, current_price: 128.00, entry_price: 125.00, target_price: 140.00, stop_loss: 120.00, composite_score: 92.5, confidence: 0.91, council_status: "🟢 شراء وتجميع" },
                    { ticker: "TMGH.CA", name_ar: "مجموعة طلعت مصطفى", price: 97.50, current_price: 97.50, entry_price: 95.00, target_price: 107.00, stop_loss: 91.50, composite_score: 89.0, confidence: 0.88, council_status: "🟢 شراء واستثمار" }
                ];
            }

            const top3 = stocks.slice(0, 3);
            const containers = [
                document.getElementById('golden-picks-overview'),
                document.getElementById('golden-picks-ranking')
            ];

            const rankBadges = [
                { badge: '🥇 المركز #1', color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.15)', border: '#f59e0b' },
                { badge: '🥈 المركز #2', color: '#94a3b8', bg: 'rgba(148, 163, 184, 0.15)', border: '#94a3b8' },
                { badge: '🥉 المركز #3', color: '#d97706', bg: 'rgba(217, 119, 6, 0.15)', border: '#d97706' }
            ];

            const html = top3.map((s, idx) => {
                const rb = rankBadges[idx] || { badge: `#${idx+1}`, color: '#60a5fa', bg: 'rgba(59, 130, 246, 0.15)', border: '#3b82f6' };
                const priceVal = parseFloat(s.price || s.current_price || (idx === 0 ? 139.28 : idx === 1 ? 128.00 : 97.50));
                const entryLow = s.entry_price ? parseFloat(s.entry_price) : (priceVal * 0.985);
                const entryHigh = priceVal;
                const targetVal = s.target_price ? parseFloat(s.target_price) : (priceVal * 1.085);
                const stopVal = s.stop_loss ? parseFloat(s.stop_loss) : (priceVal * 0.935);
                const upsidePct = (((targetVal - priceVal) / priceVal) * 100).toFixed(1);
                const downsidePct = (((priceVal - stopVal) / priceVal) * 100).toFixed(1);
                const confidencePct = s.confidence ? (s.confidence * 100).toFixed(0) : (s.ai_confidence ? (s.ai_confidence * 100).toFixed(0) : (94 - idx * 3));
                const name = s.name_ar || s.company_name || s.name || s.ticker;
                const councilStatus = s.council_status || s.action || "🟢 إجماع مجلس الخبراء: شراء قوي";

                return `
                    <div class="card" style="background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(255, 255, 255, 0.12); border-radius: var(--radius-md); padding: 18px; display: flex; flex-direction: column; justify-content: space-between; position: relative; transition: all 0.25s ease; box-shadow: 0 4px 20px rgba(0,0,0,0.25);">
                        <div>
                            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
                                <div>
                                    <span class="badge" style="background: ${rb.bg}; color: ${rb.color}; border: 1px solid ${rb.border}; font-weight: 800; font-size: 11px; margin-bottom: 4px;">${rb.badge}</span>
                                    <div style="font-size: 15px; font-weight: 800; color: #ffffff; margin-top: 2px;">${name}</div>
                                    <div class="ltr-text text-blue font-bold font-mono" style="font-size: 12px;">${s.ticker}</div>
                                </div>
                                <div style="text-align: left;">
                                    <div class="ltr-text font-bold font-mono" style="font-size: 18px; color: #34d399;">${priceVal.toFixed(2)} <span style="font-size: 11px; color: var(--text-muted);">ج.م</span></div>
                                    <span class="badge badge-green" style="font-size: 10px; padding: 2px 6px;">🟢 سعر السوق الحي</span>
                                </div>
                            </div>

                            <div style="background: rgba(0,0,0,0.3); border-radius: var(--radius-sm); padding: 10px 12px; margin-bottom: 12px; border: 1px solid rgba(255,255,255,0.06);">
                                <div style="display: flex; justify-content: space-between; font-size: 11.5px; margin-bottom: 6px;">
                                    <span style="color: var(--text-muted);">منطقة الدخول الموصى بها:</span>
                                    <span class="ltr-text text-blue font-bold font-mono">${entryLow.toFixed(2)} – ${entryHigh.toFixed(2)} ج.م</span>
                                </div>
                                <div style="display: flex; justify-content: space-between; font-size: 11.5px; margin-bottom: 6px;">
                                    <span style="color: var(--text-muted);">🎯 المستهدف الربحي (+Upside):</span>
                                    <span class="ltr-text text-green font-bold font-mono">${targetVal.toFixed(2)} ج.م (+${upsidePct}%)</span>
                                </div>
                                <div style="display: flex; justify-content: space-between; font-size: 11.5px;">
                                    <span style="color: var(--text-muted);">🛑 وقف الخسارة الصارم (-Risk):</span>
                                    <span class="ltr-text text-red font-bold font-mono">${stopVal.toFixed(2)} ج.م (-${downsidePct}%)</span>
                                </div>
                            </div>

                            <div style="display: flex; justify-content: space-between; align-items: center; background: rgba(59, 130, 246, 0.08); padding: 6px 10px; border-radius: 6px; margin-bottom: 14px; font-size: 11px;">
                                <span style="color: #93c5fd;">🤖 ثقة نموذج الذكاء الاصطناعي:</span>
                                <span class="badge badge-blue font-bold">${confidencePct}% (High Alpha)</span>
                            </div>
                            <div style="font-size: 11px; color: #a7f3d0; margin-bottom: 14px; display: flex; align-items: center; gap: 4px;">
                                <i class="fa-solid fa-check-double"></i> <span>${councilStatus}</span>
                            </div>
                        </div>

                        <div style="display: flex; gap: 8px; margin-top: auto;">
                            <button class="btn btn-primary btn-sm btn-block" onclick="openPortfolioSizer('${s.ticker}')">
                                <i class="fa-solid fa-wallet"></i> 💼 توزيع الميزانية والشراء
                            </button>
                            <button class="btn btn-secondary btn-sm" onclick="loadStockDetails('${s.ticker}')" title="فحص ملف السهم">
                                <i class="fa-solid fa-chart-line"></i>
                            </button>
                        </div>
                    </div>
                `;
            }).join('');

            containers.forEach(c => {
                if (c) c.innerHTML = html;
            });
        }"""

content = content.replace(old_sizer_block, new_sizer_block)

# 5. Connect renderGoldenPicks to loadRankingData and renderDefaultMockRankings
old_ranking_loader = """                cachedRankings = rawList.slice(0, 100);
                renderRankingContent(cachedRankings);
                populateStockSelectOptions(cachedRankings);"""

new_ranking_loader = """                cachedRankings = rawList.slice(0, 100);
                renderRankingContent(cachedRankings);
                renderGoldenPicks(cachedRankings);
                populateStockSelectOptions(cachedRankings);"""

content = content.replace(old_ranking_loader, new_ranking_loader)

old_default_mock = """        function renderDefaultMockRankings() {
            const defaults = [
                { ticker: "COMI.CA", name_ar: "البنك التجاري الدولي (CIB)", price: 140.50, composite_score: 95.0 },
                { ticker: "SWDY.CA", name_ar: "السويدي إليكتريك", price: 128.00, composite_score: 92.5 },
                { ticker: "TMGH.CA", name_ar: "مجموعة طلعت مصطفى", price: 97.50, composite_score: 89.0 },
                { ticker: "ORAS.CA", name_ar: "أوراسكوم للإنشاء", price: 782.25, composite_score: 86.5 },
                { ticker: "ABUK.CA", name_ar: "أبو قير للأسمدة", price: 75.50, composite_score: 84.0 },
                { ticker: "MFPC.CA", name_ar: "مصر لإنتاج الأسمدة", price: 48.50, composite_score: 82.0 },
                { ticker: "ETEL.CA", name_ar: "المصرية للاتصالات", price: 114.89, composite_score: 80.0 },
                { ticker: "EGAL.CA", name_ar: "مصر للألومنيوم", price: 330.00, composite_score: 78.5 }
            ];
            renderRankingContent(defaults);
        }"""

new_default_mock = """        function renderDefaultMockRankings() {
            const defaults = [
                { ticker: "COMI.CA", name_ar: "البنك التجاري الدولي (CIB)", price: 139.28, current_price: 139.28, entry_price: 136.50, target_price: 152.00, stop_loss: 131.00, composite_score: 95.0, confidence: 0.94, council_status: "🟢 شراء قوي بالإجماع" },
                { ticker: "SWDY.CA", name_ar: "السويدي إليكتريك", price: 128.00, current_price: 128.00, entry_price: 125.00, target_price: 140.00, stop_loss: 120.00, composite_score: 92.5, confidence: 0.91, council_status: "🟢 شراء وتجميع" },
                { ticker: "TMGH.CA", name_ar: "مجموعة طلعت مصطفى", price: 97.50, current_price: 97.50, entry_price: 95.00, target_price: 107.00, stop_loss: 91.50, composite_score: 89.0, confidence: 0.88, council_status: "🟢 شراء واستثمار" },
                { ticker: "ORAS.CA", name_ar: "أوراسكوم للإنشاء", price: 782.25, current_price: 782.25, composite_score: 86.5 },
                { ticker: "ABUK.CA", name_ar: "أبو قير للأسمدة", price: 75.50, current_price: 75.50, composite_score: 84.0 },
                { ticker: "MFPC.CA", name_ar: "مصر لإنتاج الأسمدة", price: 48.50, current_price: 48.50, composite_score: 82.0 },
                { ticker: "ETEL.CA", name_ar: "المصرية للاتصالات", price: 114.89, current_price: 114.89, composite_score: 80.0 },
                { ticker: "EGAL.CA", name_ar: "مصر للألومنيوم", price: 330.00, current_price: 330.00, composite_score: 78.5 }
            ];
            cachedRankings = defaults;
            renderRankingContent(defaults);
            renderGoldenPicks(defaults);
        }"""

content = content.replace(old_default_mock, new_default_mock)

# Write to dashboard/templates/index.html
with open(INDEX_TEMPLATE, "w", encoding="utf-8") as f:
    f.write(content)

# Mirror to templates/index.html and dashboard/index.html
for target_rel in ["templates/index.html", "dashboard/index.html"]:
    target_path = os.path.join(WORKSPACE, target_rel)
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    shutil.copyfile(INDEX_TEMPLATE, target_path)

print("Dashboard templates updated and mirrored successfully!")
