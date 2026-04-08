"""
Unit Tests — compute_short_term.py

Tests individual functions: compute_tb, compute_vs, compute_vf,
compute_fragility, compute_correction_probabilities, and the
top-level compute_short_term_signal.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tests.fixtures import MINIMAL_BUNDLE, DISTRESSED_BUNDLE
from compute_short_term import (
    compute_tb, compute_vs, compute_vf,
    compute_fragility, compute_correction_probabilities,
    compute_short_term_signal,
)


class TestComputeTB(unittest.TestCase):
    """Gate 1: Trend Break — price below declining 200-MA."""

    def test_tb_false_when_price_above_sma(self):
        """Price above SMA200 → TB=False."""
        result = compute_tb(110.0, MINIMAL_BUNDLE["sma_200"])
        self.assertFalse(result["tb"])

    def test_tb_true_when_below_declining_sma(self):
        """Price well below a declining SMA200 → TB=True."""
        # SMA200 entries decline from 110 → lower, price at 75
        declining_sma = [{"date": f"2026-03-{25-i:02d}", "value": str(110 + i * 0.2)}
                         for i in range(25)]
        result = compute_tb(75.0, declining_sma)
        self.assertTrue(result["tb"])

    def test_tb_false_with_insufficient_data(self):
        """Less than 21 SMA200 data points → TB=False (insufficient data)."""
        result = compute_tb(100.0, MINIMAL_BUNDLE["sma_200"][:5])
        self.assertFalse(result["tb"])
        self.assertEqual(result["sma_200_slope"], "INSUFFICIENT_DATA")

    def test_tb_false_when_sma_rising(self):
        """Price below SMA200 but SMA is rising → TB=False (slope not negative)."""
        rising_sma = [{"date": f"2026-03-{25-i:02d}", "value": str(105 + i * 0.3)}
                      for i in range(25)]
        # SMA goes 108.2 at [20] → 105 at [0], which is declining, not rising
        # Let's make it actually rise
        rising_sma = [{"date": f"2026-03-{25-i:02d}", "value": str(100 + i * 0.3)}
                      for i in range(25)]
        # sma[0]=100, sma[20]=106 → slope = 100-106 = -6 → still declining
        # Need sma[0] > sma[20]
        rising_sma = [{"date": f"2026-03-{25-i:02d}", "value": str(110 - i * 0.3)}
                      for i in range(25)]
        # sma[0]=110, sma[20]=104 → slope = 110-104 = +6 → POSITIVE
        result = compute_tb(105.0, rising_sma)
        # Price is below buffered SMA (105 < 0.995*110=109.45) but slope is POSITIVE
        self.assertFalse(result["tb"])
        self.assertEqual(result["sma_200_slope"], "POSITIVE")

    def test_tb_returns_sma_value(self):
        """Result includes the actual SMA200 value."""
        result = compute_tb(100.0, MINIMAL_BUNDLE["sma_200"])
        self.assertIsNotNone(result["sma_200"])
        self.assertIsInstance(result["sma_200"], float)


class TestComputeVS(unittest.TestCase):
    """Gate 2: Volatility Shift — ATR above 80th percentile."""

    def test_vs_false_for_normal_vol(self):
        """Normal ATR values → VS=False."""
        result = compute_vs(MINIMAL_BUNDLE["atr_14"])
        self.assertFalse(result["vs"])
        self.assertIsNotNone(result["atr_percentile"])

    def test_vs_true_for_extreme_atr(self):
        """ATR[0] above all historical values → VS=True."""
        extreme_atr = [{"date": "2026-03-25", "value": "99.0"}] + \
                      [{"date": f"2026-03-{25-i:02d}", "value": str(2.0)} for i in range(1, 260)]
        result = compute_vs(extreme_atr)
        self.assertTrue(result["vs"])
        self.assertGreaterEqual(result["atr_percentile"], 80.0)

    def test_vs_false_with_too_few_points(self):
        """Fewer than 20 ATR values → VS=False."""
        result = compute_vs(MINIMAL_BUNDLE["atr_14"][:5])
        self.assertFalse(result["vs"])


class TestComputeVF(unittest.TestCase):
    """Gate 3: Volume Filter — volume >= 1x 20-day average."""

    def test_vf_true_when_above_average(self):
        """Volume above SMA → VF=True."""
        gq = {"volume_sma_20": 4000000}
        result = compute_vf(5000000, [], gq)
        self.assertTrue(result["vf"])
        self.assertGreaterEqual(result["volume_ratio"], 1.0)

    def test_vf_false_when_below_average(self):
        """Volume below SMA → VF=False."""
        gq = {"volume_sma_20": 6000000}
        result = compute_vf(3000000, [], gq)
        self.assertFalse(result["vf"])

    def test_vf_false_when_no_volume_data(self):
        """No volume → conservative False."""
        result = compute_vf(0, [], {})
        self.assertFalse(result["vf"])

    def test_vf_uses_volume_history_first(self):
        """volume_history (20 entries) takes priority over volume_sma_20."""
        gq = {
            "volume_history": [1000000] * 20,
            "volume_sma_20": 999999999,  # would give very low ratio if used
        }
        result = compute_vf(1500000, [], gq)
        self.assertTrue(result["vf"])
        self.assertEqual(result["volume_ratio"], 1.5)


class TestComputeFragility(unittest.TestCase):
    """Fragility Stack — 5 dimensions, each LOW or HIGH."""

    def test_minimal_bundle_low_fragility(self):
        """Healthy company → low fragility score."""
        result = compute_fragility(MINIMAL_BUNDLE)
        self.assertLessEqual(result["score"], 2)
        self.assertIn(result["level"], ("LOW", "MODERATE"))
        self.assertEqual(len(result["dimensions"]), 5)

    def test_distressed_bundle_high_fragility(self):
        """Distressed company → higher fragility score."""
        result = compute_fragility(DISTRESSED_BUNDLE)
        self.assertGreaterEqual(result["score"], 2)

    def test_fragility_score_equals_high_count(self):
        """Score must equal the count of HIGH dimensions."""
        result = compute_fragility(MINIMAL_BUNDLE)
        high_count = sum(1 for v in result["dimensions"].values() if v == "HIGH")
        self.assertEqual(result["score"], high_count)

    def test_fragility_level_mapping(self):
        """Level must correctly map from score."""
        for data in (MINIMAL_BUNDLE, DISTRESSED_BUNDLE):
            result = compute_fragility(data)
            score = result["score"]
            if score <= 1:
                self.assertEqual(result["level"], "LOW")
            elif score <= 3:
                self.assertEqual(result["level"], "MODERATE")
            else:
                self.assertEqual(result["level"], "HIGH")

    def test_all_dimensions_present(self):
        """All 5 dimensions must be present."""
        result = compute_fragility(MINIMAL_BUNDLE)
        for dim in ("leverage", "liquidity", "info_risk", "valuation", "momentum"):
            self.assertIn(dim, result["dimensions"])
            self.assertIn(result["dimensions"][dim], ("LOW", "HIGH"))


class TestCorrectionProbabilities(unittest.TestCase):
    """Correction probability calibration."""

    def test_monotonically_decreasing(self):
        """mild >= standard >= severe >= black_swan."""
        probs = compute_correction_probabilities(2, 1.0, 10.0)
        self.assertGreaterEqual(probs["mild"], probs["standard"])
        self.assertGreaterEqual(probs["standard"], probs["severe"])
        self.assertGreaterEqual(probs["severe"], probs["black_swan"])

    def test_all_in_bounds(self):
        """All probabilities in [1, 99]."""
        for frag in range(6):
            for beta in (0.5, 1.0, 1.5, 2.5):
                probs = compute_correction_probabilities(frag, beta, 10.0)
                for k, v in probs.items():
                    self.assertGreaterEqual(v, 1, f"frag={frag} beta={beta} {k}={v}")
                    self.assertLessEqual(v, 99, f"frag={frag} beta={beta} {k}={v}")

    def test_high_fragility_increases_severe(self):
        """Fragility 5 should produce higher correction probs than fragility 0."""
        low = compute_correction_probabilities(0, 1.0, 10.0)
        high = compute_correction_probabilities(5, 1.0, 10.0)
        self.assertGreater(high["severe"], low["severe"])

    def test_high_beta_increases_probs(self):
        """Beta > 1.5 adjustment."""
        normal = compute_correction_probabilities(2, 1.0, 10.0)
        high_beta = compute_correction_probabilities(2, 2.0, 10.0)
        self.assertGreater(high_beta["mild"], normal["mild"])

    def test_recent_ipo_increases_tail_risk(self):
        """IPO < 2 years → +10% to severe and black_swan."""
        old = compute_correction_probabilities(2, 1.0, 20.0)
        new_ipo = compute_correction_probabilities(2, 1.0, 1.0)
        self.assertGreater(new_ipo["severe"], old["severe"])
        self.assertGreater(new_ipo["black_swan"], old["black_swan"])


class TestShortTermSignalComplete(unittest.TestCase):
    """End-to-end SHORT_TERM_SIGNAL output."""

    def test_signal_has_all_keys(self):
        """Signal must contain all contract-required keys."""
        signal = compute_short_term_signal(MINIMAL_BUNDLE)
        required = ["ticker", "as_of", "price", "trend_break", "indicators",
                     "fragility", "correction_probabilities"]
        for key in required:
            self.assertIn(key, signal, f"Missing key: {key}")

    def test_entry_active_logic(self):
        """entry_active = tb AND vs AND vf."""
        signal = compute_short_term_signal(MINIMAL_BUNDLE)
        tb = signal["trend_break"]
        expected = tb["tb"] and tb["vs"] and tb["vf"]
        self.assertEqual(tb["entry_active"], expected)

    def test_uses_bundle_ticker(self):
        """Signal ticker matches bundle ticker."""
        signal = compute_short_term_signal(MINIMAL_BUNDLE)
        self.assertEqual(signal["ticker"], "TEST")

    def test_price_matches_bundle(self):
        """Signal price matches bundle global_quote.price."""
        signal = compute_short_term_signal(MINIMAL_BUNDLE)
        self.assertEqual(signal["price"], MINIMAL_BUNDLE["global_quote"]["price"])


if __name__ == "__main__":
    unittest.main()
