#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
html_path = os.path.join(WORKSPACE, "templates", "index.html")

with open(html_path, "r", encoding="utf-8") as f:
    c = f.read()

replacements = [
    # Tape
    ('id="tape-egx30">51,492.80</span>', 'id="tape-egx30">52,089.00</span>'),
    ('id="tape-egx70">18,330.80</span>', 'id="tape-egx70">17,903.70</span>'),
    ('id="tape-egx100">30,735.60</span>', 'id="tape-egx100">24,013.00</span>'),
    ('id="tape-equity">13,274.93 ج.م</span> <span class="ticker-change up">(صافي أرباح: +808.30 ج.م / +6.17%)</span>', 'id="tape-equity">13,463.43 ج.م</span> <span class="ticker-change up">(صافي أرباح: +996.87 ج.م / +8.00%)</span>'),
    ('id="tape-COMI">122.00</span>', 'id="tape-COMI">125.90</span>'),
    ('id="tape-SWDY">114.00</span>', 'id="tape-SWDY">111.00</span>'),
    ('id="tape-TMGH">83.94</span>', 'id="tape-TMGH">84.79</span>'),
    ('id="tape-PHDC">12.75</span>', 'id="tape-PHDC">12.93</span>'),
    ('id="tape-RAYA">5.89</span>', 'id="tape-RAYA">5.90</span>'),
    ('id="tape-MFPC">44.01</span>', 'id="tape-MFPC">46.42</span>'),
    ('id="tape-ABUK">84.34</span>', 'id="tape-ABUK">93.50</span>'),
    ('id="tape-AMOC">13.56</span>', 'id="tape-AMOC">13.65</span>'),
    ('id="tape-FWRY">18.40</span>', 'id="tape-FWRY">18.61</span>'),
    ('id="tape-ETEL">145.00</span>', 'id="tape-ETEL">142.00</span>'),
    ('id="tape-ORAS">907.00</span>', 'id="tape-ORAS">870.00</span>'),

    # Hero & detail prices
    ('<div class="hero-pick-price"><span class="ltr-text">122.00</span> ج.م</div>', '<div class="hero-pick-price"><span class="ltr-text">125.90</span> ج.م</div>'),
    ('id="hero-price" class="ltr-text">122.00</span>', 'id="hero-price" class="ltr-text">125.90</span>'),
    ('id="detail-current-price">122.00</span>', 'id="detail-current-price">125.90</span>'),
    ('id="cam-pivot-val">122.00 ج.م</strong>', 'id="cam-pivot-val">125.90 ج.م</strong>'),
    ('id="meter-current-price">122.00</span>', 'id="meter-current-price">125.90</span>'),

    # Options
    ('البنك التجاري الدولي (COMI.CA) — 122.00 ج.م', 'البنك التجاري الدولي (COMI.CA) — 125.90 ج.م'),
    ('السويدي إليكتريك (SWDY.CA) — 114.00 ج.م', 'السويدي إليكتريك (SWDY.CA) — 111.00 ج.م'),
    ('مجموعة طلعت مصطفى (TMGH.CA) — 83.94 ج.م', 'مجموعة طلعت مصطفى (TMGH.CA) — 84.79 ج.م'),
    ('بالم هيلز للتعمير (PHDC.CA) — 12.75 ج.م', 'بالم هيلز للتعمير (PHDC.CA) — 12.93 ج.م'),
    ('راية القابضة (RAYA.CA) — 5.89 ج.م', 'راية القابضة (RAYA.CA) — 5.90 ج.م'),
    ('أوراسكوم للإنشاء (ORAS.CA) — 907.00 ج.م', 'أوراسكوم للإنشاء (ORAS.CA) — 870.00 ج.م'),
    ('المصرية للاتصالات (ETEL.CA) — 145.00 ج.م', 'المصرية للاتصالات (ETEL.CA) — 142.00 ج.م'),
    ('أبو قير للأسمدة (ABUK.CA) — 84.34 ج.م', 'أبو قير للأسمدة (ABUK.CA) — 93.50 ج.م'),
    ('مصر لإنتاج الأسمدة (MFPC.CA) — 44.01 ج.م', 'مصر لإنتاج الأسمدة (MFPC.CA) — 46.42 ج.م'),

    # Table rows in static html
    ('<td style="text-align: center; font-weight: 700;" class="ltr-text font-mono">122.00</td>', '<td style="text-align: center; font-weight: 700;" class="ltr-text font-mono">125.90</td>'),
    ('<td class="font-mono">122.00 ج.م</td>', '<td class="font-mono">125.90 ج.م</td>'),
    ('id="ta-res-price" style="font-weight: 800; font-size: 16px; margin-right: 6px;">122.00 ج.م</span>', 'id="ta-res-price" style="font-weight: 800; font-size: 16px; margin-right: 6px;">125.90 ج.م</span>'),

    # Fallbacks in script
    ("top1.ticker === 'SWDY.CA' ? 114.00 : (top1.ticker === 'TMGH.CA' ? 83.94 : 122.00)", "top1.ticker === 'SWDY.CA' ? 111.00 : (top1.ticker === 'TMGH.CA' ? 84.79 : 125.90)"),
    ("p.ticker === 'SWDY.CA' ? 114.00 : (p.ticker === 'TMGH.CA' ? 83.94 : 122.00)", "p.ticker === 'SWDY.CA' ? 111.00 : (p.ticker === 'TMGH.CA' ? 84.79 : 125.90)"),
    ("data.egx30_level || 51492.80", "data.egx30_level || 52089.00"),
    ('{ name_ar: "البنك التجاري الدولي (CIB)", ticker: "COMI.CA", price: 122.00, current_price: 122.00 }', '{ name_ar: "البنك التجاري الدولي (CIB)", ticker: "COMI.CA", price: 125.90, current_price: 125.90 }'),
    ('{ name_ar: "السويدي إليكتريك", ticker: "SWDY.CA", price: 114.00, current_price: 114.00 }', '{ name_ar: "السويدي إليكتريك", ticker: "SWDY.CA", price: 111.00, current_price: 111.00 }'),
    ('{ name_ar: "مجموعة طلعت مصطفى", ticker: "TMGH.CA", price: 83.94, current_price: 83.94 }', '{ name_ar: "مجموعة طلعت مصطفى", ticker: "TMGH.CA", price: 84.79, current_price: 84.79 }'),
    ('(idx === 0 ? 122.00 : idx === 1 ? 114.00 : 83.94)', '(idx === 0 ? 125.90 : idx === 1 ? 111.00 : 84.79)'),
    ('{ ticker: "COMI.CA", name_ar: "البنك التجاري الدولي (CIB)", price: 122.00, current_price: 122.00', '{ ticker: "COMI.CA", name_ar: "البنك التجاري الدولي (CIB)", price: 125.90, current_price: 125.90'),
    ('{ ticker: "SWDY.CA", name_ar: "السويدي إليكتريك", price: 114.00, current_price: 114.00', '{ ticker: "SWDY.CA", name_ar: "السويدي إليكتريك", price: 111.00, current_price: 111.00'),
    ('{ ticker: "TMGH.CA", name_ar: "مجموعة طلعت مصطفى", price: 83.94, current_price: 83.94', '{ ticker: "TMGH.CA", name_ar: "مجموعة طلعت مصطفى", price: 84.79, current_price: 84.79'),

    # THNDR_SIM_PORTFOLIO
    ("'COMI.CA': { name: 'البنك التجاري الدولي', shares: 50, avg: 120.83, curr: 122.00, dropFloor: 118.00, bounceTarget: 128.50 }", "'COMI.CA': { name: 'البنك التجاري الدولي', shares: 45, avg: 134.26, curr: 125.90, dropFloor: 122.50, bounceTarget: 135.54 }"),
    ("'SWDY.CA': { name: 'السويدي إليكتريك', shares: 14, avg: 107.56, curr: 114.00, dropFloor: 112.50, bounceTarget: 123.12 }", "'SWDY.CA': { name: 'السويدي إليكتريك', shares: 13, avg: 115.83, curr: 111.00, dropFloor: 108.50, bounceTarget: 116.93 }"),
    ("'TMGH.CA': { name: 'مجموعة طلعت مصطفى', shares: 26, avg: 83.17, curr: 83.94, dropFloor: 81.00, bounceTarget: 91.50 }", "'TMGH.CA': { name: 'مجموعة طلعت مصطفى', shares: 25, avg: 86.50, curr: 84.79, dropFloor: 82.90, bounceTarget: 87.32 }"),
    ("'PHDC.CA': { name: 'بالم هيلز للتعمير', shares: 180, avg: 12.11, curr: 12.75, dropFloor: 12.20, bounceTarget: 13.90 }", "'PHDC.CA': { name: 'بالم هيلز للتعمير', shares: 162, avg: 13.46, curr: 12.93, dropFloor: 12.56, bounceTarget: 13.59 }"),
    ("'RAYA.CA': { name: 'راية القابضة', shares: 220, avg: 5.47, curr: 5.89, dropFloor: 5.60, bounceTarget: 6.45 }", "'RAYA.CA': { name: 'راية القابضة', shares: 159, avg: 7.57, curr: 5.90, dropFloor: 5.75, bounceTarget: 7.64 }"),

    # fallbackMatrix
    ('{ ticker: "COMI.CA", name_ar: "البنك التجاري الدولي", current_price: 122.0, min_dip_price: 120.5, final_target: 138.5, expected_return_pct: 13.5, net_breakeven: 135.54, is_portfolio_holding: true }', '{ ticker: "COMI.CA", name_ar: "البنك التجاري الدولي", current_price: 125.90, min_dip_price: 122.5, final_target: 138.5, expected_return_pct: 10.0, net_breakeven: 135.54, is_portfolio_holding: true }'),
    ('{ ticker: "TMGH.CA", name_ar: "طلعت مصطفى", current_price: 83.94, min_dip_price: 82.5, final_target: 95.8, expected_return_pct: 14.1, net_breakeven: 87.32, is_portfolio_holding: true }', '{ ticker: "TMGH.CA", name_ar: "طلعت مصطفى", current_price: 84.79, min_dip_price: 82.9, final_target: 95.8, expected_return_pct: 13.0, net_breakeven: 87.32, is_portfolio_holding: true }'),
    ('{ ticker: "SWDY.CA", name_ar: "السويدي إليكتريك", current_price: 114.0, min_dip_price: 112.0, final_target: 131.0, expected_return_pct: 14.9, net_breakeven: 116.93, is_portfolio_holding: true }', '{ ticker: "SWDY.CA", name_ar: "السويدي إليكتريك", current_price: 111.00, min_dip_price: 108.5, final_target: 124.5, expected_return_pct: 12.2, net_breakeven: 116.93, is_portfolio_holding: true }'),
    ('{ ticker: "PHDC.CA", name_ar: "بالم هيلز", current_price: 12.75, min_dip_price: 12.5, final_target: 14.8, expected_return_pct: 16.1, net_breakeven: 13.59, is_portfolio_holding: true }', '{ ticker: "PHDC.CA", name_ar: "بالم هيلز", current_price: 12.93, min_dip_price: 12.56, final_target: 14.8, expected_return_pct: 14.5, net_breakeven: 13.59, is_portfolio_holding: true }'),
    ('{ ticker: "RAYA.CA", name_ar: "راية القابضة", current_price: 5.89, min_dip_price: 5.75, final_target: 7.2, expected_return_pct: 22.2, net_breakeven: 7.64, is_portfolio_holding: true }', '{ ticker: "RAYA.CA", name_ar: "راية القابضة", current_price: 5.90, min_dip_price: 5.75, final_target: 7.2, expected_return_pct: 22.0, net_breakeven: 7.64, is_portfolio_holding: true }'),

    # Overrides placeholders
    ('id="thndr-override-COMI" class="form-control ltr-text font-mono" placeholder="122.00"', 'id="thndr-override-COMI" class="form-control ltr-text font-mono" placeholder="125.90"'),
    ('id="thndr-override-TMGH" class="form-control ltr-text font-mono" placeholder="83.94"', 'id="thndr-override-TMGH" class="form-control ltr-text font-mono" placeholder="84.79"'),
    ('id="thndr-override-SWDY" class="form-control ltr-text font-mono" placeholder="114.00"', 'id="thndr-override-SWDY" class="form-control ltr-text font-mono" placeholder="111.00"'),
    ('id="thndr-override-PHDC" class="form-control ltr-text font-mono" placeholder="12.75"', 'id="thndr-override-PHDC" class="form-control ltr-text font-mono" placeholder="12.93"'),
    ('id="thndr-override-RAYA" class="form-control ltr-text font-mono" placeholder="5.89"', 'id="thndr-override-RAYA" class="form-control ltr-text font-mono" placeholder="5.90"')
]

made = 0
for old, new in replacements:
    if old in c:
        c = c.replace(old, new)
        made += 1

with open(html_path, "w", encoding="utf-8") as f:
    f.write(c)

print(f"Successfully applied {made} replacements to templates/index.html!")
