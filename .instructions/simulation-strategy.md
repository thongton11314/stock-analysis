# Event Risk Simulation — Strategy & Methodology

## Overview

The Event Risk Simulation system estimates probabilities for 6 financially significant event
classes across multiple horizons (5d, 10d, 20d) by combining regime detection, rule-based
event scoring, and scenario weighting. It operates entirely on data already collected from
Alpha Vantage MCP during standard report generation.

**Skill file**: `.github/skills/simulation/SKILL.md`
**Research reference**: `.github/skills/simulation/AI_Ticker_Event_Research.md`

---

## Theoretical Foundation

This system is a simplified but practical implementation of the hybrid probabilistic event
architecture described in `AI_Ticker_Event_Research.md`. The research framework recommends:

1. **Prediction layer** → implemented as rule-based event scoring with regime conditioning
2. **Simulation layer** → implemented as scenario weighting with probability adjustments
3. **Strategy layer** → implemented as fragility/CCRLO inputs and crowding/liquidity risk factors

The key simplification: instead of trained ML models (HMM, Bayesian logistic, GARCH), the
system uses rule-based scoring tables that approximate the same signal structure using the
same features. This is appropriate because:
- The agent operates without a Python ML runtime
- Alpha Vantage provides pre-computed technical indicators
- Rule-based scoring is transparent and auditable
- The scoring tables are calibrated from the same research literature

---

## Regime Detection — Detailed Specification

### Why Regimes Matter

Financial markets exhibit non-stationary behavior. The probability of a 5% drawdown is
fundamentally different in a calm vs stressed regime. Regime detection conditions all
downstream event probabilities and scenario weights.

### Four-State Model

| Regime | Description | Typical Duration | Example Conditions |
|---|---|---|---|
| **Calm** | Low volatility, range-bound, no strong trend | Weeks to months | VIX <15, RSI 40-60, ADX <20 |
| **Trending** | Directional move with moderate volatility | Weeks to months | ADX >25, consistent above/below SMAs |
| **Stressed** | Elevated volatility, extreme indicators | Days to weeks | ATR >75th pctile, RSI extreme, high volume |
| **Crash-Prone** | Multiple risk factors aligned for severe drawdown | Days | ATR >90th pctile, below both SMAs, fragility >= 3 |

### Feature Extraction from Alpha Vantage Data

All features are computed from data already collected in the standard report workflow:

| Feature | Source | Computation |
|---|---|---|
| `RSI_14` | `RSI` tool (daily, 14-period) | Direct value |
| `ADX_14` | `ADX` tool (daily, 14-period) | Direct value |
| `ATR_pctile` | `ATR` tool (daily, 14-period) | Rank today's ATR vs last 252 values → percentile |
| `ATR_ratio` | `ATR` tool | Today's ATR / average of last 50 ATR values |
| `MACD_histogram` | `MACD` tool | MACD - Signal line |
| `BB_width` | `BBANDS` tool (daily, 20-period) | (Upper - Lower) / Middle × 100 |
| `Price_vs_SMA200` | `SMA` tool (200-period) | (Price - SMA200) / SMA200 × 100 |
| `Price_vs_SMA50` | `SMA` tool (50-period) | (Price - SMA50) / SMA50 × 100 |
| `Volume_ratio` | `GLOBAL_QUOTE` + historical avg | Today volume / 20-day average volume |
| `Beta` | `COMPANY_OVERVIEW` | Direct value |

### Scoring Tables

See Skill.md Phase 2 for the complete scoring rules. Summary:

| Feature Condition | Calm | Trending | Stressed | Crash-Prone |
|---|---|---|---|---|
| RSI 40-60 | +30 | 0 | 0 | 0 |
| RSI <30 or >70 | 0 | 0 | +25 | +20 (if <30) |
| ADX <20 | +25 | 0 | 0 | 0 |
| ADX >25 | 0 | +30 | 0 | 0 |
| ATR pctile <50 | +20 | 0 | 0 | 0 |
| ATR pctile >75 | 0 | 0 | +30 | 0 |
| ATR pctile >90 | 0 | 0 | +30 | +25 |
| Below both SMAs | 0 | 0 | 0 | +25 |
| BB width <5% | +15 | 0 | 0 | 0 |
| BB width >8% | 0 | 0 | +20 | 0 |
| Fragility >=3 | 0 | 0 | 0 | +15 |

---

## Event Probability Scoring — Detailed Specification

### Event Class Definitions

| # | Event | Definition | Measurement |
|---|---|---|---|
| 1 | Large Move | `|return| > 2.5 × daily ATR %` | Absolute return over horizon |
| 2 | Vol Spike | ATR rises above 90th percentile | ATR percentile shift |
| 3 | Trend Reversal | Price crosses SMA50 opposite to trend | SMA50 crossover |
| 4 | Earnings Reaction | Post-earnings gap > ±5% | 2-day post-earnings return |
| 5 | Liquidity Stress | Volume <50% avg OR ATR/Vol ratio >2× | Volume + price impact proxy |
| 6 | Crash Path | Drawdown >15% within horizon | Peak-to-trough within window |

### Base Probability Calibration

Base rates are calibrated from historical equity market frequencies:

| Event | 5d Base | 10d Base | 20d Base | Source |
|---|---|---|---|---|
| Large Move | 12% | 18% | 25% | Empirical: ~20% of 20d windows have >2σ moves |
| Vol Spike | 8% | 15% | 22% | Vol clustering: elevated states persist ~15-25% of time |
| Trend Reversal | 6% | 12% | 20% | MA crossovers: ~quarterly frequency for SMA50 |
| Earnings Reaction | — | — | 20% | ~25-30% of S&P stocks gap >5% on earnings |
| Liquidity Stress | 5% | 8% | 12% | Illiquidity events: ~10-15% of time for mid/small-cap |
| Crash Path (>15%) | 2% | 4% | 7% | ~3-5% annual crash frequency → 7% per 20d window |

### Adjustment Table

See Skill.md Phase 3 for complete adjustment rules per event class.

**Earnings Proximity Adjustment** (implemented in Python scripts):
- If next earnings date is within 5 trading days: `earnings_reaction` probability +15%
- If next earnings date is within 10 trading days: `earnings_reaction` probability +10%
- Earnings proximity is estimated from the quarterly earnings date pattern in the data bundle

### Regime Conditioning

Final probabilities are regime-weighted:
```
final_prob = adjusted_base × regime_multiplier

Where regime_multiplier for each event varies:
  Large Move:    calm ×0.8, trending ×1.0, stressed ×1.3, crash ×1.6
  Vol Spike:     calm ×0.7, trending ×0.9, stressed ×1.4, crash ×1.8
  Trend Reversal: calm ×1.0, trending ×0.8, stressed ×1.2, crash ×1.5
  Earnings React: calm ×0.9, trending ×1.0, stressed ×1.3, crash ×1.5
  Liquidity:     calm ×0.6, trending ×0.8, stressed ×1.5, crash ×2.0
  Crash Path:    calm ×0.5, trending ×0.7, stressed ×1.5, crash ×2.5

regime_multiplier = Σ (regime_prob_i × multiplier_i) for all 4 regimes
```

---

## Scenario Framework — Detailed Specification

### Scenario Construction

Each scenario represents a plausible forward path with associated probability weight.

| Scenario | Weight Formula | Return Expectation | Vol Expectation |
|---|---|---|---|
| Base Case | `calm + 0.5 × trend` | Consensus drift | Current ATR ±10% |
| Vol Expansion | `0.5 × stress + 0.3 × crash` | -1× to -3× daily ATR | 1.5× current |
| Trend Shift | `0.5 × trend + 0.2 × stress` | ±2× ATR × √horizon | 1.2× current |
| Tail Risk | `crash + 0.3 × stress` | -(5-15)% | 2-3× current |

### Scenario Narratives

The agent should generate scenario-specific narratives based on the ticker's context:

**Base Case example**: "AAPL continues current range-bound trading with moderate volatility.
No major catalyst expected. Consensus price drift of +0.5% per month."

**Vol Expansion example**: "Volatility expands from current 25th percentile to above 75th.
Potential trigger: CPI surprise, sector rotation, or earnings preannouncement."

**Trend Shift example**: "Current uptrend exhausts as ADX declines. RSI mean-reversion
from overbought levels. Price tests SMA50 support."

**Tail Risk example**: "Sharp drawdown driven by macro shock or liquidity withdrawal.
Fragility score of 3+ amplifies selling pressure. Institutional de-risking accelerates."

---

## Integration with Existing Signal Systems

### How Simulation Uses TB/VS/VF and Fragility

The simulation system consumes (not replaces) the short-term signal outputs:

- **Fragility Score (0-5)** → Direct input to crash-prone regime affinity (+15 if >=3)
  and crash-like event probability (+8 if >=4)
- **TB status** → Input to trend reversal probability (if TB active, trend break is in progress)
- **VS status** → Input to vol spike probability (if VS active, vol is already elevated)
- **VF status** → Input to liquidity stress probability (if VF not active, low volume concern)

### How Simulation Uses CCRLO

- **CCRLO score (0-21)** → Input to crash-like event probability (+5 if >=12)
  and tail risk scenario weight (higher CCRLO → higher tail weight)
- **CCRLO risk level** → Calibrates corridor width in Section 5 price chart

### Signal Flow Diagram

```
Alpha Vantage Data
  ├── TB/VS/VF computation → Fragility Score (0-5)
  ├── CCRLO computation → Correction Probability (0-21)
  └── Simulation computation
        ├── Uses: Fragility + CCRLO as inputs
        ├── Regime Detection (4 states)
        ├── Event Scoring (6 classes × 3 horizons)
        ├── Scenario Weighting (4 scenarios)
        └── Confidence Assessment
              ↓
        Report Integration (Sections 3, 5, 11, 12, 13, 18)
```

---

## Report Integration — HTML Patterns

### Section 3: Executive Summary — Market Regime Badge

```html
<li><strong>Market Regime:</strong>
  <span class="signal neutral">TRENDING (42%)</span>
  <br><span class="signal-desc">Secondary: Stressed 28%. Top event risk: Vol Spike 20d at 30%</span>
</li>
```

Color mapping for regime badge:
- Calm → `.signal.bullish` (green)
- Trending → `.signal.neutral` (amber)
- Stressed → `.signal.bearish` (red)
- Crash-Prone → `.signal.bearish` (red, stronger label)

### Section 11: Technical Indicators — Regime Row

```html
<tr style="background:#f0f9ff;">
  <td>Market Regime</td>
  <td>
    <span class="signal neutral">TRENDING</span>
    <span style="font-size:0.82em; color:#5a6577;">
      Calm 20% | Trend 42% | Stress 28% | Crash 10%
    </span>
  </td>
</tr>
```

### Section 11: Technical Indicators — Event Risk Row

```html
<tr style="background:#fef3c7;">
  <td>Event Risk (20d)</td>
  <td>
    <span class="signal bearish">Vol Spike 30%</span>
    <span class="signal neutral">Large Move 25%</span>
    <span class="signal bullish">Crash &lt;5%</span>
  </td>
</tr>
```

### Section 18: Scorecard — Event Risk Tile

```html
<div class="score-tile" style="border-color: #d97706;">
  <div class="score-label">Event Risk (20d)</div>
  <div class="score-value" style="color: #d97706;">NEUTRAL</div>
  <div class="score-detail">Top: Vol Spike 30% | Avg top-3: 22%</div>
</div>
```

### Section 12: Event Risk Simulation Visualization

Full-width card between Section 11 (Technical Indicators) and Section 13 (News & Risks).
Uses `.sim-grid` flexbox with two `.sim-panel` children.

**Left panel**:
- Regime probability horizontal bars (`.regime-row` with `.regime-pct-bar` + `.regime-pct-fill`)
- Dominant regime callout box (colored border-left)
- **Scenario Price Targets (20-Day)**: Table with Scenario | Weight | Price Range | Expected P/L
  - Price ranges computed using asymmetric ATR × √horizon multipliers:
    - Base Case: Current ± (ATR_h × 0.10)
    - Vol Expansion: (Current - ATR_h × 0.55) to (Current + ATR_h × 0.22) — downside biased
    - Trend Shift: (Current - ATR_h × 0.68) to min(SMA_50, Current + ATR_h × 0.65)
    - Tail Risk: (Current × (1 - 0.15×Beta/1.5)) to (Current × 0.97) — Beta-scaled, downside only
  - ATR_h = ATR_daily × √20
- **Weighted Expected Price callout**: Σ(weight_i × midpoint_i) where midpoint = (low+high)/2
  - Adjacent: 80% CI = Σ(weight_i × low_i) to Σ(weight_i × high_i)
- **Downside Skew**: (vol_weight × 0.7) + tail_weight + (trend_weight × 0.5), clipped [20%,85%]

**Right panel** (flex: 1.5):
- Heatmap table: 6 events × 3 horizons (5d, 10d, 20d) + **Price Impact** column + Key Driver
  - Price Impact shows the dollar range if that event occurs
  - Large Move: `Current ± (2.5 × ATR × √horizon_factor)`
  - Vol Spike: wider range due to expanded ATR
  - Trend Reversal: target = SMA_50 (upside bounce)
  - Crash Path: `< Current × 0.85`
- Color cells: `.heatmap-low` (<10%), `.heatmap-med` (10-20%), `.heatmap-high` (20-30%), `.heatmap-extreme` (>30%)
- Bottom tiles: Model Disagreement, Confidence, Composite Risk (20d), Downside Skew

See `.instructions/styling.md` for CSS classes and `examples/TSLA-analysis.html` for reference.

---

## Validation and Quality Checks

### Internal Consistency Checks

When auditing a report with simulation data (extends Layer 2 of report-audit skill):

| Check | What to Verify |
|---|---|
| Regime probabilities sum to 1.0 | Sum of 4 regime values = 100% |
| Event probabilities in [1%, 85%] | No event below 1% or above 85% |
| Crash probability ≤ 35% | Hard cap enforced |
| Scenario weights sum to 1.0 | Sum of 4 scenario weights = 100% |
| Regime badge matches table | Section 3 regime badge = Section 11 regime tile = Section 12 bars |
| Event risk badge matches table | Section 3 top events = Section 11 event risk tile = Section 12 heatmap |
| Heatmap colors correct | <10% green, 10-20% amber, 20-30% light red, >30% dark red |
| Event price impact consistent | Price Impact column matches ATR-based computation; crash < Current×0.85 |
| Scenario price ranges valid | All scenario ranges use ATR×√horizon formulas; tail risk shows negative returns only |
| Weighted expected price correct | Σ(weight_i × midpoint_i) matches displayed value; % change from current is correct |
| Downside skew formula | Matches (vol×0.7 + tail + trend×0.5) clipped [20%,85%] |
| CCRLO used as input | Crash-like prob reflects CCRLO score direction |
| Fragility used as input | Crash-prone regime reflects fragility score |
| Confidence level matches disagreement | Disagreement <0.15 = HIGH, etc. |

### Cross-Section Consistency

The simulation results must be consistent with existing signal outputs:
- If TB is active AND fragility >=3: crash-prone regime should have >15% probability
- If CCRLO is HIGH (>=12): tail risk scenario weight should be >0.15
- If regime is Calm dominant: all event probabilities should be at/below base rates
- If regime is Stressed: at least one event should be >30% probability

---

## Limitations and Disclaimers

1. **Rule-based approximation**: This is NOT a trained ML model; probabilities are calibrated
   estimates from research literature, not backtested predictions
2. **No options data**: The system uses ATR as a volatility proxy; true implied volatility
   from options surfaces would improve accuracy
3. **Static base rates**: Base probabilities are derived from broad equity market statistics
   and may not perfectly match specific sectors or market cap ranges
4. **Single-ticker scope**: Peer contagion and sector spillover effects are captured only
   through sector-level indicators in COMPANY_OVERVIEW, not through real-time peer analysis
5. **No intraday resolution**: All features use daily or longer timeframes
6. **Alpha Vantage delay**: Free tier data is 15-minute delayed; intraday features are approximate

Always include the standard financial disclaimer when reporting simulation results.
