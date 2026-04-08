# Market Analysis — Copilot Instructions

## Project Context
This project generates stock analysis HTML reports using Alpha Vantage MCP Server data. Each report is a standalone HTML file following a strict layout, styling, and PDF export spec.

## Folder Structure
```
market-analysis/
├── .github/copilot-instructions.md    ← You are here (auto-loaded by VS Code)
├── .github/agents/                    ← Custom agents (.agent.md files)
│   ├── stock-analyst.agent.md        ← Stock Analyst agent (appears in agent picker)
│   ├── test-engineer.agent.md        ← Test Engineer agent (system verification)
│   └── portfolio-manager.agent.md    ← Portfolio Manager agent (dashboard builder)
├── .github/workflows/                 ← CI/CD automation
│   └── system-guard.yml              ← Auto-test on script changes (push/PR)
├── .github/skills/                    ← Skills (auto-matched by task description)
│   ├── data-collection/SKILL.md      ← "fetch data" → standardized MCP data gathering
│   ├── report-generation/SKILL.md     ← "analyze TICKER" → full report workflow
│   ├── report-fix/SKILL.md           ← "fix the layout" → diagnose & repair
│   ├── short-term-analysis/SKILL.md  ← "short-term signal" → trend-break + fragility
│   ├── long-term-prediction/SKILL.md ← "correction risk" → CCRLO 6-month probability
│   ├── simulation/SKILL.md           ← "simulate events" → regime + event probabilities
│   ├── analyst-compute-engine/SKILL.md ← "compute signals" → unified Python pipeline
│   ├── numerical-audit/SKILL.md      ← "validate numbers" → numerical accuracy check
│   ├── report-audit/SKILL.md         ← "audit report" → 7-layer consistency check
│   ├── system-test/SKILL.md          ← "run tests" → 183-test automated verification
│   ├── stock-tagging/SKILL.md        ← "tag TICKER" → 5-dimension stock classification
│   ├── portfolio-build/SKILL.md      ← "build portfolio" → aggregate dashboard generation
│   └── portfolio-audit/SKILL.md      ← "audit portfolio" → 8-layer portfolio validation
├── .instructions/                     ← Detailed reference docs (load on demand)
│   ├── data-collection.md             ← MCP workflow, tools, required data
│   ├── report-layout.md               ← Section order, card splitting, layout rules
│   ├── styling.md                     ← CSS specs, theme, signals, PDF export
│   ├── analysis-methodology.md        ← Price targets, corridors, macro, competitive
│   ├── analysis-reference.md          ← Fundamental & technical analysis tables
│   ├── signal-contracts.md            ← Signal output schemas (SHORT_TERM, CCRLO, SIMULATION)
│   ├── tag-taxonomy.md                ← Tag classification taxonomy (5 dimensions, thresholds)
│   ├── short-term-strategy.md         ← Trend-break risk-off strategy specification
│   ├── long-term-strategy.md          ← CCRLO correction prediction specification
│   └── simulation-strategy.md         ← Event simulation regime + probability specification
├── .vscode/settings.json              ← VS Code agent & skills configuration
├── strategies/                        ← Research documents
│   ├── short-term/                    ← Short-horizon bearish trading research
│   └── long-term/                     ← Long-horizon investment research
├── templates/report-template.html      ← CSS/structure reference (copy CSS from here)
├── templates/portfolio-template.html  ← Portfolio dashboard HTML template
├── examples/                          ← Reference reports (read-only examples)
│   └── HOOD-analysis.html            ← Gold standard: Fintech/Digital, Python-computed signals
├── scripts/                           ← Python computation scripts (local compute)
│   ├── analyst_compute_engine.py     ← Unified pipeline: validate → compute → validate
│   ├── compute_short_term.py         ← TB/VS/VF + Fragility → SHORT_TERM_SIGNAL
│   ├── compute_ccrlo.py              ← CCRLO scoring → CCRLO_SIGNAL
│   ├── compute_simulation.py         ← Regime + Events → SIMULATION_SIGNAL
│   ├── compute_tags.py               ← Stock classification → TAG_SIGNAL (5 dimensions)
│   ├── validate_inputs.py            ← Data bundle validation (pre-computation gate)
│   ├── validate_outputs.py           ← Signal contract validation (post-computation gate)
│   ├── validate_numbers.py           ← Numerical accuracy audit (3-stage pipeline)
│   ├── run_tests.py                  ← Unified test runner (183 tests, 6 suites, live AV test)
│   ├── build_portfolio.py            ← Portfolio aggregation + HTML generation
│   ├── audit_portfolio.py            ← Portfolio 8-layer audit script
│   ├── portfolio_optimizer.py        ← Evidence-based portfolio construction engine
│   └── tests/                        ← Test framework (unit, contract, regression, integration)
│       ├── fixtures.py               ← Shared fixtures (MINIMAL_BUNDLE, DISTRESSED_BUNDLE)
│       ├── test_unit_short_term.py   ← Unit tests: Short-term signals
│       ├── test_unit_ccrlo.py        ← Unit tests: CCRLO scoring
│       ├── test_unit_simulation.py   ← Unit tests: Simulation signals
│       ├── test_unit_tags.py         ← Unit tests: Tag classification
│       ├── test_contracts.py         ← Contract schema + regression tests
│       ├── test_integration.py       ← Full pipeline + cross-module tests
│       └── golden/                   ← Golden reference snapshots
├── portfolio-manager/                 ← Portfolio dashboard system
│   ├── portfolio.html                ← Generated portfolio dashboard page
│   └── portfolio-management-research.md ← Portfolio construction research
└── reports/                           ← Generated output (agent saves new reports here)
```

## How to Use This Structure
1. **This file** is auto-loaded. It has the essential rules for every task.
2. **For report generation**: Read `templates/report-template.html` for CSS, then read `examples/HOOD-analysis.html` for structure reference (primary gold standard).
3. **For data collection**: The data-collection skill (`.github/skills/data-collection/SKILL.md`) defines the standard Data Bundle all skills consume.
4. **For signal output format**: `.instructions/signal-contracts.md` defines the output schemas (SHORT_TERM_SIGNAL, CCRLO_SIGNAL, SIMULATION_SIGNAL) that all signal skills produce.
5. **For detailed specs**: Read the relevant `.instructions/` file:
   - Data collection questions → `.instructions/data-collection.md`
   - Section order / layout → `.instructions/report-layout.md`
   - CSS / styling / PDF → `.instructions/styling.md`
   - Price targets / macro / competitive → `.instructions/analysis-methodology.md`
   - Fundamental / technical analysis → `.instructions/analysis-reference.md`
   - Signal output schemas → `.instructions/signal-contracts.md`
   - Short-term signals / trend-break → `.instructions/short-term-strategy.md`
   - Long-term correction prediction → `.instructions/long-term-strategy.md`
   - Event simulation / regime / scenarios → `.instructions/simulation-strategy.md`
6. **For short-term signals**: Say "short-term signal for [TICKER]" — triggers the short-term-analysis skill
7. **For correction risk**: Say "correction risk for [TICKER]" — triggers the long-term-prediction skill
8. **For event simulation**: Say "simulate events for [TICKER]" — triggers the simulation skill
9. **For numerical validation**: Say "validate numbers for [TICKER]" — triggers the numerical-audit skill
10. **New reports** go into `reports/[TICKER]-analysis.html`
11. **For testing**: Say "run tests" or "verify changes" → triggers the system-test skill via @test-engineer agent
12. **Phase Gate Protocol**: Both agents (stock-analyst, test-engineer) must print structured gate checklists at each phase boundary. If any item shows ❌, the agent must fix before advancing. See the agent `.md` files for gate definitions.

## Python Computation Pipeline (CRITICAL)
All signal computations (SHORT_TERM, CCRLO, SIMULATION, TAGS) MUST be executed via Python scripts
in `scripts/`, NOT computed inline by the AI agent. The agent must:
1. Collect data via MCP and write a structured JSON data bundle to `scripts/data/[TICKER]_bundle.json`
2. Run the unified engine: `python scripts/analyst_compute_engine.py --ticker [TICKER]`
   - **Phase 0**: Pre-flight integrity check (runs 135 quick tests automatically — aborts if any fail)
   - Phase 1: Validates inputs (data completeness, ranges, freshness)
   - Phase 2: Computes all 4 signals (SHORT_TERM → CCRLO → SIMULATION → TAGS)
   - Phase 3: Validates outputs (contracts, bounds, cross-signal consistency)
   - Exit code 0 = success, 1 = input validation failed, 2 = computation error, 3 = output validation failed, 4 = pre-flight integrity check failed
   - Use `--no-verify` to skip pre-flight (not recommended — only for re-runs after confirmed fix)
3. Read the output signal JSONs from `scripts/output/[TICKER]_*.json` and use them directly in report generation
- **Never recompute** signal values — always use Python-computed results
- **Never skip validation** — the engine validates both inputs and outputs automatically
- **Numerical audit**: Run `python scripts/validate_numbers.py --ticker [TICKER]` to verify numerical accuracy at any pipeline stage (A=data, B=signals, C=report)
- See `.github/skills/analyst-compute-engine/SKILL.md` for data bundle schema and full details
- See `.github/skills/numerical-audit/SKILL.md` for numerical accuracy validation

## MCP Data Collection Workflow
See `.github/skills/data-collection/SKILL.md` for the full standardized workflow.
Quick reference:
1. **List tools**: `TOOL_LIST` with category (e.g., `core_stock_apis`)
2. **Get schema**: `TOOL_GET` with tool name (e.g., `GLOBAL_QUOTE`)
3. **Call tool**: `TOOL_CALL` with `tool_name` and `arguments`
4. Always collect: GLOBAL_QUOTE, COMPANY_OVERVIEW, INCOME_STATEMENT, BALANCE_SHEET, CASH_FLOW, EARNINGS, RSI, MACD, BBANDS, SMA, EMA, ADX, ATR, NEWS_SENTIMENT, INSTITUTIONAL_HOLDINGS
5. For competitive landscape: fetch COMPANY_OVERVIEW + GLOBAL_QUOTE for 3-5 industry peers
6. For macro dashboard: fetch CPI, FEDERAL_FUNDS_RATE (≥12 monthly values), UNEMPLOYMENT, REAL_GDP
7. **Macro data depth**: `FEDERAL_FUNDS_RATE` must return ≥12 data points. Never store only 1 value — the Fed chart needs 12 months of actual data. If fewer than 12 are returned, re-fetch or flag as incomplete

## Report Section Order (STRICT — Importance-Based Top to Bottom)

**Philosophy**: "Inverted pyramid" structure prioritizes decision-critical content first:
Verdict → Price Outlook → Performance Benchmarking → External Validation → Fundamental Metrics → Technical Signals → Risk Factors → Supporting Context → Macro Backdrop

1. Export Bar — "Export to PDF" button (hidden in print)
2. Header — Ticker, company name, exchange, sector, price, change, OHLCV, date
3. Executive Summary & Analysis — MUST be on Page 1
4. Price Target Projections — Multi-year scenario table (SEPARATE CARD)
5. Expected Price Corridors & Correction Scenarios (SEPARATE CARD)
6. Scenario Assumptions & Revenue Projections (SEPARATE CARD)
7. **Performance vs. S&P 500 Benchmark** — Performance vs market (full width) with monthly chart, period returns, statistical analysis
8. **Analyst Consensus + Quarterly EPS Trajectory** — External validation (side by side)
    - **Analyst Consensus card (visual graph layout)**:
      - Centered hero block: large green target price (`font-size:1.4em; color:#16a34a`), subtitle "Mean Target Price (+X% upside)", analyst count + latest quarter
      - Visual `.rating-bar` showing proportional colored segments (Strong Buy/Buy/Hold/Sell)
      - Percentage breakdown text line below the bar (centered)
      - Green consensus box (`background:#f0fdf4; border:1px solid #bbf7d0`) with consensus label badge + summary text
      - **NO table-based breakdown** — use only the visual bar + text format
9. **Valuation Metrics + Financial Health** — Fundamental metrics (side by side)
10. **Financial Flow — Income Statement Breakdown** — Profit breakdown visualization (full width)
11. **Technical Indicators** — Price action signals dashboard (full width)
    - **3-row layout (STRICT order)**:
      - Row 1: RSI (14) + MACD + ADX (14) + ATR (14) — 4 tiles side by side
      - Row 2: Moving Averages table (with `<thead>`: Indicator/Value/vs Price) + Bollinger Bands **gradient bar visual** (not plain table) — side by side
      - Row 3: Trend-Break Status + Fragility Score + Market Regime + Event Risk (20d) — 4 signal tiles side by side
    - **Narrative analysis box** (REQUIRED): Below Row 3, add a styled box (`background:#f8fafc; border:1px solid #e8ecf3; border-radius:6px; padding:12px; margin-top:10px`) with:
      - Title: "Technical Analysis Summary" (`font-size:0.82em; font-weight:700; color:#1b2a4a`)
      - Body: 3-5 sentence narrative interpreting RSI zone, MACD momentum direction, distance from MAs, trend-break status, fragility assessment, and dominant regime implication
      - Use `<strong>` for key numerical values (RSI, MA distances, fragility score)
      - See HOOD gold standard Section 11 for reference
12. **Event Risk Simulation — 20-Day Forward Analysis** — Regime bars, event heatmap with price impact, scenario price targets (full width)
13. Recent News & Sentiment + Key Risks & Catalyst Factors (side by side)
14. Shares & Ownership — Institutional holdings, leadership, insider activity (full width)
15. US Economic Indicators — Macro Dashboard (full width)
16. Global Market Indicators + Macro-Equity Correlation Analysis (side by side)
17. Competitive Landscape — [Industry] Peers (full width)
18. Net Macro Environment Scorecard (full width)
19. Disclaimer
20. Timestamp

### Canonical Section `<h2>` Titles (MUST match exactly)
These are the exact `<h2>` titles from the HOOD gold standard. Every report must use these exact names:
```
 S3:  Executive Summary & Analysis
 S4:  Price Target Projections — Multi-Year Scenario Analysis
 S5:  Expected Price Corridors & Correction Scenarios
 S6:  Scenario Assumptions & Revenue Projections
 S7:  Performance vs. S&P 500 Benchmark
 S8a: Analyst Consensus
 S8b: Quarterly EPS Trajectory
 S9a: Valuation Metrics
 S9b: Financial Health
 S10: Financial Flow — Income Statement Breakdown (FY[YEAR])
 S11: Technical Indicators
 S12: Event Risk Simulation — 20-Day Forward Analysis
 S13a: Recent News & Sentiment
 S13b: Key Risks & Catalyst Factors
 S14: Shares & Ownership
 S15: US Economic Indicators — Macro Dashboard
 S16a: Global Market Indicators
 S16b: Macro-Equity Correlation Analysis
 S17: Competitive Landscape — [Industry] Peers
 S18: Net Macro Environment Scorecard
```
- Section 10 uses the actual fiscal year (e.g., "FY2025")
- Section 17 uses the actual industry label (e.g., "Digital Brokerage & Fintech Peers")

## Short-Term Signal Integration (in every report)
- Compute TB (trend break), VS (volatility shift), VF (volume filter) from SMA/ATR/Volume data
- Compute Fragility Score (0-5): Leverage + Liquidity + Info Risk + Valuation + Momentum
- **Section 3 (Executive Summary)**: Show TB/VS/VF status + fragility score in Short-Term Outlook
- **Section 5 (Price Corridors)**: Adjust correction probabilities if fragility >= 3
- **Section 11 (Technical Indicators)**: Add Trend-Break Status and Fragility Score rows
- **Section 13 (Risks)**: Flag HIGH fragility dimensions as named risk factors
- See `.instructions/short-term-strategy.md` for full specification

## Card Splitting for PDF (CRITICAL)
- Never put too much content in a single card — max ~60% of landscape A4 page height
- Price Target section MUST be split into 3 separate cards
- Each card gets its own `<div class="card full-width">` with its own `<h2>`
- This ensures `page-break-inside: avoid` works correctly

## Benchmark Comparison Section (REQUIRED in every report)
- **Section 7** — Full-width card immediately after scenario assumptions
- **Dual SVG charts side by side**: 12-Month (monthly) + 5-Year (annual)
  - **Chart Y-axis**: Percentage return (%) from baseline date — NOT normalized index values. Y-axis shows labels like +200%, +100%, 0%, -50% etc. The 0% line is the baseline (starting point)
  - **12-Month chart**: TICKER vs S&P 500 cumulative % return from 12-months-ago baseline (13 data points over 12 months, monthly x-axis with 3-letter abbreviations: Mar'25, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec, Jan'26, Feb, Mar)
  - **5-Year chart**: TICKER vs S&P 500 cumulative % return from 5-year-ago baseline (5-6 data points, yearly x-axis). If ticker has <5 years of data (e.g., recent IPO), start from earliest available date and note it in the chart subtitle
  - **0% baseline line**: The grid line at 0% should use a slightly heavier stroke (`stroke-width: 1`) or solid style to visually anchor the baseline
- **Period returns table**: 1M, 3M, 6M, YTD, 1Y performance with outperformance/underperformance column
- **Statistical analysis table**: Beta (1Y), Correlation, Alpha (annualized), Sharpe Ratio, Max Drawdown
- **Analysis box**: Interpretation of relative performance, volatility amplification (via Beta), recent divergence patterns
- **Purpose**: Provides immediate context for readers — "Is TICKER outperforming or underperforming the market?"
- **Data source**: Historical price data from GLOBAL_QUOTE or TIME_SERIES_DAILY; S&P 500 data from macro indicators
- See examples/HOOD-analysis.html Section 7 for reference implementation

## Styling Rules (NON-NEGOTIABLE)
- Light theme: white cards (#fff), light gray bg (#f4f6f9), navy header (#1b2a4a)
- Colors: Green (#16a34a) bullish, Red (#dc2626) bearish, Amber (#d97706) neutral
- Signal badges: `.signal.bullish`, `.signal.bearish`, `.signal.neutral`
- **Signal badge length**: Max 3-5 words. Longer explanations use `.signal-desc` on next line
- Fonts: Segoe UI, 13px base
- Bullet points: CSS `::before` with unicode `\25B8` — NEVER use HTML entities like `&#9656;`
- **Never write `\u25B8` as literal text** — this is a JavaScript escape, not valid HTML. Use CSS `::before` for standard bullets, or `&#x25B8;` only when colored per-item bullets are needed (e.g., scenario assumption boxes)
- Use flexbox layout (NOT CSS Grid) for all layouts
- Do NOT use absolute positioning for Support & Resistance levels — use flexbox columns
- **Support & Resistance layout**: Use colored pill badges (NOT text lists). Support = green badges (`background:#d4edda; color:#155724`), Resistance = red/pink badges (`background:#f8d7da; color:#721c24`). Format: `$PRICE (Label)` inside each badge. See HOOD gold standard Section 5
- RSI Gauge: Must include Oversold/Overbought labels + zone markers at 30/50/70

## PDF Export Rules
- `@page { size: A4 landscape; margin: 12mm; }`
- `-webkit-print-color-adjust: exact; print-color-adjust: exact;` on body
- `page-break-inside: avoid; break-inside: avoid;` on all cards and summary boxes
- `@media print` block: hide export bar, remove shadows, white background
- **Disable animations in print**: Income Statement Breakdown flow-in, corridor line draw — set `animation: none`
- **Show all labels in print**: Corridor hover labels always visible (`opacity: 1`)
- Export button: set `document.title` before `window.print()`, **restore original title after** — pattern: `const origTitle = document.title; document.title = ...; window.print(); document.title = origTitle;`

## SVG Price Corridor Chart
- **Enhanced interactive** with animated line drawing, hover data points, gradient fills, end badges
- ViewBox: `viewBox="0 0 600 200"` (wider for room)
- 3 polylines (Bullish/Average/Conservative) with colored corridor gradient polygons
- Interactive data points: each `<circle>` + `<text>` wrapped in `<g class="corridor-g">` for hover
- End badges: colored pill shapes at line endpoints showing final target price
- Red dashed lines with circle markers for correction dip zones
- Legend bar below SVG with all scenario colors + dip markers
- Y-axis grid lines with price labels; X-axis year labels
- Correction Risk table: Mild (-10-15%), Standard (-20-30%), Severe (-40-50%), Black Swan (-60%+)
- **Correction Risk table columns** (STRICT): Scenario | Drawdown | Price Floor | **12-Month Probability** | **Trigger**. Probability uses nested `<div>` bars. Never use "Recovery Time" instead of "Trigger"
- See `.instructions/styling.md` for full CSS and SVG structure

## Monthly Price Forecast (REQUIRED in every report)
- **Location**: Inside Section 5 (Price Corridors), after the corridor chart and before the correction risk table
- **Structure**: Table with columns: Month | Actual | Model Est. | Accuracy | Conservative | Average | Bullish | Key Catalyst
- **Past months** (Jan to current-1): Show actual closing price, model estimate, accuracy badge with color
- **Current month**: Highlighted row (`background:#eff6ff; border-left:3px solid #2563eb`)
- **Accuracy summary row**: Yellow background (`#fffbeb`), shows N-month backtest average accuracy
- **Future months**: Show Conservative/Average/Bullish price projections with % from current
- **December row**: Must EXACTLY match Section 4 year-end targets (critical consistency check)
- **Methodology note**: Below table, explain interpolation from current to Section 4 targets
- **Scenario path boxes**: Three colored boxes (red/blue/green) summarizing each path narrative
- **Accuracy formula**: `Accuracy = 100% - |error%|` where `error% = (Model_Est - Actual) / Actual * 100`
- **Color mapping**: >90% green, 85-90% amber, <85% red
- See `.instructions/analysis-methodology.md` for computation details

## Price Target Methodology
- Conservative: ~25-30% EPS CAGR, P/E 18-22x, macro headwinds
- Average: ~40-50% EPS CAGR, P/E 28-35x, analyst consensus extrapolated
- Bullish: ~60%+ EPS CAGR, P/E 40-50x, platform growth + index inclusion
- Always include disclaimer that projections are model-based estimates

## Scenario Assumptions & Revenue Projections (Section 6 — Format Rules)
- Revenue Projections table must have **4+ columns**: Metric | FY[YEAR] (Actual) | FY[YEAR]E Conservative | FY[YEAR]E Average | FY[YEAR]E Bullish
- **FY Actual column is required** — never omit the actual year's data
- Must include rows: Revenue, EPS, Implied P/E, Target Price
- Target Price row values MUST match Section 4 year-end targets exactly

## Valuation & Financial Health (Sections 9a/9b — Format Rules)
- Both tables use **2-column format** (Label | Value) matching report-template.html
- Do NOT add a 3rd column with signal badges — signal information goes inline in the value column
- Section 9a must include **Revenue Growth Journey (Revenue)** (`rev-chart` column bar visualization) OR **Profitability Journey (EPS)** (`rev-chart` column bars)
  - Structure: `<div class="rev-chart">` flex container with `rev-bar-wrap` > `rev-bar-val` > `rev-bar` > `rev-bar-label` children
  - Each bar: value label above, colored `<div>` with percentage height, year label below
  - Final bar uses green gradient: `linear-gradient(180deg, #16a34a, #15803d)`
  - Minimum 3 years of data required
  - **Never use `journey` pill-style layout** (`.journey-step` + `.journey-arrow`) — always use column bars
- Section 9b must include **Profitability Journey (Net Income)** using `rev-chart` column bar visualization
  - Negative income years: red gradient bars (`linear-gradient(180deg, #ef4444, #b91c1c)` with `border-radius:0 0 3px 3px`)
  - Positive income years: blue gradient bars (standard `rev-bar`)
  - Final positive bar: green gradient
  - Minimum 3 years of data required
  - **Never use `journey` pill-style layout** — always use column bars

## Revenue Chart & Financial Journey
- **Always use `rev-chart` column bar visualization** — never use `journey` pill-style layout
- `rev-chart` structure: `<div class="rev-chart">` with `rev-bar-wrap` > `rev-bar-val` > `rev-bar` (height %) > `rev-bar-label`
- Use "Revenue Growth Journey (Revenue)" for post-IPO or hypergrowth companies (CHYM, HOOD) — include Operating CF trend below
- Use "Profitability Journey (EPS)" for mature profitable companies with dramatic EPS turnaround (AMZN, ASML)
- Use "Profitability Journey (Net Income)" in S9b Financial Health for all companies
- **Always include the metric in parentheses** in chart titles: (Revenue), (EPS), or (Net Income)
- Negative values: red gradient bars (`linear-gradient(180deg, #ef4444, #b91c1c)`) with `border-radius:0 0 3px 3px`
- Final bar in chart uses green gradient: `linear-gradient(180deg, #16a34a, #15803d)`
- Minimum 3 years of historical data required

## Financial Flow — Income Statement Breakdown Diagram
- Full-width card below Valuation + Financial Health side-by-side cards
- **Enhanced interactive** with gradient flow bands, hover glow, flow-in animation, stage headers, legend
- Inline SVG with cubic bezier `<path>` flow bands, viewBox `0 0 900 280`
- 5 stages: Revenue Sources → Total Revenue → COGS + Gross Profit → OpEx + Operating Income → Expense Detail + Net Income
- Data from `INCOME_STATEMENT` (most recent annual)
- Band width proportional to dollar amounts; labels show $amount and percentage
- **Gradient fills**: Each flow band uses `<linearGradient>` (source color → target color)
- **Stage headers**: `.sankey-stage-label` text above each column
- **Legend bar**: Colored swatches below SVG identifying each node type
- **Margin callout boxes**: Gross Margin and Net Margin boxes in top-right of SVG
- **Tooltips**: `<title>` inside each `<path>` shows "Source → Target: $XX (XX%)"
- Colors: Blue (revenue), Teal (gross profit), Amber (COGS), Green (operating/net income), Red (expenses/loss)
- For companies without revenue segmentation, use simplified 4-stage flow
- **Narrative analysis box**: Below the legend, add a styled analysis box (`background:#f8fafc; border:1px solid #e8ecf3; border-radius:6px; padding:12px; margin-top:10px`) with:
  - Title: "Income Statement Analysis" (`font-size:0.82em; font-weight:700; color:#1b2a4a`)
  - Body: 3-5 sentence narrative interpreting the breakdown numbers — highlight gross margin, operating margin, net margin, dominant expense categories, year-over-year trends, and what the cost structure reveals about the business model
  - Use `<strong style="color:#16a34a;">` for key margin figures
  - See HOOD gold standard Section 10 for reference
- See `.instructions/styling.md` for CSS and `.instructions/analysis-methodology.md` for data extraction

## Post-IPO & Small-Cap Adjustments
- Add asterisk footnotes when SBC >20% of loss, restructuring >$50M, or one-time costs distort GAAP
- Show Operating CF journey for companies with negative income but positive cash flow
- Analyst consensus with <15 analysts: widen conviction bands in price projections
- Highlight valuation discount vs mature peers in Key Takeaway box

## Competitive Landscape — Peer Selection
- Select 3-5 peers by: industry/subsector, market cap proximity (0.5x-3x), strategic relevance
- Subject company row: `background:#eff6ff;` (light blue highlight)
- **Peer table columns** (STRICT 10 columns): Company | Price | Mkt Cap | Revenue | Rev Growth | **Gross Margin** | P/E | P/S | EV/Rev | Analyst. Never use "Margin" instead of "Gross Margin"
- Positioning Map uses 6 fixed dimensions with `.signal` badges for scoring
- Always end with a styled Key Takeaway box (`background:#fffbeb; border:1px solid #fde68a`)

## Fed Funds Rate Chart (CRITICAL — Data Integrity)
- **Data source**: Fetch from Alpha Vantage `FEDERAL_FUNDS_RATE` — last 12 months only
- **Data depth**: Must have ≥12 monthly data points from the API response. **NEVER use only 1 data point** and interpolate/estimate the rest
- **Exactly 12 bars** — one per month, NO prediction/forecast column
- **Only use actual API-returned values** — never fabricate, estimate, or interpolate rate values. If the API returns fewer than 12 months, use only what is available and note the gap
- Color mapping: 4%+ Red, 3.5-4% Orange, 3-3.5% Amber, <3% Green
- **Use fixed pixel heights** (e.g., `height:50px`, `height:45px`) — NEVER percentage heights (`height:90%`) which collapse in flex containers
- Bar column structure: Each bar column uses `flex:1` to spread equally across the container width. Bar div inside uses `width:30px`. **Never use `min-width:40px`** — this causes bars to bunch to the left instead of spreading evenly
- **Bar order**: Oldest month on the left, newest on the right (chronological left-to-right)
- **Rate label format**: Each bar's rate label MUST include the `%` suffix (e.g., `4.33%`, NOT bare `4.33`). The Stage C validator parses `X.XX%</div>` to extract rates
- Height calculation: tallest bar ~80px, scale others proportionally
- Title: "Federal Funds Rate — Last 12 Months"
- State total bps change and link to stock's valuation thesis
- **Narrative analysis box** (REQUIRED): Below the Fed chart analysis line, add a styled box (`background:#f8fafc; border:1px solid #e8ecf3; border-radius:6px; padding:12px; margin-top:10px`) with:
  - Title: "Macro Environment Analysis" (`font-size:0.82em; font-weight:700; color:#1b2a4a`)
  - Body: 3-5 sentence narrative interpreting GDP growth impact, Fed policy direction and its dual effects (valuation vs income), CPI/inflation trajectory, employment stability, and the net macro signal (favorable/neutral/headwind) for the specific ticker
  - Use `<strong style="color:#16a34a;">` for positive macro figures, `<strong style="color:#d97706;">` for cautionary ones
  - See HOOD gold standard Section 15 for reference
- **Cross-report consistency**: Fed chart values must be identical across all reports generated in the same session (macro data is market-wide)

## Macro Sensitivity Rubric
- HIGH (+/-): 5-15% stock impact (e.g., rate cuts → growth stocks)
- MEDIUM (+/-): 2-5% stock impact
- LOW/INDIRECT: <2% or indirect
- Score each factor independently; ensure Net Assessment is balanced (TAILWIND/NEUTRAL/HEADWIND)
- **Macro value format** (STRICT): GDP = dollar value ("$6,125.9B"), CPI = index value ("326.79"), Unemployment = percentage ("4.4%"), FFR = percentage ("3.64%"). Must match HOOD gold standard format and values exactly across all reports

## News & Sentiment
- Include 3-5 items, prioritize last 3-7 days
- Use Alpha Vantage `overall_sentiment_label` for badge assignment
- Every news item MUST have hyperlink to original article

## Analyst Consensus Section (Section 8a — Visual Graph Layout)
- **Layout**: Centered hero block, NOT a table
- **Structure** (top to bottom):
  1. **Target price hero**: `<div style="font-size:1.4em; font-weight:700; color:#16a34a;">$XXX.XX</div>` — large, centered, green
  2. **Subtitle**: "Mean Target Price (+XX.X% upside)" in `color:#5a6577`
  3. **Analyst count**: "XX Analysts • Latest Quarter: [Quarter Year]" in `color:#8a94a6`
  4. **Rating bar**: `.rating-bar` with `.rb-strong-buy`, `.rb-buy`, `.rb-hold`, `.rb-sell` segments. Width proportional to percentage. **Labels must show count + abbreviation** (e.g., "15 SB", "48 Buy", "3 Hold", "2 Sell"). Never show just a number. Omit sell segment if 0 analysts
  5. **Percentage text**: Single centered line: "Strong Buy: XX.X% • Buy: XX.X% • Hold: XX.X% • Sell: XX.X%"
  6. **Consensus box**: `background:#f0fdf4; border:1px solid #bbf7d0` with `<strong>Consensus:</strong>` + `.signal.strong-buy` / `.signal.bullish` badge + summary text (e.g., "94% Buy+Strong Buy. Zero sell ratings...")
- **Consensus badge mapping**: >80% Buy+SB → STRONG BUY (`.signal.strong-buy`), >60% → BUY (`.signal.bullish`), >50% → HOLD (`.signal.neutral`), <50% → SELL (`.signal.bearish`)
- **Never use a table** for the rating breakdown — the visual bar replaces it

## Analyst Target Price
- Use mean from `COMPANY_OVERVIEW.AnalystTargetPrice`
- Note staleness if >3 months old
- Use 12-month target as basis for Average scenario Year 1 projection
- Note wide dispersion if range exceeds 3x spread

## SVG Price Corridor Chart — Details
- ViewBox: `viewBox="0 0 600 200"` (enhanced wider format)
- Polygon order: corridor gradient fills FIRST, then polylines on top
- Correction probability base: Mild 85-95%, Standard 55-70%, Severe 25-40%, Black Swan 8-15%
- Adjust +5-10% for high Beta (>1.5) or recent IPO (<2yr)
- Adjust +5-10% if Fragility Score >= 3 (from short-term signals)

## Long-Term Signal Integration (CCRLO — in every report)
- Compute CCRLO score (0-21) from 7 macro-financial features
- Score 0-3: 5-10% (LOW), 4-7: 15-25% (MODERATE), 8-11: 30-45% (ELEVATED), 12-15: 50-65% (HIGH), 16-21: 70-85% (VERY HIGH)
- **Section 3 (Executive Summary)**: Show CCRLO score + 6-month correction probability in Long-Term Outlook
- **Section 5 (Price Corridors)**: Calibrate corridor width by risk level
- **Section 18 (Scorecard)**: Add CCRLO as composite risk tile (color by risk level)
- See `.instructions/long-term-strategy.md` for full specification

## Event Risk Simulation Integration (in every report)
- Compute market regime (Calm/Trending/Stressed/Crash-Prone) from RSI, ADX, ATR, MACD, SMA, volume
- Score 6 event probabilities at 5d/10d/20d horizons: Large Move, Vol Spike, Trend Reversal, Earnings Reaction, Liquidity Stress, Crash-Like Path
- Weight 4 forward scenarios: Base Case, Vol Expansion, Trend Shift, Tail Risk
- Compute model disagreement score and confidence assessment
- Uses TB/VS/VF Fragility Score and CCRLO as inputs (does not replace them)
- **Section 3 (Executive Summary)**: Show dominant regime badge + top event probability
- **Section 5 (Price Corridors)**: Use scenario weights to calibrate correction probabilities
- **Section 11 (Technical Indicators)**: Add Market Regime row and Event Risk (20d) row
- **Section 13 (Risks)**: Add scenario-derived risk narratives if weight > threshold
- **Section 18 (Scorecard)**: Add Event Risk tile (GREEN <15%, AMBER 15-30%, RED >30%)
- See `.instructions/simulation-strategy.md` for full specification

## Shares & Ownership Section (Section 14 — full-width)
- Now a standalone full-width section (previously paired with Technical Indicators)
- **Horizontal layout** with 3 sections side by side:
  1. Left: Ownership statistics table (Shares Outstanding, Float, Institutional %, Insider %)
  2. Center: C-Suite Leadership table (8 executives with titles: CEO, President, CFO, CPO, CRO, CProdO, CLO, CTO)
  3. Right: Recent Insider Transactions (Name, Title, Type, Shares, Price, Date, **Avg Value**, Ownership Change %)
- **Avg Value column**: Calculate as Shares × Average Price (midpoint if range). Format as $XXK or $XX.XM
- **Data sources**: COMPANY_OVERVIEW for ownership stats, INSIDER_TRANSACTIONS for trades
- **Leadership data**: Extract from Alpha Vantage COMPANY_OVERVIEW or manual research
- **Narrative analysis box** (REQUIRED): Below the ownership/transactions flex container, add a styled box (`background:#f8fafc; border:1px solid #e8ecf3; border-radius:6px; padding:12px; margin-top:10px`) with:
  - Title: "Ownership & Insider Activity Analysis" (`font-size:0.82em; font-weight:700; color:#1b2a4a`)
  - Body: 3-5 sentence narrative interpreting institutional vs insider ownership balance, insider selling patterns (routine 10b5-1 vs conviction-driven), founder alignment, float liquidity, and what the ownership structure signals about investor confidence
  - Use `<strong style="color:#1b2a4a;">` for key ownership percentages
  - See HOOD gold standard Section 14 for reference
- See examples/HOOD-analysis.html Section 14 for reference implementation

## Multi-Ticker Sequential Processing (CRITICAL)
When multiple tickers are requested for analysis (e.g., "analyze AMZN, NVDA, and MSFT"):
- **Complete each ticker fully** before starting the next — all 5 phases (Data Collection → Signal Computation → HTML Generation → Save → Post-Gen Audit) must finish for ticker N before Phase 1 begins for ticker N+1
- **Never interleave** data collection or report generation across tickers
- **Report progress** after each ticker completes (e.g., "✅ AMZN complete (1/3). Starting NVDA...")
- **Independent failures** — if one ticker fails (e.g., MCP rate limit, missing data), log the failure, skip that ticker, and continue with the next. Summarize all failures at the end
- **Shared reference loading** — templates, CSS, and `.instructions/` files only need to be loaded once for the first ticker and reused for subsequent tickers
- **Macro data reuse** — CPI, FEDERAL_FUNDS_RATE, UNEMPLOYMENT, REAL_GDP are market-wide; fetch once with the first ticker and reuse for all subsequent tickers in the same session
- **Macro data integrity** — All macro values (CPI, FFR, Unemployment, GDP) must be identical across all reports. Never fabricate or interpolate macro data. The Fed Funds Rate chart must use only actual API-returned values (≥12 monthly data points)

## Analysis Principles
- Never rely on a single indicator — combine technical + fundamental + sentiment
- Short-term = probabilistic (risk/reward ratios)
- Long-term = conviction-based (buy businesses, not tickers)
- Always define stop-loss and position sizing context
- Alpha Vantage free tier = 15-min delayed data

## Narrative Integrity Rules (ALL narrative analysis boxes)
- **Standalone per ticker**: Every narrative must be self-contained for the current ticker. NEVER reference other tickers, companies, or reports (e.g., "Unlike HOOD..." or "vs. MSFT's margins" is FORBIDDEN in narrative boxes)
- **Use numerical metrics**: Ground every claim in actual data from the report — cite specific dollar amounts, percentages, ratios, and growth rates. Never make qualitative claims without supporting numbers
- **No fabrication**: Only use data that appears elsewhere in the same report or was fetched from Alpha Vantage. Do not invent, estimate, or hallucinate figures not present in the data
- **Ticker-specific impact**: When describing macro factors, explain the impact mechanism specific to THIS company's business model (e.g., "rate cuts expand AMZN's 29.3x P/E multiple" not just "rate cuts help growth stocks")
- **Applies to all narrative boxes**: S10 Income Statement Analysis, S11 Technical Analysis Summary, S14 Ownership & Insider Activity Analysis, S15 Macro Environment Analysis

### Complete Narrative & Analysis Box Inventory (7 total across 20 sections)
Every report must contain these 7 interpretive elements — no more, no less:

| Section | Box Title | Type | Cross-ticker allowed? |
|---|---|---|---|
| S7 | Benchmark Analysis | Pre-built | Yes (vs S&P 500 only) |
| S10 | Income Statement Analysis | Narrative | No |
| S11 | Technical Analysis Summary | Narrative | No |
| S14 | Ownership & Insider Activity Analysis | Narrative | No |
| S15 | Macro Environment Analysis | Narrative | No |
| S17 | Key Takeaway | Pre-built | Yes (vs peers in table) |
| S18 | Net Assessment | Pre-built | No |

- **Narrative boxes** (S10, S11, S14, S15): Styled `background:#f8fafc; border:1px solid #e8ecf3; border-radius:6px; padding:12px; margin-top:10px` with bold title (`font-size:0.82em; font-weight:700; color:#1b2a4a`) + 3-5 sentence body
- **Pre-built boxes** (S7, S17, S18): Use their own established styling (S7 same as narrative, S17 yellow `#fffbeb`, S18 blue `#eff6ff`) but follow the same data-grounded + no-fabrication rules
- **No additional narratives** should be added to other sections — side-by-side cards (S8, S9, S13, S16) have card height limits, and remaining sections have built-in interpretive text already

## Change Verification Protocol (MANDATORY — ALL AGENTS)

This is a **non-negotiable system-level rule**. Every agent (stock-analyst, test-engineer, or
default Copilot) must follow this protocol whenever modifying any system file.

### What Counts as a System Change
Any edit to files in `scripts/` that affect computation logic, validation rules,
signal contracts, data bundle schema, or test infrastructure. Specifically:
- `compute_short_term.py`, `compute_ccrlo.py`, `compute_simulation.py`
- `validate_inputs.py`, `validate_outputs.py`, `validate_numbers.py`
- `analyst_compute_engine.py`
- `tests/fixtures.py` (test fixtures)
- `.instructions/signal-contracts.md` (schema definitions)

### After Every System Change — 3 Mandatory Steps

**Step 1: Propagate** — Identify and update ALL files affected by the change:
- If a signal output field is renamed/added/removed → update: compute script, validate_outputs.py, validate_numbers.py, signal-contracts.md, test fixtures, contract tests, the agent.md references
- If a formula changes → update: compute script, golden references, test expectations
- If a data bundle field changes → update: validate_inputs.py, test fixtures, data-collection skill
- If a validation rule changes → update: validator script, test expectations
- **Never leave related files out of sync** — a change is incomplete until all dependents are updated

**Step 2: Test** — Run the automated test suite:
```bash
python scripts/run_tests.py --suite quick    # Fast pass: unit + contract (135 tests, <0.2s)
python scripts/run_tests.py --suite all      # Full pass: + integration + docs (183 tests, <0.5s)
```
- If tests **FAIL** → fix the issue before proceeding. Do NOT skip failing tests.
- If tests fail because of an **intentional** algorithm change → update golden refs:
  ```bash
  python scripts/run_tests.py --golden all
  python scripts/run_tests.py --suite all    # Verify after update
  ```

**Step 3: Confirm** — Report the test results to the user:
- "183/183 tests pass" → change is complete
- "N tests failed" → show which tests and why, fix before declaring done

### Change Impact Quick Reference
| File Changed | Must Also Update | Test Suite |
|---|---|---|
| `compute_short_term.py` | golden refs, fixtures if schema changed | `all` |
| `compute_ccrlo.py` | golden refs, fixtures if schema changed | `all` |
| `compute_simulation.py` | golden refs, fixtures if schema changed | `all` |
| `validate_inputs.py` | fixtures if new checks added | `integration` |
| `validate_outputs.py` | contract tests if new checks | `integration` |
| `validate_numbers.py` | — | manual: `--ticker AMZN --stage B` |
| `analyst_compute_engine.py` | — | `integration` |
| `signal-contracts.md` | validate_outputs.py, contract tests | `contract` |
| `tests/fixtures.py` | golden refs | `all` + `--golden all` |
| Data bundle schema | validate_inputs.py, fixtures, data-collection skill | `all` |

### Test Infrastructure Location
```
scripts/
├── run_tests.py                    ← Unified test runner CLI (suites + live AV test)
└── tests/
    ├── fixtures.py                 ← MINIMAL_BUNDLE + DISTRESSED_BUNDLE fixtures
    ├── test_unit_short_term.py     ← Unit tests: TB/VS/VF/Fragility (26 tests)
    ├── test_unit_ccrlo.py          ← Unit tests: CCRLO features/scoring (22 tests)
    ├── test_unit_simulation.py     ← Unit tests: regime/events/scenarios (20 tests)
    ├── test_unit_tags.py           ← Unit tests: Tag classification (45 tests)
    ├── test_contracts.py           ← Schema contracts + regression (22 tests)
    ├── test_integration.py         ← Pipeline E2E + cross-module (12 tests)
    ├── test_docs_consistency.py    ← Architecture & documentation integrity (36 tests)
    └── golden/                     ← Golden reference snapshots (*.golden.json)
```

## Always Fetch Fresh Data Policy (CRITICAL — NON-NEGOTIABLE)
Every analysis request — whether it's the first time or a re-analysis — **MUST fetch fresh data
from Alpha Vantage MCP**. Never reuse, skip, or rely on existing data bundles from previous runs.

**Rules**:
- **Always fetch**: Every `analyze [TICKER]` request triggers a full Alpha Vantage data collection pass (all 15 subject data points + peers + macro). No exceptions.
- **Never reuse old bundles**: Even if `scripts/data/[TICKER]_bundle.json` already exists with recent data, fetch everything fresh. Market data changes constantly; stale data produces misleading reports.
- **Never skip data collection**: The existence of prior reports, bundles, signal outputs, or validation files does NOT justify skipping the fetch phase. Always start from Phase 1 (Data Collection).
- **Overwrite all artifacts**: Fresh data overwrites all existing files:
  - `reports/[TICKER]-analysis.html` — new report replaces old
  - `scripts/data/[TICKER]_bundle.json` — fresh MCP data replaces old bundle
  - `scripts/output/[TICKER]_*.json` — fresh signals replace old outputs
  - `scripts/data/[TICKER]_input_validation.json` — fresh validation replaces old
- **No confirmation needed** — overwriting is the default behavior. The user expects current market data every time.
- **Rationale**: Stock prices, financial statements, analyst ratings, sentiment, and macro indicators change continuously. A report built on stale data is worse than no report.

## File Naming
- Reports: `reports/[TICKER]-analysis.html`
- Portfolio: `portfolio-manager/portfolio.html`
- Always use `templates/report-template.html` as CSS/structure reference
- Reference `examples/HOOD-analysis.html` as the primary gold standard
- Agent definition: `.github/agents/stock-analyst.agent.md`
- Test agent: `.github/agents/test-engineer.agent.md`
- Portfolio agent: `.github/agents/portfolio-manager.agent.md`
