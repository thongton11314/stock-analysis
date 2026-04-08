---
name: report-generation
description: >
  Generate a complete stock analysis HTML report for any ticker symbol.
  USE FOR: "analyze [TICKER]", "generate report for [TICKER]", "create stock analysis",
  "build report", stock market analysis, financial report generation.
  DO NOT USE FOR: fixing existing reports (use report-fix skill), general questions
  about stocks, or non-report tasks.
---

# Stock Report Generation Skill

## Overview
Generate a comprehensive stock analysis HTML report using Alpha Vantage MCP data. The report is a standalone HTML file with 20 sections (including an Income Statement Breakdown flow chart), PDF-exportable, and follows strict styling rules.

## Always Fetch Fresh Data (NON-NEGOTIABLE)
Every analysis request — first-time or re-analysis — **MUST fetch fresh data from Alpha Vantage MCP**.
Never reuse, skip, or rely on existing data bundles from previous runs.
- **Always fetch**: All 15 subject data points + peers + macro are collected fresh every time
- **Never reuse old bundles**: Even if `scripts/data/[TICKER]_bundle.json` exists, fetch everything fresh
- **Never skip data collection**: Existence of prior reports, bundles, or signal outputs does NOT justify skipping
- **Overwrite all artifacts** without confirmation:
  - `reports/[TICKER]-analysis.html` — new report replaces old
  - `scripts/data/[TICKER]_bundle.json` — fresh MCP data replaces old bundle
  - `scripts/output/[TICKER]_*.json` — fresh signals replace old outputs
  - `scripts/data/[TICKER]_input_validation.json` — fresh validation replaces old

## Multi-Ticker Handling (CRITICAL)
When the user requests reports for multiple tickers (e.g., "analyze AMZN, NVDA, MSFT"):
- **Sequential, not parallel**: Complete the entire workflow (Phase 1–5) for one ticker before starting the next
- **Shared context**: Load templates/CSS/instructions once for the first ticker, reuse for all
- **Macro data reuse**: CPI, FEDERAL_FUNDS_RATE, UNEMPLOYMENT, REAL_GDP are fetched once and reused — they are market-wide, not ticker-specific
- **Macro data depth**: `FEDERAL_FUNDS_RATE` must return ≥12 monthly data points for the Fed chart. Never store only 1 data point — this causes fabricated chart data
- **Macro data integrity**: Never interpolate or estimate Fed Funds Rate history. Only use actual API-returned values for chart bars
- **Independent peer data**: Each ticker requires its own peer selection and peer data fetch
- **Failure isolation**: If a ticker fails, log the error and proceed to the next ticker
- **Progress reporting**: After each ticker completes Phase 5, report: "✅ [TICKER] complete (N/total)"
- **Final summary**: After all tickers, output a batch summary showing each ticker's status and file path

## Workflow (Follow This Order)

### Phase 1: Data Collection

Follow the **data-collection skill** workflow (`.github/skills/data-collection/SKILL.md`).
Also load `.instructions/data-collection.md` for MCP tool reference.

This phase collects the complete **Data Bundle**:
1. **Subject ticker** — All 15 data points (GLOBAL_QUOTE through INSTITUTIONAL_HOLDINGS)
2. **Peer data** — COMPANY_OVERVIEW + GLOBAL_QUOTE for 3-5 industry competitors
3. **Macro data** — CPI, FEDERAL_FUNDS_RATE (≥12 monthly values), UNEMPLOYMENT, REAL_GDP
4. **Company Profile** — Classify as Mature Large-Cap / Established Growth / Hypergrowth Post-IPO / Small-Cap Post-IPO / Fintech-Digital

See data-collection skill for exact tool call order, peer selection criteria, and rate limit handling.

Read `examples/HOOD-analysis.html` as the primary gold standard structure reference.

### Phase 2: Compute Signals via Analyst Compute Engine (MANDATORY)

All signal computations MUST use the unified Python compute engine.
See **analyst-compute-engine skill** (`.github/skills/analyst-compute-engine/SKILL.md`).

1. Write the collected Data Bundle to `scripts/data/[TICKER]_bundle.json` following the schema
   in the analyst-compute-engine skill.

2. Run **numerical audit (Stage A)** to verify data bundle numbers:
   ```bash
   python scripts/validate_numbers.py --ticker [TICKER] --stage A
   ```
   This verifies price math, financial statement consistency, data freshness, and indicator
   sanity. Fix any FAIL items before proceeding.

3. Run the unified engine:
```bash
python scripts/analyst_compute_engine.py --ticker [TICKER]
```

This single command:
- **Phase 2a**: Validates inputs (completeness, ranges, freshness) — FAIL aborts with exit code 1
- **Phase 2b**: Computes SHORT_TERM → CCRLO → SIMULATION (in dependency order)
- **Phase 2c**: Validates outputs (contracts, bounds, cross-signal consistency) — FAIL aborts with exit code 3

4. Check exit code:
   - **0**: All phases passed → proceed to numerical audit (Stage B)
   - **1**: Input validation failed → re-fetch missing data, update bundle, re-run (max 2 retries)
   - **2**: Computation error → check `scripts/output/[TICKER]_engine_report.json` for error details
   - **3**: Output validation failed → review `blocking_failures` in engine report

5. Run **numerical audit (Stage B)** to verify calculation accuracy:
   ```bash
   python scripts/validate_numbers.py --ticker [TICKER] --stage B
   ```
   This verifies TB/VS/VF gate computations, fragility score math, CCRLO composite sums,
   regime probability sums, scenario weight sums, and cross-signal price/date/ticker consistency.
   Fix any FAIL items before proceeding to HTML generation.

6. Read validated signal JSONs from `scripts/output/[TICKER]_*.json`

### Phase 2d: Pre-Generation Signal Review (MANDATORY GATE)

Before generating HTML, the agent MUST review the computed signals against methodology rules.
This catches methodology violations that structural validation cannot detect.

**Review checklist** (read each signal JSON and verify):

| # | Check | Rule | Source |
|---|---|---|---|
| R1 | **Average Year 1** target | Must be anchored to analyst 12-month mean (`AnalystTargetPrice`) ± modest premium | `.instructions/analysis-methodology.md` |
| R2 | **Fragility dimensions** | Verify each dimension used the right data field (trailing P/E → forward P/E fallback if null) | Engine computed — read `_short_term.json` |
| R3 | **Correction probs include tail-risk** | Check `_tail_risk_applied` field exists in `_short_term.json` | Engine post-adjustment |
| R4 | **Correction probs include IPO adj** | If IPO < 2yr, Severe and Black Swan should be elevated vs base | Engine computed |
| R5 | **CCRLO risk ↔ crash regime alignment** | If CCRLO ≥ 12, `crash_prone` regime prob should be > 0.15 | Cross-signal contract |
| R6 | **Regime probs sum** | Must = 1.0 (±0.01) | Signal contract |
| R7 | **Scenario weights sum** | Must = 1.0 (±0.01) | Signal contract |
| R8 | **Event prob bounds** | All in [1%, 85%], crash ≤ 35% | Signal contract |
| R9 | **Engine exit code** | Must be 0 | Engine report |
| R10 | **Signal-to-section plan** | Write a brief mapping: which signal values go into which sections | Report layout spec |

**On failure**: Do NOT proceed to HTML generation. Fix the data bundle or re-run the engine.

**Output**: Brief review summary before starting Phase 3:
```
PRE-GEN REVIEW: [TICKER]
  R1 Avg Year 1: $130 (analyst mean $127.31 + 2.1% premium) ✅
  R2 Fragility: 1/5 — valuation HIGH (fwd P/E 122x > 55x) ✅
  R3 Tail-risk: 0.142 applied ✅
  R4 IPO adj: IPO Apr 2025 (<2yr) → Severe/BS elevated ✅
  R5-R8 Contracts: All pass ✅
  R9 Engine: Exit 0 ✅
  → PROCEED TO HTML GENERATION
```

### Phase 2 — Key Rules
- **Never compute signals inline** — always use the analyst compute engine
- **Never skip validation** — the engine validates both inputs and outputs automatically
- **Never recompute** signal values in Phase 3 — read and use the Python-computed JSONs directly

### Phase 3: Generate HTML (Iterative Section-by-Section Build)

Build the report incrementally in **8 batches** using file tools. After each batch, run
an inline mini-audit to catch number/style errors early — before they compound.

**Why iterative?** A 20-section report is ~100KB+ HTML. Building in one shot risks
truncation, crashes, and unfixable compounding errors. Iterative builds let the agent
verify each chunk before moving on.

#### CRITICAL: Never Copy-and-Replace from Gold Standard (NON-NEGOTIABLE)

**DO NOT** copy `examples/HOOD-analysis.html` (or any existing report) and find-replace
values. This approach leaves stale data in sections the agent forgot to update. Known
failure modes from copy-paste:

- VF badge shows ✓ in S11 but computed signal is False (stale from source)
- MACD tile shows old value (-3.45) instead of fresh value (-3.55)
- Regime percentages differ between S3 (29/29/19/24) and S11 (40/24/16/20)
- Fed chart rates are from a different ticker's data (5.33% instead of 4.33%)
- Correction probability bar widths don't match computed signal values
- S4/S5 December targets mismatch because one section was updated and the other wasn't

**Instead**: Generate each section's HTML fresh from the data bundle and signal JSONs.
The gold standard is a **structure reference** (layout, CSS classes, element nesting),
not a **content template** to copy values from. Every number in the report must trace
back to either `scripts/data/[TICKER]_bundle.json` or `scripts/output/[TICKER]_*.json`.

**Mini-audit enforcement**: After each batch, the agent MUST read back the HTML just written
and verify at least 3 key numbers against the signal JSONs. If any number doesn't match,
fix it before proceeding. This catches copy-paste artifacts immediately.

#### Batch Plan (8 batches)

| Batch | Sections | Tool | Mini-Audit Focus |
|-------|----------|------|------------------|
| **B1** | S1 (Export) + S2 (Header) + S3 (Executive Summary) | `create_file` — creates the full HTML skeleton with `<head>`, CSS, and first 3 sections. Leave a `<!-- SECTIONS_CONTINUE -->` marker before `</div></body></html>` | **Numbers**: Price in S2 matches `global_quote.price`. Signal values in S3 match `_short_term.json` and `_ccrlo.json`. **Style**: `.meta-row` has 10 items, flexbox only, signal badges ≤5 words |
| **B2** | S4 (Price Targets) + S5 (Corridors) + S6 (Scenarios) | `replace_string_in_file` — replace `<!-- SECTIONS_CONTINUE -->` with S4+S5+S6 HTML + new `<!-- SECTIONS_CONTINUE -->` | **Numbers**: S4 target prices internally consistent (Conservative < Average < Bullish). S5 correction probs match `_short_term.json`. S6 Target Price row = S4 year-end targets. **Style**: 3 separate cards, pill badges for S&R, SVG viewBox 600×200, correction table has 5 columns |
| **B3** | S7 (Benchmark) + S8a/S8b (Analyst + EPS) | Same append pattern | **Numbers**: Period returns are directionally plausible. Analyst target = `company_overview.analyst_target_price`. **Style**: S7 has narrative box, S8a uses visual rating bar (not table), rating labels = count + abbreviation |
| **B4** | S9a/S9b (Valuation + Health) + S10 (Income Statement) | Same append pattern | **Numbers**: P/E, P/S, EV/Revenue computed correctly from bundle. Revenue/COGS/GP/OpInc/NetInc from `income_statement`. Gross margin = GP/Revenue. **Style**: 2-column tables, `rev-chart` bars (not journey pills), S10 must have: margin callout above SVG, 4 stage labels (REVENUE/COST SPLIT/OPERATIONS/DETAIL), R&D+SGA detail nodes, gradient flow bands, legend, narrative box |
| **B5** | S11 (Technical) + S12 (Event Risk Simulation) | Same append pattern | **Numbers**: RSI, MACD, ADX, ATR match bundle. TB/VS/VF and fragility match `_short_term.json`. Regime probs sum to 1.0. Event probs in [1%,85%]. Scenario weights sum to 1.0. **Style**: 3-row layout, RSI gauge with zone markers, narrative box, `.sim-grid` with 2 panels |
| **B6** | S13a/S13b (News + Risks) + S14 (Ownership) | Same append pattern | **Numbers**: News dates are recent. Insider transaction shares × price = Avg Value. **Style**: All news hyperlinked, S14 narrative box present |
| **B7** | S15 (Macro) + S16a/S16b (Global + Correlation) | Same append pattern | **Numbers**: FFR chart has exactly 12 bars with actual API values. GDP/CPI/Unemp/FFR match bundle. Macro values match cross-report standard. **Style**: Fixed-pixel bar heights (not %), bar columns use `flex:1` for equal spacing (never `min-width:40px`), S15 narrative box present |
| **B8** | S17 (Competitive) + S18 (Scorecard) + S19 (Disclaimer) + S20 (Timestamp) + close HTML | Replace `<!-- SECTIONS_CONTINUE -->` with final sections. Also append `<script>exportToPDF()</script></div></body></html>` | **Numbers**: S17 table has 10 columns, subject row data matches bundle. S18 CCRLO tile matches `_ccrlo.json`. **Style**: S17 Key Takeaway box, S18 Net Assessment box, export function saves+restores title |

#### Iterative Build Protocol

For each batch **B1–B8**:

1. **Generate** the HTML for that batch's sections following all rules below (section order, styling, format requirements)
2. **Write** to the report file:
   - B1: Use `create_file` to create `reports/[TICKER]-analysis.html` with full HTML head, CSS from `templates/report-template.html`, and sections S1–S3, followed by `<!-- SECTIONS_CONTINUE -->` and closing `</div></body></html>`
   - B2–B7: Use `replace_string_in_file` to replace `<!-- SECTIONS_CONTINUE -->` with the new sections + a fresh `<!-- SECTIONS_CONTINUE -->` marker
   - B8: Replace `<!-- SECTIONS_CONTINUE -->` with final sections + export script + closing tags (no marker left)
3. **Mini-audit** — immediately verify the just-written batch:
   - **Number check**: Read back the written HTML and verify key values against the data bundle and signal JSONs (see Mini-Audit Focus column above)
   - **Style check**: Verify flexbox-only (no `display: grid`), no HTML bullet entities (`&#9656;`), signal badges ≤5 words, correct card structure
   - **Fix before continuing**: If any number is wrong or styling violates rules, fix it with `replace_string_in_file` before proceeding to the next batch
4. **Report batch status** (brief, one line):
   ```
   B1 ✅ S1-S3 written (Header $211.71, TB=INACTIVE, CCRLO 9/21)
   ```

#### Error Recovery for Batch Failures

If `replace_string_in_file` fails at any batch B2–B8:

1. **Marker not found**: Read the report file and search for `<!-- SECTIONS_CONTINUE -->`.
   - If missing: the previous batch omitted it. Read the file, find where sections end,
     and use `replace_string_in_file` to insert the missing marker before `</div></body></html>`
   - If multiple markers: target the last occurrence by including surrounding HTML context
     (e.g., the closing tag of the previous section) in the `oldString`
2. **Content too large**: If a single batch's HTML exceeds tool limits, split it into two
   sub-batches (e.g., B5a for S11 and B5b for S12) using intermediate markers
3. **Fallback — full rewrite**: If >2 replacements fail in the same session, read the
   current file, append the remaining sections as a string, and write the complete HTML
   with `create_file` (overwriting)
4. **Verify after recovery**: After any error recovery, read the file and confirm the
   `<!-- SECTIONS_CONTINUE -->` marker exists exactly once (or zero for B8)

#### Section Content Rules

Within each batch, follow these rules for generating section HTML:

1. **Copy CSS** from `templates/report-template.html` (the `<style>` block) — included in B1 only
2. **Follow 20-section order** from `.instructions/report-layout.md` — NO reordering
   - **Section `<h2>` titles MUST match canonical names exactly** (see `copilot-instructions.md` → "Canonical Section `<h2>` Titles")
3. **Apply styling rules** from `.instructions/styling.md`
4. **Calculate analysis** using `.instructions/analysis-methodology.md`:
   - Price targets (3 scenarios with EPS CAGR + P/E multiples)
   - SVG price corridor chart (enhanced interactive: gradient fills, animated lines, hover data points, end badges)
   - **Monthly Price Forecast** (see `.instructions/analysis-methodology.md` for computation):
     - Interpolate monthly prices from current to Section 4 year-end targets
     - Past months: compare actual vs model estimate, compute accuracy badges
     - Current month: highlighted row with live price
     - Future months: 3-scenario projections adjusted by TB/VS/VF, Fragility, and CCRLO
     - December row MUST exactly match Section 4 year-end targets
   - Correction probabilities (adjusted for Beta, post-IPO status, **AND fragility score from Phase 2b**)
   - **Benchmark Section (Section 7)**: Dual SVG charts side by side (Y-axis = cumulative % return, NOT normalized index):
     - **12-Month chart**: TICKER vs S&P 500 cumulative % return, monthly x-axis with 3-letter abbreviations (13 data points, e.g., Mar'25, Apr, May, ..., Jan'26, Feb, Mar). Y-axis labels: +X%, 0%, -X%
     - **5-Year chart**: TICKER vs S&P 500 cumulative % return, yearly x-axis. If ticker has <5 years of data, start from earliest available date and note in subtitle
   - **Income Statement Breakdown Diagram** (enhanced interactive: gradient flows, stage headers, legend, margin callouts — extract from INCOME_STATEMENT — see `.instructions/styling.md` for SVG implementation)
   - Macro sensitivity scoring (HIGH/MEDIUM/LOW rubric)
   - Competitive positioning map (6 dimensions with signal badges)
   - **Analyst Consensus (Section 8a)**: Use **visual graph layout** (NOT table-based). Structure:
     - Centered hero block: large green target price (`font-size:1.4em; color:#16a34a`), subtitle, analyst count + latest quarter
     - Visual `.rating-bar` with proportional colored segments. **Every segment must show count + abbreviation** (e.g., "15 SB", "48 Buy", "3 Hold", "2 Sell"). Never show just a number. Omit sell segment if 0 analysts
     - Centered percentage breakdown text line below the bar
     - Green consensus box (`background:#f0fdf4; border:1px solid #bbf7d0`) with consensus label badge + summary narrative
     - Consensus badge: >80% Buy+SB → STRONG BUY, >60% → BUY, >50% → HOLD, <50% → SELL
5. **Integrate short-term signals** into report sections:
   - **Executive Summary (Section 3)**: Add trend-break status (TB/VS/VF) and fragility score to Short-Term Outlook. If ENTRY signal is active, lead with a prominent signal badge. Use `.signal-desc` for longer explanations.
   - **Technical Indicators (Section 11)**: Use STRICT 3-row layout from report-template.html. Row 1: RSI/MACD/ADX/ATR tiles. Row 2: Moving Averages + Bollinger. Row 3: Trend-Break Status tile + Fragility Score tile + Market Regime tile + Event Risk (20d) tile.
   - **RSI Gauge (Section 11)**: Must include Oversold/Overbought labels + zone markers at 30/50/70.
   - **Price Corridors (Section 5)**: If fragility score ≥ 3, increase correction dip markers and adjust probability bars upward per the calibration table.
   - **Risks & Catalysts (Section 13)**: Flag any fragility dimension scoring HIGH as a named risk factor.
6. **Integrate CCRLO long-term signals** into report sections:
   - **Executive Summary (Section 3)**: Add CCRLO score (X/21), 6-month correction probability, and risk level badge to Long-Term Outlook.
   - **Price Corridors (Section 5)**: Calibrate corridor width by CCRLO risk: LOW = tight (±20%), HIGH = wide (±40%).
   - **Macro Dashboard (Section 15)**: Show CCRLO feature scores alongside macro indicator values.
   - **Net Macro Scorecard (Section 18)**: Add CCRLO as a composite risk tile (TAILWIND if LOW, HEADWIND if HIGH/VERY HIGH).

### Phase 3b: Section Format Requirements (CRITICAL — prevents audit failures)

These format rules are enforced by the audit skill. Violating them causes FAIL in post-generation audit.

| Section | Format Requirement |
|---|---|
| **S2 Header** | `.meta-row` must have 10 items: Open, High, Low, Close, Volume, Market Cap, P/E, Beta, 52-Wk, Date |
| **S5 Correction Risk** | Table columns: Scenario \| Drawdown \| Price Floor \| **12-Month Probability** \| **Trigger**. Probability uses nested `<div>` bar + `<span>` percentage. Never use "Recovery Time" or plain text probabilities |
| **S5 Support & Resistance** | Use colored **pill badges** (NOT text lists). Support = green `<span>` badges (`background:#d4edda; color:#155724`). Resistance = red/pink `<span>` badges (`background:#f8d7da; color:#721c24`). Format: `$PRICE (Label)` inside each badge. Never use plain text lists with colored SUPPORT/RESISTANCE headers |
| **S6 Revenue Table** | Must have FY Actual column: `Metric \| FY[YEAR] (Actual) \| FY[YEAR]E Conservative \| FY[YEAR]E Average \| FY[YEAR]E Bullish`. Must include rows: Revenue, EPS, Implied P/E, Target Price. Target Price row must match S4 year-end targets |
| **S8a Rating Bar** | Every segment label = count + abbreviation: "15 SB", "48 Buy", "3 Hold", "2 Sell". Never show just a number |
| **S9a Valuation** | 2-column table (Label \| Value) per template. Do NOT add a 3rd column with signal badges. Must include **Revenue Growth Journey (Revenue)** or **Profitability Journey (EPS)** using `rev-chart` column bar visualization (flex container with `rev-bar-wrap` > `rev-bar-val` > `rev-bar` > `rev-bar-label`). Chart title must include metric in parentheses. Never use `journey` pill-style layout. Final bar = green gradient. Min 3 years |
| **S9b Financial Health** | 2-column table (Label \| Value) per template. Revenue row shows growth %, profit rows show margin %. Must include **Profitability Journey (Net Income)** using `rev-chart` column bar visualization. Negative years = red gradient bars. Final positive bar = green gradient. Min 3 years. Never use `journey` pills |
| **S7 Period Returns** | Use `<span class="signal ...">` badges on return values (bullish=positive, bearish=negative). Statistical Analysis: 2-column tbody (no thead), rows: Beta/Correlation/Alpha/Sharpe/Max Drawdown |
| **S17 Columns** | 10 columns: Company \| Price \| Mkt Cap \| Revenue \| Rev Growth \| **Gross Margin** (not "Margin") \| P/E \| P/S \| EV/Rev \| Analyst |
| **S15 Macro Format** | GDP = dollar value ("$6,125.9B"), CPI = index value ("326.79"), Unemployment = percentage ("4.4%"), FFR = percentage ("3.64%"). Must match HOOD gold standard values exactly (macro is market-wide) |
| **S20 Export** | `exportToPDF()` must save AND restore `document.title`: `const origTitle = document.title; ... window.print(); document.title = origTitle;` |
7. **Integrate event risk simulation** into report sections:
   - **Executive Summary (Section 3)**: Add dominant market regime badge (Calm=green, Trending=amber, Stressed/Crash=red) + top event probability (e.g., "Vol Spike 20d: 30%") to Short-Term Outlook. Use `.signal-desc` for narrative.
   - **Price Corridors (Section 5)**: Use tail_risk scenario weight to increase correction probabilities: Mild × (1 + tail_weight), Standard × (1 + 2×tail_weight), Severe × (1 + 3×tail_weight).
   - **Technical Indicators (Section 11)**: In Row 3, add "Market Regime" tile showing dominant regime + probability breakdown with `.regime-bar`, and "Event Risk (20d)" tile showing top 3 event probabilities with signal badges.
   - **Event Risk Visualization (Section 12)**: Generate a full-width card after Section 11 with:
     - Left panel: Regime probability bars (4 rows with `.regime-row` colored fills) + **Scenario Price Targets table** (Scenario | Weight | Price Range | Expected P/L using ATR×√horizon formulas) + Weighted Expected Price callout with 80% CI + Downside Skew
     - Right panel: Event probability heatmap (6 events × 3 horizons with `.heatmap-low/med/high/extreme` cells) + **Price Impact column** showing dollar range per event + Confidence tiles
     - Use `.sim-grid` layout with `.sim-panel` children. Include price methodology note at bottom.
   - **Risks & Catalysts (Section 13)**: If vol_expansion weight > 0.25, add "Volatility regime shift" risk. If tail_risk weight > 0.15, add "Tail risk dislocation" risk. If liquidity_stress_20d > 0.15, add "Liquidity deterioration" risk.
   - **Net Macro Scorecard (Section 18)**: Add "Event Risk" tile showing composite event risk (average of top-3 20d events): GREEN <15%, AMBER 15-30%, RED >30%.

### Phase 4: Full-Report Audit (after all batches complete)

After all 8 batches are written and mini-audited, run the full validation suite:

1. **Numerical audit (Stage C)** — Python cross-checks report numbers against source data:
   ```bash
   python scripts/validate_numbers.py --ticker [TICKER] --stage C
   ```
   This verifies header price, signal scores, financial figures, and macro values
   against the data bundle and signal JSONs. Fix any FAIL items before proceeding.
2. **Structural verification**:
   - 20 sections present, 3 separate Price Target cards
   - No CSS Grid, no absolute positioning
   - All news items hyperlinked
   - Regime probabilities sum to 1.0, event probabilities in [1%, 85%]
   - All `<h2>` section titles match canonical names from copilot-instructions.md exactly
   - Fed Funds Rate chart has exactly 12 bars with actual API values (not interpolated)
   - Macro values match gold standard (market-wide data must be identical across reports)
   - `<!-- SECTIONS_CONTINUE -->` marker is NOT present (was consumed in B8)
3. **No leftover markers**: Verify the final HTML has no `<!-- SECTIONS_CONTINUE -->` placeholder remaining

### Phase 5: Post-Generation 7-Layer Audit (Full Report)

After Phase 4 passes, run the full 7-layer audit inline. This is the final quality gate
before declaring the report ready. Mini-audits (per batch) catch incremental errors;
this audit catches cross-section consistency issues that only emerge in the complete report.

**Layer 1 — Price Consistency** (MUST PASS):
- 1b: Section 4 year-end targets = Section 5 Monthly Forecast December row (all 3 scenarios)
- 1d: Analyst target in Section 8 = Section 3

**Layer 2 — Signal Consistency** (MUST PASS):
- 2a: TB/VS/VF in Section 3 = Section 11
- 2b: Fragility Score in Section 3 = Section 11
- 2c: CCRLO Score in Section 3 = Section 18
- 2f: Market Regime in Section 3 = Section 11

**Layer 3 — Financial Sanity**:
- 3a: Gross Profit ≈ Revenue - COGS (within rounding)
- 3d: Income Statement Breakdown revenue node = sum of downstream flows
- 4b6: Income Statement Breakdown DETAIL column nodes have ≥12px vertical gap between labels (no overlapping text)

**Layer 4 — Prediction Integrity**:
- 4h: Regime probabilities sum to 100%
- 4i: All event probabilities in [1%, 85%], crash ≤ 35%
- 4j: Scenario weights sum to 100%
- 4e: Conservative < Average < Bullish for all projections

**Layer 5 — Structure**:
- 5a: All 20 sections present
- 5-name: All `<h2>` titles match canonical names
- 5b: Price Target = 3 separate cards
- 5c: Section 10 (Income Statement Breakdown) has `<svg class="sankey-svg">` with flow paths and gradient defs
- 5d2: Section 7 has TWO SVG charts: "12-Month Cumulative Return (Monthly)" + "5-Year Cumulative Return (Annual)". Y-axis shows cumulative % return (e.g., +200%, +50%, 0%, -25%) NOT normalized index values. The 0% baseline line uses heavier stroke (`stroke-width: 1`).
- 5l: Section 12 `.sim-grid` with 2 panels. Left: Regime Detection (4 rows + 4 explanation boxes) + Scenario Price Targets (4 rows + Weighted Expected). Right: Event Heatmap (6×3 all populated) + 4 stat tiles (Disagreement/Confidence/Composite/Skew)
- 5m: Section 11 has 3-row layout: RSI/MACD/ADX/ATR tiles → Moving Averages (with thead) + Bollinger visual (gradient bar, not table) → TB/Fragility/Regime/Event Risk tiles
- 5n: Section 14 has Leadership table + Recent Insider Transactions table (with Avg Value column) + **Ownership narrative box**
- 5o: Section 15 has macro table (4+ rows) + Fed Funds Rate bar chart: exactly 12 monthly bars, fixed-pixel heights, chronological order (oldest left, newest right), rate labels with `%` suffix, no prediction column + **Macro narrative box**
- 5o2: Section 10 (Income Statement Breakdown) has **narrative analysis box** below Sankey legend with title "Income Statement Analysis" (3-5 sentences). Missing = FAIL
- 5o3: Section 11 (Technical Indicators) has **narrative analysis box** below Row 3 with title "Technical Analysis Summary" (3-5 sentences). Missing = FAIL
- 5p: Section 2 Header has `.meta-row` with 10 meta items
- 5q: Section 5 Correction Risk table has 5 columns: Scenario/Drawdown/Price Floor/12-Month Probability/Trigger
- 5r: Section 6 Revenue table has FY Actual column + Revenue/EPS/P-E/Target Price rows
- 5s: Section 8a rating bar labels show count + abbreviation (not just numbers)
- 5t: Section 8b has eps-chart + earnings surprise table + streak text
- 5u: Section 9a uses 2-column format + includes Revenue Growth Journey or EPS Journey using `rev-chart` column bars (not `journey` pills)
- 5v: Section 9b uses 2-column format + includes Profitability Journey (Net Income) using `rev-chart` column bars (not `journey` pills)
- 5z: Section 17 table has 10 columns including "Gross Margin" (not "Margin")

**Layer 7 — Macro Data Consistency** (MUST PASS):
- 7f: Fed chart has exactly 12 bars with actual API values (not interpolated). Bars should show realistic rate trajectory with rate changes at FOMC meeting dates
- 7g: If other reports exist in `reports/`, cross-check macro values (CPI, FFR, Unemployment, GDP) match. Mismatches indicate stale or fabricated data
- 7h: Fed Funds Rate in Macro Dashboard table row matches most recent bar in Fed chart
- 7j: GDP uses dollar value format ($X,XXX.XB), CPI uses index value, Unemployment uses percentage — must match HOOD gold standard format exactly
- 7k: Only the `{{TICKER}} Impact` column text should differ between reports; all other macro columns must be word-for-word identical

**Layer 5b — Section Format** (MUST PASS):
- S5 Correction Risk: 5 columns (Scenario/Drawdown/Floor/12-Month Probability/Trigger), bar visual for probability
- S5 Support & Resistance: pill badge style — green badges for support (`background:#d4edda`), red/pink badges for resistance (`background:#f8d7da`). Format: `$PRICE (Label)`. Never use plain text lists with colored headers
- S6: Has FY Actual column, Target Price row matches S4
- S8a: Rating bar labels have count + abbreviation
- S9a/S9b: 2-column tables per template
- S17: 10 columns with "Gross Margin" (not "Margin")
- S20: Export function saves AND restores document.title

**Layer 6 — Styling Quick Check**:
- 6a: No HTML `&#9656;` entities for bullets
- 6b: No `display: grid` in inline styles

**On failure**: Fix issues immediately before reporting completion to the user.
Output a brief audit summary:
```
POST-GEN AUDIT: [TICKER]
  L1 Price:      ✅ PASS
  L2 Signals:    ✅ PASS
  L3 Financials: ✅ PASS
  L4 Predictions: ✅ PASS
  L5 Structure:  ✅ PASS
  L6 Styling:    ✅ PASS
  L7 Macro:      ✅ PASS (12 FFR bars, values match gold standard)
  → READY TO PUBLISH
```

## Critical Rules (Never Violate)
1. **Section order**: Follow the 20-section order exactly; all `<h2>` titles must match canonical names
2. **Card splitting**: Price Target = 3 separate cards; no card >60% A4 landscape height
3. **Flexbox only**: Never CSS Grid, never absolute positioning for S&R levels
4. **Bullet points**: CSS `\25B8` via `::before` — never HTML entities `&#9656;`
5. **News hyperlinks**: Every news item MUST have `<a>` tag to original article
6. **Disclaimer + timestamp**: Always include at bottom
7. **Subject row highlight**: `background:#eff6ff;` in competitive landscape table
8. **Key Takeaway box**: `background:#fffbeb; border:1px solid #fde68a;` in competitive section
9. **Short-term signals**: Always compute TB/VS/VF and fragility score; integrate into Executive Summary, Technical Indicators, and Price Corridors sections
10. **CCRLO signals**: Always compute CCRLO score; integrate into Executive Summary, Price Corridors, and Macro Scorecard
11. **Monthly Price Forecast**: Always include in Section 5 with past accuracy + future projections; December MUST match Section 4 targets
12. **Signal badges**: Max 3-5 words in badge; use `.signal-desc` for longer explanations
13. **RSI Gauge**: Must include Oversold/Overbought labels + zone markers at 30/50/70
14. **Enhanced Income Statement Breakdown**: Use gradient flow bands, stage headers, legend bar, margin callout boxes, and **narrative analysis box** below the legend (3-5 sentences interpreting gross/operating/net margins, dominant expenses, and business model implications)
15. **Enhanced Corridor Chart**: Use SVG viewBox 600x200, animated lines, hover points, end badges, gradient fills
16. **Simulation signals**: Always compute regime detection, event probabilities, and scenario weights; integrate into Sections 3, 5, 11, 12, 13, 18
17. **Shares & Ownership narrative**: Always include "Ownership & Insider Activity Analysis" narrative box below ownership/transactions data (3-5 sentences on institutional balance, insider selling patterns, founder alignment)
18. **Macro Dashboard narrative**: Always include "Macro Environment Analysis" narrative box below Fed chart (3-5 sentences on GDP, Fed policy, inflation, employment, net macro signal for the ticker)
19. **Narrative integrity**: ALL narrative boxes (S10, S11, S14, S15) must be **standalone per ticker** — NEVER reference other tickers/companies (e.g., "Unlike HOOD..." is FORBIDDEN). Ground every claim in numerical metrics from the report data. Do not fabricate or hallucinate figures not present in the collected data
20. **Technical Indicators narrative**: Always include "Technical Analysis Summary" narrative box below Row 3 signal tiles (3-5 sentences on RSI zone, MACD direction, MA distance, trend-break status, fragility, regime)
21. **Complete narrative inventory**: Every report must contain exactly **7 interpretive elements** — S7 Benchmark Analysis, S10 Income Statement Analysis, S11 Technical Analysis Summary, S14 Ownership & Insider Activity, S15 Macro Environment Analysis, S17 Key Takeaway, S18 Net Assessment. Do NOT add narrative boxes to other sections (card height limits apply to side-by-side cards S8, S9, S13, S16)
17. **Regime probabilities**: MUST sum to 1.0; crash probability capped at 35%
18. **Event probability bounds**: All event probabilities clipped to [1%, 85%]
19. **Simulation visualization (12)**: Always include full-width Event Risk Simulation card with regime bars, heatmap, and scenario weights after Section 11
