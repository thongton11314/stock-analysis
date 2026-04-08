"""
CCRLO Signal Computation — Composite Correction Risk Logit Overlay

Implements the CCRLO scoring from .instructions/long-term-strategy.md.
Output conforms to the CCRLO_SIGNAL contract in .instructions/signal-contracts.md.

Usage:
    python scripts/compute_ccrlo.py --input data_bundle.json --output ccrlo_signal.json
"""

import argparse
import json
import sys
import statistics
from datetime import datetime


def score_term_spread(data: dict) -> dict:
    """Feature 1: Term Spread — Fed rate trajectory (cutting vs hiking)."""
    fed_rates = data.get("federal_funds_rate", [])
    if len(fed_rates) < 2:
        return {"value": "Insufficient data", "score": 1}

    current = float(fed_rates[0].get("value", 0))

    # Find rate ~6 months ago
    rate_6m_ago = None
    for entry in fed_rates:
        try:
            entry_date = datetime.strptime(entry["date"], "%Y-%m-%d")
            days_ago = (datetime.now() - entry_date).days
            if days_ago >= 150:
                rate_6m_ago = float(entry["value"])
                break
        except (ValueError, KeyError):
            continue

    if rate_6m_ago is None:
        rate_6m_ago = float(fed_rates[-1].get("value", current))

    spread = rate_6m_ago - current  # Positive = cutting, Negative = hiking

    if spread > 0.50:
        score, desc = 0, f"Cutting {int(spread*100)}bps (easing)"
    elif spread > 0:
        score, desc = 1, f"Mild cutting {int(spread*100)}bps"
    elif spread > -0.25:
        score, desc = 2, f"Flat to mild hiking {int(abs(spread)*100)}bps"
    else:
        score, desc = 3, f"Hiking {int(abs(spread)*100)}bps (tightening)"

    return {"value": desc, "score": score}


def score_credit_risk(data: dict) -> dict:
    """Feature 2: Credit Risk — D/E ratio as proxy for credit stress."""
    de = data.get("company_overview", {}).get("debt_to_equity")
    if de is None or str(de) in ("None", "-", ""):
        return {"value": "N/A", "score": 1}

    de_val = float(de)
    if de_val < 0.5:
        score, desc = 0, f"Low leverage (D/E={de_val:.2f})"
    elif de_val < 1.0:
        score, desc = 1, f"Moderate leverage (D/E={de_val:.2f})"
    elif de_val < 2.0:
        score, desc = 2, f"Elevated leverage (D/E={de_val:.2f})"
    else:
        score, desc = 3, f"High leverage (D/E={de_val:.2f})"

    return {"value": desc, "score": score}


def score_ig_credit(data: dict) -> dict:
    """Feature 3: IG Credit Proxy — Fed Rate absolute level."""
    fed_rates = data.get("federal_funds_rate", [])
    if not fed_rates:
        return {"value": "N/A", "score": 1}

    rate = float(fed_rates[0].get("value", 0))
    if rate < 2.0:
        score, desc = 0, f"Low rates ({rate:.2f}%)"
    elif rate < 3.5:
        score, desc = 1, f"Moderate rates ({rate:.2f}%)"
    elif rate < 5.0:
        score, desc = 2, f"Elevated rates ({rate:.2f}%)"
    else:
        score, desc = 3, f"High rates ({rate:.2f}%)"

    return {"value": desc, "score": score}


def score_volatility_regime(data: dict) -> dict:
    """Feature 4: Volatility Regime — ATR percentile vs 1-year history."""
    atr_values = data.get("atr_14", [])
    if len(atr_values) < 50:
        return {"value": "Insufficient ATR data", "score": 1}

    lookback = min(len(atr_values), 252)
    atr_today = float(atr_values[0]["value"])
    historical = sorted(float(v["value"]) for v in atr_values[:lookback])
    rank = sum(1 for v in historical if v <= atr_today)
    percentile = (rank / len(historical)) * 100

    if percentile < 25:
        score, desc = 0, f"Low vol regime ({percentile:.0f}th pctile)"
    elif percentile < 50:
        score, desc = 1, f"Normal vol ({percentile:.0f}th pctile)"
    elif percentile < 75:
        score, desc = 2, f"Elevated vol ({percentile:.0f}th pctile)"
    else:
        score, desc = 3, f"High vol regime ({percentile:.0f}th pctile)"

    return {"value": desc, "score": score}


def score_financial_conditions(data: dict) -> dict:
    """Feature 5: Financial Conditions — Composite of rate + unemployment + GDP."""
    score_total = 0
    components = []

    # Rate direction (from feature 1 logic)
    fed_rates = data.get("federal_funds_rate", [])
    if fed_rates:
        rate = float(fed_rates[0].get("value", 0))
        if rate >= 4.5:
            score_total += 1
            components.append("tight rates")

    # Unemployment trend
    unemployment = data.get("unemployment", [])
    if len(unemployment) >= 2:
        ue_current = float(unemployment[0].get("value", 0))
        ue_prev = float(unemployment[1].get("value", 0))
        if ue_current > ue_prev + 0.2:
            score_total += 1
            components.append("rising UE")
        elif ue_current > 5.0:
            score_total += 1
            components.append(f"high UE ({ue_current}%)")

    # GDP momentum
    gdp = data.get("real_gdp", [])
    if gdp:
        gdp_val = float(gdp[0].get("value", 0))
        if gdp_val < 1.0:
            score_total += 1
            components.append(f"weak GDP ({gdp_val}%)")

    score = min(score_total, 3)
    desc = "; ".join(components) if components else "Normal conditions"
    return {"value": desc, "score": score}


def score_momentum_12m(data: dict) -> dict:
    """Feature 6: Momentum (12M) — Price vs 52W High position."""
    overview = data.get("company_overview", {})
    price = float(data.get("global_quote", {}).get("price", 0))
    high_52w = overview.get("52_week_high")

    if not high_52w or price <= 0:
        return {"value": "N/A", "score": 1}

    high_val = float(high_52w)
    drawdown_pct = ((high_val - price) / high_val) * 100

    if drawdown_pct < 5:
        score, desc = 0, f"Near 52W high (−{drawdown_pct:.1f}%)"
    elif drawdown_pct < 15:
        score, desc = 1, f"Moderate pullback (−{drawdown_pct:.1f}%)"
    elif drawdown_pct < 30:
        score, desc = 2, f"Significant decline (−{drawdown_pct:.1f}%)"
    else:
        score, desc = 3, f"Deep drawdown (−{drawdown_pct:.1f}%)"

    return {"value": desc, "score": score}


def score_realized_vol(data: dict) -> dict:
    """Feature 7: Realized Volatility — ATR/Price annualized."""
    atr_values = data.get("atr_14", [])
    price = float(data.get("global_quote", {}).get("price", 0))

    if not atr_values or price <= 0:
        return {"value": "N/A", "score": 1}

    atr = float(atr_values[0]["value"])
    daily_vol = atr / price
    annual_vol = daily_vol * (252 ** 0.5) * 100  # Annualized %

    if annual_vol < 20:
        score, desc = 0, f"Low realized vol ({annual_vol:.1f}% ann.)"
    elif annual_vol < 35:
        score, desc = 1, f"Normal realized vol ({annual_vol:.1f}% ann.)"
    elif annual_vol < 50:
        score, desc = 2, f"Elevated realized vol ({annual_vol:.1f}% ann.)"
    else:
        score, desc = 3, f"High realized vol ({annual_vol:.1f}% ann.)"

    return {"value": desc, "score": score}


def map_score_to_probability(score: int) -> tuple[float, str]:
    """Map composite score (0-21) to correction probability and risk level."""
    if score <= 3:
        return 7.5, "LOW"
    elif score <= 7:
        return 20.0, "MODERATE"
    elif score <= 11:
        return 37.5, "ELEVATED"
    elif score <= 15:
        return 57.5, "HIGH"
    else:
        return 77.5, "VERY HIGH"


def compute_ccrlo_signal(data: dict) -> dict:
    """Main computation — produces CCRLO_SIGNAL contract."""
    features = {
        "term_spread": score_term_spread(data),
        "credit_risk": score_credit_risk(data),
        "ig_credit": score_ig_credit(data),
        "volatility_regime": score_volatility_regime(data),
        "financial_conditions": score_financial_conditions(data),
        "momentum_12m": score_momentum_12m(data),
        "realized_vol": score_realized_vol(data),
    }

    composite_score = sum(f["score"] for f in features.values())
    probability, risk_level = map_score_to_probability(composite_score)

    # Decision framework text
    decisions = {
        "LOW": "Full equity exposure; monitor monthly",
        "MODERATE": "Monitor weekly; prepare hedge instruments",
        "ELEVATED": "Reduce to 80% equity; buy protective puts",
        "HIGH": "Reduce to 50% equity; active hedging",
        "VERY HIGH": "Reduce to 20% equity; maximum defensive posture",
    }

    signal = {
        "ticker": data.get("ticker", "UNKNOWN"),
        "as_of": data.get("as_of", datetime.now().strftime("%Y-%m-%d")),
        "horizon": "6 months (126 trading days)",
        "features": features,
        "composite_score": composite_score,
        "correction_probability": probability,
        "risk_level": risk_level,
        "decision": decisions.get(risk_level, "Monitor"),
    }

    return signal


def main():
    parser = argparse.ArgumentParser(description="Compute CCRLO_SIGNAL from data bundle")
    parser.add_argument("--input", required=True, help="Path to data bundle JSON")
    parser.add_argument("--output", required=True, help="Path to write signal JSON")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    signal = compute_ccrlo_signal(data)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(signal, f, indent=2)

    print(f"CCRLO_SIGNAL computed for {signal['ticker']}")
    print(f"  Composite Score: {signal['composite_score']}/21")
    print(f"  Correction Probability: {signal['correction_probability']}%")
    print(f"  Risk Level: {signal['risk_level']}")
    for name, feat in signal["features"].items():
        print(f"    {name}: {feat['score']}/3 — {feat['value']}")
    sys.exit(0)


if __name__ == "__main__":
    main()
