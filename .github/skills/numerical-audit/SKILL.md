---
name: numerical-audit
description: >
  Validate numerical accuracy and data integrity across the entire stock analysis pipeline —
  from data bundle through computed signals to the final HTML report. Ensures all numbers
  are up-to-date, traceable to source data, mathematically consistent, and free from
  fabrication or staleness.
  USE FOR: "validate numbers for [TICKER]", "numerical audit", "check data accuracy",
  "verify calculations", "number check", "are the numbers correct", "data integrity check",
  "cross-check report numbers", "verify report data", "numerical consistency check",
  "stale data check", "fabricated data check", number validation, data accuracy audit.
  DO NOT USE FOR: generating reports (use report-generation), fixing CSS/layout (use report-fix),
  structural report audit (use report-audit), computing signals (use analyst-compute-engine).
---

# Numerical Audit & Validation Skill

## Overview

End-to-end numerical integrity validator that operates at three stages of the analysis pipeline:

1. **Stage A — Pre-Computation Gate**: Validates data bundle numbers are fresh, reasonable, and internally consistent before signals are computed
2. **Stage B — Post-Computation Gate**: Validates computed signal numbers are mathematically correct and consistent with source data
3. **Stage C — Post-Report Audit**: Extracts numbers from the generated HTML report and cross-references against source data bundle and signal JSONs

**Why separate from existing validators**: The existing `validate_inputs.py` and `validate_outputs.py` handle structural completeness and contract compliance. This skill handles **numerical accuracy** — verifying that actual dollar values, percentages, and derived metrics are correct, traceable, and not fabricated.

## Architecture

```
Pipeline Stage          Validator                        Catches
─────────────────────  ─────────────────────────────    ──────────────────────────
Data Bundle Ready  →   Stage A (validate_numbers.py)  → Stale prices, math errors in source
                                                         data, unreasonable values
Signals Computed   →   Stage B (validate_numbers.py)  → Wrong derivations, methodology
                                                         violations, broken calculations
HTML Report Saved  →   Stage C (validate_numbers.py)  → Numbers not matching source,
                                                         fabricated figures, cross-section
                                                         mismatches, rounding errors
```

## Usage

### Single Command (Preferred)

```bash
python scripts/validate_numbers.py --ticker AMZN
```

This runs all three stages sequentially:
1. Reads `scripts/data/AMZN_bundle.json` → Stage A
2. Reads `scripts/output/AMZN_*.json` → Stage B
3. Reads `reports/AMZN-analysis.html` → Stage C (skipped if report doesn't exist)

### Stage-Specific Runs

```bash
# Stage A only (pre-computation)
python scripts/validate_numbers.py --ticker AMZN --stage A

# Stage B only (post-computation)
python scripts/validate_numbers.py --ticker AMZN --stage B

# Stage C only (post-report)
python scripts/validate_numbers.py --ticker AMZN --stage C
```

### Exit Codes

| Code | Meaning | Agent Action |
|------|---------|--------------|
| 0 | All stages PASS (or WARN) | Proceed / Report is valid |
| 1 | Stage A failed — data bundle numbers invalid | Fix data, re-fetch from MCP |
| 2 | Stage B failed — signal calculations wrong | Re-run compute engine |
| 3 | Stage C failed — report numbers don't match source | Fix report HTML |

### Output

Results are written to `scripts/output/[TICKER]_numerical_audit.json`:

```json
{
  "ticker": "AMZN",
  "validated_at": "2026-03-25T10:30:00",
  "overall_status": "PASS",
  "stages": {
    "A_data_bundle": { "status": "PASS", "checks": 14, "passed": 13, "warnings": 1, "failures": 0 },
    "B_signal_math": { "status": "PASS", "checks": 24, "passed": 24, "warnings": 0, "failures": 0 },
    "C_report_html": { "status": "PASS", "checks": 14, "passed": 14, "warnings": 0, "failures": 0 }
  },
  "checks": [...],
  "blocking_failures": []
}
```

## Stage A — Data Bundle Numerical Validation

### A1: Price & Quote Consistency

| Check | Rule | Severity |
|---|---|---|
| A1a. Price vs previous close | `change = price - previous_close` (±$0.01) | FAIL |
| A1b. Change percent | `change_percent = (change / previous_close) × 100` (±0.05%) | FAIL |
| A1c. OHLC ordering | `low ≤ open, close ≤ high` | FAIL |
| A1d. Price vs 52-week range | `52_week_low ≤ price ≤ 52_week_high` (allow 5% overshoot for lag) | WARN |
| A1e. Market cap derivation | `market_cap ≈ price × shares_outstanding` (±5%) | WARN |

### A2: Financial Statement Math

| Check | Rule | Severity |
|---|---|---|
| A2a. Gross profit | `gross_profit = revenue - cost_of_revenue` (±1% of revenue) | FAIL |
| A2b. Operating income | `operating_income = gross_profit - operating_expenses` (±2% of revenue) | WARN |
| A2c. Net margin | `net_income / revenue × 100` matches stated margin (±1pt) | WARN |
| A2d. EPS derivation | `net_income / shares_outstanding ≈ EPS` (±$0.05) | WARN |
| A2e. FCF calculation | `free_cash_flow = operating_cf - capex` (±1% of OCF) | FAIL |
| A2f. Debt-to-equity | `total_debt / total_equity ≈ D/E ratio` if both available (±0.1) | WARN |
| A2g. Balance sheet identity | `total_assets ≈ total_liabilities + total_equity` (±1%) | WARN |

### A3: Data Freshness & Staleness

| Check | Rule | Severity |
|---|---|---|
| A3a. as_of date | Must be within 3 trading days of today | WARN (>3d), FAIL (>10d) |
| A3b. Earnings recency | Most recent earnings quarter within 4 months | WARN |
| A3c. Financial statements | Annual report within 12 months | WARN |
| A3d. News sentiment | At least 1 article within 7 days | WARN |
| A3e. Macro data currency | Fed rate, CPI within 2 months of today | WARN |

### A4: Indicator Value Sanity

| Check | Rule | Severity |
|---|---|---|
| A4a. SMA ordering | If price > SMA_50 > SMA_200: uptrend. If reversed: downtrend. Flag if SMA_50 = SMA_200 (±0.1%) | INFO |
| A4b. ATR vs price | ATR should be < 10% of price for most stocks | WARN if >10% |
| A4c. BB width | Upper - Lower > 0 and Middle ≈ SMA_20 | FAIL if width ≤ 0 |
| A4d. MACD signal crossover | MACD_Hist sign consistent with MACD vs Signal line | WARN if inconsistent |
| A4e. Volume reasonableness | Volume > 0 and < 10× average | WARN if extreme |

## Stage B — Signal Computation Numerical Validation

### B1: Short-Term Signal Math

| Check | Rule | Severity |
|---|---|---|
| B1a. TB gate | `tb = (price ≤ 0.995 × SMA_200) AND (SMA_200_slope < 0)` — verify against data bundle | FAIL |
| B1b. VS gate | `vs = (ATR_percentile > 80)` — verify percentile computation | FAIL |
| B1c. VF gate | `vf = (volume_ratio ≥ 1.0)` — verify ratio computation | FAIL |
| B1d. Entry consistency | `entry_active = tb AND vs AND vf` | FAIL |
| B1e. Fragility score sum | Score = count of HIGH dimensions (must equal stated score) | FAIL |
| B1f. Fragility level mapping | 0-1→LOW, 2-3→MODERATE, 4-5→HIGH | FAIL |
| B1g. Correction prob monotonicity | mild ≥ standard ≥ severe ≥ black_swan | FAIL |
| B1h. Correction prob bounds | All in [1, 99] | FAIL |
| B1i. Tail-risk adjustment | If `_tail_risk_applied` exists, verify the formula was applied correctly | WARN |

### B2: CCRLO Signal Math

| Check | Rule | Severity |
|---|---|---|
| B2a. Feature score range | Each feature score in [0, 3] | FAIL |
| B2b. Composite sum | `composite_score = Σ(feature scores)` | FAIL |
| B2c. Composite range | `composite_score ∈ [0, 21]` | FAIL |
| B2d. Risk level mapping | 0-3→LOW, 4-7→MODERATE, 8-11→ELEVATED, 12-15→HIGH, 16-21→VERY HIGH | FAIL |
| B2e. Correction probability | Matches risk level band (LOW=5-10%, MODERATE=15-25%, ELEVATED=30-45%, HIGH=50-65%, VERY HIGH=70-85%) | FAIL |
| B2f. Feature vs source data | Verify each feature score uses the correct source data field from bundle | WARN |

### B3: Simulation Signal Math

| Check | Rule | Severity |
|---|---|---|
| B3a. Regime sum | 4 regime probabilities sum to 1.0 (±0.01) | FAIL |
| B3b. Dominant regime | Matches highest probability regime | FAIL |
| B3c. Event bounds | All event probabilities in [1, 85], crash_like ≤ 35 | FAIL |
| B3d. Event horizon ordering | For most events: 5d ≤ 10d ≤ 20d (longer horizon = more likely) | WARN |
| B3e. Scenario weight sum | 4 scenario weights sum to 1.0 (±0.01) | FAIL |
| B3f. Weighted expected price | `weighted_price = Σ(weight × midpoint)` for all scenarios | FAIL |
| B3g. Risk color mapping | CER <15%→GREEN, 15-30%→AMBER, >30%→RED | FAIL |
| B3h. Composite event risk | Average of top-3 20d event probabilities | WARN |

### B4: Cross-Signal Consistency

| Check | Rule | Severity |
|---|---|---|
| B4a. Price match | All 3 signals use same price from data bundle | FAIL |
| B4b. Date match | All 3 signals have same as_of date | FAIL |
| B4c. Ticker match | All 3 signals have same ticker | FAIL |
| B4d. CCRLO-regime alignment | CCRLO ≥ 12 → crash_prone > 0.15 | WARN |
| B4e. Fragility-regime alignment | Fragility ≥ 3 → crash_prone > 0.15 | WARN |
| B4f. ATR consistency | ATR in short_term.indicators ≈ data bundle ATR (±0.01) | FAIL |
| B4g. SMA consistency | SMA_200 in short_term.indicators ≈ data bundle SMA_200 (±0.01) | FAIL |

## Stage C — Post-Report HTML Numerical Audit

This stage parses the HTML report and extracts numerical values to cross-check against source data.

### C1: Header & Price Numbers

| Check | Rule | Severity | Status |
|---|---|---|---|
| C1a. Header price | Matches `global_quote.price` from bundle | FAIL | Implemented |
| C1b. Price change | Matches `global_quote.change` / `change_percent` | FAIL | Planned |
| C1c. Market cap | Matches `company_overview.market_cap` (formatted) | WARN | Planned |
| C1d. P/E ratio | Matches `company_overview.pe_ratio` | WARN | Planned |
| C1e. Beta | Matches `company_overview.beta` | WARN | Planned |
| C1f. 52-week range | Matches `company_overview.52_week_low` / `52_week_high` | WARN | Planned |
| C1g. Meta-row OHLCV | Open/High/Low/Close/Volume match `global_quote` | FAIL | Planned |

### C2: Signal Numbers in Report

| Check | Rule | Severity | Status |
|---|---|---|---|
| C2a. RSI value | Section 11 RSI matches `rsi[0].value` from bundle | FAIL | Implemented |
| C2b. MACD value | Section 11 MACD matches `macd[0].MACD` from bundle | FAIL | Implemented |
| C2c. ADX value | Section 11 ADX matches `adx[0].value` from bundle | FAIL | Implemented |
| C2d. ATR value | Section 11 ATR matches `atr_14[0].value` from bundle | FAIL | Implemented |
| C2e. SMA values | Section 11 MAs match bundle SMA_50/200, EMA_12/26 | FAIL | Planned |
| C2f. BB values | Section 11 Bollinger matches bundle bbands[0] | WARN | Planned |
| C2g. TB/VS/VF status | Section 3 + 11 match `_short_term.json` | FAIL | Planned |
| C2h. Fragility score | Section 3 + 11 match `_short_term.json` | FAIL | Implemented |
| C2i. CCRLO score | Section 3 + 18 match `_ccrlo.json` | FAIL | Implemented |
| C2j.tb_badge | All TB badge characters (✓/✗) across sections match `_short_term.json` | FAIL | Implemented |
| C2j.vs_badge | All VS badge characters across sections match signal | FAIL | Implemented |
| C2j.vf_badge | All VF badge characters across sections match signal | FAIL | Implemented |
| C2k. Event probabilities | Section 11 + 12 match `_simulation.json` | WARN | Planned |

### C3: Financial Numbers in Report

| Check | Rule | Severity | Status |
|---|---|---|---|
| C3a. Revenue | Section 9b/10 revenue matches `income_statement` annual[0] | FAIL | Planned |
| C3b. Net income | Section 9b matches `income_statement` annual[0] | FAIL | Planned |
| C3c. Gross margin | Stated margin = gross_profit / revenue x 100 (+-1pt) | WARN | Planned |
| C3d. Operating margin | Stated margin = operating_income / revenue x 100 (+-1pt) | WARN | Planned |
| C3e. EPS values | Section 8b/9a EPS matches `earnings` data | FAIL | Planned |
| C3f. Analyst target | Section 8a target matches `company_overview.analyst_target_price` | FAIL | Implemented |
| C3g. Analyst count | If stated, should match `company_overview` data | WARN | Planned |

### C4: Cross-Section Number Consistency

| Check | Rule | Severity | Status |
|---|---|---|---|
| C4a. Price everywhere | Current price consistent across report sections | FAIL | Implemented |
| C4b. Year-end targets | S4 table = S5 December row = S6 Target Price row (all 3 scenarios) | FAIL | Implemented |
| C4c. Analyst target | S3 = S8a (same value) | FAIL | Planned |
| C4d. Revenue | S9b = S10 = S17 (same revenue figure for subject company) | WARN | Planned |
| C4e. Market cap | S2 header = S17 competitive table (subject row) | WARN | Planned |
| C4f. Correction probs | S5 table probabilities match `_short_term.json` | FAIL | Implemented |
| C4g. CCRLO features | S18 tile values match `_ccrlo.json` | WARN | Planned |

### C5: Macro Number Consistency

| Check | Rule | Severity | Status |
|---|---|---|---|
| C5a. Fed rate | S15 table FFR matches data bundle `federal_funds_rate[0]` | FAIL | Planned |
| C5b. Fed chart bars | Exactly 12 bars in S15 with correct rates from bundle | FAIL | Implemented |
| C5b1. Fed bar spacing | Bars use `flex:1` for equal spacing, not `min-width:40px` (which bunches left) | FAIL | Implemented |
| C5b2. Fed bar rates | All 12 bar rate values match `federal_funds_rate[0:12]` | FAIL | Implemented |
| C5c. CPI value | S15 table CPI matches data bundle `cpi[0]` | FAIL | Planned |
| C5d. Unemployment | S15 table matches data bundle `unemployment[0]` | FAIL | Planned |
| C5e. GDP value | S15 table GDP matches data bundle `real_gdp[0]` (dollar format) | FAIL | Planned |
| C5f. Cross-report macro | If other reports exist in reports/, macro values must match | WARN | Implemented |

### C6: Percentage & Ratio Calculations

| Check | Rule | Severity | Status |
|---|---|---|---|
| C6a. Change percent | Header change% = (change / prev_close) x 100 | FAIL | Planned |
| C6b. Upside percent | S8a upside = (analyst_target - price) / price x 100 | WARN | Implemented |
| C6c1. Sankey SVG | S10 has `<svg class="sankey-svg">` element | FAIL | Implemented |
| C6c2. Gradient defs | S10 has `<linearGradient>` definitions for flow bands | FAIL | Implemented |
| C6c3. Flow paths | S10 has ≥8 `sankey-link` references (DETAIL stage needs OpEx→R&D/SGA) | FAIL | Implemented |
| C6c4. Stage labels | S10 has 4 stage labels: REVENUE, COST SPLIT, OPERATIONS, DETAIL | FAIL | Implemented |
| C6c5. Detail nodes | S10 has R&D/SGA detail breakdown nodes in DETAIL stage | FAIL | Implemented |
| C6c6. Margin callout | S10 has Gross Margin + Net Margin callout above SVG | FAIL | Implemented |
| C6c7. Legend | S10 has `sankey-legend` bar below SVG | FAIL | Implemented |
| C6c8. Narrative | S10 has Income Statement Analysis narrative box | FAIL | Implemented |
| C6d. Volume vs avg | If stated, volume_ratio matches actual ratio | WARN | Planned |
| C6e. Buy percentage | S8a Buy+SB percentage matches rating counts | WARN | Planned |
| C6f. Monthly accuracy | Past months: Accuracy = 100% - abs(error%) where error% = (est - actual) / actual x 100 | WARN | Planned |

### C7: Cross-Section Signal Consistency

| Check | Rule | Severity | Status |
|---|---|---|---|
| C7a. Regime consistency | Regime calm % identical across all sections (S3, S11, S12) | FAIL | Implemented |
| C7b. MACD consistency | MACD value in S3 narrative matches S11 tile (handles `&minus;` entity) | FAIL | Implemented |

### Implementation Status Summary

| Stage | Checks Spec'd | Implemented | Coverage |
|---|---|---|---|
| Stage A (Data Bundle) | 14 | 14 | 100% |
| Stage B (Signals) | 24 | 24 | 100% |
| Stage C (Report HTML) | 41 | 26 | 63% |
| **Total** | **79** | **64** | **81%** |

Stage A and B are fully implemented. Stage C has 26 implemented checks covering: price/signal accuracy (C1-C2), financial numbers (C3), cross-section consistency (C4, C7), macro data integrity (C5, including Fed bar spacing C5b1), S10 Sankey layout validation (C6c1-C6c8), and percentage calculations (C6a-C6b). Remaining planned checks can be added incrementally.

## Integration Points

### In Compute Engine Pipeline (Stages A+B)

The numerical audit runs **automatically** within the compute engine pipeline:

```
Data Collection (MCP) → Write Bundle
                        ↓
                    Stage A: validate_numbers.py --stage A
                        ↓ (PASS)
                    analyst_compute_engine.py --ticker TICKER
                        ↓
                    Stage B: validate_numbers.py --stage B
                        ↓ (PASS)
                    Proceed to HTML Generation
```

The agent should run Stage A after writing the data bundle (before running the compute engine)
and Stage B after the compute engine completes (before starting HTML generation).

### In Report Generation Pipeline (Stage C)

Stage C runs **after** the HTML report is saved (Phase 4 of report-generation):

```
Phase 3: Generate HTML → Phase 4: Save Report
                                    ↓
                              Stage C: validate_numbers.py --stage C
                                    ↓ (PASS)
                              Phase 5: Post-Gen Audit (existing 7-layer)
                                    ↓ (PASS)
                              READY TO PUBLISH
```

### In Standalone Audit (All Stages)

When triggered independently ("validate numbers for AMZN"):

```bash
python scripts/validate_numbers.py --ticker AMZN
```

Runs all three stages and produces a comprehensive numerical audit report.

## Output Format

```
═══════════════════════════════════════════════
 NUMERICAL AUDIT — AMZN
 Date: 2026-03-25
═══════════════════════════════════════════════

STAGE A: DATA BUNDLE NUMBERS
  ✅ A1a. Price change: $210.14 - $208.43 = $1.71 ✓
  ✅ A1b. Change%: 1.71/208.43 × 100 = 0.82% ✓
  ✅ A1c. OHLC ordering: $208.90 ≤ $211.20 ≤ $210.14 ✓
  ⚠️ A1d. Price $210.14 vs 52w-high $242.52 (13.4% below) — OK
  ✅ A2a. Gross Profit: $291.33B - $179.79B = $111.54B ✓
  ✅ A2e. FCF: $115.88B - $83.04B = $32.84B ✓
  ✅ A3a. Data freshness: 1 day old ✓
  STAGE SCORE: 17/18 PASS, 1 WARN

STAGE B: SIGNAL CALCULATIONS
  ✅ B1a. TB gate: 210.14 ≤ 0.995×224.81 (223.69) = TRUE ✓
  ✅ B1b. VS gate: ATR pctile 39.2% < 80% = FALSE ✓
  ✅ B1e. Fragility: 1 HIGH dim (momentum) = score 1/5 ✓
  ✅ B2b. CCRLO composite: 1+0+2+1+0+2+2 = 8 ✓
  ✅ B3a. Regime: 0.35+0.30+0.25+0.10 = 1.00 ✓
  ✅ B4a. Price match: all signals use $210.14 ✓
  STAGE SCORE: 24/24 PASS

STAGE C: REPORT HTML NUMBERS
  ✅ C1a. Header price $210.14 matches bundle ✓
  ✅ C2a. RSI 42.63 matches bundle rsi[0] ✓
  ✅ C2g. TB=✓ VS=✗ VF=✓ matches short_term.json ✓
  ✅ C3a. Revenue $291.33B matches income_statement ✓
  ✅ C4b. Year-end targets S4=S5 Dec=S6 Target Price ✓
  ✅ C5b. Fed chart: 12 bars match bundle values ✓
  ❌ C4d. Revenue mismatch: S9b=$291.3B, S17=$290B — FAIL
  STAGE SCORE: 30/32 PASS, 1 WARN, 1 FAIL

OVERALL: WARN (1 failure in Stage C)
  Action: Fix revenue figure in S17 competitive table
```

## When to Use This Skill

| Trigger | Stage | Context |
|---|---|---|
| "validate numbers for [TICKER]" | A+B+C | Standalone full audit |
| "check data accuracy" | A | After data collection |
| "verify calculations" | B | After compute engine |
| "cross-check report numbers" | C | After report generation |
| "numerical audit" | A+B+C | Standalone full audit |
| "are the numbers correct" | A+B+C | Standalone full audit |
| "stale data check" | A | Data freshness focus |
| Building report (Phase 2) | A | Auto-run before compute |
| Building report (Phase 2d) | B | Auto-run after compute |
| Building report (Phase 4) | C | Auto-run after save |

## Relationship to Other Skills

| Skill | Overlap | Distinction |
|---|---|---|
| `validate_inputs.py` | Both check data bundle | validate_inputs = structural completeness; numerical-audit = mathematical accuracy |
| `validate_outputs.py` | Both check signal outputs | validate_outputs = contract compliance; numerical-audit = calculation verification |
| `report-audit` | Both check HTML report | report-audit = 7-layer structural/styling; numerical-audit = number-by-number verification |
| `analyst-compute-engine` | Runs input+output validators | numerical-audit adds a mathematical verification layer on top |
