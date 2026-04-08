# Data Collection via Alpha Vantage MCP

## Available Data Categories

| Category | Key Tools | Use Case |
|---|---|---|
| **Core Stock Data** | `GLOBAL_QUOTE`, `TIME_SERIES_DAILY`, `TIME_SERIES_INTRADAY` | Price, volume, OHLCV |
| **Fundamentals** | `COMPANY_OVERVIEW`, `INCOME_STATEMENT`, `BALANCE_SHEET`, `CASH_FLOW`, `EARNINGS` | Financial health |
| **Technical Indicators** | `RSI`, `MACD`, `SMA`, `EMA`, `BBANDS`, `STOCH`, `ADX`, `ATR` | Trend & momentum signals |
| **Market Intelligence** | `NEWS_SENTIMENT`, `INSIDER_TRANSACTIONS`, `INSTITUTIONAL_HOLDINGS` | Sentiment & smart money |
| **Economic Indicators** | `CPI`, `FEDERAL_FUNDS_RATE`, `UNEMPLOYMENT`, `REAL_GDP` | Macro environment |
| **Options** | `REALTIME_OPTIONS`, `HISTORICAL_OPTIONS` | Derivatives analysis |

## MCP Workflow

1. **List tools**: Use `TOOL_LIST` with a category (e.g., `core_stock_apis`)
2. **Get schema**: Use `TOOL_GET` with the tool name (e.g., `GLOBAL_QUOTE`)
3. **Call tool**: Use `TOOL_CALL` with `tool_name` and `arguments` (e.g., `{"symbol": "AAPL", "datatype": "json"}`)

## Required Data for Full Report

Always collect all of the following for a complete analysis:

| Data | Tool | Purpose |
|---|---|---|
| Current price & OHLCV | `GLOBAL_QUOTE` | Header, price block |
| Company fundamentals | `COMPANY_OVERVIEW` | Valuation, sector, analyst target |
| Income statements | `INCOME_STATEMENT` | Revenue trends, margins, Income Statement Breakdown chart data |
| Balance sheet | `BALANCE_SHEET` | Debt levels, cash position |
| Cash flow | `CASH_FLOW` | Free cash flow, operating CF |
| Earnings | `EARNINGS` | EPS history, surprise table |
| RSI (14-day) | `RSI` | Overbought/oversold signals |
| MACD | `MACD` | Momentum crossovers |
| Bollinger Bands | `BBANDS` | Support/resistance, squeeze |
| SMA (50/200) | `SMA` | Golden/death cross |
| EMA (12/26) | `EMA` | Short-term trend |
| ADX | `ADX` | Trend strength |
| ATR | `ATR` | Volatility, stop-loss sizing |
| News sentiment | `NEWS_SENTIMENT` | Recent catalysts |
| Institutional holdings | `INSTITUTIONAL_HOLDINGS` | Smart money positioning |

For **competitive landscape**: `COMPANY_OVERVIEW` + `GLOBAL_QUOTE` for 3-5 industry peers
For **macro dashboard**: `CPI` (≥4 months), `FEDERAL_FUNDS_RATE` (≥12 months), `UNEMPLOYMENT` (≥4 months), `REAL_GDP` (≥4 quarters)

### Macro Data Depth Requirements (CRITICAL)
- **`FEDERAL_FUNDS_RATE`**: Must store **≥12 monthly data points** from the API response. The Fed chart requires exactly 12 bars. Storing only 1 value causes the report generator to fabricate/interpolate the remaining 11 months, producing **incorrect charts**. Always store the full API response.
- **`CPI`**: Must store ≥4 monthly values (current + 3 prior for trend calculation)
- **`UNEMPLOYMENT`**: Must store ≥4 monthly values
- **`REAL_GDP`**: Must store ≥4 quarterly values
- **Cross-report consistency**: Macro data is market-wide. When generating multiple reports, all macro values must be identical. Fetch once, cache, and reuse.

## Derived Features for Simulation

The event risk simulation system computes all features from the SAME data collected above.
No additional API calls are needed. Key derived features:

| Derived Feature | Source Tool(s) | How to Compute |
|---|---|---|
| ATR percentile (1Y) | `ATR` (daily, 14) | Rank today's ATR value against the last 252 data points in the ATR time series response → compute percentile |
| ATR ratio (50d) | `ATR` (daily, 14) | Today's ATR / average of the last 50 ATR data points |
| Bollinger width | `BBANDS` (daily, 20) | `(Upper Band - Lower Band) / Middle Band × 100` |
| MACD histogram | `MACD` (daily) | `MACD_Line - Signal_Line` from the response |
| Price vs SMA distance | `SMA` (50 & 200) + `GLOBAL_QUOTE` | `(Current_Price - SMA_value) / SMA_value × 100` |
| Volume ratio | `GLOBAL_QUOTE` | Today's volume / 20-day average volume (compute from daily series) |
| 52-week positioning | `COMPANY_OVERVIEW` | `(Current_Price - 52WeekLow) / (52WeekHigh - 52WeekLow)` |
| Earnings proximity | `EARNINGS` | Days until next quarterly earnings date (from quarterly history pattern) |
| Leverage (D/E) | `BALANCE_SHEET` | `totalLongTermDebt / totalShareholderEquity` |
| Institutional concentration | `INSTITUTIONAL_HOLDINGS` | Sum of top holders' percentage |

**Important**: Alpha Vantage technical indicator tools return time series (not single values).
The daily ATR response typically contains 100+ data points, which provides enough history
to compute percentiles and moving averages inline during report generation.

## Example Workflows

### Quick Stock Screening
```
1. TOOL_CALL → GLOBAL_QUOTE (symbol=AAPL) → Get current price
2. TOOL_CALL → COMPANY_OVERVIEW (symbol=AAPL) → Get P/E, EPS, sector
3. TOOL_CALL → RSI (symbol=AAPL, interval=daily, time_period=14) → Overbought/oversold
4. TOOL_CALL → NEWS_SENTIMENT (tickers=AAPL) → Current sentiment
```

### Swing Trade Setup
```
1. TOOL_CALL → TIME_SERIES_DAILY (symbol=AAPL, outputsize=compact)
2. TOOL_CALL → MACD (symbol=AAPL, interval=daily)
3. TOOL_CALL → BBANDS (symbol=AAPL, interval=daily, time_period=20)
4. TOOL_CALL → ATR (symbol=AAPL, interval=daily, time_period=14)
→ Entry: MACD crossover + price at lower Bollinger Band
→ Stop-loss: 1.5x ATR below entry
```

### Long-Term Investment Thesis
```
1. TOOL_CALL → COMPANY_OVERVIEW (symbol=AAPL)
2. TOOL_CALL → INCOME_STATEMENT (symbol=AAPL)
3. TOOL_CALL → BALANCE_SHEET (symbol=AAPL)
4. TOOL_CALL → CASH_FLOW (symbol=AAPL)
5. TOOL_CALL → EARNINGS (symbol=AAPL)
6. TOOL_CALL → INSTITUTIONAL_HOLDINGS (symbol=AAPL)
→ Build DCF model, compare to current price, assess margin of safety
```
