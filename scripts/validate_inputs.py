"""
Data Bundle Input Validator

Validates the data bundle collected from Alpha Vantage MCP before it enters
the computation pipeline. Checks completeness, freshness, range validity,
and structural integrity.

Usage:
    python scripts/validate_inputs.py --input data_bundle.json --output validation_report.json
"""

import argparse
import json
import sys
from datetime import datetime, timedelta


def check_required_fields(data: dict) -> list[dict]:
    """Check that all required top-level fields are present and non-empty."""
    checks = []

    required_fields = {
        "ticker": "string",
        "as_of": "string",
        "global_quote": "dict",
        "company_overview": "dict",
        "sma_200": "list",
        "sma_50": "list",
        "atr_14": "list",
        "rsi": "list",
        "macd": "list",
        "bbands": "list",
        "adx": "list",
        "income_statement": "dict",
        "balance_sheet": "dict",
        "cash_flow": "dict",
        "earnings": "dict",
    }

    for field, expected_type in required_fields.items():
        value = data.get(field)
        if value is None:
            checks.append({"field": field, "status": "FAIL", "reason": "Missing"})
        elif expected_type == "list" and (not isinstance(value, list) or len(value) == 0):
            checks.append({"field": field, "status": "FAIL", "reason": "Empty list"})
        elif expected_type == "dict" and (not isinstance(value, dict) or len(value) == 0):
            checks.append({"field": field, "status": "FAIL", "reason": "Empty dict"})
        elif expected_type == "string" and (not isinstance(value, str) or len(value.strip()) == 0):
            checks.append({"field": field, "status": "FAIL", "reason": "Empty string"})
        else:
            checks.append({"field": field, "status": "PASS", "reason": ""})

    return checks


def check_optional_fields(data: dict) -> list[dict]:
    """Check optional but recommended fields."""
    checks = []

    optional = [
        "ema_12", "ema_26", "news_sentiment", "institutional_holdings",
        "insider_transactions",
        "federal_funds_rate", "cpi", "unemployment", "real_gdp",
        "peers",
    ]

    for field in optional:
        value = data.get(field)
        if value is None or (isinstance(value, (list, dict)) and len(value) == 0):
            checks.append({"field": field, "status": "WARN", "reason": "Missing (recommended)"})
        else:
            checks.append({"field": field, "status": "PASS", "reason": ""})

    # Peers structure validation — should be a dict with ticker keys
    peers = data.get("peers")
    if isinstance(peers, dict) and len(peers) > 0:
        peer_count = len(peers)
        if peer_count >= 3:
            checks.append({"field": "peers_depth", "status": "PASS",
                           "reason": f"{peer_count} peers (min 3)"})
        else:
            checks.append({"field": "peers_depth", "status": "WARN",
                           "reason": f"Only {peer_count} peer(s) — recommend 3-5"})
    elif isinstance(peers, list):
        checks.append({"field": "peers_depth", "status": "WARN",
                       "reason": "Peers stored as list, expected dict keyed by ticker"})

    # Volume history depth — needed for accurate VF computation
    gq = data.get("global_quote", {})
    vol_hist = gq.get("volume_history", [])
    vol_sma = gq.get("volume_sma_20")
    if isinstance(vol_hist, list) and len(vol_hist) >= 20:
        checks.append({"field": "volume_history", "status": "PASS",
                       "reason": f"{len(vol_hist)} daily volumes (VF uses 20-day avg)"})
    elif vol_sma is not None and float(vol_sma) > 0:
        checks.append({"field": "volume_history", "status": "PASS",
                       "reason": f"volume_sma_20 provided ({vol_sma}) — VF fallback available"})
    else:
        checks.append({"field": "volume_history", "status": "WARN",
                       "reason": "No volume_history or volume_sma_20 — VF gate defaults to False"})

    return checks


def check_macro_data_depth(data: dict) -> list[dict]:
    """Validate macro data has sufficient history for charts and computations.

    CRITICAL: FEDERAL_FUNDS_RATE needs ≥12 monthly values for the Fed chart.
    Storing only 1 data point causes the report generator to fabricate
    the remaining 11 months, producing incorrect charts.
    """
    checks = []

    macro_min_depths = {
        "federal_funds_rate": {"min": 12, "label": "Fed Funds Rate (≥12 for chart)"},
        "cpi": {"min": 4, "label": "CPI (≥4 for trend)"},
        "unemployment": {"min": 4, "label": "Unemployment (≥4 for trend)"},
        "real_gdp": {"min": 4, "label": "Real GDP (≥4 quarters)"},
    }

    for field, spec in macro_min_depths.items():
        values = data.get(field, [])
        if not isinstance(values, list):
            checks.append({
                "field": f"{field}_depth",
                "status": "WARN",
                "reason": f"{spec['label']}: not a list",
            })
            continue

        count = len(values)
        if count >= spec["min"]:
            checks.append({
                "field": f"{field}_depth",
                "status": "PASS",
                "reason": f"{spec['label']}: {count} values (min {spec['min']})",
            })
        elif count == 0:
            checks.append({
                "field": f"{field}_depth",
                "status": "WARN",
                "reason": f"{spec['label']}: no data",
            })
        else:
            # Specifically flag federal_funds_rate with only 1 value as a WARN
            # since this is a known failure mode that causes fabricated Fed charts
            severity = "WARN"
            note = ""
            if field == "federal_funds_rate" and count == 1:
                note = " — CRITICAL: Only 1 value stored. Fed chart will have fabricated data. Re-fetch with full history."
            checks.append({
                "field": f"{field}_depth",
                "status": severity,
                "reason": f"{spec['label']}: only {count} values, need {spec['min']}{note}",
            })

    return checks


def check_price_sanity(data: dict) -> list[dict]:
    """Validate price data is reasonable."""
    checks = []
    gq = data.get("global_quote", {})

    price = gq.get("price")
    if price is not None:
        p = float(price)
        if p <= 0:
            checks.append({"field": "price", "status": "FAIL", "reason": f"Non-positive price: {p}"})
        elif p > 100000:
            checks.append({"field": "price", "status": "WARN", "reason": f"Unusually high price: {p}"})
        else:
            checks.append({"field": "price", "status": "PASS", "reason": f"${p:.2f}"})
    else:
        checks.append({"field": "price", "status": "FAIL", "reason": "Missing price"})

    volume = gq.get("volume")
    if volume is not None:
        v = float(volume)
        if v <= 0:
            checks.append({"field": "volume", "status": "WARN", "reason": f"Zero/negative volume: {v}"})
        else:
            checks.append({"field": "volume", "status": "PASS", "reason": f"{v:,.0f}"})
    else:
        checks.append({"field": "volume", "status": "WARN", "reason": "Missing volume"})

    return checks


def check_time_series_depth(data: dict) -> list[dict]:
    """Verify time series have sufficient history for computations."""
    checks = []

    min_depths = {
        "sma_200": 21,     # Need 20 days of slope
        "sma_50": 1,       # Need current value
        "atr_14": 50,      # Need 50-day average for fragility
        "rsi": 1,          # Need current value
        "macd": 1,         # Need current value
        "bbands": 1,       # Need current value
        "adx": 1,          # Need current value
    }

    for field, min_depth in min_depths.items():
        values = data.get(field, [])
        if len(values) >= min_depth:
            checks.append({
                "field": f"{field}_depth",
                "status": "PASS",
                "reason": f"{len(values)} values (min {min_depth})",
            })
        else:
            status = "FAIL" if min_depth > 1 else "WARN"
            checks.append({
                "field": f"{field}_depth",
                "status": status,
                "reason": f"Only {len(values)} values, need {min_depth}",
            })

    # ATR ideally needs 252 for percentile calculation
    atr_len = len(data.get("atr_14", []))
    if atr_len < 252:
        checks.append({
            "field": "atr_14_full_year",
            "status": "WARN",
            "reason": f"Only {atr_len} ATR values; 252 recommended for accurate percentile",
        })
    else:
        checks.append({
            "field": "atr_14_full_year",
            "status": "PASS",
            "reason": f"{atr_len} values (full year coverage)",
        })

    return checks


def check_indicator_ranges(data: dict) -> list[dict]:
    """Validate indicator values are within expected ranges."""
    checks = []

    # RSI should be 0-100
    rsi_vals = data.get("rsi", [])
    if rsi_vals:
        rsi = float(rsi_vals[0].get("value", 50))
        if 0 <= rsi <= 100:
            checks.append({"field": "rsi_range", "status": "PASS", "reason": f"RSI={rsi:.1f}"})
        else:
            checks.append({"field": "rsi_range", "status": "FAIL", "reason": f"RSI={rsi} out of [0,100]"})

    # ADX should be 0-100
    adx_vals = data.get("adx", [])
    if adx_vals:
        adx = float(adx_vals[0].get("value", 20))
        if 0 <= adx <= 100:
            checks.append({"field": "adx_range", "status": "PASS", "reason": f"ADX={adx:.1f}"})
        else:
            checks.append({"field": "adx_range", "status": "FAIL", "reason": f"ADX={adx} out of [0,100]"})

    # ATR should be positive
    atr_vals = data.get("atr_14", [])
    if atr_vals:
        atr = float(atr_vals[0].get("value", 0))
        if atr > 0:
            checks.append({"field": "atr_positive", "status": "PASS", "reason": f"ATR={atr:.4f}"})
        else:
            checks.append({"field": "atr_positive", "status": "FAIL", "reason": f"ATR={atr} must be positive"})

    # Beta should be a reasonable range
    beta = data.get("company_overview", {}).get("beta")
    if beta is not None and str(beta) not in ("None", "-", ""):
        b = float(beta)
        if -2 <= b <= 5:
            checks.append({"field": "beta_range", "status": "PASS", "reason": f"Beta={b:.2f}"})
        else:
            checks.append({"field": "beta_range", "status": "WARN", "reason": f"Beta={b} unusual"})

    return checks


def check_financial_data(data: dict) -> list[dict]:
    """Validate financial statement data."""
    checks = []

    # Income statement: revenue should be positive (for most companies)
    income = data.get("income_statement", {})
    annual = income.get("annual", income.get("annualReports", []))
    if isinstance(annual, list) and len(annual) > 0:
        revenue = annual[0].get("totalRevenue", annual[0].get("revenue"))
        if revenue is not None:
            rev = float(revenue)
            if rev > 0:
                checks.append({"field": "revenue", "status": "PASS", "reason": f"${rev/1e9:.2f}B"})
            else:
                checks.append({"field": "revenue", "status": "WARN", "reason": f"Revenue={rev} (pre-revenue company?)"})
        else:
            checks.append({"field": "revenue", "status": "WARN", "reason": "Revenue field not found"})
    else:
        checks.append({"field": "revenue", "status": "WARN", "reason": "No annual income data"})

    # Balance sheet: D/E ratio
    de = data.get("company_overview", {}).get("debt_to_equity")
    if de is not None and str(de) not in ("None", "-", ""):
        checks.append({"field": "debt_to_equity", "status": "PASS", "reason": f"D/E={float(de):.2f}"})
    else:
        checks.append({"field": "debt_to_equity", "status": "WARN", "reason": "D/E not available"})

    return checks


def check_data_freshness(data: dict) -> list[dict]:
    """Check that data is recent enough to be useful."""
    checks = []
    today = datetime.now()

    as_of = data.get("as_of")
    if as_of:
        try:
            data_date = datetime.strptime(as_of, "%Y-%m-%d")
            days_old = (today - data_date).days
            if days_old <= 3:
                checks.append({"field": "data_freshness", "status": "PASS", "reason": f"{days_old} days old"})
            elif days_old <= 7:
                checks.append({"field": "data_freshness", "status": "WARN", "reason": f"{days_old} days old"})
            else:
                checks.append({"field": "data_freshness", "status": "WARN", "reason": f"Data is {days_old} days old"})
        except ValueError:
            checks.append({"field": "data_freshness", "status": "WARN", "reason": f"Cannot parse date: {as_of}"})

    return checks


def run_validation(data: dict) -> dict:
    """Run all validation checks and produce report."""
    all_checks = []
    all_checks.extend(check_required_fields(data))
    all_checks.extend(check_optional_fields(data))
    all_checks.extend(check_macro_data_depth(data))
    all_checks.extend(check_price_sanity(data))
    all_checks.extend(check_time_series_depth(data))
    all_checks.extend(check_indicator_ranges(data))
    all_checks.extend(check_financial_data(data))
    all_checks.extend(check_data_freshness(data))

    fails = [c for c in all_checks if c["status"] == "FAIL"]
    warns = [c for c in all_checks if c["status"] == "WARN"]
    passes = [c for c in all_checks if c["status"] == "PASS"]

    # Overall status
    if fails:
        overall = "FAIL"
    elif len(warns) > 5:
        overall = "WARN"
    else:
        overall = "PASS"

    return {
        "ticker": data.get("ticker", "UNKNOWN"),
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
    parser = argparse.ArgumentParser(description="Validate data bundle inputs")
    parser.add_argument("--input", required=True, help="Path to data bundle JSON")
    parser.add_argument("--output", required=True, help="Path to write validation report JSON")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    report = run_validation(data)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    # Console output
    print(f"INPUT VALIDATION: {report['ticker']}")
    print(f"  Overall: {report['overall_status']}")
    print(f"  Passed: {report['summary']['passed']} | Warnings: {report['summary']['warnings']} | Failures: {report['summary']['failures']}")
    if report["blocking_failures"]:
        print(f"  BLOCKING FAILURES: {', '.join(report['blocking_failures'])}")

    sys.exit(0 if report["overall_status"] != "FAIL" else 1)


if __name__ == "__main__":
    main()
