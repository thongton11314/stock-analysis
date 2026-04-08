# Styling & PDF Export Rules

## Theme (NON-NEGOTIABLE)

- **Light professional theme**: White cards (`#fff`), light gray background (`#f4f6f9`), navy header (`#1b2a4a`)
- **Fonts**: `'Segoe UI', Tahoma, Geneva, Verdana, sans-serif`, 13px base
- **Line height**: 1.55
- **Container**: `max-width: 1140px`, centered

## Color System

| Purpose | Color | Hex |
|---|---|---|
| Bullish / Positive | Green | `#16a34a` |
| Bearish / Negative | Red | `#dc2626` |
| Neutral / Caution | Amber | `#d97706` |
| Header background | Navy gradient | `#1b2a4a → #2c3e6b` |
| Card background | White | `#fff` |
| Page background | Light gray | `#f4f6f9` |
| Body text | Dark navy | `#1a1a2e` |
| Label text | Muted gray | `#5a6577` |
| Link blue | Blue | `#2563eb` |

## Signal Badges

```css
.signal { display: inline-block; padding: 2px 8px; border-radius: 3px; font-size: 0.78em; font-weight: 600; max-width: 100%; overflow: hidden; text-overflow: ellipsis; }
.signal.bullish { background: #d4edda; color: #155724; }
.signal.bearish { background: #f8d7da; color: #721c24; }
.signal.neutral { background: #fff3cd; color: #856404; }
.signal.strong-buy { background: #c3e6cb; color: #0d5524; }
.signal-desc { font-size: 0.82em; color: #5a6577; padding-left: 14px; display: block; margin-top: 2px; }
```

### Signal Badge Length Rule

Signal badges must be **SHORT labels** (3-5 words max). If a signal needs explanation, split into:
1. **Badge**: Short label (e.g., "BEARISH — Trend-Break Active")
2. **Description**: Longer text on next line using `<br>` + `<span class="signal-desc">`

```html
<!-- CORRECT: Short badge + description -->
<li><strong>Signal:</strong> <span class="signal bearish">BEARISH — Trend-Break Active</span>
<br><span class="signal-desc">Trend-break active with moderate fragility. Standard correction probability elevated to ~70%</span></li>

<!-- WRONG: Full sentence in badge (overflows container) -->
<li><strong>Signal:</strong> <span class="signal bearish">Short-term bearish — trend-break active with moderate fragility. Standard correction probability elevated to ~70%</span></li>
```

## Bullet Points

- Use CSS `::before` with unicode `\25B8`
- **NEVER** use HTML entities like `&#9656;`

```css
.summary-col li::before { content: "\25B8"; color: #3b82f6; position: absolute; left: 0; }
```

## Layout Rules

- Use **flexbox** for ALL layouts (NOT CSS Grid)
- Do **NOT** use absolute positioning for Support & Resistance levels — use flexbox columns
- **Support & Resistance pill badge style** (MANDATORY):
  - Support levels: `<span style="background:#d4edda; color:#155724; padding:3px 8px; border-radius:3px; font-size:0.75em; font-weight:600;">$PRICE (Label)</span>`
  - Resistance levels: `<span style="background:#f8d7da; color:#721c24; padding:3px 8px; border-radius:3px; font-size:0.75em; font-weight:600;">$PRICE (Label)</span>`
  - Do **NOT** use plain text lists with colored SUPPORT/RESISTANCE headers — always use pill badges with correct color semantics (green=support, red=resistance)
- Cards: `flex: 1 1 340px; min-width: 340px;` for side-by-side
- Full-width cards: `flex: 1 1 100%; min-width: 100%;`

## Key CSS Classes

| Class | Purpose |
|---|---|
| `.card` | Standard card container (white, rounded, bordered) |
| `.card.full-width` | Full-width card |
| `.summary-box` | Executive summary container |
| `.signal.bullish/bearish/neutral` | Colored signal badges |
| `.gauge-container` / `.gauge-bar` / `.gauge-fill` | RSI gauge visualization |

### RSI Gauge — Enhanced Layout

The RSI gauge must show **Oversold** and **Overbought** labels at the ends, plus zone markers at 30, 50, 70:

```html
<div style="font-size:0.82em; color:#5a6577; margin-top:8px;">RSI Gauge</div>
<div class="gauge-container">
    <span style="font-size:0.72em; color:#dc2626; min-width:52px;">Oversold</span>
    <div style="flex:1; position:relative;">
        <div class="gauge-bar">
            <div class="gauge-fill" style="width:[RSI]%; background:linear-gradient(90deg,#ef4444,#f59e0b,#22c55e);"></div>
        </div>
        <div style="display:flex; justify-content:space-between; margin-top:2px;">
            <span style="font-size:0.58em; color:#dc2626;">0</span>
            <span style="font-size:0.58em; color:#dc2626; position:absolute; left:30%; transform:translateX(-50%);">30</span>
            <span style="font-size:0.58em; color:#6b7a8d; position:absolute; left:50%; transform:translateX(-50%);">50</span>
            <span style="font-size:0.58em; color:#16a34a; position:absolute; left:70%; transform:translateX(-50%);">70</span>
            <span style="font-size:0.58em; color:#16a34a;">100</span>
        </div>
    </div>
    <span style="font-size:0.72em; color:#16a34a; min-width:60px; text-align:right;">Overbought</span>
</div>
<div style="font-size:0.72em; color:#5a6577; text-align:center; margin-top:4px;">
    RSI <strong style="color:[COLOR];">[VALUE]</strong> — <span class="signal [CLASS]">[LABEL]</span>
</div>
```

**RSI Zone Mapping:**
- RSI < 30: `color:#dc2626`, `signal bearish`, label "Oversold"
- RSI 30-40: `color:#d97706`, `signal neutral`, label "Approaching Oversold"
- RSI 40-60: `color:#6b7a8d`, `signal neutral`, label "Neutral"
- RSI 60-70: `color:#d97706`, `signal neutral`, label "Approaching Overbought"
- RSI > 70: `color:#16a34a`, `signal bearish`, label "Overbought"
| `.rating-bar` | Analyst consensus visual rating bar (graph layout) |
| `.rb-strong-buy` / `.rb-buy` / `.rb-hold` / `.rb-sell` | Rating bar segment colors |
| `.eps-chart` / `.eps-bar-wrap` / `.eps-bar` | EPS/Revenue bar chart |
| `.rev-chart` / `.rev-bar-wrap` / `.rev-bar` | Revenue trajectory chart (hypergrowth) |
| `.journey` / `.journey-step` / `.journey-arrow` | Financial journey visualization |
| `.scorecard-grid` / `.score-tile` | Macro scorecard tiles |
| `.news-item` / `.news-title` / `.news-meta` | News section items |
| `.regime-bar` / `.segment-*` / `.regime-label` | Market regime indicator (simulation) |
| `.row-regime` / `.row-event-risk` | Technical indicator table rows (simulation) |

## Regime & Event Risk Styling (Simulation Integration)

### Regime Indicator (Section 3 Executive Summary + Section 11 Technical Indicators)

The regime indicator shows the 4-state market regime as a mini progress bar + text breakdown.

```css
/* Regime progress bar */
.regime-bar { display: flex; height: 6px; border-radius: 3px; overflow: hidden; margin-top: 4px; gap: 1px; }
.regime-bar .segment { height: 100%; border-radius: 2px; }
.regime-bar .segment-calm { background: #16a34a; }
.regime-bar .segment-trending { background: #2563eb; }
.regime-bar .segment-stressed { background: #d97706; }
.regime-bar .segment-crash { background: #dc2626; }

/* Regime text label */
.regime-label { display: inline-flex; gap: 6px; align-items: center; font-size: 0.78em; color: #5a6577; flex-wrap: wrap; }
.regime-label .regime-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
```

**Regime badge color mapping** (use existing `.signal` classes):
- Calm → `.signal.bullish` (green)
- Trending → `.signal.neutral` (amber)
- Stressed → `.signal.bearish` (red)
- Crash-Prone → `.signal.bearish` (red, with stronger label like "CRASH-PRONE")

**HTML pattern — Executive Summary (Section 3):**

```html
<li><strong>Market Regime:</strong>
  <span class="signal neutral">TRENDING (42%)</span>
  <br><span class="signal-desc">Calm 20% | Stressed 28% | Crash-Prone 10%. Top 20d risk: Vol Spike 30%</span>
  <div class="regime-bar">
    <div class="segment segment-calm" style="width:20%"></div>
    <div class="segment segment-trending" style="width:42%"></div>
    <div class="segment segment-stressed" style="width:28%"></div>
    <div class="segment segment-crash" style="width:10%"></div>
  </div>
</li>
```

### Technical Indicator Section Layout (Section 11 — STRICT 3-Row Structure)

Section 11 must follow this exact 3-row flexbox layout:

| Row | Contents | Layout |
|---|---|---|
| **Row 1** | RSI (14) + MACD + ADX (14) + ATR (14) | 4 tiles, `flex:1; min-width:200px`, `gap:12px` |
| **Row 2** | Moving Averages table + Bollinger Bands visual | 2 panels, Moving Averages `flex:2; min-width:300px`, Bollinger `flex:1; min-width:240px` |
| **Row 3** | Trend-Break Status + Fragility Score + Market Regime + Event Risk (20d) | 4 tiles, `flex:1; min-width:200px`, `gap:12px` |

Each row is wrapped in a `<div style="display:flex; gap:12px; flex-wrap:wrap; margin-bottom:14px;">`. Row 3 uses `margin-bottom:12px` (narrative box below provides additional spacing). Row 3 tiles have uniform `background:#f8fafc; border:1px solid #e8ecf3` with colored `border-left:3px solid [color]` accents — never use semantic background colors (`#fffbeb`, `#f0fdf4`) on individual tiles.

#### Row 1 Tile Structure (RSI / MACD / ADX / ATR)
Each tile follows this pattern:
```
Label (uppercase, 0.72em) → Value (1.6em bold) → Signal badge → Detail lines (0.78em)
```
- **ADX tile**: Must show `Trend strength: <strong>X</strong>` + `>25 = trending, >50 = strong` subtitle
- **ATR tile**: Must show percentile badge (e.g., "25.9th pctile") + `Daily swing: <strong>~X%</strong>` + volatility description

#### Row 2: Moving Averages Table
- Must have a **title div** before the table: `<div style="font-size:0.82em; color:#1b2a4a; font-weight:600; margin-bottom:6px;">Moving Averages</div>`
- Must have `<thead>` with columns: **Indicator | Value | vs Price ($XX.XX)**
- Rows in order: **50-Day MA**, **200-Day MA**, **EMA 12**, **EMA 26** (use "50-Day MA" not "SMA 50")
- Each "vs Price" cell uses a signal badge: `<span class="signal bearish">-X.X%</span>` or `<span class="signal bullish">+X.X%</span>`

#### Row 2: Bollinger Bands Visual
- Must have a **title div**: `<div>Bollinger Bands (20, 2)</div>` (always include parameters)
- Must use the **gradient bar visual** — NOT a plain table
- Structure: Upper price (red) + "Resistance" → gradient bar with blue price marker → Lower price (green) + "Support" → Middle price note
- Gradient: `linear-gradient(90deg, #fecaca 0%, #fef3c7 30%, #d1fae5 70%, #d1fae5 100%)`
- Price marker: 3px blue bar positioned at `left:{{BB_POSITION_PCT}}` with price label above

### Technical Indicator Signal Tiles — Row 3 (Section 11)

The Market Regime and Event Risk tiles are part of Section 11 Row 3 (not table rows). The CSS classes below are retained for backward compatibility but the primary layout uses flexbox tiles:

```css
/* Row backgrounds */
.row-regime { background: #f0f9ff; }      /* light blue — for Market Regime row */
.row-event-risk { background: #fef3c7; }  /* light amber — for Event Risk row */
```

**HTML pattern — Market Regime row:**

```html
<tr class="row-regime">
  <td>Market Regime</td>
  <td>
    <span class="signal neutral">TRENDING</span>
    <span style="font-size:0.78em; color:#5a6577; margin-left:6px;">
      Calm 20% | Trend 42% | Stress 28% | Crash 10%
    </span>
    <div class="regime-bar" style="max-width:200px;">
      <div class="segment segment-calm" style="width:20%"></div>
      <div class="segment segment-trending" style="width:42%"></div>
      <div class="segment segment-stressed" style="width:28%"></div>
      <div class="segment segment-crash" style="width:10%"></div>
    </div>
  </td>
</tr>
```

**HTML pattern — Event Risk (20d) row:**

```html
<tr class="row-event-risk">
  <td>Event Risk (20d)</td>
  <td>
    <span class="signal bearish">Vol Spike 30%</span>
    <span class="signal neutral">Large Move 25%</span>
    <span class="signal bullish">Crash &lt;5%</span>
  </td>
</tr>
```

### Event Risk Tile (Section 18 Scorecard)

Uses existing `.score-tile` class with color overrides:

```html
<div class="score-tile" style="border-left-color: #d97706;">
  <div class="tile-label">Event Risk (20d)</div>
  <div class="tile-value" style="color: #d97706;">NEUTRAL</div>
  <div class="tile-detail">Top: Vol Spike 30% | Avg top-3: 22%</div>
</div>
```

**Color mapping for Event Risk tile `border-left-color` and `tile-value` color:**
- Composite <15%: `#16a34a` (green), tile-value = "TAILWIND"
- Composite 15-30%: `#d97706` (amber), tile-value = "NEUTRAL"
- Composite >30%: `#dc2626` (red), tile-value = "HEADWIND"

**Boundary rule**: Use strict `>30%` for HEADWIND. A composite of exactly 30% rounds to NEUTRAL.
Composite = average of top-3 20d event probabilities (rounded to 1 decimal).

### Event Probability Heatmap (Section 12)

The event probability heatmap is a 6-row × 3-column table with color-coded cells showing event probabilities across horizons.

```css
/* Simulation visualization layout */
.sim-grid { display: flex; gap: 14px; flex-wrap: wrap; }
.sim-panel { flex: 1 1 280px; min-width: 260px; }
.sim-panel h3 { font-size: 0.88em; color: #1b2a4a; margin-bottom: 8px; font-weight: 700; }

/* Regime probability bars */
.regime-visual { display: flex; flex-direction: column; gap: 6px; }
.regime-row { display: flex; align-items: center; gap: 8px; font-size: 0.82em; }
.regime-row .regime-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.regime-row .regime-name { min-width: 80px; color: #5a6577; }
.regime-row .regime-pct-bar { flex: 1; height: 14px; background: #e8ecf3; border-radius: 3px; overflow: hidden; }
.regime-row .regime-pct-fill { height: 100%; border-radius: 3px; }
.regime-row .regime-pct-val { min-width: 36px; text-align: right; font-weight: 600; font-size: 0.92em; }

/* Heatmap cells */
.heatmap-cell { text-align: center; padding: 5px 6px; font-size: 0.78em; font-weight: 600; border-radius: 3px; }
.heatmap-low { background: #d4edda; color: #155724; }       /* <10% */
.heatmap-med { background: #fff3cd; color: #856404; }       /* 10-20% */
.heatmap-high { background: #f8d7da; color: #721c24; }      /* 20-30% */
.heatmap-extreme { background: #dc2626; color: #fff; }      /* >30% */

/* Scenario weight bars */
.scenario-row { display: flex; align-items: center; gap: 8px; margin-bottom: 5px; font-size: 0.82em; }
.scenario-row .sc-name { min-width: 100px; color: #5a6577; }
.scenario-row .sc-bar { flex: 1; height: 18px; border-radius: 3px; display: flex; align-items: center; padding-left: 6px; font-size: 0.78em; font-weight: 600; color: #fff; }
```

**Heatmap color mapping:**
| Probability | CSS Class | Background | Text |
|---|---|---|---|
| <10% | `.heatmap-low` | `#d4edda` | `#155724` |
| 10-20% | `.heatmap-med` | `#fff3cd` | `#856404` |
| 20-30% | `.heatmap-high` | `#f8d7da` | `#721c24` |
| >30% | `.heatmap-extreme` | `#dc2626` | `#fff` |

**Scenario bar colors:**
- Base Case: `#6b7a8d` (gray)
- Vol Expansion: `#d97706` (amber)
- Trend Shift: `#2563eb` (blue)
- Tail Risk: `#dc2626` (red)

**Layout**: Two-panel flexbox. Left panel = regime bars + **scenario price targets table** + weighted expected price callout. Right panel (flex: 1.5) = heatmap table **with Price Impact column** + confidence tiles.

### Scenario Price Targets Table (Left Panel)

A standard `<table>` with 4 columns: Scenario | Weight | Price Range | Expected P/L.
Tail Risk row highlighted: `background:#fef2f2`.
Below the table, a prominent callout box (`background:#f0f3f8; border:1px solid #dde3ed`) showing:
- **Weighted Expected Price**: Large font (1.3em, bold), colored by direction (green if up, red if down)
- **80% Confidence Range**: Adjacent, showing dollar range and percentage

### Event Price Impact Column (Right Panel)

The heatmap table adds a "Price Impact" column after the 20d probability column:
- Shows the dollar range (e.g., `$347–$413`) for each event if it occurs
- Below the dollar range, a secondary line showing the magnitude (e.g., `±$33`)
- Color the text: green for upside events (trend reversal), red for downside (crash), neutral for symmetric

### Downside Skew Tile

Additional confidence tile showing directional bias:
- Formula: `(vol_weight × 0.7) + tail_weight + (trend_weight × 0.5)`, clipped [20%, 85%]
- Color: `#dc2626` if >50%, `#d97706` if 30-50%, `#16a34a` if <30%
- Arrow: `↓` suffix for downside, `↑` for upside

Bottom tiles use inline styling with `border-left: 3px solid [color]` accent.

### Event Risk Signal Badge Mapping

Event probabilities use existing `.signal` classes:
- Probability <15%: `.signal.bullish` (green)
- Probability 15-30%: `.signal.neutral` (amber)
- Probability >30%: `.signal.bearish` (red)

Keep badge text SHORT (3-5 words): e.g., "Vol Spike 30%", "Crash <5%", "Large Move 25%"

## Revenue Chart CSS (for hypergrowth companies)

Use when revenue CAGR >200% over 3+ years, or revenue scale shift >10x:

```css
.rev-chart { display: flex; align-items: flex-end; gap: 8px; height: 130px; margin-top: 8px; }
.rev-bar-wrap { flex: 1; display: flex; flex-direction: column; align-items: center; height: 100%; justify-content: flex-end; }
.rev-bar { width: 100%; max-width: 50px; border-radius: 3px 3px 0 0; min-height: 3px; background: linear-gradient(180deg, #3b82f6, #2563eb); }
.rev-bar-label { font-size: 0.72em; color: #5a6577; margin-top: 4px; text-align: center; }
.rev-bar-val { font-size: 0.72em; color: #1a1a2e; margin-bottom: 3px; font-weight: 600; }
```

Final bar (latest year) uses green gradient: `linear-gradient(180deg, #16a34a, #15803d)`

## Price Corridor Chart — Enhanced Interactive

The price corridor chart visualizes 3 scenario paths (Bullish/Average/Conservative) over 4 years with interactive data points, animated line drawing, and correction dip markers.

### CSS Classes

```css
/* Container */
.corridor-chart { width: 100%; overflow: visible; }
.corridor-svg { width: 100%; height: auto; }

/* Grid & Axis */
.corridor-grid-line { stroke: #e8ecf3; stroke-width: 0.5; stroke-dasharray: 3,3; }
.corridor-axis-label { font-size: 7px; fill: #8a94a6; font-weight: 500; }
.corridor-year-label { font-size: 8.5px; fill: #5a6577; font-weight: 600; text-anchor: middle; }

/* Scenario Lines */
.corridor-line { fill: none; stroke-width: 2.5; stroke-linecap: round; stroke-linejoin: round; }
.corridor-line-bullish { stroke: #16a34a; }
.corridor-line-average { stroke: #2563eb; }
.corridor-line-conservative { stroke: #dc2626; }

/* Interactive Data Points — hover to enlarge + show price label */
.corridor-point { transition: r 0.2s, filter 0.15s; cursor: pointer; }
.corridor-point:hover { filter: drop-shadow(0 0 6px rgba(0,0,0,0.3)); }
.corridor-point-label { opacity: 0; transition: opacity 0.2s; pointer-events: none; font-size: 8px; font-weight: 700; }
.corridor-g:hover .corridor-point-label { opacity: 1; }
.corridor-g:hover .corridor-point { r: 6; }

/* End-of-line price badges */
.corridor-badge { font-size: 8px; font-weight: 700; }

/* Correction dip markers */
.corridor-dip-line { stroke: #ef4444; stroke-width: 1; stroke-dasharray: 3,2; }
.corridor-dip-dot { fill: #ef4444; transition: r 0.2s; cursor: pointer; }
.corridor-dip-dot:hover { r: 5; filter: drop-shadow(0 0 4px rgba(239,68,68,0.5)); }
.corridor-dip-label { font-size: 6.5px; fill: #dc2626; font-weight: 600; }

/* Current price marker */
.corridor-now-marker { font-size: 7.5px; fill: #2563eb; font-weight: 700; }

/* Line draw animation */
@keyframes corridorDrawLine { from { stroke-dashoffset: 1000; } to { stroke-dashoffset: 0; } }
.corridor-line-animated { stroke-dasharray: 1000; stroke-dashoffset: 1000; animation: corridorDrawLine 1.5s ease-out forwards; }

/* Legend */
.corridor-legend { display: flex; gap: 16px; flex-wrap: wrap; margin-top: 6px; }
.corridor-legend-item { display: flex; align-items: center; gap: 5px; font-size: 0.72em; color: #5a6577; }
.corridor-legend-line { width: 18px; height: 3px; border-radius: 2px; }
```

### Interactive Features

| Feature | Implementation | Print Behavior |
|---|---|---|
| **Hover price labels** | `.corridor-g:hover .corridor-point-label { opacity: 1 }` | Always visible |
| **Point enlargement** | `.corridor-g:hover .corridor-point { r: 6 }` | Default size |
| **Animated line draw** | `@keyframes corridorDrawLine` — lines draw in over 1.5s, staggered | Disabled |
| **Correction dip hover** | `.corridor-dip-dot:hover` — enlarges + red glow | Default |
| **Gradient corridor fills** | SVG `<linearGradient>` vertical (opaque top → transparent bottom) | Renders |

### Print-Safe Rules

```css
@media print {
    .corridor-line-animated { animation: none; stroke-dashoffset: 0; stroke-dasharray: none; }
    .corridor-point-label { opacity: 1; }
}
```

### SVG Structure

```html
<div class="corridor-chart">
<svg viewBox="0 0 600 200" class="corridor-svg">
    <defs>
        <linearGradient id="gCorridorBull" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#16a34a" stop-opacity="0.18"/>
            <stop offset="100%" stop-color="#16a34a" stop-opacity="0.03"/>
        </linearGradient>
        <!-- Similar for gCorridorAvg (#2563eb) and gCorridorCons (#dc2626) -->
    </defs>

    <!-- Y-axis: price grid lines with labels ($200-$1500) -->
    <line x1="55" y1="170" x2="530" y2="170" class="corridor-grid-line"/>
    <text x="50" y="173" text-anchor="end" class="corridor-axis-label">$200</text>

    <!-- X-axis: year labels -->
    <text x="80" y="192" class="corridor-year-label">Now</text>
    <text x="200" y="192" class="corridor-year-label">End 2026</text>

    <!-- Corridor gradient fills (polygons) -->
    <polygon points="..." fill="url(#gCorridorBull)"/>

    <!-- Scenario lines (animated) -->
    <polyline points="..." class="corridor-line corridor-line-bullish corridor-line-animated" style="animation-delay:0.3s;"/>

    <!-- Current price marker -->
    <circle cx="80" cy="141" r="5" fill="#2563eb" stroke="#fff" stroke-width="2"/>
    <text x="80" y="133" text-anchor="middle" class="corridor-now-marker">NOW $380</text>

    <!-- Interactive data points (wrapped in <g> for hover) -->
    <g class="corridor-g">
        <circle cx="200" cy="128" r="4" fill="#16a34a" stroke="#fff" stroke-width="1.5" class="corridor-point"/>
        <text x="200" y="121" text-anchor="middle" fill="#16a34a" class="corridor-point-label">$500</text>
    </g>

    <!-- End-of-line badges -->
    <rect x="535" y="13" width="55" height="16" rx="3" fill="#d1fae5" stroke="#16a34a" stroke-width="0.5"/>
    <text x="562" y="24" text-anchor="middle" class="corridor-badge" fill="#16a34a">$1,500</text>

    <!-- Correction dip markers with labels -->
    <line x1="155" y1="136" x2="155" y2="158" class="corridor-dip-line"/>
    <circle cx="155" cy="158" r="3.5" class="corridor-dip-dot"/>
    <text x="155" y="166" text-anchor="middle" class="corridor-dip-label">-20% dip</text>
</svg>
</div>
<div class="corridor-legend">
    <div class="corridor-legend-item"><div class="corridor-legend-line" style="background:#16a34a;"></div>Bullish</div>
    <div class="corridor-legend-item"><div class="corridor-legend-line" style="background:#2563eb;"></div>Average</div>
    <div class="corridor-legend-item"><div class="corridor-legend-line" style="background:#dc2626;"></div>Conservative</div>
    <div class="corridor-legend-item"><div style="width:8px; height:8px; border-radius:50%; background:#ef4444;"></div>Correction dips</div>
    <div class="corridor-legend-item" style="color:#8a94a6; font-style:italic;">Hover data points for prices</div>
</div>
```

### Layout Rules
- **ViewBox**: `viewBox="0 0 600 200"` (wider than old 500x140 for room)
- **Y-axis**: Price scale on left (x=50, right-aligned), grid lines from x=55 to x=530
- **X-axis**: "Now" at x=80, then End 2026-2029 evenly spaced to x=530
- **Y coordinate formula**: `y = 182 - (price / maxPrice) * 162` where maxPrice = highest bullish target
- **Conservative line**: Use `stroke-dasharray: 6,4` to differentiate from solid lines
- **Animation stagger**: Bullish delay 0.3s, Average 0.1s, Conservative 0.5s
- **Data points**: Wrap each `<circle>` + `<text>` in `<g class="corridor-g">` for grouped hover
- **End badges**: Positioned at x=535, colored pill shapes matching scenario color
- **Correction dips**: Place between year markers, label with "-XX% dip" text below dot

## PDF Export

```css
@page { size: A4 landscape; margin: 12mm; }
body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
.card, .summary-box { page-break-inside: avoid; break-inside: avoid; }

@media print {
    body { background: #fff; font-size: 11px; }
    .container { max-width: 100%; padding: 0; }
    .header { border-radius: 0; }
    .card, .summary-box { box-shadow: none; border: 1px solid #ccc; }
    .grid { gap: 8px; }
    a { color: #2563eb !important; }
    .export-bar { display: none !important; }
    .corridor-line-animated { animation: none; stroke-dashoffset: 0; stroke-dasharray: none; }
    .corridor-point-label { opacity: 1; }
}
```

## Income Statement Breakdown Diagram (Financial Flow Chart) — Enhanced Interactive

The Income Statement Breakdown chart visualizes how revenue flows through the income statement. It's a full-width card below the Valuation + Financial Health side-by-side cards.

### CSS Classes (Enhanced)

```css
/* Container & SVG */
.sankey-container { width: 100%; overflow-x: auto; }
.sankey-svg { width: 100%; height: 280px; }

/* Nodes — hover highlights with drop-shadow */
.sankey-node rect { stroke: #fff; stroke-width: 1.5px; rx: 3; transition: filter 0.2s, stroke-width 0.2s; cursor: default; }
.sankey-node text { font-family: 'Segoe UI', sans-serif; fill: #1a1a2e; pointer-events: none; }
.sankey-node:hover rect { filter: drop-shadow(0 0 4px rgba(0,0,0,0.25)); stroke-width: 2px; }

/* Flow Bands — gradient fills with hover glow */
.sankey-link { fill-opacity: 0.3; stroke: none; transition: fill-opacity 0.25s, filter 0.25s; cursor: pointer; }
.sankey-link:hover { fill-opacity: 0.6; filter: drop-shadow(0 1px 3px rgba(0,0,0,0.15)); }

/* Text classes for consistent sizing */
.sankey-stage-label { font-size: 8px; fill: #8a94a6; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; }
.sankey-amount { font-size: 9px; fill: #1a1a2e; font-weight: 700; }
.sankey-pct { font-size: 7.5px; fill: #5a6577; }
.sankey-name { font-size: 9px; fill: #1a1a2e; font-weight: 600; }

/* Legend bar */
.sankey-legend { display: flex; gap: 14px; flex-wrap: wrap; margin-top: 8px; padding: 8px 12px; background: #f8fafc; border-radius: 4px; border: 1px solid #e8ecf3; }
.sankey-legend-item { display: flex; align-items: center; gap: 5px; font-size: 0.72em; color: #5a6577; }
.sankey-legend-swatch { width: 14px; height: 8px; border-radius: 2px; }

/* Page-load animation (disabled in print) */
@keyframes sankeyFlowIn { from { fill-opacity: 0; } to { fill-opacity: 0.3; } }
.sankey-link { animation: sankeyFlowIn 0.8s ease-out forwards; }
```

### Interactive Features

| Feature | Implementation | Print Behavior |
|---|---|---|
| **Hover glow on flows** | `filter: drop-shadow()` on `.sankey-link:hover` | Disabled |
| **Hover highlight on nodes** | `filter: drop-shadow()` on `.sankey-node:hover rect` | Disabled |
| **Flow-in animation** | `@keyframes sankeyFlowIn` — bands fade in on page load | Disabled (`animation: none`) |
| **Tooltips** | `<title>` inside each `<path>` — shows "Source → Target: $XX (XX%)" | N/A (native browser) |
| **Gradient flow bands** | SVG `<linearGradient>` defs — source color → target color | Renders correctly |
| **Cursor** | `cursor: pointer` on flows, `cursor: default` on nodes | N/A |

### Print-Safe Rules

```css
@media print {
    .sankey-link { animation: none; fill-opacity: 0.35; }
    .sankey-node rect { filter: none; }
}
```

### SVG Gradient Definitions

Use `<linearGradient>` in `<defs>` for each flow band. This shows direction (source → target) visually:

```html
<defs>
    <linearGradient id="gRevCogs" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0%" stop-color="#2563eb"/>  <!-- Revenue blue -->
        <stop offset="100%" stop-color="#d97706"/> <!-- COGS amber -->
    </linearGradient>
    <linearGradient id="gRevGP" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0%" stop-color="#2563eb"/>
        <stop offset="100%" stop-color="#0d9488"/>  <!-- Gross Profit teal -->
    </linearGradient>
    <!-- ... one gradient per flow band -->
</defs>
```

Then reference in flow paths: `fill="url(#gRevCogs)"` instead of flat colors.

### Color Scheme for Nodes

| Node Type | Color | Hex |
|---|---|---|
| Revenue / Total Revenue | Blue | `#2563eb` |
| Gross Profit | Teal | `#0d9488` |
| COGS / Cost of Revenue | Amber | `#d97706` |
| Operating Expenses | Red-orange | `#ea580c` |
| Operating Income | Green | `#16a34a` |
| Net Income (profit) | Emerald | `#059669` |
| Net Loss | Red | `#dc2626` |
| R&D | Indigo | `#6366f1` |
| SG&A | Violet | `#8b5cf6` |
| Tax | Orange | `#f97316` |

### Enhanced SVG Structure

```html
<div class="sankey-container">
<svg viewBox="0 0 900 280" class="sankey-svg">
    <defs><!-- gradient definitions --></defs>

    <!-- Stage headers -->
    <text x="8" y="16" class="sankey-stage-label">Revenue</text>
    <text x="188" y="16" class="sankey-stage-label">Cost Split</text>
    <text x="368" y="16" class="sankey-stage-label">Operating Split</text>
    <text x="555" y="16" class="sankey-stage-label">Expense Detail</text>
    <line x1="0" y1="22" x2="900" y2="22" stroke="#e8ecf3" stroke-width="0.5"/>

    <!-- Nodes wrapped in <g class="sankey-node"> for hover targeting -->
    <g class="sankey-node">
        <rect x="0" y="30" width="18" height="200" fill="#2563eb"/>
        <text x="22" y="128" class="sankey-amount">$94.8B</text>
        <text x="22" y="140" class="sankey-pct">100% of Revenue</text>
    </g>

    <!-- Flow bands with gradient fills and title tooltips -->
    <path d="M18,30 C100,30 100,30 180,30 L180,194 C100,194 100,196 18,196 Z" 
          fill="url(#gRevCogs)" class="sankey-link">
        <title>Total Revenue → Cost of Revenue: $77.7B (81.9%)</title>
    </path>

    <!-- Margin callout boxes (top-right of SVG) -->
    <rect x="660" y="38" width="100" height="30" rx="4" fill="#f0fdf4" stroke="#bbf7d0"/>
    <text x="710" y="52" text-anchor="middle" font-size="7.5" fill="#166534" font-weight="600">Gross Margin</text>
    <text x="710" y="63" text-anchor="middle" font-size="10" fill="#16a34a" font-weight="700">18.0%</text>
</svg>
</div>

<!-- Legend bar below SVG -->
<div class="sankey-legend">
    <div class="sankey-legend-item"><div class="sankey-legend-swatch" style="background:#2563eb;"></div>Revenue</div>
    <div class="sankey-legend-item"><div class="sankey-legend-swatch" style="background:#d97706;"></div>COGS</div>
    <!-- ... one per category -->
</div>

<!-- Narrative analysis box (REQUIRED) -->
<div style="background:#f8fafc; border:1px solid #e8ecf3; border-radius:6px; padding:12px; margin-top:10px;">
    <div style="font-size:0.82em; font-weight:700; color:#1b2a4a; margin-bottom:4px;">Income Statement Analysis</div>
    <div style="font-size:0.78em; color:#5a6577; line-height:1.5;">3-5 sentence narrative: gross margin quality, dominant expense, operating leverage, net margin trend, business model insight. Use <strong style="color:#16a34a;">bold green</strong> for key margin figures.</div>
</div>
<!-- Same narrative box styling is reused for:
     S11: "Technical Analysis Summary" (below Row 3 signal tiles)
     S14: "Ownership & Insider Activity Analysis" (below ownership flex)
     S15: "Macro Environment Analysis" (below Fed chart)
     See .instructions/report-layout.md for the complete 7-element inventory and narrative integrity rules. -->
```

### Layout Rules
- **ViewBox**: `viewBox="0 0 900 280"` (wide enough for 4 stages + margin callouts)
- **Node width**: 18px rectangles with `rx="3"` rounded corners
- **Stage positions (x)**: Stage 1 = 0, Stage 2 = 180, Stage 3 = 360, Stage 4 = 540
- **Margin callouts**: Position at x=660 in top-right area of SVG
- **Band width**: Proportional to `amount / total_revenue * total_height`
- **Labels**: Use `.sankey-name` for category, `.sankey-amount` for dollar value, `.sankey-pct` for percentage
- **Stage headers**: `.sankey-stage-label` text above each column at y=16
- **Separator line**: `<line>` at y=22 spanning full width
- **Height**: Keep total SVG height at 250-300px for PDF compatibility
- **DETAIL column node spacing (CRITICAL)**: Adjacent nodes in the DETAIL column (Stage 4) must have ≥12px vertical gap between the bottom of one node's lowest text label (y + ~7px for font-size 8) and the top of the next node's `<rect>`. This prevents text overlap. For companies with many expense categories (e.g., R&D + Fulfillment + SGA), spread nodes across the full available height (y=55 to y=220) rather than cramming them near the top.
- Each flow band must have a `<title>` tooltip: "Source → Target: $XX.XB (XX% of revenue)"
- Always include a `.sankey-legend` bar below the SVG
- Include Gross Margin and Net Margin callout boxes in the SVG

### Data Stages (Left to Right)

| Stage | Node(s) | Data Source |
|---|---|---|
| 1. Total Revenue | Single node | `totalRevenue` |
| 2. Cost Split | COGS, Gross Profit | `costOfRevenue`, `grossProfit` |
| 3. Operating Split | Operating Expenses, Operating Income | `operatingExpenses`, `operatingIncome` |
| 4. Expense Detail | R&D, SGA, Tax, Net Income | `researchAndDevelopment`, `sellingGeneralAndAdministrative`, `incomeTaxExpense`, `netIncome` |

### For Companies with Limited Revenue Segmentation
If `INCOME_STATEMENT` doesn't break down revenue sources, use a simplified 4-stage flow:
Total Revenue → COGS + Gross Profit → OpEx + Operating Income → Tax + Interest + Net Income

## Export Button JavaScript

```javascript
function exportToPDF() {
    document.title = '[TICKER] Stock Analysis Report';
    window.print();
}
```

## Monthly Price Forecast — Styling & Structure

The Monthly Price Forecast table appears inside Section 5 (Price Corridors), after the SVG corridor chart and before the correction risk table.

### Table Structure

| Column | Width | Styling |
|---|---|---|
| Month | Auto | `.val` for month name |
| Actual | Center | `.val` for past months; `color:#8a94a6` dash for future |
| Model Est. | Center | `color:#2563eb; font-weight:600` |
| Accuracy | Center | Color-coded badge (see below) |
| Conservative | Center | `color:#dc2626; font-weight:600` |
| Average | Center | `color:#2563eb; font-weight:600` |
| Bullish | Center | `color:#16a34a; font-weight:600` |
| Key Catalyst | Auto | `font-size:0.78em` with inline signal badges |

### Row Types

| Row Type | Background | Border | Use For |
|---|---|---|---|
| **Past month** | `#f0f3f8` | None | Months with actual closing data |
| **Current month** | `#eff6ff` | `border-left:3px solid #2563eb` | The month of the report date |
| **Accuracy summary** | `#fffbeb` | `border-top:2px solid #fde68a` | N-month backtest average |
| **Future month** | Alternating white/`#f8fafc` | None | Predicted months |
| **December (year-end)** | `#f0fdf4` | `border-bottom:2px solid #16a34a` | Must match Section 4 targets |

### Accuracy Badge Colors

```
Accuracy >= 90%:  background: #d4edda;  color: #155724;  (green)
Accuracy 85-90%:  background: #fff3cd;  color: #856404;  (amber)
Accuracy < 85%:   background: #f8d7da;  color: #721c24;  (red)
```

**Accuracy formula**: `Accuracy = 100% - |error%|` where `error% = (Model_Est - Actual) / Actual * 100`

### Scenario Path Boxes (below forecast table)

```html
<div style="display:flex; gap:10px; margin-top:8px; flex-wrap:wrap;">
    <div style="flex:1 1 200px; padding:8px; background:#fef2f2; border-radius:4px; border-left:3px solid #dc2626;">
        <div style="font-size:0.72em; font-weight:600; color:#991b1b;">Conservative Path → $[TARGET]</div>
        <div style="font-size:0.68em; color:#5a6577;">[Narrative]. Matches Section 4 target: <strong>$[TARGET]</strong></div>
    </div>
    <div style="flex:1 1 200px; padding:8px; background:#eff6ff; border-radius:4px; border-left:3px solid #2563eb;">
        <div style="font-size:0.72em; font-weight:600; color:#1e40af;">Average Path → $[TARGET]</div>
        <div style="font-size:0.68em; color:#5a6577;">[Narrative]. Matches Section 4 & analyst consensus: <strong>$[TARGET]</strong></div>
    </div>
    <div style="flex:1 1 200px; padding:8px; background:#f0fdf4; border-radius:4px; border-left:3px solid #16a34a;">
        <div style="font-size:0.72em; font-weight:600; color:#166534;">Bullish Path → $[TARGET]</div>
        <div style="font-size:0.68em; color:#5a6577;">[Narrative]. Matches Section 4 bullish target: <strong>$[TARGET]</strong></div>
    </div>
</div>
```

### Methodology Note (below path boxes)

```html
<div style="margin-top:6px; font-size:0.68em; color:#8a94a6;">
    <strong>Methodology:</strong> Monthly targets interpolate from current price to Section 4 year-end targets.
    <strong>Accuracy metric:</strong> Model Est shows pre-recalibration prediction. Accuracy = 100% − |error%|.
    <strong>Recalibration:</strong> Future projections incorporate active signals (TB/VS/VF), Fragility, CCRLO, and event risk simulation (regime + scenario weights).
</div>
```

### Consistency Rule (CRITICAL)
The **December row** year-end targets MUST exactly match Section 4 (Price Target Projections) year-end targets for all 3 scenarios. This is a top-priority audit check (Layer 1b in report-audit skill).

## Analyst Consensus — Visual Graph Layout (Section 8a)

The Analyst Consensus card uses a **visual graph layout** (NOT a table-based breakdown). This provides a more intuitive, scannable reading experience.

### Structure (top to bottom)

```html
<div style="text-align:center; margin-bottom:10px;">
    <!-- 1. Target price hero -->
    <div style="font-size:1.4em; font-weight:700; color:#16a34a;">$XXX.XX</div>
    <!-- 2. Subtitle -->
    <div style="font-size:0.78em; color:#5a6577;">Mean Target Price (+XX.X% upside)</div>
    <!-- 3. Analyst count -->
    <div style="font-size:0.72em; color:#8a94a6;">XX Analysts &bull; Latest Quarter: [Quarter Year]</div>
</div>
<!-- 4. Visual rating bar -->
<div class="rating-bar">
    <div class="rb-strong-buy" style="width:XX%;">X SB</div>
    <div class="rb-buy" style="width:XX%;">X Buy</div>
    <div class="rb-hold" style="width:XX%;">X</div>
    <!-- Omit rb-sell if 0 sell ratings -->
</div>
<!-- 5. Percentage breakdown text -->
<div style="font-size:0.72em; color:#5a6577; text-align:center; margin-top:4px;">
    Strong Buy: XX.X% &bull; Buy: XX.X% &bull; Hold: XX.X% &bull; Sell: XX.X%
</div>
<!-- 6. Green consensus box -->
<div style="background:#f0fdf4; border:1px solid #bbf7d0; border-radius:4px; padding:8px; margin-top:10px;">
    <div style="font-size:0.78em; color:#166534;">
        <strong>Consensus:</strong> <span class="signal strong-buy">STRONG BUY</span>
    </div>
    <div style="font-size:0.72em; color:#5a6577;">
        XX% Buy+Strong Buy. [Narrative about conviction level, sell count, analyst coverage depth.]
    </div>
</div>
```

### Consensus Badge Mapping

| Buy+Strong Buy % | Badge | CSS Class |
|---|---|---|
| >80% | STRONG BUY | `.signal.strong-buy` |
| >60% | BUY | `.signal.bullish` |
| >50% | HOLD | `.signal.neutral` |
| <50% | SELL | `.signal.bearish` |

### Rating Bar Segment Colors

| Segment | CSS Class | Background |
|---|---|---|
| Strong Buy | `.rb-strong-buy` | `#28a745` (dark green) |
| Buy | `.rb-buy` | `#51cf66` (light green) |
| Hold | `.rb-hold` | `#ffc107` (amber, `color:#333`) |
| Sell | `.rb-sell` | `#fd7e14` (orange) |
| Strong Sell | `.rb-strong-sell` | `#dc3545` (red) |

### Important Rules
- **Never use a `<table>`** for the rating breakdown — the visual bar + percentage text replaces it
- Hold segment shows only the count number (e.g., "4"), not "4 Hold" — saves space when small
- Sell segment width should be omitted entirely if 0 sell ratings (don't render empty segment)
- Target price is always `color:#16a34a` (green) regardless of upside magnitude
- Summary narrative should include: Buy+SB %, sell count commentary, and coverage depth note
