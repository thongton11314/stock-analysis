"""
Shared test fixtures and helpers for the market-analysis test suite.

Provides:
  - load_bundle(ticker) — load a data bundle from scripts/data/
  - load_signal(ticker, signal_type) — load computed signal from scripts/output/
  - MINIMAL_BUNDLE — a minimal valid bundle for unit tests (no file I/O)
  - GOLDEN_DIR — path to golden reference outputs
  - save_golden(ticker) — snapshot current outputs as golden references
  - assert_signal_keys(test_case, signal, required_keys) — structural assertion
"""

import json
import os
import sys

_SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BASE_DIR = os.path.dirname(_SCRIPT_DIR)

# Ensure scripts/ is importable
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

DATA_DIR = os.path.join(_SCRIPT_DIR, "data")
OUTPUT_DIR = os.path.join(_SCRIPT_DIR, "output")
GOLDEN_DIR = os.path.join(_SCRIPT_DIR, "tests", "golden")
REPORTS_DIR = os.path.join(_BASE_DIR, "reports")


def load_bundle(ticker: str) -> dict:
    """Load a data bundle JSON file."""
    path = os.path.join(DATA_DIR, f"{ticker}_bundle.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Bundle not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_signal(ticker: str, signal_type: str) -> dict:
    """Load a computed signal JSON file.

    signal_type: 'short_term', 'ccrlo', 'simulation', 'engine_report'
    """
    path = os.path.join(OUTPUT_DIR, f"{ticker}_{signal_type}.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Signal not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_golden(ticker: str):
    """Snapshot current outputs as golden references for regression testing."""
    os.makedirs(GOLDEN_DIR, exist_ok=True)
    for signal_type in ("short_term", "ccrlo", "simulation"):
        src = os.path.join(OUTPUT_DIR, f"{ticker}_{signal_type}.json")
        if os.path.exists(src):
            dst = os.path.join(GOLDEN_DIR, f"{ticker}_{signal_type}.golden.json")
            with open(src, "r", encoding="utf-8") as f:
                data = json.load(f)
            with open(dst, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            print(f"  Saved golden: {dst}")


def load_golden(ticker: str, signal_type: str) -> dict | None:
    """Load golden reference, or None if not yet snapshotted."""
    path = os.path.join(GOLDEN_DIR, f"{ticker}_{signal_type}.golden.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def available_bundles() -> list[str]:
    """Return list of tickers that have data bundles."""
    if not os.path.isdir(DATA_DIR):
        return []
    return [
        f.replace("_bundle.json", "")
        for f in os.listdir(DATA_DIR)
        if f.endswith("_bundle.json")
    ]


def available_golden() -> list[str]:
    """Return list of tickers that have golden references."""
    if not os.path.isdir(GOLDEN_DIR):
        return []
    tickers = set()
    for f in os.listdir(GOLDEN_DIR):
        if f.endswith(".golden.json"):
            tickers.add(f.split("_")[0])
    return sorted(tickers)


def assert_signal_keys(test_case, signal: dict, required_keys: list[str], prefix: str = ""):
    """Assert that a signal dict contains all required top-level keys."""
    for key in required_keys:
        test_case.assertIn(key, signal, f"{prefix}Missing required key: '{key}'")


# ═══════════════════════════════════════════════════════════════
# MINIMAL BUNDLES — deterministic fixtures for unit tests
# (no file I/O, no Alpha Vantage dependency)
# ═══════════════════════════════════════════════════════════════

MINIMAL_BUNDLE = {
    "ticker": "TEST",
    "as_of": "2026-03-25",
    "global_quote": {
        "price": 100.0,
        "open": 99.0,
        "high": 102.0,
        "low": 98.0,
        "volume": 5000000,
        "previous_close": 99.50,
        "change": 0.50,
        "change_percent": 0.5025,
        "volume_sma_20": 4800000,
    },
    "company_overview": {
        "market_cap": 50000000000,
        "pe_ratio": 25.0,
        "forward_pe": 22.0,
        "beta": 1.2,
        "eps": 4.0,
        "52_week_high": 120.0,
        "52_week_low": 80.0,
        "analyst_target_price": 115.0,
        "sector": "TECHNOLOGY",
        "shares_outstanding": 500000000,
        "debt_to_equity": 0.5,
        "ipo_date": "2010-01-01",
    },
    "sma_200": [{"date": f"2026-03-{25-i:02d}", "value": str(105 - i * 0.1)} for i in range(25)],
    "sma_50": [{"date": f"2026-03-{25-i:02d}", "value": str(102 - i * 0.05)} for i in range(10)],
    "atr_14": [{"date": f"2026-03-{25-i:02d}", "value": str(2.0 + (i % 5) * 0.1)} for i in range(300)],
    "rsi": [{"date": "2026-03-25", "value": "55.0"}],
    "macd": [{"date": "2026-03-25", "MACD": "1.5", "MACD_Signal": "1.2", "MACD_Hist": "0.3"}],
    "bbands": [{"date": "2026-03-25", "Real Upper Band": "108.0", "Real Middle Band": "100.0", "Real Lower Band": "92.0"}],
    "adx": [{"date": "2026-03-25", "value": "22.0"}],
    "income_statement": {"annual": [{"totalRevenue": "10000000000", "costOfRevenue": "6000000000", "grossProfit": "4000000000", "operatingIncome": "2500000000", "netIncome": "2000000000"}]},
    "balance_sheet": {"annual": [{"totalAssets": "30000000000", "totalLiabilities": "15000000000", "totalShareholderEquity": "15000000000", "longTermDebt": "7500000000"}]},
    "cash_flow": {"annual": [{"operatingCashflow": "3000000000", "capitalExpenditures": "-500000000"}]},
    "earnings": {"quarterly": [
        {"reportedDate": "2026-01-15", "reportedEPS": "1.10", "estimatedEPS": "1.05", "surprise": "0.05", "surprise_percentage": "4.76"},
        {"reportedDate": "2025-10-15", "reportedEPS": "1.00", "estimatedEPS": "0.98", "surprise": "0.02", "surprise_percentage": "2.04"},
    ]},
    "federal_funds_rate": [
        {"date": "2026-02-01", "value": "4.08"},
        {"date": "2026-01-01", "value": "4.33"},
        {"date": "2025-12-01", "value": "4.33"},
        {"date": "2025-11-01", "value": "4.58"},
        {"date": "2025-10-01", "value": "4.58"},
        {"date": "2025-09-01", "value": "4.83"},
        {"date": "2025-08-01", "value": "5.33"},
        {"date": "2025-07-01", "value": "5.33"},
        {"date": "2025-06-01", "value": "5.33"},
        {"date": "2025-05-01", "value": "5.33"},
        {"date": "2025-04-01", "value": "5.33"},
        {"date": "2025-03-01", "value": "5.33"},
    ],
    "cpi": [{"date": "2026-01-01", "value": "320.0"}, {"date": "2025-12-01", "value": "318.5"},
            {"date": "2025-11-01", "value": "317.0"}, {"date": "2025-10-01", "value": "316.0"}],
    "unemployment": [{"date": "2026-01-01", "value": "4.2"}, {"date": "2025-12-01", "value": "4.1"}],
    "real_gdp": [{"date": "2025-10-01", "value": "6100.0"}],
}


# Bundle with distressed signals for testing edge cases
DISTRESSED_BUNDLE = {
    **MINIMAL_BUNDLE,
    "ticker": "STRESS",
    "global_quote": {
        **MINIMAL_BUNDLE["global_quote"],
        "price": 75.0,
        "volume": 12000000,
        "previous_close": 80.0,
        "change": -5.0,
        "change_percent": -6.25,
    },
    "company_overview": {
        **MINIMAL_BUNDLE["company_overview"],
        "beta": 2.1,
        "pe_ratio": 85.0,
        "debt_to_equity": 3.5,
        "ipo_date": "2025-01-01",  # Recent IPO
    },
    "sma_200": [{"date": f"2026-03-{25-i:02d}", "value": str(110 + i * 0.2)} for i in range(25)],
    "sma_50": [{"date": f"2026-03-{25-i:02d}", "value": str(95 + i * 0.1)} for i in range(10)],
    "rsi": [{"date": "2026-03-25", "value": "25.0"}],  # Oversold
    "adx": [{"date": "2026-03-25", "value": "35.0"}],  # Strong trend
    "atr_14": [{"date": f"2026-03-{25-i:02d}", "value": str(5.0 + (i % 3) * 0.5)} for i in range(300)],
    "earnings": {"quarterly": [
        {"reportedDate": "2026-01-15", "reportedEPS": "0.50", "estimatedEPS": "0.80", "surprise": "-0.30", "surprise_percentage": "-37.5"},
        {"reportedDate": "2025-10-15", "reportedEPS": "0.40", "estimatedEPS": "0.70", "surprise": "-0.30", "surprise_percentage": "-42.8"},
    ]},
}
