# Report Layout & Section Order

## Section Order (STRICT — Importance-Based Top to Bottom)

**Total: 20 sections** (Export Bar through Timestamp). Every report MUST contain all 20.

**Philosophy**: "Inverted pyramid" structure prioritizes decision-critical content for professional readers who need immediate actionable intelligence:
**Verdict → Price Targets → Performance Benchmarks → External Validation → Fundamentals → Technical Signals → Risks → Supporting Context → Macro Backdrop**

Every report MUST follow this exact order. Do not skip or reorder sections.

1. **Export Bar** — "Export to PDF" button (hidden in print)
2. **Header** — Ticker, company name, exchange, sector, price, change, OHLCV, date
3. **Executive Summary & Analysis** — MUST be on Page 1 immediately after header
   - Short-Term Outlook (Days-Weeks): RSI, MACD, Bollinger, MA signals
     - **Include Trend-Break Status**: TB ✓/✗, VS ✓/✗, VF ✓/✗ with signal badge if ENTRY is active
     - **Include Fragility Score**: X/5 with interpretation (Low/Moderate/High)
   - Long-Term Outlook (Months-Years): Revenue, EPS trajectory, P/E, analyst target, moat
     - **Include CCRLO Score**: X/21 with risk level (LOW/MODERATE/ELEVATED/HIGH/VERY HIGH)
     - **Include 6-month correction probability** from CCRLO mapping
   - **Include Market Regime badge**: Dominant regime (Calm/Trending/Stressed/Crash-Prone) with probability
     - Color: Calm=green(.signal.bullish), Trending=amber(.signal.neutral), Stressed/Crash=red(.signal.bearish)
     - Include top event probability (e.g., "Vol Spike 20d: 30%") in Short-Term Outlook
   - **Signal badges**: Use short labels (3-5 words) + `.signal-desc` for explanations
4. **Price Target Projections** — Multi-year scenario table (SEPARATE CARD)
   - Three scenarios: Conservative, Average (Consensus), Bullish
   - Columns: Current, End of Year 1 (with months), End of Year 2, End of Year 3, End of Year 4
   - Include % upside from current price for each cell
5. **Expected Price Corridors & Correction Scenarios** — (SEPARATE CARD)
   - SVG price corridor chart showing Bullish / Average / Conservative paths over 4 years
     - **Enhanced interactive**: Animated line drawing, hover data points, gradient fills, end badges
     - ViewBox `viewBox="0 0 600 200"`, Y-axis grid with labels, X-axis year labels
     - Corridor gradient polygons FIRST, then polylines on top
   - Correction dip markers on the chart (red dots)
   - **Monthly Price Forecast Table (REQUIRED)**:
     - Columns: Month | Actual | Model Est. | Accuracy | Conservative | Average | Bullish | Key Catalyst
     - Past months: Actual closing + model estimate + accuracy badge (>90% green, 85-90% amber, <85% red)
     - Current month: Highlighted row (`background:#eff6ff; border-left:3px solid #2563eb`)
     - Accuracy summary row: Yellow (`#fffbeb`) with N-month backtest average accuracy
     - Future months: 3-scenario projections with % from current price
     - **December row MUST exactly match Section 4 year-end targets** (critical consistency)
     - Scenario path boxes: 3 colored boxes summarizing each path narrative
     - Methodology note: Interpolation method + recalibration description
   - Correction Risk Scenarios table: Mild Pullback, Standard Correction, Severe Drawdown, Black Swan
   - **Correction probabilities adjusted by fragility score** (if ≥3, increase probabilities per calibration table in `.instructions/short-term-strategy.md`)
   - Volatility Metrics tiles: Daily ATR, 52W Range, Beta
   - Key Support & Resistance Levels using **colored pill badges** (NOT text lists with colored headers):
     - Support: green badges (`background:#d4edda; color:#155724; padding:3px 8px; border-radius:3px; font-size:0.75em; font-weight:600`)
     - Resistance: red/pink badges (`background:#f8d7da; color:#721c24; padding:3px 8px; border-radius:3px; font-size:0.75em; font-weight:600`)
     - Format: `$PRICE (Description)` inside each badge, e.g. `$70.97 (BB Lower)`
     - Layout: Two flex containers side by side, flexbox columns (NOT absolute positioning)
   - Correction Probability bars: -10%, -20%, -30%, -50%+ with percentage fills
6. **Scenario Assumptions & Revenue Projections** — (SEPARATE CARD)
   - Three assumption description boxes (Conservative, Average, Bullish)
   - Underlying EPS/Revenue & P/E assumptions table
   - Methodology disclaimer note
7. **Performance vs. S&P 500 Benchmark** — Performance vs market baseline (full width)
   - **Dual SVG charts side by side** (flexbox layout):
     - **Y-axis**: Cumulative percentage return (%) from baseline — NOT normalized index values. Labels show +200%, +100%, 0%, -50% etc. The 0% line is the baseline
     - **12-Month chart (left)**: TICKER vs S&P 500 cumulative % return, monthly x-axis with 3-letter abbreviations (13 data points, e.g., Mar'25, Apr, May, ..., Jan'26, Feb, Mar)
     - **5-Year chart (right)**: TICKER vs S&P 500 cumulative % return, yearly x-axis (5-6 data points). If ticker has <5 years of data (e.g., recent IPO), start from the ticker's earliest available date and note the shorter history in the chart subtitle (e.g., "IPO Jul 2021, data from Aug 2021")
   - Period returns table: 1M, 3M, 6M, YTD, 1Y with outperformance column
   - Statistical analysis table: Beta (1Y), Correlation, Alpha (annualized), Sharpe Ratio, Max Drawdown
   - Benchmark analysis box: Interpretation of relative performance, volatility amplification, recent divergence
   - **Purpose**: Provides immediate context for TICKER's performance relative to broad market
8. **Analyst Consensus** + **Quarterly EPS/Revenue Chart** (side by side)
   - **Analyst Consensus card** (visual graph layout — NOT a table):
     - Centered hero block: large green target price, Mean Target Price subtitle, analyst count + latest quarter
     - Visual `.rating-bar` showing proportional colored segments (Strong Buy green / Buy light green / Hold amber / Sell orange)
     - Centered percentage breakdown text line below the bar
     - Green consensus box with signal badge + summary narrative
   - **Quarterly EPS card**:
     - EPS bar chart or Revenue bar chart showing trajectory (8 quarters)
     - Earnings surprise table (4 most recent quarters)
   - **Purpose**: External validation — what Wall Street thinks (mean target, rating distribution, earnings momentum)
9. **Valuation Metrics** + **Financial Health** (side by side)
   - Include Profitability/Revenue Journey visual (annual progression)
   - **Purpose**: Fundamental metrics — intrinsic value assessment
10. **Financial Flow — Income Statement Breakdown** (full width, separate card)
   - Full-width card (NOT embedded below side-by-side cards)
     - **Enhanced interactive** with gradient flow bands, hover glow, flow-in animation
     - SVG flow chart showing: Revenue Sources → Total Revenue → COGS vs Gross Profit → Operating Expenses vs Operating Income → Expense Categories + Net Income
     - Data sourced from `INCOME_STATEMENT` (annual, most recent fiscal year)
     - Band width = proportional to dollar amount
     - **Gradient fills**: Each flow band uses `<linearGradient>` (source color → target color)
     - **Stage headers**: `.sankey-stage-label` text above each column
     - **Legend bar**: Colored swatches below SVG identifying each node type
     - **Margin callout boxes**: Gross Margin and Net Margin in top-right of SVG
     - **Tooltips**: `<title>` inside each `<path>` shows "Source → Target: $XX (XX%)"
     - Color scheme: Revenue/income nodes in blue (#2563eb), expense nodes in red/amber, profit node in green (#16a34a)
     - Must include dollar amounts and percentages on each flow band
   - **Narrative analysis box** below the legend:
     - Styled box: `background:#f8fafc; border:1px solid #e8ecf3; border-radius:6px; padding:12px; margin-top:10px`
     - Title: "Income Statement Analysis" (bold, 0.82em)
     - Body: 3-5 sentence narrative interpreting the breakdown — gross margin quality, dominant expense categories, operating leverage, net margin trend, what cost structure reveals about the business model
     - Use `<strong style="color:#16a34a;">` to highlight key margin percentages
   - **Purpose**: How does the business generate and retain profit? (unit economics)
     - Use inline SVG with `<path>` cubic bezier curves for flow bands
     - Keep chart height reasonable (~250-300px) for PDF compatibility
   - **Purpose**: Visual income statement flow from revenue to net income
11. **Technical Indicators** (full width)
   - Dashboard layout with 3 rows (STRICT order — see report-template.html Section 11):
     1. **Row 1 — Indicator Tiles**: RSI (14), MACD, ADX (14), ATR (14) — 4 tiles side by side using flexbox (`flex:1; min-width:200px`)
     2. **Row 2 — Moving Averages + Bollinger Bands**: Moving Averages table with `<thead>` (Indicator/Value/vs Price columns, rows: 50-MA, 200-MA, EMA12, EMA26, `flex:2`) + Bollinger Bands **gradient bar visual** with price position marker (NOT a plain table, `flex:1`)
     3. **Row 3 — Signal Status Tiles**: Trend-Break Status, Fragility Score, Market Regime, Event Risk (20d) — 4 tiles side by side using flexbox
   - **Include Trend-Break Status tile**: TB ✓/✗, VS ✓/✗, VF ✓/✗ with NO ENTRY/ENTRY status (border-left colored by status)
   - **Include Fragility Score tile**: X/5 with color by level (green 0-1, amber 2-3, red 4-5)
   - **Include Market Regime tile**: Dominant regime name + `.regime-bar` probability breakdown
   - **Include Event Risk (20d) tile**: Top 3 event probabilities with signal badges
   - **Narrative analysis box** (REQUIRED) below Row 3:
     - Styled box: `background:#f8fafc; border:1px solid #e8ecf3; border-radius:6px; padding:12px; margin-top:10px`
     - Title: "Technical Analysis Summary" (bold, 0.82em)
     - Body: 3-5 sentences interpreting RSI zone, MACD direction, MA distance, trend-break status, fragility, and regime implication
   - **Purpose**: Price action signals and momentum indicators for tactical timing
12. **Event Risk Simulation Visualization** (full width)
   - Full-width card with two-panel layout using `.sim-grid`:
   - **Left panel** (`.sim-panel`):
     - `<h3>Regime Detection</h3>` + description text
     - **4 regime probability rows** in order: Calm (green), Trending (blue), Stressed (amber), Crash-Prone (red) — ALL 4 REQUIRED even if 0%
     - **4 regime explanation boxes** in order: Calm (`#f0fdf4`), Trending (`#eff6ff`), Stressed (`#fffbeb`), Crash-Prone (`#fef2f2`) — ALL 4 REQUIRED
     - `<h3>Scenario Price Targets</h3>` table (Scenario | Weight | Price Range | Expected P/L) with exactly 4 rows: Base Case, Vol Expansion, Trend Shift, Tail Risk — all cells must have data or "N/A"
     - **Weighted Expected Price** callout box (`#f0fdf4`) with: dollar amount + % change, 80% Confidence range, Downside Skew %
   - **Right panel** (`.sim-panel`):
     - `<h3>Event Probability & Price Impact Heatmap</h3>`
     - Heatmap table (Event | 5d | 10d | 20d | Price Impact) with exactly 6 rows in order: Large Move, Vol Spike, Trend Reversal, Earnings Reaction, Liquidity Stress, Crash-Like — all cells must have data or "N/A"
     - **4 stat tiles** in order: Disagreement, Confidence, Composite Risk, Downside Skew — ALL 4 REQUIRED
   - Heatmap color coding: `.heatmap-low` (<10% green), `.heatmap-med` (10-20% amber), `.heatmap-high` (20-30% red), `.heatmap-extreme` (>30% dark red)
   - Price methodology: Scenario ranges = Current ± (ATR × √horizon × regime_vol_multiplier)
   - **Purpose**: Forward-looking risk assessment with probabilistic scenario modeling
13. **Recent News & Sentiment** + **Key Risk & Catalyst Factors** (side by side)
    - News items must include hyperlinks to original articles
    - Include news summary text and sentiment badges
    - Overall sentiment score box
    - **Include simulation-derived risk narratives**: If vol_expansion weight > 0.25, flag "Volatility regime shift". If tail_risk weight > 0.15, flag "Tail risk dislocation". If liquidity_stress_20d > 0.15, flag "Liquidity deterioration".
   - **Purpose**: Recent developments and qualitative risk/catalyst assessment
14. **Shares & Ownership** (full width)
   - Ownership statistics table (Shares Outstanding, Float, Institutional %, Insider %)
   - C-Suite Leadership table (8 executives: CEO, President, CFO, CPO, CRO, CProdO, CLO, CTO with full names and titles)
   - Recent Insider Transactions table (Name, Title, Type, Shares, Price, Date, Value, Ownership Change)
   - **Narrative analysis box** below the ownership/transactions flex container:
     - Styled box: `background:#f8fafc; border:1px solid #e8ecf3; border-radius:6px; padding:12px; margin-top:10px`
     - Title: "Ownership & Insider Activity Analysis" (bold, 0.82em)
     - Body: 3-5 sentences interpreting institutional vs insider balance, selling patterns, founder alignment, float liquidity
   - **Purpose**: Governance, insider behavior, institutional commitment

### Narrative Integrity (applies to ALL narrative analysis boxes in S10, S11, S14, S15)
- **Standalone**: Each narrative must be self-contained for the current ticker. NEVER reference other tickers or reports
- **Data-grounded**: Every claim must cite specific numerical metrics (dollar amounts, percentages, ratios) from the report
- **No fabrication**: Only use data fetched from Alpha Vantage or computed by the Python engine. Never invent figures
- **Ticker-specific**: Explain macro/financial impact using THIS company's specific business model and numbers

15. **US Economic Indicators — Macro Dashboard** (full width)
    - GDP, CPI, Fed Funds Rate, Unemployment, 10Y Treasury, Retail Sales, NFP
    - Include "[TICKER] Impact" column explaining relevance to the stock
    - Federal Funds Rate cutting cycle visual chart
    - **Narrative analysis box** below the Fed chart:
      - Styled box: `background:#f8fafc; border:1px solid #e8ecf3; border-radius:6px; padding:12px; margin-top:10px`
      - Title: "Macro Environment Analysis" (bold, 0.82em)
      - Body: 3-5 sentences interpreting GDP impact, Fed policy dual effects, inflation trajectory, employment, and net macro signal for the ticker
   - **Purpose**: US economic backdrop (GDP, inflation, Fed policy, employment)
16. **Global Market Indicators** + **Macro-Equity Correlation Analysis** (side by side)
   - Gold, Silver, Oil, EUR/USD, GBP/USD, USD/JPY
   - Sensitivity analysis: HIGH/MEDIUM/LOW impact on the stock
   - **Purpose**: Global market conditions and cross-asset correlations
17. **Competitive Landscape** — Industry peer comparison (full width)
    - Peer comparison table: Price, Market Cap, Revenue, Rev Growth, Gross Margin, P/S, EV/Revenue, Analyst Rating
    - Competitive Positioning Map table comparing 6 dimensions
    - Industry Value Chain Position visual (flexbox tag layout)
    - Differentiation summary box
    - Key Takeaway disclaimer box
   - **Purpose**: Competitive positioning vs industry peers
18. **Net Macro Environment Scorecard** (full width)
    - Scorecard tiles: TAILWIND / NEUTRAL / HEADWIND for each factor
    - **Include CCRLO tile**: Composite risk score X/21 with color by risk level (green LOW, amber MODERATE, red HIGH)
    - **Include Event Risk tile**: Composite event risk (average of top-3 20d event probabilities); GREEN <15%, AMBER 15-30%, RED >30%
    - Net assessment summary box
   - **Purpose**: Aggregated macro environment assessment (GDP, inflation, Fed, employment, dollar, global trade)
19. **Disclaimer** — Standard financial disclaimer
20. **Timestamp** — Generation date, data source, delay notice

## Complete Narrative & Analysis Box Inventory (7 total)
Every report contains exactly 7 interpretive elements — no more, no less:

| Section | Box Title | Type | Styling |
|---|---|---|---|
| S7 | Benchmark Analysis | Pre-built | `#f8fafc` gray box |
| S10 | Income Statement Analysis | Narrative | `#f8fafc` gray box |
| S11 | Technical Analysis Summary | Narrative | `#f8fafc` gray box |
| S14 | Ownership & Insider Activity Analysis | Narrative | `#f8fafc` gray box |
| S15 | Macro Environment Analysis | Narrative | `#f8fafc` gray box |
| S17 | Key Takeaway | Pre-built | `#fffbeb` yellow box |
| S18 | Net Assessment | Pre-built | `#eff6ff` blue box |

Do NOT add narrative boxes to other sections — side-by-side cards (S8, S9, S13, S16) have card height limits that prevent it.

- **Never put too much content in a single card** — max ~60% of landscape A4 page height
- The Price Target section MUST be split into **3 separate cards**:
  1. Scenario Table
  2. Price Corridors & Corrections
  3. Assumptions & Projections
- Each card gets its own `<div class="card full-width">` with its own `<h2>`
- This ensures `page-break-inside: avoid` works correctly
- If any other section exceeds 60% height (e.g., Competitive Landscape with many peers), split it too

## Side-by-Side vs Full-Width Layout

| Layout | Sections |
|---|---|
| **Full-width** | Executive Summary, Price Target (3 cards), Benchmark Comparison, Valuation+Financial (when with Income Statement Breakdown), Financial Flow — Income Statement Breakdown, Technical Indicators, Event Risk Simulation, Shares & Ownership, US Economic Indicators, Competitive Landscape, Net Macro Environment Scorecard, Disclaimer |
| **Side-by-side** (flex row) | Analyst Consensus+EPS, Valuation+Financial Health (when standalone), Recent News+Risks, Global Markets+Correlation |
| **Embedded in card** | Monthly Price Forecast (inside Section 5 card), Correction Risk table (inside Section 5 card) |

## Rationale for Importance-Based Reorganization

The new section order (implemented March 2026) follows an "inverted pyramid" journalism principle adapted for investment research:

**Top Priority (Sections 1-6)**: Verdict and price outlook
- Readers get Executive Summary + price targets immediately
- Answers: "What's the recommendation and where's the price going?"

**High Priority (Sections 7-10)**: Performance validation and fundamentals  
- **Section 7 (Benchmark)**: NEW - How has TICKER performed vs S&P 500? (immediate context, dual 12-month + 5-year charts)
- **Section 8 (Analyst Consensus)**: MOVED UP - What does Wall Street think? (external validation)
- **Section 9 (Valuation)**: MOVED UP - What's it worth fundamentally? (intrinsic value)
- **Section 10 (Income Statement Breakdown)**: MOVED UP - How does the business generate profit? (unit economics)

**Medium Priority (Sections 11-13)**: Technical signals and risks
- **Section 11 (Technical Indicators)**: When to enter/exit based on price action?
- **Section 12 (Event Risk)**: What could go wrong in next 20 days?
- **Section 13 (News & Risks)**: What's happening now and what are the catalysts?

**Lower Priority (Sections 14-18)**: Supporting context and macro backdrop
- Shares & Ownership, Economic Indicators, Global Markets, Competitive Landscape, Macro Scorecard
- Important for completeness but not immediately decision-critical
- Professional readers can skip these if short on time

**Key Philosophy**: Decision-makers need actionable intelligence first, supporting context later. The reorganization ensures readers get verdict → price targets → performance benchmarks → external validation → fundamentals → technicals → risks → background → macro in that sequence.
