---
name: data-collection
description: >
  Collect all required market data from Alpha Vantage MCP for stock analysis.
  USE FOR: "fetch data for [TICKER]", "collect market data", "get stock data",
  "pull financial data", data collection phase, pre-report data gathering.
  DO NOT USE FOR: generating reports (use report-generation), computing signals
  (use short-term-analysis/long-term-prediction/simulation), fixing reports (use report-fix).
---

# Data Collection Skill

## Overview

Collect all required Alpha Vantage MCP data for a given ticker in a single structured pass.
This skill standardizes data gathering across all analysis workflows — report generation,
standalone signals, and audits all consume the same data contract.

**Always fetch fresh data (NON-NEGOTIABLE)**: Every analysis request — first-time or re-analysis —
MUST fetch fresh data from Alpha Vantage MCP. Never reuse, skip, or rely on existing data bundles.
Even if `scripts/data/[TICKER]_bundle.json` already exists, fetch everything fresh and overwrite.
Market data changes constantly; stale data produces misleading reports.

**Reference**: `.instructions/data-collection.md` for full MCP tool details.

## Data Contract

This skill produces a **Data Bundle** — a structured collection of all raw data needed
by downstream skills. The bundle has 4 sections:

### 1. Subject Ticker Data (15 data points)

| # | Tool | Key Fields | Used By |
|---|---|---|---|
| 1 | `GLOBAL_QUOTE` | Price, OHLCV, change%, latest trading day | All skills |
| 2 | `COMPANY_OVERVIEW` | Market cap, P/E, Beta, D/E, 52W range, sector, analyst target | All skills |
| 3 | `INCOME_STATEMENT` | Revenue, COGS, gross profit, operating income, net income (annual) | Report, Income Statement Breakdown |
| 4 | `BALANCE_SHEET` | Total debt, equity, cash, assets (most recent) | Report, Fragility |
| 5 | `CASH_FLOW` | Operating CF, CapEx, FCF (most recent) | Report, Fragility |
| 6 | `EARNINGS` | Quarterly EPS history (8+ quarters) | Report, Fragility |
| 7 | `RSI` | RSI(14) daily values | All signal skills |
| 8 | `MACD` | MACD line, signal, histogram | All signal skills |
| 9 | `BBANDS` | Upper, middle, lower bands (20-day) | Simulation |
| 10 | `SMA` × 2 | SMA(50) and SMA(200) daily values | TB/VS/VF, Regime |
| 11 | `EMA` × 2 | EMA(12) and EMA(26) daily values | Report |
| 12 | `ADX` | ADX(14) daily values | Regime detection |
| 13 | `ATR` | ATR(14) daily values | All signal skills |
| 14 | `NEWS_SENTIMENT` | Sentiment labels, scores, article URLs (tickers=[TICKER]) | Report, Simulation |
| 15 | `INSTITUTIONAL_HOLDINGS` | Ownership %, top holders | Report, Simulation |

### 2. Peer Data (3-5 competitors)

For each peer, fetch:
- `COMPANY_OVERVIEW` — fundamentals for competitive comparison
- `GLOBAL_QUOTE` — current price for relative valuation

**Peer selection criteria** (in priority order):
1. Same GICS subsector/industry
2. Market cap within 0.5x–3x of subject
3. Strategic relevance (direct competitors, supply chain)

### 3. Macro Data (4 indicators — MARKET-WIDE)

**CRITICAL**: Macro data is market-wide and must be identical across ALL reports generated in the same session. Fetch once with the first ticker, cache, and reuse for all subsequent tickers.

| Tool | Key Fields | Min History | Used By |
|---|---|---|---|
| `CPI` | Monthly CPI values | **4 months** (current + 3 prior) | CCRLO, Macro Dashboard |
| `FEDERAL_FUNDS_RATE` | Monthly effective rate | **12 months** (for Fed chart) | CCRLO, Fed Chart, Macro Dashboard |
| `UNEMPLOYMENT` | Monthly rate | **4 months** (current + 3 prior) | CCRLO, Macro Dashboard |
| `REAL_GDP` | Quarterly GDP growth | **4 quarters** | CCRLO, Macro Dashboard |

#### FEDERAL_FUNDS_RATE — Data Depth Requirement (CRITICAL)
The Fed Funds Rate chart requires **exactly 12 months** of historical data. The Alpha Vantage `FEDERAL_FUNDS_RATE` API returns monthly data — you MUST:
1. Fetch the full response (it returns multiple months by default)
2. Extract the **12 most recent monthly values** for the chart
3. Store ALL returned data points in the bundle (not just the latest value)
4. **NEVER store only 1 data point** — this causes the report generator to fabricate/interpolate the remaining 11 months, producing incorrect charts
5. **NEVER estimate or interpolate** rate values — only use actual API data

#### Cross-Report Consistency Rule
When generating multiple reports in one session:
- Use the **exact same macro values** from the cached data for every report
- The Fed chart bars, CPI value, unemployment rate, and GDP figure must match across all reports
- The only section that changes between reports is the `{{TICKER}} Impact` column text

### 4. Company Profile Classification

After collecting data, classify the company:

| Profile | Criteria | Journey Type |
|---|---|---|
| Mature Large-Cap | Profitable 3+ years, >$50B market cap | Profitability Journey (EPS) |
| Established Growth | Profitable, high-growth sector | Profitability Journey (EPS) |
| Hypergrowth Post-IPO | Revenue CAGR >200%, IPO <3 years | Revenue Chart (`.rev-chart`) |
| Small-Cap Post-IPO | Unprofitable, positive operating CF | Revenue Growth + Operating CF |
| Fintech/Digital | Transitioning to profitability | Revenue Growth Journey |

## MCP Workflow

### Step 1: List Available Tools
```
TOOL_LIST → category: "core_stock_apis"
TOOL_LIST → category: "economic_indicators"
TOOL_LIST → category: "technical_indicators"
```

### Step 2: Get Schemas (if needed)
```
TOOL_GET → tool_name: "GLOBAL_QUOTE"   (to verify argument format)
```

### Step 3: Fetch Subject Data
Call all 15 tools for the subject ticker. Recommended order to minimize rate limits:
1. `GLOBAL_QUOTE` and `COMPANY_OVERVIEW` (fast, small responses)
2. Financial statements: `INCOME_STATEMENT`, `BALANCE_SHEET`, `CASH_FLOW`, `EARNINGS`
3. Technical indicators: `RSI`, `MACD`, `BBANDS`, `SMA`×2, `EMA`×2, `ADX`, `ATR`
4. Sentiment & ownership: `NEWS_SENTIMENT`, `INSTITUTIONAL_HOLDINGS`

**Technical Indicator Data Depth (CRITICAL)**:
All technical indicator calls (RSI, MACD, BBANDS, SMA, EMA, ADX, ATR) MUST include
`datatype: "json"` to get full history. The default CSV response truncates to ~45 data
points, which fails the input validator (ATR needs ≥50, SMA200 needs ≥200).
```
TOOL_CALL → tool_name: "ATR"
arguments: { symbol: "[TICKER]", interval: "daily", time_period: 14, datatype: "json" }
```
After each fetch, verify the response has sufficient data points:
- SMA(200): ≥200 values (FAIL if fewer)
- SMA(50), ATR: ≥50 values (FAIL if fewer)
- RSI, MACD, BBANDS, EMA, ADX: ≥1 value (WARN if fewer)

### Step 4: Fetch Peer Data
After subject data is loaded, identify 3-5 peers from `COMPANY_OVERVIEW.Sector` and
`COMPANY_OVERVIEW.Industry`. Fetch `COMPANY_OVERVIEW` + `GLOBAL_QUOTE` for each.

### Step 5: Fetch Macro Data (Market-Wide — Cache for Reuse)
Call `CPI`, `FEDERAL_FUNDS_RATE`, `UNEMPLOYMENT`, `REAL_GDP`.

**Data depth requirements**:
- `FEDERAL_FUNDS_RATE`: Must return 12+ monthly data points. Verify the response contains at least 12 entries before proceeding. If the response is truncated, fetch with `outputsize=full` or `datatype=json` parameters.
- `CPI`: Must return at least 4 monthly values (for Current + Prior + trend calculation)
- `UNEMPLOYMENT`: Must return at least 4 monthly values
- `REAL_GDP`: Must return at least 4 quarterly values

**Validation gate**: After fetching, verify `federal_funds_rate` array has ≥12 entries. If fewer, log a WARNING and re-fetch. If still insufficient, proceed but add a note in the report that chart data is incomplete.

### Step 6: Classify Company Profile
Use the criteria table above to assign a profile type based on the collected data.

## Output

The data bundle is held in working memory for consumption by downstream skills:
- **report-generation**: Uses entire bundle for HTML generation
- **short-term-analysis**: Uses Subject Ticker (items 1-2, 4-5, 6-13) + Macro (Fed Rate)
- **long-term-prediction**: Uses Subject Ticker (items 1-2, 7, 12-13) + all Macro
- **simulation**: Uses entire Subject Ticker + Macro (no peers needed)
- **report-audit**: Re-reads the generated report file (no raw data needed)

## Rate Limit Awareness

Alpha Vantage free tier: 5 calls/minute, 500 calls/day.
- Total calls for a full report: ~25-30 (15 subject + 8-10 peers + 4 macro)
- Space calls with brief pauses if hitting rate limits
- If a call fails, retry once after 15 seconds before reporting failure

## Critical Rules

1. **Always collect all 15 subject data points** — never skip any
2. **Always collect all 4 macro indicators** — even for standalone signals
3. **Peer selection must be justified** — document why each peer was chosen
4. **Profile classification drives report structure** — get it right before generation
5. **Data is 15-min delayed** — note this in report disclaimer (not in timestamp)
6. **Never fabricate data** — if an API call fails, report the failure and proceed with available data. **NEVER interpolate or estimate** macro data values (especially Fed Funds Rate history)
7. **Macro data depth** — `FEDERAL_FUNDS_RATE` must have ≥12 monthly data points for the Fed chart. `CPI` and `UNEMPLOYMENT` must have ≥4 data points. If insufficient, re-fetch or flag as incomplete
8. **Cross-report macro consistency** — when generating multiple reports, macro values (CPI, FFR, Unemployment, GDP) must be identical across all reports. Cache macro data after first fetch and reuse
