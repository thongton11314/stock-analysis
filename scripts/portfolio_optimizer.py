#!/usr/bin/env python3
"""
portfolio_optimizer.py — Evidence-based portfolio construction engine.

Implements the portfolio construction methodology from the research document:
- Risk-band-aware weight optimization (min-variance, risk-parity, signal-weighted)
- Portfolio risk metrics (expected shortfall proxy, concentration, diversification)
- Rebalancing signals (drift detection, risk limit breach)
- Regime-aware risk controls (de-risking rules from CCRLO/regime data)
- Strategy recommendation (maps portfolio state to research frameworks)

Uses existing per-ticker signals as inputs — NOT historical return optimization.
The system's computed signals (Beta, ATR, Fragility, CCRLO, Regime, Simulation)
serve as proxy inputs where traditional covariance/return data would be used.

Usage:
    python scripts/portfolio_optimizer.py                          # Default: all tickers, growth band
    python scripts/portfolio_optimizer.py --risk-band aggressive
    python scripts/portfolio_optimizer.py --config portfolio-manager/portfolio_config.json
"""

import argparse
import json
import math
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = SCRIPT_DIR / "output"
DATA_DIR = SCRIPT_DIR / "data"
TAGS_INDEX_PATH = OUTPUT_DIR / "tags_index.json"

# ─── Risk Band Thresholds (from research §6) ───
RISK_BAND_CONFIG = {
    "conservative": {
        "objective": "capital_preservation",
        "method": "inverse_volatility",
        "max_single_weight": 0.25,
        "min_single_weight": 0.02,
        "max_sector_weight": 0.40,
        "fragility_penalty": 0.15,    # reduce weight by 15% per fragility point
        "ccrlo_threshold": 30.0,      # flag if avg CCRLO > this
        "regime_derisking": True,
        "es_limit": 0.08,             # max 8% expected shortfall
        "rebalance_drift_pct": 3.0,   # rebalance if drift > 3%
    },
    "moderate": {
        "objective": "balanced_growth",
        "method": "risk_parity",
        "max_single_weight": 0.30,
        "min_single_weight": 0.02,
        "max_sector_weight": 0.50,
        "fragility_penalty": 0.10,
        "ccrlo_threshold": 40.0,
        "regime_derisking": True,
        "es_limit": 0.12,
        "rebalance_drift_pct": 5.0,
    },
    "growth": {
        "objective": "higher_return_controlled_drawdown",
        "method": "signal_weighted",
        "max_single_weight": 0.35,
        "min_single_weight": 0.02,
        "max_sector_weight": 0.60,
        "fragility_penalty": 0.08,
        "ccrlo_threshold": 50.0,
        "regime_derisking": True,
        "es_limit": 0.18,
        "rebalance_drift_pct": 7.0,
    },
    "aggressive": {
        "objective": "max_return_with_survivability",
        "method": "signal_weighted",
        "max_single_weight": 0.40,
        "min_single_weight": 0.02,
        "max_sector_weight": 0.70,
        "fragility_penalty": 0.05,
        "ccrlo_threshold": 60.0,
        "regime_derisking": True,
        "es_limit": 0.25,
        "rebalance_drift_pct": 10.0,
    },
}


def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def load_ticker_signals(ticker):
    """Load all signal data for a single ticker."""
    bundle = load_json(DATA_DIR / ("%s_bundle.json" % ticker))
    short_term = load_json(OUTPUT_DIR / ("%s_short_term.json" % ticker))
    ccrlo = load_json(OUTPUT_DIR / ("%s_ccrlo.json" % ticker))
    simulation = load_json(OUTPUT_DIR / ("%s_simulation.json" % ticker))
    tags = load_json(OUTPUT_DIR / ("%s_tags.json" % ticker))

    if not all([bundle, short_term, ccrlo, simulation]):
        return None

    co = bundle.get("company_overview", {})
    gq = bundle.get("global_quote", {})
    we = simulation.get("weighted_expected", {})

    return {
        "ticker": ticker,
        "price": float(gq.get("price", 0)),
        "beta": float(co.get("beta", 1.0)),
        "atr": float(short_term.get("indicators", {}).get("atr_14", 0)),
        "atr_pct": float(short_term.get("indicators", {}).get("atr_14", 0)) / max(float(gq.get("price", 1)), 0.01) * 100,
        "fragility_score": int(short_term.get("fragility", {}).get("score", 0)),
        "fragility_level": short_term.get("fragility", {}).get("level", "LOW"),
        "fragility_dims": short_term.get("fragility", {}).get("dimensions", {}),
        "ccrlo_score": int(ccrlo.get("composite_score", 0)),
        "ccrlo_prob": float(ccrlo.get("correction_probability", 0)),
        "ccrlo_level": ccrlo.get("risk_level", "LOW"),
        "regime": simulation.get("regime", {}).get("dominant", "calm"),
        "regime_probs": simulation.get("regime", {}).get("probabilities", {}),
        "tail_risk_weight": float(simulation.get("scenarios", {}).get("tail_risk", {}).get("weight", 0)),
        "downside_skew": float(we.get("downside_skew", 0)),
        "expected_change_pct": float(we.get("change_pct", "0").replace("%", "").replace("\u2212", "-")),
        "ci_80_low": float(we.get("ci_80_low", 0)),
        "ci_80_high": float(we.get("ci_80_high", 0)),
        "tb_active": short_term.get("trend_break", {}).get("entry_active", False),
        "correction_probs": short_term.get("correction_probabilities", {}),
        "sector": tags.get("tags", {}).get("sector", ["unknown"])[0] if tags else "unknown",
        "risk_tags": tags.get("tags", {}).get("risk", []) if tags else [],
        "momentum_tags": tags.get("tags", {}).get("momentum", []) if tags else [],
        "market_cap": float(co.get("market_cap", 0)),
    }


# ═══════════════════════════════════════════════════════════
#  WEIGHT OPTIMIZATION — §7 Logic Steps 1-6
# ═══════════════════════════════════════════════════════════

def compute_inverse_volatility_weights(holdings):
    """
    Conservative method: weight inversely proportional to realized volatility.
    Uses ATR% as volatility proxy (from research §6.1: min-variance base).
    Lower vol → higher weight.
    """
    inv_vols = []
    for h in holdings:
        vol = max(h["atr_pct"], 0.5)  # floor at 0.5%
        inv_vols.append(1.0 / vol)
    total = sum(inv_vols)
    return {h["ticker"]: iv / total for h, iv in zip(holdings, inv_vols)}


def compute_risk_parity_weights(holdings):
    """
    Moderate method: equalize risk contributions.
    Uses Beta * ATR% as risk proxy (from research §6.2: risk budgeting).
    Risk contribution ∝ weight × risk_proxy.
    We solve for weights where each asset's risk contribution is equal.
    """
    risk_proxies = []
    for h in holdings:
        # Combined risk = beta × atr_pct (systematic × idiosyncratic)
        risk = max(h["beta"], 0.3) * max(h["atr_pct"], 0.5)
        risk_proxies.append(risk)

    # Risk parity: w_i ∝ 1/risk_i (simplified analytical solution)
    inv_risks = [1.0 / r for r in risk_proxies]
    total = sum(inv_risks)
    return {h["ticker"]: ir / total for h, ir in zip(holdings, inv_risks)}


def compute_signal_weighted(holdings):
    """
    Growth/Aggressive method: weight by composite signal quality.
    Uses research §6.3-6.4: signal-driven with risk overlay.

    Score = f(low_fragility, low_ccrlo, favorable_regime, low_tail_risk, low_beta)
    Higher score → higher weight.
    """
    scores = []
    for h in holdings:
        score = 10.0  # base score

        # Fragility: lower is better (research §3.7)
        score -= h["fragility_score"] * 1.5

        # CCRLO probability: lower is better (research §3.8)
        if h["ccrlo_prob"] < 25:
            score += 2.0
        elif h["ccrlo_prob"] > 50:
            score -= 2.0
        elif h["ccrlo_prob"] > 40:
            score -= 1.0

        # Regime: calm is best (research §3.8)
        regime_scores = {"calm": 2.0, "trending": 0.5, "stressed": -2.0, "crash_prone": -4.0}
        score += regime_scores.get(h["regime"], 0)

        # Tail risk weight: lower is better
        if h["tail_risk_weight"] > 0.3:
            score -= 2.0
        elif h["tail_risk_weight"] > 0.2:
            score -= 1.0

        # Beta: moderate is ideal for growth, very high is penalized
        if h["beta"] > 2.0:
            score -= 1.5
        elif h["beta"] > 1.5:
            score -= 0.5

        # Downside skew: lower is better
        if h["downside_skew"] > 50:
            score -= 1.5
        elif h["downside_skew"] > 30:
            score -= 0.5

        # Trend-break active: penalize (research short-term signals)
        if h["tb_active"]:
            score -= 3.0

        # Floor at 1.0 to ensure minimum allocation
        scores.append(max(score, 1.0))

    total = sum(scores)
    return {h["ticker"]: s / total for h, s in zip(holdings, scores)}


def apply_fragility_penalty(weights, holdings, penalty_rate):
    """
    Research §3.7: reduce allocation to fragile assets.
    Penalty = weight × (1 - fragility_score × penalty_rate).
    """
    adjusted = {}
    for h in holdings:
        t = h["ticker"]
        factor = max(0.3, 1.0 - h["fragility_score"] * penalty_rate)
        adjusted[t] = weights[t] * factor
    # Renormalize
    total = sum(adjusted.values())
    if total > 0:
        return {t: w / total for t, w in adjusted.items()}
    return weights


def enforce_constraints(weights, holdings, config):
    """
    Research §7 Logic Step 7: Enforce all constraints.
    - max/min single weight
    - max sector weight
    """
    max_w = config["max_single_weight"]
    min_w = config["min_single_weight"]
    max_sector = config["max_sector_weight"]

    # Build sector map
    sector_weights = {}
    for h in holdings:
        s = h["sector"]
        sector_weights.setdefault(s, 0)
        sector_weights[s] += weights[h["ticker"]]

    # Iterative constraint enforcement (3 passes for convergence)
    constrained = dict(weights)
    for _ in range(3):
        # Cap individual weights
        excess = 0
        under_cap_count = 0
        for t, w in constrained.items():
            if w > max_w:
                excess += w - max_w
                constrained[t] = max_w
            else:
                under_cap_count += 1

        # Redistribute excess
        if excess > 0 and under_cap_count > 0:
            for t in constrained:
                if constrained[t] < max_w:
                    constrained[t] += excess / under_cap_count

        # Apply minimum
        for t in constrained:
            constrained[t] = max(constrained[t], min_w)

        # Renormalize
        total = sum(constrained.values())
        constrained = {t: w / total for t, w in constrained.items()}

    return constrained


def apply_regime_derisking(weights, holdings, config):
    """
    Research §3.8 + §6: Regime-aware de-risking.
    If a ticker is in stressed/crash-prone regime, reduce its weight.
    Redistribute to calmer assets.
    """
    derisked = dict(weights)
    derisking_applied = []

    for h in holdings:
        t = h["ticker"]
        regime = h["regime"]

        if regime == "crash_prone":
            reduction = derisked[t] * 0.40  # cut 40%
            derisked[t] -= reduction
            derisking_applied.append((t, regime, reduction))
        elif regime == "stressed":
            reduction = derisked[t] * 0.20  # cut 20%
            derisked[t] -= reduction
            derisking_applied.append((t, regime, reduction))

    if derisking_applied:
        # Redistribute to calm/trending assets
        calm_tickers = [h["ticker"] for h in holdings if h["regime"] in ("calm", "trending")]
        total_freed = sum(r[2] for r in derisking_applied)
        if calm_tickers and total_freed > 0:
            per_ticker = total_freed / len(calm_tickers)
            for t in calm_tickers:
                derisked[t] += per_ticker

        # Renormalize
        total = sum(derisked.values())
        derisked = {t: w / total for t, w in derisked.items()}

    return derisked, derisking_applied


def optimize_weights(holdings, risk_band, config=None):
    """
    Main optimization pipeline — implements research §7 Logic Steps 1-7.
    Returns target weights + optimization metadata.
    """
    band_config = RISK_BAND_CONFIG.get(risk_band, RISK_BAND_CONFIG["growth"])
    method = band_config["method"]

    # Step 1: Base weight calculation
    if method == "inverse_volatility":
        raw_weights = compute_inverse_volatility_weights(holdings)
    elif method == "risk_parity":
        raw_weights = compute_risk_parity_weights(holdings)
    else:  # signal_weighted
        raw_weights = compute_signal_weighted(holdings)

    # Step 2: Apply fragility penalty (research §3.7)
    penalized = apply_fragility_penalty(raw_weights, holdings, band_config["fragility_penalty"])

    # Step 3: Enforce constraints (research §7 step 7)
    constrained = enforce_constraints(penalized, holdings, band_config)

    # Step 4: Regime-aware de-risking (research §3.8)
    if band_config["regime_derisking"]:
        final_weights, derisking_log = apply_regime_derisking(constrained, holdings, band_config)
    else:
        final_weights, derisking_log = constrained, []

    # Equal weights for comparison
    n = len(holdings)
    equal_weights = {h["ticker"]: 1.0 / n for h in holdings}

    return {
        "method": method,
        "risk_band": risk_band,
        "objective": band_config["objective"],
        "raw_weights": raw_weights,
        "fragility_adjusted": penalized,
        "constrained": constrained,
        "final_weights": final_weights,
        "equal_weights": equal_weights,
        "derisking_applied": derisking_log,
        "constraints": {
            "max_single_weight": band_config["max_single_weight"],
            "min_single_weight": band_config["min_single_weight"],
            "max_sector_weight": band_config["max_sector_weight"],
        },
    }


# ═══════════════════════════════════════════════════════════
#  PORTFOLIO RISK METRICS — §7 Logic Step 10
# ═══════════════════════════════════════════════════════════

def compute_portfolio_risk_metrics(holdings, weights):
    """
    Compute portfolio-level risk metrics using signal data.
    Implements research §7 monitoring requirements.
    """
    metrics = {}

    # ── Weighted Beta ──
    metrics["portfolio_beta"] = round(
        sum(weights[h["ticker"]] * h["beta"] for h in holdings), 3
    )

    # ── Weighted Volatility (ATR% proxy) ──
    metrics["portfolio_vol_proxy"] = round(
        sum(weights[h["ticker"]] * h["atr_pct"] for h in holdings), 2
    )

    # ── Weighted Fragility ──
    metrics["weighted_fragility"] = round(
        sum(weights[h["ticker"]] * h["fragility_score"] for h in holdings), 2
    )

    # ── Weighted CCRLO ──
    metrics["weighted_ccrlo"] = round(
        sum(weights[h["ticker"]] * h["ccrlo_prob"] for h in holdings), 2
    )

    # ── Concentration: Herfindahl Index ──
    # HHI = sum(w_i^2). 1/N = perfectly diversified. 1.0 = single stock.
    hhi = sum(w ** 2 for w in weights.values())
    n = len(weights)
    metrics["herfindahl_index"] = round(hhi, 4)
    metrics["effective_n"] = round(1.0 / hhi, 1) if hhi > 0 else n
    metrics["max_single_weight"] = round(max(weights.values()) * 100, 1)

    # ── Sector Diversification ──
    sector_weights = {}
    for h in holdings:
        s = h["sector"]
        sector_weights[s] = sector_weights.get(s, 0) + weights[h["ticker"]]
    metrics["sector_concentration"] = round(max(sector_weights.values()) * 100, 1) if sector_weights else 0
    metrics["sector_count"] = len(sector_weights)
    metrics["sector_weights"] = {s: round(w * 100, 1) for s, w in sector_weights.items()}

    # ── Expected Shortfall Proxy ──
    # ES ≈ weighted average of per-ticker severe correction probabilities × downside
    # Approximation using simulation scenario data
    weighted_tail_risk = sum(
        weights[h["ticker"]] * h["tail_risk_weight"] for h in holdings
    )
    weighted_downside_skew = sum(
        weights[h["ticker"]] * h["downside_skew"] for h in holdings
    )

    # ES proxy = probability of tail scenario × expected tail loss magnitude
    # Using correction probabilities as loss magnitude approximation
    es_proxy_pcts = []
    for h in holdings:
        w = weights[h["ticker"]]
        # Use severe correction probability as loss magnitude proxy
        severe_prob = h["correction_probs"].get("severe", 30) / 100.0
        contribution = w * severe_prob * (h["atr_pct"] / 100.0 * 5)  # ~5 ATR move in severe
        es_proxy_pcts.append(contribution)

    metrics["expected_shortfall_proxy"] = round(sum(es_proxy_pcts) * 100, 2)
    metrics["weighted_tail_risk"] = round(weighted_tail_risk, 3)
    metrics["weighted_downside_skew"] = round(weighted_downside_skew, 1)

    # ── Drawdown Risk Score (0-100) ──
    # Composite: beta-adjusted vol + CCRLO + tail risk + regime stress
    regime_stress = sum(
        weights[h["ticker"]] * (h["regime_probs"].get("stressed", 0) + h["regime_probs"].get("crash_prone", 0))
        for h in holdings
    )
    drawdown_score = (
        metrics["portfolio_beta"] * 10 +
        metrics["weighted_ccrlo"] * 0.5 +
        weighted_tail_risk * 30 +
        regime_stress * 20 +
        weighted_downside_skew * 0.3
    )
    metrics["drawdown_risk_score"] = round(min(drawdown_score, 100), 1)

    return metrics


# ═══════════════════════════════════════════════════════════
#  STRESS TESTING — §7 Logic Step 9
# ═══════════════════════════════════════════════════════════

def run_stress_tests(holdings, weights):
    """
    Research §3.7: Scenario stress testing.
    Run predefined stress scenarios and compute portfolio impact.
    """
    scenarios = [
        {
            "name": "Market Correction (-15%)",
            "description": "Broad market selloff. Higher-beta names hit harder.",
            "impact_fn": lambda h: -15.0 * h["beta"],
        },
        {
            "name": "Volatility Spike (+50% ATR)",
            "description": "Sudden volatility regime shift. High-ATR names most affected.",
            "impact_fn": lambda h: -h["atr_pct"] * 2.5,
        },
        {
            "name": "Sector Rotation",
            "description": "Growth-to-value rotation. High-PE growth stocks underperform.",
            "impact_fn": lambda h: -8.0 if "bearish" in h.get("momentum_tags", []) else 2.0,
        },
        {
            "name": "Credit Stress",
            "description": "Credit spread widening. High-leverage names underperform.",
            "impact_fn": lambda h: -12.0 if h["fragility_dims"].get("leverage") == "HIGH" else -3.0,
        },
        {
            "name": "Tail Event (Black Swan -30%)",
            "description": "Extreme market dislocation. All assets decline, betas amplify.",
            "impact_fn": lambda h: -30.0 * max(h["beta"], 0.8),
        },
    ]

    results = []
    for scenario in scenarios:
        ticker_impacts = {}
        portfolio_impact = 0
        for h in holdings:
            impact = scenario["impact_fn"](h)
            ticker_impacts[h["ticker"]] = round(impact, 2)
            portfolio_impact += weights[h["ticker"]] * impact

        results.append({
            "name": scenario["name"],
            "description": scenario["description"],
            "portfolio_impact_pct": round(portfolio_impact, 2),
            "ticker_impacts": ticker_impacts,
            "severity": "HIGH" if portfolio_impact < -15 else ("MEDIUM" if portfolio_impact < -8 else "LOW"),
        })

    return results


# ═══════════════════════════════════════════════════════════
#  REBALANCING SIGNALS — §7 Logic Step 8
# ═══════════════════════════════════════════════════════════

def compute_rebalancing_signals(holdings, target_weights, current_weights, config):
    """
    Research §7 Step 8: Determine if rebalance is justified.
    Checks drift, risk limit breaches, and regime changes.
    """
    band_config = RISK_BAND_CONFIG.get(config.get("risk_band", "growth"), RISK_BAND_CONFIG["growth"])
    signals = {"triggers": [], "actions": [], "urgency": "NONE"}

    # ── Weight Drift ──
    max_drift = 0
    drifts = {}
    for t, target_w in target_weights.items():
        current_w = current_weights.get(t, target_w)
        drift = abs(current_w - target_w) * 100
        drifts[t] = round(drift, 2)
        max_drift = max(max_drift, drift)

    if max_drift > band_config["rebalance_drift_pct"]:
        signals["triggers"].append({
            "type": "WEIGHT_DRIFT",
            "detail": "Max drift %.1f%% exceeds threshold %.1f%%" % (max_drift, band_config["rebalance_drift_pct"]),
            "severity": "HIGH" if max_drift > band_config["rebalance_drift_pct"] * 2 else "MEDIUM",
        })
        signals["actions"].append("Rebalance to target weights — drift exceeds threshold")

    signals["weight_drifts"] = drifts
    signals["max_drift"] = round(max_drift, 2)

    # ── CCRLO Breach ──
    avg_ccrlo = sum(target_weights[h["ticker"]] * h["ccrlo_prob"] for h in holdings)
    if avg_ccrlo > band_config["ccrlo_threshold"]:
        signals["triggers"].append({
            "type": "CCRLO_BREACH",
            "detail": "Weighted CCRLO %.1f%% exceeds %s band limit %.1f%%" % (avg_ccrlo, config.get("risk_band", "growth"), band_config["ccrlo_threshold"]),
            "severity": "HIGH",
        })
        signals["actions"].append("Reduce exposure to high-CCRLO holdings or shift to more conservative risk band")

    # ── Regime Change ──
    stressed_count = sum(1 for h in holdings if h["regime"] in ("stressed", "crash_prone"))
    if stressed_count > len(holdings) * 0.5:
        signals["triggers"].append({
            "type": "REGIME_SHIFT",
            "detail": "%d of %d holdings in stressed/crash-prone regime" % (stressed_count, len(holdings)),
            "severity": "HIGH",
        })
        signals["actions"].append("Consider defensive shift — majority of holdings in adverse regime")

    # ── Trend-Break Active ──
    tb_count = sum(1 for h in holdings if h["tb_active"])
    if tb_count > 0:
        tb_tickers = [h["ticker"] for h in holdings if h["tb_active"]]
        signals["triggers"].append({
            "type": "TREND_BREAK",
            "detail": "%d holdings with active trend-break: %s" % (tb_count, ", ".join(tb_tickers)),
            "severity": "MEDIUM",
        })
        signals["actions"].append("Review trend-breaking positions — consider underweighting %s" % ", ".join(tb_tickers))

    # ── Concentration ──
    max_w = max(target_weights.values())
    if max_w > band_config["max_single_weight"]:
        signals["triggers"].append({
            "type": "CONCENTRATION",
            "detail": "Max single weight %.1f%% exceeds limit %.1f%%" % (max_w * 100, band_config["max_single_weight"] * 100),
            "severity": "MEDIUM",
        })
        signals["actions"].append("Trim overweight position to comply with concentration limit")

    # Set urgency
    severities = [t["severity"] for t in signals["triggers"]]
    if "HIGH" in severities:
        signals["urgency"] = "HIGH"
    elif "MEDIUM" in severities:
        signals["urgency"] = "MEDIUM"
    elif signals["triggers"]:
        signals["urgency"] = "LOW"

    return signals


# ═══════════════════════════════════════════════════════════
#  STRATEGY RECOMMENDATION — Research §6 + §9
# ═══════════════════════════════════════════════════════════

def generate_strategy_recommendation(holdings, weights, risk_metrics, risk_band):
    """
    Map current portfolio state to research framework recommendations.
    Returns structured recommendation with rationale.
    """
    band_config = RISK_BAND_CONFIG.get(risk_band, RISK_BAND_CONFIG["growth"])
    rec = {
        "risk_band": risk_band,
        "objective": band_config["objective"],
        "recommended_framework": "",
        "base_method": band_config["method"],
        "overlays": [],
        "hard_controls": [],
        "current_assessment": "",
        "action_items": [],
        "warnings": [],
    }

    # Framework recommendation from research §6
    if risk_band == "conservative":
        rec["recommended_framework"] = "Minimum-variance with tail constraints"
        rec["hard_controls"] = ["expected_shortfall_cap", "stress_tests", "concentration_limits"]
    elif risk_band == "moderate":
        rec["recommended_framework"] = "Risk budgeting with bounded volatility control"
        rec["overlays"] = ["bounded_vol_target"]
        rec["hard_controls"] = ["expected_shortfall_cap", "turnover_cap", "scenario_limits"]
    elif risk_band == "growth":
        rec["recommended_framework"] = "Constrained signal-weighted with factor diversification"
        rec["overlays"] = ["trend_overlay", "regime_monitoring"]
        rec["hard_controls"] = ["expected_shortfall_cap", "leverage_cap", "regime_monitoring"]
    elif risk_band == "aggressive":
        rec["recommended_framework"] = "Diversified return stack with survivability controls"
        rec["overlays"] = ["factor_diversification", "trend_overlay", "bounded_vol_target"]
        rec["hard_controls"] = ["expected_shortfall_cap", "drawdown_trigger", "stress_gate", "leverage_cap"]

    # Current assessment
    dd_score = risk_metrics["drawdown_risk_score"]
    if dd_score < 25:
        rec["current_assessment"] = "Portfolio drawdown risk is LOW (%.1f/100). Current allocation is within risk tolerance for the %s mandate." % (dd_score, risk_band)
    elif dd_score < 50:
        rec["current_assessment"] = "Portfolio drawdown risk is MODERATE (%.1f/100). Monitor regime shifts and consider incremental de-risking if conditions deteriorate." % dd_score
    elif dd_score < 75:
        rec["current_assessment"] = "Portfolio drawdown risk is ELEVATED (%.1f/100). Active risk management recommended — review concentrated positions and high-CCRLO holdings." % dd_score
    else:
        rec["current_assessment"] = "Portfolio drawdown risk is HIGH (%.1f/100). Immediate defensive action recommended — reduce gross exposure, trim high-beta positions, and increase cash or hedges." % dd_score

    # Action items based on current state
    w_ccrlo = risk_metrics["weighted_ccrlo"]
    if w_ccrlo > band_config["ccrlo_threshold"]:
        rec["action_items"].append("Weighted CCRLO (%.1f%%) exceeds %s threshold (%.1f%%). Consider reducing high-CCRLO positions." % (w_ccrlo, risk_band, band_config["ccrlo_threshold"]))

    es = risk_metrics["expected_shortfall_proxy"]
    if es > band_config["es_limit"] * 100:
        rec["action_items"].append("Expected shortfall proxy (%.2f%%) exceeds limit (%.1f%%). Portfolio tail risk is above tolerance." % (es, band_config["es_limit"] * 100))

    if risk_metrics["sector_concentration"] > band_config["max_sector_weight"] * 100:
        rec["action_items"].append("Sector concentration (%.1f%%) exceeds limit (%.1f%%). Diversify across additional sectors." % (risk_metrics["sector_concentration"], band_config["max_sector_weight"] * 100))

    if risk_metrics["effective_n"] < len(holdings) * 0.6:
        rec["action_items"].append("Effective diversification (%.1f assets) is low relative to holdings (%d). Portfolio is concentrated despite nominal breadth." % (risk_metrics["effective_n"], len(holdings)))

    # Warnings from research
    stressed = sum(1 for h in holdings if h["regime"] in ("stressed", "crash_prone"))
    if stressed > 0:
        rec["warnings"].append("%d holdings in stressed/crash-prone regime. Static diversification benefits may be reduced (research §3.8)." % stressed)

    high_beta = [h["ticker"] for h in holdings if h["beta"] > 1.8]
    if high_beta:
        rec["warnings"].append("High-beta positions (%s) amplify market drawdowns. Ensure position sizing accounts for beta-adjusted risk." % ", ".join(high_beta))

    if not rec["action_items"]:
        rec["action_items"].append("No immediate action required. Portfolio is within risk parameters for the %s mandate." % risk_band)

    return rec


# ═══════════════════════════════════════════════════════════
#  MAIN PIPELINE
# ═══════════════════════════════════════════════════════════

def run_optimizer(tickers, risk_band="growth", current_weights=None, config=None):
    """
    Full optimization pipeline.
    Returns complete optimization result as JSON-serializable dict.
    """
    # Load all ticker signals
    holdings = []
    for t in tickers:
        data = load_ticker_signals(t)
        if data:
            holdings.append(data)
        else:
            print("  WARN: Skipping %s — missing signal data" % t, file=sys.stderr)

    if not holdings:
        return {"error": "No valid tickers with complete signal data"}

    # If no current weights provided, assume equal
    if current_weights is None:
        n = len(holdings)
        current_weights = {h["ticker"]: 1.0 / n for h in holdings}

    # Step 1: Optimize weights
    optimization = optimize_weights(holdings, risk_band, config)

    # Step 2: Compute risk metrics for final weights
    risk_metrics = compute_portfolio_risk_metrics(holdings, optimization["final_weights"])

    # Step 3: Also compute risk metrics for equal weights (comparison)
    equal_risk_metrics = compute_portfolio_risk_metrics(holdings, optimization["equal_weights"])

    # Step 4: Run stress tests
    stress_tests = run_stress_tests(holdings, optimization["final_weights"])

    # Step 5: Compute rebalancing signals
    rebalancing = compute_rebalancing_signals(
        holdings, optimization["final_weights"], current_weights,
        {"risk_band": risk_band}
    )

    # Step 6: Generate strategy recommendation
    recommendation = generate_strategy_recommendation(
        holdings, optimization["final_weights"], risk_metrics, risk_band
    )

    return {
        "generated_at": datetime.now().isoformat(),
        "risk_band": risk_band,
        "ticker_count": len(holdings),
        "tickers": [h["ticker"] for h in holdings],
        "optimization": {
            "method": optimization["method"],
            "objective": optimization["objective"],
            "final_weights": {t: round(w, 4) for t, w in optimization["final_weights"].items()},
            "equal_weights": {t: round(w, 4) for t, w in optimization["equal_weights"].items()},
            "weight_comparison": {
                t: {
                    "optimized": round(optimization["final_weights"][t] * 100, 1),
                    "equal": round(optimization["equal_weights"][t] * 100, 1),
                    "diff": round((optimization["final_weights"][t] - optimization["equal_weights"][t]) * 100, 1),
                }
                for t in optimization["final_weights"]
            },
            "constraints": optimization["constraints"],
            "derisking_applied": [
                {"ticker": t, "regime": r, "weight_reduced": round(red, 4)}
                for t, r, red in optimization["derisking_applied"]
            ],
        },
        "risk_metrics": {
            "optimized": risk_metrics,
            "equal_weight": equal_risk_metrics,
            "improvement": {
                "beta": round(equal_risk_metrics["portfolio_beta"] - risk_metrics["portfolio_beta"], 3),
                "vol_proxy": round(equal_risk_metrics["portfolio_vol_proxy"] - risk_metrics["portfolio_vol_proxy"], 2),
                "ccrlo": round(equal_risk_metrics["weighted_ccrlo"] - risk_metrics["weighted_ccrlo"], 2),
                "drawdown_score": round(equal_risk_metrics["drawdown_risk_score"] - risk_metrics["drawdown_risk_score"], 1),
            },
        },
        "stress_tests": stress_tests,
        "rebalancing": rebalancing,
        "recommendation": recommendation,
        "per_ticker_summary": [
            {
                "ticker": h["ticker"],
                "price": h["price"],
                "beta": h["beta"],
                "atr_pct": round(h["atr_pct"], 2),
                "fragility": h["fragility_score"],
                "ccrlo": h["ccrlo_prob"],
                "regime": h["regime"],
                "tail_risk": round(h["tail_risk_weight"], 3),
                "optimized_weight": round(optimization["final_weights"][h["ticker"]] * 100, 1),
                "equal_weight": round(100.0 / len(holdings), 1),
            }
            for h in holdings
        ],
    }


def main():
    parser = argparse.ArgumentParser(description="Portfolio optimizer — evidence-based construction")
    parser.add_argument("--tickers", nargs="+", help="Specific tickers")
    parser.add_argument("--risk-band", default="growth",
                        choices=["conservative", "moderate", "growth", "aggressive"],
                        help="Risk band (default: growth)")
    parser.add_argument("--config", help="Path to portfolio_config.json")
    args = parser.parse_args()

    print("=" * 60)
    print("PORTFOLIO OPTIMIZER — Evidence-Based Construction")
    print("  Risk Band: %s" % args.risk_band)
    print("=" * 60)

    # Discover tickers
    tickers = args.tickers
    config = None
    if args.config:
        config = load_json(args.config)
        if config:
            tickers = config.get("tickers", tickers)
            if "risk_band" in config:
                args.risk_band = config["risk_band"]

    if not tickers:
        tags_index = load_json(TAGS_INDEX_PATH)
        if tags_index:
            tickers = list(tags_index.keys())
        else:
            print("ERROR: No tickers found.", file=sys.stderr)
            sys.exit(1)

    print("  Tickers: %s" % ", ".join(tickers))
    print()

    # Run optimizer
    result = run_optimizer(tickers, args.risk_band, config=config)

    if "error" in result:
        print("ERROR: %s" % result["error"], file=sys.stderr)
        sys.exit(1)

    # Save result
    output_path = OUTPUT_DIR / "portfolio_optimization.json"
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("Optimization saved: %s" % output_path)

    # Print summary
    opt = result["optimization"]
    rm = result["risk_metrics"]["optimized"]
    rec = result["recommendation"]

    print()
    print("─── TARGET WEIGHTS ───")
    for t, data in opt["weight_comparison"].items():
        arrow = "+" if data["diff"] > 0 else ""
        print("  %s: %.1f%% (equal: %.1f%%, %s%.1f%%)" % (t, data["optimized"], data["equal"], arrow, data["diff"]))

    print()
    print("─── RISK METRICS (Optimized vs Equal-Weight) ───")
    imp = result["risk_metrics"]["improvement"]
    print("  Portfolio Beta:    %.3f (improvement: %+.3f)" % (rm["portfolio_beta"], imp["beta"]))
    print("  Vol Proxy (ATR%%):  %.2f%% (improvement: %+.2f%%)" % (rm["portfolio_vol_proxy"], imp["vol_proxy"]))
    print("  Weighted CCRLO:    %.1f%% (improvement: %+.1f%%)" % (rm["weighted_ccrlo"], imp["ccrlo"]))
    print("  Drawdown Score:    %.1f/100 (improvement: %+.1f)" % (rm["drawdown_risk_score"], imp["drawdown_score"]))
    print("  Expected Shortfall: %.2f%%" % rm["expected_shortfall_proxy"])
    print("  Concentration:     %.1f%% max single / %.1f effective-N" % (rm["max_single_weight"], rm["effective_n"]))

    print()
    print("─── STRESS TESTS ───")
    for st in result["stress_tests"]:
        print("  [%s] %s: %.1f%%" % (st["severity"], st["name"], st["portfolio_impact_pct"]))

    print()
    print("─── REBALANCING ───")
    print("  Urgency: %s" % result["rebalancing"]["urgency"])
    for t in result["rebalancing"]["triggers"]:
        print("  [%s] %s: %s" % (t["severity"], t["type"], t["detail"]))

    print()
    print("─── STRATEGY RECOMMENDATION ───")
    print("  Framework: %s" % rec["recommended_framework"])
    print("  Assessment: %s" % rec["current_assessment"])
    for a in rec["action_items"]:
        print("  ACTION: %s" % a)
    for w in rec["warnings"]:
        print("  WARNING: %s" % w)

    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
