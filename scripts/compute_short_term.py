"""
Short-Term Signal Computation — TB/VS/VF + Fragility Stack

Implements the Trend-Break Risk-Off strategy from .instructions/short-term-strategy.md.
Output conforms to the SHORT_TERM_SIGNAL contract in .instructions/signal-contracts.md.

Usage:
    python scripts/compute_short_term.py --input data_bundle.json --output short_term_signal.json
"""

import argparse
import json
import sys
import statistics
from datetime import datetime


def compute_tb(price: float, sma_200_values: list[dict]) -> dict:
    """Gate 1: Trend Break — Price below declining 200-MA."""
    if len(sma_200_values) < 21:
        return {"tb": False, "sma_200": None, "sma_200_slope": "INSUFFICIENT_DATA"}

    sma_200_today = float(sma_200_values[0]["value"])
    sma_200_20d_ago = float(sma_200_values[20]["value"])
    slope = sma_200_today - sma_200_20d_ago

    # TB = (Price <= 0.995 × SMA_200) AND (slope < 0)
    below_ma = price <= 0.995 * sma_200_today
    declining = slope < 0

    return {
        "tb": below_ma and declining,
        "sma_200": round(sma_200_today, 2),
        "sma_200_slope": "NEGATIVE" if declining else "POSITIVE",
        "_details": {
            "price_vs_buffered_ma": round(price / (0.995 * sma_200_today), 4),
            "slope_value": round(slope, 4),
        },
    }


def compute_vs(atr_values: list[dict]) -> dict:
    """Gate 2: Volatility Shift — ATR above 80th percentile of last 252 days."""
    if len(atr_values) < 252:
        lookback = len(atr_values)
    else:
        lookback = 252

    if lookback < 20:
        return {"vs": False, "atr_14": None, "atr_percentile": None}

    atr_today = float(atr_values[0]["value"])
    historical = sorted(float(v["value"]) for v in atr_values[:lookback])
    rank = sum(1 for v in historical if v <= atr_today)
    percentile = (rank / len(historical)) * 100

    return {
        "vs": percentile >= 80.0,
        "atr_14": round(atr_today, 4),
        "atr_percentile": round(percentile, 1),
    }


def compute_vf(volume_today: float, sma_50_values: list[dict], global_quote: dict) -> dict:
    """Gate 3: Volume Filter — Volume >= 1.0 × 20-day average volume.

    Per research spec: VF_t = 1{Vol_t >= m * SMA(Vol, N_v)} where m=1.0, N_v=20.
    Uses volume_history from bundle if available, then volume_sma_20, then defaults
    to INDETERMINATE (vf=False) rather than silently passing.
    """
    vol_today = volume_today

    if vol_today is None or vol_today <= 0:
        return {"vf": False, "volume_ratio": None, "_note": "No volume data"}

    # Priority 1: Compute from volume_history array if provided in the bundle
    volume_history = global_quote.get("volume_history", [])
    if isinstance(volume_history, list) and len(volume_history) >= 20:
        avg_volume = statistics.mean(float(v) for v in volume_history[:20])
        if avg_volume > 0:
            ratio = vol_today / avg_volume
            return {"vf": ratio >= 1.0, "volume_ratio": round(ratio, 2)}

    # Priority 2: Use pre-computed volume_sma_20 if provided
    avg_volume = global_quote.get("volume_sma_20")
    if avg_volume is not None and float(avg_volume) > 0:
        ratio = vol_today / float(avg_volume)
        return {"vf": ratio >= 1.0, "volume_ratio": round(ratio, 2)}

    # Priority 3: No volume average available — default to False (conservative)
    # This avoids silently bypassing the volume gate
    return {"vf": False, "volume_ratio": None, "_note": "volume_sma_20 not provided; defaulted to False (conservative)"}


def compute_fragility(data: dict) -> dict:
    """Fragility Stack — 5 dimensions, each scored 0 (LOW) or 1 (HIGH), total 0-5."""
    dimensions = {}

    # 1. Leverage: HIGH if D/E > 2.0 or negative FCF
    de_ratio = data.get("company_overview", {}).get("debt_to_equity")
    fcf = data.get("cash_flow", {}).get("free_cash_flow")
    if de_ratio is not None and fcf is not None:
        dimensions["leverage"] = "HIGH" if (float(de_ratio) > 2.0 or float(fcf) < 0) else "LOW"
    elif de_ratio is not None:
        dimensions["leverage"] = "HIGH" if float(de_ratio) > 2.0 else "LOW"
    else:
        dimensions["leverage"] = "LOW"

    # 2. Liquidity: HIGH if ATR > 2× its 50-day average
    atr_values = data.get("atr_14", [])
    if len(atr_values) >= 50:
        atr_today = float(atr_values[0]["value"])
        atr_50d_avg = statistics.mean(float(v["value"]) for v in atr_values[:50])
        dimensions["liquidity"] = "HIGH" if atr_today > 2 * atr_50d_avg else "LOW"
    else:
        dimensions["liquidity"] = "LOW"

    # 3. Info Risk: HIGH if ≥2 consecutive earnings misses
    earnings = data.get("earnings", {}).get("quarterly", [])
    if len(earnings) >= 2:
        consecutive_misses = 0
        for q in earnings:
            surprise_pct = q.get("surprise_percentage")
            if surprise_pct is not None and float(surprise_pct) < 0:
                consecutive_misses += 1
            else:
                break
        dimensions["info_risk"] = "HIGH" if consecutive_misses >= 2 else "LOW"
    else:
        dimensions["info_risk"] = "LOW"

    # 4. Valuation: HIGH if P/E > 90th percentile of sector
    # Use trailing P/E first; fall back to forward P/E if trailing is null/negative
    pe_ratio = data.get("company_overview", {}).get("pe_ratio")
    forward_pe = data.get("company_overview", {}).get("forward_pe")
    sector_pe_90th = data.get("company_overview", {}).get("sector_pe_90th_percentile")

    # Resolve effective P/E: trailing → forward → None
    effective_pe = None
    if pe_ratio is not None and str(pe_ratio) not in ("None", "-", "", "0"):
        try:
            v = float(pe_ratio)
            if v > 0:
                effective_pe = v
        except (ValueError, TypeError):
            pass
    if effective_pe is None and forward_pe is not None and str(forward_pe) not in ("None", "-", "", "0"):
        try:
            v = float(forward_pe)
            if v > 0:
                effective_pe = v
        except (ValueError, TypeError):
            pass

    if effective_pe is not None and sector_pe_90th is not None:
        dimensions["valuation"] = "HIGH" if effective_pe > float(sector_pe_90th) else "LOW"
    elif effective_pe is not None:
        # Without sector benchmark, use absolute threshold (P/E > 50 as proxy for 90th pctile)
        dimensions["valuation"] = "HIGH" if effective_pe > 50 else "LOW"
    else:
        dimensions["valuation"] = "LOW"

    # 5. Momentum: HIGH if price below BOTH 50-MA and 200-MA
    price = data.get("global_quote", {}).get("price")
    sma_50 = data.get("sma_50", [])
    sma_200 = data.get("sma_200", [])
    if price and sma_50 and sma_200:
        p = float(price)
        s50 = float(sma_50[0]["value"])
        s200 = float(sma_200[0]["value"])
        dimensions["momentum"] = "HIGH" if (p < s50 and p < s200) else "LOW"
    else:
        dimensions["momentum"] = "LOW"

    score = sum(1 for v in dimensions.values() if v == "HIGH")
    if score <= 1:
        level = "LOW"
    elif score <= 3:
        level = "MODERATE"
    else:
        level = "HIGH"

    return {"score": score, "level": level, "dimensions": dimensions}


def compute_correction_probabilities(fragility_score: int, beta: float | None,
                                     ipo_years: float | None,
                                     short_interest_pct: float | None = None) -> dict:
    """Calibrate correction probabilities using fragility score + beta + IPO recency + short interest.

    Research spec adjustments (from short-term-strategy.md):
      - Fragility 0-1: mild -5, std -10, severe -10, bs -5
      - Fragility 2-3: no adjustment
      - Fragility 4-5: mild +5, std +10, severe +15, bs +10
      - Beta > 1.5: +5-10% across all tiers
      - Recent IPO (<2yr): +10% to Severe/Black Swan
      - High short interest (>20%): +5% to Standard/Severe
    """
    # Base probabilities (midpoints of research ranges)
    base = {"mild": 90, "standard": 62, "severe": 32, "black_swan": 11}

    # Fragility adjustment
    if fragility_score <= 1:
        adj = {"mild": -5, "standard": -10, "severe": -10, "black_swan": -5}
    elif fragility_score <= 3:
        adj = {"mild": 0, "standard": 0, "severe": 0, "black_swan": 0}
    else:
        adj = {"mild": 5, "standard": 10, "severe": 15, "black_swan": 10}

    probs = {k: base[k] + adj[k] for k in base}

    # Beta > 1.5: +5-10% across all tiers (use midpoint 7)
    if beta is not None and float(beta) > 1.5:
        beta_adj = 7
        probs = {k: v + beta_adj for k, v in probs.items()}

    # Recent IPO (<2 years): +10% to Severe/Black Swan
    if ipo_years is not None and ipo_years < 2:
        probs["severe"] += 10
        probs["black_swan"] += 10

    # High short interest (>20%): +5% to Standard/Severe (from research spec)
    if short_interest_pct is not None and short_interest_pct > 20:
        probs["standard"] += 5
        probs["severe"] += 5

    # Clamp to reasonable ranges
    for k in probs:
        probs[k] = max(1, min(99, probs[k]))

    return probs


def compute_short_term_signal(data: dict) -> dict:
    """Main computation — produces SHORT_TERM_SIGNAL contract."""
    gq = data.get("global_quote", {})
    price = float(gq.get("price", 0))
    volume = float(gq.get("volume", 0))

    # Compute three gates
    tb_result = compute_tb(price, data.get("sma_200", []))
    vs_result = compute_vs(data.get("atr_14", []))
    vf_result = compute_vf(volume, data.get("sma_50", []), gq)

    entry_active = tb_result["tb"] and vs_result["vs"] and vf_result["vf"]

    # Compute fragility
    fragility = compute_fragility(data)

    # Compute correction probabilities
    beta = data.get("company_overview", {}).get("beta")
    ipo_date = data.get("company_overview", {}).get("ipo_date")
    ipo_years = None
    if ipo_date:
        try:
            ipo_dt = datetime.strptime(str(ipo_date), "%Y-%m-%d")
            ipo_years = (datetime.now() - ipo_dt).days / 365.25
        except (ValueError, TypeError):
            pass

    # Short interest from institutional data (research spec: +5% to Standard/Severe if >20%)
    short_interest_pct = data.get("company_overview", {}).get("short_percent_float")

    correction_probs = compute_correction_probabilities(
        fragility["score"],
        float(beta) if beta else None,
        ipo_years,
        float(short_interest_pct) if short_interest_pct else None,
    )

    signal = {
        "ticker": data.get("ticker", "UNKNOWN"),
        "as_of": data.get("as_of", datetime.now().strftime("%Y-%m-%d")),
        "price": price,
        "trend_break": {
            "tb": tb_result["tb"],
            "vs": vs_result["vs"],
            "vf": vf_result["vf"],
            "entry_active": entry_active,
        },
        "indicators": {
            "sma_200": tb_result["sma_200"],
            "sma_200_slope": tb_result["sma_200_slope"],
            "atr_14": vs_result["atr_14"],
            "atr_percentile": vs_result["atr_percentile"],
            "volume_ratio": vf_result.get("volume_ratio"),
        },
        "fragility": fragility,
        "correction_probabilities": correction_probs,
    }

    return signal


def main():
    parser = argparse.ArgumentParser(description="Compute SHORT_TERM_SIGNAL from data bundle")
    parser.add_argument("--input", required=True, help="Path to data bundle JSON")
    parser.add_argument("--output", required=True, help="Path to write signal JSON")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    signal = compute_short_term_signal(data)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(signal, f, indent=2)

    print(f"SHORT_TERM_SIGNAL computed for {signal['ticker']}")
    print(f"  TB={signal['trend_break']['tb']} VS={signal['trend_break']['vs']} VF={signal['trend_break']['vf']}")
    print(f"  Entry Active: {signal['trend_break']['entry_active']}")
    print(f"  Fragility: {signal['fragility']['score']}/5 ({signal['fragility']['level']})")
    sys.exit(0)


if __name__ == "__main__":
    main()
