# Short-Term Trading Strategy — Trend-Break Risk-Off

Consolidated from `strategies/short-term/short-term-research-report.md` (theory + historical cases)
and `strategies/short-term/deep-research-report.md` (formal specification + skill.md).

## Strategy Summary

Detect "trend-break + volatility regime shift" conditions and generate bearish signals when
both hold simultaneously. Grounded in academic research on liquidity spirals, leverage cycles,
and information discontinuities. Uses a multi-gate entry (TB + VS + VF) with a 5-dimension
fragility stack to assess correction severity.

---

## Part 1: Theoretical Foundation (from Research Report)

### Why Extreme Corrections Happen (3 Structural Mechanisms)

1. **Funding/Liquidity Spirals**: When funding becomes scarce (margin constraints tighten, haircuts
   rise), market makers reduce risk-bearing capacity, lowering depth precisely when others must sell.
   This creates nonlinear "spirals" that transform moderate bad news into outsized declines.

2. **Leverage Cycle Amplification**: Procyclical leverage (expanding in booms, contracting in busts)
   creates boom-bust dynamics. When collateral values fall, borrowing capacity contracts, forcing
   deleveraging and potentially cascading selloffs. Assets whose valuations depend on easy funding
   are especially crash-prone when credit tightens.

3. **Information Discontinuities ("Bad News Hoarding")**: Negative fundamentals accumulate while
   prices stay elevated, then release in bursts when a threshold event triggers rapid repricing.
   This bridges fraud cases and non-fraud cases where management incentives or investor narratives
   delay incorporation of bad news.

### Historical Cases of >70% Corrections

| Asset | Peak → Trough | Decline | Duration | Dominant Catalyst |
|---|---|---|---|---|
| NASDAQ-100 | 2000 → 2002 | -82.9% | ~30 months | Dot-com bubble unwind |
| Nikkei 225 | 1989 → 2003 | -80.5% | ~13 years | Post-bubble deleveraging |
| Dow Jones | 1929 → 1932 | -87.1% | ~33 months | Depression-era contraction |
| Cisco (CSCO) | 2000 → 2002 | -89.3% | ~2-3 years | Dot-com; "infinite growth" repricing |
| Amazon (AMZN) | 2000 → 2001 | -93.3% | ~1-2 years | Profitability skepticism |
| Meta (META) | 2021 → 2022 | -76.7% | ~1 year | Growth decoupling + spending uncertainty |
| PayPal (PYPL) | 2021 → 2023 | -83.7% | Multi-year | Multiple compression under higher rates |
| Carvana (CVNA) | 2021 → 2022 | -99.0% | ~1-2 years | Leverage + funding stress |
| Tesla (TSLA) | 2021 → 2022 | -73.4% | ~1 year | Demand reset + 2022 risk-off |
| AIG | 2000 → 2008 | -98.6% | Multi-year | GFC insolvency/funding crisis |

### Why Single Indicators Fail

Because >70% collapses are rare (low base rate), even moderately informative indicators generate
many more false positives than true positives unless combined with other filters. This is why
the literature supports **fragility stacks** (multiple concurrent risk conditions) rather than
single-threshold alarms.

---

## Part 2: Formal Strategy Specification (from Deep Research Report)

### Three-Gate Entry System

All three gates must fire simultaneously. This is the core insight: a trend break alone is
often a buyable dip; it only becomes dangerous when combined with volatility stress and
confirmed selling pressure.

#### Gate 1: Trend Break (TB)

$$MA^{(L)}_t = \frac{1}{L}\sum_{i=0}^{L-1} P_{t-i} \quad (L=200 \text{ default})$$

$$\Delta MA^{(L)}_t = MA^{(L)}_t - MA^{(L)}_{t-s} \quad (s=20 \text{ default})$$

$$TB_t = \mathbb{1}\{P_t \le (1-b) \cdot MA^{(L)}_t\} \cdot \mathbb{1}\{\Delta MA^{(L)}_t < 0\}$$

Buffer $b = 0.005$ (0.5%) to avoid micro-whipsaws around the MA.

#### Gate 2: Volatility Shift (VS)

$$Q^{(q,B)}_t = \text{Quantile}_q(\{V_{t-B}, \ldots, V_{t-1}\}) \quad (q=0.80, B=252)$$

$$VS_t = \mathbb{1}\{V_t \ge Q^{(q,B)}_t\}$$

Where $V_t$ = ATR(14) or VIX-style implied volatility proxy.

#### Gate 3: Volume Filter (VF)

$$VF_t = \mathbb{1}\{Vol_t \ge m \cdot SMA(Vol, N_v)\} \quad (m=1.0, N_v=20)$$

#### Entry Signal

$$Entry_t = TB_t \cdot VS_t \cdot VF_t$$

Execute at $t+1$ (next session open) to avoid look-ahead bias.

### Exit Rules (Multi-Trigger — ANY fires)

| Exit Type | Formula | Default |
|---|---|---|
| Stop-Loss | $P_t \ge (1+\delta) \cdot P_{entry}$ | $\delta = 0.08$ (8%) |
| Time Stop | $h_t \ge H$ | $H = 60$ trading days |
| Trend Recovery | $P_t \ge MA^{(L)}_t$ | 200-MA |
| Vol Normalization | $V_t \le SMA(V, n_V)$ | $n_V = 20$ (optional) |

### Default Parameter Set

| Parameter | Symbol | Default | Range |
|---|---|---|---|
| Long MA window | $L$ | 200 | 150–300 |
| Buffer under MA | $b$ | 0.005 | 0–0.02 |
| Slope lag | $s$ | 20 | 10–30 |
| Vol percentile | $q$ | 0.80 | 0.75–0.90 |
| Vol lookback | $B$ | 252 | 126–504 |
| Volume multiplier | $m$ | 1.0 | 1.0–1.5 |
| Stop-loss | $\delta$ | 0.08 | 0.05–0.12 |
| Time stop | $H$ | 60 | 20–90 |
| Risk budget | $r$ | 0.01 | 0.0025–0.02 |
| Max leverage | $\lambda_{max}$ | 1.0 | 0.5–1.5 |

---

## Part 3: Fragility Stack Assessment

Score each dimension 0 (LOW) or 1 (HIGH). Total = 0-5.

| Dimension | HIGH if... | Data Source |
|---|---|---|
| Leverage/Funding | D/E > 2.0 OR negative FCF | BALANCE_SHEET, CASH_FLOW |
| Liquidity | ATR > 2× its 50-day average | ATR |
| Information Risk | ≥2 consecutive earnings misses | EARNINGS |
| Valuation | P/E > 90th percentile of sector | COMPANY_OVERVIEW |
| Momentum | Below BOTH 50-MA and 200-MA | SMA |

**Score interpretation:**
- **0-1 (Low)**: Corrections likely mild; trend break may be a buyable dip
- **2-3 (Moderate)**: Standard correction risk; signal worth monitoring
- **4-5 (High)**: Severe drawdown risk elevated; signal is actionable

## Correction Probability Calibration

Base probabilities adjusted by fragility score AND additional factors:

| Tier | Base Probability | Fragility 0-1 | Fragility 2-3 | Fragility 4-5 |
|---|---|---|---|---|
| Mild (-10-15%) | 85-95% | -5% | +0% | +5% |
| Standard (-20-30%) | 55-70% | -10% | +0% | +10% |
| Severe (-40-50%) | 25-40% | -10% | +0% | +15% |
| Black Swan (-60%+) | 8-15% | -5% | +0% | +10% |

Additional adjustments:
- Beta > 1.5: +5-10% across all tiers
- Recent IPO (<2 years): +10% to Severe/Black Swan
- High short interest (>20%): +5% to Standard/Severe

---

## Part 4: Position Sizing (Margin-Aware)

### Risk-Budget Sizing

$$\text{Notional}^{risk} = \frac{r \cdot E_t}{\delta}$$

### Margin Constraints (U.S. Equities/ETFs)

- **Initial margin**: 150% of proceeds (Reg T convention) → additional deposit $m_{init} \approx 0.50$
- **Maintenance floor**: FINRA Rule 4210: $5/share or 30% of market value, whichever is greater

$$\text{Notional}^{margin} = \min\left(\frac{E_t}{MR^{init}}, \frac{E_t}{MR^{maint}}\right)$$

### Final Size

$$\text{Notional} = \min(\text{Notional}^{risk}, \lambda_{max} \cdot E_t, \alpha \cdot ADV, \text{Notional}^{margin})$$

---

## Part 5: Strategy Archetypes (from Research Report)

| Archetype | Instruments | Entry Logic | Strengths | Failure Modes |
|---|---|---|---|---|
| **Trend-break risk-off** | Short shares or index puts | TB + VS + VF | Aligns with leverage/liquidity theory; scalable | Whipsaws; bear-market rallies; borrow costs |
| **Fragility stack single-name** | Short shares or put spreads | High leverage + deteriorating action + info risk | Targets extreme collapse mechanisms | False positives when financing extended; squeezes |
| **Options defined-risk** | Put spread, ratio spread | Tail risk underpriced + fragility + catalyst | Loss limited by design; no borrow needed | IV already elevated; theta decay |
| **Event-window hedge** | Index puts / put spreads | Macro conditions signal rising crash probability | Portfolio insurance | Carry cost; repeated small losses in calm |

---

## Part 6: Pseudocode (from Deep Research Report)

```
DAILY (after close):
  1. VALIDATE DATA: price, volume, ATR, MA(200), MA(50), earnings, D/E
     → If missing/stale: DO NOT TRADE

  2. COMPUTE SIGNALS:
     MA_long = SMA(Price, 200)
     MA_slope = MA_long - MA_long.shift(20)
     vol_threshold = rolling_quantile(ATR, 252, 0.80)
     vol_ok = (ATR >= vol_threshold)
     volume_ok = (Volume >= 1.0 × SMA(Volume, 20))

     TB = (Price <= 0.995 × MA_long) AND (MA_slope < 0)
     VS = vol_ok
     VF = volume_ok
     ENTRY = TB AND VS AND VF

  3. COMPUTE FRAGILITY (0-5):
     leverage_high = (D/E > 2.0) OR (FCF < 0)
     liquidity_high = (ATR > 2 × SMA(ATR, 50))
     info_risk_high = (≥2 consecutive earnings misses)
     valuation_high = (P/E > 90th percentile of sector)
     momentum_high = (Price < SMA(50)) AND (Price < SMA(200))
     fragility_score = sum of HIGH flags

  4. EXITS (if in position):
     exit_stop = (Price >= entry_price × 1.08)
     exit_time = (holding_days >= 60)
     exit_trend = (Price >= MA_long)
     exit_vol = (ATR < SMA(ATR, 20))
     EXIT = any of above

  5. SIZING (if entering):
     risk_notional = (0.01 × equity) / 0.08
     margin_notional = equity / broker_margin_requirement
     final_size = MIN(risk_notional, 1.0 × equity, 0.05 × ADV, margin_notional)

  6. EXECUTE at next session open (t+1)
```

---

## Part 7: Compliance Framework (from Research Report)

### Legal Constraints (U.S.)

| Regulation | Prohibits | Relevance |
|---|---|---|
| **Exchange Act Section 9** | False/misleading trading appearances (wash trades, matched orders) | Never create artificial prints |
| **Rule 10b-5** | Fraud, deceptive schemes, misleading statements in connection with trades | Never trade on false narratives |
| **Regulation SHO** | Short selling without locate/borrow; fails-to-deliver | Always confirm locate before shorting |
| **Rule 105 (Reg M)** | Short selling in restricted period around offerings | Check before single-name shorts |
| **FINRA Rule 4210** | Margin maintenance floors for short positions | Size within margin limits |
| **Regulation T** | Initial margin requirements (150% for unhedged shorts) | Factor into sizing |

### Operational Guardrails

- **Refuse to act** if: locate unavailable, margin insufficient, data stale, or any manipulative intent
- **Prefer defined-risk options** when: borrow scarce, squeeze risk high, gap risk around catalysts
- **Size by maximum plausible adverse move** (squeeze/halt), not anticipated return
- **Gap risk**: if price gaps beyond stop by >$g\%$, flatten immediately — do not double down

---

## Part 8: Integration with Full Report

When the short-term skill is invoked alongside report-generation:

1. **Section 3 (Executive Summary)**: Show TB/VS/VF status + fragility score in Short-Term Outlook
2. **Section 5 (Price Corridors)**: Adjust correction probabilities if fragility >= 3
3. **Section 11 (Technical Indicators)**: Add Trend-Break Status and Fragility Score rows
4. **Section 13 (Risks & Catalysts)**: Flag HIGH fragility dimensions as named risk factors

When invoked standalone, output the structured signal report (see SKILL.md Phase 4).

---

## Disclaimers

- This strategy is for **analysis and education only** — not investment advice
- Any implementation requires: proper risk management, margin compliance, short-sale compliance, and avoidance of manipulative conduct
- Backtests are hypothetical and may not reflect live trading constraints
- Rare-event prediction is inherently unstable — models can fail abruptly
- Original research documents preserved in `strategies/short-term/` for full academic references
