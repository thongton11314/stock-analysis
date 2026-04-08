"""
Signal Output Validator

Validates computed signal outputs against the contracts defined in
.instructions/signal-contracts.md. Checks structural completeness,
mathematical constraints, bounds, and cross-signal consistency.

Usage:
    python scripts/validate_outputs.py \
        --short-term short_term_signal.json \
        --ccrlo ccrlo_signal.json \
        --simulation simulation_signal.json \
        --output validation_report.json
"""

import argparse
import json
import sys
from datetime import datetime


def validate_short_term(signal: dict) -> list[dict]:
    """Validate SHORT_TERM_SIGNAL contract."""
    checks = []

    # Structure checks
    for field in ("ticker", "as_of", "price", "trend_break", "indicators", "fragility", "correction_probabilities"):
        if field in signal:
            checks.append({"field": f"st.{field}", "status": "PASS", "reason": "Present"})
        else:
            checks.append({"field": f"st.{field}", "status": "FAIL", "reason": "Missing required field"})

    # Trend break fields
    tb = signal.get("trend_break", {})
    for f in ("tb", "vs", "vf", "entry_active"):
        if f in tb:
            if not isinstance(tb[f], bool):
                checks.append({"field": f"st.tb.{f}", "status": "FAIL", "reason": f"Must be boolean, got {type(tb[f]).__name__}"})
            else:
                checks.append({"field": f"st.tb.{f}", "status": "PASS", "reason": str(tb[f])})
        else:
            checks.append({"field": f"st.tb.{f}", "status": "FAIL", "reason": "Missing"})

    # Entry signal consistency: entry_active must equal tb AND vs AND vf
    if all(f in tb for f in ("tb", "vs", "vf", "entry_active")):
        expected = tb["tb"] and tb["vs"] and tb["vf"]
        if tb["entry_active"] == expected:
            checks.append({"field": "st.entry_consistency", "status": "PASS", "reason": "entry = tb AND vs AND vf"})
        else:
            checks.append({"field": "st.entry_consistency", "status": "FAIL", "reason": f"entry_active={tb['entry_active']} but tb={tb['tb']} vs={tb['vs']} vf={tb['vf']}"})

    # Fragility score
    frag = signal.get("fragility", {})
    score = frag.get("score")
    level = frag.get("level")
    if score is not None:
        if 0 <= score <= 5:
            checks.append({"field": "st.fragility.score", "status": "PASS", "reason": f"{score}/5"})
        else:
            checks.append({"field": "st.fragility.score", "status": "FAIL", "reason": f"Score {score} out of [0,5]"})

        # Level must match score range
        expected_level = "LOW" if score <= 1 else ("MODERATE" if score <= 3 else "HIGH")
        if level == expected_level:
            checks.append({"field": "st.fragility.level", "status": "PASS", "reason": level})
        else:
            checks.append({"field": "st.fragility.level", "status": "FAIL", "reason": f"Level '{level}' but score={score} expects '{expected_level}'"})

    # Fragility dimensions
    dims = frag.get("dimensions", {})
    for dim in ("leverage", "liquidity", "info_risk", "valuation", "momentum"):
        val = dims.get(dim)
        if val in ("LOW", "HIGH"):
            checks.append({"field": f"st.frag.{dim}", "status": "PASS", "reason": val})
        elif val is None:
            checks.append({"field": f"st.frag.{dim}", "status": "FAIL", "reason": "Missing"})
        else:
            checks.append({"field": f"st.frag.{dim}", "status": "FAIL", "reason": f"Must be LOW|HIGH, got '{val}'"})

    # Dimension count must match score
    if score is not None and dims:
        high_count = sum(1 for v in dims.values() if v == "HIGH")
        if high_count == score:
            checks.append({"field": "st.frag.count", "status": "PASS", "reason": f"{high_count} HIGH dims = score {score}"})
        else:
            checks.append({"field": "st.frag.count", "status": "FAIL", "reason": f"{high_count} HIGH dims ≠ score {score}"})

    # Correction probabilities: mild > standard > severe > black_swan
    cp = signal.get("correction_probabilities", {})
    if all(k in cp for k in ("mild", "standard", "severe", "black_swan")):
        if cp["mild"] >= cp["standard"] >= cp["severe"] >= cp["black_swan"]:
            checks.append({"field": "st.corr_monotonic", "status": "PASS", "reason": "Monotonically decreasing"})
        else:
            checks.append({"field": "st.corr_monotonic", "status": "FAIL", "reason": f"Not monotonic: {cp}"})

    return checks


def validate_ccrlo(signal: dict) -> list[dict]:
    """Validate CCRLO_SIGNAL contract."""
    checks = []

    # Structure
    for field in ("ticker", "as_of", "horizon", "features", "composite_score", "correction_probability", "risk_level"):
        if field in signal:
            checks.append({"field": f"cc.{field}", "status": "PASS", "reason": "Present"})
        else:
            checks.append({"field": f"cc.{field}", "status": "FAIL", "reason": "Missing"})

    # Features: 7 features, each scored 0-3
    features = signal.get("features", {})
    expected_features = ["term_spread", "credit_risk", "ig_credit", "volatility_regime",
                         "financial_conditions", "momentum_12m", "realized_vol"]

    for feat_name in expected_features:
        feat = features.get(feat_name)
        if feat is None:
            checks.append({"field": f"cc.feat.{feat_name}", "status": "FAIL", "reason": "Missing"})
            continue
        s = feat.get("score")
        if s is not None and 0 <= s <= 3:
            checks.append({"field": f"cc.feat.{feat_name}", "status": "PASS", "reason": f"Score={s}"})
        else:
            checks.append({"field": f"cc.feat.{feat_name}", "status": "FAIL", "reason": f"Score {s} out of [0,3]"})

    # Composite score = sum of feature scores
    composite = signal.get("composite_score")
    if composite is not None:
        expected_sum = sum(features.get(f, {}).get("score", 0) for f in expected_features)
        if composite == expected_sum:
            checks.append({"field": "cc.composite_sum", "status": "PASS", "reason": f"{composite} = sum of features"})
        else:
            checks.append({"field": "cc.composite_sum", "status": "FAIL", "reason": f"Composite {composite} ≠ sum {expected_sum}"})

        if 0 <= composite <= 21:
            checks.append({"field": "cc.composite_range", "status": "PASS", "reason": f"{composite}/21"})
        else:
            checks.append({"field": "cc.composite_range", "status": "FAIL", "reason": f"Score {composite} out of [0,21]"})

    # Risk level matches score range
    risk_level = signal.get("risk_level")
    if composite is not None and risk_level:
        expected_levels = {
            range(0, 4): "LOW", range(4, 8): "MODERATE", range(8, 12): "ELEVATED",
            range(12, 16): "HIGH", range(16, 22): "VERY HIGH",
        }
        expected_rl = next((v for k, v in expected_levels.items() if composite in k), None)
        if risk_level == expected_rl:
            checks.append({"field": "cc.risk_level", "status": "PASS", "reason": risk_level})
        else:
            checks.append({"field": "cc.risk_level", "status": "FAIL", "reason": f"'{risk_level}' but score {composite} expects '{expected_rl}'"})

    return checks


def validate_simulation(signal: dict) -> list[dict]:
    """Validate SIMULATION_SIGNAL contract."""
    checks = []

    # Structure
    for field in ("ticker", "as_of", "price", "regime", "events", "scenarios",
                   "weighted_expected", "confidence", "composite_event_risk", "risk_color"):
        if field in signal:
            checks.append({"field": f"sim.{field}", "status": "PASS", "reason": "Present"})
        else:
            checks.append({"field": f"sim.{field}", "status": "FAIL", "reason": "Missing"})

    # Regime probabilities must sum to 1.0
    regime = signal.get("regime", {})
    probs = regime.get("probabilities", {})
    if probs:
        total = sum(probs.values())
        if abs(total - 1.0) <= 0.01:
            checks.append({"field": "sim.regime_sum", "status": "PASS", "reason": f"Sum={total:.3f}"})
        else:
            checks.append({"field": "sim.regime_sum", "status": "FAIL", "reason": f"Sum={total:.3f}, must be 1.0 ±0.01"})

        # All probs non-negative
        if all(v >= 0 for v in probs.values()):
            checks.append({"field": "sim.regime_nonneg", "status": "PASS", "reason": "All non-negative"})
        else:
            checks.append({"field": "sim.regime_nonneg", "status": "FAIL", "reason": "Negative probability found"})

        # Dominant matches max
        dominant = regime.get("dominant")
        max_regime = max(probs, key=probs.get) if probs else None
        if dominant == max_regime:
            checks.append({"field": "sim.regime_dominant", "status": "PASS", "reason": dominant})
        else:
            checks.append({"field": "sim.regime_dominant", "status": "FAIL", "reason": f"Dominant='{dominant}' but max is '{max_regime}'"})

    # Event probability bounds
    events = signal.get("events", {})
    expected_events = ["large_move", "vol_spike", "trend_reversal", "earnings_reaction", "liquidity_stress", "crash_like"]
    for event_name in expected_events:
        event = events.get(event_name, {})
        for horizon in ("5d", "10d", "20d"):
            val = event.get(horizon)
            if val is None:
                checks.append({"field": f"sim.ev.{event_name}.{horizon}", "status": "FAIL", "reason": "Missing"})
                continue

            cap = 35 if event_name == "crash_like" else 85
            if 1 <= val <= cap:
                checks.append({"field": f"sim.ev.{event_name}.{horizon}", "status": "PASS", "reason": f"{val}%"})
            else:
                checks.append({"field": f"sim.ev.{event_name}.{horizon}", "status": "FAIL", "reason": f"{val}% out of [1,{cap}]"})

    # Scenario weights must sum to 1.0
    scenarios = signal.get("scenarios", {})
    expected_scenarios = ["base_case", "vol_expansion", "trend_shift", "tail_risk"]
    weights = [scenarios.get(s, {}).get("weight", 0) for s in expected_scenarios]
    weight_sum = sum(weights)
    if abs(weight_sum - 1.0) <= 0.01:
        checks.append({"field": "sim.scenario_sum", "status": "PASS", "reason": f"Sum={weight_sum:.3f}"})
    else:
        checks.append({"field": "sim.scenario_sum", "status": "FAIL", "reason": f"Sum={weight_sum:.3f}, must be 1.0 ±0.01"})

    # All scenario weights non-negative
    if all(w >= 0 for w in weights):
        checks.append({"field": "sim.scenario_nonneg", "status": "PASS", "reason": "All non-negative"})
    else:
        checks.append({"field": "sim.scenario_nonneg", "status": "FAIL", "reason": "Negative weight found"})

    # Risk color matches composite
    cer = signal.get("composite_event_risk", 0)
    color = signal.get("risk_color")
    if cer < 15:
        expected_color = "GREEN"
    elif cer <= 30:
        expected_color = "AMBER"
    else:
        expected_color = "RED"
    if color == expected_color:
        checks.append({"field": "sim.risk_color", "status": "PASS", "reason": f"{cer}% → {color}"})
    else:
        checks.append({"field": "sim.risk_color", "status": "FAIL", "reason": f"CER={cer}% expects {expected_color}, got {color}"})

    return checks


def validate_cross_signal(short_term: dict, ccrlo: dict, simulation: dict) -> list[dict]:
    """Validate consistency between signals."""
    checks = []

    ccrlo_score = ccrlo.get("composite_score", 0)
    fragility_score = short_term.get("fragility", {}).get("score", 0)
    tb_active = short_term.get("trend_break", {}).get("entry_active", False)
    crash_prone = simulation.get("regime", {}).get("probabilities", {}).get("crash_prone", 0)

    # If CCRLO >= 12, crash_prone should be > 0.15
    if ccrlo_score >= 12 and crash_prone < 0.15:
        checks.append({"field": "cross.ccrlo_crash", "status": "WARN", "reason": f"CCRLO={ccrlo_score} (HIGH) but crash_prone={crash_prone:.2f} <0.15"})
    elif ccrlo_score >= 12:
        checks.append({"field": "cross.ccrlo_crash", "status": "PASS", "reason": f"CCRLO={ccrlo_score}, crash_prone={crash_prone:.2f}"})

    # If fragility >= 3, crash_prone should be > 0.15
    if fragility_score >= 3 and crash_prone < 0.15:
        checks.append({"field": "cross.frag_crash", "status": "WARN", "reason": f"Fragility={fragility_score} (HIGH) but crash_prone={crash_prone:.2f} <0.15"})
    elif fragility_score >= 3:
        checks.append({"field": "cross.frag_crash", "status": "PASS", "reason": f"Fragility={fragility_score}, crash_prone={crash_prone:.2f}"})

    # If TB active AND fragility >= 3, composite_event_risk should be elevated (>20%)
    cer = simulation.get("composite_event_risk", 0)
    if tb_active and fragility_score >= 3:
        if cer > 20:
            checks.append({"field": "cross.tb_frag_cer", "status": "PASS", "reason": f"TB active + fragility {fragility_score}: CER={cer}%"})
        else:
            checks.append({"field": "cross.tb_frag_cer", "status": "WARN", "reason": f"TB active + fragility {fragility_score} but CER={cer}% ≤20%"})

    # Tickers must match
    tickers = {short_term.get("ticker"), ccrlo.get("ticker"), simulation.get("ticker")}
    tickers.discard(None)
    if len(tickers) == 1:
        checks.append({"field": "cross.ticker_match", "status": "PASS", "reason": tickers.pop()})
    else:
        checks.append({"field": "cross.ticker_match", "status": "FAIL", "reason": f"Ticker mismatch: {tickers}"})

    return checks


def run_validation(short_term: dict, ccrlo: dict, simulation: dict) -> dict:
    """Run all output validation checks."""
    all_checks = []
    all_checks.extend(validate_short_term(short_term))
    all_checks.extend(validate_ccrlo(ccrlo))
    all_checks.extend(validate_simulation(simulation))
    all_checks.extend(validate_cross_signal(short_term, ccrlo, simulation))

    fails = [c for c in all_checks if c["status"] == "FAIL"]
    warns = [c for c in all_checks if c["status"] == "WARN"]
    passes = [c for c in all_checks if c["status"] == "PASS"]

    overall = "FAIL" if fails else ("WARN" if warns else "PASS")

    return {
        "validated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "overall_status": overall,
        "summary": {
            "total_checks": len(all_checks),
            "passed": len(passes),
            "warnings": len(warns),
            "failures": len(fails),
        },
        "checks": all_checks,
        "blocking_failures": [c["field"] for c in fails],
    }


def main():
    parser = argparse.ArgumentParser(description="Validate computed signal outputs")
    parser.add_argument("--short-term", required=True, help="Path to SHORT_TERM_SIGNAL JSON")
    parser.add_argument("--ccrlo", required=True, help="Path to CCRLO_SIGNAL JSON")
    parser.add_argument("--simulation", required=True, help="Path to SIMULATION_SIGNAL JSON")
    parser.add_argument("--output", required=True, help="Path to write validation report JSON")
    args = parser.parse_args()

    with open(getattr(args, "short_term"), "r", encoding="utf-8") as f:
        short_term = json.load(f)
    with open(args.ccrlo, "r", encoding="utf-8") as f:
        ccrlo = json.load(f)
    with open(args.simulation, "r", encoding="utf-8") as f:
        simulation = json.load(f)

    report = run_validation(short_term, ccrlo, simulation)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"OUTPUT VALIDATION:")
    print(f"  Overall: {report['overall_status']}")
    print(f"  Passed: {report['summary']['passed']} | Warnings: {report['summary']['warnings']} | Failures: {report['summary']['failures']}")
    if report["blocking_failures"]:
        print(f"  BLOCKING FAILURES: {', '.join(report['blocking_failures'])}")

    sys.exit(0 if report["overall_status"] != "FAIL" else 1)


if __name__ == "__main__":
    main()
