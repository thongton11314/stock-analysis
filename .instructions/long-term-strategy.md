# Long-Term Correction Prediction — CCRLO Strategy

## Strategy Summary

**Name**: Composite Correction Risk Logit Overlay (CCRLO)
**Goal**: Predict >=10% market corrections within a 6-month forward horizon
**Model**: Regularized logistic regression with 7 macro-financial features
**Research basis**: Credit/term-spread EWS models (AUROC ~0.70-0.88), valuation residual models,
and macro-finance ML classification approaches

## Theoretical Foundation

### Why These Predictors Work (from academic literature)

1. **Term Spread**: Yield curve inversion is the strongest single recession predictor (AUROC ~0.88
   in some studies). Recessions are highly correlated with market corrections.
2. **Credit Spreads**: Widening HY/IG spreads signal rising default expectations and funding stress,
   which precede equity drawdowns via the liquidity spiral mechanism.
3. **Volatility Regime**: Elevated implied/realized vol indicates market stress and risk-limit
   tightening, consistent with leverage-cycle amplification theory.
4. **Financial Conditions**: Composite indices (NFCI, OFR) capture broad stress across credit,
   equity, and funding markets simultaneously.
5. **Momentum**: Negative 12-month momentum signals trend exhaustion and potential regime shift.
6. **Realized Volatility**: Rising realized vol precedes corrections via margin/risk-limit feedback.
7. **GDP/Growth**: Slowing growth reduces earnings support and makes valuations vulnerable.

### Historical Performance Benchmarks

| Strategy Family | Event Definition | Reported Skill | Limitations |
|---|---|---|---|
| Valuation residual + logit | 15-30% crash | AUROC ~0.85 | Episode-dependent; out-of-sample mixed |
| Credit-spread PCA + logit EWS | Abnormal drawdown (CMAX) | ~84-88% crisis hit rate | False alarms high; may detect ongoing events |
| Macro probit (term/credit) | Recession within 12 months | AUROC ~0.88 | Recession ≠ correction; regime shifts |
| High-dim ML classification | 20%+ crash months | >90% cross-val accuracy | Class imbalance; limited independent crises |

## Feature Specifications

### Alpha Vantage Data Adapter

The original CCRLO research specification uses FRED-sourced macro data (T10Y3M, HY OAS, Baa yield,
VIX, NFCI). Since this system uses Alpha Vantage as its sole data provider, each feature is
implemented via the closest available proxy:

| # | Research Feature | FRED Source | Alpha Vantage Proxy | Adaptation Notes |
|---|---|---|---|---|
| 1 | Term Spread | T10Y3M (10Y-3M) | Fed rate trajectory (6M change) | Measures monetary policy direction; correlated with but distinct from yield curve slope |
| 2 | Credit Risk (HY OAS) | BAMLH0A0HYM2 | Company D/E ratio | Company-level leverage vs market-wide credit stress; captures similar risk through different lens |
| 3 | IG Credit (Baa yield) | BAA | Fed rate absolute level | Higher rate = tighter conditions; directionally aligned with credit yield |
| 4 | Implied Volatility | VIXCLS | ATR percentile (1Y) | Realized vol proxy; tracks stress regime shifts similarly to VIX |
| 5 | Financial Conditions | NFCI | Composite: rate + UE + GDP | Simplified composite; NFCI captures broader credit/equity/funding signals |
| 6 | Momentum (12M) | 12-month return | Drawdown from 52W high | Both capture negative momentum; drawdown measures distance from peak |
| 7 | Realized Volatility | Weekly return stdev | ATR/Price × √252 | Standard ATR-based vol estimation; reasonable approximation |

These proxies are documented trade-offs: they sacrifice some signal fidelity for data availability.
If FRED data becomes available in future, the scoring functions can be upgraded to use HY OAS and
term spread directly while keeping the same 0-3 scoring framework.

### 7 CCRLO Features

| # | Feature | Data Source | Interpretation |
|---|---|---|---|
| 1 | Term Spread | FEDERAL_FUNDS_RATE trajectory | Cutting = easing (low risk); Hiking = tightening (high risk) |
| 2 | Credit Risk | D/E ratio from BALANCE_SHEET | High leverage = elevated credit stress |
| 3 | IG Credit Proxy | Fed Rate level | Higher absolute rate = tighter conditions |
| 4 | Volatility Regime | ATR percentile vs 1-year | Top quartile = stress regime |
| 5 | Financial Conditions | Composite of rate + UE + GDP | Tight conditions = elevated risk |
| 6 | Momentum (12M) | Price vs 52W High | Deep drawdown from peak = negative momentum |
| 7 | Realized Volatility | ATR/Price annualized | Rising vol = increasing risk |

### Scoring System (0-3 per feature, total 0-21)

Each feature is scored 0-3 based on risk severity:
- **0** = Low risk / favorable conditions
- **1** = Neutral / mildly concerning
- **2** = Elevated risk
- **3** = High risk / crisis-level

### Correction Probability Mapping

| Composite Score | Probability | Risk Level | Suggested Action |
|---|---|---|---|
| 0-3 | 5-10% | LOW | Full equity exposure |
| 4-7 | 15-25% | MODERATE | Monitor weekly, prepare hedges |
| 8-11 | 30-45% | ELEVATED | Reduce to 80%, buy protective puts |
| 12-15 | 50-65% | HIGH | Reduce to 50%, active hedging |
| 16-21 | 70-85% | VERY HIGH | Reduce to 20%, maximum defensive |

## Decision Rule (Hysteresis)

To reduce turnover (critical because false alarms are frequent in crisis predictors):

```
If correction_probability >= 0.35: set equity_weight = 0.20 (risk-off)
Elif correction_probability <= 0.25: set equity_weight = 1.00 (risk-on)
Else: maintain previous weight (no change)
```

## Integration with Report System

### In Full Stock Analysis Reports (Sections 3, 5, 11, 14)

| Report Section | CCRLO Integration |
|---|---|
| **Section 3 (Executive Summary)** | Long-Term Outlook includes: CCRLO score X/21, 6-month correction probability, risk level badge |
| **Section 5 (Price Corridors)** | Corridor width calibrated by CCRLO: LOW = tight, HIGH = wide |
| **Section 15 (Macro Dashboard)** | CCRLO feature scores shown alongside macro indicators |
| **Section 18 (Scorecard)** | CCRLO added as a composite risk tile (TAILWIND if LOW, HEADWIND if HIGH) |

### Combined with Short-Term Skill

| Time Horizon | Skill | What It Answers |
|---|---|---|
| Days to weeks | short-term-analysis | Is the trend breaking NOW? (tactical) |
| 6 months | long-term-prediction (CCRLO) | Is a correction LIKELY? (strategic) |

**Ideal workflow**: Run BOTH skills when analyzing a stock. If both signal elevated risk,
confidence in the bearish thesis increases substantially.

## Backtesting Requirements (from research)

- **Walk-forward only** — no future data in training
- **Purged time-series splits** — label windows cannot overlap between train/test
- **Elastic net regularization** — L1/L2 with l1_ratio=0.5
- **Monthly refit** — expanding window, minimum 10 years history
- **Probability calibration** — isotonic regression on trailing 5-year validation window
- **Cost model** — include transaction costs and turnover tracking

## Data Sources

| Component | Source | Notes |
|---|---|---|
| Fed Funds Rate | Alpha Vantage `FEDERAL_FUNDS_RATE` | Monthly, proxy for term structure |
| GDP | Alpha Vantage `REAL_GDP` | Annual, growth direction |
| CPI | Alpha Vantage `CPI` | Monthly, inflation regime |
| Unemployment | Alpha Vantage `UNEMPLOYMENT` | Monthly, labor stress |
| Price/Vol | Alpha Vantage `GLOBAL_QUOTE`, `ATR`, `SMA` | Daily, for momentum + vol |
| Company Financials | Alpha Vantage `BALANCE_SHEET`, `COMPANY_OVERVIEW` | For credit risk proxy |

## Compliance & Disclaimers

- This is a **probabilistic risk assessment**, not a market-timing algorithm
- Backtests are hypothetical and may not reflect live trading constraints
- Rare-event prediction is inherently unstable — models can fail abruptly
- Not investment advice — always consult a licensed financial advisor
- See `strategies/long-term/long-term-strategy.md` for full academic references and formal specification
