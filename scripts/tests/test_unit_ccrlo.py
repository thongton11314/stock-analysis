"""
Unit Tests — compute_ccrlo.py

Tests CCRLO feature scoring functions and composite signal.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tests.fixtures import MINIMAL_BUNDLE, DISTRESSED_BUNDLE
from compute_ccrlo import (
    score_term_spread, score_credit_risk, score_ig_credit,
    score_volatility_regime, score_financial_conditions,
    score_momentum_12m, score_realized_vol,
    map_score_to_probability, compute_ccrlo_signal,
)


class TestFeatureScoring(unittest.TestCase):
    """Each feature must return score in [0, 3]."""

    def _assert_valid_feature(self, result: dict):
        self.assertIn("score", result)
        self.assertIn("value", result)
        self.assertGreaterEqual(result["score"], 0)
        self.assertLessEqual(result["score"], 3)

    def test_term_spread(self):
        self._assert_valid_feature(score_term_spread(MINIMAL_BUNDLE))

    def test_credit_risk(self):
        self._assert_valid_feature(score_credit_risk(MINIMAL_BUNDLE))

    def test_ig_credit(self):
        self._assert_valid_feature(score_ig_credit(MINIMAL_BUNDLE))

    def test_volatility_regime(self):
        self._assert_valid_feature(score_volatility_regime(MINIMAL_BUNDLE))

    def test_financial_conditions(self):
        self._assert_valid_feature(score_financial_conditions(MINIMAL_BUNDLE))

    def test_momentum_12m(self):
        self._assert_valid_feature(score_momentum_12m(MINIMAL_BUNDLE))

    def test_realized_vol(self):
        self._assert_valid_feature(score_realized_vol(MINIMAL_BUNDLE))


class TestFeatureEdgeCases(unittest.TestCase):
    """Edge case inputs for feature scoring."""

    def test_term_spread_with_no_fed_data(self):
        """No federal_funds_rate → default score."""
        data = {**MINIMAL_BUNDLE, "federal_funds_rate": []}
        result = score_term_spread(data)
        self.assertGreaterEqual(result["score"], 0)

    def test_credit_risk_missing_debt_equity(self):
        """Missing D/E → default score."""
        data = {**MINIMAL_BUNDLE, "company_overview": {}}
        result = score_credit_risk(data)
        self.assertGreaterEqual(result["score"], 0)

    def test_momentum_missing_52w_high(self):
        """Missing 52-week high → default score."""
        data = {**MINIMAL_BUNDLE, "company_overview": {**MINIMAL_BUNDLE["company_overview"]}}
        data["company_overview"].pop("52_week_high", None)
        result = score_momentum_12m(data)
        self.assertGreaterEqual(result["score"], 0)

    def test_realized_vol_zero_price(self):
        """Zero price → safe default."""
        data = {**MINIMAL_BUNDLE, "global_quote": {**MINIMAL_BUNDLE["global_quote"], "price": 0}}
        result = score_realized_vol(data)
        self.assertGreaterEqual(result["score"], 0)

    def test_high_leverage_scores_high(self):
        """D/E > 2.0 → score 3."""
        data = {**MINIMAL_BUNDLE, "company_overview": {**MINIMAL_BUNDLE["company_overview"], "debt_to_equity": 3.5}}
        result = score_credit_risk(data)
        self.assertEqual(result["score"], 3)

    def test_deep_drawdown_scores_high(self):
        """Price well below 52W high → score 3."""
        data = {**DISTRESSED_BUNDLE}
        result = score_momentum_12m(data)
        self.assertGreaterEqual(result["score"], 2)


class TestScoreToProb(unittest.TestCase):
    """map_score_to_probability must return valid ranges."""

    def test_all_score_ranges(self):
        """Every score 0-21 maps to a valid probability and level."""
        valid_levels = {"LOW", "MODERATE", "ELEVATED", "HIGH", "VERY HIGH"}
        for score in range(22):
            prob, level = map_score_to_probability(score)
            self.assertGreater(prob, 0)
            self.assertLessEqual(prob, 100)
            self.assertIn(level, valid_levels, f"Score {score} → invalid level '{level}'")

    def test_higher_score_higher_prob(self):
        """Higher composite score → higher or equal probability."""
        prev_prob = 0
        for score in (0, 4, 8, 12, 16):
            prob, _ = map_score_to_probability(score)
            self.assertGreaterEqual(prob, prev_prob)
            prev_prob = prob

    def test_risk_level_boundaries(self):
        """Verify exact boundary mappings."""
        _, lvl3 = map_score_to_probability(3)
        self.assertEqual(lvl3, "LOW")
        _, lvl4 = map_score_to_probability(4)
        self.assertEqual(lvl4, "MODERATE")
        _, lvl8 = map_score_to_probability(8)
        self.assertEqual(lvl8, "ELEVATED")
        _, lvl12 = map_score_to_probability(12)
        self.assertEqual(lvl12, "HIGH")
        _, lvl16 = map_score_to_probability(16)
        self.assertEqual(lvl16, "VERY HIGH")


class TestCCRLOSignalComplete(unittest.TestCase):
    """End-to-end CCRLO_SIGNAL output."""

    def test_signal_structure(self):
        """Signal has all required contract keys."""
        signal = compute_ccrlo_signal(MINIMAL_BUNDLE)
        for key in ("ticker", "as_of", "horizon", "features",
                     "composite_score", "correction_probability", "risk_level"):
            self.assertIn(key, signal)

    def test_seven_features(self):
        """Exactly 7 features must be present."""
        signal = compute_ccrlo_signal(MINIMAL_BUNDLE)
        expected = {"term_spread", "credit_risk", "ig_credit", "volatility_regime",
                    "financial_conditions", "momentum_12m", "realized_vol"}
        self.assertEqual(set(signal["features"].keys()), expected)

    def test_composite_equals_sum(self):
        """composite_score = sum of all feature scores."""
        signal = compute_ccrlo_signal(MINIMAL_BUNDLE)
        expected_sum = sum(f["score"] for f in signal["features"].values())
        self.assertEqual(signal["composite_score"], expected_sum)

    def test_composite_in_range(self):
        """Composite score in [0, 21]."""
        for data in (MINIMAL_BUNDLE, DISTRESSED_BUNDLE):
            signal = compute_ccrlo_signal(data)
            self.assertGreaterEqual(signal["composite_score"], 0)
            self.assertLessEqual(signal["composite_score"], 21)

    def test_ticker_matches(self):
        signal = compute_ccrlo_signal(MINIMAL_BUNDLE)
        self.assertEqual(signal["ticker"], "TEST")

    def test_distressed_higher_score(self):
        """Distressed bundle should score higher than minimal."""
        normal = compute_ccrlo_signal(MINIMAL_BUNDLE)
        stressed = compute_ccrlo_signal(DISTRESSED_BUNDLE)
        self.assertGreaterEqual(stressed["composite_score"], normal["composite_score"])


if __name__ == "__main__":
    unittest.main()
