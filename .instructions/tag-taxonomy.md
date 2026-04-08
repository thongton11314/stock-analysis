# Tag Taxonomy — Stock Classification Reference

## Overview

The tagging system assigns deterministic, rule-based classification tags to each
analyzed ticker across 5 independent dimensions. Tags are computed from the data
bundle + all 3 signal outputs — never inferred by AI.

## Tag Contract (TAG_SIGNAL)

Output file: `scripts/output/[TICKER]_tags.json`

```json
{
  "ticker": "AMZN",
  "as_of": "2026-03-23",
  "tags": {
    "profile":   ["mega-cap", "mature"],
    "sector":    ["consumer-cyclical", "cloud", "e-commerce"],
    "risk":      ["elevated-risk"],
    "momentum":  ["bearish", "below-200sma"],
    "valuation": ["fair-value"]
  },
  "primary_tag": "mega-cap-bearish-elevated-risk",
  "tag_version": "1.0"
}
```

### Rules
- Each dimension MUST have >= 1 tag
- All tags must belong to the valid taxonomy (see below)
- Sector allows dynamic tags for unknown Alpha Vantage sectors (WARN, not FAIL)
- `primary_tag` = `{first_profile}-{direction}-{first_risk}` (composite label)
- `tag_version` tracks taxonomy schema changes

---

## Dimension 1: Profile (Company Lifecycle)

Based on market cap + IPO date.

| Tag | Condition |
|---|---|
| `mega-cap` | Market cap >= $200B |
| `large-cap` | Market cap >= $10B |
| `mid-cap` | Market cap >= $2B |
| `small-cap` | Market cap >= $300M |
| `micro-cap` | Market cap < $300M |
| `mature` | IPO >= 15 years ago |
| `established` | IPO 8-15 years ago |
| `growth-stage` | IPO 3-8 years ago |
| `post-ipo` | IPO < 3 years ago |
| `pre-profit` | Latest annual net income < 0 |

**Source**: `company_overview.market_cap`, `company_overview.ipo_date`, `income_statement.annual[0].netIncome`

---

## Dimension 2: Sector (Industry Classification)

Maps Alpha Vantage sector names to canonical tags, plus thematic overlays from company description.

### Primary Sector Tags
| Alpha Vantage Sector | Tag |
|---|---|
| TECHNOLOGY | `technology` |
| HEALTH CARE / HEALTHCARE | `healthcare` |
| FINANCIAL SERVICES / FINANCIALS | `financials` |
| CONSUMER CYCLICAL / DISCRETIONARY | `consumer-cyclical` |
| CONSUMER DEFENSIVE / STAPLES | `consumer-defensive` |
| INDUSTRIALS | `industrials` |
| ENERGY | `energy` |
| UTILITIES | `utilities` |
| REAL ESTATE | `real-estate` |
| BASIC MATERIALS / MATERIALS | `materials` |
| COMMUNICATION SERVICES | `communication` |

### Thematic Overlay Tags
Detected from `company_overview.description` + `industry` keywords:

| Tag | Keywords |
|---|---|
| `ai` | artificial intelligence, machine learning, neural, generative ai |
| `cloud` | cloud computing, aws, azure, cloud infrastructure |
| `saas` | software as a service, saas, subscription software |
| `fintech` | fintech, digital payments, neobank, digital brokerage |
| `crypto` | cryptocurrency, bitcoin, blockchain, stablecoin |
| `ev` | electric vehicle, ev charging, battery technology |
| `e-commerce` | e-commerce, online retail, marketplace |
| `cybersecurity` | cybersecurity, network security |
| `biotech` | biotech, biotechnology, pharmaceutical |
| `semiconductor` | semiconductor, chip, wafer, fabless |

---

## Dimension 3: Risk (Composite Signal Risk)

Combines CCRLO risk level, trend-break status, and regime probabilities.

| Tag | Condition |
|---|---|
| `low-risk` | CCRLO risk_level = LOW |
| `moderate-risk` | CCRLO risk_level = MODERATE |
| `elevated-risk` | CCRLO risk_level = ELEVATED |
| `high-risk` | CCRLO risk_level = HIGH or VERY HIGH |
| `trend-break-active` | SHORT_TERM entry_active = true |
| `crash-prone` | SIMULATION regime crash_prone >= 0.20 |

**Source**: `ccrlo.risk_level`, `short_term.trend_break.entry_active`, `simulation.regime.probabilities.crash_prone`

---

## Dimension 4: Momentum (Trend Direction)

Based on price vs SMA-200, SMA slope, and RSI zone.

| Tag | Condition |
|---|---|
| `bullish` | Price > SMA-200 AND slope = POSITIVE |
| `bearish` | Price < SMA-200 AND slope = NEGATIVE |
| `neutral` | Mixed signals (price/slope disagree) |
| `oversold` | RSI <= 30 |
| `overbought` | RSI >= 70 |
| `above-200sma` | Price > SMA-200 |
| `below-200sma` | Price < SMA-200 |
| `mean-reverting` | RSI <= 35 AND Price < SMA-200 |

**Source**: `short_term.indicators.sma_200`, `short_term.indicators.sma_200_slope`, `bundle.rsi[0].value`

---

## Dimension 5: Valuation (Price Relative to Fundamentals)

Based on P/E ratio relative to sector 90th percentile.

| Tag | P/E / Sector_PE_90th Ratio |
|---|---|
| `deep-value` | < 0.30 |
| `undervalued` | 0.30 – 0.55 |
| `fair-value` | 0.55 – 0.85 |
| `overvalued` | 0.85 – 1.20 |
| `speculative-premium` | > 1.20 |

**Fallback** (no sector P/E available): Uses absolute P/E thresholds: <10 deep-value, <18 undervalued, <=30 fair-value, <=50 overvalued, >50 speculative-premium.

**Special case**: Negative P/E (pre-profit) with forward P/E > 60 → `speculative-premium`

**Source**: `company_overview.pe_ratio`, `company_overview.forward_pe`, `company_overview.sector_pe_90th_percentile`

---

## Cross-Ticker Index

Location: `scripts/output/tags_index.json`

Persists across runs. Updated automatically after each tag computation.

```json
{
  "AMZN": {
    "tags": { "profile": [...], "sector": [...], ... },
    "primary_tag": "mega-cap-bearish-elevated-risk",
    "as_of": "2026-03-23",
    "updated_at": "2026-03-24T10:30:00"
  },
  "HOOD": { ... }
}
```

### Query Examples
```bash
# All tickers
python scripts/compute_tags.py --ticker ANY --query all

# All high-risk tickers
python scripts/compute_tags.py --ticker ANY --query filter --dimension risk --tag high-risk

# All fintech tickers
python scripts/compute_tags.py --ticker ANY --query filter --dimension sector --tag fintech
```

---

## Pipeline Integration

Tags are computed as **Phase 2.5** in the analyst compute engine — after all 3 signals
are computed (Phase 2 + 2b) and before output validation (Phase 3).

```
Phase 2:  SHORT_TERM + CCRLO + SIMULATION
Phase 2b: Tail-risk adjustment
Phase 2.5: TAG computation (NEW)
Phase 3:  Output validation (includes tag contract checks)
```

---

## HTML Report Integration

Tags appear in the report header as colored pill badges:

```html
<div class="tag-badges">
  <span class="tag tag-profile">Mega-Cap</span>
  <span class="tag tag-sector">Consumer Cyclical</span>
  <span class="tag tag-risk">Elevated Risk</span>
  <span class="tag tag-momentum">Bearish</span>
  <span class="tag tag-valuation">Fair Value</span>
</div>
```

CSS classes: `.tag-profile` (blue), `.tag-sector` (purple), `.tag-risk` (red/amber/green),
`.tag-momentum` (green/red), `.tag-valuation` (teal).
