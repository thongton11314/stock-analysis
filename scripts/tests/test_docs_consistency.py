"""
Documentation Consistency Tests — Architecture & System Integrity

Verifies that documentation, instructions, agent definitions, skill files,
and signal contracts stay in sync with the actual codebase. Catches:
  - File paths in docs that don't exist on disk
  - Test counts in docs that don't match actual counts
  - Signal field names in contracts that don't match compute script outputs
  - Folder structure trees that are outdated
  - Agent gate checklists referencing non-existent scripts
  - Skill directories missing SKILL.md

These tests run without any network access or data bundles.
"""

import unittest
import os
import re
import sys

_SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BASE_DIR = os.path.dirname(_SCRIPT_DIR)

if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)


class TestFilePathsExist(unittest.TestCase):
    """Every file/directory referenced in key docs must exist on disk."""

    # Paths that MUST exist (relative to project root)
    REQUIRED_PATHS = [
        # Agents
        ".github/agents/stock-analyst.agent.md",
        ".github/agents/test-engineer.agent.md",
        ".github/agents/portfolio-manager.agent.md",
        # Core instructions
        ".github/copilot-instructions.md",
        ".vscode/settings.json",
        # Templates & examples
        "templates/report-template.html",
        "templates/portfolio-template.html",
        "examples/HOOD-analysis.html",
        # Instructions
        ".instructions/data-collection.md",
        ".instructions/report-layout.md",
        ".instructions/styling.md",
        ".instructions/analysis-methodology.md",
        ".instructions/analysis-reference.md",
        ".instructions/signal-contracts.md",
        ".instructions/short-term-strategy.md",
        ".instructions/long-term-strategy.md",
        ".instructions/simulation-strategy.md",
        # Scripts
        "scripts/analyst_compute_engine.py",
        "scripts/compute_short_term.py",
        "scripts/compute_ccrlo.py",
        "scripts/compute_simulation.py",
        "scripts/validate_inputs.py",
        "scripts/validate_outputs.py",
        "scripts/validate_numbers.py",
        "scripts/compute_tags.py",
        "scripts/run_tests.py",
        "scripts/build_portfolio.py",
        "scripts/audit_portfolio.py",
        "scripts/portfolio_optimizer.py",
        # CI/CD
        ".github/workflows/system-guard.yml",
        # Test infrastructure
        "scripts/tests/__init__.py",
        "scripts/tests/fixtures.py",
        "scripts/tests/test_unit_short_term.py",
        "scripts/tests/test_unit_ccrlo.py",
        "scripts/tests/test_unit_simulation.py",
        "scripts/tests/test_unit_tags.py",
        "scripts/tests/test_contracts.py",
        "scripts/tests/test_integration.py",
    ]

    REQUIRED_DIRS = [
        ".github/agents",
        ".github/skills",
        ".github/workflows",
        ".instructions",
        "scripts",
        "scripts/tests",
        "scripts/tests/golden",
        "templates",
        "examples",
        "reports",
    ]

    def test_all_required_files_exist(self):
        """Every referenced file must exist on disk."""
        missing = []
        for rel_path in self.REQUIRED_PATHS:
            full_path = os.path.join(_BASE_DIR, rel_path)
            if not os.path.isfile(full_path):
                missing.append(rel_path)
        self.assertEqual(missing, [], f"Missing files: {missing}")

    def test_all_required_dirs_exist(self):
        """Every referenced directory must exist."""
        missing = []
        for rel_path in self.REQUIRED_DIRS:
            full_path = os.path.join(_BASE_DIR, rel_path)
            if not os.path.isdir(full_path):
                missing.append(rel_path)
        self.assertEqual(missing, [], f"Missing directories: {missing}")


class TestSkillDirectories(unittest.TestCase):
    """Every skill directory must contain a SKILL.md file."""

    EXPECTED_SKILLS = [
        "analyst-compute-engine",
        "data-collection",
        "long-term-prediction",
        "numerical-audit",
        "portfolio-audit",
        "portfolio-build",
        "report-audit",
        "report-fix",
        "report-generation",
        "short-term-analysis",
        "simulation",
        "stock-tagging",
        "system-test",
    ]

    def test_all_skill_dirs_exist(self):
        """Every expected skill directory must exist."""
        skills_dir = os.path.join(_BASE_DIR, ".github", "skills")
        for skill in self.EXPECTED_SKILLS:
            skill_dir = os.path.join(skills_dir, skill)
            self.assertTrue(os.path.isdir(skill_dir), f"Skill dir missing: {skill}/")

    def test_all_skill_dirs_have_skill_md(self):
        """Every skill directory must have a SKILL.md."""
        skills_dir = os.path.join(_BASE_DIR, ".github", "skills")
        missing = []
        for skill in self.EXPECTED_SKILLS:
            skill_file = os.path.join(skills_dir, skill, "SKILL.md")
            if not os.path.isfile(skill_file):
                missing.append(f"{skill}/SKILL.md")
        self.assertEqual(missing, [], f"Missing SKILL.md: {missing}")

    def test_no_unexpected_skill_dirs(self):
        """No orphan skill directories exist without being in the expected list."""
        skills_dir = os.path.join(_BASE_DIR, ".github", "skills")
        if not os.path.isdir(skills_dir):
            self.skipTest("Skills directory not found")
        actual = set(d for d in os.listdir(skills_dir)
                     if os.path.isdir(os.path.join(skills_dir, d)))
        expected = set(self.EXPECTED_SKILLS)
        unexpected = actual - expected
        self.assertEqual(unexpected, set(),
                         f"Unexpected skill dirs (add to EXPECTED_SKILLS or delete): {unexpected}")


class TestSignalContractConsistency(unittest.TestCase):
    """Signal field names in contracts must match what compute scripts produce."""

    def setUp(self):
        """Compute signals from MINIMAL_BUNDLE fixture to get actual output."""
        from tests.fixtures import MINIMAL_BUNDLE
        from compute_short_term import compute_short_term_signal
        from compute_ccrlo import compute_ccrlo_signal
        from compute_simulation import compute_simulation_signal

        self.st = compute_short_term_signal(MINIMAL_BUNDLE)
        self.cc = compute_ccrlo_signal(MINIMAL_BUNDLE)
        self.sim = compute_simulation_signal(MINIMAL_BUNDLE, self.st, self.cc)

    def test_short_term_top_level_keys(self):
        """SHORT_TERM_SIGNAL must have all contract-defined top-level keys."""
        contract_keys = ["ticker", "as_of", "price", "trend_break",
                         "indicators", "fragility", "correction_probabilities"]
        for key in contract_keys:
            self.assertIn(key, self.st, f"SHORT_TERM missing contract key: {key}")

    def test_short_term_trend_break_keys(self):
        tb = self.st["trend_break"]
        for key in ["tb", "vs", "vf", "entry_active"]:
            self.assertIn(key, tb, f"trend_break missing: {key}")

    def test_short_term_fragility_keys(self):
        frag = self.st["fragility"]
        for key in ["score", "level", "dimensions"]:
            self.assertIn(key, frag, f"fragility missing: {key}")
        dims = frag["dimensions"]
        for dim in ["leverage", "liquidity", "info_risk", "valuation", "momentum"]:
            self.assertIn(dim, dims, f"fragility.dimensions missing: {dim}")

    def test_short_term_correction_prob_keys(self):
        cp = self.st["correction_probabilities"]
        for key in ["mild", "standard", "severe", "black_swan"]:
            self.assertIn(key, cp, f"correction_probabilities missing: {key}")

    def test_short_term_indicators_keys(self):
        ind = self.st["indicators"]
        for key in ["sma_200", "sma_200_slope", "atr_14", "atr_percentile"]:
            self.assertIn(key, ind, f"indicators missing: {key}")

    def test_ccrlo_top_level_keys(self):
        """CCRLO_SIGNAL must have all contract-defined top-level keys."""
        contract_keys = ["ticker", "as_of", "horizon", "features",
                         "composite_score", "correction_probability", "risk_level"]
        for key in contract_keys:
            self.assertIn(key, self.cc, f"CCRLO missing contract key: {key}")

    def test_ccrlo_seven_features(self):
        features = self.cc["features"]
        expected = ["term_spread", "credit_risk", "ig_credit", "volatility_regime",
                    "financial_conditions", "momentum_12m", "realized_vol"]
        for feat in expected:
            self.assertIn(feat, features, f"CCRLO features missing: {feat}")
            self.assertIn("score", features[feat], f"Feature {feat} missing 'score'")
            self.assertIn("value", features[feat], f"Feature {feat} missing 'value'")

    def test_simulation_top_level_keys(self):
        """SIMULATION_SIGNAL must have all contract-defined top-level keys."""
        contract_keys = ["ticker", "as_of", "price", "regime", "events", "scenarios",
                         "weighted_expected", "confidence", "composite_event_risk", "risk_color"]
        for key in contract_keys:
            self.assertIn(key, self.sim, f"SIMULATION missing contract key: {key}")

    def test_simulation_regime_keys(self):
        regime = self.sim["regime"]
        self.assertIn("probabilities", regime)
        self.assertIn("dominant", regime)
        for r in ["calm", "trending", "stressed", "crash_prone"]:
            self.assertIn(r, regime["probabilities"], f"regime missing: {r}")

    def test_simulation_event_keys(self):
        events = self.sim["events"]
        expected_events = ["large_move", "vol_spike", "trend_reversal",
                           "earnings_reaction", "liquidity_stress", "crash_like"]
        for ev in expected_events:
            self.assertIn(ev, events, f"events missing: {ev}")
            for h in ["5d", "10d", "20d"]:
                self.assertIn(h, events[ev], f"event {ev} missing horizon: {h}")

    def test_simulation_scenario_keys(self):
        scenarios = self.sim["scenarios"]
        for s in ["base_case", "vol_expansion", "trend_shift", "tail_risk"]:
            self.assertIn(s, scenarios, f"scenarios missing: {s}")
            self.assertIn("weight", scenarios[s], f"scenario {s} missing 'weight'")

    def test_simulation_confidence_keys(self):
        conf = self.sim["confidence"]
        for key in ["disagreement", "level", "top_drivers"]:
            self.assertIn(key, conf, f"confidence missing: {key}")


class TestTestCountConsistency(unittest.TestCase):
    """Test counts referenced in docs must match actual unittest discovery."""

    def _count_tests_in_module(self, module_name: str) -> int:
        """Load a test module and count its tests."""
        import unittest
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromName(module_name)
        count = 0
        for test in suite:
            if isinstance(test, unittest.TestSuite):
                for t in test:
                    count += 1
            else:
                count += 1
        return count

    def _get_actual_counts(self) -> dict:
        """Get actual test counts from all modules."""
        modules = {
            "test_unit_short_term": "tests.test_unit_short_term",
            "test_unit_ccrlo": "tests.test_unit_ccrlo",
            "test_unit_simulation": "tests.test_unit_simulation",
            "test_unit_tags": "tests.test_unit_tags",
            "test_contracts": "tests.test_contracts",
            "test_integration": "tests.test_integration",
        }
        return {name: self._count_tests_in_module(mod) for name, mod in modules.items()}

    def test_copilot_instructions_test_counts(self):
        """Test counts in copilot-instructions.md must match actual counts."""
        ci_path = os.path.join(_BASE_DIR, ".github", "copilot-instructions.md")
        with open(ci_path, "r", encoding="utf-8") as f:
            content = f.read()

        actual = self._get_actual_counts()

        # Check each module's count mentioned in the file
        patterns = {
            "test_unit_short_term": r"test_unit_short_term\.py.*?(\d+)\s*tests",
            "test_unit_ccrlo": r"test_unit_ccrlo\.py.*?(\d+)\s*tests",
            "test_unit_simulation": r"test_unit_simulation\.py.*?(\d+)\s*tests",
            "test_contracts": r"test_contracts\.py.*?(\d+)\s*tests",
            "test_integration": r"test_integration\.py.*?(\d+)\s*tests",
        }

        for module, pattern in patterns.items():
            match = re.search(pattern, content)
            if match:
                documented = int(match.group(1))
                self.assertEqual(
                    documented, actual[module],
                    f"copilot-instructions.md says {module} has {documented} tests, "
                    f"but actual count is {actual[module]}",
                )

    def test_total_test_count(self):
        """Total test count in docs must match actual total across all suites."""
        actual = self._get_actual_counts()
        # Include this docs module's own count in the total
        docs_count = self._count_tests_in_module("tests.test_docs_consistency")
        full_total = sum(actual.values()) + docs_count

        ci_path = os.path.join(_BASE_DIR, ".github", "copilot-instructions.md")
        with open(ci_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Find "NNN tests, N suites" references
        matches = re.findall(r"(\d+)\s*tests,\s*\d+\s*suites", content)
        for m in matches:
            documented = int(m)
            self.assertEqual(
                documented, full_total,
                f"Documented total '{documented} tests' doesn't match actual {full_total}",
            )


class TestAgentGateReferences(unittest.TestCase):
    """Agent gate checklists must reference scripts/commands that exist."""

    def _extract_script_refs(self, content: str) -> list[str]:
        """Extract script filenames referenced in an agent .md file."""
        # Match patterns like: validate_numbers.py, analyst_compute_engine.py, run_tests.py
        refs = re.findall(r'(\w+\.py)', content)
        return list(set(refs))

    def test_stock_analyst_script_refs(self):
        """All scripts referenced in stock-analyst.agent.md must exist."""
        agent_path = os.path.join(_BASE_DIR, ".github", "agents", "stock-analyst.agent.md")
        with open(agent_path, "r", encoding="utf-8") as f:
            content = f.read()

        refs = self._extract_script_refs(content)
        scripts_dir = os.path.join(_BASE_DIR, "scripts")

        missing = []
        for ref in refs:
            # Check in scripts/ root
            if not os.path.isfile(os.path.join(scripts_dir, ref)):
                # Also check in scripts/tests/
                if not os.path.isfile(os.path.join(scripts_dir, "tests", ref)):
                    missing.append(ref)

        self.assertEqual(missing, [],
                         f"stock-analyst.agent.md references non-existent scripts: {missing}")

    def test_test_engineer_script_refs(self):
        """All scripts referenced in test-engineer.agent.md must exist."""
        agent_path = os.path.join(_BASE_DIR, ".github", "agents", "test-engineer.agent.md")
        with open(agent_path, "r", encoding="utf-8") as f:
            content = f.read()

        refs = self._extract_script_refs(content)
        scripts_dir = os.path.join(_BASE_DIR, "scripts")

        missing = []
        for ref in refs:
            if not os.path.isfile(os.path.join(scripts_dir, ref)):
                if not os.path.isfile(os.path.join(scripts_dir, "tests", ref)):
                    missing.append(ref)

        self.assertEqual(missing, [],
                         f"test-engineer.agent.md references non-existent scripts: {missing}")


class TestGoldenRefsComplete(unittest.TestCase):
    """Every fixture-based ticker must have golden references, and vice versa."""

    FIXTURE_TICKERS = ["TEST", "STRESS"]  # from MINIMAL_BUNDLE, DISTRESSED_BUNDLE
    SIGNAL_TYPES = ["short_term", "ccrlo", "simulation"]

    def test_fixture_tickers_have_golden_refs(self):
        """TEST and STRESS must have golden reference files."""
        golden_dir = os.path.join(_SCRIPT_DIR, "tests", "golden")
        missing = []
        for ticker in self.FIXTURE_TICKERS:
            for sig in self.SIGNAL_TYPES:
                path = os.path.join(golden_dir, f"{ticker}_{sig}.golden.json")
                if not os.path.isfile(path):
                    missing.append(f"{ticker}_{sig}.golden.json")
        self.assertEqual(missing, [], f"Missing golden refs: {missing}")

    def test_bundle_tickers_have_golden_refs(self):
        """Every ticker with a data bundle should have golden refs."""
        data_dir = os.path.join(_SCRIPT_DIR, "data")
        golden_dir = os.path.join(_SCRIPT_DIR, "tests", "golden")
        if not os.path.isdir(data_dir):
            self.skipTest("No data directory")

        bundle_tickers = [f.replace("_bundle.json", "")
                          for f in os.listdir(data_dir) if f.endswith("_bundle.json")]
        missing = []
        for ticker in bundle_tickers:
            for sig in self.SIGNAL_TYPES:
                path = os.path.join(golden_dir, f"{ticker}_{sig}.golden.json")
                if not os.path.isfile(path):
                    missing.append(f"{ticker}_{sig}.golden.json")
        self.assertEqual(missing, [], f"Bundle tickers without golden refs: {missing}")

    def test_no_orphan_golden_refs(self):
        """Every golden ref must have a corresponding bundle or fixture."""
        golden_dir = os.path.join(_SCRIPT_DIR, "tests", "golden")
        data_dir = os.path.join(_SCRIPT_DIR, "data")
        if not os.path.isdir(golden_dir):
            self.skipTest("No golden directory")

        bundle_tickers = set()
        if os.path.isdir(data_dir):
            bundle_tickers = set(f.replace("_bundle.json", "")
                                 for f in os.listdir(data_dir) if f.endswith("_bundle.json"))
        all_valid_tickers = bundle_tickers | set(self.FIXTURE_TICKERS)

        orphans = []
        for f in os.listdir(golden_dir):
            if f.endswith(".golden.json"):
                ticker = f.split("_")[0]
                if ticker not in all_valid_tickers:
                    orphans.append(f)

        self.assertEqual(orphans, [], f"Orphan golden refs (no bundle/fixture): {orphans}")


class TestValidatorScriptConsistency(unittest.TestCase):
    """Validate that validator scripts check the same fields as the contracts."""

    def test_output_validator_checks_all_short_term_keys(self):
        """validate_outputs.py must check all SHORT_TERM_SIGNAL contract keys."""
        vo_path = os.path.join(_SCRIPT_DIR, "validate_outputs.py")
        with open(vo_path, "r", encoding="utf-8") as f:
            content = f.read()

        # These strings must appear in the validator
        for field in ["trend_break", "fragility", "correction_probabilities",
                      "entry_active", "tb", "vs", "vf",
                      "leverage", "liquidity", "info_risk", "valuation", "momentum",
                      "mild", "standard", "severe", "black_swan"]:
            self.assertIn(field, content,
                          f"validate_outputs.py doesn't check SHORT_TERM field: {field}")

    def test_output_validator_checks_all_ccrlo_keys(self):
        """validate_outputs.py must check all CCRLO_SIGNAL contract keys."""
        vo_path = os.path.join(_SCRIPT_DIR, "validate_outputs.py")
        with open(vo_path, "r", encoding="utf-8") as f:
            content = f.read()

        for field in ["composite_score", "correction_probability", "risk_level",
                      "term_spread", "credit_risk", "ig_credit", "volatility_regime",
                      "financial_conditions", "momentum_12m", "realized_vol"]:
            self.assertIn(field, content,
                          f"validate_outputs.py doesn't check CCRLO field: {field}")

    def test_output_validator_checks_all_simulation_keys(self):
        """validate_outputs.py must check all SIMULATION_SIGNAL contract keys."""
        vo_path = os.path.join(_SCRIPT_DIR, "validate_outputs.py")
        with open(vo_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Top-level structure keys (checked by name in the validator)
        for field in ["regime", "events", "scenarios", "composite_event_risk", "risk_color",
                      "weighted_expected", "confidence"]:
            self.assertIn(field, content,
                          f"validate_outputs.py doesn't check SIMULATION field: {field}")

        # Event names (checked by name in event scoring loop)
        for field in ["large_move", "vol_spike", "trend_reversal",
                      "earnings_reaction", "liquidity_stress", "crash_like"]:
            self.assertIn(field, content,
                          f"validate_outputs.py doesn't check event: {field}")

        # Scenario names (checked by name in scenario weight loop)
        for field in ["base_case", "vol_expansion", "trend_shift", "tail_risk"]:
            self.assertIn(field, content,
                          f"validate_outputs.py doesn't check scenario: {field}")

        # Regime validation (checks sum, non-negative, dominant — may not mention
        # regime names as literals since it uses dict.values())
        self.assertIn("regime_sum", content,
                      "validate_outputs.py must check regime probability sum")
        self.assertIn("regime_nonneg", content,
                      "validate_outputs.py must check regime non-negative")
        self.assertIn("dominant", content,
                      "validate_outputs.py must check dominant regime")


class TestArchitectureMdConsistency(unittest.TestCase):
    """ARCHITECTURE.md must stay in sync with actual system state."""

    def setUp(self):
        arch_path = os.path.join(_BASE_DIR, "ARCHITECTURE.md")
        if not os.path.isfile(arch_path):
            self.skipTest("ARCHITECTURE.md not found")
        with open(arch_path, "r", encoding="utf-8") as f:
            self.content = f.read()

    def test_architecture_exists(self):
        """ARCHITECTURE.md must exist at project root."""
        self.assertTrue(len(self.content) > 0)

    def test_both_agents_mentioned(self):
        """All agents must appear."""
        self.assertIn("stock-analyst", self.content,
                      "ARCHITECTURE.md missing stock-analyst agent")
        self.assertIn("test-engineer", self.content,
                      "ARCHITECTURE.md missing test-engineer agent")
        self.assertIn("portfolio-manager", self.content,
                      "ARCHITECTURE.md missing portfolio-manager agent")

    def test_all_skills_mentioned(self):
        """All 11 skill names must appear in the architecture."""
        expected_skills = [
            "data-collection", "analyst-compute-engine", "short-term-analysis",
            "long-term-prediction", "simulation", "report-generation",
            "report-fix", "report-audit", "numerical-audit", "system-test",
            "stock-tagging", "portfolio-build", "portfolio-audit",
        ]
        for skill in expected_skills:
            self.assertIn(skill, self.content,
                          f"ARCHITECTURE.md missing skill: {skill}")

    def test_all_compute_scripts_mentioned(self):
        """All Python compute scripts must appear."""
        scripts = [
            "analyst_compute_engine.py", "compute_short_term.py",
            "compute_ccrlo.py", "compute_simulation.py", "compute_tags.py",
            "validate_inputs.py", "validate_outputs.py",
            "validate_numbers.py", "run_tests.py",
            "build_portfolio.py", "audit_portfolio.py",
            "portfolio_optimizer.py",
        ]
        for script in scripts:
            self.assertIn(script, self.content,
                          f"ARCHITECTURE.md missing script: {script}")

    def test_test_count_matches(self):
        """Test counts in ARCHITECTURE.md must match actual total."""
        # Count actual tests across all modules
        loader = unittest.TestLoader()
        all_modules = [
            "tests.test_unit_short_term", "tests.test_unit_ccrlo",
            "tests.test_unit_simulation", "tests.test_unit_tags",
            "tests.test_contracts",
            "tests.test_integration", "tests.test_docs_consistency",
        ]
        total = 0
        for mod in all_modules:
            suite = loader.loadTestsFromName(mod)
            for test_group in suite:
                if isinstance(test_group, unittest.TestSuite):
                    for _ in test_group:
                        total += 1
                else:
                    total += 1

        # Find total test count references in ARCHITECTURE.md
        # Match patterns like "183 tests · 6 suites" or "183 automated tests (6 suites)"
        # but NOT "135 quick tests" (which is a suite-specific count, not the total)
        total_patterns = [
            r"(\d+)\s*tests\s*[·.]\s*\d+\s*suites",       # "183 tests · 6 suites"
            r"(\d+)\s*automated\s*tests\s*\(\d+\s*suites",  # "183 automated tests (6 suites)"
        ]
        for pattern in total_patterns:
            for match in re.finditer(pattern, self.content):
                documented = int(match.group(1))
                self.assertEqual(
                    documented, total,
                    f"ARCHITECTURE.md says '{documented} tests' but actual is {total}",
                )

    def test_suite_count_matches(self):
        """Number of suites mentioned must match actual unique suite count in run_tests.py."""
        # Count actual suites by importing SUITES from run_tests
        rt_path = os.path.join(_SCRIPT_DIR, "run_tests.py")
        with open(rt_path, "r", encoding="utf-8") as f:
            rt_content = f.read()
        # Extract SUITES dict section and count keys within it
        suites_match = re.search(r'SUITES\s*=\s*\{(.+?)^\}', rt_content, re.DOTALL | re.MULTILINE)
        if suites_match:
            suites_block = suites_match.group(1)
            suite_names = re.findall(r'^\s+"(\w+)":\s*\[', suites_block, re.MULTILINE)
            actual_suites = len(suite_names)
        else:
            self.fail("Cannot find SUITES dict in run_tests.py")
            return

        # Find "N suites" in ARCHITECTURE.md
        suite_matches = re.findall(r"(\d+)\s*suites", self.content)
        for m in suite_matches:
            documented = int(m)
            self.assertEqual(
                documented, actual_suites,
                f"ARCHITECTURE.md says '{documented} suites' but actual is {actual_suites}",
            )

    def test_signal_names_present(self):
        """All three signal contract names must appear."""
        for signal in ["SHORT_TERM_SIGNAL", "CCRLO_SIGNAL", "SIMULATION_SIGNAL"]:
            # Check for the signal name or its common short form
            short = signal.replace("_SIGNAL", "").replace("_", " ")
            found = signal in self.content or short in self.content
            self.assertTrue(found,
                            f"ARCHITECTURE.md missing signal reference: {signal}")

    def test_all_report_sections_referenced(self):
        """Key report sections must be referenced in cross-section mapping."""
        # These sections are in the Signal Cross-Section Mapping diagram
        for section in ["Section 3", "Section 5", "Section 11",
                        "Section 12", "Section 13", "Section 18"]:
            self.assertIn(section, self.content,
                          f"ARCHITECTURE.md cross-section mapping missing: {section}")

    def test_regime_concept_present(self):
        """Regime detection concept must appear in architecture."""
        # ARCHITECTURE.md references regimes at the concept level, not individual names
        found = ("Regime" in self.content or "regime" in self.content)
        self.assertTrue(found, "ARCHITECTURE.md missing regime detection concept")


if __name__ == "__main__":
    unittest.main()
