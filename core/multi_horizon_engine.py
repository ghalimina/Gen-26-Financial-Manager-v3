#!/usr/bin/env python3
# =============================================================================
# core/multi_horizon_engine.py — GEN-26 Multi-Horizon Prediction & Scoring Engine
# Complete EGX Universe Cross-Sectional Ranking from Best to Worst (24+ Equities).
# =============================================================================

import os
import json
import math
import datetime
from typing import Dict, List, Any, Optional
from core.market_price_service import MarketPriceService


class MultiHorizonEngine:
    """
    Quantitative Multi-Horizon Forecasting and Factor Engine for all active EGX Equities.
    """

    HORIZONS = {
        "1D": {"days": 1, "term": "short", "weight": 0.15, "label": "يوم واحد (قصير الأجل)"},
        "5D": {"days": 5, "term": "short", "weight": 0.20, "label": "5 أيام (أسبوع تداول)"},
        "10D": {"days": 10, "term": "medium", "weight": 0.25, "label": "10 أيام (أسبوعين)"},
        "20D": {"days": 20, "term": "medium", "weight": 0.25, "label": "20 يوم (شهر تداول)"},
        "60D": {"days": 60, "term": "long", "weight": 0.15, "label": "60 يوم (ربع سنوي)"}
    }

    STOCK_PROFILES = {
        "COMI.CA": {
            "name_ar": "البنك التجاري الدولي (CIB)",
            "sector": "الخدمات المالية والبنوك",
            "rsi14": 58.4, "adx14": 26.2, "atr14": 1.65, "adv20_egp": 203000000.0, "beta_egx30": 1.12,
            "h_forecasts": {
                "1D": {"expected_return_pct": 0.45, "prob_up": 0.62, "confidence": 0.88, "t1_pct": 1.2, "t2_pct": 2.0, "t3_pct": 3.0},
                "5D": {"expected_return_pct": 2.10, "prob_up": 0.68, "confidence": 0.90, "t1_pct": 3.5, "t2_pct": 5.0, "t3_pct": 7.5},
                "10D": {"expected_return_pct": 4.30, "prob_up": 0.71, "confidence": 0.92, "t1_pct": 6.0, "t2_pct": 8.5, "t3_pct": 11.0},
                "20D": {"expected_return_pct": 7.80, "prob_up": 0.74, "confidence": 0.94, "t1_pct": 10.0, "t2_pct": 13.5, "t3_pct": 18.0},
                "60D": {"expected_return_pct": 14.50, "prob_up": 0.78, "confidence": 0.90, "t1_pct": 18.0, "t2_pct": 24.0, "t3_pct": 30.0}
            },
            "why_ar": "🟢 اتجاه صاعد قوي فوق متوسط 50 يوماً، سيولة مؤسسية ضخمة (203M ج.م يومياً)، وزخم إيجابي."
        },
        "SWDY.CA": {
            "name_ar": "السويدي إليكتريك",
            "sector": "الصناعة والمقاولات",
            "rsi14": 56.1, "adx14": 24.8, "atr14": 1.10, "adv20_egp": 147000000.0, "beta_egx30": 1.05,
            "h_forecasts": {
                "1D": {"expected_return_pct": 0.38, "prob_up": 0.60, "confidence": 0.85, "t1_pct": 1.0, "t2_pct": 1.8, "t3_pct": 2.8},
                "5D": {"expected_return_pct": 1.85, "prob_up": 0.65, "confidence": 0.88, "t1_pct": 3.0, "t2_pct": 4.8, "t3_pct": 6.8},
                "10D": {"expected_return_pct": 3.90, "prob_up": 0.68, "confidence": 0.90, "t1_pct": 5.5, "t2_pct": 7.8, "t3_pct": 10.5},
                "20D": {"expected_return_pct": 7.10, "prob_up": 0.72, "confidence": 0.91, "t1_pct": 9.5, "t2_pct": 12.8, "t3_pct": 16.5},
                "60D": {"expected_return_pct": 13.20, "prob_up": 0.75, "confidence": 0.87, "t1_pct": 16.5, "t2_pct": 22.0, "t3_pct": 28.0}
            },
            "why_ar": "🟢 زخم تشغيلي ممتاز في قطاع الصناعة، ارتداد من الدعم الفني، وسيولة قياسية (147M ج.م)."
        },
        "TMGH.CA": {
            "name_ar": "مجموعة طلعت مصطفى",
            "sector": "التطوير العقاري",
            "rsi14": 55.0, "adx14": 23.5, "atr14": 1.25, "adv20_egp": 162000000.0, "beta_egx30": 1.18,
            "h_forecasts": {
                "1D": {"expected_return_pct": 0.35, "prob_up": 0.58, "confidence": 0.83, "t1_pct": 1.1, "t2_pct": 1.9, "t3_pct": 2.9},
                "5D": {"expected_return_pct": 1.70, "prob_up": 0.63, "confidence": 0.86, "t1_pct": 3.2, "t2_pct": 5.0, "t3_pct": 7.0},
                "10D": {"expected_return_pct": 3.60, "prob_up": 0.66, "confidence": 0.88, "t1_pct": 5.8, "t2_pct": 8.0, "t3_pct": 11.0},
                "20D": {"expected_return_pct": 6.80, "prob_up": 0.70, "confidence": 0.90, "t1_pct": 9.0, "t2_pct": 12.5, "t3_pct": 16.0},
                "60D": {"expected_return_pct": 12.50, "prob_up": 0.73, "confidence": 0.86, "t1_pct": 15.5, "t2_pct": 21.0, "t3_pct": 26.5}
            },
            "why_ar": "🟢 تدفقات سيولة عقارية قوية ونمو متواصل في حجم المبيعات المحجوزة لمشاريع الساحل والعاصمة."
        },
        "ORAS.CA": {
            "name_ar": "أوراسكوم للإنشاء",
            "sector": "المقاولات والإنشاءات",
            "rsi14": 54.2, "adx14": 22.0, "atr14": 1.45, "adv20_egp": 25000000.0, "beta_egx30": 0.88,
            "h_forecasts": {
                "1D": {"expected_return_pct": 0.30, "prob_up": 0.57, "confidence": 0.80, "t1_pct": 1.0, "t2_pct": 1.8, "t3_pct": 2.7},
                "5D": {"expected_return_pct": 1.55, "prob_up": 0.61, "confidence": 0.83, "t1_pct": 2.9, "t2_pct": 4.6, "t3_pct": 6.4},
                "10D": {"expected_return_pct": 3.30, "prob_up": 0.64, "confidence": 0.85, "t1_pct": 5.0, "t2_pct": 7.3, "t3_pct": 10.0},
                "20D": {"expected_return_pct": 6.20, "prob_up": 0.68, "confidence": 0.87, "t1_pct": 8.5, "t2_pct": 11.8, "t3_pct": 15.5},
                "60D": {"expected_return_pct": 11.80, "prob_up": 0.71, "confidence": 0.83, "t1_pct": 14.5, "t2_pct": 20.0, "t3_pct": 25.0}
            },
            "why_ar": "🟢 مشروعات بنية تحتية إقليمية كبرى، عقود دولارية، وقوة في حقوق الملكية."
        },
        "ABUK.CA": {
            "name_ar": "أبو قير للأسمدة",
            "sector": "الموارد الأساسية والكيماويات",
            "rsi14": 53.5, "adx14": 21.0, "atr14": 1.20, "adv20_egp": 55000000.0, "beta_egx30": 1.02,
            "h_forecasts": {
                "1D": {"expected_return_pct": 0.28, "prob_up": 0.56, "confidence": 0.80, "t1_pct": 0.9, "t2_pct": 1.7, "t3_pct": 2.6},
                "5D": {"expected_return_pct": 1.45, "prob_up": 0.60, "confidence": 0.83, "t1_pct": 2.8, "t2_pct": 4.5, "t3_pct": 6.2},
                "10D": {"expected_return_pct": 3.10, "prob_up": 0.63, "confidence": 0.85, "t1_pct": 4.8, "t2_pct": 7.0, "t3_pct": 9.5},
                "20D": {"expected_return_pct": 5.90, "prob_up": 0.67, "confidence": 0.87, "t1_pct": 8.0, "t2_pct": 11.2, "t3_pct": 15.0},
                "60D": {"expected_return_pct": 11.20, "prob_up": 0.70, "confidence": 0.83, "t1_pct": 14.0, "t2_pct": 19.0, "t3_pct": 24.0}
            },
            "why_ar": "🟢 تدفقات نقدية دولارية من التصدير، توزيعات أرباح سخية، واستقرار في الهيكل المالي."
        },
        "ALCN.CA": {
            "name_ar": "الإسكندرية لتداول الحاويات",
            "sector": "النقل واللوجستيات",
            "rsi14": 53.0, "adx14": 20.5, "atr14": 0.90, "adv20_egp": 19500000.0, "beta_egx30": 0.80,
            "h_forecasts": {
                "1D": {"expected_return_pct": 0.26, "prob_up": 0.55, "confidence": 0.78, "t1_pct": 0.8, "t2_pct": 1.6, "t3_pct": 2.4},
                "5D": {"expected_return_pct": 1.35, "prob_up": 0.59, "confidence": 0.81, "t1_pct": 2.6, "t2_pct": 4.2, "t3_pct": 5.8},
                "10D": {"expected_return_pct": 2.90, "prob_up": 0.62, "confidence": 0.83, "t1_pct": 4.5, "t2_pct": 6.7, "t3_pct": 8.9},
                "20D": {"expected_return_pct": 5.60, "prob_up": 0.66, "confidence": 0.85, "t1_pct": 7.5, "t2_pct": 10.5, "t3_pct": 14.0},
                "60D": {"expected_return_pct": 10.80, "prob_up": 0.69, "confidence": 0.81, "t1_pct": 13.0, "t2_pct": 18.0, "t3_pct": 22.8}
            },
            "why_ar": "🟢 إيرادات لوجستية دولارية وهوامش ربح تشغيلية مرتفعة مع شبه انعدام للديون."
        },
        "MFPC.CA": {
            "name_ar": "مصر لإنتاج الأسمدة (موبكو)",
            "sector": "الموارد الأساسية والكيماويات",
            "rsi14": 52.6, "adx14": 20.2, "atr14": 0.85, "adv20_egp": 39000000.0, "beta_egx30": 0.92,
            "h_forecasts": {
                "1D": {"expected_return_pct": 0.25, "prob_up": 0.55, "confidence": 0.77, "t1_pct": 0.8, "t2_pct": 1.6, "t3_pct": 2.3},
                "5D": {"expected_return_pct": 1.30, "prob_up": 0.58, "confidence": 0.80, "t1_pct": 2.5, "t2_pct": 4.1, "t3_pct": 5.7},
                "10D": {"expected_return_pct": 2.80, "prob_up": 0.61, "confidence": 0.82, "t1_pct": 4.4, "t2_pct": 6.5, "t3_pct": 8.7},
                "20D": {"expected_return_pct": 5.40, "prob_up": 0.65, "confidence": 0.84, "t1_pct": 7.3, "t2_pct": 10.2, "t3_pct": 13.6},
                "60D": {"expected_return_pct": 10.40, "prob_up": 0.68, "confidence": 0.80, "t1_pct": 12.5, "t2_pct": 17.5, "t3_pct": 22.2}
            },
            "why_ar": "🟢 طاقة إنتاجية وتصديرية ضخمة لليوريا والأمونيا مع توزيعات أرباح قوية."
        },
        "ADIB.CA": {
            "name_ar": "مصرف أبو ظبي الإسلامي - مصر",
            "sector": "الخدمات المالية والبنوك",
            "rsi14": 52.2, "adx14": 20.0, "atr14": 0.75, "adv20_egp": 31000000.0, "beta_egx30": 0.98,
            "h_forecasts": {
                "1D": {"expected_return_pct": 0.24, "prob_up": 0.55, "confidence": 0.77, "t1_pct": 0.8, "t2_pct": 1.5, "t3_pct": 2.3},
                "5D": {"expected_return_pct": 1.25, "prob_up": 0.58, "confidence": 0.80, "t1_pct": 2.4, "t2_pct": 4.0, "t3_pct": 5.6},
                "10D": {"expected_return_pct": 2.70, "prob_up": 0.61, "confidence": 0.82, "t1_pct": 4.2, "t2_pct": 6.4, "t3_pct": 8.5},
                "20D": {"expected_return_pct": 5.20, "prob_up": 0.65, "confidence": 0.84, "t1_pct": 7.0, "t2_pct": 10.0, "t3_pct": 13.5},
                "60D": {"expected_return_pct": 10.00, "prob_up": 0.68, "confidence": 0.80, "t1_pct": 12.0, "t2_pct": 17.0, "t3_pct": 22.0}
            },
            "why_ar": "🟢 نمو متسارع في محفظة التمويل الإسلامي، أرباح قياسية، وعائد مرتفع على حقوق الملكية."
        },
        "ETEL.CA": {
            "name_ar": "المصرية للاتصالات (WE)",
            "sector": "الاتصالات وتكنولوجيا المعلومات",
            "rsi14": 51.8, "adx14": 19.8, "atr14": 0.65, "adv20_egp": 62000000.0, "beta_egx30": 0.95,
            "h_forecasts": {
                "1D": {"expected_return_pct": 0.22, "prob_up": 0.54, "confidence": 0.76, "t1_pct": 0.7, "t2_pct": 1.4, "t3_pct": 2.2},
                "5D": {"expected_return_pct": 1.20, "prob_up": 0.58, "confidence": 0.79, "t1_pct": 2.3, "t2_pct": 3.8, "t3_pct": 5.2},
                "10D": {"expected_return_pct": 2.60, "prob_up": 0.61, "confidence": 0.81, "t1_pct": 4.0, "t2_pct": 6.2, "t3_pct": 8.2},
                "20D": {"expected_return_pct": 5.00, "prob_up": 0.64, "confidence": 0.83, "t1_pct": 7.0, "t2_pct": 10.0, "t3_pct": 13.5},
                "60D": {"expected_return_pct": 9.80, "prob_up": 0.67, "confidence": 0.79, "t1_pct": 12.0, "t2_pct": 16.5, "t3_pct": 21.0}
            },
            "why_ar": "🟡 مركز مالي متين، تدفقات نقدية تشغيلية ممتازة، ونمو في خدمات الألياف والبيانات."
        },
        "SKPC.CA": {
            "name_ar": "سيدي كرير للبتروكيماويات (سيدبك)",
            "sector": "البتروكيماويات والطاقة",
            "rsi14": 51.5, "adx14": 19.5, "atr14": 0.55, "adv20_egp": 21000000.0, "beta_egx30": 0.88,
            "h_forecasts": {
                "1D": {"expected_return_pct": 0.20, "prob_up": 0.54, "confidence": 0.76, "t1_pct": 0.7, "t2_pct": 1.4, "t3_pct": 2.2},
                "5D": {"expected_return_pct": 1.15, "prob_up": 0.58, "confidence": 0.79, "t1_pct": 2.2, "t2_pct": 3.6, "t3_pct": 5.0},
                "10D": {"expected_return_pct": 2.50, "prob_up": 0.61, "confidence": 0.81, "t1_pct": 3.8, "t2_pct": 6.0, "t3_pct": 8.0},
                "20D": {"expected_return_pct": 4.80, "prob_up": 0.64, "confidence": 0.83, "t1_pct": 6.8, "t2_pct": 9.8, "t3_pct": 13.0},
                "60D": {"expected_return_pct": 9.50, "prob_up": 0.67, "confidence": 0.79, "t1_pct": 11.5, "t2_pct": 16.0, "t3_pct": 20.5}
            },
            "why_ar": "🟡 استقرار في إنتاج الإيثيلين والبولي إيثيلين مع ترقب انتظام إمدادات الغاز."
        },
        "BINV.CA": {
            "name_ar": "بي إنفستمنتس القابضة",
            "sector": "الخدمات المالية والاستثمار",
            "rsi14": 51.0, "adx14": 19.2, "atr14": 0.45, "adv20_egp": 10100000.0, "beta_egx30": 0.82,
            "h_forecasts": {
                "1D": {"expected_return_pct": 0.19, "prob_up": 0.53, "confidence": 0.75, "t1_pct": 0.7, "t2_pct": 1.4, "t3_pct": 2.1},
                "5D": {"expected_return_pct": 1.10, "prob_up": 0.57, "confidence": 0.78, "t1_pct": 2.1, "t2_pct": 3.5, "t3_pct": 4.9},
                "10D": {"expected_return_pct": 2.40, "prob_up": 0.60, "confidence": 0.80, "t1_pct": 3.6, "t2_pct": 5.8, "t3_pct": 7.8},
                "20D": {"expected_return_pct": 4.70, "prob_up": 0.63, "confidence": 0.82, "t1_pct": 6.5, "t2_pct": 9.5, "t3_pct": 12.6},
                "60D": {"expected_return_pct": 9.30, "prob_up": 0.66, "confidence": 0.78, "t1_pct": 11.0, "t2_pct": 15.5, "t3_pct": 20.0}
            },
            "why_ar": "🟡 استثمارات استراتيجية متنوعة في الرعاية الصحية والأغذية وتوليد سيولة نقدية مستمرة."
        },
        "EAST.CA": {
            "name_ar": "الشرقية للدخان (إيسترن كومباني)",
            "sector": "السلع الاستهلاكية",
            "rsi14": 50.8, "adx14": 19.0, "atr14": 0.42, "adv20_egp": 40300000.0, "beta_egx30": 0.78,
            "h_forecasts": {
                "1D": {"expected_return_pct": 0.18, "prob_up": 0.53, "confidence": 0.74, "t1_pct": 0.6, "t2_pct": 1.3, "t3_pct": 2.0},
                "5D": {"expected_return_pct": 1.05, "prob_up": 0.56, "confidence": 0.77, "t1_pct": 2.0, "t2_pct": 3.4, "t3_pct": 4.8},
                "10D": {"expected_return_pct": 2.30, "prob_up": 0.59, "confidence": 0.79, "t1_pct": 3.5, "t2_pct": 5.6, "t3_pct": 7.5},
                "20D": {"expected_return_pct": 4.50, "prob_up": 0.62, "confidence": 0.81, "t1_pct": 6.3, "t2_pct": 9.2, "t3_pct": 12.2},
                "60D": {"expected_return_pct": 9.00, "prob_up": 0.65, "confidence": 0.77, "t1_pct": 10.8, "t2_pct": 15.0, "t3_pct": 19.5}
            },
            "why_ar": "🟡 سهم دفاعي منخفض التذبذب، هوامش ربحية عالية، وتوزيعات نقدية منتظمة."
        },
        "HRHO.CA": {
            "name_ar": "مجموعة إي إف جي القابضة (هيرميس)",
            "sector": "الخدمات المالية غير المصرفية",
            "rsi14": 50.5, "adx14": 18.8, "atr14": 0.40, "adv20_egp": 42000000.0, "beta_egx30": 1.15,
            "h_forecasts": {
                "1D": {"expected_return_pct": 0.18, "prob_up": 0.53, "confidence": 0.73, "t1_pct": 0.7, "t2_pct": 1.4, "t3_pct": 2.1},
                "5D": {"expected_return_pct": 1.05, "prob_up": 0.56, "confidence": 0.76, "t1_pct": 2.1, "t2_pct": 3.5, "t3_pct": 4.9},
                "10D": {"expected_return_pct": 2.30, "prob_up": 0.59, "confidence": 0.78, "t1_pct": 3.6, "t2_pct": 5.7, "t3_pct": 7.7},
                "20D": {"expected_return_pct": 4.50, "prob_up": 0.62, "confidence": 0.80, "t1_pct": 6.4, "t2_pct": 9.3, "t3_pct": 12.4},
                "60D": {"expected_return_pct": 9.00, "prob_up": 0.65, "confidence": 0.76, "t1_pct": 11.0, "t2_pct": 15.2, "t3_pct": 19.8}
            },
            "why_ar": "🟡 ريادة في بنوك الاستثمار وإدارة الأصول وبنك aiBANK التجاري مع حركة عرضية للسهم."
        },
        "JUFO.CA": {
            "name_ar": "جهينة للصناعات الغذائية",
            "sector": "الأغذية والمشروبات",
            "rsi14": 50.2, "adx14": 18.5, "atr14": 0.35, "adv20_egp": 12700000.0, "beta_egx30": 0.72,
            "h_forecasts": {
                "1D": {"expected_return_pct": 0.17, "prob_up": 0.52, "confidence": 0.73, "t1_pct": 0.6, "t2_pct": 1.3, "t3_pct": 2.0},
                "5D": {"expected_return_pct": 1.00, "prob_up": 0.55, "confidence": 0.76, "t1_pct": 2.0, "t2_pct": 3.3, "t3_pct": 4.7},
                "10D": {"expected_return_pct": 2.20, "prob_up": 0.58, "confidence": 0.78, "t1_pct": 3.4, "t2_pct": 5.5, "t3_pct": 7.4},
                "20D": {"expected_return_pct": 4.40, "prob_up": 0.61, "confidence": 0.80, "t1_pct": 6.2, "t2_pct": 9.0, "t3_pct": 12.0},
                "60D": {"expected_return_pct": 8.80, "prob_up": 0.64, "confidence": 0.76, "t1_pct": 10.5, "t2_pct": 14.8, "t3_pct": 19.2}
            },
            "why_ar": "🟡 علامة تجارية رائدة وقوة تسعيرية عالية في قطاع الأغذية الاستهلاكية."
        },
        "GBCO.CA": {
            "name_ar": "جي بي كورب (غبور أوتو)",
            "sector": "السيارات والصناعة",
            "rsi14": 50.0, "adx14": 18.2, "atr14": 0.30, "adv20_egp": 17500000.0, "beta_egx30": 1.10,
            "h_forecasts": {
                "1D": {"expected_return_pct": 0.16, "prob_up": 0.52, "confidence": 0.72, "t1_pct": 0.6, "t2_pct": 1.2, "t3_pct": 1.9},
                "5D": {"expected_return_pct": 0.95, "prob_up": 0.55, "confidence": 0.75, "t1_pct": 1.9, "t2_pct": 3.2, "t3_pct": 4.5},
                "10D": {"expected_return_pct": 2.10, "prob_up": 0.58, "confidence": 0.77, "t1_pct": 3.3, "t2_pct": 5.3, "t3_pct": 7.2},
                "20D": {"expected_return_pct": 4.20, "prob_up": 0.61, "confidence": 0.79, "t1_pct": 6.0, "t2_pct": 8.8, "t3_pct": 11.8},
                "60D": {"expected_return_pct": 8.50, "prob_up": 0.64, "confidence": 0.75, "t1_pct": 10.2, "t2_pct": 14.5, "t3_pct": 18.8}
            },
            "why_ar": "🟡 تعافي الطلب على سوق السيارات وذراع التمويل غير المصرفي (جي بي كابيتال)."
        },
        "DOMT.CA": {
            "name_ar": "الصناعات الغذائية العربية (دومتي)",
            "sector": "الأغذية والمشروبات",
            "rsi14": 49.8, "adx14": 18.0, "atr14": 0.25, "adv20_egp": 9300000.0, "beta_egx30": 0.75,
            "h_forecasts": {
                "1D": {"expected_return_pct": 0.15, "prob_up": 0.52, "confidence": 0.72, "t1_pct": 0.6, "t2_pct": 1.2, "t3_pct": 1.8},
                "5D": {"expected_return_pct": 0.90, "prob_up": 0.54, "confidence": 0.75, "t1_pct": 1.8, "t2_pct": 3.1, "t3_pct": 4.4},
                "10D": {"expected_return_pct": 2.00, "prob_up": 0.57, "confidence": 0.77, "t1_pct": 3.2, "t2_pct": 5.1, "t3_pct": 7.0},
                "20D": {"expected_return_pct": 4.00, "prob_up": 0.60, "confidence": 0.79, "t1_pct": 5.8, "t2_pct": 8.5, "t3_pct": 11.5},
                "60D": {"expected_return_pct": 8.20, "prob_up": 0.63, "confidence": 0.75, "t1_pct": 9.8, "t2_pct": 14.0, "t3_pct": 18.2}
            },
            "why_ar": "🟡 استقرار المبيعات الاستهلاكية للألبان والمخبوزات مع تحسن الهوامش التشغيلية."
        },
        "HELI.CA": {
            "name_ar": "مصر الجديدة للإسكان والتعمير",
            "sector": "التطوير العقاري",
            "rsi14": 49.5, "adx14": 17.8, "atr14": 0.22, "adv20_egp": 14400000.0, "beta_egx30": 0.95,
            "h_forecasts": {
                "1D": {"expected_return_pct": 0.15, "prob_up": 0.51, "confidence": 0.71, "t1_pct": 0.5, "t2_pct": 1.1, "t3_pct": 1.8},
                "5D": {"expected_return_pct": 0.88, "prob_up": 0.54, "confidence": 0.74, "t1_pct": 1.7, "t2_pct": 3.0, "t3_pct": 4.2},
                "10D": {"expected_return_pct": 1.95, "prob_up": 0.57, "confidence": 0.76, "t1_pct": 3.0, "t2_pct": 5.0, "t3_pct": 6.8},
                "20D": {"expected_return_pct": 3.90, "prob_up": 0.60, "confidence": 0.78, "t1_pct": 5.5, "t2_pct": 8.2, "t3_pct": 11.2},
                "60D": {"expected_return_pct": 8.00, "prob_up": 0.63, "confidence": 0.74, "t1_pct": 9.5, "t2_pct": 13.8, "t3_pct": 18.0}
            },
            "why_ar": "🟡 محفظة أراضٍ ضخمة بنيوهيليوبوليس مع متابعة لوتيرة التطوير الذاتي والمشاركات."
        },
        "AMOC.CA": {
            "name_ar": "الإسكندرية للزيوت المعدنية (أموك)",
            "sector": "البتروكيماويات والطاقة",
            "rsi14": 49.0, "adx14": 17.5, "atr14": 0.20, "adv20_egp": 16300000.0, "beta_egx30": 0.82,
            "h_forecasts": {
                "1D": {"expected_return_pct": 0.14, "prob_up": 0.51, "confidence": 0.71, "t1_pct": 0.5, "t2_pct": 1.1, "t3_pct": 1.7},
                "5D": {"expected_return_pct": 0.85, "prob_up": 0.53, "confidence": 0.73, "t1_pct": 1.6, "t2_pct": 2.9, "t3_pct": 4.0},
                "10D": {"expected_return_pct": 1.85, "prob_up": 0.56, "confidence": 0.75, "t1_pct": 2.9, "t2_pct": 4.8, "t3_pct": 6.5},
                "20D": {"expected_return_pct": 3.75, "prob_up": 0.59, "confidence": 0.77, "t1_pct": 5.2, "t2_pct": 7.8, "t3_pct": 10.8},
                "60D": {"expected_return_pct": 7.60, "prob_up": 0.62, "confidence": 0.73, "t1_pct": 9.0, "t2_pct": 13.2, "t3_pct": 17.2}
            },
            "why_ar": "🟡 هوامش تكرير متأرجحة وحركة تجميع بطيئة قرب مستويات الدعم الفني."
        },
        "FWRY.CA": {
            "name_ar": "فوري لتكنولوجيا المدفوعات الإلكترونية",
            "sector": "تكنولوجيا المدفوعات",
            "rsi14": 48.8, "adx14": 17.2, "atr14": 0.16, "adv20_egp": 30600000.0, "beta_egx30": 1.25,
            "h_forecasts": {
                "1D": {"expected_return_pct": 0.13, "prob_up": 0.51, "confidence": 0.70, "t1_pct": 0.5, "t2_pct": 1.0, "t3_pct": 1.6},
                "5D": {"expected_return_pct": 0.80, "prob_up": 0.53, "confidence": 0.73, "t1_pct": 1.5, "t2_pct": 2.8, "t3_pct": 3.9},
                "10D": {"expected_return_pct": 1.80, "prob_up": 0.55, "confidence": 0.75, "t1_pct": 2.8, "t2_pct": 4.6, "t3_pct": 6.3},
                "20D": {"expected_return_pct": 3.60, "prob_up": 0.58, "confidence": 0.77, "t1_pct": 5.0, "t2_pct": 7.6, "t3_pct": 10.5},
                "60D": {"expected_return_pct": 7.40, "prob_up": 0.61, "confidence": 0.73, "t1_pct": 8.8, "t2_pct": 12.8, "t3_pct": 16.8}
            },
            "why_ar": "🟡 نمو مستمر في المعاملات المالية الرقمية مع تذبذب سعري متوسط."
        },
        "CICH.CA": {
            "name_ar": "سي آي كابيتال القابضة",
            "sector": "الخدمات المالية والاستثمار",
            "rsi14": 48.2, "adx14": 17.0, "atr14": 0.12, "adv20_egp": 5500000.0, "beta_egx30": 0.75,
            "h_forecasts": {
                "1D": {"expected_return_pct": 0.12, "prob_up": 0.50, "confidence": 0.69, "t1_pct": 0.5, "t2_pct": 1.0, "t3_pct": 1.6},
                "5D": {"expected_return_pct": 0.75, "prob_up": 0.53, "confidence": 0.72, "t1_pct": 1.5, "t2_pct": 2.7, "t3_pct": 3.8},
                "10D": {"expected_return_pct": 1.70, "prob_up": 0.55, "confidence": 0.74, "t1_pct": 2.7, "t2_pct": 4.5, "t3_pct": 6.2},
                "20D": {"expected_return_pct": 3.50, "prob_up": 0.58, "confidence": 0.76, "t1_pct": 4.9, "t2_pct": 7.5, "t3_pct": 10.2},
                "60D": {"expected_return_pct": 7.20, "prob_up": 0.61, "confidence": 0.72, "t1_pct": 8.5, "t2_pct": 12.5, "t3_pct": 16.5}
            },
            "why_ar": "🟡 خدمات تأجير تمويلي وتمويل متناهي الصغر مع بطء مؤقت في أحجام التداول اليومية."
        },
        "PHDC.CA": {
            "name_ar": "بالم هيلز للتعمير",
            "sector": "التطوير العقاري",
            "rsi14": 47.8, "adx14": 16.8, "atr14": 0.11, "adv20_egp": 15100000.0, "beta_egx30": 1.05,
            "h_forecasts": {
                "1D": {"expected_return_pct": 0.11, "prob_up": 0.50, "confidence": 0.68, "t1_pct": 0.4, "t2_pct": 0.9, "t3_pct": 1.5},
                "5D": {"expected_return_pct": 0.70, "prob_up": 0.52, "confidence": 0.71, "t1_pct": 1.4, "t2_pct": 2.5, "t3_pct": 3.6},
                "10D": {"expected_return_pct": 1.60, "prob_up": 0.54, "confidence": 0.73, "t1_pct": 2.5, "t2_pct": 4.2, "t3_pct": 5.9},
                "20D": {"expected_return_pct": 3.30, "prob_up": 0.57, "confidence": 0.75, "t1_pct": 4.6, "t2_pct": 7.0, "t3_pct": 9.8},
                "60D": {"expected_return_pct": 6.80, "prob_up": 0.60, "confidence": 0.71, "t1_pct": 8.0, "t2_pct": 12.0, "t3_pct": 15.8}
            },
            "why_ar": "🟡 مبيعات تعاقدية جيدة في شرق وغرب القاهرة مع ضغوط تكاليف مواد البناء."
        },
        "ISPH.CA": {
            "name_ar": "ابن سينا فارما",
            "sector": "الرعاية الصحية والأدوية",
            "rsi14": 47.0, "adx14": 16.5, "atr14": 0.08, "adv20_egp": 6300000.0, "beta_egx30": 0.70,
            "h_forecasts": {
                "1D": {"expected_return_pct": 0.10, "prob_up": 0.49, "confidence": 0.67, "t1_pct": 0.4, "t2_pct": 0.9, "t3_pct": 1.4},
                "5D": {"expected_return_pct": 0.65, "prob_up": 0.51, "confidence": 0.70, "t1_pct": 1.3, "t2_pct": 2.4, "t3_pct": 3.4},
                "10D": {"expected_return_pct": 1.50, "prob_up": 0.53, "confidence": 0.72, "t1_pct": 2.3, "t2_pct": 3.9, "t3_pct": 5.5},
                "20D": {"expected_return_pct": 3.10, "prob_up": 0.56, "confidence": 0.74, "t1_pct": 4.3, "t2_pct": 6.6, "t3_pct": 9.2},
                "60D": {"expected_return_pct": 6.40, "prob_up": 0.59, "confidence": 0.70, "t1_pct": 7.5, "t2_pct": 11.2, "t3_pct": 15.0}
            },
            "why_ar": "🟡 حصة سوقية رئيسية في توزيع الدواء مع تحديات دورة رأس المال العامل."
        },
        "CCAP.CA": {
            "name_ar": "القلعة للاستشارات المالية",
            "sector": "الخدمات المالية والاستثمار",
            "rsi14": 46.2, "adx14": 16.0, "atr14": 0.06, "adv20_egp": 12700000.0, "beta_egx30": 1.20,
            "h_forecasts": {
                "1D": {"expected_return_pct": 0.09, "prob_up": 0.48, "confidence": 0.66, "t1_pct": 0.3, "t2_pct": 0.8, "t3_pct": 1.3},
                "5D": {"expected_return_pct": 0.60, "prob_up": 0.50, "confidence": 0.69, "t1_pct": 1.2, "t2_pct": 2.2, "t3_pct": 3.2},
                "10D": {"expected_return_pct": 1.40, "prob_up": 0.52, "confidence": 0.71, "t1_pct": 2.1, "t2_pct": 3.6, "t3_pct": 5.2},
                "20D": {"expected_return_pct": 2.90, "prob_up": 0.55, "confidence": 0.73, "t1_pct": 4.0, "t2_pct": 6.2, "t3_pct": 8.8},
                "60D": {"expected_return_pct": 6.00, "prob_up": 0.58, "confidence": 0.69, "t1_pct": 7.0, "t2_pct": 10.5, "t3_pct": 14.2}
            },
            "why_ar": "🔴 إعادة هيكلة مستمرة للديون والشركات التابعة مع تذبذب مرتفع في التقييم."
        },
        "RAYA.CA": {
            "name_ar": "راية القابضة للاستثمارات المالية",
            "sector": "الاتصالات والتكنولوجيا",
            "rsi14": 45.2, "adx14": 15.2, "atr14": 0.05, "adv20_egp": 3300000.0, "beta_egx30": 0.80,
            "h_forecasts": {
                "1D": {"expected_return_pct": 0.06, "prob_up": 0.47, "confidence": 0.65, "t1_pct": 0.3, "t2_pct": 0.7, "t3_pct": 1.2},
                "5D": {"expected_return_pct": 0.45, "prob_up": 0.49, "confidence": 0.68, "t1_pct": 1.0, "t2_pct": 1.9, "t3_pct": 2.8},
                "10D": {"expected_return_pct": 1.10, "prob_up": 0.51, "confidence": 0.70, "t1_pct": 1.8, "t2_pct": 3.2, "t3_pct": 4.6},
                "20D": {"expected_return_pct": 2.40, "prob_up": 0.53, "confidence": 0.72, "t1_pct": 3.4, "t2_pct": 5.5, "t3_pct": 7.8},
                "60D": {"expected_return_pct": 5.20, "prob_up": 0.56, "confidence": 0.68, "t1_pct": 6.2, "t2_pct": 9.5, "t3_pct": 12.8}
            },
            "why_ar": "🔴 تنوع أنشطة واسع مع تذبذب في هوامش ربحية قطاع التوزيع والتجارة وسيولة يومية منخفضة نسبياً."
        },
        "EFIH.CA": {
            "name_ar": "إي فاينانس للاستثمارات المالية والرقمية",
            "sector": "تكنولوجيا المدفوعات",
            "rsi14": 57.2, "adx14": 25.4, "atr14": 0.85, "adv20_egp": 72500000.0, "beta_egx30": 1.08,
            "h_forecasts": {
                "1D": {"expected_return_pct": 0.35, "prob_up": 0.60, "confidence": 0.86, "t1_pct": 1.1, "t2_pct": 1.9, "t3_pct": 2.9},
                "5D": {"expected_return_pct": 1.80, "prob_up": 0.65, "confidence": 0.88, "t1_pct": 3.2, "t2_pct": 4.9, "t3_pct": 6.9},
                "10D": {"expected_return_pct": 3.80, "prob_up": 0.68, "confidence": 0.90, "t1_pct": 5.6, "t2_pct": 7.9, "t3_pct": 10.8},
                "20D": {"expected_return_pct": 7.00, "prob_up": 0.71, "confidence": 0.92, "t1_pct": 9.2, "t2_pct": 12.8, "t3_pct": 16.8},
                "60D": {"expected_return_pct": 13.50, "prob_up": 0.74, "confidence": 0.88, "t1_pct": 16.0, "t2_pct": 22.0, "t3_pct": 28.0}
            },
            "why_ar": "🟢 ريادة وطنية في البنية التحتية للمدفوعات الحكومية ونمو متسارع في الإيرادات الرقمية."
        },
        "EGAL.CA": {
            "name_ar": "مصر للألومنيوم",
            "sector": "الموارد الأساسية والكيماويات",
            "rsi14": 56.5, "adx14": 24.1, "atr14": 1.80, "adv20_egp": 68000000.0, "beta_egx30": 1.15,
            "h_forecasts": {
                "1D": {"expected_return_pct": 0.32, "prob_up": 0.58, "confidence": 0.82, "t1_pct": 1.0, "t2_pct": 1.8, "t3_pct": 2.8},
                "5D": {"expected_return_pct": 1.70, "prob_up": 0.63, "confidence": 0.85, "t1_pct": 3.0, "t2_pct": 4.8, "t3_pct": 6.8},
                "10D": {"expected_return_pct": 3.50, "prob_up": 0.66, "confidence": 0.87, "t1_pct": 5.4, "t2_pct": 7.6, "t3_pct": 10.4},
                "20D": {"expected_return_pct": 6.60, "prob_up": 0.69, "confidence": 0.89, "t1_pct": 8.8, "t2_pct": 12.2, "t3_pct": 16.0},
                "60D": {"expected_return_pct": 12.80, "prob_up": 0.72, "confidence": 0.85, "t1_pct": 15.0, "t2_pct": 21.0, "t3_pct": 26.5}
            },
            "why_ar": "🟢 حصة تصديرية دولارية ممتازة واستفادة مباشرة من تحسن أسعار المعادن في بورصة لندن."
        },
        "ESRS.CA": {
            "name_ar": "حديد عز",
            "sector": "الموارد الأساسية والكيماويات",
            "rsi14": 58.0, "adx14": 25.8, "atr14": 2.10, "adv20_egp": 95000000.0, "beta_egx30": 1.22,
            "h_forecasts": {
                "1D": {"expected_return_pct": 0.40, "prob_up": 0.61, "confidence": 0.87, "t1_pct": 1.2, "t2_pct": 2.0, "t3_pct": 3.0},
                "5D": {"expected_return_pct": 1.95, "prob_up": 0.66, "confidence": 0.89, "t1_pct": 3.4, "t2_pct": 5.0, "t3_pct": 7.2},
                "10D": {"expected_return_pct": 4.00, "prob_up": 0.69, "confidence": 0.91, "t1_pct": 5.8, "t2_pct": 8.2, "t3_pct": 11.0},
                "20D": {"expected_return_pct": 7.40, "prob_up": 0.73, "confidence": 0.93, "t1_pct": 9.6, "t2_pct": 13.0, "t3_pct": 17.5},
                "60D": {"expected_return_pct": 14.00, "prob_up": 0.76, "confidence": 0.89, "t1_pct": 17.0, "t2_pct": 23.0, "t3_pct": 29.0}
            },
            "why_ar": "🟢 صدارة سوقية في حديد التسليح والمسطحات مع عوائد تصديرية قياسية وتدفقات نقدية قوية."
        },
        "EMFD.CA": {
            "name_ar": "إعمار مصر للتنمية",
            "sector": "التطوير العقاري",
            "rsi14": 54.8, "adx14": 22.8, "atr14": 0.35, "adv20_egp": 48500000.0, "beta_egx30": 1.04,
            "h_forecasts": {
                "1D": {"expected_return_pct": 0.28, "prob_up": 0.57, "confidence": 0.80, "t1_pct": 0.9, "t2_pct": 1.7, "t3_pct": 2.6},
                "5D": {"expected_return_pct": 1.45, "prob_up": 0.61, "confidence": 0.83, "t1_pct": 2.8, "t2_pct": 4.5, "t3_pct": 6.3},
                "10D": {"expected_return_pct": 3.15, "prob_up": 0.64, "confidence": 0.86, "t1_pct": 4.9, "t2_pct": 7.1, "t3_pct": 9.8},
                "20D": {"expected_return_pct": 6.00, "prob_up": 0.68, "confidence": 0.88, "t1_pct": 8.2, "t2_pct": 11.5, "t3_pct": 15.2},
                "60D": {"expected_return_pct": 11.50, "prob_up": 0.71, "confidence": 0.84, "t1_pct": 14.0, "t2_pct": 19.5, "t3_pct": 24.5}
            },
            "why_ar": "🟢 مشاريع فاخرة في الساحل الشمالي والقاهرة الجديدة مع قوة تسعيرية مرتفعة وسيولة وافرة."
        },
        "BTFH.CA": {
            "name_ar": "بلتون القابضة",
            "sector": "الخدمات المالية غير المصرفية",
            "rsi14": 55.4, "adx14": 26.5, "atr14": 0.15, "adv20_egp": 125000000.0, "beta_egx30": 1.35,
            "h_forecasts": {
                "1D": {"expected_return_pct": 0.36, "prob_up": 0.59, "confidence": 0.83, "t1_pct": 1.1, "t2_pct": 2.0, "t3_pct": 3.0},
                "5D": {"expected_return_pct": 1.85, "prob_up": 0.64, "confidence": 0.86, "t1_pct": 3.2, "t2_pct": 5.0, "t3_pct": 7.2},
                "10D": {"expected_return_pct": 3.90, "prob_up": 0.67, "confidence": 0.88, "t1_pct": 5.7, "t2_pct": 8.1, "t3_pct": 11.2},
                "20D": {"expected_return_pct": 7.20, "prob_up": 0.71, "confidence": 0.90, "t1_pct": 9.4, "t2_pct": 13.0, "t3_pct": 17.0},
                "60D": {"expected_return_pct": 13.80, "prob_up": 0.75, "confidence": 0.87, "t1_pct": 16.5, "t2_pct": 22.5, "t3_pct": 28.5}
            },
            "why_ar": "🟢 توسع قوي في التمويل متناهي الصغر والتأجير التمويلي وسيولة تداول يومية مرتفعة."
        },
        "POUL.CA": {
            "name_ar": "القاهرة للدواجن",
            "sector": "الأغذية والمشروبات",
            "rsi14": 53.2, "adx14": 21.0, "atr14": 0.45, "adv20_egp": 14200000.0, "beta_egx30": 0.75,
            "h_forecasts": {
                "1D": {"expected_return_pct": 0.22, "prob_up": 0.54, "confidence": 0.76, "t1_pct": 0.7, "t2_pct": 1.4, "t3_pct": 2.2},
                "5D": {"expected_return_pct": 1.15, "prob_up": 0.58, "confidence": 0.79, "t1_pct": 2.3, "t2_pct": 3.8, "t3_pct": 5.4},
                "10D": {"expected_return_pct": 2.50, "prob_up": 0.61, "confidence": 0.82, "t1_pct": 4.1, "t2_pct": 6.1, "t3_pct": 8.4},
                "20D": {"expected_return_pct": 4.80, "prob_up": 0.65, "confidence": 0.85, "t1_pct": 6.8, "t2_pct": 9.8, "t3_pct": 13.2},
                "60D": {"expected_return_pct": 9.60, "prob_up": 0.68, "confidence": 0.81, "t1_pct": 12.0, "t2_pct": 16.5, "t3_pct": 21.5}
            },
            "why_ar": "🟡 استقرار في قطاع الإنتاج الداجني والأعلاف مع هوامش تشغيلية دفاعية في EGX70."
        },
        "MOIL.CA": {
            "name_ar": "الخدمات الملاحية والبترولية (ماريديف)",
            "sector": "البتروكيماويات والطاقة",
            "rsi14": 52.8, "adx14": 20.4, "atr14": 0.02, "adv20_egp": 11500000.0, "beta_egx30": 1.10,
            "h_forecasts": {
                "1D": {"expected_return_pct": 0.20, "prob_up": 0.53, "confidence": 0.75, "t1_pct": 0.6, "t2_pct": 1.3, "t3_pct": 2.0},
                "5D": {"expected_return_pct": 1.05, "prob_up": 0.57, "confidence": 0.78, "t1_pct": 2.1, "t2_pct": 3.6, "t3_pct": 5.1},
                "10D": {"expected_return_pct": 2.30, "prob_up": 0.60, "confidence": 0.81, "t1_pct": 3.8, "t2_pct": 5.8, "t3_pct": 8.0},
                "20D": {"expected_return_pct": 4.50, "prob_up": 0.64, "confidence": 0.84, "t1_pct": 6.4, "t2_pct": 9.2, "t3_pct": 12.6},
                "60D": {"expected_return_pct": 9.00, "prob_up": 0.67, "confidence": 0.80, "t1_pct": 11.5, "t2_pct": 15.8, "t3_pct": 20.5}
            },
            "why_ar": "🟡 تحسن معدلات تشغيل أسطول الدعم البحري وخدمات الحقول البترولية الإقليمية."
        }
    }

    @classmethod
    def _synthesize_dynamic_profile(cls, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Dynamically synthesizes a quantitative multi-horizon profile for any active EGX ticker
        using metadata, beta, sector characteristics, and liquidity from EGXUniverseLoader.
        """
        from core.egx_universe_loader import EGXUniverseLoader
        info = EGXUniverseLoader.get_stock_info(ticker)
        if not info:
            return None

        name_ar = info.get("name_ar", ticker)
        sector = info.get("sector", "عام")
        beta = float(info.get("beta_egx30", 1.0))
        tier = info.get("market_cap_tier", "MID_CAP")
        adv = float(info.get("adv20_egp", 10000000.0))

        # Base alpha expectations modulated by sector beta and liquidity tier
        base_prob = 0.55 + min(max((beta - 1.0) * 0.05, -0.05), 0.08)
        if tier == "LARGE_CAP":
            base_prob += 0.03
        elif tier == "SMALL_CAP":
            base_prob -= 0.02

        prob_1d = round(base_prob, 2)
        prob_5d = round(min(base_prob + 0.04, 0.78), 2)
        prob_10d = round(min(base_prob + 0.07, 0.82), 2)
        prob_20d = round(min(base_prob + 0.10, 0.85), 2)
        prob_60d = round(min(base_prob + 0.13, 0.88), 2)

        conf = 0.85 if tier == "LARGE_CAP" else (0.80 if tier == "MID_CAP" else 0.75)

        h_forecasts = {
            "1D": {"expected_return_pct": round(0.25 * beta, 2), "prob_up": prob_1d, "confidence": conf, "t1_pct": round(0.8 * beta, 1), "t2_pct": round(1.5 * beta, 1), "t3_pct": round(2.5 * beta, 1)},
            "5D": {"expected_return_pct": round(1.30 * beta, 2), "prob_up": prob_5d, "confidence": round(conf + 0.02, 2), "t1_pct": round(2.5 * beta, 1), "t2_pct": round(4.2 * beta, 1), "t3_pct": round(6.0 * beta, 1)},
            "10D": {"expected_return_pct": round(2.80 * beta, 2), "prob_up": prob_10d, "confidence": round(conf + 0.04, 2), "t1_pct": round(4.5 * beta, 1), "t2_pct": round(6.8 * beta, 1), "t3_pct": round(9.5 * beta, 1)},
            "20D": {"expected_return_pct": round(5.50 * beta, 2), "prob_up": prob_20d, "confidence": round(conf + 0.06, 2), "t1_pct": round(7.5 * beta, 1), "t2_pct": round(11.0 * beta, 1), "t3_pct": round(15.0 * beta, 1)},
            "60D": {"expected_return_pct": round(10.50 * beta, 2), "prob_up": prob_60d, "confidence": conf, "t1_pct": round(13.5 * beta, 1), "t2_pct": round(19.0 * beta, 1), "t3_pct": round(24.5 * beta, 1)}
        }

        why_ar = f"🟡 سهم نشط ضمن قطاع {sector} بسيولة يومية تبلغ نحو {adv/1e6:.1f}M ج.م ومعامل بيتا {beta:.2f}."

        return {
            "name_ar": name_ar,
            "sector": sector,
            "rsi14": 52.0, "adx14": 21.0, "atr14": 1.0,
            "adv20_egp": adv,
            "beta_egx30": beta,
            "h_forecasts": h_forecasts,
            "why_ar": why_ar
        }

    @classmethod
    def get_stock_multi_horizon_analysis(cls, ticker: str) -> Optional[Dict[str, Any]]:
        from core.market_breadth_engine import MarketBreadthEngine
        from core.sector_rs_engine import SectorRelativeStrengthEngine
        from core.institutional_flow_engine import InstitutionalFlowEngine
        from core.live_fundamentals_engine import LiveFundamentalsEngine
        from core.news_sentiment_engine import NewsSentimentEngine
        from core.block_trades_engine import BlockTradesEngine
        from core.technical_setup_engine import TechnicalSetupEngine
        from core.risk_position_sizer import RiskBasedPositionSizer

        sym = ticker.upper().strip()
        if not sym.endswith(".CA") and "." not in sym:
            sym = f"{sym}.CA"

        prof = cls.STOCK_PROFILES.get(sym)
        if not prof:
            prof = cls._synthesize_dynamic_profile(sym)

        if not prof:
            return None

        rec = MarketPriceService.get_canonical_price_record(sym)
        p = float(rec["price"]) if rec and "price" in rec else MarketPriceService.get_latest_price(sym)
        stop_loss_price = float(rec.get("hard_stop_loss", round(p * 0.93, 2))) if rec else round(p * 0.93, 2)
        entry_low = float(rec.get("entry_zone_low", round(p * 0.985, 2))) if rec else round(p * 0.985, 2)
        entry_high = float(rec.get("entry_zone_high", round(p * 0.998, 2))) if rec else round(p * 0.998, 2)
        price_source = rec.get("source", "SSOT_LIVE_STORE") if rec else "SSOT_LIVE_STORE"
        price_timestamp = rec.get("timestamp", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")) if rec else datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. Advanced Institutional Quant Layer Evaluations
        breadth = MarketBreadthEngine.compute_market_breadth()
        sector_rs = SectorRelativeStrengthEngine.get_stock_sector_rs(sym)
        flow = InstitutionalFlowEngine.evaluate_stock_flow(sym, current_price=p)
        fundamentals = LiveFundamentalsEngine.get_stock_fundamentals(sym)
        sentiment = NewsSentimentEngine.get_sentiment_impact(sym)
        block_trades = BlockTradesEngine.detect_block_trades(sym, current_price=p)
        technical = TechnicalSetupEngine.evaluate_technical_setup(sym, current_price=p)
        risk_sizing = RiskBasedPositionSizer.calculate_position_size(
            entry_price=p,
            stop_loss_price=stop_loss_price,
            market_regime=breadth["market_regime"]
        )

        # Factor contributions
        rs_spread = sector_rs.get("rs_spread_pct", 0.0)
        rs_alpha_boost = min(max(rs_spread * 0.04, -0.08), 0.08)
        flow_alpha_boost = flow.get("flow_alpha_impact", 0.0) * 0.5
        breadth_risk_mult = breadth.get("risk_multiplier", 1.0)
        
        fund_score = fundamentals.get("fundamental_score", 65.0)
        fund_alpha_boost = (fund_score - 65.0) * 0.002
        sentiment_alpha_boost = sentiment.get("alpha_shock_pct", 0.0) * 0.02
        block_alpha_boost = block_trades.get("block_alpha_impact", 0.0) * 0.4
        tech_score = technical.get("technical_score", 60.0)
        tech_alpha_boost = (tech_score - 50.0) * 0.003

        # 2-Tier Relative Strength
        stock_rs_tier = "STRONG_LEADER" if rs_spread >= 1.0 else ("NEUTRAL" if rs_spread >= -1.0 else "WEAK_LAGGARD")
        sector_rs_tier = "OUTPERFORMING" if breadth.get("ad_ratio", 1.0) >= 1.0 else "UNDERPERFORMING"
        if rs_spread >= 0.5 and breadth.get("ad_ratio", 1.0) >= 1.0:
            rs_alignment_ar = "🟢 سهم قوي في قطاع صاعد متفوق (Dual Leader)"
        elif rs_spread >= 0.5:
            rs_alignment_ar = "🟢 سهم قوي يتفوق على أداء قطاعه"
        elif rs_spread >= -0.5:
            rs_alignment_ar = "🟡 أداء متوازن ومتوافق مع القطاع"
        else:
            rs_alignment_ar = "🔴 تراجع في القوة النسبية عن القطاع"

        horizons_data = {}
        conf_list = []
        prob_list = []

        for h_key, h_cfg in cls.HORIZONS.items():
            fc = prof["h_forecasts"][h_key]
            
            raw_prob = fc["prob_up"]
            raw_ret = fc["expected_return_pct"]

            # Horizon specific adjustments
            if h_key in ["1D", "5D"]:
                h_prob_adj = rs_alpha_boost * 0.4 + flow_alpha_boost + sentiment_alpha_boost + block_alpha_boost + tech_alpha_boost * 0.6
                h_ret_adj = (sentiment.get("alpha_shock_pct", 0.0) * 0.3) + (block_trades.get("block_alpha_impact", 0.0) * 2.5) + (tech_alpha_boost * 2.0)
            elif h_key in ["10D", "20D"]:
                h_prob_adj = rs_alpha_boost + flow_alpha_boost * 0.4 + fund_alpha_boost * 0.5 + sentiment_alpha_boost * 0.4 + tech_alpha_boost
                h_ret_adj = (rs_spread * 0.15) + (sentiment.get("alpha_shock_pct", 0.0) * 0.15) + (tech_alpha_boost * 1.5)
            else:  # 60D
                h_prob_adj = rs_alpha_boost * 0.7 + fund_alpha_boost * 1.5 + tech_alpha_boost * 0.5
                h_ret_adj = (fund_score - 65.0) * 0.10

            adj_prob = round(min(max(raw_prob + h_prob_adj, 0.35), 0.92), 2)
            adj_ret = round(max((raw_ret + h_ret_adj) * max(breadth_risk_mult, 0.5), -15.0), 2)
            adj_conf = round(min(max(fc["confidence"] * (0.95 if breadth["market_regime"] == MarketBreadthEngine.REGIME_PANIC_BEAR else 1.0), 0.50), 0.98), 2)

            conf_list.append(adj_conf)
            prob_list.append(adj_prob)

            exp_price = round(p * (1.0 + adj_ret / 100.0), 2)
            t1 = round(p * (1.0 + fc["t1_pct"] / 100.0), 2)
            t2 = round(p * (1.0 + fc["t2_pct"] / 100.0), 2)
            t3 = round(p * (1.0 + fc["t3_pct"] / 100.0), 2)
            reward = t1 - p
            risk = p - stop_loss_price
            rr_ratio = round(reward / risk, 2) if risk > 0 else 1.0

            horizons_data[h_key] = {
                "horizon_label": h_cfg["label"],
                "days": h_cfg["days"],
                "term": h_cfg["term"],
                "expected_return_pct": adj_ret,
                "expected_price": exp_price,
                "prob_up": adj_prob,
                "confidence": adj_conf,
                "target_1": t1,
                "target_2": t2,
                "target_3": t3,
                "stop_loss": stop_loss_price,
                "reward_to_risk": rr_ratio,
                "direction": "UP" if adj_ret > 0 else "DOWN"
            }

        short_score = round((horizons_data["1D"]["prob_up"] * 40 + horizons_data["5D"]["prob_up"] * 60), 1)
        med_score = round((horizons_data["10D"]["prob_up"] * 50 + horizons_data["20D"]["prob_up"] * 50), 1)
        long_score = round(horizons_data["60D"]["prob_up"] * 100, 1)
        overall_score = round(short_score * 0.35 + med_score * 0.45 + long_score * 0.20, 1)

        # 2. Decomposed UP DRIVERS & DOWN RISKS
        up_drivers = []
        down_risks = []

        # A. Sector Relative Strength Driver
        if sector_rs.get("is_leader", False) or rs_spread > 0.5:
            up_drivers.append({
                "factor": "Sector Relative Strength (قوة القطاع)",
                "impact_value": round(+abs(rs_spread) * 0.08, 2),
                "impact_label": f"+{rs_spread:+.2f}% تفوق على مؤشر القطاع",
                "description_ar": f"السهم يصنف كـ {sector_rs['leadership_label_ar']} متفوقاً على أداء قطاعه."
            })
        elif rs_spread < -0.5:
            down_risks.append({
                "factor": "Sector Drag (ضعف أداء القطاع)",
                "impact_value": round(-abs(rs_spread) * 0.08, 2),
                "impact_label": f"{rs_spread:+.2f}% فارق أداء عن القطاع",
                "description_ar": f"السهم متراجع عن متوسط أداء القطاع ({sector_rs['leadership_label_ar']})."
            })

        # B. Institutional Flow Driver
        if flow["flow_regime"] in [InstitutionalFlowEngine.FLOW_INSTITUTIONAL_ACCUMULATION, InstitutionalFlowEngine.FLOW_MODERATE_INFLOW]:
            up_drivers.append({
                "factor": "Institutional Flow (التدفق المؤسسي)",
                "impact_value": round(flow["flow_alpha_impact"], 2),
                "impact_label": f"Z-Score = {flow['volume_z_score']:+.2f}",
                "description_ar": flow["description_ar"]
            })
        elif flow["flow_regime"] in [InstitutionalFlowEngine.FLOW_RETAIL_DISTRIBUTION, InstitutionalFlowEngine.FLOW_MODERATE_OUTFLOW, InstitutionalFlowEngine.FLOW_ILLIQUID_DRYUP]:
            down_risks.append({
                "factor": "Volume & Flow Pressure (ضغط السيولة/التصريف)",
                "impact_value": round(flow["flow_alpha_impact"], 2),
                "impact_label": f"Z-Score = {flow['volume_z_score']:+.2f}",
                "description_ar": flow["description_ar"]
            })

        # C. Technical Setup & Trend Driver
        if tech_score >= 65.0:
            up_drivers.append({
                "factor": "Technical Setup & Trend (التحليل الفني والاتجاه)",
                "impact_value": round((tech_score - 50.0) * 0.004, 2),
                "impact_label": f"تقييم فني {tech_score:.1f}/100 ({technical['setup_classification']})",
                "description_ar": f"{technical['setup_label_ar']} فوق متوسط 20 يوم (RSI: {technical['rsi14']}, ADX: {technical['adx14']})."
            })
        elif tech_score < 50.0:
            down_risks.append({
                "factor": "Technical Breakdown (ضعف فني أو تراجع تحت المتوسطات)",
                "impact_value": round((tech_score - 50.0) * 0.004, 2),
                "impact_label": f"تقييم فني {tech_score:.1f}/100 ({technical['setup_classification']})",
                "description_ar": f"تراجع دون متوسط 20 يوماً أو مؤشرات عزم ضعيفة."
            })

        # D. Fundamental Quality Driver
        if fund_score >= 65.0:
            up_drivers.append({
                "factor": "Fundamental Quality & Solvency (جودة الأساسيات والتقييم)",
                "impact_value": round((fund_score - 50.0) * 0.005, 2),
                "impact_label": f"تقييم مالي {fund_score:.1f}/100 (مكرر P/E: {fundamentals['pe_ratio']:.1f})",
                "description_ar": f"عائد حقوق ملكية قوي (ROE: {fundamentals['roe_pct']:.1f}%) ونمو أرباح ({fundamentals['eps_growth_pct']:.1f}%)."
            })
        elif fund_score < 50.0:
            down_risks.append({
                "factor": "Fundamental Valuation Drag (ضغط التقييم/الرافعة)",
                "impact_value": round((fund_score - 50.0) * 0.005, 2),
                "impact_label": f"تقييم مالي {fund_score:.1f}/100 (مكرر P/E: {fundamentals['pe_ratio']:.1f})",
                "description_ar": f"رافعة مالية مرتفعة أو تراجع هوامش ربحية (مديونية: {fundamentals['debt_to_equity']:.2f})."
            })

        # E. Corporate News & Disclosure NLP Driver
        if sentiment.get("is_catalyst", False):
            up_drivers.append({
                "factor": "Corporate Disclosure Catalyst (محفز الأخبار والإفصاحات)",
                "impact_value": round(sentiment["alpha_shock_pct"] * 0.05, 2),
                "impact_label": f"{sentiment['sentiment_label_ar']} ({sentiment['materiality']})",
                "description_ar": sentiment["headline_ar"]
            })
        elif sentiment.get("is_risk_event", False):
            down_risks.append({
                "factor": "Negative News Sentiment Shock (صدمة الأخبار السلبية)",
                "impact_value": round(sentiment["alpha_shock_pct"] * 0.05, 2),
                "impact_label": f"{sentiment['sentiment_label_ar']} ({sentiment['materiality']})",
                "description_ar": sentiment["headline_ar"]
            })

        # F. Block Trades Driver
        if block_trades["classification"] == BlockTradesEngine.SIGNAL_SMART_MONEY_INFLOW:
            up_drivers.append({
                "factor": "Institutional Block Inflow (صفقات كتلية شرائية)",
                "impact_value": +0.12,
                "impact_label": f"{block_trades['ticket_multiple']}x متوسط التذكرة",
                "description_ar": block_trades["description_ar"]
            })
        elif block_trades["classification"] == BlockTradesEngine.SIGNAL_DISTRIBUTION_PRESSURE:
            down_risks.append({
                "factor": "Block Trade Distribution Pressure (ضغط بيوع كتلية)",
                "impact_value": -0.15,
                "impact_label": f"{block_trades['ticket_multiple']}x متوسط التذكرة",
                "description_ar": block_trades["description_ar"]
            })

        # G. Technical & Stop Protection
        down_risks.append({
            "factor": "Hard Stop-Loss Floor (-7.0%)",
            "impact_value": -0.07,
            "impact_label": f"{stop_loss_price:.2f} ج.م",
            "description_ar": "صمام أمان إلزامي ومحمي غير قابل للإلغاء لحماية رأس المال."
        })

        # 3. Staged Multi-Target Exits Protocol (T1 33%, T2 33%, T3 34%)
        t1_val = horizons_data["5D"]["target_1"]
        t2_val = horizons_data["20D"]["target_1"]
        t3_val = horizons_data["60D"]["target_1"]
        staged_exits = {
            "T1": {
                "price": t1_val,
                "gain_pct": round(((t1_val - p) / p) * 100.0, 1),
                "exit_share_pct": 33.3,
                "action_ar": "جني ربح جزئي (33%) ونقل وقف الخسارة لسعر الدخول (Breakeven)"
            },
            "T2": {
                "price": t2_val,
                "gain_pct": round(((t2_val - p) / p) * 100.0, 1),
                "exit_share_pct": 33.3,
                "action_ar": "جني ربح جزئي إضافي (33%) وتفعيل الوقف المتحرك (Trailing Stop 4%)"
            },
            "T3": {
                "price": t3_val,
                "gain_pct": round(((t3_val - p) / p) * 100.0, 1),
                "exit_share_pct": 33.4,
                "action_ar": "الخروج بالكمية المتبقية (34%) عند اكتمال الاتجاه أو كسر متوسط 20 يوم"
            }
        }

        # 4. Enforce the Uncertainty Rule
        avg_conf = sum(conf_list) / len(conf_list) if conf_list else 0.80
        prob_spread = max(prob_list) - min(prob_list) if prob_list else 0.0
        uncertainty_score = round((1.0 - avg_conf) + (prob_spread * 0.5), 2)

        is_high_uncertainty = (
            uncertainty_score >= 0.42 or
            avg_conf < 0.55 or
            (breadth["market_regime"] == MarketBreadthEngine.REGIME_PANIC_BEAR and overall_score < 75.0) or
            (flow["flow_regime"] == InstitutionalFlowEngine.FLOW_RETAIL_DISTRIBUTION and horizons_data["1D"]["prob_up"] < 0.50) or
            (sentiment.get("is_risk_event", False) and sentiment.get("materiality") == NewsSentimentEngine.IMPACT_HIGH)
        )

        if is_high_uncertainty:
            decision = "NO_TRADE_WAIT"
            action_ar = "🟡 مراقبة وانتظار (تفعيل قاعدة عدم اليقين لحماية رأس المال)"
            uncertainty_level = "HIGH"
        else:
            if overall_score >= 80.0:
                decision = "BUY"
                action_ar = "🟢 فرصة شراء وتجميع ممتازة"
            elif overall_score >= 65.0:
                decision = "WATCH"
                action_ar = "🟡 مراقبة / احتفاظ بالمركز"
            else:
                decision = "AVOID"
                action_ar = "🔴 تجنب فتح مراكز جديدة حالياً"
            uncertainty_level = "LOW" if avg_conf >= 0.85 else "MODERATE"

        # Dominant Catalyst classification
        if fund_score >= 75.0:
            dominant_cat = "FUNDAMENTAL_QUALITY"
        elif technical["technical_score"] >= 75.0:
            dominant_cat = "TECHNICAL_BREAKOUT"
        elif "INFLOW" in block_trades.get("classification", ""):
            dominant_cat = "INSTITUTIONAL_BLOCK_INFLOW"
        elif rs_spread >= 1.5:
            dominant_cat = "SECTOR_MOMENTUM"
        else:
            dominant_cat = "MARKET_BETA"

        # Mathematical Expectancy
        win_rate = 0.55
        avg_win_pct = horizons_data["20D"]["expected_return_pct"]
        avg_loss_pct = 3.50
        expectancy_pct = round((win_rate * avg_win_pct) - ((1.0 - win_rate) * avg_loss_pct), 2)

        return {
            "ticker": sym,
            "company_name": prof["name_ar"],
            "sector": prof["sector"],
            "current_price": p,
            "price_source": price_source,
            "price_timestamp": price_timestamp,
            "entry_zone": f"{entry_low:.2f} – {entry_high:.2f}",
            "stop_loss": stop_loss_price,
            "short_term_score": short_score,
            "medium_term_score": med_score,
            "long_term_score": long_score,
            "overall_score": overall_score,
            "explanation_ar": prof["why_ar"],
            "decision": decision,
            "action_ar": action_ar,
            "uncertainty_level": uncertainty_level,
            "uncertainty_score": uncertainty_score,
            "uncertainty_rule_triggered": is_high_uncertainty,
            "market_regime": breadth["market_regime"],
            "market_regime_label_ar": breadth["market_regime_label_ar"],
            "sector_relative_strength": sector_rs,
            "two_tier_relative_strength": {
                "stock_rs_vs_sector": stock_rs_tier,
                "sector_rs_vs_market": sector_rs_tier,
                "rs_alignment_label_ar": rs_alignment_ar
            },
            "technical_setup": technical,
            "risk_based_position": risk_sizing,
            "staged_exits": staged_exits,
            "holding_period_ar": "5 – 20 جلسة تداول (متوسط شهر)",
            "setup_name": technical["setup_classification"],
            "setup_name_ar": technical["setup_label_ar"],
            "dominant_catalyst": dominant_cat,
            "expectancy_pct": expectancy_pct,
            "expectancy_label": "[Theoretical Baseline Target - Not Empirical Until 30-Day Incubation Closes]",
            "institutional_flow": flow,
            "fundamentals": fundamentals,
            "news_sentiment": sentiment,
            "block_trades": block_trades,
            "up_drivers": up_drivers,
            "down_risks": down_risks,
            "horizons": horizons_data
        }

    @classmethod
    def get_all_multi_horizon_rankings(
        cls,
        tickers: Optional[List[str]] = None,
        universe: str = "all"
    ) -> List[Dict[str, Any]]:
        """
        Calculates rankings across specified tickers or index universe.
        Supported universe filters: 'all', 'egx30', 'egx70', 'egx100', 'core'.
        """
        selected_tickers = []
        if tickers:
            selected_tickers = list(tickers)
        elif universe.lower() in ["core", "24"]:
            selected_tickers = list(cls.STOCK_PROFILES.keys())
        else:
            try:
                from core.egx_universe_loader import EGXUniverseLoader
                selected_tickers = EGXUniverseLoader.get_tickers(universe)
            except ImportError:
                selected_tickers = list(cls.STOCK_PROFILES.keys())

        # Ensure no duplicates while preserving sequence
        seen = set()
        deduped = []
        for t in selected_tickers:
            sym = t.upper().strip()
            if not sym.endswith(".CA") and "." not in sym:
                sym = f"{sym}.CA"
            if sym not in seen:
                seen.add(sym)
                deduped.append(sym)

        results = []
        for ticker in deduped:
            try:
                analysis = cls.get_stock_multi_horizon_analysis(ticker)
                if analysis:
                    results.append(analysis)
            except Exception:
                continue

        results.sort(key=lambda x: x["overall_score"], reverse=True)
        for idx, item in enumerate(results, start=1):
            item["rank"] = idx

        return results
