#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# scripts/build_ui.py — Generates Mission Control Web Dashboard with TailwindCSS
# Integrates:
# 1. TailwindCSS Dark Mode & RTL Arabic typography (Cairo & Tajawal).
# 2. Morning Briefing Hero Card at the top (connected to /api/morning_briefing).
# 3. ChatGPT-style Floating Quant Chatbot with typing spinner (connected to /api/chat).
# 4. Traffic Light Decision System (🟢 Buy, 🟡 Hold, 🔴 Avoid).
# 5. One-Click Portfolio Sizer Modal ("توزيع ميزانيتي").
# 6. Preserves 100% of forensic DOM test IDs.
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

    # 4. Chatbot markup injection if missing
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

    # 5. Add clearChatHistory function to JavaScript if missing
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
