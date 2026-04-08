"""
Unit Tests — Tag Classification (compute_tags.py)

Tests all 5 tag dimensions + validation + index operations.
"""

import unittest
import os
import sys
import json
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tests.fixtures import MINIMAL_BUNDLE, DISTRESSED_BUNDLE
from compute_short_term import compute_short_term_signal
from compute_ccrlo import compute_ccrlo_signal
from compute_simulation import compute_simulation_signal
from compute_tags import (
    compute_tags, validate_tags, classify_profile, classify_sector,
    classify_risk, classify_momentum, classify_valuation,
    VALID_TAGS, update_index, query_index, INDEX_PATH,
)


class TestClassifyProfile(unittest.TestCase):
    """Profile dimension: market cap + lifecycle stage."""

    def test_mega_cap(self):
        bundle = {**MINIMAL_BUNDLE, "company_overview": {**MINIMAL_BUNDLE["company_overview"], "market_cap": 500_000_000_000}}
        tags = classify_profile(bundle)
        self.assertIn("mega-cap", tags)

    def test_large_cap(self):
        bundle = {**MINIMAL_BUNDLE, "company_overview": {**MINIMAL_BUNDLE["company_overview"], "market_cap": 50_000_000_000}}
        tags = classify_profile(bundle)
        self.assertIn("large-cap", tags)

    def test_mid_cap(self):
        bundle = {**MINIMAL_BUNDLE, "company_overview": {**MINIMAL_BUNDLE["company_overview"], "market_cap": 5_000_000_000}}
        tags = classify_profile(bundle)
        self.assertIn("mid-cap", tags)

    def test_small_cap(self):
        bundle = {**MINIMAL_BUNDLE, "company_overview": {**MINIMAL_BUNDLE["company_overview"], "market_cap": 500_000_000}}
        tags = classify_profile(bundle)
        self.assertIn("small-cap", tags)

    def test_micro_cap(self):
        bundle = {**MINIMAL_BUNDLE, "company_overview": {**MINIMAL_BUNDLE["company_overview"], "market_cap": 100_000_000}}
        tags = classify_profile(bundle)
        self.assertIn("micro-cap", tags)

    def test_mature_from_ipo_date(self):
        bundle = {**MINIMAL_BUNDLE, "company_overview": {**MINIMAL_BUNDLE["company_overview"], "ipo_date": "2000-01-01"}}
        tags = classify_profile(bundle)
        self.assertIn("mature", tags)

    def test_post_ipo(self):
        bundle = {**MINIMAL_BUNDLE, "company_overview": {**MINIMAL_BUNDLE["company_overview"], "ipo_date": "2025-06-01"}}
        tags = classify_profile(bundle)
        self.assertIn("post-ipo", tags)

    def test_growth_stage(self):
        bundle = {**MINIMAL_BUNDLE, "company_overview": {**MINIMAL_BUNDLE["company_overview"], "ipo_date": "2020-01-01"}}
        tags = classify_profile(bundle)
        self.assertIn("growth-stage", tags)

    def test_pre_profit(self):
        bundle = {
            **MINIMAL_BUNDLE,
            "income_statement": {"annual": [{"netIncome": "-500000000"}]},
        }
        tags = classify_profile(bundle)
        self.assertIn("pre-profit", tags)

    def test_string_market_cap(self):
        """Market cap as string should still work."""
        bundle = {**MINIMAL_BUNDLE, "company_overview": {**MINIMAL_BUNDLE["company_overview"], "market_cap": "250000000000"}}
        tags = classify_profile(bundle)
        self.assertIn("mega-cap", tags)


class TestClassifySector(unittest.TestCase):
    """Sector dimension: primary sector + thematic overlays."""

    def test_technology_sector(self):
        bundle = {**MINIMAL_BUNDLE, "company_overview": {**MINIMAL_BUNDLE["company_overview"], "sector": "TECHNOLOGY"}}
        tags = classify_sector(bundle)
        self.assertIn("technology", tags)

    def test_consumer_cyclical(self):
        bundle = {**MINIMAL_BUNDLE, "company_overview": {**MINIMAL_BUNDLE["company_overview"], "sector": "Consumer Cyclical"}}
        tags = classify_sector(bundle)
        self.assertIn("consumer-cyclical", tags)

    def test_thematic_ai_overlay(self):
        bundle = {**MINIMAL_BUNDLE, "company_overview": {
            **MINIMAL_BUNDLE["company_overview"],
            "sector": "TECHNOLOGY",
            "description": "A leading artificial intelligence platform company.",
        }}
        tags = classify_sector(bundle)
        self.assertIn("ai", tags)

    def test_thematic_fintech_overlay(self):
        bundle = {**MINIMAL_BUNDLE, "company_overview": {
            **MINIMAL_BUNDLE["company_overview"],
            "sector": "FINANCIALS",
            "industry": "Digital brokerage and fintech services",
        }}
        tags = classify_sector(bundle)
        self.assertIn("fintech", tags)

    def test_unknown_sector_passes(self):
        bundle = {**MINIMAL_BUNDLE, "company_overview": {**MINIMAL_BUNDLE["company_overview"], "sector": "Space Mining"}}
        tags = classify_sector(bundle)
        self.assertTrue(len(tags) >= 1)

    def test_multiple_themes_detected(self):
        bundle = {**MINIMAL_BUNDLE, "company_overview": {
            **MINIMAL_BUNDLE["company_overview"],
            "sector": "TECHNOLOGY",
            "description": "Cloud computing and artificial intelligence SaaS platform.",
        }}
        tags = classify_sector(bundle)
        self.assertIn("technology", tags)
        self.assertIn("cloud", tags)
        self.assertIn("ai", tags)
        self.assertIn("saas", tags)


class TestClassifyRisk(unittest.TestCase):
    """Risk dimension: composite of signal risk levels."""

    def test_low_risk(self):
        ccrlo = {"risk_level": "LOW"}
        st = {"trend_break": {"entry_active": False}}
        sim = {"regime": {"probabilities": {"crash_prone": 0.05}}}
        tags = classify_risk(st, ccrlo, sim)
        self.assertIn("low-risk", tags)
        self.assertNotIn("crash-prone", tags)

    def test_high_risk(self):
        ccrlo = {"risk_level": "HIGH"}
        st = {"trend_break": {"entry_active": False}}
        sim = {"regime": {"probabilities": {"crash_prone": 0.10}}}
        tags = classify_risk(st, ccrlo, sim)
        self.assertIn("high-risk", tags)

    def test_trend_break_active_tag(self):
        ccrlo = {"risk_level": "MODERATE"}
        st = {"trend_break": {"entry_active": True}}
        sim = {"regime": {"probabilities": {"crash_prone": 0.05}}}
        tags = classify_risk(st, ccrlo, sim)
        self.assertIn("trend-break-active", tags)

    def test_crash_prone_tag(self):
        ccrlo = {"risk_level": "ELEVATED"}
        st = {"trend_break": {"entry_active": False}}
        sim = {"regime": {"probabilities": {"crash_prone": 0.25}}}
        tags = classify_risk(st, ccrlo, sim)
        self.assertIn("crash-prone", tags)

    def test_very_high_maps_to_high(self):
        ccrlo = {"risk_level": "VERY HIGH"}
        st = {"trend_break": {"entry_active": False}}
        sim = {"regime": {"probabilities": {"crash_prone": 0.05}}}
        tags = classify_risk(st, ccrlo, sim)
        self.assertIn("high-risk", tags)


class TestClassifyMomentum(unittest.TestCase):
    """Momentum dimension: trend direction from technical indicators."""

    def test_bullish_above_sma(self):
        bundle = {**MINIMAL_BUNDLE, "rsi": [{"date": "2026-03-25", "value": "55.0"}]}
        st = {"indicators": {"sma_200": 95.0, "sma_200_slope": "POSITIVE"}}
        tags = classify_momentum(bundle, st)
        self.assertIn("bullish", tags)
        self.assertIn("above-200sma", tags)

    def test_bearish_below_sma(self):
        bundle = {**MINIMAL_BUNDLE, "rsi": [{"date": "2026-03-25", "value": "45.0"}]}
        st = {"indicators": {"sma_200": 110.0, "sma_200_slope": "NEGATIVE"}}
        tags = classify_momentum(bundle, st)
        self.assertIn("bearish", tags)
        self.assertIn("below-200sma", tags)

    def test_oversold_tag(self):
        bundle = {**MINIMAL_BUNDLE, "rsi": [{"date": "2026-03-25", "value": "22.0"}]}
        st = {"indicators": {"sma_200": 110.0, "sma_200_slope": "NEGATIVE"}}
        tags = classify_momentum(bundle, st)
        self.assertIn("oversold", tags)

    def test_overbought_tag(self):
        bundle = {**MINIMAL_BUNDLE, "rsi": [{"date": "2026-03-25", "value": "78.0"}]}
        st = {"indicators": {"sma_200": 95.0, "sma_200_slope": "POSITIVE"}}
        tags = classify_momentum(bundle, st)
        self.assertIn("overbought", tags)

    def test_mean_reverting(self):
        bundle = {**MINIMAL_BUNDLE, "rsi": [{"date": "2026-03-25", "value": "28.0"}]}
        st = {"indicators": {"sma_200": 110.0, "sma_200_slope": "NEGATIVE"}}
        tags = classify_momentum(bundle, st)
        self.assertIn("mean-reverting", tags)

    def test_neutral_mixed_signals(self):
        bundle = {**MINIMAL_BUNDLE, "rsi": [{"date": "2026-03-25", "value": "50.0"}]}
        st = {"indicators": {"sma_200": 110.0, "sma_200_slope": "POSITIVE"}}
        tags = classify_momentum(bundle, st)
        self.assertIn("neutral", tags)


class TestClassifyValuation(unittest.TestCase):
    """Valuation dimension: P/E vs sector norms."""

    def test_fair_value(self):
        bundle = {**MINIMAL_BUNDLE, "company_overview": {
            **MINIMAL_BUNDLE["company_overview"],
            "pe_ratio": 25.0, "sector_pe_90th_percentile": 45.0,
        }}
        tags = classify_valuation(bundle)
        self.assertIn("fair-value", tags)

    def test_deep_value(self):
        bundle = {**MINIMAL_BUNDLE, "company_overview": {
            **MINIMAL_BUNDLE["company_overview"],
            "pe_ratio": 8.0, "sector_pe_90th_percentile": 45.0,
        }}
        tags = classify_valuation(bundle)
        self.assertIn("deep-value", tags)

    def test_overvalued(self):
        bundle = {**MINIMAL_BUNDLE, "company_overview": {
            **MINIMAL_BUNDLE["company_overview"],
            "pe_ratio": 42.0, "sector_pe_90th_percentile": 45.0,
        }}
        tags = classify_valuation(bundle)
        self.assertIn("overvalued", tags)

    def test_speculative_premium(self):
        bundle = {**MINIMAL_BUNDLE, "company_overview": {
            **MINIMAL_BUNDLE["company_overview"],
            "pe_ratio": 80.0, "sector_pe_90th_percentile": 45.0,
        }}
        tags = classify_valuation(bundle)
        self.assertIn("speculative-premium", tags)

    def test_negative_pe_with_high_forward(self):
        bundle = {**MINIMAL_BUNDLE, "company_overview": {
            **MINIMAL_BUNDLE["company_overview"],
            "pe_ratio": -5.0, "forward_pe": 75.0,
        }}
        tags = classify_valuation(bundle)
        self.assertIn("speculative-premium", tags)

    def test_absolute_fallback(self):
        bundle = {**MINIMAL_BUNDLE, "company_overview": {
            **MINIMAL_BUNDLE["company_overview"],
            "pe_ratio": 12.0, "sector_pe_90th_percentile": 0,
        }}
        tags = classify_valuation(bundle)
        self.assertIn("undervalued", tags)


class TestComputeTagsIntegration(unittest.TestCase):
    """Full compute_tags with real signal pipeline."""

    @classmethod
    def setUpClass(cls):
        cls.st = compute_short_term_signal(MINIMAL_BUNDLE)
        cls.cc = compute_ccrlo_signal(MINIMAL_BUNDLE)
        cls.sim = compute_simulation_signal(MINIMAL_BUNDLE, cls.st, cls.cc)
        cls.tags = compute_tags(MINIMAL_BUNDLE, cls.st, cls.cc, cls.sim)

    def test_has_all_dimensions(self):
        for dim in ("profile", "sector", "risk", "momentum", "valuation"):
            self.assertIn(dim, self.tags["tags"])
            self.assertTrue(len(self.tags["tags"][dim]) >= 1, f"{dim} must have >= 1 tag")

    def test_has_primary_tag(self):
        self.assertIn("primary_tag", self.tags)
        self.assertIsInstance(self.tags["primary_tag"], str)
        self.assertNotEqual(self.tags["primary_tag"], "")

    def test_has_ticker(self):
        self.assertEqual(self.tags["ticker"], "TEST")

    def test_has_tag_version(self):
        self.assertEqual(self.tags["tag_version"], "1.0")

    def test_validation_passes(self):
        checks = validate_tags(self.tags)
        fails = [c for c in checks if c["status"] == "FAIL"]
        self.assertEqual(fails, [], f"Tag validation failures: {fails}")


class TestComputeTagsDistressed(unittest.TestCase):
    """Tags for distressed/edge-case bundle."""

    @classmethod
    def setUpClass(cls):
        cls.st = compute_short_term_signal(DISTRESSED_BUNDLE)
        cls.cc = compute_ccrlo_signal(DISTRESSED_BUNDLE)
        cls.sim = compute_simulation_signal(DISTRESSED_BUNDLE, cls.st, cls.cc)
        cls.tags = compute_tags(DISTRESSED_BUNDLE, cls.st, cls.cc, cls.sim)

    def test_post_ipo_detected(self):
        self.assertIn("post-ipo", self.tags["tags"]["profile"])

    def test_high_pe_detected(self):
        """Distressed bundle has P/E=85 vs sector 90th=45 → speculative-premium."""
        self.assertIn("speculative-premium", self.tags["tags"]["valuation"])

    def test_validation_passes(self):
        checks = validate_tags(self.tags)
        fails = [c for c in checks if c["status"] == "FAIL"]
        self.assertEqual(fails, [], f"Tag validation failures: {fails}")


class TestValidateTags(unittest.TestCase):
    """Tag validation contract checks."""

    def test_valid_tag_signal_passes(self):
        tag_signal = {
            "ticker": "TEST",
            "as_of": "2026-03-25",
            "tags": {
                "profile": ["large-cap", "mature"],
                "sector": ["technology"],
                "risk": ["low-risk"],
                "momentum": ["bullish", "above-200sma"],
                "valuation": ["fair-value"],
            },
            "primary_tag": "large-cap-bullish-low-risk",
            "tag_version": "1.0",
        }
        checks = validate_tags(tag_signal)
        fails = [c for c in checks if c["status"] == "FAIL"]
        self.assertEqual(fails, [])

    def test_missing_dimension_fails(self):
        tag_signal = {
            "ticker": "TEST", "as_of": "2026-03-25",
            "tags": {
                "profile": ["large-cap"],
                "sector": ["technology"],
                "risk": ["low-risk"],
                "momentum": ["bullish"],
                # valuation missing
            },
            "primary_tag": "test", "tag_version": "1.0",
        }
        checks = validate_tags(tag_signal)
        fails = [c for c in checks if c["status"] == "FAIL"]
        fail_fields = [c["field"] for c in fails]
        self.assertIn("tag.valuation", fail_fields)

    def test_empty_dimension_fails(self):
        tag_signal = {
            "ticker": "TEST", "as_of": "2026-03-25",
            "tags": {
                "profile": [],
                "sector": ["technology"],
                "risk": ["low-risk"],
                "momentum": ["bullish"],
                "valuation": ["fair-value"],
            },
            "primary_tag": "test", "tag_version": "1.0",
        }
        checks = validate_tags(tag_signal)
        fails = [c for c in checks if c["status"] == "FAIL"]
        self.assertTrue(any("profile" in c["field"] for c in fails))

    def test_invalid_tag_fails(self):
        tag_signal = {
            "ticker": "TEST", "as_of": "2026-03-25",
            "tags": {
                "profile": ["large-cap"],
                "sector": ["technology"],
                "risk": ["not-a-real-risk"],
                "momentum": ["bullish"],
                "valuation": ["fair-value"],
            },
            "primary_tag": "test", "tag_version": "1.0",
        }
        checks = validate_tags(tag_signal)
        fails = [c for c in checks if c["status"] == "FAIL"]
        self.assertTrue(any("not-a-real-risk" in c.get("reason", "") for c in fails))


if __name__ == "__main__":
    unittest.main()
