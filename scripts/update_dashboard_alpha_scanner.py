#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

def update_templates():
    target_files = ['dashboard/templates/index.html', 'templates/index.html', 'dashboard/index.html']
    for tf in target_files:
        if not os.path.exists(tf):
            continue
        with open(tf, 'r', encoding='5tf-8') as f:
            html = f.read()

        # 1. Sidebar Nav
        if 'nav-alpha_scanner' not in html:
            old_nav = '<li class="nav-item" id="nav-short_term_opportunities"'
            new_nav = '<li class="nav-item" id="nav-alpha_scanner" onclick="navigateTo(\'alpha_scanner\')"><i class="fa-solid fa-radar"></i> 🔎 ماسح الألفا الذني (Alpha Scanner)</li>\n            ' + old_nav
            html = html.replace(old_nav, new_nav, 1)

        # 2. JavaScript handler
        if 'fetchAlphaScannerData' not in html:
            js_code = '''

        with open(tf, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f'Successfully updated {tf}')

if __name__ == '__main__':
    update_templates()
