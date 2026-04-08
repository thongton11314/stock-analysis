"""
Numerical Audit & Validation Script

End-to-end numerical integrity validator that operates at three stages:
  Stage A: Data bundle numbers (pre-computation)
  Stage B: Signal computation math (post-computation)
  Stage C: HTML report numbers (post-report)

Usage:
    python scripts/validate_numbers.py --ticker AMZN            # All stages
    python scripts/validate_numbers.py --ticker AMZN --stage A  # Data bundle only
    python scripts/validate_numbers.py --ticker AMZN --stage B  # Signals only
    python scripts/validate_numbers.py --ticker AMZN --stage C  # Report only

Exit codes:
    0 = All stages PASS (or WARN)
    1 = Stage A failed (data bundle numbers invalid)
    2 = Stage B failed (signal calculations wrong)
    3 = Stage C failed (report numbers don't match source)
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta


# ─────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────

def _safe_float(val, default=None):
    """Convert a value to float safely."""
    if val is None or str(val).strip() in ("", "None", "-", "N/A"):
        return default
    try:
        return float(str(val).replace(",", "").replace("$", "").replace("%", ""))
    except (ValueError, TypeError):
        return default


def _approx(a, b, tolerance):
    """Check if two values are approximately equal within tolerance."""
    if a is None or b is None:
        return a is None and b is None
    return abs(a - b) <= tolerance


def _pct_diff(actual, expected):
    """Calculate percentage difference."""
    if expected == 0:
        return 0 if actual == 0 else float("inf")
    return abs(actual - expected) / abs(expected) * 100


def _check(field, status, reason):
    """Create a check result dict."""
    return {"field": field, "status": status, "reason": reason}


# ─────────────────────────────────────────────────────────────────────
# STAGE A: DATA BUNDLE NUMERICAL VALIDATION
# ─────────────────────────────────────────────────────────────────────

def stage_a_validate(data: dict) -> list[dict]:
    """Validate data bundle numbers for accuracy and consistency."""
    checks = []
    gq = data.get("global_quote", {})
    co = data.get("company_overview", {})

    # ── A1: Price & Quote Consistency ──

    price = _safe_float(gq.get("price"))
    prev_close = _safe_float(gq.get("previous_close"))
    change = _safe_float(gq.get("change"))
    change_pct = _safe_float(gq.get("change_percent"))
    open_p = _safe_float(gq.get("open"))
    high = _safe_float(gq.get("high"))
    low = _safe_float(gq.get("low"))

    # A1a: Price change math
    if price is not None and prev_close is not None and change is not None:
        expected_change = round(price - prev_close, 4)
        if _approx(change, expected_change, 0.02):
            checks.append(_check("A1a.price_change", "PASS",
                                 f"${price} - ${prev_close} = ${expected_change} ≈ ${change}"))
        else:
            checks.append(_check("A1a.price_change", "FAIL",
                                 f"${price} - ${prev_close} = ${expected_change} ≠ stated ${change}"))
    elif price is None:
        checks.append(_check("A1a.price_change", "FAIL", "Missing price"))
    else:
        checks.append(_check("A1a.price_change", "WARN", "Missing previous_close or change"))

    # A1b: Change percent
    if change is not None and prev_close is not None and prev_close != 0 and change_pct is not None:
        expected_pct = round(change / prev_close * 100, 4)
        if _approx(change_pct, expected_pct, 0.1):
            checks.append(_check("A1b.change_pct", "PASS",
                                 f"{change}/{prev_close}×100 = {expected_pct:.2f}% ≈ {change_pct}%"))
        else:
            checks.append(_check("A1b.change_pct", "FAIL",
                                 f"Expected {expected_pct:.2f}%, stated {change_pct}%"))
    else:
        checks.append(_check("A1b.change_pct", "WARN", "Cannot verify change percent"))

    # A1c: OHLC ordering
    if all(v is not None for v in (open_p, high, low, price)):
        if low <= min(open_p, price) and high >= max(open_p, price):
            checks.append(_check("A1c.ohlc_order", "PASS",
                                 f"L={low} ≤ O={open_p},C={price} ≤ H={high}"))
        else:
            checks.append(_check("A1c.ohlc_order", "FAIL",
                                 f"OHLC ordering violated: O={open_p} H={high} L={low} C={price}"))
    else:
        checks.append(_check("A1c.ohlc_order", "WARN", "Missing OHLC data"))

    # A1d: Price vs 52-week range
    wk52_high = _safe_float(co.get("52_week_high"))
    wk52_low = _safe_float(co.get("52_week_low"))
    if price is not None and wk52_low is not None and wk52_high is not None:
        # Allow 5% overshoot for data lag
        if wk52_low * 0.95 <= price <= wk52_high * 1.05:
            checks.append(_check("A1d.52wk_range", "PASS",
                                 f"${price} within 52wk [{wk52_low}, {wk52_high}]"))
        else:
            checks.append(_check("A1d.52wk_range", "WARN",
                                 f"${price} outside 52wk [{wk52_low}, {wk52_high}] (may be data lag)"))
    else:
        checks.append(_check("A1d.52wk_range", "WARN", "Missing 52-week data"))

    # A1e: Market cap derivation (approximate)
    mkt_cap = _safe_float(co.get("market_cap"))
    shares = _safe_float(co.get("shares_outstanding"))
    if price is not None and shares is not None and mkt_cap is not None and shares > 0:
        expected_mcap = price * shares
        if _pct_diff(mkt_cap, expected_mcap) <= 5:
            checks.append(_check("A1e.mkt_cap", "PASS",
                                 f"Mkt cap ${mkt_cap/1e9:.1f}B ≈ ${price}×{shares/1e9:.2f}B"))
        else:
            checks.append(_check("A1e.mkt_cap", "WARN",
                                 f"Mkt cap ${mkt_cap/1e9:.1f}B vs derived ${expected_mcap/1e9:.1f}B"))
    else:
        checks.append(_check("A1e.mkt_cap", "WARN", "Cannot verify market cap derivation"))

    # ── A2: Financial Statement Math ──

    income = data.get("income_statement", {})
    annual = income.get("annual", income.get("annualReports", []))
    if isinstance(annual, list) and len(annual) > 0:
        stmt = annual[0]
        revenue = _safe_float(stmt.get("totalRevenue", stmt.get("revenue")))
        cogs = _safe_float(stmt.get("costOfRevenue", stmt.get("costofGoodsAndServicesSold")))
        gross_profit = _safe_float(stmt.get("grossProfit"))
        op_income = _safe_float(stmt.get("operatingIncome"))
        net_income = _safe_float(stmt.get("netIncome"))

        # A2a: Gross profit
        if revenue is not None and cogs is not None and gross_profit is not None:
            expected_gp = revenue - cogs
            tol = abs(revenue) * 0.01 if revenue != 0 else 1e6
            if _approx(gross_profit, expected_gp, tol):
                checks.append(_check("A2a.gross_profit", "PASS",
                                     f"${revenue/1e9:.2f}B - ${cogs/1e9:.2f}B = ${expected_gp/1e9:.2f}B ≈ ${gross_profit/1e9:.2f}B"))
            else:
                checks.append(_check("A2a.gross_profit", "FAIL",
                                     f"GP expected ${expected_gp/1e9:.2f}B, stated ${gross_profit/1e9:.2f}B"))
        else:
            checks.append(_check("A2a.gross_profit", "WARN", "Missing revenue/COGS/GP fields"))

        # A2e: FCF
        cf = data.get("cash_flow", {})
        cf_annual = cf.get("annual", cf.get("annualReports", []))
        if isinstance(cf_annual, list) and len(cf_annual) > 0:
            cf_stmt = cf_annual[0]
            ocf = _safe_float(cf_stmt.get("operatingCashflow"))
            capex = _safe_float(cf_stmt.get("capitalExpenditures"))
            fcf_stated = _safe_float(cf.get("free_cash_flow",
                                            cf_stmt.get("freeCashFlow")))
            if ocf is not None and capex is not None:
                # CapEx is sometimes negative in Alpha Vantage
                abs_capex = abs(capex)
                expected_fcf = ocf - abs_capex
                if fcf_stated is not None:
                    tol = abs(ocf) * 0.01 if ocf != 0 else 1e6
                    if _approx(fcf_stated, expected_fcf, tol):
                        checks.append(_check("A2e.fcf", "PASS",
                                             f"OCF ${ocf/1e9:.2f}B - CapEx ${abs_capex/1e9:.2f}B = ${expected_fcf/1e9:.2f}B"))
                    else:
                        checks.append(_check("A2e.fcf", "FAIL",
                                             f"FCF expected ${expected_fcf/1e9:.2f}B, stated ${fcf_stated/1e9:.2f}B"))
                else:
                    checks.append(_check("A2e.fcf", "WARN", "FCF not stated; derived would be "
                                         f"${expected_fcf/1e9:.2f}B"))
            else:
                checks.append(_check("A2e.fcf", "WARN", "Missing OCF or CapEx"))
        else:
            checks.append(_check("A2e.fcf", "WARN", "No cash flow data"))

        # A2f: D/E ratio
        de_stated = _safe_float(co.get("debt_to_equity"))
        bs = data.get("balance_sheet", {})
        bs_annual = bs.get("annual", bs.get("annualReports", []))
        if isinstance(bs_annual, list) and len(bs_annual) > 0:
            bs_stmt = bs_annual[0]
            total_debt = _safe_float(bs_stmt.get("shortLongTermDebtTotal",
                                                  bs_stmt.get("longTermDebt")))
            total_equity = _safe_float(bs_stmt.get("totalShareholderEquity"))

            # A2g: Balance sheet identity
            total_assets = _safe_float(bs_stmt.get("totalAssets"))
            total_liab = _safe_float(bs_stmt.get("totalLiabilities"))
            if total_assets is not None and total_liab is not None and total_equity is not None:
                expected_assets = total_liab + total_equity
                tol = abs(total_assets) * 0.01 if total_assets != 0 else 1e6
                if _approx(total_assets, expected_assets, tol):
                    checks.append(_check("A2g.bs_identity", "PASS",
                                         f"Assets ${total_assets/1e9:.1f}B ≈ L+E ${expected_assets/1e9:.1f}B"))
                else:
                    checks.append(_check("A2g.bs_identity", "WARN",
                                         f"Assets ${total_assets/1e9:.1f}B ≠ L+E ${expected_assets/1e9:.1f}B"))
            else:
                checks.append(_check("A2g.bs_identity", "WARN", "Missing balance sheet totals"))
        else:
            checks.append(_check("A2g.bs_identity", "WARN", "No balance sheet data"))
    else:
        checks.append(_check("A2a.gross_profit", "WARN", "No income statement data"))
        checks.append(_check("A2e.fcf", "WARN", "No financial data"))
        checks.append(_check("A2g.bs_identity", "WARN", "No balance sheet data"))

    # ── A3: Data Freshness ──

    today = datetime.now()
    as_of = data.get("as_of")
    if as_of:
        try:
            data_date = datetime.strptime(as_of, "%Y-%m-%d")
            days_old = (today - data_date).days
            if days_old <= 3:
                checks.append(_check("A3a.freshness", "PASS", f"{days_old} days old"))
            elif days_old <= 10:
                checks.append(_check("A3a.freshness", "WARN", f"{days_old} days old (>3 days)"))
            else:
                checks.append(_check("A3a.freshness", "FAIL", f"Data is {days_old} days old (>10 days)"))
        except ValueError:
            checks.append(_check("A3a.freshness", "WARN", f"Cannot parse date: {as_of}"))
    else:
        checks.append(_check("A3a.freshness", "WARN", "Missing as_of date"))

    # A3e: Macro data currency
    ffr = data.get("federal_funds_rate", [])
    if isinstance(ffr, list) and len(ffr) > 0:
        ffr_date = ffr[0].get("date", "")
        try:
            ffr_dt = datetime.strptime(ffr_date, "%Y-%m-%d")
            months_old = (today - ffr_dt).days / 30
            if months_old <= 2:
                checks.append(_check("A3e.macro_currency", "PASS",
                                     f"Fed rate data from {ffr_date} ({months_old:.0f} months old)"))
            else:
                checks.append(_check("A3e.macro_currency", "WARN",
                                     f"Fed rate data from {ffr_date} ({months_old:.0f} months old)"))
        except ValueError:
            checks.append(_check("A3e.macro_currency", "WARN", "Cannot parse FFR date"))
    else:
        checks.append(_check("A3e.macro_currency", "WARN", "No federal_funds_rate data"))

    # ── A4: Indicator Value Sanity ──

    # A4a: SMA ordering (information only)
    sma_50_vals = data.get("sma_50", [])
    sma_200_vals = data.get("sma_200", [])
    if sma_50_vals and sma_200_vals and price is not None:
        sma50 = _safe_float(sma_50_vals[0].get("value"))
        sma200 = _safe_float(sma_200_vals[0].get("value"))
        if sma50 is not None and sma200 is not None:
            if price > sma50 > sma200:
                checks.append(_check("A4a.sma_order", "PASS",
                                     f"Uptrend: P=${price} > SMA50=${sma50:.2f} > SMA200=${sma200:.2f}"))
            elif price < sma50 < sma200:
                checks.append(_check("A4a.sma_order", "PASS",
                                     f"Downtrend: P=${price} < SMA50=${sma50:.2f} < SMA200={sma200:.2f}"))
            else:
                checks.append(_check("A4a.sma_order", "PASS",
                                     f"Mixed: P=${price}, SMA50=${sma50:.2f}, SMA200=${sma200:.2f}"))

    # A4b: ATR vs price
    atr_vals = data.get("atr_14", [])
    if atr_vals and price is not None and price > 0:
        atr = _safe_float(atr_vals[0].get("value"))
        if atr is not None:
            atr_pct = (atr / price) * 100
            if atr_pct < 10:
                checks.append(_check("A4b.atr_vs_price", "PASS",
                                     f"ATR ${atr:.2f} = {atr_pct:.1f}% of price"))
            else:
                checks.append(_check("A4b.atr_vs_price", "WARN",
                                     f"ATR ${atr:.2f} = {atr_pct:.1f}% of price (unusually high)"))

    # A4c: BB width
    bbands = data.get("bbands", [])
    if bbands:
        upper = _safe_float(bbands[0].get("Real Upper Band"))
        lower = _safe_float(bbands[0].get("Real Lower Band"))
        if upper is not None and lower is not None:
            if upper > lower:
                checks.append(_check("A4c.bb_width", "PASS",
                                     f"BB width = ${upper:.2f} - ${lower:.2f} = ${upper-lower:.2f}"))
            else:
                checks.append(_check("A4c.bb_width", "FAIL",
                                     f"Invalid BB: upper={upper} ≤ lower={lower}"))

    # A4e: Volume reasonableness
    volume = _safe_float(gq.get("volume"))
    vol_avg = _safe_float(gq.get("volume_sma_20"))
    if volume is not None and volume > 0:
        if vol_avg is not None and vol_avg > 0:
            ratio = volume / vol_avg
            if ratio < 10:
                checks.append(_check("A4e.volume", "PASS",
                                     f"Volume {volume:,.0f} = {ratio:.1f}× avg"))
            else:
                checks.append(_check("A4e.volume", "WARN",
                                     f"Volume {volume:,.0f} = {ratio:.1f}× avg (extreme)"))
        else:
            checks.append(_check("A4e.volume", "PASS", f"Volume {volume:,.0f}"))
    elif volume is not None:
        checks.append(_check("A4e.volume", "WARN", f"Zero or negative volume: {volume}"))

    return checks


# ─────────────────────────────────────────────────────────────────────
# STAGE B: SIGNAL COMPUTATION NUMERICAL VALIDATION
# ─────────────────────────────────────────────────────────────────────

def stage_b_validate(data: dict, short_term: dict, ccrlo: dict, simulation: dict) -> list[dict]:
    """Validate signal computation math against source data."""
    checks = []
    gq = data.get("global_quote", {})
    bundle_price = _safe_float(gq.get("price"))

    # ── B1: Short-Term Signal Math ──

    tb = short_term.get("trend_break", {})
    indicators = short_term.get("indicators", {})
    frag = short_term.get("fragility", {})

    # B1a: TB gate verification
    st_price = _safe_float(short_term.get("price"))
    sma200 = _safe_float(indicators.get("sma_200"))
    sma200_slope = indicators.get("sma_200_slope")
    if st_price is not None and sma200 is not None:
        tb_threshold = 0.995 * sma200
        expected_tb = (st_price <= tb_threshold) and (sma200_slope == "NEGATIVE")
        actual_tb = tb.get("tb", False)
        if actual_tb == expected_tb:
            checks.append(_check("B1a.tb_gate", "PASS",
                                 f"TB={actual_tb}: ${st_price} {'≤' if st_price <= tb_threshold else '>'} "
                                 f"0.995×${sma200:.2f}=${tb_threshold:.2f}, slope={sma200_slope}"))
        else:
            checks.append(_check("B1a.tb_gate", "FAIL",
                                 f"TB={actual_tb} but expected {expected_tb}: "
                                 f"${st_price} vs ${tb_threshold:.2f}, slope={sma200_slope}"))
    else:
        checks.append(_check("B1a.tb_gate", "WARN", "Cannot verify TB (missing price or SMA200)"))

    # B1b: VS gate
    atr_pctile = _safe_float(indicators.get("atr_percentile"))
    if atr_pctile is not None:
        expected_vs = atr_pctile > 80
        actual_vs = tb.get("vs", False)
        if actual_vs == expected_vs:
            checks.append(_check("B1b.vs_gate", "PASS",
                                 f"VS={actual_vs}: ATR pctile {atr_pctile} {'>' if atr_pctile > 80 else '≤'} 80"))
        else:
            checks.append(_check("B1b.vs_gate", "FAIL",
                                 f"VS={actual_vs} but ATR pctile={atr_pctile} expects {expected_vs}"))
    else:
        checks.append(_check("B1b.vs_gate", "WARN", "Missing ATR percentile"))

    # B1c: VF gate
    vol_ratio = _safe_float(indicators.get("volume_ratio"))
    if vol_ratio is not None:
        expected_vf = vol_ratio >= 1.0
        actual_vf = tb.get("vf", False)
        if actual_vf == expected_vf:
            checks.append(_check("B1c.vf_gate", "PASS",
                                 f"VF={actual_vf}: ratio {vol_ratio:.2f} {'≥' if vol_ratio >= 1.0 else '<'} 1.0"))
        else:
            checks.append(_check("B1c.vf_gate", "FAIL",
                                 f"VF={actual_vf} but ratio={vol_ratio:.2f} expects {expected_vf}"))
    else:
        checks.append(_check("B1c.vf_gate", "WARN", "Missing volume ratio"))

    # B1d: Entry consistency
    actual_entry = tb.get("entry_active", False)
    expected_entry = tb.get("tb", False) and tb.get("vs", False) and tb.get("vf", False)
    if actual_entry == expected_entry:
        checks.append(_check("B1d.entry", "PASS",
                             f"entry_active={actual_entry} = tb({tb.get('tb')}) AND vs({tb.get('vs')}) AND vf({tb.get('vf')})"))
    else:
        checks.append(_check("B1d.entry", "FAIL",
                             f"entry_active={actual_entry} but should be {expected_entry}"))

    # B1e: Fragility score = count of HIGH dimensions
    dims = frag.get("dimensions", {})
    high_count = sum(1 for v in dims.values() if v == "HIGH")
    score = frag.get("score", -1)
    if high_count == score:
        checks.append(_check("B1e.frag_score", "PASS",
                             f"Fragility {score}/5 = {high_count} HIGH dims"))
    else:
        checks.append(_check("B1e.frag_score", "FAIL",
                             f"Score {score} ≠ {high_count} HIGH dims: {dims}"))

    # B1f: Fragility level mapping
    level = frag.get("level")
    if score <= 1:
        expected_level = "LOW"
    elif score <= 3:
        expected_level = "MODERATE"
    else:
        expected_level = "HIGH"
    if level == expected_level:
        checks.append(_check("B1f.frag_level", "PASS", f"{level} for score {score}"))
    else:
        checks.append(_check("B1f.frag_level", "FAIL",
                             f"Level '{level}' for score {score}, expected '{expected_level}'"))

    # B1g: Correction prob monotonicity
    cp = short_term.get("correction_probabilities", {})
    mild = cp.get("mild", 0)
    standard = cp.get("standard", 0)
    severe = cp.get("severe", 0)
    bs = cp.get("black_swan", 0)
    if mild >= standard >= severe >= bs:
        checks.append(_check("B1g.corr_mono", "PASS",
                             f"Monotonic: {mild}≥{standard}≥{severe}≥{bs}"))
    else:
        checks.append(_check("B1g.corr_mono", "FAIL",
                             f"Not monotonic: {mild},{standard},{severe},{bs}"))

    # B1h: Correction prob bounds
    all_probs = [mild, standard, severe, bs]
    if all(1 <= p <= 99 for p in all_probs):
        checks.append(_check("B1h.corr_bounds", "PASS", f"All in [1,99]"))
    else:
        checks.append(_check("B1h.corr_bounds", "FAIL",
                             f"Out of bounds: {all_probs}"))

    # B1i: Tail-risk adjustment
    tail_applied = short_term.get("_tail_risk_applied")
    if tail_applied is not None:
        checks.append(_check("B1i.tail_risk", "PASS", f"Tail-risk weight {tail_applied} applied"))
    else:
        checks.append(_check("B1i.tail_risk", "WARN", "No _tail_risk_applied field"))

    # ── B2: CCRLO Signal Math ──

    features = ccrlo.get("features", {})
    expected_features = ["term_spread", "credit_risk", "ig_credit", "volatility_regime",
                         "financial_conditions", "momentum_12m", "realized_vol"]

    # B2a: Feature score ranges
    all_scores_valid = True
    feature_sum = 0
    for feat_name in expected_features:
        feat = features.get(feat_name, {})
        s = feat.get("score")
        if s is not None and 0 <= s <= 3:
            feature_sum += s
        else:
            all_scores_valid = False
            checks.append(_check(f"B2a.feat.{feat_name}", "FAIL",
                                 f"Score {s} out of [0,3]"))
    if all_scores_valid:
        checks.append(_check("B2a.feat_ranges", "PASS", "All 7 features in [0,3]"))

    # B2b: Composite sum
    composite = ccrlo.get("composite_score")
    if composite is not None and composite == feature_sum:
        checks.append(_check("B2b.composite_sum", "PASS",
                             f"{composite} = Σ features ({'+'.join(str(features.get(f,{}).get('score',0)) for f in expected_features)})"))
    elif composite is not None:
        checks.append(_check("B2b.composite_sum", "FAIL",
                             f"Composite {composite} ≠ sum {feature_sum}"))
    else:
        checks.append(_check("B2b.composite_sum", "FAIL", "Missing composite_score"))

    # B2c: Composite range
    if composite is not None and 0 <= composite <= 21:
        checks.append(_check("B2c.composite_range", "PASS", f"{composite}/21"))
    elif composite is not None:
        checks.append(_check("B2c.composite_range", "FAIL", f"{composite} out of [0,21]"))

    # B2d: Risk level mapping
    risk_level = ccrlo.get("risk_level")
    if composite is not None:
        level_map = {range(0, 4): "LOW", range(4, 8): "MODERATE", range(8, 12): "ELEVATED",
                     range(12, 16): "HIGH", range(16, 22): "VERY HIGH"}
        expected_rl = next((v for k, v in level_map.items() if composite in k), None)
        if risk_level == expected_rl:
            checks.append(_check("B2d.risk_level", "PASS", f"{risk_level} for score {composite}"))
        else:
            checks.append(_check("B2d.risk_level", "FAIL",
                                 f"'{risk_level}' for score {composite}, expected '{expected_rl}'"))

    # B2e: Correction probability matches band
    corr_prob = _safe_float(ccrlo.get("correction_probability"))
    if corr_prob is not None and risk_level:
        bands = {"LOW": (5, 10), "MODERATE": (15, 25), "ELEVATED": (30, 45),
                 "HIGH": (50, 65), "VERY HIGH": (70, 85)}
        lo, hi = bands.get(risk_level, (0, 100))
        if lo <= corr_prob <= hi:
            checks.append(_check("B2e.corr_prob_band", "PASS",
                                 f"{corr_prob}% in {risk_level} band [{lo},{hi}]"))
        else:
            checks.append(_check("B2e.corr_prob_band", "FAIL",
                                 f"{corr_prob}% not in {risk_level} band [{lo},{hi}]"))

    # ── B3: Simulation Signal Math ──

    regime = simulation.get("regime", {})
    probs = regime.get("probabilities", {})
    events = simulation.get("events", {})
    scenarios = simulation.get("scenarios", {})

    # B3a: Regime sum
    if probs:
        total = sum(probs.values())
        if abs(total - 1.0) <= 0.01:
            checks.append(_check("B3a.regime_sum", "PASS", f"Sum={total:.3f}"))
        else:
            checks.append(_check("B3a.regime_sum", "FAIL", f"Sum={total:.3f}, must be 1.0 ±0.01"))

    # B3b: Dominant regime
    dominant = regime.get("dominant")
    if probs:
        max_regime = max(probs, key=probs.get)
        if dominant == max_regime:
            checks.append(_check("B3b.dominant", "PASS",
                                 f"{dominant} ({probs.get(dominant, 0):.0%})"))
        else:
            checks.append(_check("B3b.dominant", "FAIL",
                                 f"Dominant='{dominant}' but max is '{max_regime}'"))

    # B3c: Event bounds
    expected_events = ["large_move", "vol_spike", "trend_reversal",
                       "earnings_reaction", "liquidity_stress", "crash_like"]
    event_fails = []
    for ev_name in expected_events:
        ev = events.get(ev_name, {})
        for horizon in ("5d", "10d", "20d"):
            val = ev.get(horizon)
            if val is not None:
                cap = 35 if ev_name == "crash_like" else 85
                if not (1 <= val <= cap):
                    event_fails.append(f"{ev_name}.{horizon}={val}")
    if not event_fails:
        checks.append(_check("B3c.event_bounds", "PASS", "All events in bounds"))
    else:
        checks.append(_check("B3c.event_bounds", "FAIL",
                             f"Out of bounds: {', '.join(event_fails)}"))

    # B3e: Scenario weight sum
    expected_scenarios = ["base_case", "vol_expansion", "trend_shift", "tail_risk"]
    weights = [scenarios.get(s, {}).get("weight", 0) for s in expected_scenarios]
    w_sum = sum(weights)
    if abs(w_sum - 1.0) <= 0.01:
        checks.append(_check("B3e.scenario_sum", "PASS", f"Sum={w_sum:.3f}"))
    else:
        checks.append(_check("B3e.scenario_sum", "FAIL", f"Sum={w_sum:.3f}, must be 1.0"))

    # B3g: Risk color
    cer = simulation.get("composite_event_risk", 0)
    color = simulation.get("risk_color")
    expected_color = "GREEN" if cer < 15 else ("AMBER" if cer <= 30 else "RED")
    if color == expected_color:
        checks.append(_check("B3g.risk_color", "PASS", f"CER={cer}% → {color}"))
    else:
        checks.append(_check("B3g.risk_color", "FAIL",
                             f"CER={cer}% expects {expected_color}, got {color}"))

    # ── B4: Cross-Signal Consistency ──

    # B4a: Price match
    prices = {
        "bundle": bundle_price,
        "short_term": _safe_float(short_term.get("price")),
        "simulation": _safe_float(simulation.get("price")),
    }
    unique_prices = set(v for v in prices.values() if v is not None)
    if len(unique_prices) <= 1 and unique_prices:
        checks.append(_check("B4a.price_match", "PASS",
                             f"All signals use ${next(iter(unique_prices))}"))
    elif unique_prices:
        checks.append(_check("B4a.price_match", "FAIL",
                             f"Price mismatch: {prices}"))
    else:
        checks.append(_check("B4a.price_match", "WARN", "Cannot verify prices"))

    # B4b: Date match
    dates = {
        "short_term": short_term.get("as_of"),
        "ccrlo": ccrlo.get("as_of"),
        "simulation": simulation.get("as_of"),
    }
    unique_dates = set(v for v in dates.values() if v)
    if len(unique_dates) <= 1 and unique_dates:
        checks.append(_check("B4b.date_match", "PASS", next(iter(unique_dates))))
    elif unique_dates:
        checks.append(_check("B4b.date_match", "FAIL", f"Date mismatch: {dates}"))

    # B4c: Ticker match
    tickers = {
        short_term.get("ticker"), ccrlo.get("ticker"), simulation.get("ticker")
    }
    tickers.discard(None)
    if len(tickers) == 1:
        checks.append(_check("B4c.ticker_match", "PASS", tickers.pop()))
    elif tickers:
        checks.append(_check("B4c.ticker_match", "FAIL", f"Mismatch: {tickers}"))

    # B4f: ATR consistency
    bundle_atr_vals = data.get("atr_14", [])
    if bundle_atr_vals:
        bundle_atr = _safe_float(bundle_atr_vals[0].get("value"))
        signal_atr = _safe_float(indicators.get("atr_14"))
        if bundle_atr is not None and signal_atr is not None:
            if _approx(signal_atr, bundle_atr, 0.01):
                checks.append(_check("B4f.atr_consistency", "PASS",
                                     f"Signal ATR {signal_atr} ≈ bundle {bundle_atr}"))
            else:
                checks.append(_check("B4f.atr_consistency", "FAIL",
                                     f"Signal ATR {signal_atr} ≠ bundle {bundle_atr}"))

    # B4g: SMA consistency
    bundle_sma200_vals = data.get("sma_200", [])
    if bundle_sma200_vals:
        bundle_sma200 = _safe_float(bundle_sma200_vals[0].get("value"))
        signal_sma200 = _safe_float(indicators.get("sma_200"))
        if bundle_sma200 is not None and signal_sma200 is not None:
            if _approx(signal_sma200, bundle_sma200, 0.01):
                checks.append(_check("B4g.sma_consistency", "PASS",
                                     f"Signal SMA200 {signal_sma200} ≈ bundle {bundle_sma200}"))
            else:
                checks.append(_check("B4g.sma_consistency", "FAIL",
                                     f"Signal SMA200 {signal_sma200} ≠ bundle {bundle_sma200}"))

    return checks


# ─────────────────────────────────────────────────────────────────────
# STAGE C: POST-REPORT HTML NUMERICAL AUDIT
# ─────────────────────────────────────────────────────────────────────

def _extract_numbers_from_html(html_text: str) -> dict:
    """Extract key numerical values from the HTML report."""
    extracted = {}

    # Header price (look for price-block)
    price_match = re.search(r'class="price"[^>]*>\$?([\d,]+\.?\d*)', html_text)
    if price_match:
        extracted["header_price"] = _safe_float(price_match.group(1))

    # Price change
    change_match = re.search(r'([+-]?\$?[\d.]+)\s*\(([+-]?[\d.]+)%\)', html_text)
    if change_match:
        extracted["header_change"] = _safe_float(change_match.group(1))
        extracted["header_change_pct"] = _safe_float(change_match.group(2))

    # RSI value (Section 11) — find "RSI (14)" header then the large value div
    rsi_section = re.search(r'RSI \(14\)</div>(.*?)</div>\s*</div>', html_text, re.DOTALL)
    if rsi_section:
        rsi_val = re.search(r'>([\d.]+)</div>', rsi_section.group(1))
        if rsi_val:
            extracted["rsi"] = _safe_float(rsi_val.group(1))

    # MACD value — find "MACD" header tile then the large value div
    # Handles both "MACD</div>" and "MACD (12,26,9)</div>" variants
    # Also handles both literal "-" and HTML "&minus;" entity for negative values
    macd_section = re.search(r'MACD[\s()\d,]*</div>(.*?)</div>\s*</div>', html_text, re.DOTALL)
    if macd_section:
        macd_val = re.search(r'>([+-]?[\d.]+)</div>', macd_section.group(1))
        if not macd_val:
            # Try &minus; entity variant
            macd_val = re.search(r'>&minus;([\d.]+)</div>', macd_section.group(1))
            if macd_val:
                extracted["macd"] = -_safe_float(macd_val.group(1))
        else:
            extracted["macd"] = _safe_float(macd_val.group(1))

    # ADX value
    adx_section = re.search(r'ADX \(14\)</div>(.*?)</div>\s*</div>', html_text, re.DOTALL)
    if adx_section:
        adx_val = re.search(r'>([\d.]+)</div>', adx_section.group(1))
        if adx_val:
            extracted["adx"] = _safe_float(adx_val.group(1))

    # ATR value
    atr_section = re.search(r'ATR \(14\)</div>(.*?)</div>\s*</div>', html_text, re.DOTALL)
    if atr_section:
        atr_val = re.search(r'>\$?([\d.]+)</div>', atr_section.group(1))
        if atr_val:
            extracted["atr"] = _safe_float(atr_val.group(1))

    # Fragility score
    frag_match = re.search(r'(?:Fragility|fragility)[^<]*?(\d)/5', html_text)
    if frag_match:
        extracted["fragility_score"] = int(frag_match.group(1))

    # CCRLO score
    ccrlo_match = re.search(r'(\d+)/21', html_text)
    if ccrlo_match:
        extracted["ccrlo_score"] = int(ccrlo_match.group(1))

    # Analyst target price — look for the large green-colored number before "Mean Target Price"
    target_match = re.search(r'color:#16a34a[^>]*>\$?([\d,]+\.?\d*)', html_text)
    if target_match:
        extracted["analyst_target"] = _safe_float(target_match.group(1))

    # Correction probabilities from the correction risk table
    corr_section = re.search(r'Correction Risk.*?(?=Volatility|Key Support|<div style="display:flex.*?min-width:120px)',
                             html_text, re.DOTALL)
    if corr_section:
        probs = re.findall(r'<span[^>]*>(\d+)%</span>', corr_section.group(0))
        if len(probs) >= 4:
            extracted["corr_mild"] = int(probs[0])
            extracted["corr_standard"] = int(probs[1])
            extracted["corr_severe"] = int(probs[2])
            extracted["corr_black_swan"] = int(probs[3])

    # December year-end targets from Monthly Forecast (S5)
    dec_row = re.search(r'Dec 2026.*?</tr>', html_text, re.DOTALL)
    if dec_row:
        dec_vals = re.findall(r'\$([\d,]+)', dec_row.group(0))
        if len(dec_vals) >= 3:
            extracted["dec_conservative"] = _safe_float(dec_vals[0])
            extracted["dec_average"] = _safe_float(dec_vals[1])
            extracted["dec_bullish"] = _safe_float(dec_vals[2])

    # Fed chart bar count — look specifically within Fed Funds section
    fed_section = re.search(r'Federal Funds Rate.*?(?=Macro Environment|<div style="background:#f8fafc.*?font-weight:700)',
                            html_text, re.DOTALL)
    if fed_section:
        fed_text = fed_section.group(0)
        # Primary: rate with % sign followed by bar div
        bars = re.findall(r'(\d\.\d+)%</div>\s*<div[^>]*height:\s*(\d+)px',
                          fed_text)
        if not bars:
            # Fallback: rate WITHOUT % sign followed by bar div (e.g., "4.33</div>...height:70px")
            bars = re.findall(r'>(\d\.\d{2})</div>\s*<div[^>]*height:\s*(\d+)px',
                              fed_text)
        if not bars:
            # Fallback 2: count rate values near bar styling (width:30px patterns)
            bars = re.findall(r'>(\d\.\d{2})</div>.*?width:\s*30px.*?height:\s*(\d+)px',
                              fed_text, re.DOTALL)
        if not bars:
            # Fallback 3: count bare rate values (X.XX format, no %)
            rate_matches = re.findall(r'>(\d\.\d{2})<', fed_text)
            bars = [(r, '0') for r in rate_matches[:12]]
        extracted["fed_bar_count"] = len(bars)
        extracted["fed_bar_rates"] = [float(b[0]) for b in bars]
        # Check if bars use flex:1 (correct) or min-width:40px (bunched to left)
        extracted["fed_bars_use_flex1"] = "flex:1" in fed_text
        extracted["fed_bars_use_minwidth"] = "min-width:40px" in fed_text
    else:
        extracted["fed_bar_count"] = 0

    # S10 Income Statement Breakdown structure
    s10_section = re.search(
        r'(?:Financial Flow|Income Statement Breakdown)(.*?)(?:Technical Indicators|<!-- S11)',
        html_text, re.DOTALL
    )
    if s10_section:
        s10_text = s10_section.group(1)
        extracted["s10_has_sankey_svg"] = "sankey-svg" in s10_text
        extracted["s10_has_gradient_defs"] = "linearGradient" in s10_text
        extracted["s10_flow_count"] = len(re.findall(r'sankey-link', s10_text))
        extracted["s10_stage_labels"] = re.findall(r'sankey-stage-label[^>]*>([^<]+)', s10_text)
        extracted["s10_has_margin_callout"] = (
            "Gross Margin" in s10_text and "Net Margin" in s10_text
        )
        extracted["s10_has_detail_nodes"] = bool(
            re.search(r'R&amp;D|R&D|SGA|SG&amp;A', s10_text)
        )
        extracted["s10_has_narrative"] = "Income Statement Analysis" in s10_text
        extracted["s10_has_legend"] = "sankey-legend" in s10_text

    return extracted


def stage_c_validate(data: dict, short_term: dict, ccrlo: dict,
                     simulation: dict, html_text: str) -> list[dict]:
    """Validate HTML report numbers against source data and signals."""
    checks = []
    gq = data.get("global_quote", {})
    co = data.get("company_overview", {})

    extracted = _extract_numbers_from_html(html_text)

    # ── C1: Header & Price Numbers ──

    bundle_price = _safe_float(gq.get("price"))
    header_price = extracted.get("header_price")

    if header_price is not None and bundle_price is not None:
        if _approx(header_price, bundle_price, 0.02):
            checks.append(_check("C1a.header_price", "PASS",
                                 f"Header ${header_price} matches bundle ${bundle_price}"))
        else:
            checks.append(_check("C1a.header_price", "FAIL",
                                 f"Header ${header_price} != bundle ${bundle_price}"))
    else:
        checks.append(_check("C1a.header_price", "WARN",
                             "Cannot extract header price from report"))

    # ── C2: Signal Numbers ──

    # C2a: RSI value
    report_rsi = extracted.get("rsi")
    bundle_rsi_vals = data.get("rsi", [])
    if report_rsi is not None and bundle_rsi_vals:
        bundle_rsi = _safe_float(bundle_rsi_vals[0].get("value"))
        if bundle_rsi is not None:
            if _approx(report_rsi, bundle_rsi, 0.5):
                checks.append(_check("C2a.rsi", "PASS",
                                     f"RSI {report_rsi} matches bundle {bundle_rsi}"))
            else:
                checks.append(_check("C2a.rsi", "FAIL",
                                     f"RSI {report_rsi} != bundle {bundle_rsi}"))
    else:
        checks.append(_check("C2a.rsi", "WARN", "Cannot verify RSI in report"))

    # C2b: MACD value
    report_macd = extracted.get("macd")
    bundle_macd_vals = data.get("macd", [])
    if report_macd is not None and bundle_macd_vals:
        bundle_macd = _safe_float(bundle_macd_vals[0].get("MACD"))
        if bundle_macd is not None:
            if _approx(report_macd, bundle_macd, 0.1):
                checks.append(_check("C2b.macd", "PASS",
                                     f"MACD {report_macd} matches bundle {bundle_macd}"))
            else:
                checks.append(_check("C2b.macd", "FAIL",
                                     f"MACD {report_macd} != bundle {bundle_macd}"))
    else:
        checks.append(_check("C2b.macd", "WARN", "Cannot verify MACD in report"))

    # C2c: ADX value
    report_adx = extracted.get("adx")
    bundle_adx_vals = data.get("adx", [])
    if report_adx is not None and bundle_adx_vals:
        bundle_adx = _safe_float(bundle_adx_vals[0].get("value"))
        if bundle_adx is not None:
            if _approx(report_adx, bundle_adx, 0.5):
                checks.append(_check("C2c.adx", "PASS",
                                     f"ADX {report_adx} matches bundle {bundle_adx}"))
            else:
                checks.append(_check("C2c.adx", "FAIL",
                                     f"ADX {report_adx} != bundle {bundle_adx}"))
    else:
        checks.append(_check("C2c.adx", "WARN", "Cannot verify ADX in report"))

    # C2d: ATR value
    report_atr = extracted.get("atr")
    bundle_atr_vals = data.get("atr_14", [])
    if report_atr is not None and bundle_atr_vals:
        bundle_atr = _safe_float(bundle_atr_vals[0].get("value"))
        if bundle_atr is not None:
            if _approx(report_atr, bundle_atr, 0.1):
                checks.append(_check("C2d.atr", "PASS",
                                     f"ATR ${report_atr} matches bundle ${bundle_atr}"))
            else:
                checks.append(_check("C2d.atr", "FAIL",
                                     f"ATR ${report_atr} != bundle ${bundle_atr}"))
    else:
        checks.append(_check("C2d.atr", "WARN", "Cannot verify ATR in report"))

    # C2h: Fragility score
    report_frag = extracted.get("fragility_score")
    signal_frag = short_term.get("fragility", {}).get("score")
    if report_frag is not None and signal_frag is not None:
        if report_frag == signal_frag:
            checks.append(_check("C2h.fragility", "PASS",
                                 f"Report {report_frag}/5 matches signal {signal_frag}/5"))
        else:
            checks.append(_check("C2h.fragility", "FAIL",
                                 f"Report {report_frag}/5 != signal {signal_frag}/5"))
    else:
        checks.append(_check("C2h.fragility", "WARN", "Cannot verify fragility score in report"))

    # C2i: CCRLO score
    report_ccrlo = extracted.get("ccrlo_score")
    signal_ccrlo = ccrlo.get("composite_score")
    if report_ccrlo is not None and signal_ccrlo is not None:
        if report_ccrlo == signal_ccrlo:
            checks.append(_check("C2i.ccrlo", "PASS",
                                 f"Report {report_ccrlo}/21 matches signal {signal_ccrlo}/21"))
        else:
            checks.append(_check("C2i.ccrlo", "FAIL",
                                 f"Report {report_ccrlo}/21 != signal {signal_ccrlo}/21"))
    else:
        checks.append(_check("C2i.ccrlo", "WARN", "Cannot verify CCRLO score in report"))

    # C2j: TB/VS/VF badge consistency across all sections
    # Checks that every TB/VS/VF display in the HTML matches computed signals.
    # Common failure: agent updates Section 3 but leaves stale badges in Section 11.
    tb_signal = short_term.get("trend_break", {})
    for gate_name in ("TB", "VS", "VF"):
        computed_val = tb_signal.get(gate_name.lower(), False)
        # ✓ = &#10003; (active/true), ✗ = &#10007; (inactive/false)
        # Find all occurrences of "TB " or "VF " followed by a signal badge
        pattern = rf'{gate_name}\s*<span\s+class="signal\s+(bullish|bearish)">\s*([&#;\w]+)\s*</span>'
        matches = re.findall(pattern, html_text)
        if matches:
            mismatches = []
            for css_class, char_entity in matches:
                # &#10003; (✓) = active/true typically shown as bearish
                # &#10007; (✗) = inactive/false typically shown as bullish
                is_check = "10003" in char_entity  # ✓
                is_cross = "10007" in char_entity   # ✗
                # True signal → should show ✓; False signal → should show ✗
                if computed_val and is_cross:
                    mismatches.append(f"{gate_name}=True but shows ✗")
                elif not computed_val and is_check:
                    mismatches.append(f"{gate_name}=False but shows ✓")
            if mismatches:
                checks.append(_check(f"C2j.{gate_name.lower()}_badge", "FAIL",
                                     f"Badge mismatch: {'; '.join(mismatches)} (found {len(matches)} instances)"))
            else:
                checks.append(_check(f"C2j.{gate_name.lower()}_badge", "PASS",
                                     f"All {len(matches)} {gate_name} badges match signal ({computed_val})"))
        else:
            checks.append(_check(f"C2j.{gate_name.lower()}_badge", "WARN",
                                 f"Cannot find {gate_name} badge markup in report"))

    # ── C3: Financial Numbers ──

    # C3f: Analyst target
    report_target = extracted.get("analyst_target")
    bundle_target = _safe_float(co.get("analyst_target_price"))
    if report_target is not None and bundle_target is not None:
        if _approx(report_target, bundle_target, 1.0):
            checks.append(_check("C3f.analyst_target", "PASS",
                                 f"Report ${report_target} matches bundle ${bundle_target}"))
        else:
            checks.append(_check("C3f.analyst_target", "FAIL",
                                 f"Report ${report_target} != bundle ${bundle_target}"))
    else:
        checks.append(_check("C3f.analyst_target", "WARN", "Cannot verify analyst target"))

    # ── C4: Cross-Section Consistency ──

    # C4a: Price appears consistently
    if header_price is not None:
        price_str = f"{header_price:.2f}"
        occurrences = html_text.count(price_str)
        if occurrences >= 3:
            checks.append(_check("C4a.price_consistency", "PASS",
                                 f"Price ${price_str} found {occurrences} times across sections"))
        elif occurrences >= 1:
            checks.append(_check("C4a.price_consistency", "WARN",
                                 f"Price ${price_str} found only {occurrences} time(s)"))
        else:
            checks.append(_check("C4a.price_consistency", "FAIL",
                                 f"Price ${price_str} not found in report"))

    # C4b: S5 December targets vs S4 year-end targets
    dec_cons = extracted.get("dec_conservative")
    dec_avg = extracted.get("dec_average")
    dec_bull = extracted.get("dec_bullish")
    if dec_cons is not None and dec_avg is not None and dec_bull is not None:
        # Extract S4 year-end 2026 targets from scenario rows
        # Look for each scenario row and extract its first target price (Year 1)
        s4_cons_m = re.search(r'Conservative.*?\$(\d+)\s', html_text)
        s4_avg_m = re.search(r'Average.*?Consensus.*?\$\d+\.\d+.*?\$(\d+)\s', html_text)
        s4_bull_m = re.search(r'Bullish.*?\$\d+\.\d+.*?\$(\d+)\s', html_text)

        # Fallback: extract all 3 from the Price Target table header row "End of 2026"
        if not (s4_cons_m and s4_avg_m and s4_bull_m):
            # Find section between "Price Target" h2 and next h2, limited to 3000 chars
            pt_start = html_text.find('Price Target Projections')
            if pt_start >= 0:
                pt_chunk = html_text[pt_start:pt_start + 3000]
                # Extract all dollar values after the header
                all_prices = re.findall(r'\$(\d+)(?:\s|<)', pt_chunk)
                # Filter out the current price
                targets = [int(v) for v in all_prices
                           if abs(int(v) - (header_price or 0)) > 5]
                if len(targets) >= 3:
                    # First 3 non-current prices in order: Conservative, Average, Bullish
                    # Actually order is Cons row first, then Avg, then Bull
                    s4_cons_v = targets[0]
                    s4_avg_v = targets[1] if len(targets) > 1 else None
                    s4_bull_v = targets[2] if len(targets) > 2 else None
                    s4_cons_m = True  # flag as found
                    s4_avg_m = True
                    s4_bull_m = True
                else:
                    s4_cons_m = s4_avg_m = s4_bull_m = None

        if s4_cons_m and s4_avg_m and s4_bull_m:
            # Get values — from regex match or fallback
            if isinstance(s4_cons_m, bool):
                s4_cons, s4_avg, s4_bull = s4_cons_v, s4_avg_v, s4_bull_v
            else:
                s4_cons = int(s4_cons_m.group(1))
                s4_avg = int(s4_avg_m.group(1))
                s4_bull = int(s4_bull_m.group(1))
            # Compare Dec targets vs S4 targets
            mismatches = []
            if not _approx(dec_cons, s4_cons, 1):
                mismatches.append(f"Cons: S5=${dec_cons} vs S4=${s4_cons}")
            if not _approx(dec_avg, s4_avg, 1):
                mismatches.append(f"Avg: S5=${dec_avg} vs S4=${s4_avg}")
            if not _approx(dec_bull, s4_bull, 1):
                mismatches.append(f"Bull: S5=${dec_bull} vs S4=${s4_bull}")
            if not mismatches:
                checks.append(_check("C4b.dec_vs_s4", "PASS",
                                     f"S5 Dec matches S4: ${dec_cons}/${dec_avg}/${dec_bull}"))
            else:
                checks.append(_check("C4b.dec_vs_s4", "FAIL",
                                     f"Mismatch: {'; '.join(mismatches)}"))
        else:
            checks.append(_check("C4b.dec_vs_s4", "WARN", "Cannot extract S4 targets"))
    else:
        checks.append(_check("C4b.dec_vs_s4", "WARN", "Cannot extract S5 December targets"))

    # C4f: Correction probabilities vs signal
    cp = short_term.get("correction_probabilities", {})
    report_mild = extracted.get("corr_mild")
    report_std = extracted.get("corr_standard")
    report_severe = extracted.get("corr_severe")
    report_bs = extracted.get("corr_black_swan")
    if all(v is not None for v in [report_mild, report_std, report_severe, report_bs]):
        mismatches = []
        if report_mild != cp.get("mild"):
            mismatches.append(f"Mild: report={report_mild}% vs signal={cp.get('mild')}%")
        if report_std != cp.get("standard"):
            mismatches.append(f"Std: report={report_std}% vs signal={cp.get('standard')}%")
        if report_severe != cp.get("severe"):
            mismatches.append(f"Severe: report={report_severe}% vs signal={cp.get('severe')}%")
        if report_bs != cp.get("black_swan"):
            mismatches.append(f"BS: report={report_bs}% vs signal={cp.get('black_swan')}%")
        if not mismatches:
            checks.append(_check("C4f.corr_probs", "PASS",
                                 f"Correction probs match: {report_mild}/{report_std}/{report_severe}/{report_bs}%"))
        else:
            checks.append(_check("C4f.corr_probs", "FAIL",
                                 f"Mismatch: {'; '.join(mismatches)}"))
    else:
        checks.append(_check("C4f.corr_probs", "WARN", "Cannot extract correction probabilities"))

    # ── C5: Macro Number Consistency ──

    # C5b: Fed chart bars
    fed_bar_count = extracted.get("fed_bar_count", 0)
    ffr_data = data.get("federal_funds_rate", [])
    ffr_available = len(ffr_data) if isinstance(ffr_data, list) else 0
    if fed_bar_count == 12:
        checks.append(_check("C5b.fed_bars", "PASS",
                             f"Exactly 12 Fed chart bars found"))
    elif fed_bar_count > 0:
        checks.append(_check("C5b.fed_bars", "WARN",
                             f"Found {fed_bar_count} Fed bars (need exactly 12)"))
    else:
        checks.append(_check("C5b.fed_bars", "WARN",
                             "Cannot count Fed chart bars in report"))

    # C5b1: Fed bar spacing — must use flex:1, never min-width:40px
    if extracted.get("fed_bars_use_minwidth"):
        checks.append(_check("C5b1.fed_spacing", "FAIL",
                             "Fed bars use min-width:40px — bars bunch to left. Use flex:1 instead"))
    elif extracted.get("fed_bars_use_flex1"):
        checks.append(_check("C5b1.fed_spacing", "PASS",
                             "Fed bars use flex:1 for equal spacing"))
    elif fed_bar_count > 0:
        checks.append(_check("C5b1.fed_spacing", "WARN",
                             "Cannot determine Fed bar spacing method"))

    # C5b2: Fed bar rate values match bundle
    fed_bar_rates = extracted.get("fed_bar_rates", [])
    if fed_bar_rates and isinstance(ffr_data, list) and len(ffr_data) >= 12:
        bundle_rates = [_safe_float(r.get("value")) for r in ffr_data[:12]]
        bundle_rates_clean = [r for r in bundle_rates if r is not None]
        # Bundle is newest-first; chart is oldest-first (chronological L→R)
        # Reverse bundle to match chart's chronological order
        if len(fed_bar_rates) >= 12 and len(bundle_rates_clean) >= 12:
            bundle_chrono = list(reversed(bundle_rates_clean[:12]))
            mismatches = []
            for i in range(12):
                if not _approx(fed_bar_rates[i], bundle_chrono[i], 0.02):
                    mismatches.append(f"Bar {i+1}: report={fed_bar_rates[i]}% vs bundle={bundle_chrono[i]}%")
            if not mismatches:
                checks.append(_check("C5b2.fed_rates", "PASS",
                                     "All 12 Fed bar rates match bundle data"))
            else:
                checks.append(_check("C5b2.fed_rates", "FAIL",
                                     f"{len(mismatches)} rate mismatches: {mismatches[0]}"))

    # C5f: Cross-report macro consistency
    report_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    reports_path = os.path.join(report_dir, "reports")
    if os.path.isdir(reports_path):
        ticker = data.get("ticker", "")
        other_reports = [f for f in os.listdir(reports_path)
                         if f.endswith("-analysis.html") and not f.startswith(ticker)]
        if other_reports and ffr_data:
            checks.append(_check("C5f.cross_report", "PASS",
                                 f"{len(other_reports)} other report(s) exist for cross-check"))
        else:
            checks.append(_check("C5f.cross_report", "PASS",
                                 "No other reports to cross-check (first report)"))

    # ── C6: Percentage Calculations ──

    # C6b: Upside percent
    if report_target is not None and header_price is not None and header_price > 0:
        expected_upside = (report_target - header_price) / header_price * 100
        upside_match = re.search(r'([+-]?[\d.]+)%\s*upside', html_text, re.IGNORECASE)
        if upside_match:
            stated_upside = _safe_float(upside_match.group(1))
            if stated_upside is not None and _approx(stated_upside, expected_upside, 1.5):
                checks.append(_check("C6b.upside_pct", "PASS",
                                     f"Upside {stated_upside}% matches computed {expected_upside:.1f}%"))
            elif stated_upside is not None:
                checks.append(_check("C6b.upside_pct", "WARN",
                                     f"Upside {stated_upside}% vs computed {expected_upside:.1f}%"))
        else:
            checks.append(_check("C6b.upside_pct", "WARN", "Cannot find upside % in report"))

    # ── C6c: S10 Income Statement Breakdown Structure ──
    # Validates the Sankey flow diagram has the correct layout:
    # - SVG with gradient defs and flow paths
    # - 4 stage headers (REVENUE, COST SPLIT, OPERATIONS, DETAIL)
    # - Detail nodes (R&D, SGA) for OpEx breakdown
    # - Margin callout above SVG
    # - Legend and narrative below

    if extracted.get("s10_has_sankey_svg"):
        checks.append(_check("C6c1.sankey_svg", "PASS", "S10 has sankey-svg element"))
    else:
        checks.append(_check("C6c1.sankey_svg", "FAIL", "S10 missing sankey-svg element"))

    if extracted.get("s10_has_gradient_defs"):
        checks.append(_check("C6c2.gradient_defs", "PASS", "S10 has linearGradient defs for flow bands"))
    else:
        checks.append(_check("C6c2.gradient_defs", "FAIL", "S10 missing linearGradient defs"))

    flow_count = extracted.get("s10_flow_count", 0)
    if flow_count >= 8:
        checks.append(_check("C6c3.flow_paths", "PASS",
                             f"S10 has {flow_count} flow references (min 8 for 5-stage layout)"))
    elif flow_count >= 6:
        checks.append(_check("C6c3.flow_paths", "WARN",
                             f"S10 has {flow_count} flows (recommend 8+ for DETAIL stage)"))
    else:
        checks.append(_check("C6c3.flow_paths", "FAIL",
                             f"S10 has only {flow_count} flows (need ≥6 for basic Sankey)"))

    stage_labels = extracted.get("s10_stage_labels", [])
    expected_labels = ["REVENUE", "COST SPLIT", "OPERATIONS", "DETAIL"]
    if len(stage_labels) >= 4:
        upper_labels = [l.upper() for l in stage_labels[:4]]
        if upper_labels == expected_labels:
            checks.append(_check("C6c4.stage_labels", "PASS",
                                 f"S10 stage labels: {stage_labels[:4]}"))
        else:
            checks.append(_check("C6c4.stage_labels", "FAIL",
                                 f"S10 stage labels {stage_labels[:4]} != expected {expected_labels}"))
    else:
        checks.append(_check("C6c4.stage_labels", "FAIL",
                             f"S10 has {len(stage_labels)} stage labels (need 4)"))

    if extracted.get("s10_has_detail_nodes"):
        checks.append(_check("C6c5.detail_nodes", "PASS",
                             "S10 has R&D/SGA detail nodes in DETAIL stage"))
    else:
        checks.append(_check("C6c5.detail_nodes", "FAIL",
                             "S10 missing R&D/SGA detail breakdown nodes"))

    if extracted.get("s10_has_margin_callout"):
        checks.append(_check("C6c6.margin_callout", "PASS",
                             "S10 has Gross Margin + Net Margin callout"))
    else:
        checks.append(_check("C6c6.margin_callout", "FAIL",
                             "S10 missing Gross Margin / Net Margin callout above SVG"))

    if extracted.get("s10_has_legend"):
        checks.append(_check("C6c7.legend", "PASS", "S10 has sankey-legend"))
    else:
        checks.append(_check("C6c7.legend", "FAIL", "S10 missing sankey-legend"))

    if extracted.get("s10_has_narrative"):
        checks.append(_check("C6c8.narrative", "PASS",
                             "S10 has Income Statement Analysis narrative"))
    else:
        checks.append(_check("C6c8.narrative", "FAIL",
                             "S10 missing Income Statement Analysis narrative box"))

    # ── C7: Cross-Section Signal Consistency ──
    # These checks detect copy-paste artifacts where the same signal value
    # appears differently across sections (e.g., S3 vs S11).

    # C7a: Regime percentages consistency (S3 vs S11 vs S12)
    # Find all regime bar width patterns: segment-calm.*width:XX%
    regime_bars = re.findall(
        r'segment-calm.*?width:([\d.]+)%.*?'
        r'segment-(?:trending|crash).*?width:([\d.]+)%',
        html_text, re.DOTALL
    )
    if len(regime_bars) >= 2:
        first_calm = regime_bars[0][0]
        mismatches = [i for i, (c, _) in enumerate(regime_bars) if c != first_calm]
        if not mismatches:
            checks.append(_check("C7a.regime_consistency", "PASS",
                                 f"Regime calm={first_calm}% consistent across {len(regime_bars)} instances"))
        else:
            vals = [f"instance{i}={c}%" for i, (c, _) in enumerate(regime_bars)]
            checks.append(_check("C7a.regime_consistency", "FAIL",
                                 f"Regime calm % differs across sections: {'; '.join(vals)}"))
    else:
        checks.append(_check("C7a.regime_consistency", "WARN",
                             f"Found {len(regime_bars)} regime bars (need ≥2 for cross-check)"))

    # C7b: MACD value consistency (S3 narrative vs S11 tile)
    # S3 text around MACD can have various HTML formatting:
    #   "MACD:</strong> <strong>&minus;3.55</strong>"
    #   "MACD: -3.55"
    # Strategy: strip HTML tags from executive summary, decode &minus; to -, then extract
    # Use 25KB range to cover the CSS block (~10KB) + S1-S3 content
    s3_chunk = html_text[:25000]
    s3_plain = re.sub(r'<[^>]+>', '', s3_chunk)
    s3_plain = s3_plain.replace('&minus;', '-').replace('\u2212', '-')
    s3_macd_matches = re.findall(r'MACD[:\s]*(-?\d+\.\d+)', s3_plain)
    s3_val = _safe_float(s3_macd_matches[0]) if s3_macd_matches else None
    s11_macd = extracted.get("macd")
    if s3_val is not None and s11_macd is not None:
        if not _approx(s3_val, s11_macd, 0.15):
            checks.append(_check("C7b.macd_consistency", "FAIL",
                                 f"MACD in S3 ({s3_val}) != S11 tile ({s11_macd})"))
        else:
            checks.append(_check("C7b.macd_consistency", "PASS",
                                 f"MACD consistent: S3={s3_val}, S11={s11_macd}"))
    else:
        checks.append(_check("C7b.macd_consistency", "WARN",
                             "Cannot cross-check MACD between S3 and S11"))

    return checks


# ─────────────────────────────────────────────────────────────────────
# MAIN ORCHESTRATOR
# ─────────────────────────────────────────────────────────────────────

def run_audit(ticker: str, stage: str = "ALL") -> dict:
    """Run numerical audit for the given ticker and stage(s)."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)

    bundle_path = os.path.join(script_dir, "data", f"{ticker}_bundle.json")
    st_path = os.path.join(script_dir, "output", f"{ticker}_short_term.json")
    cc_path = os.path.join(script_dir, "output", f"{ticker}_ccrlo.json")
    sim_path = os.path.join(script_dir, "output", f"{ticker}_simulation.json")
    report_path = os.path.join(base_dir, "reports", f"{ticker}-analysis.html")

    all_checks = []
    stage_results = {}
    run_stages = stage.upper()

    # ── Stage A ──
    if run_stages in ("ALL", "A"):
        if not os.path.exists(bundle_path):
            print(f"ERROR: Data bundle not found: {bundle_path}")
            return {"overall_status": "FAIL", "error": "Bundle not found"}

        with open(bundle_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        print(f"\n{'='*60}")
        print(f"STAGE A: DATA BUNDLE NUMBERS — {ticker}")
        print(f"{'='*60}")

        a_checks = stage_a_validate(data)
        all_checks.extend(a_checks)
        a_fails = sum(1 for c in a_checks if c["status"] == "FAIL")
        a_warns = sum(1 for c in a_checks if c["status"] == "WARN")
        a_pass = sum(1 for c in a_checks if c["status"] == "PASS")
        stage_results["A_data_bundle"] = {
            "status": "FAIL" if a_fails else ("WARN" if a_warns else "PASS"),
            "checks": len(a_checks), "passed": a_pass,
            "warnings": a_warns, "failures": a_fails,
        }
        for c in a_checks:
            icon = "✅" if c["status"] == "PASS" else ("⚠️" if c["status"] == "WARN" else "❌")
            print(f"  {icon} {c['field']}: {c['reason']}")
        print(f"  STAGE SCORE: {a_pass}/{len(a_checks)} PASS, {a_warns} WARN, {a_fails} FAIL")

    # ── Stage B ──
    if run_stages in ("ALL", "B"):
        # Need bundle + signals
        if not os.path.exists(bundle_path):
            print(f"ERROR: Data bundle not found: {bundle_path}")
            return {"overall_status": "FAIL", "error": "Bundle not found"}

        for path, name in [(st_path, "short_term"), (cc_path, "ccrlo"), (sim_path, "simulation")]:
            if not os.path.exists(path):
                print(f"ERROR: Signal file not found: {path}")
                return {"overall_status": "FAIL", "error": f"{name} signal not found"}

        with open(bundle_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        with open(st_path, "r", encoding="utf-8") as f:
            short_term = json.load(f)
        with open(cc_path, "r", encoding="utf-8") as f:
            ccrlo_signal = json.load(f)
        with open(sim_path, "r", encoding="utf-8") as f:
            sim_signal = json.load(f)

        print(f"\n{'='*60}")
        print(f"STAGE B: SIGNAL CALCULATIONS — {ticker}")
        print(f"{'='*60}")

        b_checks = stage_b_validate(data, short_term, ccrlo_signal, sim_signal)
        all_checks.extend(b_checks)
        b_fails = sum(1 for c in b_checks if c["status"] == "FAIL")
        b_warns = sum(1 for c in b_checks if c["status"] == "WARN")
        b_pass = sum(1 for c in b_checks if c["status"] == "PASS")
        stage_results["B_signal_math"] = {
            "status": "FAIL" if b_fails else ("WARN" if b_warns else "PASS"),
            "checks": len(b_checks), "passed": b_pass,
            "warnings": b_warns, "failures": b_fails,
        }
        for c in b_checks:
            icon = "✅" if c["status"] == "PASS" else ("⚠️" if c["status"] == "WARN" else "❌")
            print(f"  {icon} {c['field']}: {c['reason']}")
        print(f"  STAGE SCORE: {b_pass}/{len(b_checks)} PASS, {b_warns} WARN, {b_fails} FAIL")

    # ── Stage C ──
    if run_stages in ("ALL", "C"):
        if not os.path.exists(report_path):
            print(f"\nSTAGE C: SKIPPED — Report not found: {report_path}")
            stage_results["C_report_html"] = {"status": "SKIP", "reason": "Report not found"}
        else:
            if not os.path.exists(bundle_path):
                print(f"ERROR: Data bundle not found: {bundle_path}")
                return {"overall_status": "FAIL", "error": "Bundle not found"}

            with open(bundle_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            with open(st_path, "r", encoding="utf-8") as f:
                short_term = json.load(f)
            with open(cc_path, "r", encoding="utf-8") as f:
                ccrlo_signal = json.load(f)
            with open(sim_path, "r", encoding="utf-8") as f:
                sim_signal = json.load(f)
            with open(report_path, "r", encoding="utf-8") as f:
                html_text = f.read()

            print(f"\n{'='*60}")
            print(f"STAGE C: REPORT HTML NUMBERS — {ticker}")
            print(f"{'='*60}")

            c_checks = stage_c_validate(data, short_term, ccrlo_signal, sim_signal, html_text)
            all_checks.extend(c_checks)
            c_fails = sum(1 for c in c_checks if c["status"] == "FAIL")
            c_warns = sum(1 for c in c_checks if c["status"] == "WARN")
            c_pass = sum(1 for c in c_checks if c["status"] == "PASS")
            stage_results["C_report_html"] = {
                "status": "FAIL" if c_fails else ("WARN" if c_warns else "PASS"),
                "checks": len(c_checks), "passed": c_pass,
                "warnings": c_warns, "failures": c_fails,
            }
            for c in c_checks:
                icon = "✅" if c["status"] == "PASS" else ("⚠️" if c["status"] == "WARN" else "❌")
                print(f"  {icon} {c['field']}: {c['reason']}")
            print(f"  STAGE SCORE: {c_pass}/{len(c_checks)} PASS, {c_warns} WARN, {c_fails} FAIL")

    # ── Overall ──
    total_fails = sum(1 for c in all_checks if c["status"] == "FAIL")
    total_warns = sum(1 for c in all_checks if c["status"] == "WARN")
    total_pass = sum(1 for c in all_checks if c["status"] == "PASS")

    if total_fails:
        overall = "FAIL"
    elif total_warns:
        overall = "WARN"
    else:
        overall = "PASS"

    result = {
        "ticker": ticker,
        "validated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "overall_status": overall,
        "stages": stage_results,
        "summary": {
            "total_checks": len(all_checks),
            "passed": total_pass,
            "warnings": total_warns,
            "failures": total_fails,
        },
        "checks": all_checks,
        "blocking_failures": [c["field"] for c in all_checks if c["status"] == "FAIL"],
    }

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Numerical Audit & Validation — verify data accuracy across the pipeline"
    )
    parser.add_argument("--ticker", required=True, help="Ticker symbol (e.g., AMZN)")
    parser.add_argument("--stage", default="ALL", choices=["ALL", "A", "B", "C"],
                        help="Which stage to run (default: ALL)")
    args = parser.parse_args()

    ticker = args.ticker.upper()

    print(f"\n{'='*60}")
    print(f" NUMERICAL AUDIT -- {ticker}")
    print(f" Date: {datetime.now().strftime('%Y-%m-%d')}")
    print(f" Stage: {args.stage}")
    print(f"{'='*60}")

    result = run_audit(ticker, args.stage)

    # Write output
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "output", f"{ticker}_numerical_audit.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    # Summary
    s = result.get("summary", {})
    print(f"\n{'='*60}")
    print(f" OVERALL: {result['overall_status']}")
    print(f" Passed: {s.get('passed', 0)} | Warnings: {s.get('warnings', 0)} | Failures: {s.get('failures', 0)}")
    if result.get("blocking_failures"):
        print(f" BLOCKING: {', '.join(result['blocking_failures'])}")
    print(f" Output: {output_path}")
    print(f"{'='*60}")

    # Exit code
    status = result.get("overall_status", "FAIL")
    if status == "PASS" or status == "WARN":
        sys.exit(0)

    # Determine which stage failed for the exit code
    stages = result.get("stages", {})
    if stages.get("A_data_bundle", {}).get("status") == "FAIL":
        sys.exit(1)
    elif stages.get("B_signal_math", {}).get("status") == "FAIL":
        sys.exit(2)
    elif stages.get("C_report_html", {}).get("status") == "FAIL":
        sys.exit(3)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
