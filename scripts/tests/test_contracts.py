"""
Contract Tests — Signal Output Schema Validation

Ensures that signal outputs conform to the contracts defined in
.instructions/signal-contracts.md. If any script changes its output
structure, these tests catch it immediately.

Also includes regression tests against golden reference outputs.
"""

import unittest
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tests.fixtures import (
    MINIMAL_BUNDLE, DISTRESSED_BUNDLE,
    load_golden, available_bundles, load_bundle, GOLDEN_DIR,
)
from compute_short_term import compute_short_term_signal
from compute_ccrlo import compute_ccrlo_signal
from compute_simulation import compute_simulation_signal


class TestShortTermContract(unittest.TestCase):
    """SHORT_TERM_SIGNAL must conform to its contract."""

    def setUp(self):
        self.signal = compute_short_term_signal(MINIMAL_BUNDLE)

    def test_top_level_keys(self):
        required = ["ticker", "as_of", "price", "trend_break",
                     "indicators", "fragility", "correction_probabilities"]
        for key in required:
            self.assertIn(key, self.signal)

    def test_trend_break_booleans(self):
        tb = self.signal["trend_break"]
        for field in ("tb", "vs", "vf", "entry_active"):
            self.assertIn(field, tb)
            self.assertIsInstance(tb[field], bool, f"{field} must be bool")

    def test_entry_consistency(self):
        tb = self.signal["trend_break"]
        self.assertEqual(tb["entry_active"], tb["tb"] and tb["vs"] and tb["vf"])

    def test_fragility_structure(self):
        frag = self.signal["fragility"]
        self.assertIn("score", frag)
        self.assertIn("level", frag)
        self.assertIn("dimensions", frag)
        self.assertIsInstance(frag["score"], int)
        self.assertIn(frag["level"], ("LOW", "MODERATE", "HIGH"))

    def test_fragility_dimensions_complete(self):
        dims = self.signal["fragility"]["dimensions"]
        for d in ("leverage", "liquidity", "info_risk", "valuation", "momentum"):
            self.assertIn(d, dims)
            self.assertIn(dims[d], ("LOW", "HIGH"))

    def test_correction_probs_keys(self):
        cp = self.signal["correction_probabilities"]
        for k in ("mild", "standard", "severe", "black_swan"):
            self.assertIn(k, cp)
            self.assertIsInstance(cp[k], (int, float))

    def test_indicators_structure(self):
        ind = self.signal["indicators"]
        for k in ("sma_200", "sma_200_slope", "atr_14", "atr_percentile"):
            self.assertIn(k, ind)


class TestCCRLOContract(unittest.TestCase):
    """CCRLO_SIGNAL must conform to its contract."""

    def setUp(self):
        self.signal = compute_ccrlo_signal(MINIMAL_BUNDLE)

    def test_top_level_keys(self):
        for key in ("ticker", "as_of", "horizon", "features",
                     "composite_score", "correction_probability", "risk_level"):
            self.assertIn(key, self.signal)

    def test_exactly_seven_features(self):
        expected = {"term_spread", "credit_risk", "ig_credit", "volatility_regime",
                    "financial_conditions", "momentum_12m", "realized_vol"}
        self.assertEqual(set(self.signal["features"].keys()), expected)

    def test_feature_schema(self):
        for name, feat in self.signal["features"].items():
            self.assertIn("score", feat, f"{name} missing 'score'")
            self.assertIn("value", feat, f"{name} missing 'value'")
            self.assertGreaterEqual(feat["score"], 0)
            self.assertLessEqual(feat["score"], 3)

    def test_composite_score_range(self):
        self.assertGreaterEqual(self.signal["composite_score"], 0)
        self.assertLessEqual(self.signal["composite_score"], 21)

    def test_risk_level_valid(self):
        self.assertIn(self.signal["risk_level"],
                      ("LOW", "MODERATE", "ELEVATED", "HIGH", "VERY HIGH"))

    def test_composite_equals_feature_sum(self):
        expected = sum(f["score"] for f in self.signal["features"].values())
        self.assertEqual(self.signal["composite_score"], expected)


class TestSimulationContract(unittest.TestCase):
    """SIMULATION_SIGNAL must conform to its contract."""

    def setUp(self):
        st = compute_short_term_signal(MINIMAL_BUNDLE)
        cc = compute_ccrlo_signal(MINIMAL_BUNDLE)
        self.signal = compute_simulation_signal(MINIMAL_BUNDLE, st, cc)

    def test_top_level_keys(self):
        for key in ("ticker", "as_of", "price", "regime", "events", "scenarios",
                     "weighted_expected", "confidence", "composite_event_risk", "risk_color"):
            self.assertIn(key, self.signal)

    def test_regime_structure(self):
        regime = self.signal["regime"]
        self.assertIn("probabilities", regime)
        self.assertIn("dominant", regime)
        probs = regime["probabilities"]
        for r in ("calm", "trending", "stressed", "crash_prone"):
            self.assertIn(r, probs)

    def test_regime_probs_sum(self):
        total = sum(self.signal["regime"]["probabilities"].values())
        self.assertAlmostEqual(total, 1.0, delta=0.01)

    def test_six_events_three_horizons(self):
        events = self.signal["events"]
        expected_events = {"large_move", "vol_spike", "trend_reversal",
                           "earnings_reaction", "liquidity_stress", "crash_like"}
        self.assertEqual(set(events.keys()), expected_events)
        for name, ev in events.items():
            for h in ("5d", "10d", "20d"):
                self.assertIn(h, ev, f"{name} missing {h}")

    def test_four_scenarios_with_weights(self):
        scenarios = self.signal["scenarios"]
        expected = {"base_case", "vol_expansion", "trend_shift", "tail_risk"}
        self.assertEqual(set(scenarios.keys()), expected)
        total = sum(s["weight"] for s in scenarios.values())
        self.assertAlmostEqual(total, 1.0, delta=0.01)

    def test_confidence_structure(self):
        conf = self.signal["confidence"]
        self.assertIn("level", conf)
        self.assertIn("disagreement", conf)
        self.assertIn("top_drivers", conf)

    def test_risk_color_valid(self):
        self.assertIn(self.signal["risk_color"], ("GREEN", "AMBER", "RED"))


# ═══════════════════════════════════════════════════════════════
# REGRESSION TESTS — compare against golden references
# ═══════════════════════════════════════════════════════════════

class TestRegressionGolden(unittest.TestCase):
    """Compare current outputs against golden snapshots.

    If a golden reference exists, the signal's structural keys and
    numeric values must match within tolerance. This catches
    unintended drift from code changes.

    Metadata fields (as_of, price) are excluded from string comparison
    since they change with every fresh data fetch.
    """

    # Fields that change with every fresh data fetch — skip in string comparison
    METADATA_FIELDS = {"as_of", "price"}

    def _compare_dict(self, current, golden, path="", tolerance=0.5):
        """Recursively compare two dicts. Numeric differences within tolerance OK.
        Metadata fields (dates, live prices) are skipped."""
        if golden is None:
            return  # No golden ref yet
        for key in golden:
            full_key = f"{path}.{key}" if path else key
            self.assertIn(key, current, f"Key '{full_key}' missing from current output")
            g_val = golden[key]
            c_val = current.get(key)

            if isinstance(g_val, dict) and isinstance(c_val, dict):
                self._compare_dict(c_val, g_val, full_key, tolerance)
            elif isinstance(g_val, (int, float)) and isinstance(c_val, (int, float)):
                self.assertAlmostEqual(
                    c_val, g_val, delta=tolerance,
                    msg=f"Regression at '{full_key}': current={c_val}, golden={g_val}",
                )
            elif isinstance(g_val, bool):
                self.assertEqual(c_val, g_val, f"Boolean changed at '{full_key}'")
            elif isinstance(g_val, str):
                if key in self.METADATA_FIELDS:
                    continue  # Skip metadata — changes with every fresh fetch
                self.assertEqual(c_val, g_val, f"String changed at '{full_key}'")
            # Skip lists for now (too complex for deep comparison)

    def test_regression_minimal_bundle(self):
        """Minimal fixture bundle → signals match golden refs."""
        signal_st = compute_short_term_signal(MINIMAL_BUNDLE)
        golden_st = load_golden("TEST", "short_term")
        if golden_st:
            self._compare_dict(signal_st, golden_st, "st")

        signal_cc = compute_ccrlo_signal(MINIMAL_BUNDLE)
        golden_cc = load_golden("TEST", "ccrlo")
        if golden_cc:
            self._compare_dict(signal_cc, golden_cc, "cc")

    def test_regression_real_bundles(self):
        """All tickers with golden refs must match."""
        from tests.fixtures import available_golden

        for ticker in available_golden():
            try:
                data = load_bundle(ticker)
            except FileNotFoundError:
                continue

            st = compute_short_term_signal(data)
            golden_st = load_golden(ticker, "short_term")
            if golden_st:
                self._compare_dict(st, golden_st, f"{ticker}.st")

            cc = compute_ccrlo_signal(data)
            golden_cc = load_golden(ticker, "ccrlo")
            if golden_cc:
                self._compare_dict(cc, golden_cc, f"{ticker}.cc")


if __name__ == "__main__":
    unittest.main()
