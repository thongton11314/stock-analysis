# Signal Output Contracts

Standardized output schemas for all three signal systems. Report-generation and other
downstream consumers reference these contracts to ensure consistent integration.

## 1. Short-Term Signal Contract (TB/VS/VF + Fragility)

```
SHORT_TERM_SIGNAL:
  ticker:        string          # e.g. "AAPL"
  as_of:         string          # ISO date, e.g. "2026-03-20"
  price:         number          # Current price from GLOBAL_QUOTE

  trend_break:
    tb:            boolean       # Price <= 0.995 × SMA_200 AND SMA_200_slope < 0
    vs:            boolean       # ATR > 80th percentile of 1-year range
    vf:            boolean       # Volume >= 1.0 × SMA(Volume, 20)
    entry_active:  boolean       # TB AND VS AND VF

  indicators:
    sma_200:       number        # Current SMA(200) value
    sma_200_slope: string        # "POSITIVE" | "NEGATIVE"
    atr_14:        number        # Current ATR(14) value
    atr_percentile: number       # 0-100, percentile vs 1-year history
    volume_ratio:  number        # today / 20d average

  fragility:
    score:         number        # 0-5 count of HIGH dimensions
    level:         string        # "LOW" (0-1) | "MODERATE" (2-3) | "HIGH" (4-5)
    dimensions:
      leverage:    string        # "LOW" | "HIGH" — D/E > 2.0 or negative FCF
      liquidity:   string        # "LOW" | "HIGH" — ATR > 2× its 50d average
      info_risk:   string        # "LOW" | "HIGH" — ≥2 consecutive earnings misses
      valuation:   string        # "LOW" | "HIGH" — P/E > 90th percentile of sector
      momentum:    string        # "LOW" | "HIGH" — below BOTH 50-MA and 200-MA

  correction_probabilities:      # Base + fragility + beta + IPO + short interest + tail-risk modifier
    mild:          number        # -10% to -15% drawdown probability (%)
    standard:      number        # -20% to -30% drawdown probability (%)
    severe:        number        # -40% to -50% drawdown probability (%)
    black_swan:    number        # -60%+ drawdown probability (%)
  _tail_risk_applied: number     # (optional) Tail-risk scenario weight used for post-engine adjustment
```

### Correction Probability Adjustments

Correction probabilities are computed in two stages:

**Stage 1** (in `compute_short_term.py`): Base probabilities adjusted by:
- Fragility score (0-5): See calibration table in `.instructions/short-term-strategy.md`
- Beta > 1.5: +5-10% across all tiers
- Recent IPO (<2 years): +10% to Severe/Black Swan
- High short interest (>20%): +5% to Standard/Severe

**Stage 2** (in `analyst_compute_engine.py` post-computation):
After simulation computes tail-risk scenario weight, correction probabilities are amplified:
```
Mild     × (1 + tail_weight)
Standard × (1 + 2 × tail_weight)
Severe   × (1 + 3 × tail_weight)
Black Swan: not adjusted by tail formula
```
Monotonicity is enforced after adjustment: mild ≥ standard ≥ severe ≥ black_swan.

### Report Section Mapping

| Field | Section 3 (Exec Summary) | Section 5 (Corridors) | Section 11 (Technical) | Section 13 (Risks) |
|---|---|---|---|---|
| `entry_active` | Signal badge: ACTIVE/INACTIVE | — | — | — |
| `tb`, `vs`, `vf` | TB ✓/✗ VS ✓/✗ VF ✓/✗ | — | Trend-Break Status row | — |
| `fragility.score` | "Fragility: X/5" badge | Adjust probs if ≥3 | Fragility Score row | — |
| `fragility.dimensions` (HIGH) | — | — | — | Named risk factor |
| `correction_probabilities` | — | Probability bars + dip markers | — | — |

---

## 2. Long-Term Signal Contract (CCRLO)

```
CCRLO_SIGNAL:
  ticker:         string         # e.g. "AAPL"
  as_of:          string         # ISO date
  horizon:        string         # "6 months (126 trading days)"

  features:                      # 7 dimensions, each scored 0-3
    term_spread:
      value:      string         # Description (e.g. "Cutting 50bps")
      score:      number         # 0-3
    credit_risk:
      value:      string
      score:      number
    ig_credit:
      value:      string
      score:      number
    volatility_regime:
      value:      string
      score:      number
    financial_conditions:
      value:      string
      score:      number
    momentum_12m:
      value:      string
      score:      number
    realized_vol:
      value:      string
      score:      number

  composite_score: number        # Sum of 7 feature scores (0-21)
  correction_probability: number # Mapped percentage (5-85%)
  risk_level:     string         # "LOW" | "MODERATE" | "ELEVATED" | "HIGH" | "VERY HIGH"

  decision:       string         # Action framework text
```

### Score-to-Probability Mapping

| Score Range | Probability | Risk Level |
|---|---|---|
| 0-3 | 5-10% | LOW |
| 4-7 | 15-25% | MODERATE |
| 8-11 | 30-45% | ELEVATED |
| 12-15 | 50-65% | HIGH |
| 16-21 | 70-85% | VERY HIGH |

### Report Section Mapping

| Field | Section 3 | Section 5 | Section 18 |
|---|---|---|---|
| `composite_score` | "CCRLO: X/21" | — | CCRLO tile |
| `correction_probability` | "6-mo correction: X%" | Corridor width calibration | — |
| `risk_level` | Badge color | LOW=±20%, HIGH=±40% | TAILWIND/HEADWIND |
| `features` | — | — | Feature breakdown |

---

## 3. Simulation Signal Contract (Regime + Events + Scenarios)

```
SIMULATION_SIGNAL:
  ticker:          string
  as_of:           string
  price:           number

  regime:
    probabilities:
      calm:        number        # 0.0-1.0, all four MUST sum to 1.0
      trending:    number
      stressed:    number
      crash_prone: number
    dominant:      string        # Name of highest-probability regime

  events:                        # 6 event classes × 3 horizons
    large_move:
      5d:          number        # Probability (%), clipped [1, 85]
      10d:         number
      20d:         number
      price_impact: string       # e.g. "$370-$395"
    vol_spike:
      5d:          number
      10d:         number
      20d:         number
      price_impact: string
    trend_reversal:
      5d:          number
      10d:         number
      20d:         number
      price_impact: string
    earnings_reaction:
      5d:          number
      10d:         number
      20d:         number
      price_impact: string
    liquidity_stress:
      5d:          number
      10d:         number
      20d:         number
      price_impact: string
    crash_like:
      5d:          number        # Capped at 35%
      10d:         number
      20d:         number
      price_impact: string

  scenarios:                     # 4 named scenarios, weights MUST sum to 1.0
    base_case:
      weight:      number
      price_range: string        # e.g. "$378-$385"
      expected_pl: string        # e.g. "+0.5%"
    vol_expansion:
      weight:      number
      price_range: string
      expected_pl: string
    trend_shift:
      weight:      number
      price_range: string
      expected_pl: string
    tail_risk:
      weight:      number
      price_range: string
      expected_pl: string

  weighted_expected:
    price:         number        # Σ(weight × midpoint)
    change_pct:    string        # From current price
    ci_80_low:     number        # 80% confidence interval low
    ci_80_high:    number        # 80% confidence interval high
    downside_skew: number        # Probability 20d return < 0 (%)

  confidence:
    disagreement:  number        # 0.0-1.0
    level:         string        # "HIGH" | "MODERATE-HIGH" | "MODERATE" | "LOW-MODERATE" | "LOW"
    top_drivers:   list[string]  # 3-5 top risk drivers

  composite_event_risk: number   # Average of top-3 20d event probabilities (%)
  risk_color:      string        # "GREEN" (<15%) | "AMBER" (15-30%) | "RED" (>30%)
```

### Report Section Mapping

| Field | S3 | S5 | S11 | S12 | S13 | S18 |
|---|---|---|---|---|---|---|
| `regime.dominant` | Badge | — | Regime tile | Regime bars | — | — |
| `events.*_20d` (top) | Top event | Prob adjustment | Event Risk tile | Heatmap | — | — |
| `scenarios.*.weight` | — | Correction calibration | — | Scenario table | Risk narratives | — |
| `weighted_expected` | — | — | — | Callout box | — | — |
| `confidence` | — | — | — | Metrics tiles | — | — |
| `composite_event_risk` | — | — | — | — | — | Event Risk tile |

---

## Validation Rules (All Contracts)

1. **Regime probabilities**: `calm + trending + stressed + crash_prone = 1.0` (±0.01 tolerance)
2. **Scenario weights**: `base + vol + trend + tail = 1.0` (±0.01 tolerance)
3. **Event probability bounds**: All in `[1%, 85%]`; crash-like capped at `35%`
4. **Fragility score**: Integer `0-5`, level must match score range
5. **CCRLO score**: Integer `0-21`, risk_level must match score-to-probability table
6. **Correction probabilities**: `mild > standard > severe > black_swan` (monotonic decreasing)
7. **Cross-signal consistency**:
   - If CCRLO ≥ 12 (HIGH), `crash_prone` regime should be > 0.15
   - If fragility ≥ 3 (HIGH), `crash_prone` regime should be > 0.15
   - If TB active AND fragility ≥ 3, `composite_event_risk` should be elevated (>20%)
