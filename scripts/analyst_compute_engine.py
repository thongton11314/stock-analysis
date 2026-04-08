"""
Analyst Compute Engine — Unified Signal Computation Pipeline

Single-command orchestrator that runs the full computation pipeline:
  0. Pre-flight system integrity check (--verify, on by default)
  1. Validate inputs (data bundle)
  2. Compute SHORT_TERM_SIGNAL (TB/VS/VF + Fragility)
  3. Compute CCRLO_SIGNAL (7-feature scoring)
  4. Compute SIMULATION_SIGNAL (regime + events + scenarios)
  5. Validate outputs (signal contracts + cross-signal consistency)

Usage:
    python scripts/analyst_compute_engine.py --ticker AMZN
    python scripts/analyst_compute_engine.py --ticker AMZN --no-verify  # skip pre-flight

    This expects:
      Input:  scripts/data/AMZN_bundle.json
    Produces:
      scripts/output/AMZN_short_term.json
      scripts/output/AMZN_ccrlo.json
      scripts/output/AMZN_simulation.json
      scripts/output/AMZN_tags.json            (stock classification tags)
      scripts/output/AMZN_engine_report.json   (unified validation report)

Exit codes:
    0 = All phases passed (PASS or WARN)
    1 = Input validation failed (blocking)
    2 = Computation failed (script error)
    3 = Output validation failed (blocking)
    4 = Pre-flight integrity check failed (system inconsistency)
"""

import argparse
import json
import os
import sys
from datetime import datetime

# Ensure scripts/ is on the path so imports work from any cwd
_script_dir = os.path.dirname(os.path.abspath(__file__))
if _script_dir not in sys.path:
    sys.path.insert(0, _script_dir)

from compute_short_term import compute_short_term_signal
from compute_ccrlo import compute_ccrlo_signal
from compute_simulation import compute_simulation_signal
from compute_tags import compute_tags, validate_tags, update_index
from validate_inputs import run_validation as run_input_validation
from validate_outputs import run_validation as run_output_validation


def ensure_dirs():
    """Create data/ and output/ directories if they don't exist."""
    os.makedirs("scripts/data", exist_ok=True)
    os.makedirs("scripts/output", exist_ok=True)


def phase_input_validation(ticker: str, data: dict) -> dict:
    """Phase 1: Validate the data bundle."""
    print(f"\n{'='*60}")
    print(f"PHASE 1: INPUT VALIDATION — {ticker}")
    print(f"{'='*60}")

    report = run_input_validation(data)

    status = report["overall_status"]
    s = report["summary"]
    print(f"  Status: {status}")
    print(f"  Passed: {s['passed']} | Warnings: {s['warnings']} | Failures: {s['failures']}")

    if report["blocking_failures"]:
        print(f"  BLOCKING: {', '.join(report['blocking_failures'])}")

    return report


def phase_computation(ticker: str, data: dict) -> tuple[dict, dict, dict]:
    """Phase 2: Run all three signal computations."""
    print(f"\n{'='*60}")
    print(f"PHASE 2: SIGNAL COMPUTATION — {ticker}")
    print(f"{'='*60}")

    # Step 1: Short-term (standalone)
    print("  Computing SHORT_TERM_SIGNAL...")
    short_term = compute_short_term_signal(data)
    tb = short_term["trend_break"]
    frag = short_term["fragility"]
    print(f"    TB={tb['tb']} VS={tb['vs']} VF={tb['vf']} | Entry={tb['entry_active']}")
    print(f"    Fragility: {frag['score']}/5 ({frag['level']})")

    # Step 2: CCRLO (standalone)
    print("  Computing CCRLO_SIGNAL...")
    ccrlo = compute_ccrlo_signal(data)
    print(f"    Score: {ccrlo['composite_score']}/21 | Prob: {ccrlo['correction_probability']}% | Level: {ccrlo['risk_level']}")

    # Step 3: Simulation (depends on short_term + ccrlo)
    print("  Computing SIMULATION_SIGNAL...")
    simulation = compute_simulation_signal(data, short_term, ccrlo)
    print(f"    Regime: {simulation['regime']['dominant']}")
    print(f"    Event Risk: {simulation['composite_event_risk']}% ({simulation['risk_color']})")
    print(f"    Confidence: {simulation['confidence']['level']}")

    return short_term, ccrlo, simulation


def phase_output_validation(short_term: dict, ccrlo: dict, simulation: dict) -> dict:
    """Phase 3: Validate all computed signals."""
    print(f"\n{'='*60}")
    print(f"PHASE 3: OUTPUT VALIDATION")
    print(f"{'='*60}")

    report = run_output_validation(short_term, ccrlo, simulation)

    status = report["overall_status"]
    s = report["summary"]
    print(f"  Status: {status}")
    print(f"  Passed: {s['passed']} | Warnings: {s['warnings']} | Failures: {s['failures']}")

    if report["blocking_failures"]:
        print(f"  BLOCKING: {', '.join(report['blocking_failures'])}")

    return report


def write_json(path: str, data: dict):
    """Write JSON to file."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _run_preflight_check() -> bool:
    """Phase 0: Run the quick test suite to verify system integrity.

    Returns True if all tests pass, False if any fail.
    This catches cases where a system file was modified but
    related files weren't updated — before wasting time on computation.
    """
    import unittest
    import io

    print(f"\n{'='*60}")
    print(f"PHASE 0: PRE-FLIGHT SYSTEM INTEGRITY CHECK")
    print(f"{'='*60}")

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Load the quick suite (unit + contract) — fast, no I/O
    quick_modules = [
        "tests.test_unit_short_term",
        "tests.test_unit_ccrlo",
        "tests.test_unit_simulation",
        "tests.test_unit_tags",
        "tests.test_contracts",
    ]

    for module_name in quick_modules:
        try:
            suite.addTests(loader.loadTestsFromName(module_name))
        except Exception as e:
            print(f"  ERROR loading {module_name}: {e}")
            return False

    # Count tests
    test_count = 0
    for test_group in suite:
        if isinstance(test_group, unittest.TestSuite):
            for _ in test_group:
                test_count += 1
        else:
            test_count += 1

    print(f"  Running {test_count} quick tests (unit + contract)...")

    # Run silently — capture output
    stream = io.StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=0)
    result = runner.run(suite)

    passed = test_count - len(result.failures) - len(result.errors)
    failed = len(result.failures) + len(result.errors)

    if failed == 0:
        print(f"  PASS: {passed}/{test_count} tests passed")
        return True
    else:
        print(f"  FAIL: {failed} test(s) failed out of {test_count}")
        for test, _ in result.failures:
            print(f"    FAILED: {test}")
        for test, _ in result.errors:
            print(f"    ERROR: {test}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Analyst Compute Engine — unified signal computation pipeline"
    )
    parser.add_argument("--ticker", required=True, help="Ticker symbol (e.g., AMZN)")
    parser.add_argument("--no-verify", action="store_true",
                        help="Skip pre-flight system integrity check")
    args = parser.parse_args()

    ticker = args.ticker.upper()
    bundle_path = f"scripts/data/{ticker}_bundle.json"

    # Check input exists
    if not os.path.exists(bundle_path):
        print(f"ERROR: Data bundle not found: {bundle_path}")
        print(f"  The agent must write the data bundle before running the engine.")
        sys.exit(1)

    ensure_dirs()

    # ─────────────────────────────────────────────
    # PHASE 0: Pre-Flight System Integrity Check
    # ─────────────────────────────────────────────
    if not args.no_verify:
        if not _run_preflight_check():
            print(f"\n[FAIL] ENGINE ABORTED: Pre-flight integrity check failed.")
            print(f"   The system has inconsistencies — fix them before computing signals.")
            print(f"   Run: python scripts/run_tests.py --suite quick --verbose")
            print(f"   Use --no-verify to bypass (not recommended).")
            sys.exit(4)

    # Load data bundle
    with open(bundle_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    started_at = datetime.now()
    engine_report = {
        "ticker": ticker,
        "started_at": started_at.strftime("%Y-%m-%dT%H:%M:%S"),
        "phases": {},
    }

    # ─────────────────────────────────────────────
    # PHASE 1: Input Validation
    # ─────────────────────────────────────────────
    input_report = phase_input_validation(ticker, data)
    engine_report["phases"]["input_validation"] = input_report["overall_status"]

    if input_report["overall_status"] == "FAIL":
        engine_report["overall_status"] = "INPUT_VALIDATION_FAILED"
        engine_report["blocking_failures"] = input_report["blocking_failures"]
        write_json(f"scripts/output/{ticker}_engine_report.json", engine_report)
        print(f"\n[FAIL] ENGINE ABORTED: Input validation failed for {ticker}")
        print(f"   Fix the data bundle and re-run.")
        sys.exit(1)

    # Save input validation report
    write_json(f"scripts/data/{ticker}_input_validation.json", input_report)

    # ─────────────────────────────────────────────
    # PHASE 2: Computation
    # ─────────────────────────────────────────────
    try:
        short_term, ccrlo, simulation = phase_computation(ticker, data)
    except Exception as e:
        engine_report["phases"]["computation"] = "ERROR"
        engine_report["overall_status"] = "COMPUTATION_FAILED"
        engine_report["error"] = str(e)
        write_json(f"scripts/output/{ticker}_engine_report.json", engine_report)
        print(f"\n❌ ENGINE ABORTED: Computation error for {ticker}: {e}")
        sys.exit(2)

    engine_report["phases"]["computation"] = "COMPLETE"

    # ─────────────────────────────────────────────
    # PHASE 2b: Post-Computation Adjustments
    # ─────────────────────────────────────────────
    # Apply tail-risk scenario weight from simulation to short-term correction probs.
    # Per spec: Mild × (1+tail), Standard × (1+2×tail), Severe × (1+3×tail)
    tail_weight = simulation.get("scenarios", {}).get("tail_risk", {}).get("weight", 0)
    if tail_weight > 0:
        cp = short_term.get("correction_probabilities", {})
        cp["mild"] = min(99, round(cp.get("mild", 85) * (1 + tail_weight)))
        cp["standard"] = min(99, round(cp.get("standard", 52) * (1 + 2 * tail_weight)))
        cp["severe"] = min(99, round(cp.get("severe", 32) * (1 + 3 * tail_weight)))
        # black_swan not multiplied by tail formula per spec

        # B4 fix: Enforce monotonicity invariant (mild >= standard >= severe >= black_swan)
        # after tail-risk adjustment, the scaling factors can break ordering
        cp["severe"] = min(cp["severe"], cp["standard"])
        cp["black_swan"] = min(cp.get("black_swan", 11), cp["severe"])

        short_term["correction_probabilities"] = cp
        short_term["_tail_risk_applied"] = round(tail_weight, 3)
        print(f"  Post-adjustment: tail_weight={tail_weight:.3f} applied to correction probs")
        print(f"    Mild={cp['mild']}% Std={cp['standard']}% Severe={cp['severe']}% BS={cp['black_swan']}%")

    # Save signal outputs
    write_json(f"scripts/output/{ticker}_short_term.json", short_term)
    write_json(f"scripts/output/{ticker}_ccrlo.json", ccrlo)
    write_json(f"scripts/output/{ticker}_simulation.json", simulation)

    # ─────────────────────────────────────────────
    # PHASE 2.5: Tag Classification
    # ─────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"PHASE 2.5: TAG CLASSIFICATION — {ticker}")
    print(f"{'='*60}")

    tag_signal = compute_tags(data, short_term, ccrlo, simulation)
    tag_checks = validate_tags(tag_signal)
    tag_fails = [c for c in tag_checks if c["status"] == "FAIL"]

    if tag_fails:
        print(f"  TAG VALIDATION FAILED:")
        for c in tag_fails:
            print(f"    {c['field']}: {c['reason']}")
        engine_report["phases"]["tags"] = "FAIL"
    else:
        for dim, dim_tags in tag_signal["tags"].items():
            print(f"  {dim}: {', '.join(dim_tags)}")
        print(f"  Primary: {tag_signal['primary_tag']}")
        engine_report["phases"]["tags"] = "COMPLETE"
        write_json(f"scripts/output/{ticker}_tags.json", tag_signal)
        update_index(tag_signal)

    # ─────────────────────────────────────────────
    # PHASE 3: Output Validation
    # ─────────────────────────────────────────────
    output_report = phase_output_validation(short_term, ccrlo, simulation)
    engine_report["phases"]["output_validation"] = output_report["overall_status"]

    # Save output validation report
    write_json(f"scripts/output/{ticker}_output_validation.json", output_report)

    if output_report["overall_status"] == "FAIL":
        engine_report["overall_status"] = "OUTPUT_VALIDATION_FAILED"
        engine_report["blocking_failures"] = output_report["blocking_failures"]
        write_json(f"scripts/output/{ticker}_engine_report.json", engine_report)
        print(f"\n[FAIL] ENGINE FAILED: Output validation failed for {ticker}")
        print(f"   Review blocking_failures in scripts/output/{ticker}_engine_report.json")
        sys.exit(3)

    # ─────────────────────────────────────────────
    # SUCCESS
    # ─────────────────────────────────────────────
    finished_at = datetime.now()
    engine_report["finished_at"] = finished_at.strftime("%Y-%m-%dT%H:%M:%S")
    engine_report["duration_seconds"] = (finished_at - started_at).total_seconds()
    engine_report["overall_status"] = "PASS" if output_report["overall_status"] == "PASS" else "WARN"

    # Signal summary for quick reference
    engine_report["signal_summary"] = {
        "short_term": {
            "entry_active": short_term["trend_break"]["entry_active"],
            "fragility": f"{short_term['fragility']['score']}/5 ({short_term['fragility']['level']})",
        },
        "ccrlo": {
            "score": f"{ccrlo['composite_score']}/21",
            "risk_level": ccrlo["risk_level"],
            "correction_probability": f"{ccrlo['correction_probability']}%",
        },
        "simulation": {
            "regime": simulation["regime"]["dominant"],
            "event_risk": f"{simulation['composite_event_risk']}% ({simulation['risk_color']})",
            "confidence": simulation["confidence"]["level"],
        },
        "tags": {
            "primary_tag": tag_signal.get("primary_tag", "unknown"),
            "profile": tag_signal.get("tags", {}).get("profile", []),
            "risk": tag_signal.get("tags", {}).get("risk", []),
        },
    }

    engine_report["output_files"] = {
        "short_term": f"scripts/output/{ticker}_short_term.json",
        "ccrlo": f"scripts/output/{ticker}_ccrlo.json",
        "simulation": f"scripts/output/{ticker}_simulation.json",
        "tags": f"scripts/output/{ticker}_tags.json",
        "engine_report": f"scripts/output/{ticker}_engine_report.json",
    }

    write_json(f"scripts/output/{ticker}_engine_report.json", engine_report)

    print(f"\n{'='*60}")
    print(f"[OK] ENGINE COMPLETE: {ticker}")
    print(f"{'='*60}")
    print(f"  Status: {engine_report['overall_status']}")
    print(f"  Duration: {engine_report['duration_seconds']:.1f}s")
    print(f"  Short-Term: TB={short_term['trend_break']['entry_active']} | Fragility {short_term['fragility']['score']}/5")
    print(f"  CCRLO: {ccrlo['composite_score']}/21 ({ccrlo['risk_level']})")
    print(f"  Simulation: {simulation['regime']['dominant']} regime | Event Risk {simulation['composite_event_risk']}%")
    print(f"  Tags: {tag_signal.get('primary_tag', 'N/A')}")
    print(f"  Output: scripts/output/{ticker}_*.json")

    sys.exit(0)


if __name__ == "__main__":
    main()
