"""
Stock Tag Classification Engine

Deterministic, rule-based tag assignment across 5 dimensions:
  1. Profile  — company lifecycle (market cap + IPO age)
  2. Sector   — industry classification + thematic keywords
  3. Risk     — composite of fragility, CCRLO, regime signals
  4. Momentum — trend direction from SMA, RSI, 12-month return
  5. Valuation — P/E vs sector, forward vs trailing

Inputs:
  - Data bundle (scripts/data/[TICKER]_bundle.json)
  - SHORT_TERM_SIGNAL  (scripts/output/[TICKER]_short_term.json)
  - CCRLO_SIGNAL       (scripts/output/[TICKER]_ccrlo.json)
  - SIMULATION_SIGNAL  (scripts/output/[TICKER]_simulation.json)

Output:
  - scripts/output/[TICKER]_tags.json
  - Updates scripts/output/tags_index.json (cross-ticker registry)

Usage:
    python scripts/compute_tags.py --ticker AMZN
    python scripts/compute_tags.py --ticker AMZN --no-index  # skip index update

Can also be called programmatically:
    from compute_tags import compute_tags
    tags = compute_tags(bundle, short_term, ccrlo, simulation)
"""

import argparse
import json
import os
import sys
from datetime import datetime, date

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

DATA_DIR = os.path.join(_SCRIPT_DIR, "data")
OUTPUT_DIR = os.path.join(_SCRIPT_DIR, "output")
INDEX_PATH = os.path.join(OUTPUT_DIR, "tags_index.json")


# ═══════════════════════════════════════════════════════════════
# TAXONOMY DEFINITIONS
# ═══════════════════════════════════════════════════════════════

VALID_TAGS = {
    "profile": [
        "mega-cap", "large-cap", "mid-cap", "small-cap", "micro-cap",
        "mature", "established", "growth-stage", "post-ipo", "pre-profit",
    ],
    "sector": [
        "technology", "healthcare", "financials", "consumer-cyclical",
        "consumer-defensive", "industrials", "energy", "utilities",
        "real-estate", "materials", "communication",
        # Thematic overlays
        "ai", "cloud", "saas", "fintech", "crypto", "ev",
        "e-commerce", "cybersecurity", "biotech", "semiconductor",
    ],
    "risk": [
        "low-risk", "moderate-risk", "elevated-risk", "high-risk",
        "trend-break-active", "crash-prone",
    ],
    "momentum": [
        "bullish", "bearish", "neutral",
        "oversold", "overbought",
        "above-200sma", "below-200sma",
        "mean-reverting",
    ],
    "valuation": [
        "deep-value", "undervalued", "fair-value",
        "overvalued", "speculative-premium",
    ],
}


# ═══════════════════════════════════════════════════════════════
# SECTOR KEYWORD MAPPING
# ═══════════════════════════════════════════════════════════════

# Maps Alpha Vantage sector names to canonical tags
SECTOR_MAP = {
    "TECHNOLOGY": "technology",
    "HEALTH CARE": "healthcare",
    "HEALTHCARE": "healthcare",
    "FINANCIAL SERVICES": "financials",
    "FINANCIALS": "financials",
    "CONSUMER CYCLICAL": "consumer-cyclical",
    "CONSUMER DISCRETIONARY": "consumer-cyclical",
    "CONSUMER DEFENSIVE": "consumer-defensive",
    "CONSUMER STAPLES": "consumer-defensive",
    "INDUSTRIALS": "industrials",
    "ENERGY": "energy",
    "UTILITIES": "utilities",
    "REAL ESTATE": "real-estate",
    "BASIC MATERIALS": "materials",
    "MATERIALS": "materials",
    "COMMUNICATION SERVICES": "communication",
}

# Thematic keywords detected from company description or sector context
THEME_KEYWORDS = {
    "ai": ["artificial intelligence", "machine learning", "neural", "ai platform", "generative ai"],
    "cloud": ["cloud computing", "aws", "azure", "cloud infrastructure", "iaas", "paas"],
    "saas": ["software as a service", "saas", "subscription software"],
    "fintech": ["fintech", "digital payments", "neobank", "digital brokerage", "crypto exchange"],
    "crypto": ["cryptocurrency", "bitcoin", "blockchain", "digital asset", "stablecoin"],
    "ev": ["electric vehicle", "ev charging", "battery technology"],
    "e-commerce": ["e-commerce", "ecommerce", "online retail", "marketplace"],
    "cybersecurity": ["cybersecurity", "cyber security", "network security"],
    "biotech": ["biotech", "biotechnology", "pharmaceutical", "drug development"],
    "semiconductor": ["semiconductor", "chip", "wafer", "fabless"],
}


# ═══════════════════════════════════════════════════════════════
# DIMENSION CLASSIFIERS
# ═══════════════════════════════════════════════════════════════

def classify_profile(bundle: dict) -> list[str]:
    """Classify company by market cap tier + lifecycle stage."""
    tags = []
    co = bundle.get("company_overview", {})

    # Market cap tier
    market_cap = co.get("market_cap", 0)
    if isinstance(market_cap, str):
        try:
            market_cap = float(market_cap)
        except (ValueError, TypeError):
            market_cap = 0

    if market_cap >= 200_000_000_000:
        tags.append("mega-cap")
    elif market_cap >= 10_000_000_000:
        tags.append("large-cap")
    elif market_cap >= 2_000_000_000:
        tags.append("mid-cap")
    elif market_cap >= 300_000_000:
        tags.append("small-cap")
    else:
        tags.append("micro-cap")

    # Lifecycle stage from IPO date
    ipo_date_str = co.get("ipo_date", "")
    years_since_ipo = _years_since(ipo_date_str)

    if years_since_ipo is not None:
        if years_since_ipo < 3:
            tags.append("post-ipo")
        elif years_since_ipo < 8:
            tags.append("growth-stage")
        elif years_since_ipo < 15:
            tags.append("established")
        else:
            tags.append("mature")

    # Pre-profit check: negative net income in latest annual
    income = bundle.get("income_statement", {})
    annual = income.get("annual", []) if isinstance(income, dict) else []
    if annual:
        latest_ni = _safe_float(annual[0].get("netIncome", "0"))
        if latest_ni is not None and latest_ni < 0:
            tags.append("pre-profit")

    return tags


def classify_sector(bundle: dict) -> list[str]:
    """Classify by sector + thematic overlays."""
    tags = []
    co = bundle.get("company_overview", {})

    # Primary sector
    sector_raw = co.get("sector", "").upper().strip()
    mapped = SECTOR_MAP.get(sector_raw)
    if mapped:
        tags.append(mapped)
    elif sector_raw:
        # Normalize unknown sector as-is
        tags.append(sector_raw.lower().replace(" ", "-"))

    # Thematic overlays — search description and sector for keywords
    description = co.get("description", "").lower()
    sector_lower = co.get("sector", "").lower()
    industry = co.get("industry", "").lower()
    search_text = f"{description} {sector_lower} {industry}"

    for theme, keywords in THEME_KEYWORDS.items():
        if any(kw in search_text for kw in keywords):
            if theme not in tags:
                tags.append(theme)

    return tags


def classify_risk(short_term: dict, ccrlo: dict, simulation: dict) -> list[str]:
    """Classify composite risk from all 3 signal outputs."""
    tags = []

    # Core risk level from CCRLO
    risk_level = ccrlo.get("risk_level", "MODERATE")
    risk_map = {
        "LOW": "low-risk",
        "MODERATE": "moderate-risk",
        "ELEVATED": "elevated-risk",
        "HIGH": "high-risk",
        "VERY HIGH": "high-risk",
    }
    tags.append(risk_map.get(risk_level, "moderate-risk"))

    # Trend-break active flag
    if short_term.get("trend_break", {}).get("entry_active", False):
        tags.append("trend-break-active")

    # Crash-prone regime
    crash_prone = simulation.get("regime", {}).get("probabilities", {}).get("crash_prone", 0)
    if crash_prone >= 0.20:
        tags.append("crash-prone")

    return tags


def classify_momentum(bundle: dict, short_term: dict) -> list[str]:
    """Classify momentum direction from technical indicators."""
    tags = []

    price = bundle.get("global_quote", {}).get("price", 0)
    if isinstance(price, str):
        price = _safe_float(price) or 0

    # SMA-200 relationship
    sma_200 = short_term.get("indicators", {}).get("sma_200", 0)
    if sma_200 and price:
        if price > sma_200:
            tags.append("above-200sma")
        else:
            tags.append("below-200sma")

    # SMA slope direction
    slope = short_term.get("indicators", {}).get("sma_200_slope", "")

    # RSI zone
    rsi_data = bundle.get("rsi", [])
    rsi_val = None
    if rsi_data:
        rsi_val = _safe_float(rsi_data[0].get("value", "50"))

    if rsi_val is not None:
        if rsi_val <= 30:
            tags.append("oversold")
        elif rsi_val >= 70:
            tags.append("overbought")

    # Overall momentum direction
    if price > sma_200 and slope == "POSITIVE":
        tags.append("bullish")
    elif price < sma_200 and slope == "NEGATIVE":
        tags.append("bearish")
    else:
        tags.append("neutral")

    # Mean-reversion: oversold + below 200 SMA + negative slope
    if rsi_val is not None and rsi_val <= 35 and price < sma_200:
        tags.append("mean-reverting")

    return tags


def classify_valuation(bundle: dict) -> list[str]:
    """Classify valuation relative to sector norms."""
    tags = []
    co = bundle.get("company_overview", {})

    pe = _safe_float(co.get("pe_ratio"))
    forward_pe = _safe_float(co.get("forward_pe"))
    sector_pe_90th = _safe_float(co.get("sector_pe_90th_percentile", 45))

    if pe is None or pe <= 0:
        # Negative or missing P/E — likely pre-profit
        if forward_pe and forward_pe > 0 and forward_pe > 60:
            tags.append("speculative-premium")
        else:
            tags.append("fair-value")  # Can't determine without P/E
        return tags

    # Valuation tiers relative to sector P/E 90th percentile
    if sector_pe_90th and sector_pe_90th > 0:
        ratio = pe / sector_pe_90th
        if ratio < 0.3:
            tags.append("deep-value")
        elif ratio < 0.55:
            tags.append("undervalued")
        elif ratio <= 0.85:
            tags.append("fair-value")
        elif ratio <= 1.2:
            tags.append("overvalued")
        else:
            tags.append("speculative-premium")
    else:
        # Absolute P/E fallback
        if pe < 10:
            tags.append("deep-value")
        elif pe < 18:
            tags.append("undervalued")
        elif pe <= 30:
            tags.append("fair-value")
        elif pe <= 50:
            tags.append("overvalued")
        else:
            tags.append("speculative-premium")

    return tags


# ═══════════════════════════════════════════════════════════════
# MAIN COMPUTE FUNCTION
# ═══════════════════════════════════════════════════════════════

def compute_tags(bundle: dict, short_term: dict, ccrlo: dict, simulation: dict) -> dict:
    """Compute tags for a ticker from bundle + signal data.

    Returns a TAG_SIGNAL dict conforming to the tag contract.
    """
    ticker = bundle.get("ticker", short_term.get("ticker", "UNKNOWN"))
    as_of = bundle.get("as_of", short_term.get("as_of", ""))

    profile_tags = classify_profile(bundle)
    sector_tags = classify_sector(bundle)
    risk_tags = classify_risk(short_term, ccrlo, simulation)
    momentum_tags = classify_momentum(bundle, short_term)
    valuation_tags = classify_valuation(bundle)

    # Build primary tag: first profile + first momentum + first risk
    primary_parts = []
    if profile_tags:
        primary_parts.append(profile_tags[0])
    if momentum_tags:
        # Use bullish/bearish/neutral, not sma tag
        direction = next((t for t in momentum_tags if t in ("bullish", "bearish", "neutral")), "")
        if direction:
            primary_parts.append(direction)
    if risk_tags:
        primary_parts.append(risk_tags[0])
    primary_tag = "-".join(primary_parts) if primary_parts else "unclassified"

    return {
        "ticker": ticker,
        "as_of": as_of,
        "tags": {
            "profile": profile_tags,
            "sector": sector_tags,
            "risk": risk_tags,
            "momentum": momentum_tags,
            "valuation": valuation_tags,
        },
        "primary_tag": primary_tag,
        "tag_version": "1.0",
    }


def validate_tags(tag_signal: dict) -> list[dict]:
    """Validate a TAG_SIGNAL against the taxonomy contract.

    Returns a list of check results (field, status, reason).
    """
    checks = []

    # Top-level structure
    for field in ("ticker", "as_of", "tags", "primary_tag", "tag_version"):
        if field in tag_signal:
            checks.append({"field": f"tag.{field}", "status": "PASS", "reason": "Present"})
        else:
            checks.append({"field": f"tag.{field}", "status": "FAIL", "reason": "Missing required field"})

    tags = tag_signal.get("tags", {})

    # Each dimension must exist and have >= 1 tag
    for dim in ("profile", "sector", "risk", "momentum", "valuation"):
        dim_tags = tags.get(dim, [])
        if not isinstance(dim_tags, list):
            checks.append({"field": f"tag.{dim}", "status": "FAIL", "reason": "Must be a list"})
            continue
        if len(dim_tags) == 0:
            checks.append({"field": f"tag.{dim}", "status": "FAIL", "reason": "Must have >= 1 tag"})
            continue
        checks.append({"field": f"tag.{dim}", "status": "PASS", "reason": f"{len(dim_tags)} tags"})

        # All tags must be in the valid set for this dimension
        valid = set(VALID_TAGS.get(dim, []))
        for t in dim_tags:
            if t in valid:
                checks.append({"field": f"tag.{dim}.{t}", "status": "PASS", "reason": "Valid tag"})
            else:
                # Sector allows dynamic tags from unknown sectors
                if dim == "sector":
                    checks.append({"field": f"tag.{dim}.{t}", "status": "WARN", "reason": f"Unknown sector tag (dynamic): {t}"})
                else:
                    checks.append({"field": f"tag.{dim}.{t}", "status": "FAIL", "reason": f"Invalid tag for {dim}: {t}"})

    return checks


# ═══════════════════════════════════════════════════════════════
# INDEX MANAGEMENT
# ═══════════════════════════════════════════════════════════════

def update_index(tag_signal: dict):
    """Add/update this ticker's tags in the cross-ticker index."""
    index = {}
    if os.path.exists(INDEX_PATH):
        with open(INDEX_PATH, "r", encoding="utf-8") as f:
            try:
                index = json.load(f)
            except (json.JSONDecodeError, ValueError):
                index = {}

    ticker = tag_signal["ticker"]
    index[ticker] = {
        "tags": tag_signal["tags"],
        "primary_tag": tag_signal["primary_tag"],
        "as_of": tag_signal["as_of"],
        "updated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    }

    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)


def query_index(dimension: str = None, tag: str = None) -> dict:
    """Query the tag index.

    Returns all tickers, optionally filtered by dimension and/or tag.
    """
    if not os.path.exists(INDEX_PATH):
        return {}

    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        index = json.load(f)

    if dimension is None and tag is None:
        return index

    results = {}
    for ticker, entry in index.items():
        tags = entry.get("tags", {})
        if dimension:
            dim_tags = tags.get(dimension, [])
            if tag:
                if tag in dim_tags:
                    results[ticker] = entry
            else:
                if dim_tags:
                    results[ticker] = entry
        elif tag:
            # Search all dimensions for the tag
            for dim_tags in tags.values():
                if tag in dim_tags:
                    results[ticker] = entry
                    break

    return results


# ═══════════════════════════════════════════════════════════════
# UTILITIES
# ═══════════════════════════════════════════════════════════════

def _safe_float(val) -> float | None:
    """Safely convert a value to float."""
    if val is None:
        return None
    try:
        v = float(val)
        return v if v == v else None  # NaN check
    except (ValueError, TypeError):
        return None


def _years_since(date_str: str) -> float | None:
    """Calculate years since a date string (YYYY-MM-DD)."""
    if not date_str:
        return None
    try:
        d = date.fromisoformat(date_str)
        today = date.today()
        return (today - d).days / 365.25
    except (ValueError, TypeError):
        return None


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Compute stock classification tags")
    parser.add_argument("--ticker", required=True, help="Ticker symbol (e.g., AMZN)")
    parser.add_argument("--no-index", action="store_true", help="Skip updating the cross-ticker index")
    parser.add_argument("--query", nargs="?", const="all", help="Query the tag index instead of computing")
    parser.add_argument("--dimension", help="Filter query by dimension")
    parser.add_argument("--tag", help="Filter query by specific tag")
    args = parser.parse_args()

    # Query mode
    if args.query:
        results = query_index(args.dimension, args.tag)
        print(json.dumps(results, indent=2))
        return

    ticker = args.ticker.upper()

    # Load inputs
    bundle_path = os.path.join(DATA_DIR, f"{ticker}_bundle.json")
    st_path = os.path.join(OUTPUT_DIR, f"{ticker}_short_term.json")
    cc_path = os.path.join(OUTPUT_DIR, f"{ticker}_ccrlo.json")
    sim_path = os.path.join(OUTPUT_DIR, f"{ticker}_simulation.json")

    for path, label in [(bundle_path, "bundle"), (st_path, "short_term"),
                         (cc_path, "ccrlo"), (sim_path, "simulation")]:
        if not os.path.exists(path):
            print(f"ERROR: {label} not found: {path}")
            sys.exit(1)

    with open(bundle_path, "r", encoding="utf-8") as f:
        bundle = json.load(f)
    with open(st_path, "r", encoding="utf-8") as f:
        short_term = json.load(f)
    with open(cc_path, "r", encoding="utf-8") as f:
        ccrlo = json.load(f)
    with open(sim_path, "r", encoding="utf-8") as f:
        simulation = json.load(f)

    # Compute
    tag_signal = compute_tags(bundle, short_term, ccrlo, simulation)

    # Validate
    checks = validate_tags(tag_signal)
    fails = [c for c in checks if c["status"] == "FAIL"]

    if fails:
        print(f"TAG VALIDATION FAILED:")
        for c in fails:
            print(f"  {c['field']}: {c['reason']}")
        sys.exit(1)

    # Save output
    output_path = os.path.join(OUTPUT_DIR, f"{ticker}_tags.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(tag_signal, f, indent=2)

    print(f"TAGS COMPUTED: {ticker}")
    for dim, dim_tags in tag_signal["tags"].items():
        print(f"  {dim}: {', '.join(dim_tags)}")
    print(f"  Primary: {tag_signal['primary_tag']}")

    # Update index
    if not args.no_index:
        update_index(tag_signal)
        print(f"  Index updated: {INDEX_PATH}")

    sys.exit(0)


if __name__ == "__main__":
    main()
