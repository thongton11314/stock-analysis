"""
Unified Test Runner — Single entry point for all testing

Usage:
    python scripts/run_tests.py                    # Run all tests
    python scripts/run_tests.py --suite unit       # Unit tests only
    python scripts/run_tests.py --suite contract   # Contract + regression tests
    python scripts/run_tests.py --suite integration # Integration tests only
    python scripts/run_tests.py --suite quick      # Unit + contract (fast, no I/O)
    python scripts/run_tests.py --suite all        # Everything
    python scripts/run_tests.py --golden AMZN      # Snapshot golden refs for AMZN
    python scripts/run_tests.py --golden all       # Snapshot golden refs for all bundles
    python scripts/run_tests.py --live AMZN        # Live AV pipeline test (existing bundle)
    python scripts/run_tests.py --live MSFT --apikey KEY  # Live AV test (fetch fresh data)
    python scripts/run_tests.py --verbose          # Detailed output
    python scripts/run_tests.py --list             # List available suites/tests

Exit codes:
    0 = All tests passed
    1 = Some tests failed
    2 = Error loading tests
"""

import argparse
import json
import os
import sys
import unittest
from datetime import datetime

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_BASE_DIR = os.path.dirname(_SCRIPT_DIR)

# Ensure imports work
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)


# ═══════════════════════════════════════════════════════════════
# SUITE REGISTRY
# ═══════════════════════════════════════════════════════════════

SUITES = {
    "unit": [
        "tests.test_unit_short_term",
        "tests.test_unit_ccrlo",
        "tests.test_unit_simulation",
        "tests.test_unit_tags",
    ],
    "contract": [
        "tests.test_contracts",
    ],
    "integration": [
        "tests.test_integration",
    ],
    "docs": [
        "tests.test_docs_consistency",
    ],
    "quick": [
        "tests.test_unit_short_term",
        "tests.test_unit_ccrlo",
        "tests.test_unit_simulation",
        "tests.test_unit_tags",
        "tests.test_contracts",
    ],
    "all": [
        "tests.test_unit_short_term",
        "tests.test_unit_ccrlo",
        "tests.test_unit_simulation",
        "tests.test_unit_tags",
        "tests.test_contracts",
        "tests.test_integration",
        "tests.test_docs_consistency",
    ],
}


def load_suite(suite_name: str) -> unittest.TestSuite:
    """Load a test suite by name."""
    if suite_name not in SUITES:
        print(f"Unknown suite: '{suite_name}'. Available: {', '.join(SUITES.keys())}")
        sys.exit(2)

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    for module_name in SUITES[suite_name]:
        try:
            suite.addTests(loader.loadTestsFromName(module_name))
        except Exception as e:
            print(f"  ERROR loading {module_name}: {e}")
            sys.exit(2)

    return suite


def count_tests(suite: unittest.TestSuite) -> int:
    """Recursively count tests in a suite."""
    count = 0
    for test in suite:
        if isinstance(test, unittest.TestSuite):
            count += count_tests(test)
        else:
            count += 1
    return count


# ═══════════════════════════════════════════════════════════════
# GOLDEN REFERENCE MANAGEMENT
# ═══════════════════════════════════════════════════════════════

def snapshot_golden(ticker: str):
    """Snapshot current outputs as golden references."""
    from tests.fixtures import save_golden, GOLDEN_DIR, available_bundles, load_bundle
    from compute_short_term import compute_short_term_signal
    from compute_ccrlo import compute_ccrlo_signal
    from compute_simulation import compute_simulation_signal

    os.makedirs(GOLDEN_DIR, exist_ok=True)

    if ticker.upper() == "ALL":
        tickers = available_bundles()
        # Also add the synthetic fixture bundles
        tickers_to_do = list(tickers) + ["TEST", "STRESS"]
    else:
        tickers_to_do = [ticker.upper()]

    for t in tickers_to_do:
        print(f"\nSnapshoting golden refs for {t}...")

        if t == "TEST":
            from tests.fixtures import MINIMAL_BUNDLE
            data = MINIMAL_BUNDLE
        elif t == "STRESS":
            from tests.fixtures import DISTRESSED_BUNDLE
            data = DISTRESSED_BUNDLE
        else:
            try:
                data = load_bundle(t)
            except FileNotFoundError:
                print(f"  SKIP: No bundle for {t}")
                continue

        st = compute_short_term_signal(data)
        cc = compute_ccrlo_signal(data)
        sim = compute_simulation_signal(data, st, cc)

        for signal_type, signal_data in [
            ("short_term", st), ("ccrlo", cc), ("simulation", sim),
        ]:
            path = os.path.join(GOLDEN_DIR, f"{t}_{signal_type}.golden.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(signal_data, f, indent=2)
            print(f"  Saved: {path}")


# ═══════════════════════════════════════════════════════════════
# RESULT REPORTING
# ═══════════════════════════════════════════════════════════════

class TestReport:
    """Collect and display test results."""

    def __init__(self, result: unittest.TestResult, suite_name: str, duration: float):
        self.result = result
        self.suite_name = suite_name
        self.duration = duration
        self.total = result.testsRun
        self.failures = len(result.failures)
        self.errors = len(result.errors)
        self.skipped = len(result.skipped)
        self.passed = self.total - self.failures - self.errors - self.skipped

    def print_summary(self):
        """Print a formatted summary."""
        status = "PASS" if self.failures == 0 and self.errors == 0 else "FAIL"
        icon = "✅" if status == "PASS" else "❌"

        print(f"\n{'='*60}")
        print(f" {icon} TEST RESULTS — {self.suite_name.upper()}")
        print(f"{'='*60}")
        print(f"  Total:    {self.total}")
        print(f"  Passed:   {self.passed}")
        print(f"  Failed:   {self.failures}")
        print(f"  Errors:   {self.errors}")
        print(f"  Skipped:  {self.skipped}")
        print(f"  Duration: {self.duration:.2f}s")
        print(f"  Status:   {status}")
        print(f"{'='*60}")

        if self.failures > 0:
            print(f"\n FAILURES:")
            for test, traceback in self.result.failures:
                print(f"  ❌ {test}")
                # Show just the assertion message, not full traceback
                lines = traceback.strip().split("\n")
                msg = lines[-1] if lines else traceback
                print(f"     {msg}")

        if self.errors > 0:
            print(f"\n ERRORS:")
            for test, traceback in self.result.errors:
                print(f"  💥 {test}")
                lines = traceback.strip().split("\n")
                msg = lines[-1] if lines else traceback
                print(f"     {msg}")

    def to_json(self) -> dict:
        """Export results as JSON for the test agent."""
        return {
            "suite": self.suite_name,
            "ran_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "total": self.total,
            "passed": self.passed,
            "failed": self.failures,
            "errors": self.errors,
            "skipped": self.skipped,
            "duration_seconds": round(self.duration, 2),
            "status": "PASS" if self.failures == 0 and self.errors == 0 else "FAIL",
            "failure_details": [
                {"test": str(t), "message": tb.strip().split("\n")[-1]}
                for t, tb in self.result.failures
            ],
            "error_details": [
                {"test": str(t), "message": tb.strip().split("\n")[-1]}
                for t, tb in self.result.errors
            ],
        }


def list_tests():
    """List all available test suites and their test counts."""
    print(f"\n{'='*60}")
    print(f" AVAILABLE TEST SUITES")
    print(f"{'='*60}")
    loader = unittest.TestLoader()
    for name, modules in SUITES.items():
        suite = unittest.TestSuite()
        for mod in modules:
            try:
                suite.addTests(loader.loadTestsFromName(mod))
            except Exception:
                pass
        total = count_tests(suite)
        print(f"\n  {name:<15} ({total} tests)")
        for mod in modules:
            print(f"    → {mod}")
    print(f"\n  Other commands:")
    print(f"    --live TICKER [--apikey KEY]   Live Alpha Vantage pipeline test")
    print(f"    --golden TICKER|all            Snapshot golden references")
    print(f"\n  Use: python scripts/run_tests.py --suite <name>")
    print(f"{'='*60}")


# ═══════════════════════════════════════════════════════════════
# LIVE ALPHA VANTAGE PIPELINE TEST
# ═══════════════════════════════════════════════════════════════

def run_live_test(ticker: str, apikey: str | None = None):
    """Run a live end-to-end pipeline test for a ticker.

    If apikey is provided, fetches fresh data from Alpha Vantage.
    Otherwise, uses existing bundle in scripts/data/.
    """
    import time
    import urllib.request
    import urllib.error
    import urllib.parse

    ticker = ticker.upper()
    data_dir = os.path.join(_SCRIPT_DIR, "data")
    output_dir = os.path.join(_SCRIPT_DIR, "output")
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    bundle_path = os.path.join(data_dir, f"{ticker}_bundle.json")

    print(f"\n{'='*60}")
    print(f" LIVE PIPELINE TEST — {ticker}")
    print(f" Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    # ── Step 1: Get data ──
    if apikey:
        print(f"\n[1/4] FETCHING DATA from Alpha Vantage...")
        data, fetch_errors = _fetch_av_bundle(ticker, apikey)
        if not data.get("global_quote", {}).get("price"):
            print(f"  FATAL: No price data returned. Check ticker and API key.")
            sys.exit(1)
        with open(bundle_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"  Bundle saved: {bundle_path}")
        if fetch_errors:
            for err in fetch_errors:
                print(f"    ⚠ {err}")
    else:
        print(f"\n[1/4] LOADING existing bundle (no API key)...")
        if not os.path.exists(bundle_path):
            print(f"  ERROR: Bundle not found: {bundle_path}")
            print(f"  Provide --apikey to fetch fresh data, or ensure bundle exists.")
            sys.exit(1)
        with open(bundle_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        fetch_errors = []
        print(f"  Loaded: {bundle_path} (as_of: {data.get('as_of')})")

    # ── Step 2: Input validation ──
    from validate_inputs import run_validation as run_input_validation
    print(f"\n[2/4] INPUT VALIDATION...")
    input_report = run_input_validation(data)
    s = input_report["summary"]
    status = input_report["overall_status"]
    icon = "✅" if status == "PASS" else ("⚠️" if status == "WARN" else "❌")
    print(f"  {icon} {status} — Passed: {s['passed']} | Warnings: {s['warnings']} | Failures: {s['failures']}")

    # ── Step 3: Compute engine ──
    from compute_short_term import compute_short_term_signal
    from compute_ccrlo import compute_ccrlo_signal
    from compute_simulation import compute_simulation_signal
    from validate_outputs import run_validation as run_output_validation

    print(f"\n[3/4] RUNNING COMPUTE ENGINE...")
    try:
        st = compute_short_term_signal(data)
        cc = compute_ccrlo_signal(data)
        sim = compute_simulation_signal(data, st, cc)
    except Exception as e:
        print(f"  ❌ Computation error: {e}")
        sys.exit(3)

    # Tail-risk adjustment
    tw = sim.get("scenarios", {}).get("tail_risk", {}).get("weight", 0)
    if tw > 0:
        cp = st["correction_probabilities"]
        cp["mild"] = min(99, round(cp["mild"] * (1 + tw)))
        cp["standard"] = min(99, round(cp["standard"] * (1 + 2 * tw)))
        cp["severe"] = min(99, round(cp["severe"] * (1 + 3 * tw)))
        cp["severe"] = min(cp["severe"], cp["standard"])
        cp["black_swan"] = min(cp.get("black_swan", 11), cp["severe"])
        st["_tail_risk_applied"] = round(tw, 3)

    output_report = run_output_validation(st, cc, sim)
    o_status = output_report["overall_status"]
    icon = "✅" if o_status != "FAIL" else "❌"
    print(f"  {icon} Output validation: {o_status}")

    if o_status == "FAIL":
        print(f"  Blocking: {output_report.get('blocking_failures')}")
        sys.exit(3)

    # Print signal summary
    tb = st["trend_break"]
    frag = st["fragility"]
    print(f"\n  Short-Term: TB={tb['tb']} VS={tb['vs']} VF={tb['vf']} → Entry={tb['entry_active']}")
    print(f"  Fragility: {frag['score']}/5 ({frag['level']})")
    print(f"  CCRLO: {cc['composite_score']}/21 ({cc['risk_level']})")
    print(f"  Regime: {sim['regime']['dominant']} | Event Risk: {sim['composite_event_risk']}% ({sim['risk_color']})")

    # Save outputs
    for name, sig in [("short_term", st), ("ccrlo", cc), ("simulation", sim)]:
        with open(os.path.join(output_dir, f"{ticker}_{name}.json"), "w") as f:
            json.dump(sig, f, indent=2)

    # ── Step 4: Numerical audit ──
    from validate_numbers import run_audit
    print(f"\n[4/4] NUMERICAL AUDIT (Stage B)...")
    audit = run_audit(ticker, "B")
    a_s = audit.get("summary", {})
    a_status = audit.get("overall_status", "UNKNOWN")
    icon = "✅" if a_status != "FAIL" else "❌"
    print(f"  {icon} {a_status} — Passed: {a_s.get('passed', 0)} | Warnings: {a_s.get('warnings', 0)} | Failures: {a_s.get('failures', 0)}")

    with open(os.path.join(output_dir, f"{ticker}_numerical_audit.json"), "w") as f:
        json.dump(audit, f, indent=2)

    # ── Summary ──
    overall = "PASS" if o_status != "FAIL" and a_status != "FAIL" else "FAIL"
    print(f"\n{'='*60}")
    icon = "✅" if overall != "FAIL" else "❌"
    print(f" {icon} LIVE TEST {'PASSED' if overall != 'FAIL' else 'FAILED'} — {ticker}")
    print(f"{'='*60}")
    sys.exit(0 if overall != "FAIL" else 3)


def _fetch_av_bundle(ticker: str, apikey: str) -> tuple[dict, list]:
    """Fetch data from Alpha Vantage REST API and build a data bundle."""
    import time
    import urllib.request
    import urllib.error
    import urllib.parse

    BASE_URL = "https://www.alphavantage.co/query"
    DELAY = 13  # seconds between calls (free tier safe)

    def _av(function, params):
        params["function"] = function
        params["apikey"] = apikey
        url = f"{BASE_URL}?{urllib.parse.urlencode(params)}"
        print(f"    Fetching {function}...")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "MarketAnalysis/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as e:
            print(f"      ERROR: {e}")
            return {}
        for err_key in ("Error Message", "Note", "Information"):
            if err_key in data:
                print(f"      {err_key}: {data[err_key]}")
                return {}
        return data

    def _parse_tech(data, value_key, max_pts=300):
        for k in data:
            if "Technical Analysis" in k:
                series = data[k]
                return [{"date": d, "value": series[d].get(value_key, "0")}
                        for d in sorted(series.keys(), reverse=True)[:max_pts]]
        return []

    def _parse_macd(data, max_pts=10):
        for k in data:
            if "Technical Analysis" in k:
                series = data[k]
                return [{"date": d, "MACD": series[d].get("MACD", "0"),
                         "MACD_Signal": series[d].get("MACD_Signal", "0"),
                         "MACD_Hist": series[d].get("MACD_Hist", "0")}
                        for d in sorted(series.keys(), reverse=True)[:max_pts]]
        return []

    def _parse_bb(data, max_pts=10):
        for k in data:
            if "Technical Analysis" in k:
                series = data[k]
                return [{"date": d, "Real Upper Band": series[d].get("Real Upper Band", "0"),
                         "Real Middle Band": series[d].get("Real Middle Band", "0"),
                         "Real Lower Band": series[d].get("Real Lower Band", "0")}
                        for d in sorted(series.keys(), reverse=True)[:max_pts]]
        return []

    errors = []
    bundle = {"ticker": ticker, "as_of": datetime.now().strftime("%Y-%m-%d")}

    # Global Quote
    gq = _av("GLOBAL_QUOTE", {"symbol": ticker, "datatype": "json"}).get("Global Quote", {})
    if gq:
        bundle["global_quote"] = {
            "price": float(gq.get("05. price", 0)), "open": float(gq.get("02. open", 0)),
            "high": float(gq.get("03. high", 0)), "low": float(gq.get("04. low", 0)),
            "volume": float(gq.get("06. volume", 0)), "previous_close": float(gq.get("08. previous close", 0)),
            "change": float(gq.get("09. change", 0)),
            "change_percent": float(gq.get("10. change percent", "0").replace("%", "")),
        }
    else:
        errors.append("GLOBAL_QUOTE failed"); bundle["global_quote"] = {}
    time.sleep(DELAY)

    # Company Overview
    co = _av("OVERVIEW", {"symbol": ticker})
    if co and "Symbol" in co:
        _s = lambda v, d=None: d if v in (None, "None", "-", "") else v
        bundle["company_overview"] = {
            "market_cap": float(_s(co.get("MarketCapitalization"), 0)),
            "pe_ratio": float(_s(co.get("TrailingPE"), 0)), "forward_pe": float(_s(co.get("ForwardPE"), 0)),
            "beta": float(_s(co.get("Beta"), 1.0)), "eps": float(_s(co.get("EPS"), 0)),
            "52_week_high": float(_s(co.get("52WeekHigh"), 0)), "52_week_low": float(_s(co.get("52WeekLow"), 0)),
            "analyst_target_price": float(_s(co.get("AnalystTargetPrice"), 0)),
            "sector": co.get("Sector", "Unknown"), "shares_outstanding": float(_s(co.get("SharesOutstanding"), 0)),
            "debt_to_equity": float(_s(co.get("DebtToEquityRatio", co.get("DebtEquityRatio")), 0)),
            "ipo_date": co.get("IPODate"),
        }
    else:
        errors.append("OVERVIEW failed"); bundle["company_overview"] = {}
    time.sleep(DELAY)

    indicators = [
        ("SMA", {"symbol": ticker, "interval": "daily", "time_period": "200", "series_type": "close", "datatype": "json"}, "sma_200", "SMA", 30),
        ("SMA", {"symbol": ticker, "interval": "daily", "time_period": "50", "series_type": "close", "datatype": "json"}, "sma_50", "SMA", 10),
        ("ATR", {"symbol": ticker, "interval": "daily", "time_period": "14", "datatype": "json"}, "atr_14", "ATR", 300),
        ("RSI", {"symbol": ticker, "interval": "daily", "time_period": "14", "series_type": "close", "datatype": "json"}, "rsi", "RSI", 10),
        ("ADX", {"symbol": ticker, "interval": "daily", "time_period": "14", "datatype": "json"}, "adx", "ADX", 10),
    ]
    for func, params, key, val_key, pts in indicators:
        raw = _av(func, params)
        bundle[key] = _parse_tech(raw, val_key, pts)
        if not bundle[key]: errors.append(f"{key} failed")
        time.sleep(DELAY)

    # MACD
    raw = _av("MACD", {"symbol": ticker, "interval": "daily", "series_type": "close", "datatype": "json"})
    bundle["macd"] = _parse_macd(raw, 10)
    if not bundle["macd"]: errors.append("MACD failed")
    time.sleep(DELAY)

    # BBANDS
    raw = _av("BBANDS", {"symbol": ticker, "interval": "daily", "time_period": "20", "series_type": "close", "datatype": "json"})
    bundle["bbands"] = _parse_bb(raw, 10)
    if not bundle["bbands"]: errors.append("BBANDS failed")
    time.sleep(DELAY)

    # Financial statements
    for func, key, rkey in [("INCOME_STATEMENT", "income_statement", "annualReports"),
                             ("BALANCE_SHEET", "balance_sheet", "annualReports"),
                             ("CASH_FLOW", "cash_flow", "annualReports")]:
        raw = _av(func, {"symbol": ticker})
        if raw and rkey in raw:
            bundle[key] = {"annual": raw[rkey][:3]}
        else:
            errors.append(f"{func} failed"); bundle[key] = {"annual": []}
        time.sleep(DELAY)

    # Earnings
    raw = _av("EARNINGS", {"symbol": ticker})
    bundle["earnings"] = {"quarterly": raw.get("quarterlyEarnings", [])[:8]} if raw else {"quarterly": []}
    time.sleep(DELAY)

    # Macro data
    for func, params, key, dkey, n in [
        ("FEDERAL_FUNDS_RATE", {"interval": "monthly", "datatype": "json"}, "federal_funds_rate", "data", 24),
        ("CPI", {"interval": "monthly", "datatype": "json"}, "cpi", "data", 12),
        ("UNEMPLOYMENT", {"datatype": "json"}, "unemployment", "data", 12),
        ("REAL_GDP", {"interval": "quarterly", "datatype": "json"}, "real_gdp", "data", 8),
    ]:
        raw = _av(func, params)
        if raw and dkey in raw:
            bundle[key] = [{"date": d["date"], "value": d["value"]} for d in raw[dkey][:n]]
        else:
            bundle[key] = []
        time.sleep(DELAY)

    return bundle, errors


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Market Analysis Test Runner — unified test execution"
    )
    parser.add_argument("--suite", default="all",
                        choices=list(SUITES.keys()),
                        help="Which test suite to run (default: all)")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Verbose test output")
    parser.add_argument("--golden", metavar="TICKER",
                        help="Snapshot golden references (use 'all' for all bundles)")
    parser.add_argument("--live", metavar="TICKER",
                        help="Run live pipeline test for a ticker (uses existing bundle or --apikey)")
    parser.add_argument("--apikey", default=None,
                        help="Alpha Vantage API key for --live (or set AV_API_KEY env var)")
    parser.add_argument("--list", action="store_true",
                        help="List available test suites")
    parser.add_argument("--json", metavar="PATH",
                        help="Write JSON results to file")
    args = parser.parse_args()

    if args.list:
        list_tests()
        sys.exit(0)

    if args.golden:
        snapshot_golden(args.golden)
        sys.exit(0)

    if args.live:
        key = args.apikey or os.environ.get("AV_API_KEY")
        run_live_test(args.live, key)
        return  # run_live_test calls sys.exit

    # Run tests
    suite_name = args.suite
    verbosity = 2 if args.verbose else 1

    print(f"\n{'='*60}")
    print(f" MARKET ANALYSIS TEST RUNNER")
    print(f" Suite: {suite_name}")
    print(f" Date:  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    suite = load_suite(suite_name)
    total = count_tests(suite)
    print(f"\n  Loading {total} tests from {len(SUITES[suite_name])} modules...")

    runner = unittest.TextTestRunner(verbosity=verbosity, stream=sys.stdout)
    start = datetime.now()
    result = runner.run(suite)
    duration = (datetime.now() - start).total_seconds()

    report = TestReport(result, suite_name, duration)
    report.print_summary()

    # Write JSON if requested
    if args.json:
        report_data = report.to_json()
        output_path = args.json
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)
        print(f"\n  JSON report: {output_path}")

    # Always write latest results to scripts/output/
    output_dir = os.path.join(_SCRIPT_DIR, "output")
    os.makedirs(output_dir, exist_ok=True)
    latest_path = os.path.join(output_dir, "test_results_latest.json")
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(report.to_json(), f, indent=2)

    sys.exit(0 if report.failures == 0 and report.errors == 0 else 1)


if __name__ == "__main__":
    main()
