---
name: simulation
description: >
  Estimate event probabilities and simulate forward scenarios for a stock ticker using
  regime detection, multi-horizon event scoring, and scenario-weighted analysis.
  USE FOR: "simulate events for [TICKER]", "event risk for [TICKER]", "regime analysis",
  "what could happen to [TICKER]", "scenario simulation", "event probability", "risk simulation",
  "forward scenarios", "regime detection", "crash probability", "volatility forecast",
  "liquidity risk assessment", "earnings gap risk".
  DO NOT USE FOR: generating full HTML reports (use report-generation skill), fixing reports
  (use report-fix skill), standalone short-term signals only (use short-term-analysis skill),
  standalone CCRLO only (use long-term-prediction skill).
---

# Event Risk Simulation Skill

## Overview

Estimate the probability of financially significant events for a stock ticker by combining
regime detection, event scoring, and scenario simulation — all computed inline from
Alpha Vantage MCP data already collected for standard reports.

This skill produces:
- **Market regime classification** (Calm / Trending / Stressed / Crash-Prone)
- **Event probabilities** across 6 event classes at multiple horizons (5d, 10d, 20d)
- **Scenario-weighted forward outlook** with 4 named scenarios and probability weights
- **Top risk drivers** and confidence assessment
- **Structured output** for standalone use or integration into HTML reports

**Theory reference**: `AI_Ticker_Event_Research.md` (full research framework — in this folder)
**Short-term reference**: `.instructions/short-term-strategy.md` (TB/VS/VF + Fragility)
**Long-term reference**: `.instructions/long-term-strategy.md` (CCRLO)
**Simulation detail**: `.instructions/simulation-strategy.md` (full computation tables)

---

## Workflow

### Phase 1: Data Collection

Use the SAME Alpha Vantage MCP data already collected per the **data-collection skill**
(`.github/skills/data-collection/SKILL.md`). No additional API calls are needed beyond
the standard 15 data points + macro + peers.

**Required data (already fetched in standard workflow):**

| Data | Tool | Used For |
|---|---|---|
| Current price, OHLCV | `GLOBAL_QUOTE` | Regime features, event baselines |
| Company fundamentals | `COMPANY_OVERVIEW` | Beta, P/E, sector, analyst target, 52W range |
| Balance sheet | `BALANCE_SHEET` | Leverage (D/E), cash position |
| Cash flow | `CASH_FLOW` | FCF, operating CF |
| Earnings history | `EARNINGS` | Surprise history, earnings proximity |
| RSI (14-day) | `RSI` | Momentum regime |
| MACD | `MACD` | Trend momentum |
| Bollinger Bands | `BBANDS` | Squeeze / breakout detection |
| SMA (50/200) | `SMA` | Trend state |
| EMA (12/26) | `EMA` | Short-term trend |
| ADX (14-day) | `ADX` | Trend strength |
| ATR (14-day) | `ATR` | Volatility regime |
| News sentiment | `NEWS_SENTIMENT` | Catalyst detection |
| Institutional holdings | `INSTITUTIONAL_HOLDINGS` | Ownership concentration |
| Macro indicators | `CPI`, `FEDERAL_FUNDS_RATE`, `UNEMPLOYMENT`, `REAL_GDP` | Macro regime |

### Phase 2: Regime Detection

Classify the current market regime using a rule-based state model.
Four regimes, scored by probability (must sum to 1.0).

#### Regime Feature Extraction

```
Features (from collected data):
  RSI_14          = RSI value (0-100)
  ADX_14          = ADX value (trend strength)
  ATR_pctile      = ATR percentile vs 1-year history (0-100)
  ATR_ratio       = ATR_today / SMA(ATR, 50-day)
  MACD_histogram  = MACD histogram value (positive = bullish momentum)
  BB_width        = (Upper_BB - Lower_BB) / Middle_BB × 100
  Price_vs_SMA200 = (Price - SMA_200) / SMA_200 × 100
  Price_vs_SMA50  = (Price - SMA_50) / SMA_50 × 100
  Volume_ratio    = Volume_today / Average_Volume_20d
  Beta            = from COMPANY_OVERVIEW
```

#### Regime Classification Rules

Score each regime on a 0-100 affinity scale, then normalize to probabilities:

**CALM regime affinity:**
```
calm_score = 0
+30 if RSI between 40-60
+25 if ADX < 20 (no strong trend)
+20 if ATR_pctile < 50 (below-median volatility)
+15 if BB_width < 5% (tight bands = low vol)
+10 if Volume_ratio between 0.7-1.3 (normal volume)
```

**TRENDING regime affinity:**
```
trend_score = 0
+30 if ADX > 25 (strong trend)
+25 if |Price_vs_SMA200| > 5% (clear trend displacement)
+20 if Price_vs_SMA50 and Price_vs_SMA200 same sign (aligned trend)
+15 if MACD_histogram consistently positive or negative (3+ days)
+10 if ATR_pctile between 30-70 (moderate, not extreme vol)
```

**STRESSED regime affinity:**
```
stress_score = 0
+30 if ATR_pctile > 75 (elevated volatility)
+25 if RSI < 30 or RSI > 70 (extreme reading)
+20 if BB_width > 8% (expanded bands)
+15 if Volume_ratio > 1.5 (above-average volume)
+10 if |Price_vs_SMA200| > 10% (stretched from mean)
```

**CRASH-PRONE regime affinity:**
```
crash_score = 0
+25 if ATR_pctile > 90 (extreme volatility)
+25 if Price_vs_SMA200 < -5% AND Price_vs_SMA50 < -3% (below both MAs)
+20 if RSI < 30 (oversold)
+15 if MACD_histogram < 0 AND declining
+15 if Fragility_Score >= 3 (from TB/VS/VF computation)
```

**Normalize to probabilities:**
```
total = calm_score + trend_score + stress_score + crash_score
If total == 0: default to calm=0.50, trend=0.25, stress=0.15, crash=0.10

regime_probs = {
  calm:       calm_score / total,
  trend:      trend_score / total,
  stress:     stress_score / total,
  crash_prone: crash_score / total
}
```

### Phase 3: Event Probability Scoring

Score 6 event classes at 3 horizons (5d, 10d, 20d). Each event has a base probability
that is regime-adjusted and feature-modified.

#### Event 1: Large Price Move

Definition: `|return over horizon| > 2.5 × daily ATR as % of price`

```
Base probability by horizon:
  5d:  12%
  10d: 18%
  20d: 25%

Adjustments (additive):
  +8%  if ATR_pctile > 75
  +5%  if earnings within horizon window
  +5%  if Beta > 1.5
  +3%  if RSI < 25 or RSI > 75
  +3%  if Volume_ratio > 2.0
  -5%  if ADX < 15 (no trend = range-bound)
  -3%  if regime_probs.calm > 0.50

Regime weighting:
  final = base × (1 + 0.3 × stress_prob + 0.6 × crash_prob - 0.2 × calm_prob)
```

#### Event 2: Volatility Spike

Definition: ATR rises to above 90th percentile within horizon

```
Base probability by horizon:
  5d:  8%
  10d: 15%
  20d: 22%

Adjustments:
  +10% if ATR_pctile already > 60 (vol clustering)
  +8%  if earnings within horizon
  +5%  if BB_width expanding (current > 5d-ago)
  +3%  if news_sentiment score < -0.3 (negative catalyst)
  -5%  if ATR_pctile < 30 (calm baseline)
  -3%  if ADX > 25 AND trend stable (orderly trend)
```

#### Event 3: Trend Reversal

Definition: Price crosses SMA_50 in opposite direction of current trend within horizon

```
Base probability by horizon:
  5d:  6%
  10d: 12%
  20d: 20%

Adjustments:
  +8%  if RSI > 70 (overbought → reversal risk) or RSI < 30 (oversold → bounce risk)
  +5%  if ADX declining from > 30 (trend exhaustion)
  +5%  if MACD histogram diverging from price (momentum divergence)
  +3%  if Price near SMA_50 (within 2%)
  -5%  if ADX > 35 AND rising (strong accelerating trend)
  -3%  if price far from SMA_50 (>8% away)
```

#### Event 4: Earnings Reaction (>5% gap)

Definition: Post-earnings move exceeds ±5% within 2 sessions

```
Base probability (applicable only if earnings within horizon):
  If no earnings in horizon: probability = 2% (spillover/peer reaction only)
  If earnings within horizon: base = 20%

Adjustments:
  +10% if prior 2 earnings had >5% moves (reactive stock)
  +8%  if Beta > 1.5
  +5%  if analyst dispersion is high (52W target range > 2× current price)
  +5%  if ATR_pctile > 60 (already volatile)
  -5%  if prior 4 earnings all had <3% moves (stable reactor)
  -3%  if analyst coverage > 30 (well-understood company)
```

#### Event 5: Liquidity Stress

Definition: Volume drops below 50% of 20d average OR ATR/Volume ratio spikes >2× normal

```
Base probability by horizon:
  5d:  5%
  10d: 8%
  20d: 12%

Adjustments:
  +8%  if institutional_ownership > 80% (crowded)
  +5%  if market_cap < $2B (small-cap liquidity risk)
  +5%  if Volume_ratio < 0.5 (already thin)
  +3%  if recent news_sentiment strongly negative
  -5%  if market_cap > $100B (deep liquidity)
  -3%  if Volume_ratio > 1.2 (healthy participation)
```

#### Event 6: Crash-Like Path

Definition: Peak-to-trough drawdown > 15% within horizon

```
Base probability by horizon:
  5d:  2%
  10d: 4%
  20d: 7%

Adjustments:
  +8%  if Fragility_Score >= 4
  +5%  if CCRLO_score >= 12 (HIGH correction risk)
  +5%  if ATR_pctile > 85
  +3%  if Price_vs_SMA200 < -10% (already in downtrend)
  +3%  if D/E > 3.0 (extreme leverage)
  -3%  if regime_probs.calm > 0.50
  -3%  if CCRLO_score < 4 (LOW macro risk)

All crash probabilities capped at 35% (model humility for rare events).
```

#### Probability Bounds

All event probabilities are clipped to [1%, 85%] range.
Events with <5% base + adjustments are reported as "LOW" with exact number.

### Phase 4: Scenario Weighting

Construct 4 named scenarios with weights derived from regime and event probabilities.

#### Scenario 1: Base Case (Regime Continuation)
```
weight = regime_probs.calm + 0.5 × regime_probs.trend
(ranges ~0.30-0.70 depending on regime)

Description: Current regime persists. Moderate volatility, no major catalyst.
Expected return: Near analyst consensus drift (annualized target / 12 × horizon_months)
Expected vol: Current ATR level ± 10%
Price range: Current ± (ATR × √horizon × 0.5)
```

#### Scenario 2: Volatility Expansion
```
weight = 0.5 × regime_probs.stress + 0.3 × regime_probs.crash_prone
(ranges ~0.10-0.35)

Description: Volatility regime shifts upward. ATR expands 1.5-2×.
Expected return: -1× to -3× daily ATR over horizon
Expected vol: 1.5× current level
Price range: (Current - 3×ATR×√horizon) to (Current + ATR×√horizon)
Trigger: Macro surprise, earnings miss, sector contagion
```

#### Scenario 3: Trend Acceleration / Reversal
```
weight = 0.5 × regime_probs.trend + 0.2 × regime_probs.stress
(ranges ~0.10-0.30)

Description: Current trend accelerates OR reverses sharply.
Direction depends on: ADX direction, MACD crossover proximity, RSI extreme
Expected return: ±2× daily ATR × sqrt(horizon_days)
Expected vol: 1.2× current level
Price range: (Current - 2×ATR×√horizon) to SMA_50 (if above) or (Current - 3×ATR×√horizon)
```

#### Scenario 4: Tail Risk / Dislocation
```
weight = regime_probs.crash_prone + 0.3 × regime_probs.stress
(ranges ~0.05-0.25)

Description: Sharp drawdown with liquidity deterioration.
Expected return: -(5-15)% over horizon
Expected vol: 2-3× current level
Price range: (Current × 0.85) to (Current × 0.95)
Trigger: Liquidity shock, earnings disaster, macro crisis, forced selling
```

**Weight normalization**: Ensure all 4 weights sum to 1.0.

### Phase 4b: Scenario Price Range Computation

For each scenario, compute the expected price range at the 20d horizon using
ATR-based volatility scaling with asymmetric multipliers:

```
ATR_daily = ATR(14) value from Alpha Vantage
horizon = 20 (trading days)
ATR_h = ATR_daily × sqrt(horizon) ≈ ATR_daily × 4.47

Base Case:
  range_low  = Current - ATR_h × 0.10
  range_high = Current + ATR_h × 0.10
  midpoint   = Current × (1 + analyst_drift_20d)  (typically ±1%)

Vol Expansion (asymmetric — downside biased):
  range_low  = Current - ATR_h × 0.55
  range_high = Current + ATR_h × 0.22
  midpoint   = (range_low + range_high) / 2

Trend Shift (wide, symmetric):
  range_low  = Current - ATR_h × 0.68
  range_high = min(SMA_50, Current + ATR_h × 0.65)
  midpoint   = (range_low + range_high) / 2

Tail Risk (downside only):
  range_low  = Current × (1 - 0.15 × Beta/1.5)  (Beta-scaled 15% drawdown)
  range_high = Current × (1 - 0.03)              (minimum 3% loss)
  midpoint   = (range_low + range_high) / 2
```

**Note**: All multipliers are calibrated so that TSLA (ATR=$13.25, Beta=1.93) produces
reasonable institutional-quality ranges. For lower-beta stocks, ranges will be tighter.

### Phase 4c: Weighted Expected Price & Confidence Range

```
For each scenario, midpoint = (range_low + range_high) / 2
  (Exception: Base Case midpoint uses analyst drift instead of range mean)

Weighted_Expected_Price = Σ (scenario_weight_i × scenario_midpoint_i)

For 80% confidence range:
  CI_low  = Σ (scenario_weight_i × scenario_range_low_i)
  CI_high = Σ (scenario_weight_i × scenario_range_high_i)

Downside_Skew = probability that 20d return < 0
  = (vol_expansion_weight × 0.7) + tail_risk_weight + (trend_shift_weight × 0.5)
  Clip to [20%, 85%]
```

### Phase 4d: Event Price Impact

For each event class, compute the price range if that event occurs:

```
Large Move:     Current ± (2.5 × ATR_daily × √horizon_factor)
Vol Spike:      Current ± (ATR_daily × 1.5 × √horizon)  (wider range due to vol expansion)
Trend Reversal: SMA_50 target (upside) or Current - 2×ATR×√horizon (downside)
Earnings React: Current ± (implied_move or 5% × Current)
Liquidity:      Current × (0.95 to 0.99)  (gap down bias)
Crash Path:     < Current × 0.85
```

### Phase 5: Confidence & Disagreement Assessment

#### Model Disagreement Score (0.0 - 1.0)

Measures how much the regime model, event models, and scenario weights conflict:

```
disagreement = 0.0

+0.15 if regime_probs has no dominant state (max < 0.40)
+0.15 if TB signal and CCRLO signal contradict (TB bearish but CCRLO LOW, or vice versa)
+0.10 if RSI and MACD give opposite signals
+0.10 if news_sentiment contradicts technical signals
+0.10 if ATR regime and ADX regime conflict (high vol but strong trend)
+0.10 if analyst consensus direction conflicts with momentum direction
+0.05 if Price near SMA_200 (ambiguous trend state)
+0.05 if fragility dimensions split (2 HIGH, 3 LOW — mixed picture)

Cap at 0.80.
```

#### Confidence Assessment

```
If disagreement < 0.15: "HIGH" confidence
If disagreement 0.15-0.30: "MODERATE-HIGH" confidence
If disagreement 0.30-0.50: "MODERATE" confidence
If disagreement 0.50-0.65: "LOW-MODERATE" confidence
If disagreement > 0.65: "LOW" confidence
```

### Phase 6: Identify Top Risk Drivers

Select the top 3-5 risk drivers by contribution to event probabilities:

```
Candidate drivers (rank by adjustment magnitude contributed):
- "Elevated implied volatility" (if ATR_pctile > 70)
- "Earnings proximity" (if earnings within 20d)
- "High beta amplification" (if Beta > 1.5)
- "Negative momentum regime" (if Price below both SMAs)
- "Leverage fragility" (if D/E > 2.0)
- "Liquidity thinning" (if Volume_ratio < 0.7)
- "Macro tightening pressure" (if CCRLO_score >= 8)
- "Trend exhaustion signal" (if ADX declining from >30)
- "Overbought/oversold extreme" (if RSI < 25 or RSI > 75)
- "Negative news catalyst" (if sentiment score < -0.3)
- "Crowded institutional ownership" (if inst_ownership > 80%)
- "Small-cap liquidity risk" (if market_cap < $2B)
```

---

## Output Format

### Standalone Output (when invoked directly)

```
EVENT RISK SIMULATION — [TICKER]
Date: [DATE]
Price: $[PRICE]

═══════════════════════════════════════════
MARKET REGIME
═══════════════════════════════════════════
  Calm:        [XX]%  [████░░░░░░]
  Trending:    [XX]%  [██████░░░░]
  Stressed:    [XX]%  [███░░░░░░░]
  Crash-Prone: [XX]%  [█░░░░░░░░░]
  → Dominant: [REGIME_NAME]

═══════════════════════════════════════════
EVENT PROBABILITIES
═══════════════════════════════════════════
                          5d      10d     20d
  Large Move (>2.5σ):    [XX]%   [XX]%   [XX]%
  Volatility Spike:      [XX]%   [XX]%   [XX]%
  Trend Reversal:        [XX]%   [XX]%   [XX]%
  Earnings Reaction:     [XX]%   [XX]%   [XX]%
  Liquidity Stress:      [XX]%   [XX]%   [XX]%
  Crash-Like Path:       [XX]%   [XX]%   [XX]%

═══════════════════════════════════════════
SCENARIO OUTLOOK
═══════════════════════════════════════════
  [1] Base Case          — Weight: [XX]%
      [Description]
  [2] Vol Expansion      — Weight: [XX]%
      [Description]
  [3] Trend Shift        — Weight: [XX]%
      [Description]
  [4] Tail Risk          — Weight: [XX]%
      [Description]

═══════════════════════════════════════════
TOP RISK DRIVERS
═══════════════════════════════════════════
  1. [Driver description]
  2. [Driver description]
  3. [Driver description]

MODEL CONFIDENCE: [HIGH/MODERATE/LOW] (disagreement: [X.XX])

DISCLAIMER:
  Probabilistic estimates based on rule-based regime detection and
  historical feature scoring. Not investment advice. Event probabilities
  are calibrated approximations, not precise forecasts.
```

### JSON-Equivalent Schema (for report integration)

Output must conform to the **SIMULATION_SIGNAL** contract in `.instructions/signal-contracts.md`.
Below is an example JSON representation:

```json
{
  "ticker": "AAPL",
  "as_of": "2026-03-20",
  "regime_probabilities": {
    "calm": 0.20,
    "trending": 0.35,
    "stressed": 0.30,
    "crash_prone": 0.15
  },
  "dominant_regime": "trending",
  "events": {
    "large_move_5d":      { "probability": 0.24, "interval": [0.19, 0.30] },
    "large_move_10d":     { "probability": 0.31, "interval": [0.25, 0.38] },
    "large_move_20d":     { "probability": 0.38, "interval": [0.31, 0.46] },
    "vol_spike_5d":       { "probability": 0.15, "interval": [0.10, 0.21] },
    "vol_spike_10d":      { "probability": 0.22, "interval": [0.16, 0.29] },
    "vol_spike_20d":      { "probability": 0.30, "interval": [0.23, 0.38] },
    "trend_reversal_5d":  { "probability": 0.08, "interval": [0.04, 0.13] },
    "trend_reversal_10d": { "probability": 0.15, "interval": [0.10, 0.21] },
    "trend_reversal_20d": { "probability": 0.23, "interval": [0.17, 0.30] },
    "earnings_reaction":  { "probability": 0.25, "interval": [0.18, 0.33] },
    "liquidity_stress_5d":  { "probability": 0.08, "interval": [0.04, 0.13] },
    "liquidity_stress_10d": { "probability": 0.11, "interval": [0.07, 0.17] },
    "liquidity_stress_20d": { "probability": 0.15, "interval": [0.10, 0.21] },
    "crash_like_20d":     { "probability": 0.05, "interval": [0.02, 0.09] }
  },
  "top_drivers": [
    "elevated implied volatility",
    "negative peer spillover",
    "earnings within 12 sessions"
  ],
  "scenarios": [
    { "name": "base_case",         "weight": 0.55, "description": "..." },
    { "name": "vol_expansion",     "weight": 0.20, "description": "..." },
    { "name": "trend_shift",       "weight": 0.15, "description": "..." },
    { "name": "tail_risk",         "weight": 0.10, "description": "..." }
  ],
  "model_disagreement": 0.22,
  "confidence": "MODERATE"
}
```

---

## Confidence Interval Calculation

For each event probability `p`, compute approximate intervals:

```
Standard error proxy: se = sqrt(p × (1 - p) / effective_sample)
where effective_sample = 50 (conservative assumption for rule-based scoring)

interval_low  = max(0.01, p - 1.5 × se)
interval_high = min(0.85, p + 1.5 × se)
```

This gives approximate 80% credible intervals. Wider intervals indicate less certainty.

---

## Integration with Full Report

When generating a full stock analysis HTML report, simulation results feed into
existing sections plus a dedicated visualization card:

### Section 3 — Executive Summary
Add a **"Market Regime"** indicator showing the dominant regime with probability bar.
Include top 2 event probabilities by magnitude in the Short-Term Outlook.

```html
<li><strong>Market Regime:</strong>
  <span class="signal neutral">TRENDING (42%)</span>
  <br><span class="signal-desc">Moderate trend with 28% stress probability.
  Largest near-term risk: Vol Spike 20d at 30%</span></li>
```

### Section 5 — Price Corridors
Use simulation scenario weights to **calibrate correction probabilities**:
- Mild correction base × (1 + tail_risk_weight)
- Standard correction base × (1 + 2 × tail_risk_weight)
- Severe correction base × (1 + 3 × tail_risk_weight)

### Section 11 — Technical Indicators
Add Market Regime and Event Risk (20d) as tiles in Row 3 of the Technical Indicators section:

| Tile | Background | Content |
|---|---|---|
| **Market Regime** | `#f0fdf4` (green border) | Dominant regime + `.regime-bar` probability breakdown |
| **Event Risk (20d)** | `#fffbeb` (amber border) | Top 3 event probabilities with signal badges |

### Section 12 — Event Risk Simulation Visualization (DEDICATED CARD)

Full-width card placed **between Section 11 and Section 13**. Uses `.sim-grid` flexbox layout.

**Left panel** (`.sim-panel`):
- **Regime Detection**: 4 horizontal bars (`.regime-row`) showing regime probabilities
  with colored fills and percentage labels. Dominant regime highlighted with a callout box.
- **Scenario Price Targets (20-Day)**: Table with columns: Scenario | Weight | Price Range | Expected P/L.
  Each scenario shows the computed price range from Phase 4b.
- **Weighted Expected Price**: Prominent callout showing the probability-weighted expected
  price at 20d with percentage change from current. Adjacent: 80% confidence range.

**Right panel** (`.sim-panel`, flex: 1.5):
- **Event Probability & Price Impact Heatmap**: 6-row × 5-column table:
  Event | 5d | 10d | 20d probability cells + **Price Impact** column showing the dollar
  range if that event occurs, computed from Phase 4d.
- **Legend row**: Shows all 4 heatmap color levels.
- **Metrics tiles**: Model Disagreement, Confidence, Composite Risk (20d), **Downside Skew**.

This is a **sub-section** (like Section 10 Income Statement Breakdown), not a new top-level section.

### Section 13 — Key Risks & Catalysts
Add simulation-derived **scenario risk narratives** to the risk factors list:
- If vol_expansion weight > 0.25: flag "Volatility regime shift" as a risk
- If tail_risk weight > 0.15: flag "Tail risk dislocation" as a risk
- If liquidity_stress_20d > 0.15: flag "Liquidity deterioration" as a risk

### Section 18 — Net Macro Scorecard
Add an **"Event Risk"** tile showing:
- Composite event risk level (average of top 3 20d event probabilities)
- Color: GREEN if <15%, AMBER if 15-30%, RED if >30%
- Label: TAILWIND (low risk) / NEUTRAL / HEADWIND (high risk)

---

## Relationship to Existing Signals

Simulation builds ON TOP of existing signal systems — it does not replace them:

| Existing System | What It Does | What Simulation Adds |
|---|---|---|
| **TB/VS/VF + Fragility** | Binary trend-break gates + severity score | Regime context, event-type decomposition, confidence intervals |
| **CCRLO (0-21)** | 6-month macro correction probability | Scenario weighting, shorter horizons (5d/10d), event-specific probabilities |
| **Price corridor chart** | Visual scenario paths | Simulation-calibrated correction probabilities + regime-adjusted paths |

The simulation skill USES fragility score and CCRLO score as inputs to its own models (they are
features in the crash-prone regime affinity and crash-like event scoring).

---

## Critical Rules

1. **Data reuse**: Never make additional Alpha Vantage calls — use data already collected
2. **Regime probabilities must sum to 1.0** — always normalize
3. **All event probabilities clipped to [1%, 85%]** — avoid overconfident extremes
4. **Crash probability capped at 35%** — model humility for rare events
5. **Scenario weights must sum to 1.0** — always normalize
6. **Include confidence interval for every event probability** — never report bare point estimates
7. **Integrate, don't duplicate**: Simulation enhances existing sections; it does not create a new standalone report section
8. **Disagreement transparency**: Always report model disagreement score; if >0.50, flag explicitly
9. **Disclaimer required**: Always state that probabilities are rule-based approximations
10. **Fragility and CCRLO are inputs**: Use them as features; do not recompute them inside simulation
