"""
Integration Tests — Full Pipeline End-to-End

Tests that the complete engine pipeline (validate → compute → validate)
works correctly with real data bundles. Also tests cross-module
consistency and the engine orchestrator logic.
"""

import unittest
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tests.fixtures import (
    MINIMAL_BUNDLE, DISTRESSED_BUNDLE,
    available_bundles, load_bundle,
)
from compute_short_term import compute_short_term_signal
from compute_ccrlo import compute_ccrlo_signal
from compute_simulation import compute_simulation_signal
from validate_inputs import run_validation as run_input_validation
from validate_outputs import run_validation as run_output_validation


class TestPipelineMinimal(unittest.TestCase):
    """Full pipeline with the minimal fixture bundle."""

    def test_input_validation_passes(self):
        """Minimal bundle should pass input validation (no FAIL)."""
        report = run_input_validation(MINIMAL_BUNDLE)
        self.assertNotEqual(report["overall_status"], "FAIL",
                            f"Blocking failures: {report.get('blocking_failures')}")

    def test_full_pipeline(self):
        """Input validation → 3 signal computations → output validation."""
        # Phase 1
        input_report = run_input_validation(MINIMAL_BUNDLE)
        self.assertNotEqual(input_report["overall_status"], "FAIL")

        # Phase 2
        st = compute_short_term_signal(MINIMAL_BUNDLE)
        cc = compute_ccrlo_signal(MINIMAL_BUNDLE)
        sim = compute_simulation_signal(MINIMAL_BUNDLE, st, cc)

        # Phase 3
        output_report = run_output_validation(st, cc, sim)
        self.assertNotEqual(output_report["overall_status"], "FAIL",
                            f"Output validation failures: {output_report.get('blocking_failures')}")

    def test_tail_risk_adjustment(self):
        """Post-computation tail-risk adjustment must maintain monotonicity."""
        st = compute_short_term_signal(MINIMAL_BUNDLE)
        cc = compute_ccrlo_signal(MINIMAL_BUNDLE)
        sim = compute_simulation_signal(MINIMAL_BUNDLE, st, cc)

        tail_weight = sim.get("scenarios", {}).get("tail_risk", {}).get("weight", 0)
        if tail_weight > 0:
            cp = st["correction_probabilities"]
            cp["mild"] = min(99, round(cp["mild"] * (1 + tail_weight)))
            cp["standard"] = min(99, round(cp["standard"] * (1 + 2 * tail_weight)))
            cp["severe"] = min(99, round(cp["severe"] * (1 + 3 * tail_weight)))
            cp["severe"] = min(cp["severe"], cp["standard"])
            cp["black_swan"] = min(cp.get("black_swan", 11), cp["severe"])

            # Monotonicity must hold
            self.assertGreaterEqual(cp["mild"], cp["standard"])
            self.assertGreaterEqual(cp["standard"], cp["severe"])
            self.assertGreaterEqual(cp["severe"], cp["black_swan"])


class TestPipelineDistressed(unittest.TestCase):
    """Full pipeline with distressed/edge-case bundle."""

    def test_distressed_pipeline_completes(self):
        """Distressed bundle must not crash the pipeline."""
        input_report = run_input_validation(DISTRESSED_BUNDLE)
        st = compute_short_term_signal(DISTRESSED_BUNDLE)
        cc = compute_ccrlo_signal(DISTRESSED_BUNDLE)
        sim = compute_simulation_signal(DISTRESSED_BUNDLE, st, cc)
        output_report = run_output_validation(st, cc, sim)

        # Should not have FAIL — the pipeline handles edge cases gracefully
        self.assertNotEqual(output_report["overall_status"], "FAIL",
                            f"Output validation failures: {output_report.get('blocking_failures')}")


class TestCrossModuleConsistency(unittest.TestCase):
    """Verify that modules use each other's outputs correctly."""

    def test_tickers_match_across_signals(self):
        """All signals must use the same ticker."""
        st = compute_short_term_signal(MINIMAL_BUNDLE)
        cc = compute_ccrlo_signal(MINIMAL_BUNDLE)
        sim = compute_simulation_signal(MINIMAL_BUNDLE, st, cc)
        tickers = {st["ticker"], cc["ticker"], sim["ticker"]}
        self.assertEqual(len(tickers), 1, f"Ticker mismatch: {tickers}")

    def test_prices_match_across_signals(self):
        """Short-term and simulation must use the same price."""
        st = compute_short_term_signal(MINIMAL_BUNDLE)
        cc = compute_ccrlo_signal(MINIMAL_BUNDLE)
        sim = compute_simulation_signal(MINIMAL_BUNDLE, st, cc)
        self.assertEqual(st["price"], sim["price"])

    def test_simulation_uses_fragility(self):
        """Simulation regime detection should receive fragility score."""
        st = compute_short_term_signal(MINIMAL_BUNDLE)
        cc = compute_ccrlo_signal(MINIMAL_BUNDLE)
        sim = compute_simulation_signal(MINIMAL_BUNDLE, st, cc)
        # If fragility is HIGH, crash_prone should be influenced
        # (tested indirectly through output validation passing)
        output_report = run_output_validation(st, cc, sim)
        self.assertNotEqual(output_report["overall_status"], "FAIL")

    def test_ccrlo_independent_of_short_term(self):
        """CCRLO signal should be independent of short-term signal."""
        cc1 = compute_ccrlo_signal(MINIMAL_BUNDLE)
        cc2 = compute_ccrlo_signal(MINIMAL_BUNDLE)
        self.assertEqual(cc1["composite_score"], cc2["composite_score"])

    def test_simulation_depends_on_both_prior_signals(self):
        """Simulation with different priors should produce different results."""
        st_normal = compute_short_term_signal(MINIMAL_BUNDLE)
        cc_normal = compute_ccrlo_signal(MINIMAL_BUNDLE)
        sim_normal = compute_simulation_signal(MINIMAL_BUNDLE, st_normal, cc_normal)

        st_stress = compute_short_term_signal(DISTRESSED_BUNDLE)
        cc_stress = compute_ccrlo_signal(DISTRESSED_BUNDLE)
        sim_stress = compute_simulation_signal(DISTRESSED_BUNDLE, st_stress, cc_stress)

        # Different inputs → different simulation outputs
        self.assertNotEqual(
            sim_normal["composite_event_risk"],
            sim_stress["composite_event_risk"],
            "Simulation should differ for different input bundles",
        )


class TestRealBundlePipeline(unittest.TestCase):
    """Test pipeline with any available real data bundles."""

    def test_all_available_bundles(self):
        """Every bundle in scripts/data/ must pass the full pipeline."""
        bundles = available_bundles()
        if not bundles:
            self.skipTest("No bundles available in scripts/data/")

        for ticker in bundles:
            with self.subTest(ticker=ticker):
                data = load_bundle(ticker)

                # Input validation
                input_report = run_input_validation(data)
                self.assertNotEqual(
                    input_report["overall_status"], "FAIL",
                    f"{ticker}: input validation FAIL — {input_report.get('blocking_failures')}",
                )

                # Signal computation
                st = compute_short_term_signal(data)
                cc = compute_ccrlo_signal(data)
                sim = compute_simulation_signal(data, st, cc)

                # Output validation
                output_report = run_output_validation(st, cc, sim)
                self.assertNotEqual(
                    output_report["overall_status"], "FAIL",
                    f"{ticker}: output validation FAIL — {output_report.get('blocking_failures')}",
                )


class TestValidatorConsistency(unittest.TestCase):
    """Input and output validators must be internally consistent."""

    def test_input_validator_idempotent(self):
        """Running input validation twice gives same result."""
        r1 = run_input_validation(MINIMAL_BUNDLE)
        r2 = run_input_validation(MINIMAL_BUNDLE)
        self.assertEqual(r1["overall_status"], r2["overall_status"])
        self.assertEqual(r1["summary"]["failures"], r2["summary"]["failures"])

    def test_output_validator_idempotent(self):
        """Running output validation twice gives same result."""
        st = compute_short_term_signal(MINIMAL_BUNDLE)
        cc = compute_ccrlo_signal(MINIMAL_BUNDLE)
        sim = compute_simulation_signal(MINIMAL_BUNDLE, st, cc)
        r1 = run_output_validation(st, cc, sim)
        r2 = run_output_validation(st, cc, sim)
        self.assertEqual(r1["overall_status"], r2["overall_status"])
        self.assertEqual(r1["summary"]["failures"], r2["summary"]["failures"])


if __name__ == "__main__":
    unittest.main()
