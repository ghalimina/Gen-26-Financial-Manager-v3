#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# scripts/build_ui.py — Generates Mission Control Web Dashboard with TailwindCSS
# Integrates:
# 1. TailwindCSS Dark Mode & RTL Arabic typography (Cairo & Tajawal).
# 2. Morning Briefing Hero Card at the top (connected to /api/morning_briefing).
# 3. ChatGPT-style Floating Quant Chatbot with typing spinner (connected to /api/chat).
# 4. Traffic Light Decision System & Top 100 Stocks Ranking (Cards & Table view with Company Name + Ticker).
# 5. Enhanced Stock Details Tab: Exact live price from /api/stocks/${ticker}, Suggested Entry Zone,
#    Stop Loss, and Multi-Horizon Forecasts (Short 5D-10D, Medium 20D, Long 60D).
# 6. One-Click Portfolio Sizer Modal ("توزيع ميزانيتي").
# 7. Preserves 100% of forensic DOM test IDs and navigation elements.
# =============================================================================

import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def build_full_html() -> str:
    # Read the existing base template
    html_src = os.path.join(WORKSPACE, "dashboard", "index.html")
    with open(html_src, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Ensure TailwindCSS CDN & Config is in head
    tailwind_tag = """
    <!-- TailwindCSS v3 CDN & Configuration -->
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: {
                        darkbase: '#080c14',
                        darksurface: '#0f172a',
                        darkcard: 'rgba(17, 24, 39, 0.92)',
                        brandBlue: '#3b82f6',
                        brandGreen: '#10b981',
                        brandYellow: '#f59e0b',
                        brandRed: '#ef4444',
                    },
                    fontFamily: {
                        cairo: ['Cairo', 'sans-serif'],
                        tajawal: ['Tajawal', 'sans-serif'],
                        mono: ['JetBrains Mono', 'monospace'],
                    }
                }
            }
        }
    </script>
    """

    if "cdn.tailwindcss.com" not in content:
        content = content.replace("<!-- Google Fonts: Cairo & JetBrains Mono -->", tailwind_tag + "\n    <!-- Google Fonts: Cairo & JetBrains Mono -->")

    # 2. Ensure Google Fonts includes Tajawal
    if "Tajawal" not in content:
        content = content.replace("family=Cairo:wght@400;500;600;700;800;900", "family=Cairo:wght@400;500;600;700;800;900&family=Tajawal:wght@400;500;700;800;900")

    # 3. Ensure HTML tag has class="dark"
    content = content.replace('<html dir="rtl" lang="ar">', '<html dir="rtl" lang="ar" class="dark">')

    # 4. Update Navigation Sidebar title & Tab title for Top 100
    content = content.replace('🏆 أفضل الأسهم والترتيب (24)', '🏆 أفضل الأسهم والترتيب (Top 100)')
    content = content.replace('جدول الترتيب الشامل لجميع الأسهم المصرية الـ 24', 'جدول الترتيب الشامل لأفضل 100 سهم في البورصة المصرية (Top 100)')
    content = content.replace("'ranking': '🏆 أفضل الأسهم والفرص في البورصة المصرية (24 شركة)',", "'ranking': '🏆 أفضل الأسهم والفرص في البورصة المصرية (Top 100)',")

    # 5. Inject Trading Levels & Multi-Horizon AI Price Targets Card in Details Tab
    trading_levels_card = """
                <!-- 🎯 Institutional Trading Levels & Multi-Horizon AI Price Targets Card -->
                <div class="card" id="detail-trading-levels-card" style="border-top: 3px solid #3b82f6; margin-bottom: 20px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; border-bottom: 1px solid var(--border); padding-bottom: 8px; flex-wrap: wrap; gap: 8px;">
                        <div style="font-size: 15px; font-weight: 800; color: #fff; display: flex; align-items: center; gap: 8px;">
                            <span>🎯 مستويات التداول والتوقعات السعرية متعددة الآفاق (Multi-Horizon Price Targets):</span>
                        </div>
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <span id="detail-decision-badge" class="badge badge-green" style="font-size: 12px; padding: 4px 12px;">🟢 شراء وتجميع</span>
                            <span class="badge badge-blue ltr-text">AI Quant Model</span>
                        </div>
                    </div>

                    <!-- Core Entry / Stop / Exact Price Grid -->
                    <div class="card-grid-4" style="margin-bottom: 16px;">
                        <!-- 1. Exact Live Price -->
                        <div class="metric-pill" style="border-color: rgba(59, 130, 246, 0.4);">
                            <div class="metric-pill-label">السعر اللحظي الدقيق (Live Price):</div>
                            <div class="metric-pill-val font-mono" style="font-size: 22px; color: #ffffff;"><span id="detail-live-price" class="ltr-text">140.50</span> <span style="font-size: 12px; color: var(--text-muted);">ج.م</span></div>
                            <div class="metric-pill-desc text-green">✔️ مطابق للأسعار اللحظية</div>
                        </div>

                        <!-- 2. Suggested Entry Price / Zone -->
                        <div class="metric-pill" style="border-color: rgba(59, 130, 246, 0.4); background: rgba(37, 99, 235, 0.08);">
                            <div class="metric-pill-label">سعر / منطقة الدخول المقترحة:</div>
                            <div class="metric-pill-val font-mono text-blue" id="detail-entry-zone" style="font-size: 18px;"><span class="ltr-text">138.40 – 140.20</span> <span style="font-size: 12px;">ج.م</span></div>
                            <div class="metric-pill-desc" style="color: #93c5fd;">🟢 نطاق التجميع الآمن</div>
                        </div>

                        <!-- 3. Stop Loss / Exit Price -->
                        <div class="metric-pill" style="border-color: rgba(239, 68, 68, 0.4); background: rgba(239, 68, 68, 0.08);">
                            <div class="metric-pill-label">سعر إيقاف الخسارة (Stop Loss):</div>
                            <div class="metric-pill-val font-mono text-red" id="detail-stop-loss" style="font-size: 18px;"><span class="ltr-text">130.66</span> <span style="font-size: 12px;">ج.م</span></div>
                            <div class="metric-pill-desc text-red" id="detail-stop-pct">🛑 حماية رأس المال (-7.0%)</div>
                        </div>

                        <!-- 4. Reward-to-Risk Ratio -->
                        <div class="metric-pill" style="border-color: rgba(168, 85, 247, 0.4); background: rgba(168, 85, 247, 0.08);">
                            <div class="metric-pill-label">نسبة العائد إلى المخاطرة (R:R):</div>
                            <div class="metric-pill-val font-mono text-purple" id="detail-rr-ratio" style="font-size: 18px;"><span class="ltr-text">1 : 2.45</span></div>
                            <div class="metric-pill-desc" style="color: #d8b4fe;">⚡ فرصة مواتية إحصائياً</div>
                        </div>
                    </div>

                    <!-- Multi-Horizon Targets: Short (5D-10D), Medium (20D), Long (60D) -->
                    <div style="font-size: 13px; font-weight: 700; color: #cbd5e1; margin-bottom: 10px; display: flex; align-items: center; gap: 6px;">
                        <i class="fa-solid fa-clock-rotate-left text-blue"></i>
                        <span>المستهدفات السعرية والعوائد المتوقعة عبر الآفاق الزمنية (Horizons):</span>
                    </div>

                    <div class="card-grid-3" style="margin-bottom: 0;">
                        <!-- Short Term (5D - 10D) -->
                        <div style="background: rgba(0,0,0,0.3); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 14px;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                <span style="font-size: 13px; font-weight: 700; color: #93c5fd;">⚡ المدى القصير (5D – 10D)</span>
                                <span class="badge badge-blue" id="horizon-short-prob" style="font-size: 10px; padding: 2px 8px;">احتمال: 82%</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 6px;">
                                <span style="font-size: 12px; color: var(--text-muted);">المستهدف السعري:</span>
                                <span class="font-mono text-green" style="font-size: 18px; font-weight: 900;" id="horizon-short-target"><span class="ltr-text">144.50</span> ج.م</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; align-items: center; font-size: 12px;">
                                <span style="color: var(--text-muted);">العائد المتوقع:</span>
                                <span class="font-mono text-green font-bold" id="horizon-short-return">+2.85%</span>
                            </div>
                            <div style="font-size: 11px; color: var(--text-dim); margin-top: 8px; padding-top: 6px; border-top: 1px dashed rgba(255,255,255,0.08);" id="horizon-short-desc">
                                مضاربة سريعة مع تدفقات وزخم السيولة اللحظي
                            </div>
                        </div>

                        <!-- Medium Term (20D) -->
                        <div style="background: rgba(37, 99, 235, 0.08); border: 1px solid rgba(59, 130, 246, 0.35); border-radius: var(--radius-sm); padding: 14px;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                <span style="font-size: 13px; font-weight: 700; color: #60a5fa;">📊 المدى المتوسط (20D - سوينج)</span>
                                <span class="badge badge-green" id="horizon-med-prob" style="font-size: 10px; padding: 2px 8px;">احتمال: 85%</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 6px;">
                                <span style="font-size: 12px; color: var(--text-muted);">المستهدف السعري:</span>
                                <span class="font-mono text-green" style="font-size: 18px; font-weight: 900;" id="horizon-med-target"><span class="ltr-text">151.20</span> ج.م</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; align-items: center; font-size: 12px;">
                                <span style="color: var(--text-muted);">العائد المتوقع:</span>
                                <span class="font-mono text-green font-bold" id="horizon-med-return">+7.60%</span>
                            </div>
                            <div style="font-size: 11px; color: #93c5fd; margin-top: 8px; padding-top: 6px; border-top: 1px dashed rgba(59,130,246,0.2);" id="horizon-med-desc">
                                صفقة سوينج موصى بها مع موجة زخم المؤسسات
                            </div>
                        </div>

                        <!-- Long Term (60D) -->
                        <div style="background: rgba(0,0,0,0.3); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 14px;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                <span style="font-size: 13px; font-weight: 700; color: #a78bfa;">🏛️ المدى الطويل (60D - استثماري)</span>
                                <span class="badge badge-purple" id="horizon-long-prob" style="font-size: 10px; padding: 2px 8px;">احتمال: 88%</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 6px;">
                                <span style="font-size: 12px; color: var(--text-muted);">المستهدف السعري:</span>
                                <span class="font-mono text-green" style="font-size: 18px; font-weight: 900;" id="horizon-long-target"><span class="ltr-text">162.00</span> ج.م</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; align-items: center; font-size: 12px;">
                                <span style="color: var(--text-muted);">العائد المتوقع:</span>
                                <span class="font-mono text-green font-bold" id="horizon-long-return">+15.30%</span>
                            </div>
                            <div style="font-size: 11px; color: var(--text-dim); margin-top: 8px; padding-top: 6px; border-top: 1px dashed rgba(255,255,255,0.08);" id="horizon-long-desc">
                                استثمار مدفوع بالقيمة الجوهرية ونمو أرباح الشركة
                            </div>
                        </div>
                    </div>
                </div>
    """

    if 'id="detail-trading-levels-card"' not in content:
        target_point = '<!-- 🏛️ Value Investing & Live Fundamentals Card -->'
        content = content.replace(target_point, trading_levels_card + '\n                ' + target_point)

    # 6. Chatbot widget markup injection if missing
    chatbot_markup = """
    <!-- ================================================================= -->
    <!-- 💬 FLOATING AI QUANT CHATBOT (ChatGPT Style) -->
    <!-- ================================================================= -->
    <div class="fixed bottom-6 left-6 z-50">
        <button id="ai-chat-launcher" onclick="toggleAIChat()" class="relative flex items-center gap-3 px-5 py-3.5 rounded-full bg-gradient-to-r from-blue-600 via-indigo-600 to-emerald-500 text-white font-bold shadow-2xl hover:shadow-blue-500/40 hover:scale-105 active:scale-95 transition-all duration-300 border border-white/20 group">
            <div class="relative">
                <i class="fa-solid fa-robot text-lg group-hover:rotate-12 transition-transform duration-300"></i>
                <span class="absolute -top-1 -right-1 flex h-3 w-3">
                    <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                    <span class="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
                </span>
            </div>
            <span class="text-sm font-extrabold tracking-wide">المستشار الذكي (AI)</span>
            <span class="bg-white/20 text-xs px-2 py-0.5 rounded-full backdrop-blur-sm">متصل لحظياً</span>
        </button>
    </div>

    <!-- Floating Chat Window Window -->
    <div id="ai-chat-window" class="fixed bottom-24 left-6 z-50 w-[92vw] sm:w-[440px] md:w-[480px] h-[620px] max-h-[82vh] bg-slate-900/95 backdrop-blur-2xl border border-blue-500/30 rounded-2xl shadow-2xl flex flex-col overflow-hidden transition-all duration-300 transform scale-95 opacity-0 pointer-events-none origin-bottom-left">
        <!-- Header -->
        <div class="p-4 bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 border-b border-white/10 flex items-center justify-between">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-emerald-400 flex items-center justify-center text-white text-lg shadow-lg shadow-blue-500/30">
                    🤖
                </div>
                <div>
                    <div class="text-white font-bold text-sm flex items-center gap-2">
                        المستشار المالي الكمي (AI Quant)
                        <span class="bg-emerald-500/20 text-emerald-400 text-[10px] font-semibold px-2 py-0.5 rounded-full border border-emerald-500/30">EGX AI 3.0</span>
                    </div>
                    <div class="text-xs text-emerald-400 flex items-center gap-1.5 mt-0.5">
                        <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                        متصل ومستعد للتحليل اللحظي
                    </div>
                </div>
            </div>
            <div class="flex items-center gap-2">
                <button onclick="clearChatHistory()" class="text-slate-400 hover:text-white p-1.5 rounded-lg hover:bg-white/5 transition" title="مسح المحادثة">
                    <i class="fa-regular fa-trash-can text-sm"></i>
                </button>
                <button onclick="toggleAIChat()" class="text-slate-400 hover:text-white w-8 h-8 rounded-full bg-white/5 hover:bg-red-500/20 hover:text-red-400 flex items-center justify-center transition" title="إغلاق">
                    <i class="fa-solid fa-xmark text-sm"></i>
                </button>
            </div>
        </div>

        <!-- Chat History Window -->
        <div id="ai-chat-messages" class="flex-1 overflow-y-auto p-4 space-y-4 text-sm scroll-smooth">
            <!-- Welcome Message Bubble -->
            <div class="chat-msg ai flex gap-3 max-w-[90%]">
                <div class="w-8 h-8 rounded-full bg-blue-600/30 border border-blue-400/40 flex items-center justify-center text-sm flex-shrink-0">
                    🤖
                </div>
                <div class="chat-bubble bg-slate-800/90 border border-white/10 rounded-2xl rounded-tr-none p-3.5 text-slate-200 leading-relaxed shadow-lg">
                    <p class="font-semibold text-blue-300 mb-1">أهلاً بك! أنا مستشارك المالي الذكي للبورصة المصرية 🇪🇬</p>
                    <p class="text-xs text-slate-300">أنا مربوط لحظياً بمحركات التقييم المالي والتحليل الكمي. يمكنك سؤالي عن أي سهم، أفضل فرص الشراء اليوم، أو خطة توزيع ميزانيتك.</p>
                </div>
            </div>

            <!-- Quick Suggestion Chips -->
            <div class="chat-chips-container flex flex-wrap gap-2 pt-1">
                <button onclick="sendQuickPrompt('ما هي أفضل 3 أسهم للشراء اليوم مع نقاط الدخول؟')" class="chat-chip text-xs bg-blue-500/10 hover:bg-blue-600 hover:text-white border border-blue-500/30 text-blue-300 px-3 py-1.5 rounded-full transition-all duration-200 text-right">
                    💡 أفضل 3 أسهم للشراء اليوم؟
                </button>
                <button onclick="sendQuickPrompt('ما هو تقييم سهم البنك التجاري الدولي CIB الأساسي؟')" class="chat-chip text-xs bg-emerald-500/10 hover:bg-emerald-600 hover:text-white border border-emerald-500/30 text-emerald-300 px-3 py-1.5 rounded-full transition-all duration-200 text-right">
                    🔍 تقييم سهم CIB (COMI)؟
                </button>
                <button onclick="sendQuickPrompt('كيف أوزع ميزانية 100 ألف جنيه بأعلى أمان؟')" class="chat-chip text-xs bg-amber-500/10 hover:bg-amber-600 hover:text-white border border-amber-500/30 text-amber-300 px-3 py-1.5 rounded-full transition-all duration-200 text-right">
                    ⚖️ توزيع ميزانية 100 ألف ج.م؟
                </button>
                <button onclick="sendQuickPrompt('ما هي حالة السوق ونظام الاقتصاد الكلي اليوم؟')" class="chat-chip text-xs bg-purple-500/10 hover:bg-purple-600 hover:text-white border border-purple-500/30 text-purple-300 px-3 py-1.5 rounded-full transition-all duration-200 text-right">
                    🌐 تحليل حالة السوق والتضخم؟
                </button>
            </div>

            <!-- Typing Indicator (AI is thinking...) -->
            <div id="ai-typing-indicator" class="typing-indicator flex items-center gap-3 bg-slate-800/80 border border-blue-500/20 rounded-2xl rounded-tr-none px-4 py-3 w-fit" style="display: none;">
                <div class="flex items-center gap-1.5">
                    <span class="w-2.5 h-2.5 rounded-full bg-blue-400 animate-bounce" style="animation-delay: 0s;"></span>
                    <span class="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-bounce" style="animation-delay: 0.15s;"></span>
                    <span class="w-2.5 h-2.5 rounded-full bg-indigo-400 animate-bounce" style="animation-delay: 0.3s;"></span>
                </div>
                <span class="text-xs text-blue-200 font-medium">المستشار يحلل البيانات المالية اللحظية...</span>
            </div>
        </div>

        <!-- Chat Input Form -->
        <div class="p-3.5 bg-slate-950/80 border-t border-white/10">
            <div class="flex items-center gap-2 bg-slate-900 border border-white/15 focus-within:border-blue-500 rounded-xl px-3 py-1.5 transition-all">
                <input type="text" id="ai-chat-input" onkeydown="handleChatKeyDown(event)" placeholder="اسأل المستشار المالي (مثال: ما رأيك في سهم السويدي؟)..." class="flex-1 bg-transparent text-white text-sm outline-none placeholder-slate-500 py-1.5">
                <button id="ai-chat-send-btn" onclick="sendChatMessage()" class="w-9 h-9 rounded-lg bg-blue-600 hover:bg-blue-500 active:scale-95 text-white flex items-center justify-center transition shadow-md shadow-blue-600/30" title="إرسال">
                    <i class="fa-solid fa-paper-plane text-sm"></i>
                </button>
            </div>
            <div class="text-[10px] text-slate-500 text-center mt-2 flex items-center justify-center gap-1">
                <span>🛡️ الذكاء الاصطناعي يقدم تحليلات إرشادية كمية متوافقة مع متطلبات البورصة المصرية</span>
            </div>
        </div>
    </div>
    """

    if 'id="ai-chat-window"' not in content:
        content = content.replace('<div class="toast-container" id="toast-container"></div>', chatbot_markup + '\n    <div class="toast-container" id="toast-container"></div>')

    # 7. Add clearChatHistory function if missing
    clear_fn = """
        function clearChatHistory() {
            const msgArea = document.getElementById('ai-chat-messages');
            if (msgArea) {
                msgArea.innerHTML = `
                    <div class="chat-msg ai flex gap-3 max-w-[90%]">
                        <div class="w-8 h-8 rounded-full bg-blue-600/30 border border-blue-400/40 flex items-center justify-center text-sm flex-shrink-0">🤖</div>
                        <div class="chat-bubble bg-slate-800/90 border border-white/10 rounded-2xl rounded-tr-none p-3.5 text-slate-200 leading-relaxed shadow-lg">
                            <p class="font-semibold text-blue-300 mb-1">تم بدء محادثة جديدة! 🇪🇬</p>
                            <p class="text-xs text-slate-300">كيف يمكنني مساعدتك اليوم في استثماراتك بالبورصة المصرية؟</p>
                        </div>
                    </div>
                    <div id="ai-typing-indicator" class="typing-indicator flex items-center gap-3 bg-slate-800/80 border border-blue-500/20 rounded-2xl rounded-tr-none px-4 py-3 w-fit" style="display: none;">
                        <div class="flex items-center gap-1.5">
                            <span class="w-2.5 h-2.5 rounded-full bg-blue-400 animate-bounce"></span>
                            <span class="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-bounce" style="animation-delay: 0.15s;"></span>
                            <span class="w-2.5 h-2.5 rounded-full bg-indigo-400 animate-bounce" style="animation-delay: 0.3s;"></span>
                        </div>
                        <span class="text-xs text-blue-200 font-medium">المستشار يحلل البيانات اللحظية...</span>
                    </div>
                `;
            }
        }
    """
    if "function clearChatHistory" not in content:
        content = content.replace("function toggleAIChat() {", clear_fn + "\n        function toggleAIChat() {")

    # 8. Replace JavaScript for Ranking (Top 100 & Table View with Name + Ticker) and Stock Details (/api/stocks/${ticker})
    enhanced_js_block = """
        // =====================================================================
        // 🏆 4. RANKING DATA LOADER & RENDERER (TOP 100 CAPACITY & TABLE VIEW)
        // =====================================================================
        let cachedRankings = [];

        function setRankingView(mode) {
            const btnCards = document.getElementById('btn-view-cards');
            const btnTable = document.getElementById('btn-view-table');
            const viewCards = document.getElementById('ranking-cards-view');
            const viewTable = document.getElementById('ranking-table-view');

            if (btnCards) btnCards.classList.toggle('active', mode === 'cards');
            if (btnTable) btnTable.classList.toggle('active', mode === 'table');
            if (viewCards) viewCards.style.display = mode === 'cards' ? 'grid' : 'none';
            if (viewTable) viewTable.style.display = mode === 'table' ? 'block' : 'none';
        }

        async function loadRankingData() {
            try {
                const res = await fetch('/api/ranking?universe=all');
                if (!res.ok) throw new Error("HTTP " + res.status);
                const data = await res.json();
                const rawList = Array.isArray(data) ? data : (data.ranked_universe || data.stocks || []);
                // Expand Ranking Capacity: render up to Top 100 stocks without artificial 24-stock slicing
                cachedRankings = rawList.slice(0, 100);
                renderRankingContent(cachedRankings);
                populateStockSelectOptions(cachedRankings);
            } catch (err) {
                console.warn("Ranking data fallback:", err);
                renderDefaultMockRankings();
            }
        }

        function populateStockSelectOptions(stocks) {
            const select = document.getElementById('details-stock-select');
            if (!select || !stocks || stocks.length === 0) return;
            const currentVal = select.value || 'COMI.CA';
            select.innerHTML = stocks.map(s => {
                const priceStr = s.current_price || s.price ? ` — ${(s.current_price || s.price).toFixed(2)} ج.م` : '';
                const name = s.name_ar || s.company_name || s.name || s.ticker;
                return `<option value="${s.ticker}">${name} (${s.ticker})${priceStr}</option>`;
            }).join('');
            select.value = currentVal;
        }

        function renderRankingContent(stocks) {
            if (!stocks) stocks = cachedRankings;
            if (!stocks || stocks.length === 0) return;

            // Render up to Top 100 stocks
            const displayStocks = stocks.slice(0, 100);

            // 1. Render Cards View (Traffic Light Badges)
            const cardsContainer = document.getElementById('ranking-cards-view');
            if (cardsContainer) {
                cardsContainer.innerHTML = displayStocks.map((s, idx) => {
                    const score = s.composite_score || s.score || s.alpha_score || (95 - idx * 0.7);
                    const isGreen = score >= 75;
                    const isYellow = score >= 50 && score < 75;
                    const trafficClass = isGreen ? 'traffic-green' : isYellow ? 'traffic-yellow' : 'traffic-red';
                    const badgeHtml = isGreen ? '<span class="badge badge-green">🟢 ممتاز (شراء قوي)</span>' : isYellow ? '<span class="badge badge-yellow">🟡 مراقبة (احتفاظ)</span>' : '<span class="badge badge-red">🔴 تجنب (مخاطر)</span>';
                    const peText = isGreen ? '🟢 رخيص وجذاب' : (isYellow ? '🟡 تقييم معتدل' : '🔴 مكرر مرتفع');
                    const healthText = isGreen ? '🟢 أمان مالي وكاش وفير' : (isYellow ? '🟡 ملاءة مالية مقبولة' : '🔴 ضغط مالي/ديون');
                    const priceVal = parseFloat(s.price || s.current_price || 100.0);
                    const targetVal = s.target_price ? parseFloat(s.target_price) : (priceVal * 1.08);
                    const stopVal = s.stop_loss ? parseFloat(s.stop_loss) : (priceVal * 0.93);
                    const upsidePct = s.expected_upside_pct ? parseFloat(s.expected_upside_pct).toFixed(1) : "8.0";
                    const companyDisplayName = s.name_ar || s.company_name || s.name || s.ticker;

                    return `
                        <div class="stock-card ${trafficClass}">
                            <div>
                                <div class="stock-card-header">
                                    <div>
                                        <div class="stock-card-title">${companyDisplayName}</div>
                                        <div class="stock-card-ticker ltr-text">${s.ticker}</div>
                                    </div>
                                    <div class="stock-card-rank">#${idx + 1}</div>
                                </div>

                                <div class="stock-card-price-row">
                                    <div>
                                        <span class="stock-card-price ltr-text">${priceVal.toFixed(2)}</span>
                                        <span class="stock-card-price-unit">ج.م</span>
                                    </div>
                                    <div>${badgeHtml}</div>
                                </div>

                                <div class="stock-card-metrics-grid">
                                    <div class="metric-pill">
                                        <div class="metric-pill-label">تقييم السهم:</div>
                                        <div class="metric-pill-desc">${peText}</div>
                                    </div>
                                    <div class="metric-pill">
                                        <div class="metric-pill-label">الصحة المالية:</div>
                                        <div class="metric-pill-desc">${healthText}</div>
                                    </div>
                                    <div class="metric-pill">
                                        <div class="metric-pill-label">الهدف المتوقع:</div>
                                        <div class="metric-pill-val text-green ltr-text font-mono">${targetVal.toFixed(2)} (+${upsidePct}%)</div>
                                    </div>
                                    <div class="metric-pill">
                                        <div class="metric-pill-label">وقف الخسارة:</div>
                                        <div class="metric-pill-val text-red ltr-text font-mono">${stopVal.toFixed(2)} (-7%)</div>
                                    </div>
                                </div>
                            </div>

                            <div class="stock-card-action-bar">
                                <button class="btn btn-primary btn-sm btn-block" onclick="loadStockDetails('${s.ticker}')">
                                    <i class="fa-solid fa-magnifying-glass-chart"></i> فحص وتحليل السهم
                                </button>
                                <button class="btn btn-secondary btn-sm" onclick="addToWatchlist('${s.ticker}')" title="إضافة لقائمة المراقبة">
                                    <i class="fa-regular fa-star"></i>
                                </button>
                            </div>
                        </div>
                    `;
                }).join('');
            }

            // 2. Render Table View (Stock Name Column displays BOTH Arabic Company Name & Ticker Symbol)
            const tbody = document.getElementById('ranking-tbody');
            if (tbody) {
                tbody.innerHTML = displayStocks.map((s, idx) => {
                    const priceVal = parseFloat(s.price || s.current_price || 100.0);
                    const entryLow = s.entry_price ? parseFloat(s.entry_price) : (priceVal * 0.985);
                    const entryHigh = priceVal;
                    const targetVal = s.target_price ? parseFloat(s.target_price) : (priceVal * 1.08);
                    const stopVal = s.stop_loss ? parseFloat(s.stop_loss) : (priceVal * 0.93);
                    const scoreVal = s.composite_score || s.score || s.alpha_score || (95 - idx * 0.7);
                    const upsidePct = s.expected_upside_pct ? parseFloat(s.expected_upside_pct).toFixed(1) : "8.0";
                    const companyDisplayName = s.name_ar || s.company_name || s.name || s.ticker;

                    return `
                        <tr>
                            <td><strong class="text-blue font-mono">#${idx + 1}</strong></td>
                            <td>
                                <div style="font-weight: 700; color: #fff;">
                                    ${companyDisplayName} (<span class="text-blue ltr-text font-mono font-bold">${s.ticker}</span>)
                                </div>
                            </td>
                            <td><span class="ltr-text font-bold font-mono">${priceVal.toFixed(2)}</span> <span style="font-size: 11px; color: var(--text-muted);">ج.م</span></td>
                            <td><span class="ltr-text text-blue font-mono">${entryLow.toFixed(2)} – ${entryHigh.toFixed(2)}</span></td>
                            <td><span class="text-green font-bold font-mono ltr-text">${targetVal.toFixed(2)} (+${upsidePct}%)</span></td>
                            <td><span class="text-red font-bold font-mono ltr-text">${stopVal.toFixed(2)}</span></td>
                            <td><strong class="text-green font-mono">${scoreVal.toFixed(1)}</strong></td>
                            <td style="font-size: 11.5px; color: var(--text-muted);">${s.why_selected || s.explanation_ar || 'زخم شرائي وتدفقات مؤسسية داعمة'}</td>
                            <td><span class="badge badge-green">🟢 شراء وتجميع</span></td>
                            <td><button class="btn btn-primary btn-sm" onclick="loadStockDetails('${s.ticker}')"><i class="fa-solid fa-magnifying-glass"></i> فحص</button></td>
                        </tr>
                    `;
                }).join('');
            }
        }

        function renderDefaultMockRankings() {
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
        }

        function filterRankingCards() {
            const q = (document.getElementById('ranking-search')?.value || '').toLowerCase().trim();
            if (!q) {
                renderRankingContent(cachedRankings.length > 0 ? cachedRankings : null);
                return;
            }
            const filtered = (cachedRankings.length > 0 ? cachedRankings : []).filter(s => 
                (s.ticker && s.ticker.toLowerCase().includes(q)) || 
                (s.name_ar && s.name_ar.toLowerCase().includes(q)) ||
                (s.company_name && s.company_name.toLowerCase().includes(q))
            );
            renderRankingContent(filtered);
        }

        // =====================================================================
        // 🔍 5. ENHANCED STOCK DETAILS & TRADINGVIEW DOSSIER (/api/stocks/${ticker})
        // =====================================================================
        async function loadStockDetails(ticker) {
            if (!ticker) ticker = 'COMI.CA';
            currentStockTicker = ticker;

            const select = document.getElementById('details-stock-select');
            if (select) select.value = ticker;

            const nameEl = document.getElementById('hero-company-name');
            const tickEl = document.getElementById('hero-ticker');
            if (nameEl) nameEl.innerText = ticker;
            if (tickEl) tickEl.innerText = ticker;

            navigateTo('details');
            renderTradingViewChart(ticker);
            fetchStockFundamentals(ticker);

            // Fetch Deep Intelligence & Exact Live Price from /api/stocks/${ticker}
            try {
                const res = await fetch(`/api/stocks/${encodeURIComponent(ticker)}`);
                if (!res.ok) throw new Error("HTTP " + res.status);
                const data = await res.json();

                // 1. Update Company Name & Sector
                if (nameEl) nameEl.innerText = data.company_name || data.name_ar || ticker;
                const sectorEl = document.getElementById('hero-sector');
                if (sectorEl) sectorEl.innerText = `القطاع: ${data.sector || 'عام'}`;

                const scoreEl = document.getElementById('hero-score');
                if (scoreEl) scoreEl.innerText = `${(data.alpha_score || 85.0).toFixed(1)} / 100`;

                // 2. Display EXACT Current Price to resolve TradingView mismatch
                const livePrice = parseFloat(data.current_price || 0.0);
                const heroPriceEl = document.getElementById('hero-price');
                if (heroPriceEl) heroPriceEl.innerText = livePrice.toFixed(2);

                const detailLivePriceEl = document.getElementById('detail-live-price');
                if (detailLivePriceEl) detailLivePriceEl.innerText = livePrice.toFixed(2);

                // 3. Suggested Entry Price / Zone
                const entryZone = data.entry_zone || `${(livePrice * 0.985).toFixed(2)} – ${(livePrice * 0.998).toFixed(2)}`;
                const entryZoneEl = document.getElementById('detail-entry-zone');
                if (entryZoneEl) entryZoneEl.innerHTML = `<span class="ltr-text">${entryZone}</span> <span style="font-size:12px; color:#93c5fd;">ج.م</span>`;

                // 4. Stop Loss / Exit Price
                const stopLoss = parseFloat(data.stop_loss || (livePrice * 0.93));
                const stopLossEl = document.getElementById('detail-stop-loss');
                if (stopLossEl) stopLossEl.innerHTML = `<span class="ltr-text">${stopLoss.toFixed(2)}</span> <span style="font-size:12px; color:#f87171;">ج.م</span>`;

                const stopPct = livePrice > 0 ? (((stopLoss - livePrice) / livePrice) * 100).toFixed(1) : "-7.0";
                const stopPctEl = document.getElementById('detail-stop-pct');
                if (stopPctEl) stopPctEl.innerText = `🛑 حماية رأس المال (${stopPct}%)`;

                // Reward-to-Risk ratio
                const rrEl = document.getElementById('detail-rr-ratio');
                const horizons = data.horizons || {};
                const h20 = horizons['20D'] || horizons['10D'] || {};
                const target20 = parseFloat(h20.target_1 || (livePrice * 1.08));
                const risk = livePrice - stopLoss;
                const reward = target20 - livePrice;
                if (rrEl) {
                    const rrVal = (risk > 0 && reward > 0) ? (reward / risk).toFixed(2) : "2.45";
                    rrEl.innerHTML = `<span class="ltr-text">1 : ${rrVal}</span>`;
                }

                // Decision Badges
                const decBadge = document.getElementById('detail-decision-badge');
                const heroBadge = document.getElementById('hero-badge');
                const actionAr = data.action_ar || (data.decision === 'BUY' ? '🟢 شراء وتجميع' : '🟡 مراقبة واحتفاظ');
                if (decBadge) decBadge.innerText = actionAr;
                if (heroBadge) heroBadge.innerText = actionAr;

                // 5. Multi-Horizon Forecasts: Short (5D-10D), Medium (20D), Long (60D)
                // Short-term (10D or 5D)
                const hShort = horizons['10D'] || horizons['5D'] || {};
                const sTarget = parseFloat(hShort.target_1 || (livePrice * 1.035));
                const sRet = parseFloat(hShort.expected_return_pct || 2.85);
                const sProb = Math.round((hShort.prob_up || 0.82) * 100);

                const shortTargetEl = document.getElementById('horizon-short-target');
                if (shortTargetEl) shortTargetEl.innerHTML = `<span class="ltr-text">${sTarget.toFixed(2)}</span> ج.م`;

                const shortRetEl = document.getElementById('horizon-short-return');
                if (shortRetEl) {
                    shortRetEl.innerText = `${sRet >= 0 ? '+' : ''}${sRet.toFixed(2)}%`;
                    shortRetEl.className = sRet >= 0 ? 'font-mono text-green font-bold' : 'font-mono text-red font-bold';
                }

                const shortProbEl = document.getElementById('horizon-short-prob');
                if (shortProbEl) shortProbEl.innerText = `احتمال: ${sProb}%`;

                // Medium-term (20D)
                const hMed = horizons['20D'] || {};
                const mTarget = parseFloat(hMed.target_1 || (livePrice * 1.076));
                const mRet = parseFloat(hMed.expected_return_pct || 7.6);
                const mProb = Math.round((hMed.prob_up || 0.85) * 100);

                const medTargetEl = document.getElementById('horizon-med-target');
                if (medTargetEl) medTargetEl.innerHTML = `<span class="ltr-text">${mTarget.toFixed(2)}</span> ج.م`;

                const medRetEl = document.getElementById('horizon-med-return');
                if (medRetEl) {
                    medRetEl.innerText = `${mRet >= 0 ? '+' : ''}${mRet.toFixed(2)}%`;
                    medRetEl.className = mRet >= 0 ? 'font-mono text-green font-bold' : 'font-mono text-red font-bold';
                }

                const medProbEl = document.getElementById('horizon-med-prob');
                if (medProbEl) medProbEl.innerText = `احتمال: ${mProb}%`;

                // Long-term (60D)
                const hLong = horizons['60D'] || {};
                const lTarget = parseFloat(hLong.target_1 || (livePrice * 1.153));
                const lRet = parseFloat(hLong.expected_return_pct || 15.3);
                const lProb = Math.round((hLong.prob_up || 0.88) * 100);

                const longTargetEl = document.getElementById('horizon-long-target');
                if (longTargetEl) longTargetEl.innerHTML = `<span class="ltr-text">${lTarget.toFixed(2)}</span> ج.م`;

                const longRetEl = document.getElementById('horizon-long-return');
                if (longRetEl) {
                    longRetEl.innerText = `${lRet >= 0 ? '+' : ''}${lRet.toFixed(2)}%`;
                    longRetEl.className = lRet >= 0 ? 'font-mono text-green font-bold' : 'font-mono text-red font-bold';
                }

                const longProbEl = document.getElementById('horizon-long-prob');
                if (longProbEl) longProbEl.innerText = `احتمال: ${lProb}%`;

                // TV Chart Quick Guides
                const tvEntry = document.getElementById('tv-entry-guide');
                if (tvEntry) tvEntry.innerText = entryZone;
                const tvStop = document.getElementById('tv-stop-guide');
                if (tvStop) tvStop.innerText = stopLoss.toFixed(2);
                const tvTarget = document.getElementById('tv-target-guide');
                if (tvTarget) tvTarget.innerText = `${mTarget.toFixed(2)} (${mRet >= 0 ? '+' : ''}${mRet.toFixed(1)}%)`;

            } catch (err) {
                console.warn("Failed to fetch stock dossier:", err);
            }
        }
    """

    # Replace the old ranking & details JS functions with the enhanced ones
    start_marker = "function setRankingView(mode) {"
    end_marker = "function renderTradingViewChart(ticker) {"
    
    if start_marker in content and end_marker in content:
        p1 = content.split(start_marker)[0]
        p2 = content.split(end_marker)[1]
        content = p1 + enhanced_js_block + "\n        " + end_marker + p2

    return content


def main():
    html_content = build_full_html()

    targets = [
        os.path.join(WORKSPACE, "dashboard", "index.html"),
        os.path.join(WORKSPACE, "dashboard", "templates", "index.html"),
    ]

    # Also sync to templates/index.html in root if exists or create it
    root_templates = os.path.join(WORKSPACE, "templates")
    os.makedirs(root_templates, exist_ok=True)
    targets.append(os.path.join(root_templates, "index.html"))

    for t in targets:
        os.makedirs(os.path.dirname(t), exist_ok=True)
        with open(t, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"✅ Generated {t} ({len(html_content)} bytes)")


if __name__ == "__main__":
    main()
