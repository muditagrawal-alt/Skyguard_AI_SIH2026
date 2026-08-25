# SkyGuard AI — Figma AI (First Draft) Prompt Library

Prompts to generate the **SkyGuard AI master dashboard** — a multi-view SaaS product — in Figma's AI **First Draft**, then hand off to a React + TypeScript + Tailwind build.

> **Product in one line:** SkyGuard AI is a real-time anomaly-detection, self-healing, and explainable-AI platform for a network of Automatic Weather Stations (AWS). It watches **temperature, atmospheric pressure, and relative humidity**, separates sensor faults from genuine weather, repairs corrupted readings, and predicts sensor maintenance. (Smart India Hackathon 2026, Problem Statement 26073.)

> **v2 — master dashboard.** This is no longer a single-page rebuild of the Streamlit app. It's an **8-view product** with a persistent left navigation rail and a global top bar. The old single screen becomes just the **Live Monitor** tab; everything else is new product surface.

---

## How to use this file

Figma **First Draft** generates **one frame per prompt** and does **not** remember previous prompts. So each screen prompt below is **self-contained** and starts with two reusable blocks you paste in:

1. **⭐ Style capsule** — the visual system (color, type, the status spine). Keeps every frame visually consistent.
2. **🧭 Shell capsule** — the persistent left nav rail + global top bar. Keeps every screen structurally consistent; you just change which nav item is active and the page title.

Workflow:

1. Read **Section 0 (Design system)** and **Section 1 (Information architecture)** once.
2. Generate the **App shell (Section 2)** first to lock the frame.
3. Then generate each **view (Section 3)** as its own frame — paste Style capsule + Shell capsule + the view prompt.
4. Pull labels and numbers from the **Content library (Section 5)** so First Draft uses real data, not placeholders.
5. Use **reusable component prompts (Section 4)** when you want to regenerate one card/chart in isolation.
6. Use **Section 7** to map the design onto React + Tailwind + TypeScript with routing.

First Draft works best when a prompt states **(a) what to build, (b) who it's for, (c) sections top-to-bottom, (d) real content, (e) the visual style.** Keep each prompt to one screen.

---

## 0. Design system (foundations)

This visual system was validated on the first draft — keep it. The **Style capsule** at the end is what you paste into every prompt.

### Direction
Clean, modern SaaS **operations console** for meteorology. **Light and airy — not a dark ops console.** A calm, trustworthy instrument: lots of whitespace, soft surfaces, and a disciplined status-color language that only lights up when something needs attention. Data-dense but never cluttered.

### Color palette
| Role | Name | Hex |
| --- | --- | --- |
| Canvas / app background | Stratus | `#F6F8FB` |
| Card / surface | White | `#FFFFFF` |
| Elevated / nav surface | Frost | `#FBFCFE` |
| Border / hairline | Mist | `#E6EBF2` |
| Ink / primary text | Troposphere | `#0F1B2D` |
| Muted text / captions | Haze | `#64748B` |
| Primary accent (brand, links, active) | Azimuth Blue | `#1D6FE0` |
| **Status — healthy / normal** | Clear-sky Green | `#15A66E` |
| **Status — genuine weather event** | Squall Indigo | `#6366F1` |
| **Status — warning / drift** | Solar Amber | `#F59E0B` |
| **Status — critical fault** | Ember Red | `#E5484D` |

**Data-visualization series** (inside charts, mapped to physical parameters): temperature = coral `#F97316` · pressure = cyan `#06B6D4` · humidity = violet `#8B5CF6` · dew point = pink `#EC4899` · **self-healed / imputed line** = green `#15A66E` (dashed) · ground-truth reference = grey `#94A3B8` (dotted).

### Typography
- **Display + large numbers:** `Space Grotesk` — headings, KPI values, station temperatures (weights 500–700).
- **Body + UI:** `Inter` — labels, buttons, tables, paragraphs (400–600, sentence case).
- **Data / mono:** `JetBrains Mono` — telemetry values, station IDs (`AWS_ALPHA_MOUNTAIN`), timestamps, diagnostic reports, coordinates.

Type scale (desktop): page title 26/32, section title 18/24, card title 15/20, body 14/20, caption 12/16, KPI number 30–40.

### Shape, space, elevation
Corner radius: cards 16px, controls 12px, pills full. Borders 1px `#E6EBF2`. Shadows soft and low. Spacing on a 4px grid; 24–32px gutters; 20–24px card padding. Content max-width ~1520px; 12-column grid.

### Signature element — the "status spine"
Every card, list row, and table row carries a **slim 3px vertical bar on its left edge**, colored by current state (green / indigo / amber / red, or neutral `#E6EBF2` when idle). It lets you read the health of the whole network by glancing down the left edges — structure, not decoration. Pair it with a matching status pill and, on live surfaces, a soft 2px "live" pulse dot in Azimuth Blue.

### Components
Nav rail item, top-bar context selector, KPI stat card, status pill, station card, action button (primary filled azure / secondary tonal / ghost), segmented toggle, dropdown, slider, icon button, data table (sticky header), detail drawer, gauge/radial meter, multi-series line chart, bar chart, donut, heatmap matrix, progress meter, map with status pins, empty state, toast.

### Voice
Plain, active, sentence case. Buttons say what happens ("Start stream", "Acknowledge", "Export log"). Status is a fact, not a mood. Errors explain what happened and how to fix it.

---

### ⭐ Style capsule (paste into every prompt)

```
Style: clean, modern SaaS operations console for meteorology — light and airy, not dark.
Cool off-white canvas (#F6F8FB), white cards with 1px #E6EBF2 borders, 16px rounded corners,
soft low shadows, generous whitespace. Deep navy ink (#0F1B2D), muted slate captions (#64748B).
Primary accent azure #1D6FE0. Status colors used sparingly: healthy green #15A66E,
genuine-weather indigo #6366F1, warning amber #F59E0B, critical red #E5484D.
Signature: every card, list row and table row has a slim 3px left "status spine" in its state color.
Type: Space Grotesk for headings and large numbers, Inter for UI/body, JetBrains Mono for
telemetry values, station IDs, coordinates and timestamps. Chart series: temperature coral #F97316,
pressure cyan #06B6D4, humidity violet #8B5CF6, dew point pink #EC4899, self-healed line green
#15A66E dashed, ground-truth grey #94A3B8 dotted. Calm, confident, data-dense but uncluttered.
```

### 🧭 Shell capsule (paste into every screen prompt)

```
App shell: a fixed 248px left navigation rail on the frost surface (#FBFCFE) with a 1px right border.
Top of rail: SkyGuard AI brand lockup — an azure (#1D6FE0) rounded-square radar/satellite line-icon
next to "SkyGuard AI" in Space Grotesk. Below it, a vertical nav menu; each item is a thin line icon +
label, and the ACTIVE item has a soft azure-tint pill background and a 3px azure left spine.
Nav items in order: Overview, Live Monitor, Stations, Anomalies, Maintenance, Analytics, Map, Settings.
Bottom of rail: a small green "System healthy" chip and a user row (avatar + "Priya · Ops").
Global top bar across the content area (white, 1px bottom border, 64px tall): page title in Space Grotesk
on the left; center-right a context selector ("All stations" with a chevron), a data-source badge
("Real NOAA" with a small globe), and a time-range selector ("Last 24h"); far right a search icon,
a notifications bell with a small red count badge, and a help icon.
Content area uses the #F6F8FB canvas with 28px padding.
```

---

## 1. Information architecture

Persistent **left nav rail** (8 destinations) + **global top bar** (context, search, alerts, profile). Contextual controls (station picker, data source, stream start/stop) live in the top bar and inside **Live Monitor**, so the rail stays pure navigation.

```
┌────────────┬──────────────────────────────────────────────────────────┐
│ ◎ SkyGuard │  Page title        [All stations ▾] [Real NOAA] [24h ▾] 🔍 🔔 ? │
│            ├──────────────────────────────────────────────────────────┤
│ ▸ Overview │                                                          │
│   Live Mon.│                  ( active view content )                 │
│   Stations │                                                          │
│   Anomalies│                                                          │
│   Maintenc.│                                                          │
│   Analytics│                                                          │
│   Map      │                                                          │
│   Settings │                                                          │
│ ─────────  │                                                          │
│ ● Healthy  │                                                          │
│ 🙂 Priya    │                                                          │
└────────────┴──────────────────────────────────────────────────────────┘
```

| View | Purpose |
| --- | --- |
| **Overview** | Command center: network KPIs, all-station status, live alert feed, mini map. The landing page. |
| **Live Monitor** | Real-time single-station stream: controls, metric cards, telemetry charts, injection sandbox, live XAI, health radar. (The refined original screen.) |
| **Stations** | Fleet list/grid → per-station **Station Detail** page. |
| **Anomalies** | Alerts management: filterable audit log, severity breakdown, anomaly **detail drawer** with acknowledge/resolve. |
| **Maintenance** | Predictive maintenance: RUL leaderboard, drift/SNR trends, sensor-health matrix, service schedule. |
| **Analytics** | Model performance: precision/recall/F1, false-alarm rate, latency, detection-by-fault-type, real-vs-synthetic, ensemble consensus. |
| **Map** | Geospatial network: status-colored pins, spatial-consistency corroboration. |
| **Settings** | Detection thresholds, ensemble weights, alert rules, edge devices, team. |

---

## 2. App shell prompt (generate first)

```
Create the application shell for a meteorology operations web app called "SkyGuard AI" — just the
persistent navigation frame with an empty content area, desktop web, 1520px wide.

[PASTE THE STYLE CAPSULE]
[PASTE THE SHELL CAPSULE]

Set the active nav item to "Overview" and the page title to "Overview". Leave the content area empty
except for a faint placeholder grid so the frame is clear. Emphasize the calm nav rail, the active-item
azure pill with its left spine, and the clean top bar.
```

---

## 3. View prompts (one frame each)

### 3.1 Overview — command center

```
Create the "Overview" command-center screen for SkyGuard AI, a meteorology anomaly-monitoring web app for
network operators. Desktop, 1520px wide.

[PASTE THE STYLE CAPSULE]
[PASTE THE SHELL CAPSULE]
Active nav item: Overview. Page title: "Overview".

Content, top to bottom:
1) A row of 5 KPI stat cards, each with a thin icon, small caption, a large Space Grotesk value, and a tiny
   trend delta: "Stations online 4 / 4" (green), "Active anomalies 2" (red), "Avg network health 91%"
   (green), "Detections today 37", "Mean latency 4.9 ms". Each has its status spine.
2) A two-column split:
   LEFT (wider): "Network status" — 4 station cards in a 2×2 grid. Each: small-caps type, name, large
   temperature, status pill + spine — Alpha Ridge (Mountain) 11.8 °C Normal (green); Beta Coastline
   (Coastal) 27.4 °C Weather event (indigo); Gamma Metropole (Urban) 24.9 °C Normal (green);
   Delta Dunes (Desert) 41.2 °C Fault · Physics violation (red). Below the grid, a "Network health · 24h"
   area chart trending ~88–93%.
   RIGHT (narrower): "Live alerts" — a scrollable feed of recent events, each a row with a status spine,
   mono timestamp, station, a fault pill and a severity dot: 14:32 Delta Dunes · Physics violation ·
   Critical; 14:30 Gamma Metropole · Spike · High; 14:28 Alpha Ridge · Flatline · Medium;
   14:24 Beta Coastline · Weather event · Info. A "View all" link sits in the header → Anomalies.
3) Bottom row, two cards: "Detections by fault type" (small horizontal bar chart: Physics 9, Spike 12,
   Flatline 7, Drift 5, Packet loss 4) and "Network map" (a small map thumbnail with 4 status-colored
   pins and a "Open map" link).
Calm, scannable, executive-glance friendly.
```

### 3.2 Live Monitor — real-time single station

```
Create the "Live Monitor" screen for SkyGuard AI — the real-time view of one weather station's telemetry
with anomaly detection, self-healing, and explanations. Desktop, 1520px wide.

[PASTE THE STYLE CAPSULE]
[PASTE THE SHELL CAPSULE]
Active nav item: Live Monitor. Page title: "Live Monitor".

Content, top to bottom:
1) A contextual control strip (white card): a station dropdown "Gamma Metropole (Urban)"; a "Data source"
   segmented toggle "Real NOAA history / Synthetic generator"; a primary "Start stream" and secondary
   "Stop" button; a "Playback speed" slider (0.1–2.0 s at 0.5 s); a ghost "Clear buffer". On the right of
   the strip, a green "Normal stream" pill and mono "Last update 2 s ago".
2) A row of 6 compact metric stat cards with parameter icons, spines and sparklines: Temperature 24.9 °C,
   Pressure 1012.4 hPa, Humidity 58 %, Dew point 15.8 °C, Vapor deficit (VPD) 8.3 hPa, Anomaly state
   (green "Normal stream" pill).
3) A two-column split:
   LEFT (wider): "Real-time sensor telemetry" — three time-aligned line charts sharing an x-axis with a
   legend on top (Ground truth, Raw telemetry, Self-healed, Flagged anomaly, Dew point):
     • Temperature (°C): coral raw line with dots, dashed green self-healed line, dotted grey ground-truth,
       red X markers where the coral line spikes and the green line stays smooth.
     • Atmospheric pressure (hPa): cyan line + faint dashed green imputed line.
     • Relative humidity (%): violet line + pink dash-dot dew-point line.
   RIGHT (narrower): "Sensor health radar" — a radial gauge "92 / 100 · Healthy" (green arc),
     "Estimated remaining useful life: 318 days", advisory "All sensors within nominal SNR; no drift", and
     three progress meters: Temperature sensor 94%, Barometer 88%, Hygrometer 91%.
4) "Anomaly injection sandbox" card: caption "Simulate hardware faults, telemetry errors, or a genuine
   severe storm on the live stream", then 6 action tiles (icon + title + mono sub-label): ⚡ Temp spike
   (+15 °C), ❄️ Sensor freeze (flatline), 📈 Calibration drift (+0.25 °C/step), ⚠️ Physics fault
   (54 °C & 96% RH), 📶 Packet loss (dropouts), ⛈️ Thunderstorm (0% false alarm; subtly indigo-tinted).
5) "Explainable AI — root cause" card: a mono diagnostic block with a 3px azure spine — "Temperature rose
   15.3 °C in 60 s — 5.1× the WMO gradient limit (3.0 °C/min). Pressure and humidity stable; neighboring
   stations normal. Isolated SENSOR SPIKE, not weather. Raw value quarantined; self-healed via temporal
   imputation. Confidence 96.4%." — a caption "Spatial context: isolated to this station — 3 others normal",
   and a horizontal bar chart "Feature attribution": Temperature gradient 42%, Dew-point spread 24%,
   Pressure tendency 20%, Humidity level 14%.
Make the coral "raw" break vs. the green "self-healed" repair the visual focus.
```

### 3.3 Stations — fleet

```
Create the "Stations" fleet-management screen for SkyGuard AI, a meteorology monitoring web app.
Desktop, 1520px wide.

[PASTE THE STYLE CAPSULE]
[PASTE THE SHELL CAPSULE]
Active nav item: Stations. Page title: "Stations".

Content:
- A toolbar: a search field ("Search stations"), filter chips (Type: All/Mountain/Coastal/Urban/Desert;
  Status: All/Normal/Weather/Fault), a grid/table view toggle, and a primary "＋ Add station" button.
- A data table with a sticky header, status spine per row, and columns:
  Station · Type · Location (mono lat/long) · Status (pill) · Health · RUL · Last reading (mono) ·
  Anomalies 24h. Rows:
  • Alpha Ridge — Mountain — 34.13°N, −117.85°E — Normal (green) — 96% — 342 d — 11.8 °C · 2s — 1
  • Beta Coastline — Coastal — 18.92°N, 72.83°E — Weather event (indigo) — 90% — 281 d — 27.4 °C · 3s — 0
  • Gamma Metropole — Urban — 28.61°N, 77.21°E — Normal (green) — 92% — 318 d — 24.9 °C · 2s — 1
  • Delta Dunes — Desert — 26.92°N, 70.91°E — Fault · Physics violation (red) — 78% — 214 d — 41.2 °C · 5s — 4
  Health shows as a small inline bar + %. Each row has a right-aligned "View" chevron and a "⋯" menu.
- Above the table, 4 compact summary chips: Total 4 · Online 4 · With active faults 1 · Avg health 89%.
Clean, sortable-looking, enterprise fleet feel.
```

### 3.4 Station detail

```
Create a "Station detail" screen for SkyGuard AI, shown when an operator opens one weather station.
Desktop, 1520px wide.

[PASTE THE STYLE CAPSULE]
[PASTE THE SHELL CAPSULE]
Active nav item: Stations. Page title: "Gamma Metropole" with a back chevron to "Stations".

Content:
- A header band: station name "Gamma Metropole (Urban Station)", a small-caps "URBAN" type badge, mono
  metadata "AWS_GAMMA_URBAN · 28.61°N, 77.21°E · Elevation 216 m · Baseline 25.0 °C, 990 hPa, 60% RH",
  a green "Normal" status pill, and two buttons: primary "View live" and secondary "Configure".
- A sub-tab bar: Overview (active) · Telemetry · Health · Anomalies · Config.
- Overview content:
  • A row of metric cards: Temperature 24.9 °C, Pressure 1012.4 hPa, Humidity 58 %, Dew point 15.8 °C,
    VPD 8.3 hPa.
  • Two-column: LEFT a compact "24h telemetry" multi-line chart (temp/pressure/humidity); RIGHT a
    "Sensor health" card with a 92/100 gauge and three sensor meters (Temperature 94%, Barometer 88%,
    Hygrometer 91%).
  • A "Recent anomalies at this station" mini table (Time · Fault type · Severity · Confidence) with 2–3 rows.
  • A small map card showing this station's pin.
Everything carries the station's current status color in its spines.
```

### 3.5 Anomalies — alerts management

```
Create the "Anomalies" alerts-management screen for SkyGuard AI, a meteorology monitoring web app.
Desktop, 1520px wide.

[PASTE THE STYLE CAPSULE]
[PASTE THE SHELL CAPSULE]
Active nav item: Anomalies. Page title: "Anomalies".

Content:
1) A row of 4 severity KPI cards with spines: Critical 3 (red), High 8 (amber), Medium 12 (indigo),
   Resolved 24h 19 (green).
2) A filter toolbar: search, and dropdowns for Station, Fault type, Category, Severity, Status
   (Open / Acknowledged / Resolved), and a date range. A secondary "Export log (CSV)" button on the right.
3) A wide data table with sticky header and a status spine per row, columns:
   Time · Station · Fault type · Category · Severity (pill) · Confidence · Raw → Healed (mono) ·
   Status · ⋯. Rows:
   • 14:32:07 · Delta Dunes · PHYSICS_VIOLATION · Thermodynamic · Critical · 98.1% · 54.0 → 34.7 °C · Open
   • 14:30:55 · Gamma Metropole · SPIKE · Sensor · High · 96.4% · 39.8 → 24.9 °C · Open
   • 14:28:12 · Alpha Ridge · FLATLINE · Sensor · Medium · 91.2% · 11.8 → 11.8 °C · Acknowledged
   • 14:24:41 · Beta Coastline · GENUINE_EXTREME_WEATHER · Weather · Info · 94.7% · 1006.0 → 1006.0 hPa · Resolved
4) On the right, a docked "Anomaly detail" drawer previewing the selected row: the mono diagnostic report,
   a "Feature attribution" bar chart, a "Model consensus" mini breakdown (Physics 0.45, Isolation Forest
   0.20, Statistical 0.20, Autoencoder 0.15), a small raw-vs-healed sparkline, and action buttons
   "Acknowledge", "Resolve", "Assign".
Filterable, auditable, operational.
```

### 3.6 Maintenance — predictive sensor health

```
Create the "Maintenance" screen for SkyGuard AI — predictive sensor maintenance across the weather-station
network. Desktop, 1520px wide.

[PASTE THE STYLE CAPSULE]
[PASTE THE SHELL CAPSULE]
Active nav item: Maintenance. Page title: "Maintenance & sensor health".

Content:
1) A row of 4 KPI cards: Sensors at risk 1 (amber), Avg RUL 289 days, Drift alerts 2 (amber),
   Calibrations due 1.
2) "Remaining useful life — leaderboard": a horizontal bar list sorted shortest-first, each row a
   station+sensor with a colored bar and day count — Delta Dunes · Hygrometer 168 d (amber);
   Delta Dunes · Barometer 214 d; Beta Coastline · Barometer 258 d; Gamma Metropole · Barometer 296 d;
   Alpha Ridge · Temperature 342 d (green).
3) "Sensor health matrix": a heatmap grid — rows = 4 stations, columns = Temperature / Barometer /
   Hygrometer, each cell a health % tinted green→amber→red (e.g., Delta Dunes/Hygrometer 74% amber,
   most others 88–96% green).
4) Two charts side by side: "Cumulative drift (°C)" line chart trending up slightly for Delta Dunes, and
   "Signal-to-noise ratio (dB)" line chart, both over 30 days.
5) "Service schedule": a small table — Station · Sensor · Recommended action · Due — e.g., Delta Dunes ·
   Hygrometer · Recalibrate · in 6 days; Beta Coastline · Barometer · Inspect · in 21 days.
Reassuring, forward-looking, maintenance-planner feel.
```

### 3.7 Analytics — model performance

```
Create the "Analytics" screen for SkyGuard AI — detection-model performance and benchmarks. Desktop,
1520px wide.

[PASTE THE STYLE CAPSULE]
[PASTE THE SHELL CAPSULE]
Active nav item: Analytics. Page title: "Model analytics".

Content:
1) A row of 5 KPI cards: Precision 99.1%, Recall 91.3%, F1 95.1%, False-alarm on storms 0.0% (green),
   Mean latency 4.9 ms. Each with a small "target met ✓" caption.
2) Two-column:
   LEFT: "Recall by fault type" — a horizontal bar chart: Physics violation 100%, Flatline 90.0%,
   Drift 85.8%, Packet loss 85.0%, Spike 80.6%.
   RIGHT: "Confusion matrix" — a 2×2 heatmap (Predicted vs Actual: Normal/Anomaly) with counts and
   green/red tinting.
3) "Real vs synthetic benchmark" — grouped bars comparing Precision, Recall, F1 for two series:
   Synthetic (99.1 / 91.3 / 95.1) and Real NOAA (91.2 / 88.8 / 90.0), with a small legend.
4) "Ensemble consensus" — a horizontal stacked/weight bar showing the 4 detectors' weights: Physics 0.45,
   Isolation Forest 0.20, Statistical 0.20, Autoencoder 0.15, each a labeled segment.
5) "Inference latency distribution" — a small histogram centered near 4.9 ms with a dashed 5 ms target line.
Analytical, credible, benchmark-report feel; numbers in mono where tabular.
```

### 3.8 Map — geospatial network

```
Create the "Map" screen for SkyGuard AI — a geospatial view of the weather-station network. Desktop,
1520px wide.

[PASTE THE STYLE CAPSULE]
[PASTE THE SHELL CAPSULE]
Active nav item: Map. Page title: "Network map".

Content:
- A large light-styled map fills most of the screen with 4 station pins colored by status: Alpha Ridge
  (green, California ~34°N), Delta Dunes (red, NW India ~27°N), Gamma Metropole (green, Delhi ~28°N),
  Beta Coastline (indigo, Mumbai ~19°N). Each pin has a small label and a soft ring in its status color;
  the red one pulses gently.
- A left-docked panel (320px): "Stations" list — each row a status spine, name, type, temperature and
  status pill; clicking a row highlights its pin. Above the list, status filter chips and a legend
  (Normal green · Weather indigo · Warning amber · Fault red).
- A small floating "Spatial consistency" callout card near the two Indian stations: "2 nearby stations
  reporting a coordinated pressure drop — corroborated as a genuine regional weather event, not isolated
  sensor faults."
Calm cartography; the pins and the status legend carry all the color.
```

### 3.9 Settings

```
Create the "Settings" screen for SkyGuard AI, a meteorology monitoring web app. Desktop, 1520px wide.

[PASTE THE STYLE CAPSULE]
[PASTE THE SHELL CAPSULE]
Active nav item: Settings. Page title: "Settings".

Content:
- A sub-tab bar: Detection (active) · Alerts · Stations · Edge devices · Team.
- Detection panel, as grouped form cards:
  • "WMO quality-control limits" — three labeled numeric inputs with units: Max ΔT 3.0 °C/min,
    Max ΔP 2.0 hPa/min, Max ΔRH 15.0 %/min, plus a read-only note "Clausius-Clapeyron: T ≥ Td (enforced)".
  • "Ensemble weights" — four sliders that sum to 1.00 with live values: Physics 0.45, Isolation Forest
    0.20, Statistical 0.20, Autoencoder 0.15, and a small "Total 1.00 ✓" indicator.
  • "Severity thresholds" — four inputs on a 0–1 scale: Low 0.35, Medium 0.60, High 0.80, Critical 0.90,
    shown along a labeled gradient track.
  • "Data source" — a segmented toggle "Real NOAA history / Synthetic generator" with a caption about
    retraining.
  • A sticky footer with "Save changes" (primary) and "Reset to defaults" (ghost).
Orderly, form-first, clearly grouped; mono for all numeric values and units.
```

---

## 4. Reusable component prompts (building blocks)

Use these to regenerate one piece in isolation. Each: paste the Style capsule, then the block.

**Station card**
```
Create a single station status card. [PASTE STYLE CAPSULE] A white card, 16px radius, with a 3px left
status spine. Small-caps type label "URBAN", station name "Gamma Metropole", a large Space Grotesk
temperature "24.9 °C", and a green "Normal" status pill. A subtle "live" pulse dot top-right and a "View"
link bottom-right. Make variants for Weather event (indigo), Warning (amber) and Fault (red).
```

**Telemetry chart trio**
```
Create three time-aligned line charts for weather telemetry. [PASTE STYLE CAPSULE] Shared x-axis (time),
mono axis labels, light gridlines, legend on top. Temperature (°C): coral raw line with dots + dashed green
self-healed line + dotted grey ground-truth + red X anomaly markers. Pressure (hPa): cyan line + dashed
green imputed. Humidity (%): violet line + pink dash-dot dew-point line.
```

**Sensor health gauge**
```
Create a sensor-health card. [PASTE STYLE CAPSULE] A semicircular radial gauge reading "92 / 100 · Healthy"
(green arc; amber 50–75, red below 50), a line "Estimated remaining useful life: 318 days", an advisory
caption, and three labeled progress meters: Temperature sensor 94%, Barometer 88%, Hygrometer 91%.
```

**KPI stat card**
```
Create a KPI stat card. [PASTE STYLE CAPSULE] A white card with a 3px status spine, a thin icon, a small
caption "Avg network health", a large Space Grotesk value "91%", a green "+2% vs yesterday" delta, and a
tiny sparkline. Provide neutral, positive and warning variants.
```

**Diagnostic report block**
```
Create an "Explainable AI" diagnostic report block. [PASTE STYLE CAPSULE] A light azure-tinted panel with a
3px azure left spine, text in JetBrains Mono: "Temperature rose 15.3 °C in 60 s — 5.1× the WMO gradient
limit (3.0 °C/min). Pressure and humidity stable; neighboring stations normal. Isolated SENSOR SPIKE, not
weather. Raw value quarantined; self-healed via temporal imputation. Confidence 96.4%." Below, a
"Feature attribution" horizontal bar chart: Temperature gradient 42%, Dew-point spread 24%, Pressure
tendency 20%, Humidity level 14%.
```

---

## 5. Content & copy library (grounded sample data)

Paste any of these so First Draft uses real content.

**Stations (4):**
- `AWS_ALPHA_MOUNTAIN` — "Alpha Ridge (Highland Station)" · Mountain · 2150 m · baseline 12.0 °C, 785 hPa, 45% RH · 34.13°N, −117.85°E
- `AWS_BETA_COASTAL` — "Beta Coastline (Marine Station)" · Coastal · 10 m · baseline 27.0 °C, 1012 hPa, 82% RH · 18.92°N, 72.83°E
- `AWS_GAMMA_URBAN` — "Gamma Metropole (Urban Station)" · Urban · 216 m · baseline 25.0 °C, 990 hPa, 60% RH · 28.61°N, 77.21°E
- `AWS_DELTA_DESERT` — "Delta Dunes (Arid Desert Station)" · Desert · 220 m · baseline 34.0 °C, 995 hPa, 22% RH · 26.92°N, 70.91°E

**Monitored parameters:** Temperature (°C), Atmospheric pressure (hPa), Relative humidity (%). Derived: Dew point Td (°C), Vapor pressure deficit VPD (hPa).

**Status vocabulary:** Normal stream (green) · Genuine weather event (indigo) · Fault (amber/red). Fault types: `SPIKE`, `FLATLINE`, `DRIFT`, `PHYSICS_VIOLATION`, `PACKET_LOSS`, `GENUINE_EXTREME_WEATHER`. Categories: Sensor, Thermodynamic, Telemetry, Weather. Severities: Low, Medium, High, Critical.

**Overview KPIs:** Stations online 4/4 · Active anomalies 2 · Avg network health 91% · Detections today 37 · Mean latency 4.9 ms.

**Injection sandbox actions:** Temp spike (+15 °C) · Sensor freeze (flatline) · Calibration drift (+0.25 °C/step) · Physics fault (54 °C & 96% RH) · Packet loss & dropouts · Thunderstorm (0% false alarm).

**WMO QC limits:** Max ΔT 3.0 °C/min · Max ΔP 2.0 hPa/min · Max ΔRH 15.0 %/min · Clausius-Clapeyron: T ≥ Td.

**Ensemble weights:** Physics 0.45 · Isolation Forest 0.20 · Statistical (Z-score/EWMA/CUSUM) 0.20 · Autoencoder 0.15. **Severity thresholds:** Low 0.35 · Medium 0.60 · High 0.80 · Critical 0.90.

**Sample diagnostic reports:**
- "Temperature rose 15.3 °C in 60 s — 5.1× the WMO gradient limit (3.0 °C/min). Pressure and humidity stable; neighboring stations normal. Isolated SENSOR SPIKE, not weather. Raw value quarantined; self-healed via temporal imputation. Confidence 96.4%."
- "Reading 54 °C at 96% RH is thermodynamically impossible (exceeds saturation enthalpy). PHYSICS_VIOLATION. Value rejected; imputed 34.7 °C from recent trend."
- "Coordinated pressure drop (−6 hPa/hr) with cooling and moistening across 2 stations — corroborated GENUINE WEATHER EVENT (convective storm). No fault raised."

**Feature attribution:** Temperature gradient 42% · Dew-point spread 24% · Pressure tendency 20% · Humidity level 14%.

**Health / maintenance:** Overall health 92/100 (Healthy) · RUL 318 days · Temperature sensor 94% · Barometer 88% · Hygrometer 91%. RUL leaderboard (shortest first): Delta Dunes/Hygrometer 168 d · Delta Dunes/Barometer 214 d · Beta Coastline/Barometer 258 d · Gamma/Barometer 296 d · Alpha/Temperature 342 d.

**Analytics / benchmarks:** Synthetic — Precision 99.1% / Recall 91.3% / F1 95.1%; Real NOAA — 91.2% / 88.8% / 90.0%. False-alarm on storms 0.0%. Latency 4.9 ms. Recall by fault type: Physics 100%, Flatline 90.0%, Drift 85.8%, Packet loss 85.0%, Spike 80.6%.

**Edge devices (Settings → Edge devices):** ESP32 field units running the `skyguard_edge.h` library — < 3.2 KB RAM, < 0.05 ms latency. Sample rows: EDGE-ALPHA-01 · firmware 1.4.2 · RAM 3.1 KB · last sync 12 s ago · Online; EDGE-DELTA-04 · firmware 1.4.1 · RAM 3.0 KB · last sync 4 m ago · Update available.

**Audit log sample rows:** see 3.5.

---

## 6. States & responsiveness

- **Empty (Anomalies/Overview feed):** centered thin radar icon, "No anomalies flagged yet", caption "Simulate a fault in Live Monitor to see detection in action", primary "Go to Live Monitor".
- **Loading:** skeleton shimmer in cards/rows, neutral grey spines, mono "Awaiting telemetry…".
- **Signal lost (metric card):** "— LOST" in muted red, red spine, caption "Packet dropped · self-healing active".
- **Mobile (390px):** nav rail collapses to a top app bar with a menu icon + brand; the 8 destinations move into a slide-in drawer or a bottom tab bar (Overview, Live, Stations, Anomalies, More). Content stacks single-column; tables become stacked cards; charts full-width; 44px touch targets.

Mobile prompt:
```
Create the mobile layout (390px wide) of the SkyGuard AI Overview screen. [PASTE STYLE CAPSULE]
The left nav becomes a top app bar with a menu icon and brand mark, plus a bottom tab bar
(Overview, Live, Stations, Anomalies, More). KPI cards become a horizontally scrollable strip; the
station status grid becomes a vertical list of rows with status spines; the live-alerts feed and mini
charts stack full-width below. Touch-friendly 44px targets.
```

---

## 7. From Figma to React + Tailwind + TypeScript

- **Layout shell:** one `AppLayout` with a persistent `<Sidebar/>` (nav rail) + `<TopBar/>` and an `<Outlet/>` for the routed page. Use **React Router** with routes `/overview`, `/live`, `/stations`, `/stations/:id`, `/anomalies`, `/maintenance`, `/analytics`, `/map`, `/settings`.
- **Tokenize first:** turn Section 0 into Tailwind theme tokens (colors, radius, shadow, fonts) so status colors and the spine are a single source of truth. Drive every stateful surface off one `status: 'normal' | 'weather' | 'warning' | 'critical' | 'idle'` prop that sets spine + pill.
- **Component inventory:** `AppLayout`, `Sidebar`, `NavItem`, `TopBar`, `ContextSelector`, `KpiCard`, `StatusPill`, `StatusSpine`, `StationCard`, `StationTable`, `TelemetryChart`, `HealthGauge`, `ProgressMeter`, `InjectionButton`, `DiagnosticReport`, `AttributionBars`, `AnomalyTable`, `AnomalyDrawer`, `RulLeaderboard`, `HealthMatrix`, `ConfusionMatrix`, `EnsembleWeights`, `NetworkMap`, `SettingsForm`, `EmptyState`.
- **Charts:** Recharts or Visx for the line/bar/donut/histogram; a small custom SVG arc for the health gauge; react-simple-maps or MapLibre for the Map view.
- **Live data:** the backend streams over `ws://…/ws/telemetry?station_id=…`; model a `useTelemetryStream(stationId)` hook feeding Live Monitor and Overview; poll REST for tables.
- **Fonts:** load Space Grotesk, Inter, JetBrains Mono (e.g., Fontsource) → `font-display`, `font-sans`, `font-mono`.
- **Accessibility floor:** visible azure focus rings, status never by color alone (spine + label + pill), respect `prefers-reduced-motion` for the live pulse, keyboard-navigable tables and drawer.