---
name: analyst-compute-engine
description: >
  Run the full signal computation pipeline — validate inputs, compute all signals via Python,
  and validate outputs — in a single command. Replaces separate python-compute and
  calculation-review workflows.
  USE FOR: "compute signals for [TICKER]", "run compute engine", "validate and compute",
  "run analyst engine", "compute all signals", "run Python computation", "validate data",
  "check signal outputs", "calculation review", signal computation, input validation,
  output validation, data quality gate, signal contract verification.
  DO NOT USE FOR: collecting data from Alpha Vantage (use data-collection skill), generating
  HTML reports (use report-generation skill), fixing reports (use report-fix skill),
  post-generation 7-layer audit (use report-audit skill).
---

# Analyst Compute Engine

## Overview

Unified computation pipeline that validates inputs, computes all three signal systems
(SHORT_TERM, CCRLO, SIMULATION), and validates outputs — all in a single command.

**Why unified**: Instead of invoking 5 separate scripts manually, the engine orchestrates
the full pipeline with proper sequencing, error handling, and a consolidated status report.
The agent needs only one command to go from data bundle to validated signals.

## Architecture

```
scripts/
├── analyst_compute_engine.py    ← Unified orchestrator (run this)
├── compute_short_term.py        ← TB/VS/VF + Fragility (imported by engine)
├── compute_ccrlo.py             ← CCRLO 7-feature scoring (imported by engine)
├── compute_simulation.py        ← Regime + Events + Scenarios (imported by engine)
├── validate_inputs.py           ← Data bundle validation (imported by engine)
├── validate_outputs.py          ← Signal contract validation (imported by engine)
├── data/                        ← Agent writes data bundles here
│   └── [TICKER]_bundle.json
└── output/                      ← Engine writes signal outputs here
    ├── [TICKER]_short_term.json
    ├── [TICKER]_ccrlo.json
    ├── [TICKER]_simulation.json
    ├── [TICKER]_tags.json
    └── [TICKER]_engine_report.json
```

All scripts use Python standard library only (json, statistics, argparse, sys, datetime, os, re).
No pip installs required.

**Re-analysis overwrite**: When the engine runs for a ticker that already has signal outputs
in `scripts/output/`, all existing `[TICKER]_*.json` files are overwritten with fresh results.
This is the expected behavior — re-analysis always replaces stale signals with current computations.

## Numerical Audit Integration

The **numerical-audit skill** (`.github/skills/numerical-audit/SKILL.md`) provides a complementary
numerical accuracy layer via `scripts/validate_numbers.py`. While the compute engine validates
*structural completeness and contract compliance*, the numerical audit verifies *mathematical accuracy*:

| Layer | Script | What It Checks |
|---|---|---|
| Structural validation | `validate_inputs.py` | Required fields present, non-empty, correct types |
| Structural validation | `validate_outputs.py` | Signal contracts, field ranges, cross-signal consistency |
| **Numerical accuracy** | **`validate_numbers.py`** | **Math correctness: GP=Rev-COGS, composite=Σfeatures, price matches, TB gate logic** |

### Recommended Pipeline Integration

```bash
# Stage A: After writing bundle, before running engine
python scripts/validate_numbers.py --ticker [TICKER] --stage A

# Run the engine
python scripts/analyst_compute_engine.py --ticker [TICKER]

# Stage B: After engine, before HTML generation
python scripts/validate_numbers.py --ticker [TICKER] --stage B

# ... generate HTML report ...

# Stage C: After HTML report saved, before audit
python scripts/validate_numbers.py --ticker [TICKER] --stage C
```

## Usage

### Single Command (Preferred)

```bash
python scripts/analyst_compute_engine.py --ticker AMZN
```

This runs the full pipeline:
1. Reads `scripts/data/AMZN_bundle.json`
2. Validates inputs (completeness, ranges, freshness)
3. Computes SHORT_TERM → CCRLO → SIMULATION (in dependency order)
4. Validates outputs (contracts, bounds, cross-signal consistency)
5. Writes all outputs to `scripts/output/`

**Exit codes:**
| Code | Meaning | Agent Action |
|------|---------|--------------|
| 0 | All phases passed (PASS or WARN) | Proceed to HTML generation |
| 1 | Input validation failed | Fix data bundle, re-run engine |
| 2 | Computation error (script crash) | Check error in engine report |
| 3 | Output validation failed | Review blocking_failures, investigate |

### Output Files

After successful execution, read these files for HTML report generation:

| File | Content | Used In |
|------|---------|---------|
| `scripts/output/AMZN_short_term.json` | TB/VS/VF, Fragility, correction probabilities | Sections 3, 5, 11, 13 |
| `scripts/output/AMZN_ccrlo.json` | CCRLO score, 7 features, risk level | Sections 3, 5, 18 |
| `scripts/output/AMZN_simulation.json` | Regime, events, scenarios, confidence | Sections 3, 5, 11, 12, 13, 18 |
| `scripts/output/AMZN_tags.json` | 5-dimension stock classification tags | Header tags, portfolio aggregation |
| `scripts/output/AMZN_engine_report.json` | Pipeline status, signal summary | Agent decision-making |

### Engine Report

The engine report (`[TICKER]_engine_report.json`) provides a consolidated status:

```json
{
  "ticker": "AMZN",
  "overall_status": "PASS",
  "phases": {
    "input_validation": "PASS",
    "computation": "COMPLETE",
    "output_validation": "PASS"
  },
  "signal_summary": {
    "short_term": { "entry_active": false, "fragility": "1/5 (LOW)" },
    "ccrlo": { "score": "6/21", "risk_level": "MODERATE", "correction_probability": "20.0%" },
    "simulation": { "regime": "calm", "event_risk": "18.5% (AMBER)", "confidence": "MODERATE-HIGH" }
  },
  "output_files": { ... }
}
```

## Prerequisites

Before running the engine, the agent must:

1. **Collect data via MCP** (data-collection skill)
2. **Write the data bundle** to `scripts/data/[TICKER]_bundle.json`

## Data Bundle Schema

The agent must structure the collected MCP data into the following JSON format:

```json
{
  "ticker": "AMZN",
  "as_of": "2026-03-24",
  "global_quote": {
    "price": 185.50,
    "open": 184.20,
    "high": 186.30,
    "low": 183.90,
    "volume": 45000000,
    "previous_close": 184.80,
    "change": 0.70,
    "change_percent": 0.38,
    "volume_sma_20": 42000000
  },
  "company_overview": {
    "market_cap": 1950000000000,
    "pe_ratio": 62.5,
    "forward_pe": 42.8,
    "beta": 1.15,
    "eps": 2.97,
    "52_week_high": 242.52,
    "52_week_low": 151.61,
    "analyst_target_price": 235.00,
    "sector": "Technology",
    "debt_to_equity": 0.85,
    "ipo_date": "1997-05-15",
    "sector_pe_90th_percentile": 55.0
  },
  "sma_200": [{"date": "2026-03-24", "value": "192.50"}, ...],
  "sma_50": [{"date": "2026-03-24", "value": "188.30"}, ...],
  "atr_14": [{"date": "2026-03-24", "value": "4.25"}, ...],
  "rsi": [{"date": "2026-03-24", "value": "55.3"}, ...],
  "macd": [{"date": "...", "MACD": "1.2", "MACD_Signal": "0.8", "MACD_Hist": "0.4"}, ...],
  "bbands": [{"date": "...", "Real Upper Band": "195.0", "Real Middle Band": "190.0", "Real Lower Band": "185.0"}, ...],
  "adx": [{"date": "...", "value": "22.5"}, ...],
  "ema_12": [{"date": "...", "value": "186.0"}, ...],
  "ema_26": [{"date": "...", "value": "184.5"}, ...],
  "income_statement": { "annual": [...] },
  "balance_sheet": { "annual": [...] },
  "cash_flow": { "annual": [...], "free_cash_flow": 28500000000 },
  "earnings": { "quarterly": [{"date": "2025-12", "reported_eps": 1.86, "estimated_eps": 1.72, "surprise_percentage": 8.1}, ...] },
  "news_sentiment": [...],
  "institutional_holdings": {...},
  "federal_funds_rate": [{"date": "2026-03-01", "value": "4.50"}, {"date": "2026-02-01", "value": "4.50"}, ...],
  // CRITICAL: federal_funds_rate MUST have ≥12 monthly values for the Fed chart.
  // Storing only 1 value causes fabricated chart data. Always store the full API response.
  "cpi": [{"date": "2026-02-01", "value": "315.2"}, {"date": "2026-01-01", "value": "314.1"}, ...],
  "unemployment": [{"date": "2026-02-01", "value": "3.8"}, {"date": "2026-01-01", "value": "3.7"}, ...],
  "real_gdp": [{"date": "2025-Q4", "value": "2.1"}, ...],
  "peers": [...]
}
```

### Key Formatting Rules
- Time series arrays: most recent value FIRST (index 0 = today)
- All numeric values as numbers or numeric strings (scripts handle both)
- Dates in ISO format (YYYY-MM-DD)
- `volume_sma_20`: 20-day average volume (if available)
- `sector_pe_90th_percentile`: agent estimates from peer data
- `free_cash_flow`: operating CF minus CapEx

## Pipeline Internals

### Phase 1: Input Validation

Checks performed by `validate_inputs.py`:

| Category | Checks |
|---|---|
| Required fields | 15 subject data fields present and non-empty |
| Optional fields | Macro data, peers, news, institutional (warns if missing) |
| **Macro data depth** | **`federal_funds_rate` ≥12 entries (WARN if <12, CRITICAL if only 1 — causes fabricated Fed charts), `cpi` ≥4, `unemployment` ≥4, `real_gdp` ≥4** |
| Price sanity | Price > 0, volume > 0, reasonable ranges |
| Time series depth | SMA_200 ≥ 21 (for slope), ATR ≥ 50 (for fragility), ideally 252 |
| Indicator ranges | RSI ∈ [0,100], ADX ∈ [0,100], ATR > 0, Beta ∈ [-2,5] |
| Financial data | Revenue present, D/E available, earnings history |
| Data freshness | ≤ 3 days (PASS), ≤ 7 days (WARN), > 7 days (WARN) |

### Phase 2: Signal Computation

Execution order (dependency-driven):
1. `compute_short_term.py` — standalone, needs only data bundle
2. `compute_ccrlo.py` — standalone, needs only data bundle
3. `compute_simulation.py` — depends on outputs from steps 1 and 2
4. `compute_tags.py` — depends on all 3 signals + data bundle
5. **Post-computation adjustment** — tail-risk scenario weight from simulation is applied
   back to short-term correction probabilities:
   - Mild × (1 + tail_weight)
   - Standard × (1 + 2 × tail_weight)
   - Severe × (1 + 3 × tail_weight)
   - This ensures correction probs reflect the simulation's forward risk assessment

Note: `compute_short_term.py` already applies IPO (<2yr) and Beta (>1.5) adjustments
internally. The tail-risk adjustment is the only cross-signal correction applied by the engine.

All outputs conform to contracts in `.instructions/signal-contracts.md`.

### Phase 3: Output Validation

Checks performed by `validate_outputs.py`:

| Category | Checks |
|---|---|
| SHORT_TERM structure | 17 fields, entry = tb AND vs AND vf, fragility 0-5, monotonic correction probs |
| CCRLO structure | 7 features scored 0-3, composite = sum, risk level matches score |
| SIMULATION structure | Regime probs sum to 1.0, events in [1%,85%], crash ≤ 35%, scenario weights sum to 1.0 |
| Cross-signal | CCRLO ≥ 12 → crash_prone > 0.15; fragility ≥ 3 → crash_prone > 0.15 |

## Error Handling

| Scenario | Engine Behavior | Agent Action |
|---|---|---|
| Data bundle not found | Exit 1, error message | Write the bundle first |
| Input validation FAIL | Exit 1, blocking_failures listed | Re-fetch missing MCP data, update bundle, re-run |
| Computation crash | Exit 2, error in report | Check error message, fix bundle or report bug |
| Output validation FAIL | Exit 3, signals saved but flagged | Review blocking_failures, possibly re-run with fixed data |
| WARN (any phase) | Exit 0, warnings in report | Proceed but note warnings in HTML report |

## Standalone Script Access

Individual scripts can still be run directly for debugging:

```bash
python scripts/validate_inputs.py --input scripts/data/AMZN_bundle.json --output scripts/data/AMZN_input_validation.json
python scripts/compute_short_term.py --input scripts/data/AMZN_bundle.json --output scripts/output/AMZN_short_term.json
python scripts/compute_ccrlo.py --input scripts/data/AMZN_bundle.json --output scripts/output/AMZN_ccrlo.json
python scripts/compute_simulation.py --input scripts/data/AMZN_bundle.json --short-term scripts/output/AMZN_short_term.json --ccrlo scripts/output/AMZN_ccrlo.json --output scripts/output/AMZN_simulation.json
python scripts/validate_outputs.py --short-term scripts/output/AMZN_short_term.json --ccrlo scripts/output/AMZN_ccrlo.json --simulation scripts/output/AMZN_simulation.json --output scripts/output/AMZN_output_validation.json
```

## Multi-Ticker Behavior

Each ticker runs independently through the engine:
- Each ticker gets its own data bundle: `scripts/data/[TICKER]_bundle.json`
- Each ticker gets its own outputs: `scripts/output/[TICKER]_*.json`
- No cross-ticker contamination — scripts are stateless
- Old output files are overwritten on re-run
