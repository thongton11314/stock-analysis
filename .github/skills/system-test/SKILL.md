---
name: system-test
description: >
  Run the automated test framework to verify system integrity after any change.
  Ensures all computation scripts, signal contracts, and cross-module integration
  remain correct and consistent.
  USE FOR: "run tests", "test system", "verify changes", "check if anything broke",
  "regression test", "validate pipeline", "update golden", "test coverage",
  "system health check", "smoke test", "did my changes break anything".
  DO NOT USE FOR: generating reports (use report-generation), computing signals
  (use analyst-compute-engine), auditing reports (use report-audit).
applyTo: "run tests|test system|verify changes|check.*broke|regression test|validate pipeline|update golden|test coverage|system health|smoke test|did.*change.*break"
---

# System Test Skill

## Purpose
Run the automated test framework to verify system integrity after any change.
Ensures all computation scripts, signal contracts, and cross-module integration
remain correct and consistent.

## When to Use
- After modifying ANY script in `scripts/` (compute_*.py, validate_*.py)
- After modifying signal contracts in `.instructions/signal-contracts.md`
- After modifying the data bundle schema
- After modifying the compute engine orchestrator
- When asked to verify system health or check for regressions
- Before committing changes

## Workflow

### Step 1: Run Quick Tests (always do this first)
```bash
python scripts/run_tests.py --suite quick --verbose
```
This runs unit + contract tests with NO file I/O. Takes <1 second.
If this fails, there's a code-level issue.

### Step 2: Run Full Suite (if quick passes)
```bash
python scripts/run_tests.py --suite all --verbose
```
This adds integration tests with real data bundles. Takes <5 seconds.
If this fails, there's a cross-module or data compatibility issue.

### Step 3: Read Results
```bash
# Results always saved to:
cat scripts/output/test_results_latest.json
```

### Step 4: If Tests Fail — Diagnose
1. Read the failing test to understand what it checks
2. Read the source module that changed
3. Determine: intentional change vs bug
4. If intentional: update golden refs → `python scripts/run_tests.py --golden all`
5. If bug: fix the source → re-run tests

### Step 5: Live Data Validation (optional, for thorough checks)
```bash
python scripts/run_tests.py --live AMZN
```

## Test Suite Reference

| Suite | Tests | Purpose |
|-------|-------|---------|
| `unit` | 113 | Individual function correctness |
| `contract` | 22 | Signal schema compliance |
| `integration` | 12 | Full pipeline + cross-module |
| `docs` | 36 | Architecture & documentation integrity |
| `quick` | 135 | unit + contract (fast) |
| `all` | 183 | Everything |

## Golden Reference Management

Golden references are deterministic snapshots of known-good signal outputs.
They live in `scripts/tests/golden/` as `*.golden.json` files.

**To regenerate after intentional changes:**
```bash
python scripts/run_tests.py --golden all
python scripts/run_tests.py --suite all  # verify
```

## Change Impact Matrix

| File Changed | Run Suite | Expected Impact |
|---|---|---|
| `compute_short_term.py` | `all` | Unit + contract + integration + regression |
| `compute_ccrlo.py` | `all` | Unit + contract + integration + regression |
| `compute_simulation.py` | `all` | Unit + contract + integration + regression |
| `validate_inputs.py` | `integration` | Input validation logic |
| `validate_outputs.py` | `integration` | Output validation strictness |
| `analyst_compute_engine.py` | `integration` | Orchestration + tail-risk adjustment |
| `validate_numbers.py` | N/A (separate) | Run: `python scripts/validate_numbers.py --ticker AMZN --stage B` |
| `tests/fixtures.py` | `all` | Fixture data changes affect all tests |
| Data bundle schema | `all` | May need input validator + fixture updates |
| Signal contract spec | `contract` | Contract tests + output validator |
