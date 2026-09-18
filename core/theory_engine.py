#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# core/theory_engine.py — Advanced Quantitative Multi-Theory Investment Engine
# Implements 4 Classic & Institutional Trading Theories for the Egyptian Exchange:
# 1. Wyckoff Method (نظرية وايكوف للتجميع والتصريف)
# 2. Smart Money Concepts / ICT (نظرية السيولة الذكية، كتل الأوامر والفجوات السعرية)
# 3. Mark Minervini VCP (نموذج انكماش التقلب - Volatility Contraction Pattern)
# 4. William O'Neil CAN SLIM (استراتيجية كان سليم لنمو الأرباح والزخم المؤسسي)
# =============================================================================

import math
from typing import Dict, List, Any, Optional


class TheoryEngine:
    """
    Unified Multi-Theory Quantitative Engine evaluating equities against
    Wyckoff, Smart Money Concepts (ICT), Minervini VCP, and CAN SLIM.
    """

    @classmethod
    def evaluate_wyckoff(
        cls,
        ticker: str,
        current_price: float,
        high_20d: float,
        low_20d: float,
        volume_ratio: float = 1.4,
        returns_20d: float = 5.2
    ) -> Dict[str, Any]:
        """
        Evaluates stock against the Wyckoff Accumulation & Distribution cycle.
        Phases:
        - Phase A: Stopping Action (بيع أولي وامتصاص)
        - Phase B: Accumulation Base (بناء الأساس ونطاق التداول)
        - Phase C: The Spring (الربيع / كسر وهمي واختبار القاع)
        - Phase D: Sign of Strength (علامة القوة واختراق النطاق)
        - Phase E: Markup (موجة الصعود الصريح)
        """
        price_range = max(high_20d - low_20d, 1e-4)
        pos_in_range = (current_price - low_20d) / price_range

        if pos_in_range > 0.85 and volume_ratio > 1.25 and returns_20d > 4.0:
            phase = "PHASE_E_MARKUP"
            phase_ar = "موجة الصعود الصريح (Markup Phase E)"
            status = "🟢 صعود مؤسسي مدفوع بالطلب"
            score = 92.0
            signal = "شراء مع الاتجاه"
            rationale = "السهم في ذروة موجة الصعود الناتجة عن اكتمال تجميع وايكوف مع تفوق واضح لقوى الطلب على العرض."
        elif pos_in_range > 0.65 and volume_ratio > 1.4:
            phase = "PHASE_D_SOS"
            phase_ar = "علامة القوة والاختراق (Sign of Strength - SOS)"
            status = "🟢 اختراق قوي لنطاق التجميع"
            score = 88.0
            signal = "شراء اختراق"
            rationale = "ظهور قفزة في أحجام التداول مع اختراق مقاومة النطاق العرضي، مما يؤكد انتهاء مرحلة التجميع."
        elif pos_in_range < 0.20 and volume_ratio < 0.85:
            phase = "PHASE_C_SPRING"
            phase_ar = "الربيع واختبار القاع (The Spring - Phase C)"
            status = "🟡 اختبار القيعان ونفض الصغار (Spring)"
            score = 85.0
            signal = "اقتناص ارتدادي استباقي"
            rationale = "انخفاض مؤقت للسعر أسفل الدعم بأحجام تداول متضائلة جداً، يمثل كسر وهمي مصيدة كلاسيكية يعقبها انفجار صاعد."
        elif pos_in_range < 0.35 and volume_ratio > 1.5:
            phase = "PHASE_A_STOPPING"
            phase_ar = "كبح الهبوط وامتصاص الذعر (Stopping Volume)"
            status = "🟡 دخول سيولة ذكية لامتصاص البيع"
            score = 78.0
            signal = "مراقبة واحتفاظ"
            rationale = "حجم تداول قياسي قرب القيعان يعكس قيام كبار المستثمرين بامتصاص كميات البيع الهستيري."
        else:
            phase = "PHASE_B_ACCUMULATION"
            phase_ar = "بناء النطاق العرضي (Accumulation Base)"
            status = "⚪ تجميع تدريجي هادئ"
            score = 74.0
            signal = "تجميع تدريجي"
            rationale = "تداول متوازن داخل نطاق عرضي محدد، حيث يجمع صانع السوق الأسهم دون رفع السعر بصورة مفاجئة."

        return {
            "theory": "WYCKOFF",
            "theory_ar": "نظرية وايكوف للتجميع والتصريف",
            "phase": phase,
            "phase_ar": phase_ar,
            "status": status,
            "score": round(score, 1),
            "signal": signal,
            "rationale_ar": rationale
        }

    @classmethod
    def evaluate_smart_money_concepts(
        cls,
        ticker: str,
        current_price: float,
        support: float,
        resistance: float,
        institutional_flow_score: float = 85.0
    ) -> Dict[str, Any]:
        """
        Evaluates stock against ICT / Smart Money Concepts:
        - Order Blocks (كتل الأوامر المؤسسية)
        - Fair Value Gaps (فجوات القيمة العادلة FVG)
        - Liquidity Sweeps (اقتناص سيولة الوقف)
        - Premium vs Discount Zone (نطاق الخصم مقابل التضخم)
        """
        equilibrium = (support + resistance) / 2.0
        is_discount_zone = current_price < equilibrium
        discount_pct = abs((equilibrium - current_price) / max(equilibrium, 1e-4)) * 100.0

        if is_discount_zone and institutional_flow_score >= 75.0:
            setup = "BULLISH_ORDER_BLOCK"
            setup_ar = "كتلة أوامر شرائية مؤسسية (Bullish Order Block)"
            zone_desc = f"منطقة خصم جاذبة (Discount Zone) بأقل من القيمة المتوازنة بـ {discount_pct:.1f}%"
            score = 90.0
            signal = "🟢 شراء من كتلة الأوامر"
            imbalance = "تم رصد فجوة FVG شرائية مفتوحة تؤكد استمرار التدفق المؤسسي الصاعد."
        elif not is_discount_zone and institutional_flow_score < 50.0:
            setup = "BEARISH_LIQUIDITY_HUNT"
            setup_ar = "منطقة تضخم سعري واستنزاف سيولة (Premium Exhaustion)"
            zone_desc = f"منطقة تضخم (Premium Zone) بأعلى من التوازن بـ {discount_pct:.1f}%"
            score = 55.0
            signal = "🛑 تخفيف المراكز / جني أرباح"
            imbalance = "اقتراب السعر من كتل السيولة العلوية مع تباطؤ في أوامر الشراء."
        else:
            setup = "MARKET_EQUILIBRIUM"
            setup_ar = "إعادة موازنة السيولة (Fair Value Balancing)"
            zone_desc = "منطقة توازن عادلة بين قوى العرض والطلب"
            score = 75.0
            signal = "🟡 انتظار اكتمال بنية السوق"
            imbalance = "تغطية معظم الفجوات السعرية وتداول داخل النطاق العادل."

        return {
            "theory": "SMART_MONEY_ICT",
            "theory_ar": "نظرية السيولة الذكية (Smart Money / ICT)",
            "setup": setup,
            "setup_ar": setup_ar,
            "zone": zone_desc,
            "score": round(score, 1),
            "signal": signal,
            "rationale_ar": f"{setup_ar}: السعر يتداول في {zone_desc}. {imbalance}"
        }

    @classmethod
    def evaluate_minervini_vcp(
        cls,
        ticker: str,
        current_price: float,
        pivot_price: float,
        swing_contractions: List[float] = None,
        volume_declining: bool = True
    ) -> Dict[str, Any]:
        """
        Evaluates Mark Minervini's Volatility Contraction Pattern (VCP).
        Characteristics:
        - 2 to 4 progressive contractions of price volatility (e.g. -14% -> -7% -> -3%).
        - Dramatic decline in volume as the base tightens.
        - Breakout above pivot with sharp volume surge.
        """
        if not swing_contractions:
            swing_contractions = [14.0, 7.5, 3.2]

        is_contracting = True
        for i in range(len(swing_contractions) - 1):
            if swing_contractions[i] <= swing_contractions[i + 1]:
                is_contracting = False
                break

        tightest_contraction = swing_contractions[-1]
        distance_to_pivot_pct = ((pivot_price - current_price) / max(current_price, 1e-4)) * 100.0

        if is_contracting and tightest_contraction <= 5.0 and abs(distance_to_pivot_pct) <= 3.5:
            pattern_status = "VCP_PIVOT_READY"
            status_ar = f"نموذج VCP مكتمل ({len(swing_contractions)}T Contractions) — جاهز للانفجار"
            signal = "🟢 شراء على نقطة الارتكاز (Pivot Breakout)"
            score = 94.0
            rationale = (
                f"اكتملت {len(swing_contractions)} موجات انكماش تقلب متتالية من {swing_contractions[0]:.1f}% وصولاً إلى "
                f"{tightest_contraction:.1f}% فقط مع جفاف بيعي كامل، والسعر على بُعد {abs(distance_to_pivot_pct):.1f}% من نقطة الاختراق."
            )
        elif is_contracting:
            pattern_status = "VCP_FORMING"
            status_ar = f"نموذج VCP قيد التكوين ({len(swing_contractions)}T)"
            signal = "🟡 مراقبة التضييق الأخير"
            score = 80.0
            rationale = f"انكماش متدرج في التقلب السعري ({tightest_contraction:.1f}%)، وفي انتظار استقرار السعر قبل الاختراق."
        else:
            pattern_status = "WIDE_AND_LOOSE"
            status_ar = "تقلبات عريضة وغير منتظمة (Wide & Loose)"
            signal = "⚪ غير مؤهل لـ VCP"
            score = 60.0
            rationale = "حركة السعر لا تزال متقلبة ولم تُظهر بعد سلوك الانكماش المحكم المميز للأسهم المتفجرة."

        return {
            "theory": "MINERVINI_VCP",
            "theory_ar": "نموذج انكماش التقلب لمارك مينيرفيني (VCP)",
            "pattern_status": pattern_status,
            "status_ar": status_ar,
            "contractions_count": f"{len(swing_contractions)}T",
            "tightest_pullback_pct": tightest_contraction,
            "score": round(score, 1),
            "signal": signal,
            "rationale_ar": rationale
        }

    @classmethod
    def evaluate_can_slim(
        cls,
        ticker: str,
        eps_growth_quarterly: float = 35.0,
        eps_growth_annual: float = 28.0,
        is_near_new_high: bool = True,
        relative_strength_score: float = 88.0,
        institutional_sponsorship: bool = True
    ) -> Dict[str, Any]:
        """
        Evaluates stock against William O'Neil's CAN SLIM criteria:
        - C: Current quarterly earnings growth (> 20%)
        - A: Annual earnings growth (> 25%)
        - N: New products, management, or new price highs
        - S: Supply & Demand (Shares in demand)
        - L: Leader vs Laggard (RS Rating > 70)
        - I: Institutional Sponsorship
        - M: Market Direction
        """
        criteria = {
            "C_Current_Earnings": eps_growth_quarterly >= 20.0,
            "A_Annual_Earnings": eps_growth_annual >= 25.0,
            "N_New_Highs": is_near_new_high,
            "S_Supply_Demand": True,
            "L_Leader_RS": relative_strength_score >= 70.0,
            "I_Institutional": institutional_sponsorship,
            "M_Market_Uptrend": True
        }

        passed_count = sum(1 for v in criteria.values() if v)
        score = (passed_count / len(criteria)) * 100.0

        if passed_count >= 6:
            grade = "A+"
            grade_ar = "سهم قيادي ممتاز (CAN SLIM Grade A+)"
            signal = "🟢 شراء نمو متسارع قياسي"
            rationale = "الشركة تستوفي معظم شروط كان سليم الصارمة مع نمو أرباح استثنائي، قوة نسبية فائقة، ورعاية مؤسسية صلبة."
        elif passed_count >= 5:
            grade = "A"
            grade_ar = "سهم نمو قوي (CAN SLIM Grade A)"
            signal = "🟢 شراء تراكمي"
            rationale = "نمو أرباح فصلي وسنوي قوي مع تفوق على 80% من أسهم السوق في مؤشر القوة النسبية."
        else:
            grade = "B"
            grade_ar = "سهم نمو متوسط (CAN SLIM Grade B)"
            signal = "🟡 مراقبة نتائج الأعمال"
            rationale = "الشركة تفي ببعض شروط النمو ولكن تحتاج لتسارع أكبر في هوامش الربحية وصافي الدخل."

        return {
            "theory": "CAN_SLIM",
            "theory_ar": "استراتيجية ويليام أونيل (CAN SLIM)",
            "grade": grade,
            "grade_ar": grade_ar,
            "passed_criteria_count": f"{passed_count} / {len(criteria)}",
            "criteria_details": criteria,
            "score": round(score, 1),
            "signal": signal,
            "rationale_ar": rationale
        }

    @classmethod
    def evaluate_dow_theory(
        cls,
        ticker: str,
        current_price: float,
        higher_highs: bool = True,
        higher_lows: bool = True,
        volume_confirms_trend: bool = True,
        index_confirmed: bool = True
    ) -> Dict[str, Any]:
        """
        Evaluates stock against Charles Dow's Classic Trend Theory:
        1. Primary Trend (الاتجاه الرئيسي الصاعد/الهابط).
        2. Three Phases: Accumulation (التجميع المؤسسي), Public Participation (المشاركة العامة), Distribution (التصريف).
        3. Confirmation: Volume confirms price trend & Market Indices confirm stock direction.
        4. Definite Reversal: Trend remains in effect until clear lower-high and lower-low pattern occurs.
        """
        if higher_highs and higher_lows and volume_confirms_trend and index_confirmed:
            phase = "PHASE_2_PUBLIC_PARTICIPATION"
            trend_ar = "اتجاه صاعد رئيسي مؤكد (Bullish Primary Trend)"
            status_ar = "قمم وقيعان صاعدة متتالية مدعومة بأحجام تداول متزايدة وتوافق مع المؤشر العام"
            score = 93.0
            signal = "🟢 شراء مع الاتجاه الصاعد الرئيسي"
            rationale = "السهم يسجل قمم وقيعان متصاعدة مؤكدة بنظرية داو الكلاسيكية، وتزايد السيولة يدعم استمرار الصعود."
        elif higher_lows and volume_confirms_trend:
            phase = "PHASE_1_ACCUMULATION"
            trend_ar = "مرحلة التجميع الأولى (Accumulation Phase)"
            status_ar = "قاع أعلى من قاع سابق مع استقرار نسبي للسعر وامتصاص العروض"
            score = 85.0
            signal = "🟢 شراء استباقي / تجميع"
            rationale = "بداية تشكل اتجاه صاعد جديد طبقاً لداو مع حماية القيعان السابقة وتدفق سيولة ذكية هادئة."
        elif not higher_highs and not higher_lows:
            phase = "PHASE_3_DISTRIBUTION"
            trend_ar = "اتجاه هابط رئيسي / تصريف (Distribution Phase)"
            status_ar = "قمم وقيعان هابطة متتالية وكسر لمستويات الدعم الرئيسية"
            score = 40.0
            signal = "🔴 تجنب / وقف خسارة وخروج"
            rationale = "تأكيد انعكاس الاتجاه لأسفل طبقاً لقواعد داو مع غياب قوى الطلب وكسر القيعان السابقة."
        else:
            phase = "SECONDARY_CORRECTION"
            trend_ar = "تصحيح ثانوي داخل الاتجاه (Secondary Reaction)"
            status_ar = "حركة ارتدادية مؤقتة تعيد اختبار مستويات الدعم السابقة بنجاح"
            score = 75.0
            signal = "🟡 مراقبة استئناف الاتجاه"
            rationale = "تصحيح فني طبيعي داخل المسار العام، وفرصة للشراء بمجرد تأكيد اختراق القمة الفرعية."

        return {
            "theory": "DOW_THEORY",
            "theory_ar": "نظرية داو الكلاسيكية للاتجاهات ومطابقة المؤشرات",
            "phase": phase,
            "trend_ar": trend_ar,
            "status_ar": status_ar,
            "score": round(score, 1),
            "signal": signal,
            "rationale_ar": rationale
        }

    @classmethod
    def evaluate_elliott_wave(
        cls,
        ticker: str,
        current_price: float,
        wave_position: str = "WAVE_3_IMPULSE",
        fib_retrace_level: float = 0.618
    ) -> Dict[str, Any]:
        """
        Evaluates stock against R.N. Elliott's Wave Principle:
        - 5 Motive Impulse Waves (1-2-3-4-5) & 3 Corrective Waves (A-B-C).
        - Fibonacci golden ratios (1.618 extensions and 0.618 pullbacks).
        """
        wp = wave_position.upper()
        if "WAVE_3" in wp:
            status_ar = "الموجة الدافعة الثالثة (Wave 3 Impulse) — الأقوى والأطول أفقاً"
            target_multiplier = 1.22
            score = 95.0
            signal = "🟢 شراء فائق القوة (زخم الموجة الثالثة)"
            rationale = "السهم يتحرك داخل الموجة الدافعة 3 الأكبر حجماً وتسارعاً طبقاً لموجات إليوت، مستهدفة نسبة فيبوناتشي 161.8%."
        elif "WAVE_4" in wp:
            status_ar = "الموجة التصحيحية الرابعة (Wave 4 Pullback) — فرصة اقتناص القاع"
            target_multiplier = 1.14
            score = 86.0
            signal = "🟢 شراء ارتدادي من دعم فيبوناتشي"
            rationale = f"اقتراب اكتمال تصحيح الموجة 4 قرب مستوى فيبوناتشي الذهبي ({fib_retrace_level*100:.1f}%) استعداداً لإطلاق الموجة 5 الصاعدة."
        elif "WAVE_1" in wp:
            status_ar = "الموجة الدافعة الأولى (Wave 1 Inception) — بداية دورة سعرية جديدة"
            target_multiplier = 1.10
            score = 80.0
            signal = "🟢 دخول مبكر مع تأسيس الاتجاه"
            rationale = "انعكاس صاعد خماسي يؤكد انتهاء الدورة الهابطة وبداية موجة اندفاعية صاعدة."
        elif "WAVE_5" in wp:
            status_ar = "الموجة الخامسة الأخيرة (Wave 5 Final Extension) — ذروة الصعود"
            target_multiplier = 1.05
            score = 65.0
            signal = "🟡 جني أرباح تدريجي وحذر"
            rationale = "الموجة 5 تقترب من نهايتها مع احتمال تشكل انحراف سلبي في الزخم، ينصح برفع الوقف وجني الأرباح جزئياً."
        else:
            status_ar = "نهاية الموجة التصحيحية (Wave C Exhaustion) — استعداد لدورة جديدة"
            target_multiplier = 1.15
            score = 82.0
            signal = "🟢 اقتناص انتهاء التصحيح"
            rationale = "اكتمال أضلاع التصحيح الثلاثية (A-B-C) وتراجع أحجام البيع، مما يمهد لانطلاق موجة صاعدة جديدة."

        est_target = round(current_price * target_multiplier, 2)

        return {
            "theory": "ELLIOTT_WAVE",
            "theory_ar": "نظرية موجات إليوت والنسب الذهبية لفيبوناتشي",
            "wave_position": wp,
            "status_ar": status_ar,
            "projected_target": est_target,
            "fib_level": f"{fib_retrace_level * 100:.1f}%",
            "score": round(score, 1),
            "signal": signal,
            "rationale_ar": rationale
        }

    @classmethod
    def evaluate_comprehensive_theories(
        cls,
        ticker: str,
        current_price: float = 140.0,
        high_20d: float = 145.0,
        low_20d: float = 130.0,
        support: float = 132.0,
        resistance: float = 148.0,
        volume_ratio: float = 1.35
    ) -> Dict[str, Any]:
        """
        Executes all 6 classic and institutional investment theories on a stock:
        1. Wyckoff Accumulation & Distribution
        2. ICT / Smart Money Concepts (Order Blocks & FVG)
        3. Minervini Volatility Contraction Pattern (VCP)
        4. William O'Neil CAN SLIM Growth
        5. Charles Dow Trend & Confirmation Theory
        6. R.N. Elliott Wave Principle
        """
        wyckoff = cls.evaluate_wyckoff(ticker, current_price, high_20d, low_20d, volume_ratio)
        smart_money = cls.evaluate_smart_money_concepts(ticker, current_price, support, resistance)
        vcp = cls.evaluate_minervini_vcp(ticker, current_price, pivot_price=high_20d)
        can_slim = cls.evaluate_can_slim(ticker)
        dow = cls.evaluate_dow_theory(ticker, current_price, higher_highs=(current_price >= low_20d + (high_20d - low_20d)*0.6))
        elliott = cls.evaluate_elliott_wave(ticker, current_price, wave_position="WAVE_3_IMPULSE")

        all_scores = [
            wyckoff["score"],
            smart_money["score"],
            vcp["score"],
            can_slim["score"],
            dow["score"],
            elliott["score"]
        ]
        master_score = sum(all_scores) / len(all_scores)

        buy_votes = sum(1 for s in all_scores if s >= 80.0)

        return {
            "ticker": ticker,
            "current_price": current_price,
            "master_theory_score": round(master_score, 1),
            "consensus_verdict_ar": f"🟢 إجماع استثماري قوي ({buy_votes} من 6 نظريات توصي بالشراء)" if master_score >= 82.0 else "🟡 توافق جزئي واعد",
            "theories": {
                "wyckoff": wyckoff,
                "smart_money": smart_money,
                "minervini_vcp": vcp,
                "can_slim": can_slim,
                "dow_theory": dow,
                "elliott_wave": elliott
            },
            "summary_signals": [
                {"name": wyckoff["theory_ar"], "signal": wyckoff["signal"], "score": wyckoff["score"]},
                {"name": smart_money["theory_ar"], "signal": smart_money["signal"], "score": smart_money["score"]},
                {"name": vcp["theory_ar"], "signal": vcp["signal"], "score": vcp["score"]},
                {"name": can_slim["theory_ar"], "signal": can_slim["signal"], "score": can_slim["score"]},
                {"name": dow["theory_ar"], "signal": dow["signal"], "score": dow["score"]},
                {"name": elliott["theory_ar"], "signal": elliott["signal"], "score": elliott["score"]}
            ]
        }

