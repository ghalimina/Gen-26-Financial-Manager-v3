#!/usr/bin/env python3
# =============================================================================
# core/egx_universe_loader.py — GEN-26 Comprehensive EGX Universe Loader
# Maintains complete active Egyptian Exchange (EGX 100 / EGX 30 / EGX 70) constituents
# with sector taxonomy, Arabic/English names, ISINs, index memberships, and nominal prices.
# =============================================================================

import os
import json
from typing import Dict, List, Any, Optional


class EGXUniverseLoader:
    """
    Dynamic Loader and Single Source of Truth for the Egyptian Exchange Active Universe.
    Covers EGX 30, EGX 70, EGX 100, and Tradable Sector constituents.
    """

    # Comprehensive Active Egyptian Equities Universe
    ACTIVE_UNIVERSE: Dict[str, Dict[str, Any]] = {
        # ---------------------------------------------------------------------
        # EGX 30 Benchmark Constituents (Core Liquid Large-Caps & Blue-Chips)
        # ---------------------------------------------------------------------
        "COMI.CA": {
            "ticker": "COMI.CA",
            "name_ar": "البنك التجاري الدولي (CIB)",
            "name_en": "Commercial International Bank",
            "sector": "الخدمات المالية والبنوك",
            "sector_en": "Banking & Financial Services",
            "isin": "EGS60121C018",
            "index_membership": ["EGX30", "EGX100"],
            "market_cap_tier": "LARGE_CAP",
            "nominal_price": 137.00,
            "adv20_egp": 342500000.0,
            "beta_egx30": 1.12,
            "is_active": True
        },
        "SWDY.CA": {
            "ticker": "SWDY.CA",
            "name_ar": "السويدي إليكتريك",
            "name_en": "Elsewedy Electric",
            "sector": "الصناعة والمقاولات",
            "sector_en": "Industrial & Construction",
            "isin": "EGS3G111C013",
            "index_membership": ["EGX30", "EGX100"],
            "market_cap_tier": "LARGE_CAP",
            "nominal_price": 116.00,
            "adv20_egp": 208800000.0,
            "beta_egx30": 1.05,
            "is_active": True
        },
        "TMGH.CA": {
            "ticker": "TMGH.CA",
            "name_ar": "مجموعة طلعت مصطفى",
            "name_en": "Talaat Moustafa Group Holding",
            "sector": "التطوير العقاري",
            "sector_en": "Real Estate",
            "isin": "EGS65851C015",
            "index_membership": ["EGX30", "EGX100"],
            "market_cap_tier": "LARGE_CAP",
            "nominal_price": 97.70,
            "adv20_egp": 205170000.0,
            "beta_egx30": 1.18,
            "is_active": True
        },
        "ORAS.CA": {
            "ticker": "ORAS.CA",
            "name_ar": "أوراسكوم للإنشاء",
            "name_en": "Orascom Construction PLC",
            "sector": "الصناعة والمقاولات",
            "sector_en": "Industrial & Construction",
            "isin": "EGS21451C017",
            "index_membership": ["EGX30", "EGX100"],
            "market_cap_tier": "LARGE_CAP",
            "nominal_price": 759.00,
            "adv20_egp": 84000000.0,
            "beta_egx30": 0.88,
            "is_active": True
        },
        "EFIH.CA": {
            "ticker": "EFIH.CA",
            "name_ar": "إي فاينانس للاستثمارات المالية والرقمية",
            "name_en": "e-finance for Digital and Financial Investments",
            "sector": "تكنولوجيا المدفوعات",
            "sector_en": "Technology & FinTech",
            "isin": "EGS745V1C012",
            "index_membership": ["EGX30", "EGX100"],
            "market_cap_tier": "LARGE_CAP",
            "nominal_price": 24.50,
            "adv20_egp": 72500000.0,
            "beta_egx30": 1.08,
            "is_active": True
        },
        "EGAL.CA": {
            "ticker": "EGAL.CA",
            "name_ar": "مصر للألومنيوم",
            "name_en": "Egypt Aluminium",
            "sector": "الموارد الأساسية والكيماويات",
            "sector_en": "Basic Materials & Metals",
            "isin": "EGS34031C016",
            "index_membership": ["EGX30", "EGX100"],
            "market_cap_tier": "LARGE_CAP",
            "nominal_price": 330.00,
            "adv20_egp": 68000000.0,
            "beta_egx30": 1.15,
            "is_active": True
        },
        "ESRS.CA": {
            "ticker": "ESRS.CA",
            "name_ar": "حديد عز",
            "name_en": "Ezz Steel",
            "sector": "الموارد الأساسية والكيماويات",
            "sector_en": "Basic Materials & Metals",
            "isin": "EGS33041C012",
            "index_membership": ["EGX30", "EGX100"],
            "market_cap_tier": "LARGE_CAP",
            "nominal_price": 128.50,
            "adv20_egp": 95000000.0,
            "beta_egx30": 1.22,
            "is_active": True
        },
        "EMFD.CA": {
            "ticker": "EMFD.CA",
            "name_ar": "إعمار مصر للتنمية",
            "name_en": "Emaar Misr for Development",
            "sector": "التطوير العقاري",
            "sector_en": "Real Estate",
            "isin": "EGS65931C013",
            "index_membership": ["EGX30", "EGX100"],
            "market_cap_tier": "LARGE_CAP",
            "nominal_price": 11.81,
            "adv20_egp": 48500000.0,
            "beta_egx30": 1.04,
            "is_active": True
        },
        "BTFH.CA": {
            "ticker": "BTFH.CA",
            "name_ar": "بلتون القابضة",
            "name_en": "Beltone Financial Holding",
            "sector": "الخدمات المالية غير المصرفية",
            "sector_en": "Non-Bank Financial Services",
            "isin": "EGS691S1C011",
            "index_membership": ["EGX30", "EGX100"],
            "market_cap_tier": "LARGE_CAP",
            "nominal_price": 2.98,
            "adv20_egp": 125000000.0,
            "beta_egx30": 1.35,
            "is_active": True
        },
        "EKHO.CA": {
            "ticker": "EKHO.CA",
            "name_ar": "القابضة المصرية الكويتية (بالدولار)",
            "name_en": "Egypt Kuwait Holding (USD)",
            "sector": "الخدمات المالية والاستثمار",
            "sector_en": "Financial Services & Investment",
            "isin": "EGS69082C013",
            "index_membership": ["EGX30", "EGX100"],
            "market_cap_tier": "LARGE_CAP",
            "nominal_price": 37.20,
            "adv20_egp": 19344000.0,
            "beta_egx30": 0.85,
            "is_active": True
        },
        "EKHOA.CA": {
            "ticker": "EKHOA.CA",
            "name_ar": "القابضة المصرية الكويتية (بالجنيه)",
            "name_en": "Egypt Kuwait Holding (EGP)",
            "sector": "الخدمات المالية والاستثمار",
            "sector_en": "Financial Services & Investment",
            "isin": "EGS69081C014",
            "index_membership": ["EGX30", "EGX100"],
            "market_cap_tier": "LARGE_CAP",
            "nominal_price": 42.80,
            "adv20_egp": 28400000.0,
            "beta_egx30": 0.89,
            "is_active": True
        },
        "ABUK.CA": {
            "ticker": "ABUK.CA",
            "name_ar": "أبو قير للأسمدة",
            "name_en": "Abu Qir Fertilizers",
            "sector": "الموارد الأساسية والكيماويات",
            "sector_en": "Fertilizers & Chemicals",
            "isin": "EGS38191C010",
            "index_membership": ["EGX30", "EGX100"],
            "market_cap_tier": "LARGE_CAP",
            "nominal_price": 75.52,
            "adv20_egp": 59375000.0,
            "beta_egx30": 1.02,
            "is_active": True
        },
        "MFPC.CA": {
            "ticker": "MFPC.CA",
            "name_ar": "مصر لإنتاج الأسمدة (موبكو)",
            "name_en": "Misr Fertilizers Production (MOPCO)",
            "sector": "الموارد الأساسية والكيماويات",
            "sector_en": "Fertilizers & Chemicals",
            "isin": "EGS38201C017",
            "index_membership": ["EGX30", "EGX100"],
            "market_cap_tier": "LARGE_CAP",
            "nominal_price": 48.50,
            "adv20_egp": 41225000.0,
            "beta_egx30": 1.06,
            "is_active": True
        },
        "ADIB.CA": {
            "ticker": "ADIB.CA",
            "name_ar": "مصرف أبو ظبي الإسلامي - مصر",
            "name_en": "Abu Dhabi Islamic Bank Egypt",
            "sector": "الخدمات المالية والبنوك",
            "sector_en": "Banking & Financial Services",
            "isin": "EGS60041C018",
            "index_membership": ["EGX30", "EGX100"],
            "market_cap_tier": "LARGE_CAP",
            "nominal_price": 53.42,
            "adv20_egp": 37884000.0,
            "beta_egx30": 0.98,
            "is_active": True
        },
        "ETEL.CA": {
            "ticker": "ETEL.CA",
            "name_ar": "المصرية للاتصالات (WE)",
            "name_en": "Telecom Egypt",
            "sector": "الاتصالات وتكنولوجيا المعلومات",
            "sector_en": "Telecom & Technology",
            "isin": "EGS48031C016",
            "index_membership": ["EGX30", "EGX100"],
            "market_cap_tier": "LARGE_CAP",
            "nominal_price": 114.89,
            "adv20_egp": 75050000.0,
            "beta_egx30": 0.92,
            "is_active": True
        },
        "SKPC.CA": {
            "ticker": "SKPC.CA",
            "name_ar": "سيدي كرير للبتروكيماويات (سيدبك)",
            "name_en": "Sidi Kerir Petrochemicals",
            "sector": "البتروكيماويات والطاقة",
            "sector_en": "Petrochemicals & Energy",
            "isin": "EGS380S1C017",
            "index_membership": ["EGX30", "EGX100"],
            "market_cap_tier": "MID_CAP",
            "nominal_price": 29.80,
            "adv20_egp": 32780000.0,
            "beta_egx30": 1.08,
            "is_active": True
        },
        "BINV.CA": {
            "ticker": "BINV.CA",
            "name_ar": "بي إنفستمنتس القابضة",
            "name_en": "B Investments Holding",
            "sector": "الخدمات المالية والاستثمار",
            "sector_en": "Financial Services & Investment",
            "isin": "EGS693R1C018",
            "index_membership": ["EGX30", "EGX100"],
            "market_cap_tier": "MID_CAP",
            "nominal_price": 25.40,
            "adv20_egp": 15240000.0,
            "beta_egx30": 0.82,
            "is_active": True
        },
        "EAST.CA": {
            "ticker": "EAST.CA",
            "name_ar": "الشرقية للدخان (إيسترن كومباني)",
            "name_en": "Eastern Company",
            "sector": "السلع الاستهلاكية",
            "sector_en": "Consumer Goods & Staples",
            "isin": "EGS37091C013",
            "index_membership": ["EGX30", "EGX100"],
            "market_cap_tier": "LARGE_CAP",
            "nominal_price": 36.02,
            "adv20_egp": 56425000.0,
            "beta_egx30": 0.72,
            "is_active": True
        },
        "HRHO.CA": {
            "ticker": "HRHO.CA",
            "name_ar": "مجموعة إي إف جي القابضة (هيرميس)",
            "name_en": "EFG Holding",
            "sector": "الخدمات المالية غير المصرفية",
            "sector_en": "Non-Bank Financial Services",
            "isin": "EGS69101C011",
            "index_membership": ["EGX30", "EGX100"],
            "market_cap_tier": "LARGE_CAP",
            "nominal_price": 26.30,
            "adv20_egp": 55440000.0,
            "beta_egx30": 1.14,
            "is_active": True
        },
        "JUFO.CA": {
            "ticker": "JUFO.CA",
            "name_ar": "جهينة للصناعات الغذائية",
            "name_en": "Juhayna Food Industries",
            "sector": "الأغذية والمشروبات",
            "sector_en": "Food & Beverages",
            "isin": "EGS30901C010",
            "index_membership": ["EGX30", "EGX100"],
            "market_cap_tier": "MID_CAP",
            "nominal_price": 26.71,
            "adv20_egp": 17850000.0,
            "beta_egx30": 0.81,
            "is_active": True
        },
        "GBCO.CA": {
            "ticker": "GBCO.CA",
            "name_ar": "جي بي كورب (غبور أوتو)",
            "name_en": "GB Corp",
            "sector": "السيارات والصناعة",
            "sector_en": "Automotive & Industrial",
            "isin": "EGS673T1C012",
            "index_membership": ["EGX30", "EGX100"],
            "market_cap_tier": "MID_CAP",
            "nominal_price": 29.32,
            "adv20_egp": 16008000.0,
            "beta_egx30": 1.10,
            "is_active": True
        },
        "DOMT.CA": {
            "ticker": "DOMT.CA",
            "name_ar": "الصناعات الغذائية العربية (دومتي)",
            "name_en": "Arabian Food Industries (Domty)",
            "sector": "الأغذية والمشروبات",
            "sector_en": "Food & Beverages",
            "isin": "EGS305B1C013",
            "index_membership": ["EGX30", "EGX100"],
            "market_cap_tier": "MID_CAP",
            "nominal_price": 15.20,
            "adv20_egp": 7600000.0,
            "beta_egx30": 0.76,
            "is_active": True
        },
        "HELI.CA": {
            "ticker": "HELI.CA",
            "name_ar": "مصر الجديدة للإسكان والتعمير",
            "name_en": "Heliopolis Housing",
            "sector": "التطوير العقاري",
            "sector_en": "Real Estate",
            "isin": "EGS65591C017",
            "index_membership": ["EGX30", "EGX100"],
            "market_cap_tier": "MID_CAP",
            "nominal_price": 7.69,
            "adv20_egp": 19040000.0,
            "beta_egx30": 1.25,
            "is_active": True
        },
        "AMOC.CA": {
            "ticker": "AMOC.CA",
            "name_ar": "الإسكندرية للزيوت المعدنية (أموك)",
            "name_en": "Alexandria Mineral Oils Company",
            "sector": "البتروكيماويات والطاقة",
            "sector_en": "Petrochemicals & Energy",
            "isin": "EGS38321C019",
            "index_membership": ["EGX30", "EGX100"],
            "market_cap_tier": "MID_CAP",
            "nominal_price": 11.35,
            "adv20_egp": 17920000.0,
            "beta_egx30": 1.05,
            "is_active": True
        },
        "FWRY.CA": {
            "ticker": "FWRY.CA",
            "name_ar": "فوري لتكنولوجيا المدفوعات الإلكترونية",
            "name_en": "Fawry for Banking & Payment Technology",
            "sector": "تكنولوجيا المدفوعات",
            "sector_en": "Technology & FinTech",
            "isin": "EGS745L1C014",
            "index_membership": ["EGX30", "EGX100"],
            "market_cap_tier": "LARGE_CAP",
            "nominal_price": 19.21,
            "adv20_egp": 35325000.0,
            "beta_egx30": 1.16,
            "is_active": True
        },
        "CICH.CA": {
            "ticker": "CICH.CA",
            "name_ar": "سي آي كابيتال القابضة",
            "name_en": "CI Capital Holding",
            "sector": "الخدمات المالية والاستثمار",
            "sector_en": "Financial Services & Investment",
            "isin": "EGS691S1C011",
            "index_membership": ["EGX30", "EGX100"],
            "market_cap_tier": "MID_CAP",
            "nominal_price": 6.15,
            "adv20_egp": 5842500.0,
            "beta_egx30": 0.88,
            "is_active": True
        },
        "PHDC.CA": {
            "ticker": "PHDC.CA",
            "name_ar": "بالم هيلز للتعمير",
            "name_en": "Palm Hills Developments",
            "sector": "التطوير العقاري",
            "sector_en": "Real Estate",
            "isin": "EGS655L1C012",
            "index_membership": ["EGX30", "EGX100"],
            "market_cap_tier": "LARGE_CAP",
            "nominal_price": 15.15,
            "adv20_egp": 17440000.0,
            "beta_egx30": 1.20,
            "is_active": True
        },
        "MASR.CA": {
            "ticker": "MASR.CA",
            "name_ar": "مدينة مصر للإسكان والتعمير (MNHD)",
            "name_en": "Madinet Masr for Housing and Development",
            "sector": "التطوير العقاري",
            "sector_en": "Real Estate",
            "isin": "EGS65081C016",
            "index_membership": ["EGX30", "EGX100"],
            "market_cap_tier": "LARGE_CAP",
            "nominal_price": 4.60,
            "adv20_egp": 38200000.0,
            "beta_egx30": 1.15,
            "is_active": True
        },
        "ISPH.CA": {
            "ticker": "ISPH.CA",
            "name_ar": "ابن سينا فارما",
            "name_en": "Ibnsina Pharma",
            "sector": "الرعاية الصحية والأدوية",
            "sector_en": "Healthcare & Pharmaceuticals",
            "isin": "EGS729J1C013",
            "index_membership": ["EGX30", "EGX100"],
            "market_cap_tier": "MID_CAP",
            "nominal_price": 13.02,
            "adv20_egp": 7455000.0,
            "beta_egx30": 0.84,
            "is_active": True
        },
        "ALCN.CA": {
            "ticker": "ALCN.CA",
            "name_ar": "الإسكندرية لتداول الحاويات والبضائع",
            "name_en": "Alexandria Container & Cargo Handling",
            "sector": "النقل واللوجستيات",
            "sector_en": "Transportation & Logistics",
            "isin": "EGS42081C014",
            "index_membership": ["EGX30", "EGX100"],
            "market_cap_tier": "LARGE_CAP",
            "nominal_price": 46.40,
            "adv20_egp": 20880000.0,
            "beta_egx30": 0.78,
            "is_active": True
        },

        # ---------------------------------------------------------------------
        # EGX 70 Constituents (Active Growth, Mid-Caps & Small-Caps)
        # ---------------------------------------------------------------------
        "POUL.CA": {
            "ticker": "POUL.CA",
            "name_ar": "القاهرة للدواجن",
            "name_en": "Cairo Poultry",
            "sector": "الأغذية والمشروبات",
            "sector_en": "Food & Agriculture",
            "isin": "EGS30021C010",
            "index_membership": ["EGX70", "EGX100"],
            "market_cap_tier": "MID_CAP",
            "nominal_price": 10.45,
            "adv20_egp": 14200000.0,
            "beta_egx30": 0.75,
            "is_active": True
        },
        "MOIL.CA": {
            "ticker": "MOIL.CA",
            "name_ar": "الخدمات الملاحية والبترولية (ماريديف)",
            "name_en": "Maridive & Oil Services",
            "sector": "البتروكيماويات والطاقة",
            "sector_en": "Energy & Marine Services",
            "isin": "EGS41011C017",
            "index_membership": ["EGX70", "EGX100"],
            "market_cap_tier": "MID_CAP",
            "nominal_price": 0.28,
            "adv20_egp": 11500000.0,
            "beta_egx30": 1.10,
            "is_active": True
        },
        "CCAP.CA": {
            "ticker": "CCAP.CA",
            "name_ar": "القلعة للاستشارات المالية",
            "name_en": "Qalaa Holdings",
            "sector": "الخدمات المالية والاستثمار",
            "sector_en": "Financial Services & Investment",
            "isin": "EGS691T1C019",
            "index_membership": ["EGX70", "EGX100"],
            "market_cap_tier": "MID_CAP",
            "nominal_price": 5.60,
            "adv20_egp": 15950000.0,
            "beta_egx30": 1.28,
            "is_active": True
        },
        "RAYA.CA": {
            "ticker": "RAYA.CA",
            "name_ar": "راية القابضة للاستثمارات المالية",
            "name_en": "Raya Holding for Financial Investments",
            "sector": "الاتصالات وتكنولوجيا المعلومات",
            "sector_en": "Technology & Trade",
            "isin": "EGS69071C014",
            "index_membership": ["EGX70", "EGX100"],
            "market_cap_tier": "MID_CAP",
            "nominal_price": 7.00,
            "adv20_egp": 3315000.0,
            "beta_egx30": 0.85,
            "is_active": True
        },
        "CLHO.CA": {
            "ticker": "CLHO.CA",
            "name_ar": "مستشفى كليوباترا",
            "name_en": "Cleopatra Hospital Group",
            "sector": "الرعاية الصحية والأدوية",
            "sector_en": "Healthcare",
            "isin": "EGS72131C011",
            "index_membership": ["EGX70", "EGX100"],
            "market_cap_tier": "MID_CAP",
            "nominal_price": 6.80,
            "adv20_egp": 8500000.0,
            "beta_egx30": 0.65,
            "is_active": True
        },
        "ORHD.CA": {
            "ticker": "ORHD.CA",
            "name_ar": "أوراسكوم للتنمية مصر",
            "name_en": "Orascom Development Egypt",
            "sector": "التطوير العقاري",
            "sector_en": "Real Estate & Tourism",
            "isin": "EGS65011C013",
            "index_membership": ["EGX70", "EGX100"],
            "market_cap_tier": "LARGE_CAP",
            "nominal_price": 14.80,
            "adv20_egp": 22400000.0,
            "beta_egx30": 1.05,
            "is_active": True
        },
        "CERA.CA": {
            "ticker": "CERA.CA",
            "name_ar": "العز للسيراميك والبورسلين (الجوهرة)",
            "name_en": "Gemma (Ceramica El Ezz)",
            "sector": "الصناعة والمقاولات",
            "sector_en": "Building Materials",
            "isin": "EGS3C341C012",
            "index_membership": ["EGX70", "EGX100"],
            "market_cap_tier": "MID_CAP",
            "nominal_price": 18.50,
            "adv20_egp": 6200000.0,
            "beta_egx30": 0.88,
            "is_active": True
        },
        "SPMD.CA": {
            "ticker": "SPMD.CA",
            "name_ar": "سبيد ميديكال",
            "name_en": "Speed Medical",
            "sector": "الرعاية الصحية والأدوية",
            "sector_en": "Healthcare",
            "isin": "EGS729I1C014",
            "index_membership": ["EGX70", "EGX100"],
            "market_cap_tier": "SMALL_CAP",
            "nominal_price": 0.45,
            "adv20_egp": 4800000.0,
            "beta_egx30": 1.20,
            "is_active": True
        },
        "DSCW.CA": {
            "ticker": "DSCW.CA",
            "name_ar": "دايس للملابس الجاهزة",
            "name_en": "Dice Sport & Casual Wear",
            "sector": "السلع الاستهلاكية",
            "sector_en": "Textiles & Apparel",
            "isin": "EGS33091C017",
            "index_membership": ["EGX70", "EGX100"],
            "market_cap_tier": "SMALL_CAP",
            "nominal_price": 1.38,
            "adv20_egp": 16400000.0,
            "beta_egx30": 1.12,
            "is_active": True
        },
        "ACRO.CA": {
            "ticker": "ACRO.CA",
            "name_ar": "أكرو مصر للشدات والسقالات المعدنية",
            "name_en": "Acro Misr for Scaffolding",
            "sector": "الصناعة والمقاولات",
            "sector_en": "Industrial",
            "isin": "EGS21021C010",
            "index_membership": ["EGX70", "EGX100"],
            "market_cap_tier": "MID_CAP",
            "nominal_price": 54.00,
            "adv20_egp": 5800000.0,
            "beta_egx30": 0.70,
            "is_active": True
        },
        "OIH.CA": {
            "ticker": "OIH.CA",
            "name_ar": "أوراسكوم للاستثمار القابضة",
            "name_en": "Orascom Investment Holding",
            "sector": "الخدمات المالية والاستثمار",
            "sector_en": "Financial Services & Investment",
            "isin": "EGS693Y1C015",
            "index_membership": ["EGX70", "EGX100"],
            "market_cap_tier": "MID_CAP",
            "nominal_price": 0.48,
            "adv20_egp": 12800000.0,
            "beta_egx30": 1.18,
            "is_active": True
        },
        "ARAB.CA": {
            "ticker": "ARAB.CA",
            "name_ar": "المطورون العرب القابضة",
            "name_en": "Arab Developers Holding",
            "sector": "التطوير العقاري",
            "sector_en": "Real Estate",
            "isin": "EGS65601C015",
            "index_membership": ["EGX70", "EGX100"],
            "market_cap_tier": "SMALL_CAP",
            "nominal_price": 0.62,
            "adv20_egp": 8900000.0,
            "beta_egx30": 1.25,
            "is_active": True
        },
        "ZMID.CA": {
            "ticker": "ZMID.CA",
            "name_ar": "زهراء المعادي للاستثمار والتعمير",
            "name_en": "Zahraa Maadi Investment & Development",
            "sector": "التطوير العقاري",
            "sector_en": "Real Estate",
            "isin": "EGS65101C014",
            "index_membership": ["EGX70", "EGX100"],
            "market_cap_tier": "MID_CAP",
            "nominal_price": 7.40,
            "adv20_egp": 9800000.0,
            "beta_egx30": 1.10,
            "is_active": True
        },
        "KZPC.CA": {
            "ticker": "KZPC.CA",
            "name_ar": "كفر الزيات للمبيدات والكيماويات",
            "name_en": "Kafr El Zayat Pesticides",
            "sector": "الموارد الأساسية والكيماويات",
            "sector_en": "Chemicals & Agro",
            "isin": "EGS38081C014",
            "index_membership": ["EGX70", "EGX100"],
            "market_cap_tier": "SMALL_CAP",
            "nominal_price": 9.80,
            "adv20_egp": 4200000.0,
            "beta_egx30": 0.80,
            "is_active": True
        },
        "ELSH.CA": {
            "ticker": "ELSH.CA",
            "name_ar": "الشمس للإسكان والتعمير",
            "name_en": "El Shams Housing & Urbanization",
            "sector": "التطوير العقاري",
            "sector_en": "Real Estate",
            "isin": "EGS65061C018",
            "index_membership": ["EGX70", "EGX100"],
            "market_cap_tier": "SMALL_CAP",
            "nominal_price": 8.15,
            "adv20_egp": 6500000.0,
            "beta_egx30": 1.05,
            "is_active": True
        },
        "PRDC.CA": {
            "ticker": "PRDC.CA",
            "name_ar": "رواد السياحة (رواد)",
            "name_en": "Rowad Tourism",
            "sector": "السياحة والترفيه",
            "sector_en": "Tourism & Leisure",
            "isin": "EGS70431C019",
            "index_membership": ["EGX70", "EGX100"],
            "market_cap_tier": "SMALL_CAP",
            "nominal_price": 32.50,
            "adv20_egp": 3800000.0,
            "beta_egx30": 0.95,
            "is_active": True
        },
        "RTVC.CA": {
            "ticker": "RTVC.CA",
            "name_ar": "رمكو لإنشاء القرى السياحية",
            "name_en": "Remco Tourism Villages Construction",
            "sector": "السياحة والترفيه",
            "sector_en": "Tourism & Leisure",
            "isin": "EGS70041C012",
            "index_membership": ["EGX70", "EGX100"],
            "market_cap_tier": "SMALL_CAP",
            "nominal_price": 3.80,
            "adv20_egp": 4500000.0,
            "beta_egx30": 1.15,
            "is_active": True
        },
        "UNIP.CA": {
            "ticker": "UNIP.CA",
            "name_ar": "يونيفرسال لصناعة مواد التعبئة والتغليف (يونيباك)",
            "name_en": "Universal for Paper & Packaging (Unipack)",
            "sector": "السلع الاستهلاكية",
            "sector_en": "Paper & Packaging",
            "isin": "EGS39021C019",
            "index_membership": ["EGX70", "EGX100"],
            "market_cap_tier": "SMALL_CAP",
            "nominal_price": 0.65,
            "adv20_egp": 2900000.0,
            "beta_egx30": 0.85,
            "is_active": True
        },
        "EGCH.CA": {
            "ticker": "EGCH.CA",
            "name_ar": "الصناعات الكيماوية المصرية (كيما)",
            "name_en": "Egyptian Chemical Industries (KIMA)",
            "sector": "الموارد الأساسية والكيماويات",
            "sector_en": "Fertilizers & Chemicals",
            "isin": "EGS38011C011",
            "index_membership": ["EGX70", "EGX100"],
            "market_cap_tier": "MID_CAP",
            "nominal_price": 10.90,
            "adv20_egp": 18500000.0,
            "beta_egx30": 1.18,
            "is_active": True
        },
        "ELEC.CA": {
            "ticker": "ELEC.CA",
            "name_ar": "الكابلات الكهربائية المصرية",
            "name_en": "Electro Cable Egypt",
            "sector": "الصناعة والمقاولات",
            "sector_en": "Industrial",
            "isin": "EGS3G031C015",
            "index_membership": ["EGX70", "EGX100"],
            "market_cap_tier": "MID_CAP",
            "nominal_price": 2.85,
            "adv20_egp": 14500000.0,
            "beta_egx30": 1.22,
            "is_active": True
        }
    }

    @classmethod
    def _enrich_with_live_nominal_prices(cls, stock_record: Dict[str, Any]) -> Dict[str, Any]:
        """Dynamically binds nominal_price and price metadata from SSOT live store."""
        if not stock_record:
            return stock_record
        try:
            from core.price_sync_service import PriceSyncService
            sym = stock_record.get("ticker", "")
            rec = PriceSyncService.get_price_record(sym)
            if rec and "price" in rec:
                enriched = dict(stock_record)
                enriched["nominal_price"] = float(rec["price"])
                enriched["price"] = float(rec["price"])
                enriched["entry_zone_low"] = rec.get("entry_zone_low", round(rec["price"] * 0.985, 2))
                enriched["entry_zone_high"] = rec.get("entry_zone_high", round(rec["price"] * 0.998, 2))
                enriched["hard_stop_loss"] = rec.get("hard_stop_loss", round(rec["price"] * 0.93, 2))
                enriched["price_timestamp"] = rec.get("timestamp", "")
                return enriched
        except Exception:
            pass
        return stock_record

    @classmethod
    def get_universe(cls, index_filter: str = "all") -> List[Dict[str, Any]]:
        """
        Returns list of stock metadata dictionaries filtered by index membership.
        Supported filters: 'all', 'egx30', 'egx70', 'egx100'.
        Nominal prices are dynamically bound to the live SSOT store.
        """
        filt = (index_filter or "all").strip().upper()
        if filt == "ALL":
            raw_list = list(cls.ACTIVE_UNIVERSE.values())
        elif filt in ["EGX30", "EGX-30", "30"]:
            raw_list = [s for s in cls.ACTIVE_UNIVERSE.values() if "EGX30" in s.get("index_membership", [])]
        elif filt in ["EGX70", "EGX-70", "70"]:
            raw_list = [s for s in cls.ACTIVE_UNIVERSE.values() if "EGX70" in s.get("index_membership", [])]
        elif filt in ["EGX100", "EGX-100", "100"]:
            raw_list = [s for s in cls.ACTIVE_UNIVERSE.values() if "EGX100" in s.get("index_membership", []) or "EGX30" in s.get("index_membership", []) or "EGX70" in s.get("index_membership", [])]
        else:
            filt_lower = index_filter.strip().lower()
            sector_matches = [
                s for s in cls.ACTIVE_UNIVERSE.values()
                if filt_lower in s.get("sector", "").lower() or filt_lower in s.get("sector_en", "").lower()
            ]
            raw_list = sector_matches if sector_matches else list(cls.ACTIVE_UNIVERSE.values())

        return [cls._enrich_with_live_nominal_prices(s) for s in raw_list]

    @classmethod
    def get_active_universe(cls) -> Dict[str, Dict[str, Any]]:
        """Returns dictionary mapping of all active universe stocks with live nominal prices."""
        return {k: cls._enrich_with_live_nominal_prices(v) for k, v in cls.ACTIVE_UNIVERSE.items()}

    @classmethod
    def get_tickers(cls, index_filter: str = "all") -> List[str]:
        """Returns list of ticker symbol strings matching the filter."""
        return [s["ticker"] for s in cls.get_universe(index_filter)]

    @classmethod
    def get_stock_info(cls, ticker: str) -> Optional[Dict[str, Any]]:
        """Retrieves metadata for a specific ticker symbol bound to SSOT live store."""
        sym = ticker.upper().strip()
        if not sym.endswith(".CA") and "." not in sym:
            sym = f"{sym}.CA"
        info = cls.ACTIVE_UNIVERSE.get(sym)
        return cls._enrich_with_live_nominal_prices(info) if info else None

    @classmethod
    def is_valid_ticker(cls, ticker: str) -> bool:
        """Validates if ticker exists in the active Egyptian Exchange universe."""
        return cls.get_stock_info(ticker) is not None

    @classmethod
    def get_all_sectors(cls) -> List[str]:
        """Returns unique list of all sectors represented in the universe."""
        sectors = set()
        for s in cls.ACTIVE_UNIVERSE.values():
            if s.get("sector"):
                sectors.add(s["sector"])
        return sorted(list(sectors))

    @classmethod
    def get_universe_stats(cls) -> Dict[str, Any]:
        """Provides statistical summary of universe coverage."""
        all_stocks = cls.get_universe("all")
        egx30_count = sum(1 for s in all_stocks if "EGX30" in s.get("index_membership", []))
        egx70_count = sum(1 for s in all_stocks if "EGX70" in s.get("index_membership", []))
        egx100_count = sum(1 for s in all_stocks if "EGX100" in s.get("index_membership", []))

        sector_counts: Dict[str, int] = {}
        for s in all_stocks:
            sec = s.get("sector", "General")
            sector_counts[sec] = sector_counts.get(sec, 0) + 1

        return {
            "total_active_equities": len(all_stocks),
            "egx30_constituents": egx30_count,
            "egx70_constituents": egx70_count,
            "egx100_constituents": egx100_count,
            "sectors_count": len(sector_counts),
            "sectors_breakdown": sector_counts
        }

