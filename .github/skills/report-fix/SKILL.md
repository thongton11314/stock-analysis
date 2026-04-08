---
name: report-fix
description: >
  Fix, debug, or improve existing stock analysis HTML reports.
  USE FOR: "fix the PDF layout", "the chart is broken", "styling issue", "card is too tall",
  "section is missing", "update the data", "fix print layout", CSS problems, SVG chart issues,
  PDF export problems, layout bugs, missing sections, wrong colors, broken links.
  DO NOT USE FOR: generating new reports from scratch (use report-generation skill).
---

# Report Fix & Debug Skill

## Overview
Diagnose and fix issues in existing stock analysis HTML reports in `reports/`. Common issues: PDF layout breaks, oversized cards, SVG rendering, missing sections, styling drift.

## Diagnostic Workflow

### Step 1: Identify the Problem Category

| Symptom | Category | Reference File |
|---|---|---|
| Cards overflow PDF pages | **Card splitting** | `.instructions/report-layout.md` |
| Colors wrong, badges misaligned | **Styling** | `.instructions/styling.md` |
| SVG chart not rendering | **SVG corridor chart** | `.instructions/analysis-methodology.md` |
| Sections out of order or missing | **Layout order** | `.instructions/report-layout.md` |
| Print/PDF cuts off content | **PDF export** | `.instructions/styling.md` |
| Support & Resistance overlap or wrong style | **Layout** | Use pill badge style: green support badges (`#d4edda`), red resistance badges (`#f8d7da`). Never use plain text lists with colored headers |
| Bullet points show squares | **Unicode** | Use CSS `\25B8`, not HTML entities |
| News items have no links | **Hyperlinks** | Every `.news-title a` needs `href` |
| Competitive table unstyled | **Peer table** | `.instructions/analysis-methodology.md` |
| Fed chart values wrong/fabricated | **Macro data** | Cross-check vs HOOD gold standard; re-fetch if only 1 API data point |
| Macro data differs across reports | **Cross-report consistency** | CPI, FFR, Unemployment, GDP are market-wide; must match all reports |
| Narrative analysis box missing or empty | **Narrative** | `.instructions/report-layout.md` (7-element inventory + integrity rules) |

### Step 2: Load Context
1. Read the affected report file from `reports/`
2. Read `templates/report-template.html` for the correct CSS baseline
3. Read the relevant `.instructions/` file for the spec

### Step 3: Apply Fix

#### Common Fixes Quick Reference

**Card too tall for PDF:**
- Split into multiple `<div class="card full-width">` blocks, each with its own `<h2>`
- Max ~60% of A4 landscape height per card

**Wrong bullet characters:**
```css
/* CORRECT */
.summary-col li::before { content: "\25B8"; }
/* WRONG — never do this */
<li>&#9656; Some text</li>
```

**Support & Resistance wrong style or overlap:**
```html
<!-- CORRECT — pill badge layout (green support, red resistance) -->
<div style="display:flex; gap:6px; flex-wrap:wrap;">
  <span style="background:#d4edda; color:#155724; padding:3px 8px; border-radius:3px; font-size:0.75em; font-weight:600;">$200.00 (Psychological)</span>
</div>
<!-- WRONG — never use text lists with colored headers -->
<div style="color:#dc2626;">SUPPORT</div>
<div>$200.00 Psychological</div>
```

**SVG corridors not visible:**
- Check polygon order: fills FIRST, then polylines on top
- Check viewBox: should be `"0 0 600 200"`
- Check polygon opacity: 0.15-0.25 for corridor fills

**Missing narrative analysis box:**
Every report requires exactly 7 interpretive elements. If any narrative is missing, add the styled box at the correct position:
- S10: Below `.sankey-legend`, title "Income Statement Analysis"
- S11: Below Row 3 signal tiles, title "Technical Analysis Summary"
- S14: Below ownership/transactions flex container, title "Ownership & Insider Activity Analysis"
- S15: Below Fed chart analysis line, title "Macro Environment Analysis"
```html
<!-- CORRECT narrative box pattern -->
<div style="background:#f8fafc; border:1px solid #e8ecf3; border-radius:6px; padding:12px; margin-top:10px;">
    <div style="font-size:0.82em; font-weight:700; color:#1b2a4a; margin-bottom:4px;">{{TITLE}}</div>
    <div style="font-size:0.78em; color:#5a6577; line-height:1.5;">3-5 sentences, data-grounded, standalone per ticker, no cross-ticker references, no fabricated data.</div>
</div>
```

**PDF colors missing:**
```css
body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
```

**Export bar visible in PDF:**
```css
@media print { .export-bar { display: none !important; } }
```

### Step 4: Verify
- Compare fixed report against `templates/report-template.html` CSS
- Check all 20 sections are present and in order
- Confirm Price Target is split into 3 cards
- Test: open in browser → Ctrl+P → verify A4 landscape layout
