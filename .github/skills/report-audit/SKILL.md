---
name: report-audit
description: >
  Audit and validate stock analysis HTML reports for data consistency, prediction alignment,
  and professional quality. USE FOR: "audit TSLA report", "check report consistency",
  "validate predictions", "review report quality", "data audit", "cross-check numbers",
  "find inconsistencies", "QA the report", report validation, prediction alignment check.
  DO NOT USE FOR: generating new reports (use report-generation), fixing CSS/layout bugs
  (use report-fix), or standalone signal analysis (use short-term-analysis/long-term-prediction).
---

# Report Audit & Quality Assurance Skill

## Overview
Systematically audit a stock analysis HTML report for data consistency, prediction alignment,
calculation accuracy, and professional quality. Produces a structured audit report with
PASS/WARN/FAIL ratings per check.

## Audit Framework — 7 Validation Layers

### Layer 1: Cross-Section Price Consistency
**Goal**: Ensure price predictions are consistent across all report sections.

| Check | Compare | Must Match |
|---|---|---|
| 1a. Current price | Header (Section 2) vs all other sections | Exact match everywhere |
| 1b. Year-end targets | Section 4 (Price Target Table) vs Section 5 (Monthly Forecast Dec row) | Exact match for all 3 scenarios |
| 1c. Corridor chart | Section 5 (SVG data points) vs Section 4 (multi-year targets) | End-of-year values must align |
| 1d. Analyst target | Section 8 (Analyst Consensus) vs Section 3 (Executive Summary) | Same value |
| 1e. Monthly path | Each month must be between previous and next month | No reversals without explicit dip annotation |

**How to check**: Search for dollar values across all sections. Create a price matrix:
```
Section → Conservative 2026 | Average 2026 | Bullish 2026
S4 Table:     $___          |    $___       |    $___
S5 Monthly:   $___          |    $___       |    $___
S5 Chart:     $___          |    $___       |    $___
S6 Assumptions: implied     |   implied     |   implied
→ All must be identical
```

### Layer 2: Signal & Score Consistency
**Goal**: Ensure TB/VS/VF, Fragility, and CCRLO scores are consistent across sections.

| Check | Compare | Must Match |
|---|---|---|
| 2a. TB/VS/VF | Section 3 (Exec Summary) vs Section 11 (Technical Indicators) | Same checkmarks |
| 2b. Fragility Score | Section 3 vs Section 11 | Same X/5 |
| 2c. CCRLO Score | Section 3 (Long-Term) vs Section 18 (Scorecard) | Same X/21 and probability |
| 2d. RSI value | Section 3 (mentioned) vs Section 11 (table row) vs RSI Gauge | All same number |
| 2e. Signal badges | Bearish/Neutral/Bullish consistent with the actual values | RSI <30 = bearish, >70 = bearish (overbought), etc. |
| 2f. Market Regime | Section 3 (Exec Summary) vs Section 11 (Technical Indicators regime row) | Same dominant regime and probability |
| 2g. Event Risk | Section 3 (top event) vs Section 11 (Event Risk 20d row) | Same event and probability |
| 2h. Event Risk tile | Section 11 (Event Risk row) vs Section 18 (Event Risk tile) | Consistent risk level (GREEN/AMBER/RED) |

### Layer 3: Financial Data Accuracy
**Goal**: Verify financial figures are internally consistent.

| Check | What to Verify |
|---|---|
| 3a. Revenue math | Gross Profit = Revenue - COGS (within rounding) |
| 3b. Margin math | Gross Margin = Gross Profit / Revenue × 100 |
| 3c. EPS consistency | Annual EPS in journey vs EPS in bar chart vs earnings table |
| 3d. Income Statement Breakdown totals | Revenue node = sum of all downstream flows |
| 3e. Balance sheet | Assets ≈ Liabilities + Equity (within rounding) |
| 3f. D/E calculation | If stated, verify Debt / Equity matches balance sheet values |
| 3g. FCF | Operating CF - CapEx = FCF (verify if stated) |

### Layer 4: Prediction Methodology Alignment
**Goal**: Ensure predictions follow the documented strategy rules.

| Check | Verify Against |
|---|---|
| 4a. Correction probabilities | Base probabilities adjusted correctly by fragility score (per `.instructions/short-term-strategy.md` calibration table) |
| 4b. CCRLO scoring | Each of 7 features scored 0-3 correctly based on data (per `.instructions/long-term-strategy.md`) |
| 4c. Monthly forecast shape | Near-term bearish if TB active; recovery toward analyst target in average scenario |
| 4d. Dip placement | Aug/Sep dip consistent with CCRLO probability and seasonal patterns |
| 4e. Scenario assumptions | Conservative worst-case < Average < Bullish best-case (monotonic ordering) |
| 4f. Monthly accuracy | Past months show Model Est, Actual, and Accuracy % with correct math: Accuracy = 100% - |error%| |
| 4g. Backtest summary row | Average accuracy row present below actual months with colored badge |
| 4h. Regime probabilities | 4 regime probabilities present and sum to 100% (Calm + Trending + Stressed + Crash-Prone) |
| 4i. Event probability bounds | All event probabilities in [1%, 85%]; crash-like capped at 35% |
| 4j. Scenario weights | 4 scenario weights present and sum to 100% |
| 4k. Regime-CCRLO alignment | If CCRLO HIGH (>=12), crash-prone regime should have >15% probability |
| 4l. Regime-fragility alignment | If fragility >=3, crash-prone regime should have >15% probability |

### Layer 4b: Income Statement Breakdown & Chart Data Integrity
**Goal**: Financial visualizations are mathematically correct.

| Check | Verify |
|---|---|
| 4b1. Income flow revenue balance | Revenue node = COGS + Gross Profit (within $100M rounding) |
| 4b2. Income flow OpEx detail | R&D + SG&A + Other = total OpEx stated (note any gap as "Other") |
| 4b3. Income flow net income path | Note if interest income not shown; add footnote explaining the gap |
| 4b4. Corridor chart data points | SVG circle coordinates map correctly to stated dollar values |
| 4b5. EPS journey colors | Color intensity maps to EPS value: peak = darkest green, declining = lighter, loss = red/amber |
| 4b6. Income Statement Breakdown node spacing | In the DETAIL column (Stage 4), every adjacent pair of nodes must have ≥12px vertical gap between the bottom of one node's lowest text label and the top of the next node's `<rect>`. Text at font-size 8px extends ~7px below its y-coordinate. If labels overlap visually, it is a FAIL |
| 4b7. Income Statement Breakdown label format | Every node must show the dollar amount on one line (`<text class="sankey-amount">`) and the percentage on a **separate line below** (`<text class="sankey-pct">`). Never combine amount and percentage inline like `SGA $11.2B (1.6%)` — always split into two `<text>` elements. This ensures consistent formatting across all nodes |

### Layer 4c: External Link & URL Integrity
**Goal**: All hyperlinks are correct and functional.

| Check | Verify |
|---|---|
| 4c1. News article URLs | Every `<a href>` points to correct ticker/company (e.g., not /stocks/INTC/ for a TSLA article) |
| 4c2. URL domain match | Article source domain matches the stated source name |
| 4c3. No placeholder URLs | No `#`, `javascript:void`, or example.com links |

### Layer 5: Structural Completeness & Section Name Consistency
**Goal**: All 20 sections present with required subsections, and all `<h2>` titles exactly match the canonical names from the HOOD gold standard.

#### 5A. Section Name Consistency (CRITICAL)
Every `<h2>` title must match the canonical name from the HOOD gold standard. The only variable parts are `(FY[YEAR])` in Section 10 and `[Industry] Peers` in Section 17.

| Section | Canonical `<h2>` Title (exact match required) |
|---|---|
| S3 | `Executive Summary & Analysis` |
| S4 | `Price Target Projections — Multi-Year Scenario Analysis` |
| S5 | `Expected Price Corridors & Correction Scenarios` |
| S6 | `Scenario Assumptions & Revenue Projections` |
| S7 | `Performance vs. S&P 500 Benchmark` |
| S8a | `Analyst Consensus` |
| S8b | `Quarterly EPS Trajectory` |
| S9a | `Valuation Metrics` |
| S9b | `Financial Health` |
| S10 | `Financial Flow — Income Statement Breakdown (FY[YEAR])` |
| S11 | `Technical Indicators` |
| S12 | `Event Risk Simulation — 20-Day Forward Analysis` |
| S13a | `Recent News & Sentiment` |
| S13b | `Key Risks & Catalyst Factors` |
| S14 | `Shares & Ownership` |
| S15 | `US Economic Indicators — Macro Dashboard` |
| S16a | `Global Market Indicators` |
| S16b | `Macro-Equity Correlation Analysis` |
| S17 | `Competitive Landscape — [Industry] Peers` |
| S18 | `Net Macro Environment Scorecard` |

**Common mismatches to watch for**:
- S7: "Benchmark Comparison — S&P 500" ≠ "Performance vs. S&P 500 Benchmark"
- S8b: "Quarterly EPS & Earnings Surprise" ≠ "Quarterly EPS Trajectory"
- S13b: "Key Risks & Catalysts" ≠ "Key Risks & Catalyst Factors"
- S17: "Competitive Landscape — Peer Comparison" ≠ "Competitive Landscape — [Industry] Peers"

**How to check**: Extract all `<h2>` tags from the report and compare against this table.

#### 5B. Structural Completeness

| Check | Required Element |
|---|---|
| 5a. Section count | All 20 sections present (Export → Timestamp) |
| 5b. Card splitting | Price Target split into 3 separate cards (Sections 4, 5, 6) |
| 5c. Income Statement Breakdown SVG graph | Section 10 must contain `<svg class="sankey-svg">` with flow `<path>` elements, `<linearGradient>` defs, stage header labels, node `<rect>` elements, and `.sankey-legend` bar below. A section with only a table and no SVG is a FAIL |
| 5c2. S10 stage labels | Must have 4 `.sankey-stage-label` texts: **REVENUE**, **COST SPLIT**, **OPERATIONS**, **DETAIL** (in uppercase). Using non-standard names (e.g., "Cost Structure", "Bottom Line") or having fewer than 4 labels = FAIL |
| 5c3. S10 margin callout | Must have a Gross Margin + Net Margin callout box above the SVG (centered `display:inline-flex` div with `background:#f0fdf4; border:1px solid #bbf7d0`). Missing = FAIL |
| 5c4. S10 DETAIL nodes | DETAIL column (Stage 4) must break down OpEx into sub-categories (at minimum R&D + SGA). Must also show Net Income and Tax nodes. A Sankey that goes only Revenue → COGS/GP → OpEx/OpInc without DETAIL breakdown = FAIL |
| 5d. Monthly forecast | Present in Section 5 with actual + predicted months |
| 5d2. Dual benchmark charts | Section 7 has TWO SVG charts: 12-Month (monthly x-axis) + 5-Year (annual x-axis). Y-axis must show cumulative % return (e.g., +200%, +50%, 0%, -25%) NOT normalized index values (e.g., 100, 150, 200). The 0% baseline line must use a heavier stroke (`stroke-width: 1`) or solid style. If ticker &lt;5yr history, 5-Year chart starts from earliest date with subtitle note |
| 5e. Signal rows | TB/VS/VF and Fragility rows in Technical Indicators (Section 11) |
| 5f. CCRLO tile | Present in Macro Scorecard (Section 18) |
| 5g. Disclaimer + Timestamp | Both present at bottom |
| 5h. Market Regime row | Present in Section 11 with `.regime-bar` in Market Regime tile (Row 3) |
| 5i. Event Risk row | Present in Section 11 with Event Risk (20d) tile showing top 3 event signal badges (Row 3) |
| 5j. Event Risk tile | Present in Section 18 scorecard with GREEN/AMBER/RED color |
| 5k. Regime badge | Present in Section 3 Executive Summary (dominant regime + probability) |
| 5k2. Analyst Consensus visual layout (S8a) | Must use the **visual graph layout** (NOT a table-based breakdown). Required structure: (a) **Centered hero block**: large green target price (`font-size:1.4em; font-weight:700; color:#16a34a`), subtitle "Mean Target Price (+X% upside)" (`color:#5a6577`), analyst count + latest quarter (`color:#8a94a6`). (b) **Visual `.rating-bar`** with proportional colored segments (`.rb-strong-buy`, `.rb-buy`, `.rb-hold`, `.rb-sell`). Width proportional to percentage. Labels show count + abbreviation (e.g., "15 SB", "48 Buy"). Omit sell segment if 0 analysts. (c) **Percentage breakdown text** as a single centered line below the bar: "Strong Buy: X% • Buy: X% • Hold: X% • Sell: X%". (d) **Green consensus box** (`background:#f0fdf4; border:1px solid #bbf7d0`) containing `<strong>Consensus:</strong>` + signal badge (`.signal.strong-buy` or `.signal.bullish`) + summary narrative text. **FAIL if**: uses `<table>` for rating breakdown, missing target price hero, missing consensus box, or has inline text format instead of centered hero block |
| 5l. Event Risk Simulation layout (S12) | Full-width card using `.sim-grid` with TWO `.sim-panel` children side by side. Missing either panel is a FAIL |
| 5l1. Left panel: Regime Detection | Must contain: (a) `<h3>Regime Detection</h3>` + description text. (b) **4 regime probability rows** in order: Calm, Trending, Stressed, Crash-Prone — each using `.regime-row` with colored `.regime-pct-fill` bar + percentage value. ALL 4 MUST be present even if value is 0%. (c) **4 regime explanation boxes** in order: Calm (green `#f0fdf4`), Trending (blue `#eff6ff`), Stressed (amber `#fffbeb`), Crash-Prone (red `#fef2f2`) — ALL 4 REQUIRED even if probability is 0%. Missing any box is a FAIL |
| 5l2. Left panel: Scenario Price Targets | Must contain: `<h3>Scenario Price Targets</h3>` + table with columns (Scenario, Weight, Price Range, Expected P/L) and exactly 4 rows: Base Case, Vol Expansion, Trend Shift, Tail Risk. Each cell must have real data or "N/A" — empty cells are a FAIL. Below table: **Weighted Expected Price callout** (green box `#f0fdf4`) showing dollar amount + percentage change + 80% Confidence range + Downside Skew percentage |
| 5l3. Right panel: Event Heatmap | Must contain: `<h3>Event Probability & Price Impact Heatmap</h3>` + table with columns (Event, 5d, 10d, 20d, Price Impact) and exactly 6 rows in order: Large Move, Vol Spike, Trend Reversal, Earnings Reaction, Liquidity Stress, Crash-Like. Each probability cell must use `.heatmap-low/med/high/extreme` class. Each cell must have real percentage data or "N/A" — empty cells are a FAIL |
| 5l4. Right panel: Stat tiles | Must have exactly 4 stat tiles below the heatmap in order: Disagreement (value + color), Confidence (label + color), Composite Risk (percentage + colored background), Downside Skew (percentage in red). ALL 4 REQUIRED. Missing any tile is a FAIL |
| 5m. Technical Indicators layout (S11) | Section 11 must have 3 rows in this order: **Row 1** — 4 tiles side by side: RSI (14), MACD, ADX (14), ATR (14). **Row 2** — Moving Averages table + Bollinger Bands visual side by side. **Row 3** — 4 signal tiles side by side: Trend-Break Status, Fragility Score, Market Regime, Event Risk (20d). Missing any element or wrong order is a FAIL |
| 5m1. Moving Averages table format | Must have a **"Moving Averages" title div** before the table (`font-size:0.82em; color:#1b2a4a; font-weight:600`). Must have `<thead>` with columns: Indicator, Value, vs Price ($XX.XX). Rows in order: **50-Day MA**, **200-Day MA**, **EMA 12**, **EMA 26** (use "50-Day MA" not "SMA 50"). Each row shows signal badge with "-X.X%" or "+X.X%". Uses `flex:2; min-width:300px`. Missing title = FAIL. Wrong MA naming = FAIL |
| 5m2. Bollinger Bands visual | Must use the **gradient bar visual** (not a plain table). Title must be **"Bollinger Bands (20, 2)"** (always include parameters). Structure: Upper price + "Resistance" label → gradient bar (`linear-gradient(90deg, #fecaca, #fef3c7, #d1fae5)`) with blue price position marker → Lower price + "Support" label → Middle price note. Uses `flex:1; min-width:240px`. Missing parameters in title = WARN |
| 5m3. ADX tile format | Must show: value, signal badge, "Trend strength: **X**" + ">25 = trending, >50 = strong" subtitle |
| 5m4. ATR tile format | Must show: value, percentile badge (e.g., "25.9th pctile"), "Daily swing: **~X%**" + volatility description subtitle |
| 5m5. Row 3 tile uniformity | All 4 Row 3 tiles must use uniform `background:#f8fafc; border:1px solid #e8ecf3` with colored `border-left:3px solid [color]` accents. Never use semantic backgrounds (`#fffbeb`, `#f0fdf4`) on individual tiles. Market Regime tile must show `.regime-bar` with **all 4 segments** (Calm, Trending, Stressed, Crash-Prone) even if some have 0% width. Missing segments = FAIL |
| 5n. Shares & Ownership layout (S14) | Full-width card with flexbox layout containing: (a) **Left side**: Ownership statistics table (Shares Outstanding, Float, Institutional %, Insider %, Book Value, Dividend) + **Leadership & Key Stakeholders** table with `<thead>` (Name, Role) and CEO row highlighted `background:#eff6ff`. (b) **Right side**: **Recent Insider Transactions** table with `<thead>` columns: Date, Insider, Title, Type, Shares, Price, **Avg Value**. Avg Value = Shares × Avg Price. Must have at least 3 transactions. Missing Leadership or Insider Transactions section is a FAIL. (c) **Narrative analysis box** below the flex container with title "Ownership & Insider Activity Analysis" (3-5 sentences interpreting institutional balance, insider selling patterns, founder alignment). Missing narrative = FAIL |
| 5o. Macro Dashboard layout (S15) | Must contain: (a) **Macro table** with `<thead>` columns: Indicator, Current/Latest, Prior (optional), Trend, {{TICKER}} Impact — at least 4 rows (GDP, CPI, Fed Funds Rate, Unemployment). (b) **Federal Funds Rate bar chart** titled "Federal Funds Rate — Last 12 Months" with **exactly 12 colored column bars** using **fixed pixel heights** (NOT percentage heights). **Bar spacing**: Each bar column must use `flex:1` to spread evenly across the full container width — never `min-width:40px` which causes bars to bunch left. **Bar order**: oldest month on the left, newest on the right (chronological left-to-right). Each bar: rate label above (MUST include `%` suffix, e.g., `4.33%`), colored `<div>` bar (`width:30px`), month label below. Colors: 4%+ Red `#dc2626`, 3.5-4% Orange `#fd7e14`/`#d97706`, <3.5% Amber. Data source: Alpha Vantage `FEDERAL_FUNDS_RATE`. NO prediction/forecast bars. Bars with no visible height or fewer than 12 bars = FAIL. Rate labels without `%` suffix = FAIL. Bars using `min-width` instead of `flex:1` = FAIL. (c) **Narrative analysis box** below the Fed chart with title "Macro Environment Analysis" (3-5 sentences interpreting GDP, Fed policy, inflation, employment, net macro signal for the ticker). Missing narrative = FAIL |
| 5p. S2 Header structure | Header must contain: (a) `.header-top` with `.company-info` (h1 + subtitle) + `.price-block` (price + change badge). (b) `.meta-row` with at least 10 meta items: Open, High, Low, Close, Volume, Market Cap, P/E, Beta, 52-Wk, Date. Missing any core meta item = WARN |
| 5q. S5 Correction Risk table columns | Must have `<thead>` with exactly 5 columns in order: **Scenario | Drawdown | Price Floor | 12-Month Probability | Trigger**. Probability column must use nested `<div>` bar format (outer `background:#e8ecf3` + inner colored fill + `<span>` percentage). Using "Recovery Time" instead of "Trigger", or plain text probabilities without visual bars = FAIL |
| 5q2. S5 Support & Resistance format | Must use **colored pill badge layout**: Support levels as green `<span>` badges (`background:#d4edda; color:#155724`) and Resistance levels as red/pink `<span>` badges (`background:#f8d7da; color:#721c24`). Each badge contains `$PRICE (Label)`. Using plain text lists with colored SUPPORT/RESISTANCE headers (text-list style) instead of pill badges = FAIL |
| 5r. S6 Revenue Projections table | Must have `<thead>` with **4+ columns** including: Metric, **FY Actual** (e.g., "FY2025 (Actual)"), FY Conservative, FY Average, FY Bullish. Must include rows: Revenue, EPS, Implied P/E, Target Price. **Missing FY Actual column** = FAIL. The Target Price row must match Section 4 year-end targets (Conservative/Average/Bullish) |
| 5s. S8a rating bar labels | Every segment in `.rating-bar` must show **count + abbreviation text** (e.g., "15 SB", "48 Buy", "3 Hold", "2 Sell"). A segment showing only a number without text (e.g., "4" instead of "4 Hold") = FAIL. Omit sell segment only if 0 analysts |
| 5t. S8b EPS chart + surprise table | Must have: (a) `.eps-chart` with `eps-bar-wrap` bars showing EPS values and quarter labels (minimum 4 quarters). (b) Earnings surprise table with `<thead>` columns: Quarter, Reported, Estimate, Surprise. Surprise uses signal badges. (c) Streak text below (e.g., "4 consecutive beats"). Missing chart or table = FAIL |
| 5u. S9a Valuation table format | Must use **2-column format** (Label | Value) matching template. Rows: Market Cap, P/E Trailing, P/E Forward, P/S, P/B, EV/Revenue, EV/EBITDA, PEG. **3-column format with signal badges in a third column** ≠ template pattern — WARN. Must include **Revenue Growth Journey (Revenue)** OR **Profitability Journey (EPS)** using **column bar visualization** (`rev-chart` class with `rev-bar-wrap` > `rev-bar-val` > `rev-bar` > `rev-bar-label` children). Chart title must include the metric in parentheses: (Revenue), (EPS). Structure: flex container (`display:flex; align-items:flex-end`) with vertical bars, each bar showing a dollar/value label above, a colored `<div>` with percentage height, and a year label below. Final bar must use green gradient (`linear-gradient(180deg, #16a34a, #15803d)`). Must have at least 3 years of data. **FAIL if**: uses `journey` pill-style layout (`.journey-step` + `.journey-arrow`), missing chart entirely, fewer than 3 data points, or chart title missing metric suffix |
| 5v. S9b Financial Health table format | Must use **2-column format** (Label | Value) matching template. Revenue with growth %, Gross Profit with margin %, Operating Income with margin %, Net Income with margin %, Operating CF, FCF, Cash, Debt, Equity, ROE. **3-column format** ≠ template — WARN. Must include **Profitability Journey (Net Income)** using **column bar visualization** (`rev-chart` class with `rev-bar-wrap` > `rev-bar-val` > `rev-bar` > `rev-bar-label` children). Structure: flex container with vertical bars showing net income per year. Negative years use red gradient (`linear-gradient(180deg, #ef4444, #b91c1c)` with `border-radius:0 0 3px 3px`). Final positive bar must use green gradient. Must have at least 3 years of data. **FAIL if**: uses `journey` pill-style layout, missing chart entirely, or fewer than 3 data points |
| 5w. S7 Period Returns format | Period Returns table must use `<thead>` with columns: Period, {{TICKER}}, S&P 500, Outperformance. Return values must use `<span class="signal ...">` badges (bullish for positive, bearish for negative). Raw styled text without signal badges = WARN. Statistical Analysis table must have: Beta, Correlation, Alpha, Sharpe Ratio, Max Drawdown — uses 2-column format (no thead needed) |
| 5x. S13b Risks table format | Must have `<thead>` with columns: Factor, Type, Impact. Type column uses signal badges (Catalyst=bullish, Risk=bearish, Mixed=neutral). Must have at least 5 rows. If fragility ≥3, must include fragility-related risk. If tail_risk weight >15%, must include tail risk row |
| 5y. S16a/S16b content | S16a must have `<thead>` columns: Asset, Level, Trend. Must include at least 5 assets (Gold, Oil, 10Y Treasury, a currency pair, VIX). S16b must have `<thead>` columns: Factor, Direction/Sensitivity, Impact on {{TICKER}}. Must include at least 4 macro factors. Missing either section or empty table = FAIL |
| 5z. S17 Competitive table columns | Must have `<thead>` with **10 columns** in order: Company, Price, Mkt Cap, Revenue, Rev Growth, **Gross Margin**, P/E, P/S, EV/Rev, Analyst. Using "Margin" instead of "Gross Margin" = WARN. Must have subject row with `background:#eff6ff`. Must have Positioning Map table (6 dimensions) + Key Takeaway box (`background:#fffbeb`). Missing Positioning Map or Key Takeaway = FAIL |
| 5aa. S19 Disclaimer | Must contain: (a) `.disclaimer` class with `<h4>Important Disclaimer & Methodology</h4>` + `<p>`. (b) Must mention: "not investment advice", "Alpha Vantage", "model-based estimates", "past performance", "Python (analyst_compute_engine.py)", "20-section layout". Missing disclaimer or missing key terms = FAIL |
| 5bb. S20 Timestamp + Export | (a) `.timestamp` class with generation line only: "Report generated on {{DATE}} &bull; Data source: Alpha Vantage". No "About This Report" narrative — methodology is merged into S19 disclaimer. (b) Export function `exportToPDF()` must **save and restore** `document.title` — pattern: `const origTitle = document.title; document.title = ...; window.print(); document.title = origTitle;`. Missing title restore = FAIL |

### Layer 6: Styling & CSS Compliance
**Goal**: Report follows report-template.html styling rules.

| Check | Rule |
|---|---|
| 6a. Bullet points | CSS `\25B8` via `::before`, NOT HTML entities `&#9656;` |
| 6b. Layout | Flexbox only, no CSS Grid, no absolute positioning for S&R |
| 6c. Signal badges | Correct class: `.signal.bullish`, `.signal.bearish`, `.signal.neutral` |
| 6d. **Signal badge length** | **Max 3-5 words in badge**. If longer, must split into badge + `.signal-desc` on next line |
| 6e. Subject row | `background:#eff6ff;` in competitive landscape |
| 6f. Key Takeaway box | `background:#fffbeb; border:1px solid #fde68a;` |
| 6g. RSI Gauge | Has Oversold/Overbought labels + zone markers at 30/50/70 |
| 6h. Corridor chart | Has `.corridor-*` classes, animated lines, interactive points |
| 6i. Income Statement Breakdown | Has `.sankey-*` classes, gradient fills, legend, and **narrative analysis box** below legend with "Income Statement Analysis" title (3-5 sentences interpreting margins and cost structure). Missing narrative = FAIL |
| 6i2. Ownership narrative (S14) | Has **narrative analysis box** below ownership/transactions flex container with "Ownership & Insider Activity Analysis" title (3-5 sentences). Missing = FAIL |
| 6i3. Macro narrative (S15) | Has **narrative analysis box** below Fed chart with "Macro Environment Analysis" title (3-5 sentences). Missing = FAIL |
| 6i4. **Narrative integrity** | ALL narrative boxes (S10, S11, S14, S15) must be: (a) **Standalone** — NEVER references another ticker symbol or company name as a comparison (e.g., "Unlike HOOD", "vs. MSFT's margins"). Cross-ticker comparison in a narrative box = FAIL. (b) **Data-grounded** — every claim cites specific numerical metrics ($amounts, percentages, ratios) from the report. Qualitative claims without supporting numbers = WARN. (c) **No fabrication** — only uses data present elsewhere in the same report or fetched from Alpha Vantage. Figures not traceable to report data = FAIL |
| 6i5. Technical narrative (S11) | Has **narrative analysis box** below Row 3 signal tiles with "Technical Analysis Summary" title (3-5 sentences interpreting RSI, MACD, MA distance, TB status, fragility, regime). Missing = FAIL |
| 6i6. **Complete narrative inventory** | Report must contain exactly **7 interpretive analysis elements**: S7 Benchmark Analysis box, S10 Income Statement Analysis, S11 Technical Analysis Summary, S14 Ownership & Insider Activity Analysis, S15 Macro Environment Analysis, S17 Key Takeaway box, S18 Net Assessment box. Missing any = FAIL. Extra narrative boxes in other sections (S4, S6, S8, S9, S12, S13, S16) = WARN (risk of card height overflow and narrative fatigue) || 6j. **Container overflow** | No text/element visually overflows its parent card or summary-box |
| 6k. **Card height** | No single card exceeds ~60% of A4 landscape height (~400px) |
| 6l. **Monthly forecast table** | If present, must not exceed card height limit; split if needed |
| 6s. **CSS class completeness** | The `<style>` block must include CSS definitions for ALL classes used in the HTML body. Critical classes that must be present if used: `.rev-chart`, `.rev-bar-wrap`, `.rev-bar`, `.rev-bar-val`, `.rev-bar-label`, `.eps-chart`, `.eps-bar-wrap`, `.eps-bar`, `.regime-bar`, `.regime-row`, `.sim-grid`, `.sim-panel`, `.heatmap-low/med/high/extreme`, `.corridor-*`, `.sankey-*`. Missing CSS for used HTML classes causes visual collapse (bars render as flat text). FAIL if any class used in HTML body has no corresponding CSS rule |
| 6m. **Regime row styling** | Market Regime row uses `background:#f0f9ff` with `.regime-bar` progress bar |
| 6n. **Event Risk row styling** | Event Risk row uses `background:#fef3c7` with `.signal` badges for top events |
| 6o. **Event Risk tile color** | GREEN (`#16a34a`) if <15%, AMBER (`#d97706`) if 15-30%, RED (`#dc2626`) if >30% |
| 6p. **Heatmap colors** | `.heatmap-low` (<10%), `.heatmap-med` (10-20%), `.heatmap-high` (20-30%), `.heatmap-extreme` (>30%) correctly applied |
| 6q. **Scenario price ranges** | Price ranges in 8b consistent with ATR and current price; tail risk range shows negative P/L only |
| 6r. **Weighted expected price** | Weighted price equals Σ(weight×midpoint); percentage change from current price is correct |

### Layer 7: News & External Data Freshness + Macro Consistency
**Goal**: Report uses current data, functional links, and correct market-wide macro values.

| Check | Verify |
|---|---|
| 7a. News recency | All news items within last 7 days of report date |
| 7b. Hyperlinks | Every news item has `<a href="...">` tag |
| 7c. Sentiment mapping | Badges match Alpha Vantage `overall_sentiment_label` |
| 7d. Macro data date | Fed rate, CPI, GDP dates are recent (within 1-2 months) |
| 7e. Price date | Header date matches `latest trading day` from GLOBAL_QUOTE |
| 7f. **Fed chart data depth** | Fed Funds Rate bar chart must have **exactly 12 bars** with **12 distinct monthly values from API data**. Check that the values show a realistic rate trajectory (no flat runs of fabricated values). **FAIL** if: (a) fewer than 12 bars, (b) values appear interpolated/estimated rather than actual API data, (c) all values are identical when they should show rate changes |
| 7g. **Cross-report macro consistency** | When auditing multiple reports from the same session: CPI, Fed Funds Rate, Unemployment, and GDP values must be **identical** across all reports. The only difference should be the `{{TICKER}} Impact` column text. Compare: (a) Macro Dashboard table values, (b) Fed chart bar values, (c) CCRLO `ig_credit` feature value (should use same FFR), (d) Scorecard macro tiles |
| 7h. **Fed chart vs Macro table** | The Fed Funds Rate shown in the Macro Dashboard table row must match the most recent bar in the Fed chart. The Prior value must match the second-most-recent bar |
| 7i. **Macro values vs gold standard** | If HOOD gold standard exists, the CPI, FFR, Unemployment, and GDP values in the report should match HOOD (since macro data is market-wide and identical). Mismatches indicate stale or fabricated data |
| 7j. **Macro value FORMAT consistency** | GDP must use **dollar value format** (e.g., "$6,125.9B") not percentage format (e.g., "2.1% QoQ"). CPI must use **index value** (e.g., "326.79") not a different index base. Unemployment must use **percentage** (e.g., "4.4%"). All reports in same session must use identical format AND value. Format mismatches between reports = FAIL |
| 7k. **Macro table ticker-impact column** | The only column that should differ between reports is the `{{TICKER}} Impact` text — all other columns (Indicator, Current, Prior, Trend) must be identical word-for-word across same-session reports |

## Audit Output Format

```
═══════════════════════════════════════════════
 REPORT AUDIT — [TICKER]-analysis.html
 Date: [AUDIT DATE]
 Report Date: [REPORT DATE]
═══════════════════════════════════════════════

LAYER 1: PRICE CONSISTENCY
  ✅ 1a. Current price: $380.30 consistent across all sections
  ✅ 1b. Year-end targets: S4=$300/$421/$500, S5 Dec=$300/$421/$500 — MATCH
  ✅ 1c. Corridor chart: End badges = $500/$900/$1500 (2029) — correct
  ✅ 1d. Analyst target: $421.61 in S3, S9 — MATCH
  ⚠️ 1e. Monthly path: Conservative Aug $310 → Sep $315 (uptick in bear path)
  LAYER SCORE: 4/5 PASS, 1 WARN

LAYER 2: SIGNAL CONSISTENCY
  ✅ 2a. TB/VS/VF: S3 = ✓✓✓, S11 = ✓✓✓ — MATCH
  ✅ 2b. Fragility: S3 = 3/5, S11 = 3/5 — MATCH
  ✅ 2c. CCRLO: S3 = 6/21, S18 = 6/21 — MATCH
  ✅ 2d. RSI: S3 = 36.4, S11 = 36.43, Gauge = 36.4% — CONSISTENT
  ✅ 2e. Signal badges: RSI 36.4 = neutral (approaching oversold) — CORRECT
  ✅ 2f. Market Regime: S3 = TRENDING 42%, S11 = TRENDING 42% — MATCH
  ✅ 2g. Event Risk: S3 top = Vol Spike 30%, S11 = Vol Spike 30% — MATCH
  ✅ 2h. Event Risk tile: S11 avg top-3 = 22% (AMBER), S18 = NEUTRAL (AMBER) — MATCH
  LAYER SCORE: 8/8 PASS

LAYER 3: FINANCIAL DATA
  ✅ 3a. Revenue: $94.83B - COGS $77.73B = GP $17.09B ≈ $17.1B stated — OK
  ✅ 3b. Margin: $17.1B / $94.8B = 18.04% ≈ 18.0% stated — OK
  ✅ 3c. EPS: Journey 2025=$1.34, Bar chart 2025=$1.34 — MATCH
  ✅ 3d. Income Statement Breakdown: Revenue $94.8B = COGS $77.7B + GP $17.1B — BALANCED
  ✅ 3e. FCF: $14.75B OCF - $8.53B CapEx = $6.22B ≈ $6.2B stated — OK
  LAYER SCORE: 5/5 PASS

LAYER 4: PREDICTION METHODOLOGY
  ✅ 4a. Correction probs adjusted for fragility 3/5 (moderate = +0%) — CORRECT
  ✅ 4b. CCRLO: 0+0+2+0+2+2+0 = 6/21 — VERIFIED
  ✅ 4c. Monthly: Near-term bearish (Apr $365 conservative < $380 current) — CORRECT
  ✅ 4d. Dip: Aug dip present in all scenarios — CONSISTENT with CCRLO
  ✅ 4e. Ordering: Conservative < Average < Bullish for all months — CORRECT
  ✅ 4h. Regime probs: Calm 20% + Trend 42% + Stress 28% + Crash 10% = 100% — SUM OK
  ✅ 4i. Event bounds: All events in [1%, 85%], crash 5% ≤ 35% — OK
  ✅ 4j. Scenario weights: Base 55% + Vol 20% + Trend 15% + Tail 10% = 100% — SUM OK
  ✅ 4k. Regime-CCRLO: CCRLO 6/21 (MODERATE), crash-prone 10% — ALIGNED
  ✅ 4l. Regime-Fragility: Fragility 3/5, crash-prone 10% (>0% when >=3) — ALIGNED
  LAYER SCORE: 10/10 PASS

LAYER 5: STRUCTURAL COMPLETENESS & SECTION NAMES
  ✅ 5-name. S3: "Executive Summary & Analysis" — MATCH
  ✅ 5-name. S4: "Price Target Projections — Multi-Year Scenario Analysis" — MATCH
  ✅ 5-name. S7: "Performance vs. S&P 500 Benchmark" — MATCH
  ❌ 5-name. S8b: "Quarterly EPS & Earnings Surprise" ≠ canonical "Quarterly EPS Trajectory" — FAIL
  ✅ 5-name. S17: "Competitive Landscape — Cloud & E-Commerce Peers" — MATCH (industry-specific)
  ✅ 5a. All 20 sections present
  ✅ 5b. Price Target = 3 separate cards (S4, S5, S6)
  ✅ 5c. Income Statement Breakdown SVG graph present in S10 with flow paths, gradients, stage headers, legend
  ✅ 5d. Monthly forecast: Jan-Mar actual + Apr-Dec predicted
  ✅ 5d2. Dual benchmark charts: S7 has 12-Month (monthly) + 5-Year (annual) SVG charts — PRESENT
  ✅ 5e. TB/VS/VF + Fragility tiles in Section 11 Row 3
  ✅ 5f. CCRLO tile in Section 18
  ✅ 5g. Disclaimer + Timestamp present
  ✅ 5h. Market Regime tile in Section 11 Row 3 with regime-bar
  ✅ 5i. Event Risk (20d) tile in Section 11 Row 3 with event badges
  ✅ 5j. Event Risk tile in Section 18 (AMBER)
  ✅ 5k. Regime badge in Section 3 (TRENDING 42%)
  ✅ 5k2. Analyst Consensus visual layout: centered hero + rating bar + % text + green consensus box
  ✅ 5l. Event Risk Simulation: .sim-grid with 2 .sim-panel children
  ✅ 5l1. Left: Regime Detection — 4 regime rows (Calm/Trending/Stressed/Crash-Prone) + 4 explanation boxes
  ✅ 5l2. Left: Scenario Price Targets — 4 rows (Base/Vol/Trend/Tail) + Weighted Expected Price callout
  ✅ 5l3. Right: Event Heatmap — 6 events × 3 horizons + Price Impact, all cells populated
  ✅ 5l4. Right: 4 stat tiles (Disagreement/Confidence/Composite Risk/Downside Skew)
  ✅ 5m. Technical Indicators: Row 1 (RSI/MACD/ADX/ATR tiles) + Row 2 (Moving Averages + Bollinger) + Row 3 (TB/Fragility/Regime/Event Risk tiles)
  ✅ 5n. Shares & Ownership: Leadership table + Recent Insider Transactions (with Avg Value column)
  ✅ 5o. Macro Dashboard: macro table (4+ rows) + Fed Funds Rate chart with 12 monthly bars, no prediction
  LAYER SCORE: 12/12 PASS

LAYER 6: STYLING COMPLIANCE
  [Check CSS classes and HTML patterns]

LAYER 7: NEWS FRESHNESS
  [Check dates and links]

═══════════════════════════════════════════════
 OVERALL: [X/Y] PASS | [X] WARN | [X] FAIL
 RECOMMENDATION: [PUBLISH / REVIEW / REWORK]
═══════════════════════════════════════════════
```

## Workflow

### Step 1: Read the Report
Read the target report HTML file from `reports/[TICKER]-analysis.html`.

### Step 2: Extract Key Values
Build a data matrix of all prices, scores, and signals mentioned across sections:
- Current price (Section 2 Header)
- Year-end targets (Section 4 table)
- Monthly forecast values (Section 5 table)
- Corridor chart data points (Section 5 SVG)
- Analyst target (Section 8a)
- TB/VS/VF status (Sections 3 & 11)
- Fragility score (Sections 3 & 11)
- CCRLO score (Sections 3 & 18)
- RSI/MACD/ATR values (Sections 3 & 11)
- Market Regime (Sections 3, 11, & 12)
- Event Risk (Sections 3, 11, 12, & 18)
- Revenue/EPS/Margin (Sections 8b, 9, & 10 Income Statement Breakdown)
- Macro data (Section 15 table & Fed chart)
- Competitive peer data (Section 17 table)

### Step 3: Run All 7 Layers
Execute each check systematically. For each:
- PASS (✅): values match
- WARN (⚠️): minor discrepancy or rounding difference
- FAIL (❌): material inconsistency that misleads the reader

### Step 4: Generate Audit Report
Output the structured audit report with layer scores, overall rating, and specific fix recommendations for any WARN/FAIL items.

### Step 5: Fix or Escalate
- If all PASS: report is publishable
- If WARN only: note for future improvement, publishable
- If any FAIL: report must be fixed before publishing — invoke report-fix skill

## Critical Rules
1. **Never approve a report with price inconsistency** — Section 4 year-end targets MUST match Section 5 monthly Dec row
2. **Never approve without all 20 sections** — structural completeness is mandatory
3. **Financial math must balance** — Revenue = COGS + Gross Profit (within $100M rounding)
4. **Signal scores must match everywhere they appear** — TB/VS/VF, Fragility, CCRLO
5. **The audit itself must be reproducible** — document every value checked
6. **Section `<h2>` titles must match canonical names exactly** — compare every `<h2>` against the canonical list in Layer 5A. Mismatched names are a FAIL.

## References
- `.instructions/report-layout.md` — 20-section order
- `.instructions/styling.md` — CSS rules
- `.instructions/short-term-strategy.md` — TB/VS/VF + Fragility calibration
- `.instructions/long-term-strategy.md` — CCRLO scoring
- `.instructions/analysis-methodology.md` — Price target + correction methodology
