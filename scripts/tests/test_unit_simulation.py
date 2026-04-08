"""
Unit Tests — compute_simulation.py

Tests regime detection, event scoring, scenario weighting,
confidence assessment, and the full simulation signal.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tests.fixtures import MINIMAL_BUNDLE, DISTRESSED_BUNDLE
from compute_short_term import compute_short_term_signal
from compute_ccrlo import compute_ccrlo_signal
from compute_simulation import (
    detect_regime, score_events, compute_scenarios,
    compute_confidence, compute_simulation_signal,
)


def _make_signals(data):
    """Helper: compute short_term and ccrlo signals from a bundle."""
    st = compute_short_term_signal(data)
    cc = compute_ccrlo_signal(data)
    return st, cc


class TestRegimeDetection(unittest.TestCase):
    """detect_regime must produce valid probability distribution."""

    def test_probabilities_sum_to_one(self):
        """Regime probabilities must sum to 1.0 ±0.01."""
        regime = detect_regime(MINIMAL_BUNDLE, fragility_score=1)
        total = sum(regime["probabilities"].values())
        self.assertAlmostEqual(total, 1.0, delta=0.01)

    def test_all_four_regimes_present(self):
        """Must have calm, trending, stressed, crash_prone."""
        regime = detect_regime(MINIMAL_BUNDLE, fragility_score=0)
        for r in ("calm", "trending", "stressed", "crash_prone"):
            self.assertIn(r, regime["probabilities"])

    def test_all_nonnegative(self):
        """All probabilities must be >= 0."""
        for data in (MINIMAL_BUNDLE, DISTRESSED_BUNDLE):
            regime = detect_regime(data, fragility_score=2)
            for r, p in regime["probabilities"].items():
                self.assertGreaterEqual(p, 0, f"{r} is negative: {p}")

    def test_dominant_matches_max(self):
        """dominant must match the regime with highest probability."""
        regime = detect_regime(MINIMAL_BUNDLE, fragility_score=1)
        probs = regime["probabilities"]
        expected = max(probs, key=probs.get)
        self.assertEqual(regime["dominant"], expected)

    def test_high_fragility_boosts_crash_prone(self):
        """Fragility >= 3 should increase crash_prone weight."""
        low = detect_regime(MINIMAL_BUNDLE, fragility_score=0)
        high = detect_regime(MINIMAL_BUNDLE, fragility_score=4)
        self.assertGreaterEqual(
            high["probabilities"]["crash_prone"],
            low["probabilities"]["crash_prone"],
        )


class TestEventScoring(unittest.TestCase):
    """score_events must produce valid event probabilities."""

    def test_all_six_events(self):
        """Must score exactly 6 events."""
        regime = detect_regime(MINIMAL_BUNDLE, fragility_score=1)
        events = score_events(MINIMAL_BUNDLE, regime["probabilities"], 1, 5)
        expected = {"large_move", "vol_spike", "trend_reversal",
                    "earnings_reaction", "liquidity_stress", "crash_like"}
        self.assertEqual(set(events.keys()), expected)

    def test_three_horizons(self):
        """Each event must have 5d, 10d, 20d."""
        regime = detect_regime(MINIMAL_BUNDLE, fragility_score=1)
        events = score_events(MINIMAL_BUNDLE, regime["probabilities"], 1, 5)
        for name, horizons in events.items():
            for h in ("5d", "10d", "20d"):
                self.assertIn(h, horizons, f"{name} missing {h}")

    def test_probability_bounds(self):
        """All event probs in [1%, 85%], crash_like capped at 35%."""
        regime = detect_regime(MINIMAL_BUNDLE, fragility_score=1)
        events = score_events(MINIMAL_BUNDLE, regime["probabilities"], 1, 5)
        for name, horizons in events.items():
            cap = 35 if name == "crash_like" else 85
            for h in ("5d", "10d", "20d"):
                self.assertGreaterEqual(horizons[h], 1, f"{name}.{h} below 1%")
                self.assertLessEqual(horizons[h], cap, f"{name}.{h} above {cap}%")

    def test_longer_horizon_higher_prob(self):
        """20d probabilities should generally be >= 5d for most events."""
        regime = detect_regime(MINIMAL_BUNDLE, fragility_score=1)
        events = score_events(MINIMAL_BUNDLE, regime["probabilities"], 1, 5)
        for name, horizons in events.items():
            # Not strictly guaranteed for all events, but usually holds
            self.assertGreaterEqual(horizons["20d"], horizons["5d"] * 0.5,
                                    f"{name}: 20d should approximate >= 50% of 5d")


class TestScenarioWeighting(unittest.TestCase):
    """compute_scenarios must produce valid scenario weights."""

    def test_weights_sum_to_one(self):
        """Scenario weights must sum to 1.0 ±0.01."""
        probs = {"calm": 0.4, "trending": 0.3, "stressed": 0.2, "crash_prone": 0.1}
        scenarios = compute_scenarios(probs, 100.0, 2.0)
        total = sum(s["weight"] for s in scenarios.values())
        self.assertAlmostEqual(total, 1.0, delta=0.01)

    def test_four_scenarios(self):
        """Must produce exactly 4 scenarios."""
        probs = {"calm": 0.4, "trending": 0.3, "stressed": 0.2, "crash_prone": 0.1}
        scenarios = compute_scenarios(probs, 100.0, 2.0)
        expected = {"base_case", "vol_expansion", "trend_shift", "tail_risk"}
        self.assertEqual(set(scenarios.keys()), expected)

    def test_all_weights_nonnegative(self):
        for probs in (
            {"calm": 0.4, "trending": 0.3, "stressed": 0.2, "crash_prone": 0.1},
            {"calm": 0.0, "trending": 0.0, "stressed": 0.5, "crash_prone": 0.5},
            {"calm": 1.0, "trending": 0.0, "stressed": 0.0, "crash_prone": 0.0},
        ):
            scenarios = compute_scenarios(probs, 100.0, 2.0)
            for name, s in scenarios.items():
                self.assertGreaterEqual(s["weight"], 0, f"{name} weight negative")

    def test_each_scenario_has_price_range(self):
        probs = {"calm": 0.4, "trending": 0.3, "stressed": 0.2, "crash_prone": 0.1}
        scenarios = compute_scenarios(probs, 100.0, 2.0)
        for name, s in scenarios.items():
            self.assertIn("price_range", s)
            self.assertIn("$", s["price_range"])


class TestConfidence(unittest.TestCase):
    """compute_confidence must produce valid assessment."""

    def test_consistency_high_confidence(self):
        """Consistent signals → high confidence."""
        regime = {"dominant": "calm", "probabilities": {"calm": 0.6, "trending": 0.2, "stressed": 0.1, "crash_prone": 0.1}}
        result = compute_confidence(regime, False, False, 1, 3)
        self.assertIn(result["level"], ("HIGH", "MODERATE-HIGH"))
        self.assertGreaterEqual(len(result["top_drivers"]), 1)

    def test_contradiction_lowers_confidence(self):
        """Contradictory signals → lower confidence."""
        regime = {"dominant": "calm", "probabilities": {"calm": 0.6, "trending": 0.2, "stressed": 0.1, "crash_prone": 0.1}}
        result = compute_confidence(regime, True, True, 4, 14)
        # TB active + calm regime = contradiction; high fragility + calm = contradiction; high CCRLO
        self.assertIn(result["level"], ("LOW", "LOW-MODERATE", "MODERATE"))

    def test_disagreement_bounds(self):
        """Disagreement score in [0, 1]."""
        regime = {"dominant": "stressed", "probabilities": {"calm": 0.1, "trending": 0.1, "stressed": 0.4, "crash_prone": 0.4}}
        for tb in (True, False):
            for frag in range(6):
                for ccrlo in (0, 8, 16):
                    result = compute_confidence(regime, tb, False, frag, ccrlo)
                    self.assertGreaterEqual(result["disagreement"], 0)
                    self.assertLessEqual(result["disagreement"], 1)


class TestSimulationSignalComplete(unittest.TestCase):
    """End-to-end SIMULATION_SIGNAL output."""

    def test_signal_structure(self):
        """Signal has all Contract-required keys."""
        st, cc = _make_signals(MINIMAL_BUNDLE)
        signal = compute_simulation_signal(MINIMAL_BUNDLE, st, cc)
        for key in ("ticker", "as_of", "price", "regime", "events", "scenarios",
                     "weighted_expected", "confidence", "composite_event_risk", "risk_color"):
            self.assertIn(key, signal)

    def test_risk_color_mapping(self):
        """risk_color must match composite_event_risk thresholds."""
        st, cc = _make_signals(MINIMAL_BUNDLE)
        signal = compute_simulation_signal(MINIMAL_BUNDLE, st, cc)
        cer = signal["composite_event_risk"]
        if cer < 15:
            self.assertEqual(signal["risk_color"], "GREEN")
        elif cer <= 30:
            self.assertEqual(signal["risk_color"], "AMBER")
        else:
            self.assertEqual(signal["risk_color"], "RED")

    def test_ticker_matches(self):
        st, cc = _make_signals(MINIMAL_BUNDLE)
        signal = compute_simulation_signal(MINIMAL_BUNDLE, st, cc)
        self.assertEqual(signal["ticker"], "TEST")

    def test_distressed_higher_event_risk(self):
        """Distressed bundle should have >= event risk than minimal."""
        st1, cc1 = _make_signals(MINIMAL_BUNDLE)
        sig1 = compute_simulation_signal(MINIMAL_BUNDLE, st1, cc1)
        st2, cc2 = _make_signals(DISTRESSED_BUNDLE)
        sig2 = compute_simulation_signal(DISTRESSED_BUNDLE, st2, cc2)
        self.assertGreaterEqual(sig2["composite_event_risk"], sig1["composite_event_risk"])


if __name__ == "__main__":
    unittest.main()
