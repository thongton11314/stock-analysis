#!/usr/bin/env python3
"""
build_portfolio.py — Aggregate all analyzed tickers into a portfolio summary JSON
and generate the portfolio dashboard HTML.

Usage:
    python scripts/build_portfolio.py                     # All tickers from tags_index
    python scripts/build_portfolio.py --tickers AMZN MSFT # Specific tickers only
    python scripts/build_portfolio.py --config portfolio-manager/portfolio_config.json
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from collections import Counter
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
OUTPUT_DIR = SCRIPT_DIR / "output"
DATA_DIR = SCRIPT_DIR / "data"
REPORTS_DIR = ROOT_DIR / "reports"
PORTFOLIO_DIR = ROOT_DIR / "portfolio-manager"
TEMPLATE_PATH = ROOT_DIR / "templates" / "portfolio-template.html"
TAGS_INDEX_PATH = OUTPUT_DIR / "tags_index.json"

# Import the optimizer
from portfolio_optimizer import run_optimizer

SECTOR_COLORS = {
    "technology": "#3b82f6",
    "financials": "#8b5cf6",
    "consumer-cyclical": "#f59e0b",
    "consumer-defensive": "#84cc16",
    "healthcare": "#ef4444",
    "energy": "#78716c",
    "industrials": "#6366f1",
    "communication-services": "#14b8a6",
    "real-estate": "#a855f7",
    "utilities": "#22c55e",
    "basic-materials": "#d97706",
    "crypto": "#f97316",
}

def load_json(path):
    """Load a JSON file, return None if not found."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"  WARN: Could not load {path}: {e}", file=sys.stderr)
        return None


def discover_tickers(explicit_tickers=None, config_path=None):
    """Discover tickers from tags_index, explicit list, or config file."""
    if config_path and os.path.exists(config_path):
        config = load_json(config_path)
        if config and "tickers" in config:
            print(f"Using config: {config_path} ({len(config['tickers'])} tickers)")
            return config["tickers"], config
    if explicit_tickers:
        return explicit_tickers, None
    tags_index = load_json(TAGS_INDEX_PATH)
    if tags_index:
        tickers = list(tags_index.keys())
        print(f"Discovered {len(tickers)} tickers from tags_index.json: {', '.join(tickers)}")
        return tickers, None
    print("ERROR: No tickers found. Run stock analysis first.", file=sys.stderr)
    sys.exit(1)


def load_ticker_data(ticker):
    """Load all signal and data files for a ticker."""
    data = {"ticker": ticker, "available": True, "warnings": []}

    # Data bundle
    bundle = load_json(DATA_DIR / f"{ticker}_bundle.json")
    if not bundle:
        data["warnings"].append("Missing data bundle")
        data["available"] = False
        return data
    data["bundle"] = bundle

    # Price data from bundle
    gq = bundle.get("global_quote", {})
    data["price"] = float(gq.get("price", gq.get("05. price", 0)))
    data["change_pct"] = float(gq.get("change_percent", gq.get("10. change percent", "0").replace("%", "") or 0))

    # Company overview
    co = bundle.get("company_overview", {})
    data["company_name"] = co.get("Name", ticker)
    data["market_cap"] = co.get("MarketCapitalization", "N/A")
    data["sector"] = co.get("Sector", "N/A")

    # Signal files
    short_term = load_json(OUTPUT_DIR / f"{ticker}_short_term.json")
    if short_term:
        data["short_term"] = short_term
    else:
        data["warnings"].append("Missing short_term signal")

    ccrlo = load_json(OUTPUT_DIR / f"{ticker}_ccrlo.json")
    if ccrlo:
        data["ccrlo"] = ccrlo
    else:
        data["warnings"].append("Missing CCRLO signal")

    simulation = load_json(OUTPUT_DIR / f"{ticker}_simulation.json")
    if simulation:
        data["simulation"] = simulation
    else:
        data["warnings"].append("Missing simulation signal")

    tags = load_json(OUTPUT_DIR / f"{ticker}_tags.json")
    if tags:
        data["tags"] = tags
    else:
        data["warnings"].append("Missing tags")

    # Check if report exists
    report_path = REPORTS_DIR / f"{ticker}-analysis.html"
    data["has_report"] = report_path.exists()
    if not data["has_report"]:
        data["warnings"].append("Missing analysis report HTML")

    return data


def compute_portfolio_aggregates(holdings):
    """Compute portfolio-level aggregate metrics."""
    aggregates = {}

    # Fragility
    fragilities = [h["short_term"]["fragility"]["score"] for h in holdings
                   if "short_term" in h and "fragility" in h["short_term"]]
    aggregates["avg_fragility"] = round(sum(fragilities) / len(fragilities), 1) if fragilities else 0
    aggregates["max_fragility"] = max(fragilities) if fragilities else 0

    # CCRLO
    ccrlo_probs = [h["ccrlo"]["correction_probability"] for h in holdings
                   if "ccrlo" in h]
    aggregates["avg_ccrlo"] = round(sum(ccrlo_probs) / len(ccrlo_probs), 1) if ccrlo_probs else 0
    aggregates["max_ccrlo"] = max(ccrlo_probs) if ccrlo_probs else 0

    # Regime distribution
    regimes = [h["simulation"]["regime"]["dominant"] for h in holdings
               if "simulation" in h and "regime" in h["simulation"]]
    regime_counter = Counter(regimes)
    aggregates["dominant_regime"] = regime_counter.most_common(1)[0][0] if regime_counter else "unknown"
    aggregates["regime_distribution"] = dict(regime_counter)

    # Sector allocation
    sectors = []
    for h in holdings:
        if "tags" in h and "tags" in h["tags"]:
            sectors.extend(h["tags"]["tags"].get("sector", []))
    sector_counter = Counter(sectors)
    total = sum(sector_counter.values())
    aggregates["sector_allocation"] = {
        s: {"count": c, "pct": round(c / total * 100, 1)}
        for s, c in sector_counter.most_common()
    } if total > 0 else {}

    # Risk distribution
    risk_levels = []
    for h in holdings:
        if "tags" in h and "tags" in h["tags"]:
            risk_tags = h["tags"]["tags"].get("risk", [])
            # Use the first risk tag as primary risk level
            if risk_tags:
                risk_levels.append(risk_tags[0])
    risk_counter = Counter(risk_levels)
    aggregates["risk_distribution"] = dict(risk_counter)

    # Top event risk
    top_event_ticker = None
    top_event_type = None
    top_event_pct = 0
    for h in holdings:
        if "simulation" not in h or "events" not in h["simulation"]:
            continue
        for event_name, event_data in h["simulation"]["events"].items():
            p20d = event_data.get("20d", 0)
            if p20d > top_event_pct:
                top_event_pct = p20d
                top_event_type = event_name.replace("_", " ").title()
                top_event_ticker = h["ticker"]
    aggregates["top_event"] = {
        "ticker": top_event_ticker or "N/A",
        "type": top_event_type or "N/A",
        "pct": top_event_pct
    }

    # Fragility level label
    avg_f = aggregates["avg_fragility"]
    if avg_f <= 1:
        aggregates["fragility_level"] = "LOW"
    elif avg_f <= 2:
        aggregates["fragility_level"] = "MODERATE"
    elif avg_f <= 3:
        aggregates["fragility_level"] = "ELEVATED"
    else:
        aggregates["fragility_level"] = "HIGH"

    return aggregates


def risk_css_class(level):
    mapping = {"LOW": "risk-low", "MODERATE": "risk-moderate",
               "ELEVATED": "risk-elevated", "HIGH": "risk-high"}
    return mapping.get(level, "")


def signal_badge(value, thresholds=None):
    """Return CSS class for signal badge."""
    if isinstance(value, str):
        v = value.lower()
        if v in ("bullish", "low", "calm"):
            return "bullish"
        if v in ("bearish", "high", "crash_prone", "crash-prone", "stressed"):
            return "bearish"
        return "neutral"
    return "neutral"


def format_market_cap(mc_str):
    """Format market cap to human readable."""
    try:
        mc = float(mc_str)
        if mc >= 1e12:
            return f"${mc/1e12:.2f}T"
        if mc >= 1e9:
            return f"${mc/1e9:.1f}B"
        if mc >= 1e6:
            return f"${mc/1e6:.0f}M"
        return f"${mc:,.0f}"
    except (ValueError, TypeError):
        return str(mc_str)


def build_holdings_rows(holdings):
    """Build HTML table rows for holdings table."""
    rows = []
    for h in holdings:
        ticker = h["ticker"]
        price = h.get("price", 0)
        change_pct = h.get("change_pct", 0)
        change_class = "change-positive" if change_pct >= 0 else "change-negative"
        change_arrow = "+" if change_pct >= 0 else ""

        # Sector
        sector_tags = h.get("tags", {}).get("tags", {}).get("sector", ["N/A"]) if "tags" in h else ["N/A"]
        sector = ", ".join(sector_tags)

        # Market Cap
        mkt_cap = format_market_cap(h.get("market_cap", "N/A"))

        # Risk
        risk_tags = h.get("tags", {}).get("tags", {}).get("risk", []) if "tags" in h else []
        risk_primary = risk_tags[0] if risk_tags else "N/A"
        risk_badge_class = signal_badge(risk_primary)

        # Fragility
        frag_score = h.get("short_term", {}).get("fragility", {}).get("score", "N/A")
        frag_level = h.get("short_term", {}).get("fragility", {}).get("level", "")

        # CCRLO
        ccrlo_score = h.get("ccrlo", {}).get("composite_score", "N/A")
        ccrlo_prob = h.get("ccrlo", {}).get("correction_probability", "N/A")
        ccrlo_level = h.get("ccrlo", {}).get("risk_level", "")

        # Regime
        regime = h.get("simulation", {}).get("regime", {}).get("dominant", "N/A")

        # Short-term signal
        tb = h.get("short_term", {}).get("trend_break", {})
        entry_active = tb.get("entry_active", False)
        st_signal = "RISK-OFF" if entry_active else "NEUTRAL"
        st_badge = "bearish" if entry_active else "neutral"

        # Tags
        primary_tag = h.get("tags", {}).get("primary_tag", "") if "tags" in h else ""

        # Report link
        link_attr = f'href="../reports/{ticker}-analysis.html"' if h.get("has_report") else 'href="#" style="color:#999;cursor:default;"'

        row = f'''                    <tr class="ticker-row">
                        <td><a class="ticker-link" {link_attr}>{ticker}</a></td>
                        <td class="val" data-sortval="{price}">${price:,.2f}</td>
                        <td class="{change_class}" data-sortval="{change_pct}">{change_arrow}{change_pct:.2f}%</td>
                        <td><span class="tag tag-sector">{sector}</span></td>
                        <td data-sortval="{h.get('market_cap', 0)}">{mkt_cap}</td>
                        <td><span class="signal {risk_badge_class}">{risk_primary}</span></td>
                        <td data-sortval="{frag_score}"><span class="signal {signal_badge(frag_level)}">{frag_score}/5 {frag_level}</span></td>
                        <td data-sortval="{ccrlo_prob}"><span class="signal {signal_badge(ccrlo_level)}">{ccrlo_score}/21 ({ccrlo_prob}%)</span></td>
                        <td><span class="signal {signal_badge(regime)}">{regime}</span></td>
                        <td><span class="signal {st_badge}">{st_signal}</span></td>
                        <td style="font-size:0.72em;color:#5a6577;">{primary_tag}</td>
                    </tr>'''
        rows.append(row)
    return "\n".join(rows)


def build_sector_bar(aggregates):
    """Build sector allocation bar segments and legend."""
    sector_alloc = aggregates.get("sector_allocation", {})
    segments = []
    legend_items = []
    for sector, data in sector_alloc.items():
        color = SECTOR_COLORS.get(sector, "#6b7a8d")
        pct = data["pct"]
        segments.append(
            f'<div class="sector-segment" style="flex:{pct};background:{color};">{sector.title()} {pct}%</div>'
        )
        legend_items.append(
            f'<div class="sector-legend-item"><div class="sector-legend-swatch" style="background:{color};"></div>{sector.title()} ({data["count"]})</div>'
        )
    return "\n                    ".join(segments), "\n                    ".join(legend_items)


def build_sector_table(aggregates, holdings):
    """Build sector allocation table rows."""
    sector_alloc = aggregates.get("sector_allocation", {})
    rows = []
    for sector, data in sector_alloc.items():
        tickers_in_sector = []
        for h in holdings:
            h_sectors = h.get("tags", {}).get("tags", {}).get("sector", []) if "tags" in h else []
            if sector in h_sectors:
                tickers_in_sector.append(h["ticker"])
        rows.append(
            f'<tr><td><span class="tag tag-sector">{sector.title()}</span></td>'
            f'<td>{", ".join(tickers_in_sector)}</td>'
            f'<td class="val">{data["count"]}</td>'
            f'<td class="val">{data["pct"]}%</td></tr>'
        )
    return "\n                    ".join(rows)


def build_risk_distribution(aggregates, holdings):
    """Build risk distribution tiles and table."""
    risk_dist = aggregates.get("risk_distribution", {})
    tiles = []
    table_rows = []
    risk_order = ["low-risk", "moderate-risk", "elevated-risk", "high-risk", "crash-prone"]
    tile_colors = {
        "low-risk": "tile-green", "moderate-risk": "tile-amber",
        "elevated-risk": "tile-amber", "high-risk": "tile-red", "crash-prone": "tile-red"
    }

    for risk_level in risk_order:
        count = risk_dist.get(risk_level, 0)
        if count == 0:
            continue
        css = tile_colors.get(risk_level, "")
        tiles.append(
            f'<div class="score-tile {css}"><div class="tile-label">{risk_level.replace("-", " ").title()}</div>'
            f'<div class="tile-value">{count}</div><div class="tile-detail">ticker(s)</div></div>'
        )
        tickers_at_level = []
        for h in holdings:
            h_risks = h.get("tags", {}).get("tags", {}).get("risk", []) if "tags" in h else []
            if risk_level in h_risks:
                tickers_at_level.append(h["ticker"])
        table_rows.append(
            f'<tr><td><span class="signal {signal_badge(risk_level)}">{risk_level.replace("-", " ").title()}</span></td>'
            f'<td>{", ".join(tickers_at_level)}</td><td class="val">{count}</td></tr>'
        )

    return "\n                ".join(tiles), "\n                    ".join(table_rows)


def build_heatmap_rows(holdings):
    """Build fragility heatmap rows."""
    rows = []
    for h in holdings:
        ticker = h["ticker"]
        frag = h.get("short_term", {}).get("fragility", {})
        score = frag.get("score", "N/A")
        dims = frag.get("dimensions", {})

        def dim_cell(val):
            css = "heatmap-low" if val == "LOW" else ("heatmap-high" if val == "HIGH" else "heatmap-med")
            return f'<td class="heatmap-cell {css}">{val}</td>'

        row = f'''<tr>
                        <td class="val">{ticker}</td>
                        <td class="val">{score}/5</td>
                        {dim_cell(dims.get("leverage", "N/A"))}
                        {dim_cell(dims.get("liquidity", "N/A"))}
                        {dim_cell(dims.get("info_risk", "N/A"))}
                        {dim_cell(dims.get("valuation", "N/A"))}
                        {dim_cell(dims.get("momentum", "N/A"))}
                    </tr>'''
        rows.append(row)
    return "\n                    ".join(rows)


def build_signal_cards(holdings):
    """Build signal dashboard cards."""
    cards = []
    for h in holdings:
        ticker = h["ticker"]
        has_report = h.get("has_report", False)
        link = f'../reports/{ticker}-analysis.html' if has_report else '#" style="color:#999;cursor:default;'

        # Short-term
        tb = h.get("short_term", {}).get("trend_break", {})
        tb_active = tb.get("entry_active", False)
        frag = h.get("short_term", {}).get("fragility", {})

        # CCRLO
        ccrlo = h.get("ccrlo", {})

        # Simulation
        sim = h.get("simulation", {})
        regime = sim.get("regime", {}).get("dominant", "N/A")

        # Regime bar
        probs = sim.get("regime", {}).get("probabilities", {})
        calm_pct = round(probs.get("calm", 0) * 100)
        trend_pct = round(probs.get("trending", 0) * 100)
        stress_pct = round(probs.get("stressed", 0) * 100)
        crash_pct = round(probs.get("crash_prone", 0) * 100)

        card = f'''<div class="signal-card">
                    <div class="sc-ticker"><a href="{link}">{ticker}</a></div>
                    <div class="sc-row"><span class="sc-label">Trend-Break</span><span class="signal {"bearish" if tb_active else "bullish"}">{"ACTIVE" if tb_active else "INACTIVE"}</span></div>
                    <div class="sc-row"><span class="sc-label">Fragility</span><span class="signal {signal_badge(frag.get("level", ""))}">{frag.get("score", "?")}/5 {frag.get("level", "")}</span></div>
                    <div class="sc-row"><span class="sc-label">CCRLO</span><span class="signal {signal_badge(ccrlo.get("risk_level", ""))}">{ccrlo.get("composite_score", "?")}/21 ({ccrlo.get("correction_probability", "?")}%)</span></div>
                    <div class="sc-row"><span class="sc-label">Regime</span><span class="signal {signal_badge(regime)}">{regime}</span></div>
                    <div class="regime-bar">
                        <div class="segment segment-calm" style="width:{calm_pct}%"></div>
                        <div class="segment segment-trending" style="width:{trend_pct}%"></div>
                        <div class="segment segment-stressed" style="width:{stress_pct}%"></div>
                        <div class="segment segment-crash" style="width:{crash_pct}%"></div>
                    </div>
                </div>'''
        cards.append(card)
    return "\n                ".join(cards)


def build_portfolio_risk_tiles(aggregates):
    """Build portfolio-level risk metric tiles."""
    avg_f = aggregates["avg_fragility"]
    avg_c = aggregates["avg_ccrlo"]
    top_ev = aggregates["top_event"]

    f_css = "tile-green" if avg_f <= 1 else ("tile-amber" if avg_f <= 2.5 else "tile-red")
    c_css = "tile-green" if avg_c < 20 else ("tile-amber" if avg_c < 40 else "tile-red")
    regime = aggregates["dominant_regime"]
    r_css = "tile-green" if regime == "calm" else ("tile-amber" if regime == "trending" else "tile-red")
    e_css = "tile-green" if top_ev["pct"] < 15 else ("tile-amber" if top_ev["pct"] < 30 else "tile-red")

    tiles = [
        f'<div class="score-tile {f_css}"><div class="tile-label">Avg Fragility</div><div class="tile-value">{avg_f}/5</div><div class="tile-detail">{aggregates["fragility_level"]}</div></div>',
        f'<div class="score-tile {f_css}"><div class="tile-label">Max Fragility</div><div class="tile-value">{aggregates["max_fragility"]}/5</div><div class="tile-detail">Highest single ticker</div></div>',
        f'<div class="score-tile {c_css}"><div class="tile-label">Avg CCRLO</div><div class="tile-value">{avg_c}%</div><div class="tile-detail">6-month correction prob</div></div>',
        f'<div class="score-tile {c_css}"><div class="tile-label">Max CCRLO</div><div class="tile-value">{aggregates["max_ccrlo"]}%</div><div class="tile-detail">Highest single ticker</div></div>',
        f'<div class="score-tile {r_css}"><div class="tile-label">Dominant Regime</div><div class="tile-value">{regime.title()}</div><div class="tile-detail">Most common across holdings</div></div>',
        f'<div class="score-tile {e_css}"><div class="tile-label">Top Event Risk</div><div class="tile-value">{top_ev["pct"]}%</div><div class="tile-detail">{top_ev["ticker"]} — {top_ev["type"]} (20d)</div></div>',
    ]
    return "\n                ".join(tiles)


def build_regime_table(holdings):
    """Build regime distribution table."""
    rows = []
    for h in holdings:
        ticker = h["ticker"]
        sim = h.get("simulation", {})
        regime = sim.get("regime", {})
        dominant = regime.get("dominant", "N/A")
        probs = regime.get("probabilities", {})

        # Find top event
        top_event = "N/A"
        top_pct = 0
        for ev_name, ev_data in sim.get("events", {}).items():
            p = ev_data.get("20d", 0)
            if p > top_pct:
                top_pct = p
                top_event = ev_name.replace("_", " ").title()

        row = f'''<tr>
                        <td class="val">{ticker}</td>
                        <td><span class="signal {signal_badge(dominant)}">{dominant.title()}</span></td>
                        <td>{round(probs.get("calm", 0) * 100)}%</td>
                        <td>{round(probs.get("trending", 0) * 100)}%</td>
                        <td>{round(probs.get("stressed", 0) * 100)}%</td>
                        <td>{round(probs.get("crash_prone", 0) * 100)}%</td>
                        <td>{top_event}</td>
                        <td class="val">{top_pct}%</td>
                    </tr>'''
        rows.append(row)
    return "\n                    ".join(rows)


def build_risk_narrative(holdings, aggregates):
    """Build portfolio risk narrative."""
    n = len(holdings)
    avg_f = aggregates["avg_fragility"]
    avg_c = aggregates["avg_ccrlo"]
    regime = aggregates["dominant_regime"]
    top = aggregates["top_event"]

    parts = []
    parts.append(
        f"The portfolio tracks <strong>{n}</strong> holdings with an average fragility score of "
        f"<strong>{avg_f}/5</strong> ({aggregates['fragility_level']}) and an average 6-month "
        f"correction probability of <strong>{avg_c}%</strong>."
    )

    if regime == "calm":
        parts.append("The dominant market regime across holdings is <strong style=\"color:#16a34a;\">Calm</strong>, suggesting stable near-term conditions.")
    elif regime in ("stressed", "crash_prone"):
        parts.append(f"The dominant regime is <strong style=\"color:#dc2626;\">{regime.replace('_', '-').title()}</strong>, warranting heightened risk monitoring and potential position reduction.")
    else:
        parts.append(f"The dominant regime is <strong style=\"color:#d97706;\">{regime.title()}</strong>, indicating directional momentum but moderate risk.")

    if top["pct"] > 25:
        parts.append(f"<strong style=\"color:#dc2626;\">{top['ticker']}</strong> shows the highest event risk at {top['pct']}% probability of {top['type']} within 20 days — consider hedging or reducing exposure.")
    elif top["pct"] > 15:
        parts.append(f"{top['ticker']} has the highest event risk ({top['type']} at {top['pct']}% over 20 days) — monitor closely.")

    # Sector concentration warning
    sectors = aggregates.get("sector_allocation", {})
    for sector, data in sectors.items():
        if data["pct"] > 50:
            parts.append(f"<strong style=\"color:#d97706;\">Sector concentration warning:</strong> {data['pct']}% of holdings are in {sector.title()}.")
            break

    return " ".join(parts)


def build_optimization_weight_table(opt_result):
    """Build weight comparison table from optimizer output."""
    if not opt_result:
        return ""
    rows = []
    wc = opt_result["optimization"]["weight_comparison"]
    for ticker, data in wc.items():
        diff = data["diff"]
        diff_class = "change-positive" if diff > 0 else "change-negative"
        diff_arrow = "+" if diff > 0 else ""
        bar_width = max(data["optimized"] * 2, 4)  # scale for visual
        rows.append(
            f'<tr><td class="val">{ticker}</td>'
            f'<td><div style="display:flex;align-items:center;gap:8px;">'
            f'<div style="width:{bar_width}px;height:14px;background:linear-gradient(90deg,#2563eb,#3b82f6);border-radius:3px;"></div>'
            f'<span class="val">{data["optimized"]:.1f}%</span></div></td>'
            f'<td>{data["equal"]:.1f}%</td>'
            f'<td class="{diff_class}">{diff_arrow}{diff:.1f}%</td></tr>'
        )
    return "\n                    ".join(rows)


def build_optimization_tiles(opt_result):
    """Build optimization summary tiles."""
    if not opt_result:
        return ""
    rm = opt_result["risk_metrics"]["optimized"]
    imp = opt_result["risk_metrics"]["improvement"]
    rec = opt_result["recommendation"]

    beta_css = "tile-green" if rm["portfolio_beta"] < 1.2 else ("tile-amber" if rm["portfolio_beta"] < 1.6 else "tile-red")
    vol_css = "tile-green" if rm["portfolio_vol_proxy"] < 3 else ("tile-amber" if rm["portfolio_vol_proxy"] < 6 else "tile-red")
    dd_css = "tile-green" if rm["drawdown_risk_score"] < 30 else ("tile-amber" if rm["drawdown_risk_score"] < 60 else "tile-red")
    es_css = "tile-green" if rm["expected_shortfall_proxy"] < 10 else ("tile-amber" if rm["expected_shortfall_proxy"] < 20 else "tile-red")
    conc_css = "tile-green" if rm["max_single_weight"] < 25 else ("tile-amber" if rm["max_single_weight"] < 35 else "tile-red")
    eff_css = "tile-green" if rm["effective_n"] > 3 else ("tile-amber" if rm["effective_n"] > 2 else "tile-red")

    tiles = [
        f'<div class="score-tile {beta_css}"><div class="tile-label">Portfolio Beta</div><div class="tile-value">{rm["portfolio_beta"]}</div><div class="tile-detail">vs market (improvement: {imp["beta"]:+.3f})</div></div>',
        f'<div class="score-tile {vol_css}"><div class="tile-label">Vol Proxy (ATR%)</div><div class="tile-value">{rm["portfolio_vol_proxy"]}%</div><div class="tile-detail">improvement: {imp["vol_proxy"]:+.2f}%</div></div>',
        f'<div class="score-tile {dd_css}"><div class="tile-label">Drawdown Risk</div><div class="tile-value">{rm["drawdown_risk_score"]}/100</div><div class="tile-detail">improvement: {imp["drawdown_score"]:+.1f}</div></div>',
        f'<div class="score-tile {es_css}"><div class="tile-label">Expected Shortfall</div><div class="tile-value">{rm["expected_shortfall_proxy"]:.1f}%</div><div class="tile-detail">tail risk proxy</div></div>',
        f'<div class="score-tile {conc_css}"><div class="tile-label">Max Concentration</div><div class="tile-value">{rm["max_single_weight"]}%</div><div class="tile-detail">single ticker max</div></div>',
        f'<div class="score-tile {eff_css}"><div class="tile-label">Effective-N</div><div class="tile-value">{rm["effective_n"]}</div><div class="tile-detail">diversification measure</div></div>',
    ]
    return "\n                ".join(tiles)


def build_stress_test_table(opt_result):
    """Build stress test results table."""
    if not opt_result:
        return ""
    rows = []
    for st in opt_result["stress_tests"]:
        impact = st["portfolio_impact_pct"]
        sev = st["severity"]
        sev_css = "heatmap-low" if sev == "LOW" else ("heatmap-med" if sev == "MEDIUM" else "heatmap-high")
        impact_css = "change-positive" if impact > 0 else "change-negative"
        # Per-ticker impacts
        ticker_impacts = " | ".join(f'{t}: {v:+.1f}%' for t, v in st["ticker_impacts"].items())
        rows.append(
            f'<tr><td class="val">{st["name"]}</td>'
            f'<td style="font-size:0.78em;color:#5a6577;">{st["description"]}</td>'
            f'<td class="{impact_css} val">{impact:+.1f}%</td>'
            f'<td class="heatmap-cell {sev_css}">{sev}</td>'
            f'<td style="font-size:0.72em;color:#5a6577;">{ticker_impacts}</td></tr>'
        )
    return "\n                    ".join(rows)


def build_rebalancing_section(opt_result):
    """Build rebalancing signals HTML."""
    if not opt_result:
        return ""
    reb = opt_result["rebalancing"]
    urgency = reb["urgency"]
    urg_css = "heatmap-low" if urgency == "NONE" else ("heatmap-med" if urgency in ("LOW", "MEDIUM") else "heatmap-high")

    parts = [f'<div style="margin-bottom:10px;"><strong>Urgency:</strong> <span class="heatmap-cell {urg_css}" style="display:inline-block;">{urgency}</span></div>']

    if reb["triggers"]:
        parts.append('<table><thead><tr><th>Type</th><th>Detail</th><th>Severity</th></tr></thead><tbody>')
        for t in reb["triggers"]:
            sev_css = "heatmap-low" if t["severity"] == "LOW" else ("heatmap-med" if t["severity"] == "MEDIUM" else "heatmap-high")
            parts.append(f'<tr><td class="val">{t["type"]}</td><td>{t["detail"]}</td><td class="heatmap-cell {sev_css}">{t["severity"]}</td></tr>')
        parts.append('</tbody></table>')
    else:
        parts.append('<p style="color:#16a34a;font-size:0.88em;">No rebalancing triggers detected. Portfolio is within all limits.</p>')

    if reb["actions"]:
        parts.append('<div style="margin-top:10px;"><strong>Recommended Actions:</strong></div><ul style="margin:6px 0 0 16px;font-size:0.85em;color:#4a5568;">')
        for a in reb["actions"]:
            parts.append(f'<li>{a}</li>')
        parts.append('</ul>')

    return "\n".join(parts)


def build_recommendation_section(opt_result):
    """Build strategy recommendation HTML."""
    if not opt_result:
        return ""
    rec = opt_result["recommendation"]
    parts = []

    # Framework badge
    parts.append(f'<div style="margin-bottom:12px;"><strong>Framework:</strong> <span class="signal bullish">{rec["recommended_framework"]}</span></div>')
    parts.append(f'<div style="margin-bottom:8px;"><strong>Risk Band:</strong> <span class="signal neutral">{rec["risk_band"].title()}</span> &mdash; <em>{rec["objective"].replace("_", " ").title()}</em></div>')

    # Assessment
    parts.append(f'<div class="narrative-box" style="margin-bottom:10px;"><div class="nb-title">Current Assessment</div><div class="nb-body">{rec["current_assessment"]}</div></div>')

    # Overlays and controls
    if rec["overlays"]:
        parts.append('<div style="margin-bottom:6px;"><strong>Active Overlays:</strong> ' + " ".join(f'<span class="tag tag-profile">{o.replace("_", " ").title()}</span>' for o in rec["overlays"]) + '</div>')

    if rec["hard_controls"]:
        parts.append('<div style="margin-bottom:6px;"><strong>Hard Controls:</strong> ' + " ".join(f'<span class="tag tag-risk elevated-risk">{c.replace("_", " ").title()}</span>' for c in rec["hard_controls"]) + '</div>')

    # Action items
    if rec["action_items"]:
        parts.append('<div style="margin-top:8px;"><strong>Action Items:</strong></div><ul style="margin:4px 0 0 16px;font-size:0.85em;color:#4a5568;">')
        for a in rec["action_items"]:
            parts.append(f'<li>{a}</li>')
        parts.append('</ul>')

    # Warnings
    if rec["warnings"]:
        parts.append('<div style="margin-top:8px;background:#fffbeb;border:1px solid #fde68a;border-radius:6px;padding:10px;">')
        parts.append('<strong style="color:#92400e;">Warnings:</strong><ul style="margin:4px 0 0 16px;font-size:0.82em;color:#78716c;">')
        for w in rec["warnings"]:
            parts.append(f'<li>{w}</li>')
        parts.append('</ul></div>')

    return "\n".join(parts)


def generate_html(holdings, aggregates, config=None, opt_result=None):
    """Generate portfolio HTML iteratively, section by section with mini-audits."""
    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    now = datetime.now()
    report_date = now.strftime("%B %d, %Y")
    report_time = now.strftime("%H:%M UTC")
    portfolio_name = config.get("name", "All Analyzed Tickers") if config else "All Analyzed Tickers"

    # Risk class for summary cards
    f_level = aggregates["fragility_level"]
    f_class = risk_css_class(f_level)
    c_prob = aggregates["avg_ccrlo"]
    c_class = "risk-low" if c_prob < 20 else ("risk-moderate" if c_prob < 40 else ("risk-elevated" if c_prob < 60 else "risk-high"))
    regime = aggregates["dominant_regime"]
    r_class = "risk-low" if regime == "calm" else ("risk-moderate" if regime == "trending" else "risk-high")
    top_ev = aggregates["top_event"]
    e_class = "risk-low" if top_ev["pct"] < 15 else ("risk-moderate" if top_ev["pct"] < 30 else "risk-high")

    # ── Iterative section build with mini-audits ──
    # Each batch defines: name, placeholders→builders, and mini-audit checks.
    batches = [
        {
            "name": "B1: Header + Summary Cards",
            "replacements": {
                "{{REPORT_DATE}}": report_date,
                "{{REPORT_TIME}}": report_time,
                "{{PORTFOLIO_NAME}}": portfolio_name,
                "{{TOTAL_TICKERS}}": str(len(holdings)),
                "{{RISK_BAND}}": config.get("risk_band", "growth").title() if config else "Growth",
                "{{AVG_FRAGILITY}}": str(aggregates["avg_fragility"]),
                "{{AVG_CCRLO}}": str(aggregates["avg_ccrlo"]),
                "{{DOMINANT_REGIME}}": aggregates["dominant_regime"].title(),
                "{{FRAGILITY_RISK_CLASS}}": f_class,
                "{{FRAGILITY_LEVEL}}": f_level,
                "{{CCRLO_RISK_CLASS}}": c_class,
                "{{REGIME_RISK_CLASS}}": r_class,
                "{{EVENT_RISK_CLASS}}": e_class,
                "{{TOP_EVENT_TICKER}}": top_ev["ticker"],
                "{{TOP_EVENT_TYPE}}": top_ev["type"],
                "{{TOP_EVENT_PCT}}": str(top_ev["pct"]),
            },
            "audit": [
                ("Portfolio Dashboard title", lambda h: "Portfolio Dashboard" in h),
                ("Report date rendered", lambda h: report_date in h),
                ("Total tickers count", lambda h: str(len(holdings)) in h),
                ("Summary cards present", lambda h: "summary-card" in h),
                ("Avg fragility value", lambda h: str(aggregates["avg_fragility"]) in h),
                ("Avg CCRLO value", lambda h: ("%s%%" % aggregates["avg_ccrlo"]) in h),
                ("Dominant regime", lambda h: aggregates["dominant_regime"].title() in h),
            ],
        },
        {
            "name": "B2: Holdings Table",
            "replacements": {
                "{{HOLDINGS_ROWS}}": build_holdings_rows(holdings),
            },
            "audit": [
                ("Holdings Overview heading", lambda h: "Holdings Overview" in h),
                ("All tickers in table", lambda h: all(t["ticker"] in h for t in holdings)),
                ("Sortable columns", lambda h: 'class="sortable"' in h),
                ("Ticker links present", lambda h: "ticker-link" in h),
                ("Price values rendered", lambda h: "$" in h and "data-sortval" in h),
                ("No empty rows", lambda h: "{{HOLDINGS_ROWS}}" not in h),
            ],
        },
        {
            "name": "B3: Sector Allocation + Risk Distribution",
            "replacements": {
                "{{SECTOR_BAR_SEGMENTS}}": build_sector_bar(aggregates)[0],
                "{{SECTOR_LEGEND_ITEMS}}": build_sector_bar(aggregates)[1],
                "{{SECTOR_TABLE_ROWS}}": build_sector_table(aggregates, holdings),
                "{{RISK_DISTRIBUTION_TILES}}": build_risk_distribution(aggregates, holdings)[0],
                "{{RISK_TABLE_ROWS}}": build_risk_distribution(aggregates, holdings)[1],
            },
            "audit": [
                ("Sector Allocation heading", lambda h: "Sector Allocation" in h),
                ("Sector bar segments", lambda h: "sector-segment" in h),
                ("Sector legend", lambda h: "sector-legend-item" in h),
                ("Risk Distribution heading", lambda h: "Risk Distribution" in h),
                ("No unreplaced placeholders", lambda h: "{{SECTOR_" not in h and "{{RISK_" not in h),
            ],
        },
        {
            "name": "B4: Risk Heatmap + Signal Dashboard",
            "replacements": {
                "{{HEATMAP_ROWS}}": build_heatmap_rows(holdings),
                "{{SIGNAL_CARDS}}": build_signal_cards(holdings),
            },
            "audit": [
                ("Fragility Risk Heatmap heading", lambda h: "Fragility Risk Heatmap" in h),
                ("Heatmap cells", lambda h: "heatmap-cell" in h),
                ("All tickers in heatmap", lambda h: all(t["ticker"] in h for t in holdings)),
                ("Signal Dashboard heading", lambda h: "Signal Dashboard" in h),
                ("Signal cards rendered", lambda h: "signal-card" in h),
                ("No unreplaced placeholders", lambda h: "{{HEATMAP_" not in h and "{{SIGNAL_" not in h),
            ],
        },
        {
            "name": "B5: Portfolio Risk Metrics + Regime Distribution",
            "replacements": {
                "{{PORTFOLIO_RISK_TILES}}": build_portfolio_risk_tiles(aggregates),
                "{{PORTFOLIO_RISK_NARRATIVE}}": build_risk_narrative(holdings, aggregates),
                "{{REGIME_TABLE_ROWS}}": build_regime_table(holdings),
            },
            "audit": [
                ("Portfolio Risk Metrics heading", lambda h: "Portfolio Risk Metrics" in h),
                ("Score tiles", lambda h: "score-tile" in h),
                ("Risk narrative box", lambda h: "narrative-box" in h),
                ("Market Regime Distribution heading", lambda h: "Market Regime Distribution" in h),
                ("Regime table has all tickers", lambda h: all(t["ticker"] in h for t in holdings)),
                ("No unreplaced placeholders", lambda h: "{{PORTFOLIO_RISK" not in h and "{{REGIME_" not in h),
            ],
        },
        {
            "name": "B6: Portfolio Construction + Optimized Risk",
            "replacements": {
                "{{OPT_WEIGHT_TABLE}}": build_optimization_weight_table(opt_result),
                "{{OPT_METHOD}}": opt_result["optimization"]["method"].replace("_", " ").title() if opt_result else "N/A",
                "{{OPT_OBJECTIVE}}": opt_result["optimization"]["objective"].replace("_", " ").title() if opt_result else "N/A",
                "{{OPT_RISK_TILES}}": build_optimization_tiles(opt_result),
            },
            "audit": [
                ("Portfolio Construction heading", lambda h: "Portfolio Construction" in h),
                ("Optimization method shown", lambda h: "{{OPT_METHOD}}" not in h),
                ("Weight table rendered", lambda h: "{{OPT_WEIGHT_TABLE}}" not in h),
                ("Optimized Risk Metrics heading", lambda h: "Optimized Risk Metrics" in h),
                ("Risk tiles rendered", lambda h: "{{OPT_RISK_TILES}}" not in h),
            ],
        },
        {
            "name": "B7: Stress Tests + Rebalancing + Strategy",
            "replacements": {
                "{{STRESS_TEST_TABLE}}": build_stress_test_table(opt_result),
                "{{REBALANCING_SECTION}}": build_rebalancing_section(opt_result),
                "{{RECOMMENDATION_SECTION}}": build_recommendation_section(opt_result),
            },
            "audit": [
                ("Stress Test Results heading", lambda h: "Stress Test Results" in h),
                ("Stress table rendered", lambda h: "{{STRESS_TEST_TABLE}}" not in h),
                ("Rebalancing Signals heading", lambda h: "Rebalancing Signals" in h),
                ("Rebalancing rendered", lambda h: "{{REBALANCING_SECTION}}" not in h),
                ("Strategy Recommendation heading", lambda h: "Strategy Recommendation" in h),
                ("Recommendation rendered", lambda h: "{{RECOMMENDATION_SECTION}}" not in h),
            ],
        },
    ]

    html = template
    all_passed = True
    batch_results = []

    for batch in batches:
        # Apply replacements for this batch
        for key, value in batch["replacements"].items():
            html = html.replace(key, value)

        # Run mini-audit
        passed = 0
        failed = 0
        failures = []
        for check_name, check_fn in batch["audit"]:
            try:
                if check_fn(html):
                    passed += 1
                else:
                    failed += 1
                    failures.append(check_name)
            except Exception as e:
                failed += 1
                failures.append(f"{check_name} (error: {e})")

        status = "PASS" if failed == 0 else "FAIL"
        if failed > 0:
            all_passed = False

        batch_results.append({
            "batch": batch["name"],
            "status": status,
            "passed": passed,
            "failed": failed,
            "failures": failures,
        })

        icon = "\u2705" if failed == 0 else "\u274c"
        print(f"  {icon} {batch['name']}: {passed}/{passed + failed} checks", end="")
        if failures:
            print(f" — FAILED: {', '.join(failures)}")
        else:
            print()

    # Final check: no unreplaced template placeholders at all
    remaining = re.findall(r'\{\{[A-Z_]+\}\}', html)
    if remaining:
        all_passed = False
        print(f"  \u274c Unreplaced placeholders: {remaining}")
    else:
        print(f"  \u2705 No unreplaced placeholders")

    return html, all_passed, batch_results


def main():
    parser = argparse.ArgumentParser(description="Build portfolio dashboard")
    parser.add_argument("--tickers", nargs="+", help="Specific tickers to include")
    parser.add_argument("--config", help="Path to portfolio_config.json")
    parser.add_argument("--risk-band", default="growth",
                        choices=["conservative", "moderate", "growth", "aggressive"],
                        help="Risk band for optimization (default: growth)")
    parser.add_argument("--output", default=str(PORTFOLIO_DIR / "portfolio.html"),
                        help="Output HTML path")
    parser.add_argument("--summary-only", action="store_true",
                        help="Only generate portfolio_summary.json, skip HTML")
    args = parser.parse_args()

    print("=" * 60)
    print("PORTFOLIO BUILDER")
    print("=" * 60)

    # Discover tickers
    tickers, config = discover_tickers(args.tickers, args.config)

    # Load all ticker data
    print(f"\nLoading data for {len(tickers)} tickers...")
    holdings = []
    for ticker in tickers:
        print(f"  Loading {ticker}...", end=" ")
        data = load_ticker_data(ticker)
        if data["warnings"]:
            print(f"WARN: {', '.join(data['warnings'])}")
        else:
            print("OK")
        holdings.append(data)

    # Filter to available holdings
    available = [h for h in holdings if h.get("available", False)]
    print(f"\n{len(available)}/{len(holdings)} tickers fully available")

    if not available:
        print("ERROR: No tickers with complete data. Run stock analysis first.", file=sys.stderr)
        sys.exit(1)

    # Compute aggregates
    print("\nComputing portfolio aggregates...")
    aggregates = compute_portfolio_aggregates(available)

    # Run portfolio optimizer
    risk_band = args.risk_band
    if config and "risk_band" in config:
        risk_band = config["risk_band"]
    print(f"\nRunning portfolio optimizer (risk band: {risk_band})...")
    ticker_list = [h["ticker"] for h in available]
    opt_result = run_optimizer(ticker_list, risk_band, config=config)
    if "error" in opt_result:
        print(f"  WARN: Optimizer failed: {opt_result['error']}")
        opt_result = None
    else:
        opt_path = OUTPUT_DIR / "portfolio_optimization.json"
        opt_path.write_text(json.dumps(opt_result, indent=2), encoding="utf-8")
        print(f"  Saved: {opt_path}")

    # Save portfolio summary JSON
    summary = {
        "generated_at": datetime.now().isoformat(),
        "total_tickers": len(available),
        "tickers": [h["ticker"] for h in available],
        "aggregates": aggregates,
        "holdings": [
            {
                "ticker": h["ticker"],
                "price": h.get("price", 0),
                "change_pct": h.get("change_pct", 0),
                "company_name": h.get("company_name", ""),
                "market_cap": h.get("market_cap", "N/A"),
                "sector": h.get("tags", {}).get("tags", {}).get("sector", []) if "tags" in h else [],
                "risk": h.get("tags", {}).get("tags", {}).get("risk", []) if "tags" in h else [],
                "fragility_score": h.get("short_term", {}).get("fragility", {}).get("score"),
                "fragility_level": h.get("short_term", {}).get("fragility", {}).get("level"),
                "ccrlo_score": h.get("ccrlo", {}).get("composite_score"),
                "ccrlo_probability": h.get("ccrlo", {}).get("correction_probability"),
                "ccrlo_level": h.get("ccrlo", {}).get("risk_level"),
                "regime": h.get("simulation", {}).get("regime", {}).get("dominant"),
                "primary_tag": h.get("tags", {}).get("primary_tag") if "tags" in h else None,
                "has_report": h.get("has_report", False),
            }
            for h in available
        ]
    }

    summary_path = OUTPUT_DIR / "portfolio_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"  Saved: {summary_path}")

    if args.summary_only:
        print("\nSummary-only mode. Skipping HTML generation.")
        return

    # Generate HTML (iterative, section-by-section with mini-audits)
    print("\nGenerating portfolio HTML (iterative build)...")
    html, build_passed, batch_results = generate_html(available, aggregates, config, opt_result)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    print(f"\n  Saved: {output_path}")

    build_status = "PASS" if build_passed else "FAIL"
    total_checks = sum(b["passed"] + b["failed"] for b in batch_results)
    total_passed = sum(b["passed"] for b in batch_results)
    print(f"  Build mini-audit: {build_status} — {total_passed}/{total_checks} checks")

    # Run full post-build audit
    print("\nRunning full post-build audit...")
    from audit_portfolio import run_full_audit
    audit_result = run_full_audit(str(output_path))
    audit_status = audit_result["overall"]
    print(f"  Full audit: {audit_status} — {audit_result['passed']}/{audit_result['total']} checks")

    if audit_result["failed"] > 0:
        for c in audit_result["checks"]:
            if c["status"] == "FAIL":
                print(f"    \u274c {c['code']}: {c['description']}")

    print("\n" + "=" * 60)
    print(f"PORTFOLIO DASHBOARD COMPLETE — {len(available)} tickers")
    print(f"  HTML:  {output_path}")
    print(f"  JSON:  {summary_path}")
    print(f"  Build: {build_status} ({total_passed}/{total_checks})")
    print(f"  Audit: {audit_status} ({audit_result['passed']}/{audit_result['total']})")
    print("=" * 60)


if __name__ == "__main__":
    main()
