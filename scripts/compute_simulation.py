"""
Event Risk Simulation — Regime Detection + Event Scoring + Scenario Weighting

Implements the simulation strategy from .instructions/simulation-strategy.md.
Output conforms to the SIMULATION_SIGNAL contract in .instructions/signal-contracts.md.

Usage:
    python scripts/compute_simulation.py \
        --input data_bundle.json \
        --short-term short_term_signal.json \
        --ccrlo ccrlo_signal.json \
        --output simulation_signal.json
"""

import argparse
import json
import sys
import statistics
from datetime import datetime, timedelta


# ═══════════════════════════════════════════════════════════════════
# REGIME DETECTION
# ═══════════════════════════════════════════════════════════════════

REGIME_SCORING = {
    # (condition_name, check_function) → {calm, trending, stressed, crash_prone}
    # Implemented as functions in detect_regime()
}


def detect_regime(data: dict, fragility_score: int) -> dict:
    """Classify market regime into 4 states with probability weights."""
    # Extract features
    rsi = float(data.get("rsi", [{}])[0].get("value", 50)) if data.get("rsi") else 50
    adx = float(data.get("adx", [{}])[0].get("value", 20)) if data.get("adx") else 20
    price = float(data.get("global_quote", {}).get("price", 0))

    atr_values = data.get("atr_14", [])
    if atr_values:
        atr_today = float(atr_values[0]["value"])
        lookback = min(len(atr_values), 252)
        historical = sorted(float(v["value"]) for v in atr_values[:lookback])
        rank = sum(1 for v in historical if v <= atr_today)
        atr_pctile = (rank / len(historical)) * 100 if historical else 50
        atr_50d_avg = statistics.mean(float(v["value"]) for v in atr_values[:min(50, len(atr_values))])
        atr_ratio = atr_today / atr_50d_avg if atr_50d_avg > 0 else 1.0
    else:
        atr_pctile, atr_ratio = 50, 1.0

    macd_data = data.get("macd", [])
    macd_hist = float(macd_data[0].get("MACD_Hist", 0)) if macd_data else 0

    bbands = data.get("bbands", [])
    if bbands:
        upper = float(bbands[0].get("Real Upper Band", 0))
        lower = float(bbands[0].get("Real Lower Band", 0))
        middle = float(bbands[0].get("Real Middle Band", 1))
        bb_width = ((upper - lower) / middle * 100) if middle > 0 else 5
    else:
        bb_width = 5

    sma_200 = data.get("sma_200", [])
    sma_50 = data.get("sma_50", [])
    price_vs_sma200 = ((price - float(sma_200[0]["value"])) / float(sma_200[0]["value"]) * 100) if sma_200 and price > 0 else 0
    price_vs_sma50 = ((price - float(sma_50[0]["value"])) / float(sma_50[0]["value"]) * 100) if sma_50 and price > 0 else 0
    below_both_smas = price_vs_sma200 < 0 and price_vs_sma50 < 0

    # Volume ratio (G1 fix: from simulation SKILL.md Phase 2)
    gq = data.get("global_quote", {})
    volume_today = float(gq.get("volume", 0)) if gq.get("volume") else 0
    volume_history = gq.get("volume_history", [])
    volume_sma_20 = gq.get("volume_sma_20")
    volume_ratio = None
    if volume_history and len(volume_history) >= 20:
        avg_vol = statistics.mean(float(v) for v in volume_history[:20])
        volume_ratio = volume_today / avg_vol if avg_vol > 0 else None
    elif volume_sma_20 and float(volume_sma_20) > 0:
        volume_ratio = volume_today / float(volume_sma_20)

    # Score each regime
    scores = {"calm": 0, "trending": 0, "stressed": 0, "crash_prone": 0}

    # RSI conditions
    if 40 <= rsi <= 60:
        scores["calm"] += 30
    if rsi < 30:
        scores["stressed"] += 25
        scores["crash_prone"] += 20
    elif rsi > 70:
        scores["stressed"] += 25

    # ADX conditions
    if adx < 20:
        scores["calm"] += 25
    if adx > 25:
        scores["trending"] += 30

    # ATR percentile
    if atr_pctile < 50:
        scores["calm"] += 20
    if atr_pctile > 75:
        scores["stressed"] += 30
    if atr_pctile > 90:
        scores["stressed"] += 30
        scores["crash_prone"] += 25

    # Price vs SMAs
    if below_both_smas:
        scores["crash_prone"] += 25

    # BB width
    if bb_width < 5:
        scores["calm"] += 15
    if bb_width > 8:
        scores["stressed"] += 20

    # Volume ratio (G1: per simulation SKILL.md, normal volume = calm regime signal)
    if volume_ratio is not None:
        if 0.7 <= volume_ratio <= 1.3:
            scores["calm"] += 10

    # Fragility
    if fragility_score >= 3:
        scores["crash_prone"] += 15

    # Normalize to probabilities
    total = sum(scores.values())
    if total == 0:
        probs = {"calm": 0.4, "trending": 0.3, "stressed": 0.2, "crash_prone": 0.1}
    else:
        probs = {k: round(v / total, 3) for k, v in scores.items()}

    # Ensure sum = 1.0
    diff = 1.0 - sum(probs.values())
    dominant = max(probs, key=probs.get)
    probs[dominant] = round(probs[dominant] + diff, 3)

    return {
        "probabilities": probs,
        "dominant": dominant,
        "_raw_scores": scores,
    }


# ═══════════════════════════════════════════════════════════════════
# EVENT PROBABILITY SCORING
# ═══════════════════════════════════════════════════════════════════

BASE_RATES = {
    "large_move":       {"5d": 12, "10d": 18, "20d": 25},
    "vol_spike":        {"5d": 8,  "10d": 15, "20d": 22},
    "trend_reversal":   {"5d": 6,  "10d": 12, "20d": 20},
    "earnings_reaction":{"5d": 5,  "10d": 10, "20d": 20},
    "liquidity_stress": {"5d": 5,  "10d": 8,  "20d": 12},
    "crash_like":       {"5d": 2,  "10d": 4,  "20d": 7},
}

REGIME_MULTIPLIERS = {
    "large_move":       {"calm": 0.8, "trending": 1.0, "stressed": 1.3, "crash_prone": 1.6},
    "vol_spike":        {"calm": 0.7, "trending": 0.9, "stressed": 1.4, "crash_prone": 1.8},
    "trend_reversal":   {"calm": 1.0, "trending": 0.8, "stressed": 1.2, "crash_prone": 1.5},
    "earnings_reaction":{"calm": 0.9, "trending": 1.0, "stressed": 1.3, "crash_prone": 1.5},
    "liquidity_stress": {"calm": 0.6, "trending": 0.8, "stressed": 1.5, "crash_prone": 2.0},
    "crash_like":       {"calm": 0.5, "trending": 0.7, "stressed": 1.5, "crash_prone": 2.5},
}


def compute_feature_adjustments(data: dict, fragility_score: int, ccrlo_score: int) -> dict:
    """Compute feature-based adjustments to base event probabilities."""
    adj = {event: 0 for event in BASE_RATES}

    # ATR percentile adjustments
    atr_values = data.get("atr_14", [])
    if atr_values:
        atr_today = float(atr_values[0]["value"])
        lookback = min(len(atr_values), 252)
        historical = sorted(float(v["value"]) for v in atr_values[:lookback])
        rank = sum(1 for v in historical if v <= atr_today)
        atr_pctile = (rank / len(historical)) * 100 if historical else 50

        if atr_pctile > 80:
            adj["vol_spike"] += 8
            adj["large_move"] += 5
        if atr_pctile > 90:
            adj["crash_like"] += 3

    # RSI extremes
    rsi = float(data.get("rsi", [{}])[0].get("value", 50)) if data.get("rsi") else 50
    if rsi < 30 or rsi > 70:
        adj["trend_reversal"] += 5
        adj["large_move"] += 3

    # Fragility contribution
    if fragility_score >= 3:
        adj["crash_like"] += 5
        adj["liquidity_stress"] += 5
    if fragility_score >= 4:
        adj["crash_like"] += 3

    # CCRLO contribution
    if ccrlo_score >= 12:
        adj["crash_like"] += 5
        adj["large_move"] += 3
    if ccrlo_score >= 16:
        adj["crash_like"] += 3

    # Beta adjustment
    beta = data.get("company_overview", {}).get("beta")
    if beta and float(beta) > 1.5:
        adj["large_move"] += 5
        adj["vol_spike"] += 3

    # G2: Earnings proximity adjustment — if next earnings within 5-10 trading days,
    # elevate earnings_reaction probability (from simulation-strategy.md)
    earnings = data.get("earnings", {}).get("quarterly", [])
    if earnings:
        try:
            # Estimate next earnings from pattern of quarterly dates
            last_date = earnings[0].get("reportedDate") or earnings[0].get("fiscalDateEnding")
            if last_date:
                last_dt = datetime.strptime(str(last_date), "%Y-%m-%d")
                # Approximate next earnings ~90 days after last
                next_est = last_dt + timedelta(days=90)
                days_to_earnings = (next_est - datetime.now()).days
                if 0 <= days_to_earnings <= 5:
                    adj["earnings_reaction"] += 15
                elif 5 < days_to_earnings <= 10:
                    adj["earnings_reaction"] += 10
        except (ValueError, TypeError, KeyError, IndexError):
            pass

    return adj


def score_events(data: dict, regime_probs: dict, fragility_score: int, ccrlo_score: int) -> dict:
    """Score 6 event probabilities at 3 horizons with regime conditioning."""
    feature_adj = compute_feature_adjustments(data, fragility_score, ccrlo_score)
    events = {}

    for event_name, base in BASE_RATES.items():
        event_entry = {}
        multipliers = REGIME_MULTIPLIERS[event_name]

        # Weighted regime multiplier
        regime_mult = sum(
            regime_probs.get(regime, 0) * mult
            for regime, mult in multipliers.items()
        )

        for horizon in ("5d", "10d", "20d"):
            adjusted = base[horizon] + feature_adj.get(event_name, 0)
            final = adjusted * regime_mult

            # Clipping: [1%, 85%], crash capped at 35%
            if event_name == "crash_like":
                final = min(final, 35)
            final = max(1, min(85, final))
            event_entry[horizon] = round(final, 1)

        events[event_name] = event_entry

    return events


def compute_price_impacts(events: dict, price: float, atr: float) -> dict:
    """Compute expected price impact ranges for each event class."""
    impacts = {}
    for event_name in events:
        if event_name == "large_move":
            delta = 2.5 * atr
            impacts[event_name] = f"${price - delta:.0f}–${price + delta:.0f}"
        elif event_name == "vol_spike":
            delta = 1.5 * atr
            impacts[event_name] = f"${price - delta:.0f}–${price + delta:.0f}"
        elif event_name == "trend_reversal":
            delta = 2.0 * atr
            impacts[event_name] = f"${price - delta:.0f}–${price + delta:.0f}"
        elif event_name == "earnings_reaction":
            delta = price * 0.05  # ±5% gap
            impacts[event_name] = f"${price - delta:.0f}–${price + delta:.0f}"
        elif event_name == "liquidity_stress":
            delta = 3.0 * atr
            impacts[event_name] = f"${price - delta:.0f}–${price + delta:.0f}"
        elif event_name == "crash_like":
            impacts[event_name] = f"${price * 0.85:.0f}–${price * 0.95:.0f}"
    return impacts


# ═══════════════════════════════════════════════════════════════════
# SCENARIO WEIGHTING
# ═══════════════════════════════════════════════════════════════════

def compute_scenarios(regime_probs: dict, price: float, atr: float,
                      horizon_days: int = 20, beta: float = 1.0,
                      sma_50: float | None = None) -> dict:
    """Construct 4 forward scenarios with probability weights.

    Price range formulas per simulation-strategy.md Section 12:
      Base Case:     Current ± (ATR_h × 0.10)
      Vol Expansion: (Current - ATR_h×0.55) to (Current + ATR_h×0.22) — downside biased
      Trend Shift:   (Current - ATR_h×0.68) to min(SMA_50, Current + ATR_h×0.65)
      Tail Risk:     (Current × (1 - 0.15×Beta/1.5)) to (Current × 0.97) — Beta-scaled
    """
    calm = regime_probs.get("calm", 0)
    trend = regime_probs.get("trending", 0)
    stress = regime_probs.get("stressed", 0)
    crash = regime_probs.get("crash_prone", 0)

    # Weight formulas from specification
    weights = {
        "base_case": calm + 0.5 * trend,
        "vol_expansion": 0.5 * stress + 0.3 * crash,
        "trend_shift": 0.5 * trend + 0.2 * stress,
        "tail_risk": crash + 0.3 * stress,
    }

    # Normalize to sum to 1.0
    w_total = sum(weights.values())
    if w_total > 0:
        weights = {k: round(v / w_total, 3) for k, v in weights.items()}
    else:
        weights = {"base_case": 0.4, "vol_expansion": 0.2, "trend_shift": 0.25, "tail_risk": 0.15}

    # Fix rounding
    diff = 1.0 - sum(weights.values())
    dominant_scenario = max(weights, key=weights.get)
    weights[dominant_scenario] = round(weights[dominant_scenario] + diff, 3)

    sqrt_h = horizon_days ** 0.5
    atr_h = atr * sqrt_h

    # Clamp beta for tail-risk formula
    eff_beta = max(0.5, min(3.0, beta))

    # Trend shift upside capped at SMA50 if available (G4 fix)
    trend_shift_upside = price + atr_h * 0.65
    if sma_50 is not None and sma_50 > 0:
        trend_shift_upside = min(sma_50, trend_shift_upside)

    scenarios = {
        "base_case": {
            "weight": weights["base_case"],
            "price_range": f"${price - atr_h * 0.10:.0f}–${price + atr_h * 0.10:.0f}",
            "expected_pl": f"+{(atr_h * 0.03 / price * 100):.1f}%",
        },
        "vol_expansion": {
            "weight": weights["vol_expansion"],
            "price_range": f"${price - atr_h * 0.55:.0f}–${price + atr_h * 0.22:.0f}",
            "expected_pl": f"−{(atr_h * 0.17 / price * 100):.1f}%",
        },
        "trend_shift": {
            "weight": weights["trend_shift"],
            "price_range": f"${price - atr_h * 0.68:.0f}–${trend_shift_upside:.0f}",
            "expected_pl": f"±{(atr_h * 0.30 / price * 100):.1f}%",
        },
        "tail_risk": {
            "weight": weights["tail_risk"],
            "price_range": f"${price * (1 - 0.15 * eff_beta / 1.5):.0f}–${price * 0.97:.0f}",
            "expected_pl": f"−{(0.15 * eff_beta / 1.5 * 100):.0f}%",
        },
    }

    return scenarios


# ═══════════════════════════════════════════════════════════════════
# CONFIDENCE ASSESSMENT
# ═══════════════════════════════════════════════════════════════════

def compute_confidence(regime: dict, tb_active: bool, vs_active: bool,
                       fragility_score: int, ccrlo_score: int) -> dict:
    """Check for contradictions between signals → disagreement score → confidence level."""
    disagreements = []

    dominant = regime["dominant"]
    probs = regime["probabilities"]

    # Check: stressed/crash regime but low CCRLO
    if dominant in ("stressed", "crash_prone") and ccrlo_score < 4:
        disagreements.append("Regime stressed but CCRLO low")

    # Check: calm regime but high fragility
    if dominant == "calm" and fragility_score >= 3:
        disagreements.append("Regime calm but fragility high")

    # Check: TB active but calm regime
    if tb_active and dominant == "calm":
        disagreements.append("Trend break active but regime calm")

    # Check: VS active but low ATR percentile (shouldn't happen, internal consistency)
    # Check: CCRLO high but regime calm
    if ccrlo_score >= 12 and probs.get("crash_prone", 0) < 0.15:
        disagreements.append("CCRLO high but crash regime low")

    # Check: no dominant regime (max prob < 0.35)
    max_prob = max(probs.values())
    if max_prob < 0.35:
        disagreements.append("No dominant regime (ambiguous)")

    # Map to score
    n = len(disagreements)
    if n == 0:
        score, level = 0.05, "HIGH"
    elif n == 1:
        score, level = 0.25, "MODERATE-HIGH"
    elif n == 2:
        score, level = 0.45, "MODERATE"
    elif n == 3:
        score, level = 0.65, "LOW-MODERATE"
    else:
        score, level = 0.80, "LOW"

    # Top risk drivers
    drivers = []
    if fragility_score >= 3:
        drivers.append(f"Fragility score {fragility_score}/5")
    if ccrlo_score >= 8:
        drivers.append(f"CCRLO score {ccrlo_score}/21")
    if tb_active:
        drivers.append("Trend break active")
    if dominant in ("stressed", "crash_prone"):
        drivers.append(f"{dominant.replace('_', '-').title()} regime")
    if not drivers:
        drivers.append("No elevated risk drivers")

    return {
        "disagreement": round(score, 2),
        "level": level,
        "top_drivers": drivers[:5],
        "_contradictions": disagreements,
    }


# ═══════════════════════════════════════════════════════════════════
# MAIN COMPUTATION
# ═══════════════════════════════════════════════════════════════════

def compute_simulation_signal(data: dict, short_term: dict, ccrlo: dict) -> dict:
    """Main computation — produces SIMULATION_SIGNAL contract."""
    price = float(data.get("global_quote", {}).get("price", 0))

    atr_values = data.get("atr_14", [])
    atr = float(atr_values[0]["value"]) if atr_values else price * 0.02

    fragility_score = short_term.get("fragility", {}).get("score", 0)
    ccrlo_score = ccrlo.get("composite_score", 0)
    tb_active = short_term.get("trend_break", {}).get("tb", False)
    vs_active = short_term.get("trend_break", {}).get("vs", False)

    # Phase 1: Regime Detection
    regime = detect_regime(data, fragility_score)

    # Phase 2: Event Scoring
    events_raw = score_events(data, regime["probabilities"], fragility_score, ccrlo_score)
    price_impacts = compute_price_impacts(events_raw, price, atr)

    events = {}
    for event_name, horizons in events_raw.items():
        events[event_name] = {
            **horizons,
            "price_impact": price_impacts.get(event_name, "N/A"),
        }

    # Phase 3: Scenario Weighting (pass beta + SMA50 for spec-aligned formulas)
    beta_val = float(data.get("company_overview", {}).get("beta", 1.0) or 1.0)
    sma_50_data = data.get("sma_50", [])
    sma_50_val = float(sma_50_data[0]["value"]) if sma_50_data else None
    scenarios = compute_scenarios(regime["probabilities"], price, atr,
                                  beta=beta_val, sma_50=sma_50_val)

    # Phase 4: Weighted Expected Price
    weighted_price = 0
    for scenario_name, scenario in scenarios.items():
        # Parse midpoint from price range
        try:
            parts = scenario["price_range"].replace("$", "").replace(",", "").split("–")
            low, high = float(parts[0]), float(parts[1])
            midpoint = (low + high) / 2
        except (ValueError, IndexError):
            midpoint = price
        weighted_price += scenario["weight"] * midpoint

    sqrt_20 = 20 ** 0.5
    ci_80_low = weighted_price - 1.28 * atr * sqrt_20
    ci_80_high = weighted_price + 1.28 * atr * sqrt_20
    change_pct = ((weighted_price - price) / price) * 100

    # Downside skew: probability that 20d return < 0
    # Per simulation-strategy.md: (vol_weight × 0.7) + tail_weight + (trend_weight × 0.5)
    # clipped to [20%, 85%]
    vol_w = scenarios["vol_expansion"]["weight"]
    tail_w = scenarios["tail_risk"]["weight"]
    trend_w = scenarios["trend_shift"]["weight"]
    downside_skew = min(85, max(20, (vol_w * 0.7 + tail_w + trend_w * 0.5) * 100))

    # Phase 5: Confidence
    confidence = compute_confidence(regime, tb_active, vs_active, fragility_score, ccrlo_score)

    # Composite event risk: average of top-3 20d event probabilities
    top_3_20d = sorted([e["20d"] for e in events.values()], reverse=True)[:3]
    composite_event_risk = round(statistics.mean(top_3_20d), 1)

    if composite_event_risk < 15:
        risk_color = "GREEN"
    elif composite_event_risk <= 30:
        risk_color = "AMBER"
    else:
        risk_color = "RED"

    signal = {
        "ticker": data.get("ticker", "UNKNOWN"),
        "as_of": data.get("as_of", datetime.now().strftime("%Y-%m-%d")),
        "price": price,
        "regime": {
            "probabilities": regime["probabilities"],
            "dominant": regime["dominant"],
        },
        "events": events,
        "scenarios": scenarios,
        "weighted_expected": {
            "price": round(weighted_price, 2),
            "change_pct": f"{change_pct:+.1f}%",
            "ci_80_low": round(ci_80_low, 2),
            "ci_80_high": round(ci_80_high, 2),
            "downside_skew": round(downside_skew, 1),
        },
        "confidence": confidence,
        "composite_event_risk": composite_event_risk,
        "risk_color": risk_color,
    }

    return signal


def main():
    parser = argparse.ArgumentParser(description="Compute SIMULATION_SIGNAL from data bundle + prior signals")
    parser.add_argument("--input", required=True, help="Path to data bundle JSON")
    parser.add_argument("--short-term", required=True, help="Path to SHORT_TERM_SIGNAL JSON")
    parser.add_argument("--ccrlo", required=True, help="Path to CCRLO_SIGNAL JSON")
    parser.add_argument("--output", required=True, help="Path to write signal JSON")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)
    with open(getattr(args, "short_term"), "r", encoding="utf-8") as f:
        short_term = json.load(f)
    with open(args.ccrlo, "r", encoding="utf-8") as f:
        ccrlo = json.load(f)

    signal = compute_simulation_signal(data, short_term, ccrlo)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(signal, f, indent=2)

    print(f"SIMULATION_SIGNAL computed for {signal['ticker']}")
    print(f"  Dominant Regime: {signal['regime']['dominant']}")
    print(f"  Composite Event Risk: {signal['composite_event_risk']}% ({signal['risk_color']})")
    print(f"  Weighted Expected Price: ${signal['weighted_expected']['price']:.2f}")
    print(f"  Confidence: {signal['confidence']['level']}")
    sys.exit(0)


if __name__ == "__main__":
    main()
