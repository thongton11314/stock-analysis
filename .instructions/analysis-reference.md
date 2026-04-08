# Fundamental & Technical Analysis Reference

## Fundamental Analysis (Long-Term Focus)

Evaluate a company's intrinsic value using financial statements.

### Key Metrics

| Metric | Source Tool | What to Look For |
|---|---|---|
| P/E Ratio | `COMPANY_OVERVIEW` | Compare to industry average |
| EPS Growth | `EARNINGS` | Consistent quarterly growth |
| Revenue Trend | `INCOME_STATEMENT` | YoY growth rate |
| Debt-to-Equity | `BALANCE_SHEET` | < 1.0 preferred |
| Free Cash Flow | `CASH_FLOW` | Positive and growing |
| Dividend Yield | `COMPANY_OVERVIEW` | Stable or increasing payouts |
| ROE | `COMPANY_OVERVIEW` | > 15% is strong |

### Long-Term Checklist
- [ ] Pull `COMPANY_OVERVIEW` for valuation ratios
- [ ] Compare 3-5 years of `INCOME_STATEMENT` (annual)
- [ ] Check `BALANCE_SHEET` for debt levels
- [ ] Analyze `CASH_FLOW` for free cash flow trends
- [ ] Review `EARNINGS` for EPS beat/miss history
- [ ] Check `INSTITUTIONAL_HOLDINGS` for smart money positioning
- [ ] Assess macro with `REAL_GDP`, `CPI`, `FEDERAL_FUNDS_RATE`

## Technical Analysis (Short-Term Focus)

Identify entry/exit points using price action and indicators.

### Core Indicators

| Indicator | Tool | Signal |
|---|---|---|
| **RSI** (14) | `RSI` | < 30 oversold, > 70 overbought |
| **MACD** | `MACD` | Signal line crossovers |
| **SMA** (50/200) | `SMA` | Golden cross / death cross |
| **EMA** (12/26) | `EMA` | Short-term trend direction |
| **Bollinger Bands** | `BBANDS` | Squeeze = breakout coming |
| **Stochastic** | `STOCH` | Momentum reversals |
| **ADX** | `ADX` | > 25 = strong trend |
| **ATR** | `ATR` | Volatility / stop-loss sizing |
| **VWAP** | `VWAP` | Intraday fair value |
| **OBV** | `OBV` | Volume confirms price |

### Short-Term Checklist
- [ ] Pull `TIME_SERIES_INTRADAY` (5min/15min) for day trading
- [ ] Pull `TIME_SERIES_DAILY` for swing trading (1-4 weeks)
- [ ] Calculate `RSI`, `MACD`, `BBANDS` for momentum signals
- [ ] Check `SMA` 50-day vs 200-day for trend
- [ ] Use `ATR` for position sizing and stop-loss placement
- [ ] Review `NEWS_SENTIMENT` for catalysts
- [ ] Check `TOP_GAINERS_LOSERS` for market momentum

## Prediction Strategy Framework

### Short-Term (Days to Weeks)

| Strategy | Indicators | Timeframe |
|---|---|---|
| Mean Reversion | RSI, Bollinger Bands, Stochastic | 1-5 days |
| Momentum | MACD, EMA crossovers, ADX | 1-4 weeks |
| Breakout | Bollinger Squeeze, Volume, ATR | 1-2 weeks |
| News-Driven | NEWS_SENTIMENT, EARNINGS_CALENDAR | Event-based |

### Long-Term (Months to Years)

| Strategy | Data Points | Timeframe |
|---|---|---|
| Value Investing | P/E, P/B, DCF, Free Cash Flow | 1-5 years |
| Growth Investing | Revenue growth, EPS trajectory, TAM | 1-3 years |
| Dividend Investing | Yield, Payout ratio, Dividend growth | 3-10 years |
| Macro Timing | GDP, CPI, Fed rates, Unemployment | 6-18 months |

## Event Risk Simulation (Multi-Horizon)

Regime-based event probability scoring for 6 event classes across 3 horizons.
See `.instructions/simulation-strategy.md` for full specification.

### Regime Classification Reference

| Regime | Key Indicators | Typical Market Condition |
|---|---|---|
| **Calm** | RSI 40-60, ADX <20, ATR <50th pctile, BB width <5% | Range-bound, low vol |
| **Trending** | ADX >25, aligned above/below SMAs, moderate vol | Directional move |
| **Stressed** | ATR >75th pctile, RSI extreme, BB width >8%, high volume | Elevated uncertainty |
| **Crash-Prone** | ATR >90th pctile, below both SMAs, Fragility >=3 | Multiple risk factors |

### Event Class Quick Reference

| Event | Definition | Key Drivers |
|---|---|---|
| Large Move | `|return| > 2.5 × daily ATR %` | ATR level, earnings proximity, Beta |
| Vol Spike | ATR rises above 90th percentile | ATR clustering, BB expansion, catalyst |
| Trend Reversal | Price crosses SMA50 opposite to trend | RSI extreme, ADX declining, MACD divergence |
| Earnings Reaction | Post-earnings gap >±5% | Prior reaction history, analyst dispersion, Beta |
| Liquidity Stress | Volume <50% avg OR impact ratio >2× | Ownership concentration, market cap, volume |
| Crash-Like Path | Drawdown >15% within horizon | Fragility >=4, CCRLO >=12, ATR extreme |

### Probability Bounds

- All event probabilities: clipped to [1%, 85%]
- Crash-like probability: capped at 35% (model humility)
- Regime probabilities: must sum to 1.0
- Scenario weights: must sum to 1.0
