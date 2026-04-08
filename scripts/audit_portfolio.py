#!/usr/bin/env python3
"""
audit_portfolio.py — Comprehensive portfolio dashboard audit.

8 audit layers:
  L1: Structural completeness (all 17 sections present)
  L2: Data accuracy (prices, signals, tags match source JSONs)
  L3: Link integrity (all ticker links -> existing reports)
  L4: Aggregate metrics (totals, averages match computed values)
  L5: Styling compliance (flexbox-only, print CSS, color palette)
  L6: Layout & alignment (card structure, consistent patterns)
  L7: Text & content quality (no placeholders, no broken entities)
  L8: Numerical accuracy (prices, scores, percentages traceable to source)

Usage:
    python scripts/audit_portfolio.py
    python scripts/audit_portfolio.py --html portfolio-manager/portfolio.html
    python scripts/audit_portfolio.py --json
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
OUTPUT_DIR = SCRIPT_DIR / "output"
DATA_DIR = SCRIPT_DIR / "data"
REPORTS_DIR = ROOT_DIR / "reports"
PORTFOLIO_DIR = ROOT_DIR / "portfolio-manager"
TAGS_INDEX_PATH = OUTPUT_DIR / "tags_index.json"


def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


class AuditResult:
    def __init__(self):
        self.checks = []
        self.passed = 0
        self.failed = 0
        self.warnings = 0

    def check(self, layer, code, description, passed, detail=""):
        status = "PASS" if passed else "FAIL"
        self.checks.append({
            "layer": layer, "code": code,
            "description": description, "status": status, "detail": detail
        })
        if passed:
            self.passed += 1
        else:
            self.failed += 1

    def warn(self, layer, code, description, detail=""):
        self.checks.append({
            "layer": layer, "code": code,
            "description": description, "status": "WARN", "detail": detail
        })
        self.warnings += 1

    @property
    def total(self):
        return self.passed + self.failed

    @property
    def overall(self):
        return "PASS" if self.failed == 0 else "FAIL"

    def to_dict(self):
        return {
            "overall": self.overall,
            "passed": self.passed,
            "failed": self.failed,
            "warnings": self.warnings,
            "total": self.total,
            "checks": self.checks,
        }


# ===================================================================
#  L1: STRUCTURAL COMPLETENESS
# ===================================================================
def audit_l1_structure(html, result):
    """All sections must be present."""
    sections = [
        ("L1.1", "Export Bar", "export-bar"),
        ("L1.2", "Portfolio Header", "Portfolio Dashboard"),
        ("L1.3", "Summary Cards", "summary-card"),
        ("L1.4", "Holdings Table", "Holdings Overview"),
        ("L1.5", "Sector Allocation", "Sector Allocation"),
        ("L1.6", "Risk Distribution", "Risk Distribution"),
        ("L1.7", "Risk Heatmap", "Fragility Risk Heatmap"),
        ("L1.8", "Signal Dashboard", "Signal Dashboard"),
        ("L1.9", "Portfolio Risk Metrics", "Portfolio Risk Metrics"),
        ("L1.10", "Regime Distribution", "Market Regime Distribution"),
        ("L1.11", "Portfolio Construction", "Portfolio Construction"),
        ("L1.12", "Optimized Risk Metrics", "Optimized Risk Metrics"),
        ("L1.13", "Stress Tests", "Stress Test Results"),
        ("L1.14", "Rebalancing Signals", "Rebalancing Signals"),
        ("L1.15", "Strategy Recommendation", "Strategy Recommendation"),
        ("L1.16", "Disclaimer", "Disclaimer"),
        ("L1.17", "Timestamp", 'class="timestamp"'),
    ]
    for code, name, marker in sections:
        result.check("L1", code, f"{name} present", marker in html)

    card_count = html.count("summary-card")
    result.check("L1", "L1.18", f"Summary cards >= 5 (found {card_count})", card_count >= 5)

    h2_count = len(re.findall(r'<h2[^>]*>', html))
    result.check("L1", "L1.19", f"Section headings >= 10 (found {h2_count})", h2_count >= 10)


# ===================================================================
#  L2: DATA ACCURACY
# ===================================================================
def audit_l2_data_accuracy(html, result):
    """Every ticker's signal values in HTML must match source JSONs."""
    tags_index = load_json(TAGS_INDEX_PATH)
    if not tags_index:
        result.warn("L2", "L2.0", "Cannot run L2: tags_index.json not found")
        return

    for ticker in tags_index:
        result.check("L2", f"L2.1-{ticker}", f"{ticker} in holdings table", ticker in html)

        report_link = f"../reports/{ticker}-analysis.html"
        result.check("L2", f"L2.link-{ticker}", f"{ticker} links to report", report_link in html)

        short_term = load_json(OUTPUT_DIR / f"{ticker}_short_term.json")
        ccrlo = load_json(OUTPUT_DIR / f"{ticker}_ccrlo.json")
        tags = load_json(OUTPUT_DIR / f"{ticker}_tags.json")
        simulation = load_json(OUTPUT_DIR / f"{ticker}_simulation.json")

        if short_term:
            frag = str(short_term.get("fragility", {}).get("score", ""))
            if frag:
                result.check("L2", f"L2.frag-{ticker}",
                              f"{ticker} fragility {frag}/5", f"{frag}/5" in html)

        if ccrlo:
            cs = str(ccrlo.get("composite_score", ""))
            if cs:
                result.check("L2", f"L2.ccrlo-{ticker}",
                              f"{ticker} CCRLO {cs}/21", f"{cs}/21" in html)

        if tags:
            primary = tags.get("primary_tag", "")
            if primary:
                result.check("L2", f"L2.tag-{ticker}",
                              f"{ticker} tag '{primary}'", primary in html)

        if simulation:
            regime = simulation.get("regime", {}).get("dominant", "")
            if regime:
                result.check("L2", f"L2.regime-{ticker}",
                              f"{ticker} regime '{regime}'",
                              regime in html or regime.title() in html)


# ===================================================================
#  L3: LINK INTEGRITY
# ===================================================================
def audit_l3_links(html, result):
    """All report links must point to existing files."""
    links = re.findall(r'href="(\.\./reports/[A-Z]+-analysis\.html)"', html)
    result.check("L3", "L3.1", f"Report links found ({len(links)})", len(links) > 0)

    for link in set(links):
        # link is like ../reports/AMZN-analysis.html — resolve from portfolio-manager/
        filename = link.split("/")[-1]
        result.check("L3", f"L3.2-{filename}", f"File exists: {filename}",
                      (REPORTS_DIR / filename).exists())

    result.check("L3", "L3.3", "Export button onclick", "exportToPDF()" in html)

    disabled_count = len(re.findall(r'href="#"[^>]*style="color:#999', html))
    real_hash = len(re.findall(r'href="#"', html))
    result.check("L3", "L3.4", f"All # links are disabled ({disabled_count}/{real_hash})",
                  disabled_count == real_hash or real_hash == 0)


# ===================================================================
#  L4: AGGREGATE METRICS
# ===================================================================
def audit_l4_aggregates(html, result):
    """Aggregate values in HTML must match computed values."""
    summary = load_json(OUTPUT_DIR / "portfolio_summary.json")
    if not summary:
        result.warn("L4", "L4.0", "Cannot run L4: portfolio_summary.json not found")
        return

    agg = summary.get("aggregates", {})

    total = str(summary.get("total_tickers", 0))
    result.check("L4", "L4.1", f"Total tickers ({total})", total in html)

    avg_f = str(agg.get("avg_fragility", ""))
    if avg_f:
        result.check("L4", "L4.2", f"Avg fragility ({avg_f})", avg_f in html)

    avg_c = str(agg.get("avg_ccrlo", ""))
    if avg_c:
        result.check("L4", "L4.3", f"Avg CCRLO ({avg_c}%)", f"{avg_c}%" in html)

    regime = agg.get("dominant_regime", "")
    if regime:
        result.check("L4", "L4.4", f"Dominant regime ({regime})", regime.title() in html)

    opt = load_json(OUTPUT_DIR / "portfolio_optimization.json")
    if opt:
        method = opt.get("optimization", {}).get("method", "").replace("_", " ").title()
        if method:
            result.check("L4", "L4.5", f"Optimizer method ({method})", method in html)

        st_count = len(opt.get("stress_tests", []))
        result.check("L4", "L4.6", f"Stress tests ({st_count} scenarios)",
                      st_count > 0 and "Stress Test Results" in html)

        fw = opt.get("recommendation", {}).get("recommended_framework", "")
        if fw:
            result.check("L4", "L4.7", f"Strategy framework", fw in html)

        weights = opt.get("optimization", {}).get("final_weights", {})
        if weights:
            total_w = sum(weights.values())
            result.check("L4", "L4.8", f"Weights sum ~100% ({total_w*100:.1f}%)",
                          99.0 <= total_w * 100 <= 101.0)
    else:
        result.warn("L4", "L4.5", "portfolio_optimization.json not found")


# ===================================================================
#  L5: STYLING COMPLIANCE
# ===================================================================
def audit_l5_styling(html, result):
    """CSS compliance: flexbox, print CSS, colors, fonts."""
    result.check("L5", "L5.1", "No CSS Grid", "display: grid" not in html and "display:grid" not in html)
    result.check("L5", "L5.2", "@page A4 landscape", "size: A4 landscape" in html)
    result.check("L5", "L5.3", "page-break-inside: avoid", "page-break-inside: avoid" in html)
    result.check("L5", "L5.4", "Signal badges (.signal.bullish/.bearish)",
                  ".signal.bullish" in html and ".signal.bearish" in html)
    result.check("L5", "L5.5", "Tag badges (.tag-profile/.tag-sector)",
                  ".tag-profile" in html and ".tag-sector" in html)
    result.check("L5", "L5.6", "Export hidden in print", "display: none !important" in html)
    result.check("L5", "L5.7", "print-color-adjust: exact", "print-color-adjust: exact" in html)
    result.check("L5", "L5.8", "Segoe UI font", "Segoe UI" in html)
    result.check("L5", "L5.9", "13px base font", "font-size: 13px" in html)
    result.check("L5", "L5.10", "Background #f4f6f9", "#f4f6f9" in html)
    result.check("L5", "L5.11", "Header navy #1b2a4a", "#1b2a4a" in html)
    result.check("L5", "L5.12", "Card bg #fff", "background: #fff" in html)
    result.check("L5", "L5.13", "Green bullish #16a34a", "#16a34a" in html)
    result.check("L5", "L5.14", "Red bearish #dc2626", "#dc2626" in html)
    result.check("L5", "L5.15", "Amber neutral #d97706", "#d97706" in html)


# ===================================================================
#  L6: LAYOUT & ALIGNMENT
# ===================================================================
def audit_l6_layout(html, result):
    """Card structure, flex layout, alignment."""
    result.check("L6", "L6.1", "Container 1140px", "max-width: 1140px" in html)

    flex_count = html.count("display: flex")
    result.check("L6", "L6.2", f"Flexbox ({flex_count} uses)", flex_count >= 10)

    result.check("L6", "L6.3", "Card border-radius 6px", "border-radius: 6px" in html)
    result.check("L6", "L6.4", "Card border #dde3ed", "#dde3ed" in html)
    result.check("L6", "L6.5", "H2 border-bottom", "border-bottom: 2px solid #e8ecf3" in html)
    result.check("L6", "L6.6", "Table border-collapse", "border-collapse: collapse" in html)

    result.check("L6", "L6.7", "Score tile border-left",
                  "border-left: 3px solid" in html or "border-left: 4px solid" in html)

    grid_divs = len(re.findall(r'class="grid"', html))
    result.check("L6", "L6.8", f"Grid sections ({grid_divs} found)", grid_divs >= 5)

    full_width = html.count("full-width")
    result.check("L6", "L6.9", f"Full-width cards ({full_width})", full_width >= 5)

    result.check("L6", "L6.10", "Disclaimer border #f59e0b", "#f59e0b" in html)


# ===================================================================
#  L7: TEXT & CONTENT QUALITY
# ===================================================================
def audit_l7_text(html, result):
    """No broken content, no template remnants."""
    placeholders = re.findall(r'\{\{[A-Z_]+\}\}', html)
    result.check("L7", "L7.1", f"No {{{{ }}}} placeholders ({len(placeholders)})",
                  len(placeholders) == 0,
                  detail=str(placeholders[:5]) if placeholders else "")

    nan_outside = re.findall(r'(?<![a-zA-Z])NaN(?![a-zA-Z])', html)
    result.check("L7", "L7.2", "No NaN values", len(nan_outside) == 0)

    none_in_content = len(re.findall(r'>None<', html))
    result.check("L7", "L7.3", f"No Python None in content ({none_in_content})", none_in_content == 0)

    empty_tds = len(re.findall(r'<td[^>]*>\s*</td>', html))
    result.check("L7", "L7.4", f"Empty cells < 5 ({empty_tds})", empty_tds < 5)

    result.check("L7", "L7.5", "DOCTYPE present", "<!DOCTYPE html>" in html)
    result.check("L7", "L7.6", "HTML lang=en", 'lang="en"' in html)
    result.check("L7", "L7.7", "Title tag", "<title>" in html and "</title>" in html)

    ts_match = re.search(r'generated on (\w+ \d+, \d{4})', html)
    result.check("L7", "L7.8", "Timestamp date", ts_match is not None,
                  detail=ts_match.group(1) if ts_match else "not found")


# ===================================================================
#  L8: NUMERICAL ACCURACY
# ===================================================================
def audit_l8_numbers(html, result):
    """Prices, scores, percentages must trace to source data."""
    tags_index = load_json(TAGS_INDEX_PATH)
    if not tags_index:
        result.warn("L8", "L8.0", "Cannot run L8: tags_index.json not found")
        return

    for ticker in tags_index:
        bundle = load_json(DATA_DIR / f"{ticker}_bundle.json")
        if not bundle:
            continue

        gq = bundle.get("global_quote", {})
        price = gq.get("price", 0)

        if price:
            price_str = f"${float(price):,.2f}"
            result.check("L8", f"L8.price-{ticker}",
                          f"{ticker} price {price_str}", price_str in html)

        change_pct = gq.get("change_percent", 0)
        if change_pct:
            pct_str = f"{abs(float(change_pct)):.2f}%"
            result.check("L8", f"L8.chg-{ticker}",
                          f"{ticker} change {pct_str}", pct_str in html)

    opt = load_json(OUTPUT_DIR / "portfolio_optimization.json")
    if opt:
        wc = opt.get("optimization", {}).get("weight_comparison", {})
        for ticker, data in wc.items():
            w_str = f'{data["optimized"]:.1f}%'
            result.check("L8", f"L8.wt-{ticker}",
                          f"{ticker} weight {w_str}", w_str in html)

        for st in opt.get("stress_tests", [])[:2]:
            impact = f'{st["portfolio_impact_pct"]:+.1f}%'
            result.check("L8", f"L8.stress-{st['name'][:15]}",
                          f"Stress impact {impact}", impact in html)

        rm = opt.get("risk_metrics", {}).get("optimized", {})
        beta = rm.get("portfolio_beta")
        if beta:
            result.check("L8", "L8.beta", f"Portfolio beta {beta}", str(beta) in html)

        dd = rm.get("drawdown_risk_score")
        if dd:
            result.check("L8", "L8.drawdown", f"Drawdown score {dd}", str(dd) in html)


# ===================================================================
#  RUN FULL AUDIT (callable from build_portfolio.py)
# ===================================================================
def run_full_audit(html_path):
    """Run all 8 layers, return results dict."""
    html = Path(html_path).read_text(encoding="utf-8")
    result = AuditResult()
    audit_l1_structure(html, result)
    audit_l2_data_accuracy(html, result)
    audit_l3_links(html, result)
    audit_l4_aggregates(html, result)
    audit_l5_styling(html, result)
    audit_l6_layout(html, result)
    audit_l7_text(html, result)
    audit_l8_numbers(html, result)
    return result.to_dict()


# ===================================================================
#  CLI ENTRY POINT
# ===================================================================
def main():
    parser = argparse.ArgumentParser(description="Audit portfolio dashboard (8 layers)")
    parser.add_argument("--html", default=str(PORTFOLIO_DIR / "portfolio.html"))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    html_path = Path(args.html)
    if not html_path.exists():
        print(f"ERROR: {html_path} not found. Run build_portfolio.py first.", file=sys.stderr)
        sys.exit(1)

    html = html_path.read_text(encoding="utf-8")
    result = AuditResult()

    print("=" * 60)
    print("PORTFOLIO AUDIT — 8-Layer Comprehensive")
    print(f"  File: {html_path}")
    print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    layers = [
        ("L1", "Structural Completeness", audit_l1_structure),
        ("L2", "Data Accuracy", audit_l2_data_accuracy),
        ("L3", "Link Integrity", audit_l3_links),
        ("L4", "Aggregate Metrics", audit_l4_aggregates),
        ("L5", "Styling Compliance", audit_l5_styling),
        ("L6", "Layout & Alignment", audit_l6_layout),
        ("L7", "Text & Content Quality", audit_l7_text),
        ("L8", "Numerical Accuracy", audit_l8_numbers),
    ]

    for layer_id, layer_name, layer_fn in layers:
        layer_fn(html, result)
        checks = [c for c in result.checks if c["layer"] == layer_id]
        lp = sum(1 for c in checks if c["status"] == "PASS")
        lf = sum(1 for c in checks if c["status"] == "FAIL")
        lw = sum(1 for c in checks if c["status"] == "WARN")
        lt = lp + lf
        icon = "\u2705" if lf == 0 else "\u274c"
        ws = f" ({lw} warn)" if lw else ""
        print(f"\n  {icon} {layer_id} — {layer_name}: {lp}/{lt}{ws}")
        for c in checks:
            if c["status"] == "FAIL":
                d = f' — {c["detail"]}' if c["detail"] else ""
                print(f"    \u274c {c['code']}: {c['description']}{d}")

    if args.json:
        report = {"audit_date": datetime.now().isoformat(), "html_path": str(html_path), **result.to_dict()}
        out = OUTPUT_DIR / "portfolio_audit.json"
        out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"\n  JSON: {out}")

    ws = f", {result.warnings} warnings" if result.warnings else ""
    print(f"\n{'=' * 60}")
    print(f"  OVERALL: {result.overall} — {result.passed}/{result.total} passed{ws}")
    print(f"{'=' * 60}")
    sys.exit(0 if result.failed == 0 else 1)


if __name__ == "__main__":
    main()
