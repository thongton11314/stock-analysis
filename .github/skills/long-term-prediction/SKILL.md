---
name: long-term-prediction
description: >
  Assess long-term market correction risk using the Composite Correction Risk Logit Overlay (CCRLO).
  USE FOR: "correction risk for [TICKER]", "long-term prediction", "market correction probability",
  "CCRLO analysis", "is a correction coming?", "macro risk assessment", "6-month outlook",
  "credit spread warning", "yield curve signal", long-horizon downside probability.
  DO NOT USE FOR: short-term trend-break signals (use short-term-analysis skill),
  generating full HTML reports (use report-generation skill).
---

# Long-Term Correction Prediction Skill — CCRLO

## Overview
Assess the probability of a >=10% market correction within a 6-month (126 trading day) forward
horizon using the Composite Correction Risk Logit Overlay (CCRLO) strategy. Based on peer-reviewed
research on credit spreads, term structure, volatility regimes, and financial conditions as
downside predictors.

**Strategy reference**: `strategies/long-term/long-term-strategy.md` (full specification with skill.md)

## Strategy Summary

**Model**: Regularized logistic regression (elastic net) with 7 macro-financial features
**Target**: Will a >=10% peak-to-trough drawdown occur within the next 126 trading days?
**Frequency**: Weekly decision, monthly model refit
**Reported skill**: AUROC ~0.70-0.88 across specifications in academic/institutional research

## Workflow

### Phase 1: Collect Macro-Financial Data

Follow the **data-collection skill** workflow (`.github/skills/data-collection/SKILL.md`),
focusing on the macro and market data subset:

Fetch via Alpha Vantage MCP + FRED proxies:

1. **Market data** (from Alpha Vantage):
   - `GLOBAL_QUOTE` — current index/stock price
   - `SMA` (interval=daily, time_period=200) — trend context
   - `ATR` (interval=daily, time_period=14) — realized volatility proxy
   - `RSI` (interval=daily, time_period=14) — momentum

2. **Macro indicators** (from Alpha Vantage):
   - `FEDERAL_FUNDS_RATE` — rate cycle (proxy for term structure)
   - `CPI` — inflation regime
   - `UNEMPLOYMENT` — labor market stress
   - `REAL_GDP` — economic growth

3. **Derived features** (compute from collected data):
   - **Term spread proxy**: Fed Funds trajectory (cutting = positive, hiking = negative)
   - **Credit risk proxy**: Use company-level D/E ratio + sector P/E as credit stress proxy
   - **Volatility regime**: ATR percentile vs 1-year history
   - **Financial conditions**: Composite of rate direction + unemployment trend + GDP growth
   - **Momentum (12-month)**: Price vs 52-week high/low positioning
   - **Realized volatility**: ATR/Price ratio over recent period

### Phase 2: Compute CCRLO Feature Vector

From the formal specification in the research document:

```
Features (7 inputs):
  x1: Term Spread Proxy
      = (Fed_Rate_6mo_ago - Fed_Rate_today)
      Positive = cutting cycle (easing), Negative = hiking (tightening)

  x2: Credit Risk Proxy (high-yield spread equivalent)
      = Company D/E ratio × sector average P/E distortion
      Or for index: avg sector leverage indicator

  x3: Investment-Grade Credit Proxy
      = If available from macro data; else use Fed Rate level as proxy
      Higher rate = tighter conditions

  x4: Implied Volatility Proxy
      = ATR / Price × 100 (annualized)
      Percentile rank vs 1-year history

  x5: Financial Conditions Composite
      = Weighted score of: rate direction + unemployment trend + GDP momentum
      Scale: -1 (very tight) to +1 (very loose)

  x6: Price Momentum (12-month)
      = (Current_Price / 52W_High) - 1
      Negative = drawdown from peak

  x7: Realized Volatility (13-week)
      = Annualized standard deviation of weekly returns proxy
      Or: ATR(14) × sqrt(252) / Price
```

### Phase 3: Compute Correction Probability

Since we cannot run a trained ML model in this context, use a **rule-based probability scoring**
that maps the CCRLO features into a correction probability estimate:

```
Score each feature on a 0-3 scale:

Term Spread:
  0 = Cutting >50bps (easing = low risk)
  1 = Flat/cutting <25bps
  2 = Hiking <50bps
  3 = Hiking >50bps or inverted yield curve

Credit Risk:
  0 = Low leverage, healthy sector
  1 = Moderate leverage
  2 = High leverage, widening stress
  3 = Crisis-level leverage/stress

Volatility Regime:
  0 = Below 25th percentile (calm)
  1 = 25th-50th percentile
  2 = 50th-75th percentile (elevated)
  3 = Above 75th percentile (stress)

Financial Conditions:
  0 = Very loose (rate cuts + low unemployment + growing GDP)
  1 = Moderately loose
  2 = Tightening
  3 = Very tight (hiking + rising unemployment + slowing GDP)

Momentum:
  0 = Within 5% of 52W high
  1 = 5-15% below 52W high
  2 = 15-30% below 52W high
  3 = >30% below 52W high (deep drawdown)

Realized Volatility:
  0 = Below historical average
  1 = Average to 1.5x average
  2 = 1.5x to 2x average
  3 = >2x average

GDP/Growth:
  0 = Growing >2%
  1 = Growing 1-2%
  2 = Growing 0-1%
  3 = Contracting (recession risk)

TOTAL SCORE = Sum of all 7 dimensions (0-21)

Correction Probability Mapping:
  Score 0-3:   5-10%   → LOW risk
  Score 4-7:   15-25%  → MODERATE risk
  Score 8-11:  30-45%  → ELEVATED risk
  Score 12-15: 50-65%  → HIGH risk
  Score 16-21: 70-85%  → VERY HIGH risk
```

### Phase 4: Generate Assessment Output

Produce a structured assessment conforming to the **CCRLO_SIGNAL** contract
in `.instructions/signal-contracts.md`.

```
LONG-TERM CORRECTION RISK ASSESSMENT — [TICKER/INDEX]
Model: Composite Correction Risk Logit Overlay (CCRLO)
Date: [DATE]
Horizon: 6 months (126 trading days)

MACRO-FINANCIAL FEATURE VECTOR:
  Term Spread:         [VALUE] → Score [0-3] — [Description]
  Credit Risk:         [VALUE] → Score [0-3] — [Description]
  Volatility Regime:   [VALUE] → Score [0-3] — [Description]
  Financial Conditions: [VALUE] → Score [0-3] — [Description]
  Momentum (12M):      [VALUE] → Score [0-3] — [Description]
  Realized Volatility: [VALUE] → Score [0-3] — [Description]
  GDP/Growth:          [VALUE] → Score [0-3] — [Description]

COMPOSITE SCORE: [X/21]
CORRECTION PROBABILITY (6-month): [XX]%
RISK LEVEL: [LOW / MODERATE / ELEVATED / HIGH / VERY HIGH]

DECISION FRAMEWORK:
  If LOW (0-10%):     Full equity exposure — stay invested
  If MODERATE (15-25%): Monitor weekly — prepare hedges
  If ELEVATED (30-45%): Reduce exposure to 80% — buy protective puts
  If HIGH (50-65%):    Reduce exposure to 50% — active hedging
  If VERY HIGH (70%+): Reduce exposure to 20% — maximum defensive

HISTORICAL CONTEXT:
  [Compare current score to known historical episodes]

DISCLAIMER:
  This is a probabilistic risk assessment based on macro-financial indicators.
  It is NOT investment advice. Backtests are hypothetical. Rare-event models
  can fail abruptly. Always consult a licensed financial advisor.
```

### Phase 5: Integration with Full Report

When generating a full stock analysis report:

1. **Executive Summary (Section 3)**: Add CCRLO score and 6-month correction probability
   to the Long-Term Outlook column
2. **Price Corridors (Section 5)**: Use CCRLO risk level to calibrate corridor width
   - LOW: tighter corridors (±20% from average)
   - HIGH: wider corridors (±40% from average)
3. **Macro Dashboard (Section 15)**: Show CCRLO feature scores alongside macro indicators
4. **Net Macro Scorecard (Section 18)**: Include CCRLO as a composite risk factor tile

## Critical Rules
1. **All 7 features must be scored** — never skip a dimension
2. **Use only backward-looking data** — no future information leakage
3. **Simulation uses CCRLO as input** — CCRLO score feeds into event risk simulation: crash-like event probability (+5 if >=12) and tail risk scenario weighting. High CCRLO increases crash-prone regime affinity. See `.github/skills/simulation/SKILL.md` for details.
3. **Probability is an estimate, not a prediction** — always communicate uncertainty
4. **Rate cycle is the #1 predictor** — weight term spread/credit signals heavily
5. **Combine with short-term skill** for comprehensive view (CCRLO = strategic, trend-break = tactical)
6. **Always include disclaimer** — this is informational, not investment advice
7. **Score calibration is approximate** — the rule-based scoring is a proxy for the trained logistic model described in the research
