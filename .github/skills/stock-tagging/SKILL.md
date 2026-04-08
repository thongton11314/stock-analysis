---
name: stock-tagging
description: >
  Classify stocks with deterministic tags across 5 dimensions: Profile, Sector,
  Risk, Momentum, Valuation. Produces TAG_SIGNAL JSON and updates the cross-ticker
  index for portfolio screening and comparison.
  USE FOR: "tag TICKER", "classify TICKER", "what type of stock is TICKER",
  "show all high-risk tickers", "compare tags", "stock classification",
  "filter by sector", "portfolio screening", "tag query".
  DO NOT USE FOR: generating reports (use report-generation), computing signals
  (use analyst-compute-engine), fixing reports (use report-fix).
---

# Stock Tagging Skill

## Overview

Assigns deterministic classification tags to tickers using computed signal data.
Tags are derived from the data bundle + SHORT_TERM + CCRLO + SIMULATION signals —
never inferred by AI.

**Reference**: `.instructions/tag-taxonomy.md` for full taxonomy, thresholds, and rules.

## Prerequisites

Before tagging, the ticker must have:
1. A data bundle at `scripts/data/[TICKER]_bundle.json`
2. All 3 signal outputs at `scripts/output/[TICKER]_*.json`

If these don't exist, run data collection + compute engine first.

## Workflow

### Phase 1: Verify Inputs Exist
```
Check: scripts/data/[TICKER]_bundle.json exists
Check: scripts/output/[TICKER]_short_term.json exists
Check: scripts/output/[TICKER]_ccrlo.json exists
Check: scripts/output/[TICKER]_simulation.json exists
```

If missing → direct user to run data-collection + analyst-compute-engine first.

### Phase 2: Compute Tags
```bash
python scripts/compute_tags.py --ticker [TICKER]
```

This will:
1. Load bundle + all 3 signal outputs
2. Classify across 5 dimensions (Profile, Sector, Risk, Momentum, Valuation)
3. Validate all tags against the taxonomy
4. Save to `scripts/output/[TICKER]_tags.json`
5. Update `scripts/output/tags_index.json` (cross-ticker registry)

### Phase 3: Report Results

Display the tag results to the user:
```
TAGS COMPUTED: [TICKER]
  Profile:   mega-cap, mature
  Sector:    consumer-cyclical, cloud, e-commerce
  Risk:      elevated-risk
  Momentum:  bearish, below-200sma
  Valuation: fair-value
  Primary:   mega-cap-bearish-elevated-risk
```

## Query Mode

To query existing tags across all analyzed tickers:

```bash
# Show all tagged tickers
python scripts/compute_tags.py --ticker ANY --query all

# Filter by dimension + tag
python scripts/compute_tags.py --ticker ANY --query filter --dimension risk --tag high-risk
python scripts/compute_tags.py --ticker ANY --query filter --dimension sector --tag fintech
```

## Integration with Reports

When generating HTML reports, tags from `[TICKER]_tags.json` should be rendered
as colored pill badges in the report header (Section 2 area), using CSS classes:
- `.tag-profile` (blue)
- `.tag-sector` (purple)
- `.tag-risk` (color varies by risk level)
- `.tag-momentum` (green/red/amber)
- `.tag-valuation` (teal)

## Tag Dimensions Quick Reference

| Dimension | Source | Example Tags |
|---|---|---|
| Profile | Market cap + IPO age | `mega-cap`, `post-ipo`, `pre-profit` |
| Sector | AV sector + keywords | `technology`, `fintech`, `ai`, `cloud` |
| Risk | CCRLO + TB + regime | `low-risk`, `high-risk`, `crash-prone` |
| Momentum | SMA + RSI + slope | `bullish`, `bearish`, `oversold` |
| Valuation | P/E vs sector norms | `deep-value`, `fair-value`, `overvalued` |
