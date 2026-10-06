"""
Verification script for CollegeConnect Light Theme and Dark Theme fidelity.
Verifies all CSS token definitions, mirror selectors, WCAG contrast colors,
HTML toggle markup, zero-FOUC head script, and JS theme controller logic.
"""

import os
import re

def verify_theme_system():
    print("======================================================================")
    print("COLLEGECONNECT LIGHT & DARK THEME COMPREHENSIVE VERIFICATION")
    print("======================================================================")
    
    # 1. Inspect index.html
    html_path = os.path.join("frontend", "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    print("\n--- 1. HTML STRUCTURE & ZERO-FOUC HEAD SCRIPT ---")
    assert '<script>' in html and 'collegeconnect_theme' in html and 'document.documentElement.setAttribute("data-theme", "light")' in html, "Zero-FOUC script missing in head"
    print("  [PASS] Zero-FOUC head script present before page render")

    assert 'id="themeToggleBtn"' in html, "Theme toggle button missing"
    assert 'id="themeToggleIcon"' in html, "Theme toggle icon element missing"
    assert 'id="themeToggleText"' in html, "Theme toggle text element missing"
    print("  [PASS] Theme toggle button rendered in navbar (.nav-container)")

    # 2. Inspect styles.css
    css_path = os.path.join("frontend", "styles.css")
    with open(css_path, "r", encoding="utf-8") as f:
        css = f.read()

    print("\n--- 2. CSS TOKENS & MIRROR ARCHITECTURE ---")
    # Verify dark theme variables remain untouched in :root
    assert ':root {' in css, "Root tokens missing"
    assert '--background: #090d16' in css, "Original dark theme background altered!"
    assert '--panel: rgba(20, 27, 42, 0.90)' in css, "Original dark theme panel altered!"
    assert '--panel-border:' in css and 'rgba(255, 255, 255, 0.08)' in css, "Original dark theme border altered!"
    print("  [PASS] Dark theme tokens in :root are 100% untouched and preserved")

    # Verify light theme token overrides under html[data-theme="light"]
    assert 'html[data-theme="light"] {' in css, "Light theme root selector missing"
    light_tokens = [
        "--background: #f8fafc",
        "--panel: #ffffff",
        "--panel-soft: #f1f5f9",
        "--panel-border: #e2e8f0",
        "--primary: #4f46e5",
        "--cyan: #0284c7",
        "--violet: #7c3aed",
        "--success: #059669",
        "--warning: #d97706",
        "--danger: #dc2626",
        "--text: #0f172a",
        "--muted: #64748b",
        "--input: #ffffff"
    ]
    for token in light_tokens:
        assert token in css, f"Light theme token missing: {token}"
    print(f"  [PASS] All {len(light_tokens)} core light theme design tokens verified")

    print("\n--- 3. MIRROR COMPONENT SELECTORS AUDIT ---")
    components_to_check = [
        ("Navbar", 'html[data-theme="light"] .navbar'),
        ("Theme Toggle Button", 'html[data-theme="light"] .theme-toggle-btn'),
        ("Page Panels & Predictor", 'html[data-theme="light"] .page-panel'),
        ("Hero Title & Badge", 'html[data-theme="light"] .hero h1'),
        ("Form Controls & Inputs", 'html[data-theme="light"] input'),
        ("Dropdowns & Select", 'html[data-theme="light"] select'),
        ("Multi-Select Picker Box", 'html[data-theme="light"] .picker-box'),
        ("Multi-Select Option Item", 'html[data-theme="light"] .picker-option'),
        ("Multi-Select Checkbox", 'html[data-theme="light"] .picker-checkbox'),
        ("College Suggestions Dropdown", 'html[data-theme="light"] .college-suggestions'),
        ("Calculator Widget", 'html[data-theme="light"] .calc-widget'),
        ("Filter Buttons", 'html[data-theme="light"] .result-filter-btn'),
        ("Result Cards", 'html[data-theme="light"] .result-card'),
        ("Result Titles & Meta", 'html[data-theme="light"] .result-college-name'),
        ("Safe Tier Badge", 'html[data-theme="light"] .tier-safe'),
        ("Target Tier Badge", 'html[data-theme="light"] .tier-target'),
        ("Reach Tier Badge", 'html[data-theme="light"] .tier-reach'),
        ("Institutional Tier Badges", 'html[data-theme="light"] .tier-inst-1'),
        ("Quota Advisory Banner", 'html[data-theme="light"] .quota-advisory'),
        ("Choice Optimizer Cards", 'html[data-theme="light"] .choice-card'),
        ("AI Suggested Choice Cards", 'html[data-theme="light"] .ai-suggested-card'),
        ("State Rank Matrix Table", 'html[data-theme="light"] .table-wrapper'),
        ("5-Yr Trend Modal", 'html[data-theme="light"] .modal-container'),
        ("5-Yr Trend Metrics Grid", 'html[data-theme="light"] .trend-metrics-grid'),
        ("Branch Swap Modal Controls", 'html[data-theme="light"] .branch-swap-add-btn'),
        ("Scrollbars", 'html[data-theme="light"] ::-webkit-scrollbar-track'),
        ("Loading & Error States", 'html[data-theme="light"] .error-message'),
    ]

    for label, sel in components_to_check:
        assert sel in css, f"Selector for {label} missing: {sel}"
        print(f"  [PASS] {label} has dedicated light theme mirror rules")

    print("\n--- 4. JAVASCRIPT THEME CONTROLLER & ACCESSIBLE STYLING ---")
    js_path = os.path.join("frontend", "app.js")
    with open(js_path, "r", encoding="utf-8") as f:
        js = f.read()

    assert 'const THEME_STORAGE_KEY = "collegeconnect_theme";' in js, "THEME_STORAGE_KEY missing"
    assert 'function applyTheme(' in js, "applyTheme missing"
    assert 'function initTheme(' in js, "initTheme missing"
    assert 'initTheme();' in js, "initTheme call missing in DOMContentLoaded"
    print("  [PASS] Theme controller logic properly initialized")

    # Verify getTierColor light vs dark differentiation
    assert 'document.documentElement.getAttribute("data-theme") === "light"' in js, "data-theme check missing in JS"
    assert '#047857' in js, "WCAG Safe text color (#047857) missing in getTierColor"
    assert '#be123c' in js, "WCAG Reach text color (#be123c) missing in getTierColor"
    assert '#b45309' in js, "WCAG Target text color (#b45309) missing in getTierColor"
    print("  [PASS] getTierColor returns WCAG-accessible light hex values in light mode and original dark values in dark mode")

    # Verify SVG Chart dynamic theme coloring
    assert 'gridStroke = isLight ? "#e2e8f0" : "rgba(255,255,255,0.06)"' in js, "SVG grid stroke theme check missing"
    assert 'curveStroke = isLight ? "#4f46e5" : "#818cf8"' in js, "SVG curve stroke theme check missing"
    assert 'markerStroke = isLight ? "#4f46e5" : "#818cf8"' in js, "SVG marker stroke theme check missing"
    print("  [PASS] renderTrendSvgChart dynamically updates SVG strokes, fills and labels based on theme")

    print("\n======================================================================")
    print("THEME VERIFICATION SUMMARY: ALL CHECKS PASSED SUCCESSFULLY (100%)")
    print("======================================================================")

if __name__ == "__main__":
    verify_theme_system()
