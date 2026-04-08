---
name: portfolio-build
description: >
  Build or update the portfolio dashboard HTML page that aggregates all analyzed tickers
  into a single view with holdings table, risk heatmap, sector allocation, signal dashboard,
  and links to individual ticker reports.
  USE FOR: "build portfolio", "update portfolio", "portfolio dashboard", "portfolio view",
  "show portfolio", "refresh portfolio page", "add ticker to portfolio", "portfolio summary".
  DO NOT USE FOR: analyzing individual stocks (use report-generation), auditing the portfolio
  page (use portfolio-audit), computing signals (use analyst-compute-engine).
---

# Portfolio Build Skill

## Overview
Generates or updates `portfolio-manager/portfolio.html` — a static HTML dashboard that aggregates
all analyzed tickers into a unified portfolio view. The page sources all data from
existing signal JSONs, tag data, and data bundles produced by the stock-analyst agent.

## Prerequisites
Before building the portfolio page, at least one ticker must have been fully analyzed:
- `scripts/output/[TICKER]_short_term.json` exists
- `scripts/output/[TICKER]_ccrlo.json` exists
- `scripts/output/[TICKER]_simulation.json` exists
- `scripts/output/[TICKER]_tags.json` exists
- `scripts/data/[TICKER]_bundle.json` exists
- `reports/[TICKER]-analysis.html` exists

If no tickers have been analyzed, instruct the user to run `@stock-analyst analyze [TICKER]` first.

## Workflow

### Phase 1: Data Inventory
1. Read `scripts/output/tags_index.json` to discover all analyzed tickers
2. For each ticker, verify all required files exist:
   ```
   scripts/output/[TICKER]_short_term.json
   scripts/output/[TICKER]_ccrlo.json
   scripts/output/[TICKER]_simulation.json
   scripts/output/[TICKER]_tags.json
   scripts/data/[TICKER]_bundle.json
   reports/[TICKER]-analysis.html
   ```
3. Read `templates/portfolio-template.html` for CSS reference
4. Log any tickers with missing data (include with warnings in portfolio)

### Phase 2: Aggregate Data
Run the aggregation and optimization:
```bash
python scripts/build_portfolio.py --risk-band growth
```

This invokes:
- **Data aggregation**: Reads all signal JSONs, tags, bundles
- **Portfolio optimizer** (`portfolio_optimizer.py`): Evidence-based weight construction
  - Risk-band-aware method selection (inverse-vol / risk-parity / signal-weighted)
  - Fragility penalty (reduce allocation to fragile assets)
  - Regime-aware de-risking (cut stressed/crash-prone positions)
  - Constraint enforcement (max weight, sector limits)
  - Stress testing (5 scenarios: market correction, vol spike, sector rotation, credit stress, tail event)
  - Rebalancing signal detection (drift, CCRLO breach, regime shift, trend-break)
  - Strategy recommendation (maps to research framework by risk band)
- Outputs: `portfolio_summary.json` + `portfolio_optimization.json`

Risk bands (from portfolio research §6):
- `conservative`: Inverse-volatility weights, max 25% single, ES limit 8%
- `moderate`: Risk-parity weights, max 30% single, ES limit 12%
- `growth`: Signal-weighted, max 35% single, ES limit 18%
- `aggressive`: Signal-weighted, max 40% single, ES limit 25%

### Phase 3: Generate HTML (Iterative Section-by-Section Build)

The build script (`build_portfolio.py`) generates HTML **iteratively** — one batch of sections
at a time, with a **mini-audit** after each batch. If any mini-audit check fails, the batch
is flagged but building continues to produce a complete page for diagnosis.

| Batch | Sections | Mini-Audit Checks |
|-------|----------|-------------------|
| B1 | Header + Summary Cards | Title, date, tickers count, fragility, CCRLO, regime (7 checks) |
| B2 | Holdings Table | Heading, all tickers present, sortable, links, prices, no empty rows (6 checks) |
| B3 | Sector Allocation + Risk Distribution | Headings, bar segments, legend, tiles, no placeholders (5 checks) |
| B4 | Risk Heatmap + Signal Dashboard | Headings, heatmap cells, all tickers, signal cards, no placeholders (6 checks) |
| B5 | Portfolio Risk + Regime Distribution | Headings, score tiles, narrative, regime table, no placeholders (6 checks) |
| B6 | Portfolio Construction + Optimized Risk | Headings, method, weight table, risk tiles, no placeholders (5 checks) |
| B7 | Stress Tests + Rebalancing + Strategy | Headings, tables rendered, sections populated (6 checks) |

**Total: 41 mini-audit checks across 7 batches** plus a final unreplaced-placeholder sweep.

### Phase 4: Full Post-Build Audit (8 Layers, ~100+ checks)

After HTML is saved, `build_portfolio.py` automatically calls `audit_portfolio.py`'s
`run_full_audit()` function to validate the complete page:
- L1: Structure (19 checks) — all 17 sections + card/heading counts
- L2: Data accuracy — per-ticker signal value verification
- L3: Link integrity — report file existence + disabled link consistency
- L4: Aggregate metrics — totals, averages, optimizer data, weight sum
- L5: Styling — CSS Grid ban, print CSS, color palette, fonts
- L6: Layout — container width, flexbox use, card borders, alignment
- L7: Text quality — no placeholders, no NaN/None/undefined, valid HTML
- L8: Numerical accuracy — prices, change%, weights, stress impacts, beta, drawdown

## Portfolio HTML Section Order

1. **Export Bar** — PDF export button (hidden in print)
2. **Portfolio Header** — "Portfolio Dashboard", date, total holdings count, aggregate risk badge
3. **Portfolio Summary Cards** — 5 metric cards: Total Tickers, Avg Fragility, Avg CCRLO, Dominant Regime, Top Risk Event
4. **Holdings Table** — Full-width card, one row per ticker, sortable columns:
   - Ticker (hyperlink to report) | Price | Change% | Sector | Market Cap | Risk Level | Fragility | CCRLO | Regime | Short-Term Signal | Primary Tag
5. **Sector Allocation + Risk Distribution** — Side-by-side cards with bar chart and risk tiles
6. **Risk Heatmap** — Tickers × Risk Dimensions matrix (leverage, liquidity, info_risk, valuation, momentum)
7. **Signal Dashboard** — Grid of signal tiles per ticker (short-term + long-term at a glance)
8. **Portfolio Risk Metrics** — Aggregate cards + risk assessment narrative
9. **Market Regime Distribution** — Per-ticker regime breakdown table
10. **Portfolio Construction** — Optimized weights table (optimized vs equal), method + objective
11. **Optimized Risk Metrics** — Portfolio Beta, Vol Proxy, Drawdown Risk, ES, Concentration, Effective-N
12. **Stress Test Results** — 5 scenario table with portfolio + per-ticker impacts
13. **Rebalancing Signals** — Drift detection, CCRLO breach, regime shift, trend-break flags
14. **Strategy Recommendation** — Framework, assessment, overlays, hard controls, action items, warnings
15. **Disclaimer** — Standard financial disclaimer
16. **Timestamp** — Generation timestamp

## Portfolio Config (Optional)
If user wants a selective portfolio (not all analyzed tickers), create `portfolio-manager/portfolio_config.json`:
```json
{
  "name": "My Growth Portfolio",
  "tickers": ["AMZN", "MSFT", "HOOD"],
  "weights": { "AMZN": 0.40, "MSFT": 0.35, "HOOD": 0.25 },
  "risk_band": "growth",
  "benchmark": "SPY"
}
```
If no config exists, include ALL tickers from `tags_index.json` with equal weights.

## Critical Rules
1. **Never fabricate data** — all values come from source JSONs
2. **Never recompute signals** — use Python-computed results only
3. **Every ticker must link to its report** — use relative path `../reports/[TICKER]-analysis.html`
4. **Use flexbox only** — no CSS Grid
5. **PDF-exportable** — all print CSS rules from report-template.html apply
6. **Iterative building** — build in batches, mini-audit after each
7. **Overwrite existing** — `portfolio-manager/portfolio.html` is always overwritten on rebuild
