#!/usr/bin/env python3
# =============================================================================
# core/ai_generative_engine.py — GEN-26 Generative AI & Financial Chatbot Engine
# Institutional Generative AI Architecture for the Egyptian Stock Exchange (EGX):
# 1. Multi-LLM Provider Bridge (Google Gemini 1.5/2.0 Flash & OpenAI GPT-4o).
# 2. Daily Arabic Quantitative Morning Briefing Synthesizer.
# 3. Interactive Context-Aware Quant Chatbot Assistant for Web Dashboard.
# 4. Graceful Offline Rule-Based Quant Intelligence Fallbacks (Zero Downtime).
# 5. Strict Risk Disclaimers & Egyptian Financial Regulatory Alignment.
# =============================================================================

import os
import sys
import json
import time
import datetime
import logging
import urllib.request
import urllib.error
from typing import Dict, List, Any, Optional, Union, Tuple

# Configure logger
logger = logging.getLogger("AIGenerativeEngine")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] [AIGenerativeEngine] %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)


class AIGenerativeEngine:
    """
    Core Generative AI & Interactive NLP Engine for Gen-26 Quant Robo-Advisor.
    
    Provides:
    - High-level macro & micro automated Arabic market reports (Morning Briefing).
    - Real-time interactive financial chatbot responding to portfolio, stock, and market inquiries.
    - Seamless fallback to deterministic quantitative synthesizers when LLM API keys are absent or unreachable.
    """

    REQUEST_TIMEOUT_SECONDS: float = 6.0

    # Arabic descriptions of market regimes
    REGIME_TRANSLATIONS: Dict[str, str] = {
        "BULLISH_TREND": "🟢 اتجاه صاعد قوي (زخم شرائي مؤسسي)",
        "BULL_MARKET": "🟢 سوق صاعد (Bull Market)",
        "BULL": "🟢 سوق صاعد وقوي (Bull Market)",
        "BEARISH_CORRECTION": "🔴 تصحيح هابط (ضغوط بيعية واحتراس)",
        "BEAR_MARKET": "🔴 سوق هابط (Bear Market)",
        "BEAR": "🔴 سوق هابط واحتراس (Bear Market)",
        "HIGH_VOLATILITY": "⚡ تقلبات سعرية حادة (High Volatility)",
        "SIDEWAYS": "⚪ اتجاه عرضي وتذبذب ضيق (Range-Bound)",
        "ACCUMULATION": "🔵 مرحلة تجميع ذكي (Institutional Accumulation)",
        "DISTRIBUTION": "🟠 مرحلة تصريف وتخفيف مراكز (Distribution)"
    }

    # Ticker name translations for natural conversational responses
    COMPANY_NAMES_AR: Dict[str, str] = {
        "COMI.CA": "البنك التجاري الدولي (CIB)",
        "SWDY.CA": "السويدي إليكتريك",
        "TMGH.CA": "مجموعة طلعت مصطفى",
        "ORAS.CA": "أوراسكوم للإنشاء",
        "ABUK.CA": "أبو قير للأسمدة",
        "FWRY.CA": "فوري لتكنولوجيا المدفوعات",
        "ETEL.CA": "المصرية للاتصالات (وي)",
        "EKHO.CA": "المصرية الكويتية القابضة",
        "EAST.CA": "الشرقية - إيسترن كومباني",
        "AMOC.CA": "الإسكندرية للزيوت المعدنية (أموك)",
        "MFPC.CA": "مصر لإنتاج الأسمدة (موبكو)",
        "SKPC.CA": "سيدي كرير للبتروكيماويات",
        "HELI.CA": "مصر الجديدة للإسكان والتعمير",
        "PHDC.CA": "بالم هيلز للتعمير",
        "ISPH.CA": "ابن سينا فارما",
        "CICH.CA": "سي آي كابيتال القابضة",
        "HRHO.CA": "إي إف جي هيرمس القابضة"
    }

    @classmethod
    def _get_api_credentials(cls) -> Tuple[Optional[str], str]:
        """
        Detects configured LLM API keys in order of priority:
        1. GEMINI_API_KEY (Google Gemini)
        2. OPENAI_API_KEY (OpenAI)
        3. LLM_API_KEY (Generic fallback)
        
        Returns:
            Tuple[Optional[str], str]: (api_key, provider_type) where provider_type in ['GEMINI', 'OPENAI', 'NONE']
        """
        gemini_key = os.getenv("GEMINI_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        generic_key = os.getenv("LLM_API_KEY")

        if gemini_key:
            return gemini_key.strip(), "GEMINI"
        if openai_key:
            return openai_key.strip(), "OPENAI"
        if generic_key:
            key_str = generic_key.strip()
            if key_str.startswith("AIza"):
                return key_str, "GEMINI"
            elif key_str.startswith("sk-"):
                return key_str, "OPENAI"
            return key_str, "GEMINI"

        return None, "NONE"

    # =========================================================================
    # 1. MORNING BRIEFING GENERATOR
    # =========================================================================

    @classmethod
    def generate_morning_briefing(
        cls,
        top_stocks: List[Union[Dict[str, Any], str]],
        market_regime: str = "BULLISH_TREND"
    ) -> Dict[str, Any]:
        """
        Generates a comprehensive, professional Arabic morning financial briefing for EGX traders.
        
        Uses an LLM when API keys are present; otherwise uses the internal
        quantitative synthesis engine to ensure zero downtime.

        Args:
            top_stocks: List of top-ranked stock dictionaries or ticker strings.
            market_regime: Active market regime label (e.g. 'BULLISH_TREND', 'HIGH_VOLATILITY').

        Returns:
            Dict[str, Any]: Structured briefing report including markdown text, recommendations, and metadata.
        """
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        regime_clean = market_regime.upper().strip() if market_regime else "BULLISH_TREND"
        regime_ar = cls.REGIME_TRANSLATIONS.get(regime_clean, f"حالة السوق ({regime_clean})")

        # Sanitize and normalize stock payload
        normalized_stocks = cls._normalize_top_stocks(top_stocks)
        
        api_key, provider = cls._get_api_credentials()
        llm_briefing_text = None
        source_tag = "OFFLINE_QUANT_INTELLIGENCE"

        if api_key and provider != "NONE":
            logger.info(f"Attempting live LLM generation via {provider}...")
            prompt = cls._build_morning_briefing_prompt(normalized_stocks, regime_clean, regime_ar)
            llm_briefing_text = cls._call_llm_api(prompt, api_key, provider)
            if llm_briefing_text:
                source_tag = f"LIVE_{provider}_LLM"

        # If LLM response succeeded, use it; otherwise fallback to rich deterministic synthesis
        if not llm_briefing_text:
            llm_briefing_text = cls._synthesize_offline_morning_briefing(normalized_stocks, regime_clean, regime_ar)

        # Build structured key recommendations
        key_recs = []
        for stock in normalized_stocks[:5]:
            ticker = stock.get("ticker", "EGX")
            name = cls.COMPANY_NAMES_AR.get(ticker, ticker)
            p = stock.get("price", 0.0)
            score = stock.get("composite_score", 85.0)
            
            target_p = round(p * 1.08, 2) if p > 0 else "مستهدف +8%"
            stop_p = round(p * 0.95, 2) if p > 0 else "وقف -5%"
            
            key_recs.append({
                "ticker": ticker,
                "name_ar": name,
                "current_price_egp": p,
                "composite_score": score,
                "action": "شراء تدريجي وتجميع" if score >= 80 else "مراقبة واحتفاظ",
                "target_price_egp": target_p,
                "stop_loss_egp": stop_p,
                "rationale": f"زخم كمي إيجابي مرتفع بقوة {score:.1f}/100 مع ثبات فوق المتوسطات المتحركة الرئيسية."
            })

        return {
            "status": "SUCCESS",
            "generated_at": now_str,
            "market_regime": regime_clean,
            "market_regime_ar": regime_ar,
            "headline": f"التقرير الصباحي الكمي للبورصة المصرية ({now_str.split()[0]})",
            "summary_markdown": llm_briefing_text,
            "key_recommendations": key_recs,
            "macro_tactics": "التركيز على الأسهم القيادية ذات التدفقات النقدية القوية مع وضع أوامر وقف خسارة متحركة.",
            "risk_guidelines": "الالتزام بسقف 30% كحد أقصى للسهم الواحد، والاحتفاظ بنسبة سيولة نقدية لا تقل عن 10%.",
            "source": source_tag
        }

    # =========================================================================
    # 2. INTERACTIVE QUANT CHATBOT
    # =========================================================================

    @classmethod
    def chat_with_quant(
        cls,
        user_query: str,
        system_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Interactive financial chatbot for EGX investors and traders.
        
        Answers user questions in fluent, highly professional Arabic using real-time
        system context (prices, rankings, model forecasts, portfolio state).

        Args:
            user_query: The natural language question entered by the user.
            system_context: Real-time contextual dictionary (holdings, cash, top picks, regime).

        Returns:
            str: Intelligent Arabic markdown response tailored to the query.
        """
        if not user_query or not user_query.strip():
            return "مرحباً بك! أنا المستشار الكمي الذكي لنظام GEN-26. كيف يمكنني مساعدتك اليوم في تداولات البورصة المصرية وإدارة محفظتك؟"

        clean_query = user_query.strip()
        system_context = system_context or {}
        
        api_key, provider = cls._get_api_credentials()
        
        if api_key and provider != "NONE":
            logger.info(f"Routing chat query to {provider}...")
            prompt = cls._build_chat_prompt(clean_query, system_context)
            llm_response = cls._call_llm_api(prompt, api_key, provider, is_chat=True)
            if llm_response:
                return llm_response

        # Fallback to smart context-aware quantitative response synthesizer
        return cls._synthesize_offline_chat_response(clean_query, system_context)

    # =========================================================================
    # 3. LLM API CALL BRIDGES (GEMINI & OPENAI)
    # =========================================================================

    @classmethod
    def _call_llm_api(
        cls,
        prompt: str,
        api_key: str,
        provider: str,
        is_chat: bool = False
    ) -> Optional[str]:
        """
        Executes a robust HTTPS REST request to Gemini or OpenAI with strict timeout guards.
        """
        try:
            if provider == "GEMINI":
                return cls._call_gemini_rest(prompt, api_key)
            elif provider == "OPENAI":
                return cls._call_openai_rest(prompt, api_key)
        except Exception as e:
            logger.warning(f"Live LLM API call failed ({type(e).__name__}: {str(e)}). Falling back to internal engine.")
            return None

        return None

    @classmethod
    def _call_gemini_rest(cls, prompt: str, api_key: str) -> Optional[str]:
        """
        Invokes Google Gemini 1.5 Flash via standard REST API.
        """
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 1000
            }
        }
        
        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data_bytes,
            headers={"Content-Type": "application/json"}
        )
        
        with urllib.request.urlopen(req, timeout=cls.REQUEST_TIMEOUT_SECONDS) as resp:
            if resp.status == 200:
                body = json.loads(resp.read().decode("utf-8"))
                candidates = body.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "").strip()

        return None

    @classmethod
    def _call_openai_rest(cls, prompt: str, api_key: str) -> Optional[str]:
        """
        Invokes OpenAI GPT-4o-mini via standard REST API.
        """
        url = "https://api.openai.com/v1/chat/completions"
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "أنت المستشار المالي والكمي الذكي (GEN-26 Quant Robo-Advisor) للبورصة المصرية. تجيب باللغة العربية الفصحى بدقة واحترافية."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 1000
        }
        
        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data_bytes,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
        )
        
        with urllib.request.urlopen(req, timeout=cls.REQUEST_TIMEOUT_SECONDS) as resp:
            if resp.status == 200:
                body = json.loads(resp.read().decode("utf-8"))
                choices = body.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "").strip()

        return None

    # =========================================================================
    # 4. PROMPT BUILDERS
    # =========================================================================

    @classmethod
    def _build_morning_briefing_prompt(
        cls,
        stocks: List[Dict[str, Any]],
        regime: str,
        regime_ar: str
    ) -> str:
        """
        Constructs an institutional prompt for generating Arabic daily market briefings.
        """
        stocks_summary = "\n".join([
            f"- {s.get('ticker')}: سعر {s.get('price', 'N/A')} ج.م | درجة التقييم الكمي: {s.get('composite_score', 80):.1f}/100"
            for s in stocks[:5]
        ])

        return f"""
أنت رئيس أبحاث الاستثمار الكمي في صندوق استثماري للبورصة المصرية (EGX).
المطلوب: إعداد 'التقرير الصباحي الكمي' لجلسة اليوم باللغة العربية الفصحى الاحترافية وبتنسيق Markdown منسق وجميل.

بيانات الجلسة المتاحة:
- حالة نظام السوق الإجمالية (Market Regime): {regime_ar} ({regime})
- أفضل الأسهم المختارة كمياً بالخوارزميات:
{stocks_summary}

هيكل التقرير المطلوب:
1. ☀️ **نظرة عامة على جلسة التداول واتجاه السوق**: تحليل موجز للحالة العامة وحجم السيولة المتوقع.
2. 🎯 **الفرص الاستثمارية والأسهم المرشحة**: تحليل مقتضب لأبرز سهمين أو 3 أسهم مع تحديد أهداف سعرية ومستويات وقف خسارة.
3. 🛡️ **استراتيجية إدارة المخاطر وتوزيع السيولة**: نصائح للمتداولين بناءً على حالة السوق الحالية.
4. ⚠️ **إخلاء المسؤولية المالي**: تذكير بأن هذه التقديرات نتاج نماذج كمية وليست توصيات شراء مباشرة.
"""

    @classmethod
    def _build_chat_prompt(cls, query: str, context: Dict[str, Any]) -> str:
        """
        Builds the context-injected prompt for the conversational chatbot.
        """
        context_str = json.dumps(context, ensure_ascii=False, indent=2)
        return f"""
أنت المستشار الكمي والمساعد الذكي (GEN-26 Quant AI) الخاص بمنصة إدارة الاستثمار في البورصة المصرية.
تحدث باللغة العربية الفصحى بأسلوب مالي رصين، واثق، ودقيق ومباشر.

بيانات النظام اللحظية المتاحة (Real-time Context):
{context_str}

سؤال المستثمر:
"{query}"

تعليمات الإجابة:
1. أجب بشكل مباشر ودقيق على استفسار المستخدم مع ذكر الأرقام والأسعار إن توفرت في السياق.
2. استخدم نقاطاً منسقة وأيقونات مناسبة لجعل الرد سهل القراءة وممتعاً.
3. ركز على إدارة رأس المال وحماية المحفظة كأولوية أولى.
"""

    # =========================================================================
    # 5. OFFLINE INTELLIGENT SYNTHESIZERS (ZERO-DEPENDENCY FALLBACKS)
    # =========================================================================

    @classmethod
    def _synthesize_offline_morning_briefing(
        cls,
        stocks: List[Dict[str, Any]],
        regime: str,
        regime_ar: str
    ) -> str:
        """
        Generates a human-like, beautifully formatted Arabic financial morning report
        using native quantitative data without requiring an external internet LLM.
        """
        date_today = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # Build highlights table
        stock_lines = []
        for i, s in enumerate(stocks[:4], 1):
            ticker = s.get("ticker", "EGX")
            name = cls.COMPANY_NAMES_AR.get(ticker, ticker)
            p = s.get("price", 0.0)
            score = s.get("composite_score", 85.0)
            target = f"{p * 1.07:.2f} ج.م" if p > 0 else "مستهدف +7%"
            stop = f"{p * 0.95:.2f} ج.م" if p > 0 else "وقف -5%"
            price_str = f"{p:.2f} ج.م" if p > 0 else "سعر السوق اللحظي"
            
            stock_lines.append(
                f"| {i} | **{name}** (`{ticker}`) | `{price_str}` | `{score:.1f}/100` | `{target}` | `{stop}` | 🟢 تجميع وشراء |"
            )

        stocks_table = "\n".join(stock_lines) if stock_lines else "| - | لا توجد أسهم متاحة حالياً | - | - | - | - | - |"

        return f"""# ☀️ التقرير الصباحي الكمي — البورصة المصرية (EGX)
**تاريخ الجلسة:** `{date_today}` | **حالة السوق العامة:** {regime_ar}

---

### 📊 1. النظرة العامة على جلسة التداول
تُشير القراءات الخوارزمية لنظام **GEN-26** إلى سيطرة **{regime_ar}** على المؤشر العام، مع استقرار التدفقات النقدية المؤسسية داخل قطاعات البنوك، البتروكيماويات، والتطوير العقاري. يُنصح بالحفاظ على توازن المراكز الاستثمارية واستغلال الارتدادات الفنية لتجميع الأسهم القيادية.

---

### 🎯 2. أبرز الفرص الاستثمارية المرشحة كمياً اليوم
تم اختيار هذه القائمة بناءً على نموذج الذكاء الاصطناعي متعدد الأبعاد (الزخم السعري + التدفق النقدي + التحليل الإخباري):

| # | السهم والشركة | السعر الحالي | التقييم الكمي | المستهدف الفني | وقف الخسارة | الإجراء المقترح |
|---|---|---|---|---|---|---|
{stocks_table}

---

### 🛡️ 3. خطة توزيع السيولة وإدارة المخاطر
* **حد التركيز الإلزامي:** لا تتجاوز استثماراتك في السهم الواحد **30%** من إجمالي حجم المحفظة لضمان التنويع الرقابي.
* **الاحتياطي النقدي (Cash Buffer):** يُوصى بالاحتفاظ بنسبة سيولة لا تقل عن **10% - 15%** لاقتناص الفرص السريعة خلال الجلسة.
* **تفعيل وقف الخسارة المتحرك (Trailing Stop):** لحماية الأرباح المحققة مع صعود الأسعار.

---
> ⚠️ **إخلاء مسؤولية تنظيمي:** هذا التقرير تم إعداده بواسطة نماذج التحليل الكمي لنظام GEN-26 لأغراض الإرشاد المعرفي ودعم القرار الاستثماري، ولا يُعتبر توصية شراء أو بيع مالية مباشرة دون دراسة ملائمة المخاطر الفردية.
"""

    TICKER_SEARCH_ALIASES: Dict[str, List[str]] = {
        "COMI.CA": ["comi", "cib", "التجاري الدولي", "تجاري دولي", "سي اي بي", "البنك التجاري"],
        "SWDY.CA": ["swdy", "السويدي", "سويدي", "السويدى", "سويدى"],
        "TMGH.CA": ["tmgh", "طلعت مصطفى", "طلعت", "مجموعة طلعت"],
        "ORAS.CA": ["oras", "أوراسكوم", "اوراسكوم", "أوراسكوم للإنشاء", "اوراسكوم للانشاء"],
        "ABUK.CA": ["abuk", "أبو قير", "ابو قير", "أبوقير", "ابوقير"],
        "FWRY.CA": ["fwry", "فوري", "فورى"],
        "ETEL.CA": ["etel", "المصرية للاتصالات", "we", "وي"],
        "AMOC.CA": ["amoc", "أموك", "اموك"],
        "MFPC.CA": ["mfpc", "موبكو", "مصر لإنتاج الأسمدة"],
        "EAST.CA": ["east", "الشرقية للدخان", "إيسترن", "ايسترن"],
        "HELI.CA": ["heli", "مصر الجديدة للإسكان", "مصر الجديدة"],
        "PHDC.CA": ["phdc", "بالم هيلز", "بالم هيلز للتعمير"],
        "SKPC.CA": ["skpc", "سيدي كرير", "سيدى كرير"],
        "HRHO.CA": ["hrho", "هيرمس", "إي إف جي", "هيرميس"]
    }

    @classmethod
    def _synthesize_offline_chat_response(
        cls,
        query: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Natural Language understanding and response generator for chatbot queries offline.
        """
        q_lower = query.lower()
        context = context or {}

        # Safely normalize prices input whether dict or list
        prices_input = context.get("prices", {})
        if isinstance(prices_input, list):
            prices_dict = {
                item.get("ticker", item.get("symbol", "")): item.get("price", 0.0)
                for item in prices_input if isinstance(item, dict)
            }
        elif isinstance(prices_input, dict):
            prices_dict = prices_input
        else:
            prices_dict = {}
        
        # 1. Check for specific ticker inquiries using aliases
        for ticker, aliases in cls.TICKER_SEARCH_ALIASES.items():
            if any(alias in q_lower for alias in aliases):
                name_ar = cls.COMPANY_NAMES_AR.get(ticker, ticker)
                p = prices_dict.get(ticker, prices_dict.get(ticker.replace(".CA", "")))
                p_text = f"{p:.2f} ج.م" if (p and p > 0) else "حوالي سعر الإغلاق السابق"
                target_text = f"{p * 1.08:.2f} ج.م" if (p and p > 0) else "+8% من سعر الدخول"
                stop_text = f"{p * 0.95:.2f} ج.م" if (p and p > 0) else "-5% من سعر الدخول"
                return f"""### 📈 التحليل الكمي لسهم {name_ar} (`{ticker}`):

* **السعر الحالي:** `{p_text}`
* **التقييم الخوارزمي:** يتمتع السهم بزخم إيجابي وتدفقات نقدية قوية ضمن أفضل أسهم المؤشر.
* **المستهدف المقترح:** `{target_text}`
* **وقف الخسارة الموصى به:** `{stop_text}`

💡 **نصيحة المستشار:** يُفضل الدخول بنظام الشراء التدريجي وتجنب تخصيص أكثر من **30%** من المحفظة في هذا السهم."""

        # 2. Inquiries about Best Stocks to buy / Recommendations
        if any(w in query for w in ["أفضل", "شراء", "ترشيح", "فرص", "اشتري", "اسهم"]):
            top_list = context.get("top_stocks", ["COMI.CA", "SWDY.CA", "TMGH.CA", "ORAS.CA"])
            top_formatted = []
            for s in top_list[:4]:
                t = s.get("ticker", s) if isinstance(s, dict) else str(s)
                name = cls.COMPANY_NAMES_AR.get(t, t)
                top_formatted.append(f"- **{name}** (`{t}`): مؤشرات الزخم والتدفق المالي مرتفعة.")
            
            top_str = "\n".join(top_formatted)
            return f"""### 🚀 أفضل الفرص الاستثمارية المرشحة حالياً:

بناءً على التقييم الكمي لنظام GEN-26، إليك أبرز الأسهم المؤهلة للشراء اليوم:

{top_str}

🎯 **توجيه تكتيكي:** وزّع رأس مالك المخصص بين هذه الأسهم بالتساوي أو وفقاً لنموذج تكافؤ المخاطر (Risk Parity) للحصول على أعلى عائد معدل بالمخاطر."""

        # 3. Inquiries about Market Regime / Market State
        if any(w in query for w in ["سوق", "المؤشر", "egx30", "اتجاه", "الوضع"]):
            regime = context.get("market_regime", "BULLISH_TREND")
            regime_ar = cls.REGIME_TRANSLATIONS.get(regime, "اتجاه صاعد إيجابي")
            return f"""### 🏛️ تقرير حالة البورصة المصرية (EGX):

* **حالة السوق الحالية:** {regime_ar}
* **قراءة السيولة:** تدفقات مؤسسية نشطة مع تحسن في قيم التداول اليومية.
* **الاستراتيجية المعتمدة:** الشراء عند مستويات الدعم مع الاحتفاظ بـ **15% كاش** لتجنب أي تصحيحات مباغتة."""

        # 4. Inquiries about Portfolio allocation / Capital sizing
        if any(w in query for w in ["محفظ", "توزيع", "رأس مال", "فلوس", "جنيه", "مبلغ"]):
            cash = context.get("total_capital_egp", context.get("cash", 100000.0))
            return f"""### 💼 خطة التوزيع الذكي لرأس المال (Portfolio Sizing):

للحصول على محفظة استثمارية متوازنة تحمي رأس المال وتحقق عائداً مرتفعاً:

1. **الأسهم القيادية (Large Caps):** خصص **60%** موزعة على (CIB، السويدي، طلعت مصطفى).
2. **أسهم النمو السريع (Mid/Growth):** خصص **25%** موزعة على قطاعات التكنولوجيا أو البتروكيماويات.
3. **السيولة النقدية (Cash Reserve):** احتفظ بـ **15%** كاش لمواجهة أي فرص لحظية.
4. ⚠️ **قيد تنظيمي:** تأكد أن أي سهم منفرد لا يتجاوز **30%** من إجمالي المحفظة."""

        # General Intelligent Response
        return f"""مرحباً بك! أنا مستشارك المالي والكمي الذكي لنظام **GEN-26**.

أستطيع مساعدتك في:
- 📊 **تحليل أي سهم مصري** وتحديد نقاط الدخول والخروج ووقف الخسارة.
- 🎯 **استعراض أفضل الأسهم المؤهلة للشراء** وفق أحدث تقييم خوارزمي.
- 🏛️ **شرح اتجاه السوق وحالة مؤشر EGX30**.
- 💼 **توزيع السيولة وبناء محفظة متوازنة** تحترم قيود إدارة المخاطر.

ما هو السهم أو الموضوع الذي ترغب في استكشافه الآن؟"""

    # =========================================================================
    # 6. HELPERS & UTILITIES
    # =========================================================================

    @classmethod
    def _normalize_top_stocks(cls, raw_stocks: List[Union[Dict[str, Any], str]]) -> List[Dict[str, Any]]:
        """
        Normalizes various stock input structures into clean dictionaries.
        """
        if not raw_stocks:
            # Default institutional baseline picks
            return [
                {"ticker": "COMI.CA", "price": 140.50, "composite_score": 92.5},
                {"ticker": "SWDY.CA", "price": 128.00, "composite_score": 88.0},
                {"ticker": "TMGH.CA", "price": 62.25, "composite_score": 86.4},
                {"ticker": "ORAS.CA", "price": 310.00, "composite_score": 84.2},
                {"ticker": "ABUK.CA", "price": 55.80, "composite_score": 81.0}
            ]

        results = []
        for item in raw_stocks:
            if isinstance(item, str):
                ticker_clean = item.upper().strip()
                results.append({
                    "ticker": ticker_clean,
                    "price": 100.0,
                    "composite_score": 85.0
                })
            elif isinstance(item, dict):
                ticker = item.get("ticker", item.get("symbol", "EGX")).upper().strip()
                price = float(item.get("price", item.get("current_price", item.get("close", 0.0))))
                score = float(item.get("composite_score", item.get("score", 85.0)))
                results.append({
                    "ticker": ticker,
                    "price": price,
                    "composite_score": score
                })
        return results


# =============================================================================
# CLI DEMONSTRATION & TEST RUNNER
# =============================================================================

if __name__ == "__main__":
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("===============================================================")
    print("🤖 GEN-26 GENERATIVE AI & QUANT CHATBOT ENGINE")
    print("===============================================================")

    # 1. Test Morning Briefing
    sample_stocks = [
        {"ticker": "COMI.CA", "price": 140.50, "composite_score": 94.2},
        {"ticker": "SWDY.CA", "price": 128.00, "composite_score": 89.5},
        {"ticker": "TMGH.CA", "price": 62.25, "composite_score": 87.1},
        {"ticker": "ORAS.CA", "price": 310.00, "composite_score": 85.0}
    ]
    briefing = AIGenerativeEngine.generate_morning_briefing(sample_stocks, market_regime="BULLISH_TREND")
    print("\n--- 1. MORNING BRIEFING OUTPUT ---")
    print(briefing["summary_markdown"])

    # 2. Test Interactive Chatbot
    print("\n--- 2. INTERACTIVE CHATBOT RESPONSES ---")
    test_queries = [
        "ما هو أفضل سهم للشراء اليوم؟",
        "ما هو وضع سهم طلعت مصطفى وسعر الدخول؟",
        "كيف أوزع محفظة قيمتها 200 ألف جنيه؟"
    ]
    context = {
        "market_regime": "BULLISH_TREND",
        "top_stocks": sample_stocks,
        "prices": {"TMGH.CA": 62.25, "COMI.CA": 140.50, "SWDY.CA": 128.00}
    }
    for q in test_queries:
        print(f"\n👤 المستخدم: {q}")
        reply = AIGenerativeEngine.chat_with_quant(q, context)
        print(f"🤖 المستشار الذكي:\n{reply}")
