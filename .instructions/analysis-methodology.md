# Analysis Methodology

## Price Target Scenario Framework

### Three Scenarios

| Scenario | EPS CAGR | P/E Multiple | Conditions |
|---|---|---|---|
| **Conservative** | ~25-30% | 18-22x | P/E compression, macro headwinds, slower growth |
| **Average (Consensus)** | ~40-50% | 28-35x | Analyst 12-month target extrapolated, steady EPS growth |
| **Bullish** | ~60%+ | 40-50x | Platform flywheel, index inclusion, P/E expansion |

- Always include disclaimer that projections are model-based estimates, not investment recommendations
- Use analyst 12-month target as basis for Average scenario Year 1

### Analyst Target Price Sourcing

- **Which target**: Use the **mean** from `COMPANY_OVERVIEW` (`AnalystTargetPrice` field)
- **Recency**: If data >3 months old, note the staleness
- **Range display**: Include analyst high/low range when available
- **Outlier handling**: If range exceeds 3x spread (e.g., $15-$50), note wide dispersion, weight median over mean
- **In projections**: 12-month analyst target = Year 1 Average scenario basis

### Analyst Coverage Thresholds

- **<15 analysts**: Less reliable, widen conviction bands in projections
- **15-30 analysts**: Good consensus, trust within ±10% bands
- **>30 analysts**: Institutional benchmark, use as price anchor

## SVG Price Corridor Chart

### Specifications
- **ViewBox**: `viewBox="0 0 600 200"` (enhanced wider format)
- **Polygon order**: Define corridor gradient fill polygons FIRST, then polylines on top
- **Polyline colors**: Green (`#16a34a`) Bullish, Blue (`#2563eb`) Average, Red (`#dc2626`) Conservative
- **Corridor gradient fills**: Use SVG `<linearGradient>` vertical (opaque top → transparent bottom)
- **Interactive data points**: Each `<circle>` + `<text>` wrapped in `<g class="corridor-g">` for hover
- **End badges**: Colored pill shapes at line endpoints showing final target price
- **Correction dip markers**: Red circles (`fill:#dc2626`) with dashed connecting lines
- **Number of dip markers**: 2-3 per corridor
- **Animated line drawing**: `@keyframes corridorDrawLine` with staggered delays
- **Y-axis**: Price grid lines with labels; X-axis year labels
- **Y coordinate formula**: `y = 182 - (price / maxPrice) * 162` where maxPrice = highest bullish target
- See `.instructions/styling.md` for full CSS classes and SVG structure

### Correction Probability Calculation

| Tier | Drawdown Range | Base Probability | Beta >1.5 Adj | Post-IPO (<2yr) Adj |
|---|---|---|---|---|
| Mild Pullback | -10% to -15% | 85-95% | +5% | — |
| Standard Correction | -20% to -30% | 55-70% | +10% | — |
| Severe Drawdown | -40% to -50% | 25-40% | — | +10% |
| Black Swan | -60%+ | 8-15% | — | +5% |

Calculate price floors: `current_price × (1 - drawdown%)`

## Monthly Price Forecast — Computation

### Overview
The Monthly Price Forecast provides month-by-month price projections for the current year, incorporating both historical accuracy validation (past months) and forward predictions (future months). It appears in Section 5 (Price Corridors).

### Step 1: Identify Past vs Future Months
- **Report month**: The month the report is generated (e.g., March 2026)
- **Past months**: Jan through (report_month - 1)
- **Current month**: The report month itself
- **Future months**: (report_month + 1) through December

### Step 2: Past Months — Actual vs Model Estimate
For each past month:
1. **Actual price**: Use the month-end closing price
2. **Model estimate**: What the Average scenario would have predicted for that month at the START of the year (pre-trend-break, pre-recalibration). This is a linear interpolation from the price at year start to the original analyst target.
3. **Accuracy calculation**:
   - `error% = (Model_Est - Actual) / Actual × 100`
   - `Accuracy = 100% - |error%|`
   - If error is positive: "over" (model overestimated)
   - If error is negative: "under" (model underestimated)

### Step 3: Accuracy Summary
- Calculate average accuracy across all past months
- Calculate average error magnitude and direction (systematic bias)
- Color-code the summary badge: >90% green, 85-90% amber, <85% red

### Step 4: Future Months — 3-Scenario Interpolation
For each future month (Apr through Dec):
1. **Start point**: Current price (report month)
2. **End point**: Section 4 year-end targets for each scenario
3. **Interpolation**: Linear interpolation from current price to year-end target
   - `Month_Price = Current + (Target - Current) × (months_remaining / total_months_to_dec)`
4. **Adjustments**:
   - If TB is ACTIVE: Conservative path declines more steeply in near-term
   - If CCRLO is elevated: Insert expected dip (Aug-Sep seasonal + CCRLO probability)
   - If strong catalyst upcoming: Allow temporary deviation from linear path

### Step 5: December Consistency (CRITICAL)
- December row Conservative = Section 4 Conservative year-end target
- December row Average = Section 4 Average year-end target
- December row Bullish = Section 4 Bullish year-end target
- These MUST be exact matches. No exceptions.

### Step 6: Narrative Path Boxes
Three colored boxes below the table summarizing each scenario's narrative:
- Conservative (red): Why the price declines, what goes wrong
- Average (blue): The base case, key drivers, matches analyst consensus
- Bullish (green): Best case, catalysts that drive outperformance

## Financial Journey Visualization

### Use "Profitability Journey" (EPS) when:
- Company profitable for 3+ years
- EPS shows clear growth trajectory
- Examples: AAPL, ASML

### Use "Revenue Growth Journey" when:
- Post-IPO, still unprofitable (GAAP distorted by SBC)
- Revenue is more meaningful metric
- Include Operating Cash Flow trend below
- Examples: CHYM, HOOD

### Use `.rev-chart` (bar chart) when:
- Revenue CAGR >200% over 3+ years
- Revenue scale shift >10x
- Hypergrowth is central to thesis
- Example: NBIS

## Financial Flow — Income Statement Breakdown

### Purpose
Visualize how revenue flows through the income statement to show where money comes from, how it's allocated, and what becomes profit vs. expense. Placed as a full-width card below the Valuation Metrics + Financial Health side-by-side cards.

### Enhanced Interactive Features
- **Gradient flow bands**: Each `<path>` uses `<linearGradient>` (source color → target color)
- **Hover glow**: `fill-opacity` increases + `drop-shadow` on hover
- **Flow-in animation**: `@keyframes sankeyFlowIn` — bands fade in on page load (disabled in print)
- **Stage headers**: `.sankey-stage-label` text above each column
- **Legend bar**: Colored swatches below SVG identifying each node type
- **Margin callout boxes**: Gross Margin and Net Margin in top-right corner of SVG
- **Tooltips**: `<title>` inside each `<path>` shows "Source → Target: $XX (XX%)"
- See `.instructions/styling.md` for full CSS classes and SVG structure

### Data Extraction (from `INCOME_STATEMENT`)
Extract the most recent annual fiscal year data:

| Field | Variable | Stage |
|---|---|---|
| `totalRevenue` | Total top-line revenue | Stage 1-2 |
| `costOfRevenue` (COGS) | Direct costs | Stage 2-3 |
| `grossProfit` | Revenue minus COGS | Stage 2-3 |
| `researchAndDevelopment` | R&D expense | Stage 4-5 |
| `sellingGeneralAndAdministrative` | SGA expense | Stage 4-5 |
| `operatingExpenses` | Total operating expenses | Stage 3-4 |
| `operatingIncome` | Gross profit minus OpEx | Stage 3-4 |
| `incomeTaxExpense` | Taxes paid | Stage 4-5 |
| `interestExpense` | Debt servicing cost | Stage 4-5 |
| `netIncome` | Bottom-line profit/loss | Stage 5 |

### Flow Structure (5 Stages)

```
Revenue Sources → Total Revenue → [COGS + Gross Profit] → [OpEx + Operating Income] → [R&D + SGA + Tax + Interest + Net Income]
```

**Stage 1 → 2**: Revenue breakdown (Product/Service/Subscription if available, else single flow)
**Stage 2 → 3**: Revenue splits into COGS and Gross Profit
**Stage 3 → 4**: Gross Profit splits into Operating Expenses and Operating Income
**Stage 4 → 5**: Breakdown into R&D, SGA, Tax, Interest, and Net Income

### Analysis Notes
- For **profitable companies**: Net Income node is green, show margin percentage
- For **unprofitable companies**: Net Loss node is red, add footnote about path to profitability
- **Gross margin visual**: The Gross Profit band width relative to Revenue immediately shows margin health

### Narrative Analysis Box (REQUIRED)
Below the Sankey legend bar, every report must include a narrative interpretation box:
- **Style**: `background:#f8fafc; border:1px solid #e8ecf3; border-radius:6px; padding:12px; margin-top:10px`
- **Title**: "Income Statement Analysis" (`font-size:0.82em; font-weight:700; color:#1b2a4a`)
- **Body**: 3-5 sentences in `font-size:0.78em; color:#5a6577; line-height:1.5` interpreting:
  - Gross margin quality and what it reveals (asset-light vs capital-intensive)
  - Dominant expense category (R&D-heavy, fulfillment-heavy, SGA-heavy) and its strategic implication
  - Operating margin and operating leverage trend
  - Net margin and effective tax rate
  - Year-over-year trend or turnaround narrative (e.g., loss-to-profit transition)
- Use `<strong style="color:#16a34a;">` for key margin percentages
- See HOOD gold standard Section 10 for reference implementation
- **Narrative integrity rules apply** — see `.instructions/report-layout.md` for standalone/data-grounded/no-fabrication requirements. These same rules apply to all narrative boxes: S10, S11, S14, S15
- **R&D intensity**: Compare R&D band width to total revenue — tech companies often >15%
- **SGA efficiency**: Declining SGA-to-revenue ratio = improving operational leverage
- If a company has very simple revenue (single product line), use the 4-stage simplified version

### When to Simplify
If Alpha Vantage `INCOME_STATEMENT` doesn't provide revenue segmentation:
- Use 4 stages: Total Revenue → COGS + Gross Profit → OpEx + Operating Income → Expense Detail + Net Income
- Label the single revenue node with the company's primary business description

## Post-IPO & Small-Cap Adjustments

### Earnings Table Footnotes
Add asterisks when: SBC >20% of loss, restructuring >$50M, one-time costs

### Operating Cash Flow Proxy
For unprofitable companies with positive operating CF, show journey with:
- Red steps for negative years, green steps for positive years
- Checkmark note when CF turns positive

### Valuation Discount Callout
When post-IPO trades at discount vs mature peers, add Key Takeaway box explaining the gap.

## Macro Analysis Framework

### Fed Funds Rate Chart
- **Data source**: Alpha Vantage `FEDERAL_FUNDS_RATE` API — extract the 12 most recent monthly values
- **Data depth**: Must use ≥12 actual API-returned data points. **NEVER interpolate or estimate** rate values from a single data point
- **Cross-report consistency**: Fed chart values are market-wide and MUST be identical across all reports generated in the same session
- **Color mapping**: 4%+ Red (#dc2626), 3.5-4% Orange (#fd7e14/#d97706), 3-3.5% Amber (#d97706), <3% Green (#16a34a)
- **Height**: tallest bar ~80px, scale others proportionally using `(rate / max_rate) * 80px` (fixed pixel heights only)
- **Bar structure**: Each bar column uses `flex:1` to spread equally across the container. Bar div inside uses `width:30px; border-radius:3px 3px 0 0`. **Never use `min-width:40px`** — this causes bars to bunch to the left instead of spreading evenly
- **Narrative**: State total bps change from peak, link to stock's valuation thesis

### Macro Sensitivity Rubric

| Score | Magnitude | Example |
|---|---|---|
| **HIGH +** | +5% to +15% stock impact | Fed rate cuts 75bps → growth stocks |
| **HIGH -** | -5% to -15% stock impact | China tariffs 25% → semiconductors |
| **MEDIUM +** | +2% to +5% stock impact | Unemployment stays flat → broad consumer |
| **MEDIUM -** | -2% to -5% stock impact | Oil prices spike 30% → manufacturing |
| **LOW / INDIRECT** | <2% or indirect | Gold prices high → crypto (risk-off signal) |
| **NEUTRAL** | No consistent correlation | Trade policy uncertainty |

Score each factor independently. Net Assessment must be balanced: TAILWIND / NEUTRAL / HEADWIND.

## News & Sentiment

- **Quantity**: 3-5 items per report
- **Recency**: Prioritize last 3-7 days
- **Sentiment mapping**: Alpha Vantage `overall_sentiment_label` → `.signal` badges
  - "Bullish" / "Somewhat-Bullish" → `.signal.bullish`
  - "Neutral" → `.signal.neutral`
  - "Bearish" / "Somewhat-Bearish" → `.signal.bearish`
- **Hyperlinks**: Every item MUST link to original article
- **Overall score**: Summary box with aggregate sentiment

## Competitive Landscape

### Peer Selection Criteria
1. **Industry/subsector** — 3-5 direct competitors or adjacent players
2. **Market cap proximity** — 0.5x to 3x of subject company
3. **Strategic relevance** — At least one leader, one challenger, one emerging player
4. **Avoid** — Private, delisted, or <$100M revenue companies

### Peer Table (9 columns)
Company | Price | Market Cap | Revenue (TTM) | Rev Growth YoY | Gross Margin | P/S Ratio | EV/Revenue | Analyst Rating

- Subject row: `background:#eff6ff;` (light blue)
- Revenue Growth: green bold (`color:#16a34a;`)
- Ratings: use `.signal` badges

### Positioning Map (6 dimensions)
Revenue Growth, Revenue Scale, Gross Margin, Valuation, Key Catalyst, Profitability
- Score with `.signal` badges: bullish for "Leader"/"High", neutral for "Moderate", bearish for "Declining"

### Key Takeaway Box
```html
<div style="margin-top:12px; padding:10px; background:#fffbeb; border-radius:4px; border:1px solid #fde68a;">
  <div style="font-size:0.76em; color:#92400e;"><strong>Key Takeaway:</strong> [Summary]</div>
</div>
```

## Event Risk Simulation — Methodology Integration

### Correction Probability Calibration via Simulation

When simulation data is available, use tail_risk scenario weight to adjust correction probabilities:

```
Adjusted_Mild      = Base_Mild      × (1 + tail_risk_weight)
Adjusted_Standard  = Base_Standard  × (1 + 2 × tail_risk_weight)
Adjusted_Severe    = Base_Severe    × (1 + 3 × tail_risk_weight)
Adjusted_BlackSwan = Base_BlackSwan × (1 + 3 × tail_risk_weight)
```

Where `tail_risk_weight` is the Tail Risk scenario weight from simulation (typically 0.05–0.25).
Cap all adjusted probabilities at 95%.

**Example**: If Standard correction base = 60% and tail_risk_weight = 0.15:
- Adjusted_Standard = 60% × (1 + 2 × 0.15) = 60% × 1.30 = 78%

This adjustment stacks with existing Beta, post-IPO, and fragility adjustments.
Apply simulation adjustment LAST (after all other adjustments).

### Regime Feature Extraction

All features are computed from data already collected via Alpha Vantage MCP (Phase 1):

| Feature | Source | Formula |
|---|---|---|
| `RSI_14` | `RSI` (daily, 14) | Direct value from most recent data point |
| `ADX_14` | `ADX` (daily, 14) | Direct value from most recent data point |
| `ATR_pctile` | `ATR` (daily, 14) | Rank today's ATR vs last 252 values → percentile |
| `ATR_ratio` | `ATR` (daily, 14) | Today's ATR / average of last 50 ATR values |
| `MACD_histogram` | `MACD` (daily) | `MACD_line - Signal_line` from response |
| `BB_width` | `BBANDS` (daily, 20) | `(Upper - Lower) / Middle × 100` |
| `Price_vs_SMA200` | `SMA` (200) | `(Price - SMA200) / SMA200 × 100` |
| `Price_vs_SMA50` | `SMA` (50) | `(Price - SMA50) / SMA50 × 100` |
| `Volume_ratio` | `GLOBAL_QUOTE` | Today's volume / 20-day average volume |
| `Beta` | `COMPANY_OVERVIEW` | Direct field |

### Event Base Rates (Historical Calibration)

| Event | 5d | 10d | 20d | Source |
|---|---|---|---|---|
| Large Move (>2.5σ) | 12% | 18% | 25% | Empirical: ~20% of 20d windows have >2σ moves |
| Volatility Spike | 8% | 15% | 22% | Vol clustering: elevated states persist ~15-25% of time |
| Trend Reversal | 6% | 12% | 20% | MA crossovers: ~quarterly frequency for SMA50 |
| Earnings Reaction | — | — | 20% | ~25-30% of S&P stocks gap >5% on earnings |
| Liquidity Stress | 5% | 8% | 12% | Illiquidity events: ~10-15% for mid/small-cap |
| Crash-Like Path | 2% | 4% | 7% | ~3-5% annual crash frequency → 7% per 20d |

See `.instructions/simulation-strategy.md` for full adjustment tables and regime conditioning multipliers.

### Scenario Price Range Computation (Section 12)

Each simulation scenario produces a 20-day price range using ATR-based volatility scaling:

```
ATR_daily = ATR(14) from Alpha Vantage
ATR_h = ATR_daily × sqrt(20) ≈ ATR_daily × 4.47

Base Case:      Current ± (ATR_h × 0.10)
Vol Expansion:  (Current - ATR_h × 0.55) to (Current + ATR_h × 0.22)  [asymmetric, downside biased]
Trend Shift:    (Current - ATR_h × 0.68) to min(SMA_50, Current + ATR_h × 0.65)
Tail Risk:      (Current × (1 - 0.15 × Beta/1.5)) to (Current × 0.97)  [Beta-scaled, downside only]
```

**Scenario Midpoints**: `midpoint = (range_low + range_high) / 2` for all scenarios.
(Exception: Base Case midpoint uses analyst consensus drift ≈ Current × (1 ± 0.01).)

**Weighted Expected Price** = Σ(scenario_weight_i × scenario_midpoint_i)
**80% Confidence Range**: Σ(weight_i × range_low_i) to Σ(weight_i × range_high_i)
**Downside Skew** = (vol_weight × 0.7) + tail_weight + (trend_weight × 0.5), clipped [20%, 85%]

### Event Price Impact (Section 12 Heatmap)

| Event | Price Impact Formula |
|---|---|
| Large Move | Current ± (2.5 × ATR × √horizon_factor) |
| Vol Spike | Current ± (1.5 × ATR × √horizon) wider range |
| Trend Reversal | Upside target = SMA_50; downside = Current - 2×ATR×√horizon |
| Earnings Reaction | Current ± (implied_move or 5% × Current) |
| Liquidity Stress | Current × 0.95 to Current × 0.99 (gap down bias) |
| Crash-Like Path | < Current × 0.85 |
