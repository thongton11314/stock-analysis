---
name: short-term-analysis
description: >
  Generate short-term bearish/bullish trading signals using trend-break risk-off methodology.
  USE FOR: "short-term signal for [TICKER]", "trend-break analysis", "risk-off signal",
  "short-term prediction", "bearish setup", "is [TICKER] breaking down?", "fragility analysis",
  "correction risk assessment", "drawdown prediction", short-horizon trading signals.
  DO NOT USE FOR: generating full HTML reports (use report-generation skill), fixing reports
  (use report-fix skill), long-term fundamental analysis only.
---

# Short-Term Trading Analysis Skill

## Overview
Analyze a ticker for short-horizon bearish/bullish signals using the formalized Trend-Break Risk-Off
strategy. Combines technical trend breaks with volatility regime shifts and fragility indicators
to identify high-probability correction setups. Based on academic research on liquidity spirals,
leverage cycles, and information discontinuities.

**Strategy reference**: `strategies/short-term/short-term-strategy.md` (formal specification)
**Research reference**: `strategies/short-term/short-term-research-report.md` (theoretical framework)

## Workflow

### Phase 1: Data Collection
Follow the **data-collection skill** workflow (`.github/skills/data-collection/SKILL.md`),
but only the subset needed for short-term signals:

1. **Price data**:
   - `GLOBAL_QUOTE` — current price, OHLCV
   - `SMA` (interval=daily, time_period=200) — long-horizon trend proxy
   - `SMA` (interval=daily, time_period=50) — medium-term trend
   - `EMA` (interval=daily, time_period=12 AND time_period=26) — short-term trend

2. **Volatility & momentum**:
   - `RSI` (interval=daily, time_period=14) — overbought/oversold
   - `MACD` (interval=daily) — momentum crossovers
   - `BBANDS` (interval=daily, time_period=20) — squeeze/breakout
   - `ADX` (interval=daily, time_period=14) — trend strength
   - `ATR` (interval=daily, time_period=14) — volatility/stop sizing

3. **Fundamental context** (for fragility assessment):
   - `COMPANY_OVERVIEW` — Beta, P/E, debt ratios, analyst target
   - `BALANCE_SHEET` — leverage, cash position (most recent)
   - `NEWS_SENTIMENT` — catalyst/sentiment context

4. **Macro context** (for regime assessment):
   - `FEDERAL_FUNDS_RATE` — rate cycle direction
   - VIX proxy: use broad market RSI/ATR as volatility regime proxy

### Phase 2: Compute Trend-Break Indicators

Use the formalized strategy from `strategies/short-term/deep-research-report.md`:

#### Core Indicators (compute from fetched data)

```
MA_long = SMA(200)
MA_slope = MA_long_today - MA_long_20_days_ago  (positive = uptrend, negative = downtrend)

Trend Break (TB):
  TB = (Price <= 0.995 * MA_long) AND (MA_slope < 0)
  → Price is below 200-MA with buffer, AND the MA itself is declining

Volatility Shift (VS):
  VS = ATR_today > ATR_80th_percentile_of_last_252_days
  → Current volatility is in the top 20% of the past year
  (Proxy: if ATR/Price ratio is elevated vs recent history)

Volume Filter (VF):
  VF = Volume_today >= 1.0 * Average_Volume_20_days
  → Volume confirms activity (not a low-liquidity drift)
```

#### Entry Signal
```
ENTRY = TB AND VS AND VF
→ All three must be TRUE simultaneously
```

#### Exit Signals (any one triggers)
```
EXIT_STOP  = Price >= Entry_Price * 1.08    (8% adverse move)
EXIT_TIME  = Holding_Days >= 60             (time stop)
EXIT_TREND = Price >= MA_long               (trend recovery)
EXIT_VOL   = ATR < SMA(ATR, 20)            (volatility normalized)
```

### Phase 3: Fragility Stack Assessment

Score each fragility dimension (from research report):

| Dimension | Indicators | Signal |
|---|---|---|
| **Leverage/Funding** | Debt-to-Equity, Interest Coverage, Cash Burn | HIGH if D/E >2 or negative FCF |
| **Liquidity** | Bid-Ask spread, Volume vs avg, ATR expansion | HIGH if ATR >2x normal |
| **Information Risk** | Recent earnings misses, analyst dispersion, SBC distortion | HIGH if >2 consecutive misses |
| **Valuation Fragility** | P/E vs sector, P/S percentile, Forward PE gap | HIGH if >90th percentile P/E |
| **Momentum Breakdown** | Price below 50-MA AND 200-MA, RSI trend, MACD negative | HIGH if all bearish |

**Fragility Score**: Count of HIGH dimensions (0-5)
- 0-1: Low fragility (corrections unlikely to be severe)
- 2-3: Moderate fragility (standard correction risk)
- 4-5: High fragility (severe drawdown risk elevated)

### Phase 4: Generate Signal Output

Produce a structured signal assessment conforming to the **SHORT_TERM_SIGNAL** contract
in `.instructions/signal-contracts.md`. Can be standalone or integrated into Section 3
of a full report:

```
SHORT-TERM SIGNAL REPORT — [TICKER]
Date: [DATE]
Price: $[PRICE]

TREND-BREAK STATUS:
  MA(200): $[VALUE] — Price [ABOVE/BELOW] by [X]%
  MA Slope (20d): [POSITIVE/NEGATIVE] — Trend [INTACT/BREAKING]
  Trend Break: [YES/NO]

VOLATILITY REGIME:
  ATR(14): $[VALUE] — [X]% daily range
  ATR Percentile (1Y): [XX]th percentile
  Volatility Shift: [YES/NO]

ENTRY SIGNAL: [ACTIVE / NOT ACTIVE]
  TB: [✓/✗]  VS: [✓/✗]  VF: [✓/✗]

FRAGILITY STACK: [X/5] — [LOW/MODERATE/HIGH]
  Leverage:    [LOW/HIGH] — D/E [X], FCF [$X]
  Liquidity:   [LOW/HIGH] — ATR [X]x normal
  Info Risk:   [LOW/HIGH] — [X] recent misses
  Valuation:   [LOW/HIGH] — P/E [X] vs sector [Y]
  Momentum:    [LOW/HIGH] — Below 50-MA [✓/✗], 200-MA [✓/✗]

CORRECTION RISK ASSESSMENT:
  Mild (-10-15%):    [XX]% probability
  Standard (-20-30%): [XX]% probability
  Severe (-40-50%):  [XX]% probability
  Base: ATR vol + Beta adjustment + fragility score modifier

RECOMMENDED ACTION:
  [SIGNAL DESCRIPTION]
  Risk/Reward: [X:X]
  Stop-Loss: $[PRICE] ([X]% from current)
  Time Horizon: [X] trading days

COMPLIANCE NOTE:
  This analysis is for informational purposes only. Not investment advice.
  Any trading requires proper risk management, position sizing, and
  compliance with applicable regulations (Reg SHO, margin requirements).
```

### Phase 5: Integration with Full Report (Optional)

When generating a full stock analysis report AND short-term signals are active:

1. **Executive Summary (Section 3)**: Include the trend-break status and fragility score
   in the Short-Term Outlook column
2. **Technical Indicators (Section 11)**: Add a "Trend-Break Status" row showing TB/VS/VF
3. **Price Corridors (Section 5)**: Adjust correction probabilities upward if fragility score >= 3

## Position Sizing Rules (from research)

```
Risk Notional = (Risk_Budget × Account_Equity) / Stop_Loss_Distance
Max Leverage = 1.0x (conservative default)
Liquidity Cap = 5% of Average Daily Volume

Final Size = MIN(Risk_Notional, Leverage_Cap, Liquidity_Cap)
```

Defaults: Risk budget 1%, Stop 8%, Max holding 60 days.

## Critical Rules
1. **All three gates must fire** (TB + VS + VF) for a bearish signal — never act on one alone
2. **False positives are common** — the base rate for >30% corrections is low; report confidence levels
3. **Fragility score context is essential** — a trend break without fragility is often a buyable dip
4. **Always include compliance disclaimer** — this is analysis, not investment advice
5. **Stop-loss is non-negotiable** — every signal must include a defined exit level
6. **Integrate with fundamentals** — short-term signals should be read alongside the full report's long-term thesis
7. **Simulation uses fragility as input** — Fragility Score feeds into event risk simulation: crash-prone regime affinity (+15 if >=3) and crash-like event probability (+8 if >=4). See `.github/skills/simulation/SKILL.md` for details.
