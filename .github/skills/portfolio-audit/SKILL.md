---
name: portfolio-audit
description: >
  Audit the portfolio dashboard HTML page across 8 layers: structure, data accuracy,
  links, aggregates, styling, layout/alignment, text quality, and numerical accuracy.
  USE FOR: "audit portfolio", "check portfolio", "validate portfolio page",
  "verify portfolio data", "portfolio integrity check", "portfolio QA".
  DO NOT USE FOR: building the portfolio page (use portfolio-build), analyzing
  individual stocks (use report-generation), auditing individual reports (use report-audit).
---

# Portfolio Audit Skill

## Overview
Validates `portfolio-manager/portfolio.html` across 8 comprehensive layers — from structural
completeness through styling compliance to numerical accuracy. The automated
`scripts/audit_portfolio.py` script runs all checks and reports results.

## Prerequisites
- `portfolio-manager/portfolio.html` exists
- `scripts/output/portfolio_summary.json` exists
- `scripts/output/portfolio_optimization.json` exists
- Source signal JSONs + data bundles in `scripts/output/` and `scripts/data/`

## Audit Layers (8 Total)

### L1: Structural Completeness (19 checks)
All 16 sections present (Export Bar through Timestamp), summary card count, section heading count.

### L2: Data Accuracy (per-ticker checks)
For each ticker: appears in holdings, links to report, fragility score matches `_short_term.json`,
CCRLO matches `_ccrlo.json`, primary tag matches `_tags.json`, regime matches `_simulation.json`.

### L3: Link Integrity (4+ checks)
Report links count, each linked file exists on disk, export button has onclick,
no dead `href="#"` links that should be real.

### L4: Aggregate Metrics (8 checks)
Total tickers, avg fragility, avg CCRLO, dominant regime match `portfolio_summary.json`.
Optimizer method, stress test count, strategy framework, weights sum ~100%
match `portfolio_optimization.json`.

### L5: Styling Compliance (15 checks)
No CSS Grid (flexbox only), A4 landscape, page-break-inside, signal/tag badge classes,
export hidden in print, print-color-adjust, Segoe UI font, 13px base,
background #f4f6f9, header #1b2a4a, card #fff, bullish #16a34a, bearish #dc2626,
amber #d97706.

### L6: Layout & Alignment (10 checks)
Container 1140px, flexbox count ≥10, card border-radius 6px, card border #dde3ed,
H2 border-bottom, table border-collapse, score tile border-left, grid sections ≥5,
full-width cards ≥5, disclaimer border.

### L7: Text & Content Quality (8 checks)
No unreplaced `{{PLACEHOLDER}}` markers, no NaN values, no Python `None` in content,
empty table cells <5, DOCTYPE present, HTML lang=en, title tag, timestamp date.

### L8: Numerical Accuracy (per-ticker + optimizer checks)
Each ticker's price `$XXX.XX` traceable to bundle, change percent traceable,
optimized weight percentages match, stress test impacts match, portfolio beta and
drawdown score match source JSONs.

## Workflow

### Step 1: Run Automated Audit
```bash
python scripts/audit_portfolio.py                # Text output
python scripts/audit_portfolio.py --json          # Save JSON report
```

### Step 2: Review Results
Each layer prints pass/fail. Fix any failures before declaring complete.

### Step 3: Fix Issues
- L1 failures → rebuild missing section (re-run `build_portfolio.py`)
- L2 failures → data mismatch, re-run pipeline
- L3 failures → missing report files, generate with `@stock-analyst`
- L4 failures → aggregate computation error
- L5 failures → CSS violation, fix template
- L6 failures → layout broken, fix template
- L7 failures → content corruption, rebuild
- L8 failures → number mismatch, re-run optimizer or rebuild

## Critical Rules
1. **Automated first** — always run `audit_portfolio.py` before manual checks
2. **Fix before declaring done** — never report PASS with known failures
3. **Source of truth** — signal JSONs and data bundles are the source; HTML must match
4. **8 layers, not 5** — the old 5-layer audit is replaced by this comprehensive 8-layer version
