# SkyGuard AI — Figma AI (First Draft) Prompt Library

Modular prompts to generate a clean, modern SaaS UI for the **SkyGuard AI Control Center** in Figma's AI **First Draft** feature, then hand off to a React + TypeScript + Tailwind build.

> **Product in one line:** SkyGuard AI is a real-time anomaly-detection, self-healing, and explainable-AI platform for Automatic Weather Stations (AWS). It watches **temperature, atmospheric pressure, and relative humidity** across a network of stations, flags sensor faults vs. genuine weather, repairs corrupted readings, and predicts sensor maintenance needs. (Smart India Hackathon 2026, Problem Statement 26073.)

---

## How to use this file

Figma **First Draft** generates **one frame per prompt** and does **not** remember your previous prompts. So each prompt below is **self-contained**: it restates the app, the visual style, and the section to draw.

Recommended workflow:

1. **Read Section 0 (Design System)** once — it's the source of truth for color, type, and components.
2. To generate the whole screen in one shot, use the **Master Prompt (Section 1)**.
3. To build cleaner, more controllable pieces, paste the **modular prompts (Section 2)** one at a time — each produces a focused frame you can assemble into the full layout.
4. Every modular prompt already begins with a short **Style capsule** (a condensed version of the design system) so all frames come out visually consistent.
5. Use **Section 4 (Content library)** to keep First Draft from inventing placeholder text — realistic labels and values make the design read like a real product.
6. After you like the design, use **Section 5** notes to map it cleanly onto React + Tailwind + TypeScript.

Tip: First Draft responds best to prompts that state **(a) what to build, (b) who it's for, (c) the sections top-to-bottom, (d) real content, and (e) the visual style.** Keep each prompt focused on one frame; if a result is too busy, generate a sub-section on its own and combine.

---

## 0. Design system (foundations)

This is the canonical style. The **Style capsule** at the end of this section is what you paste into each modular prompt.

### Direction
Clean, modern SaaS **analytics console** for meteorology and station operations. **Light and airy — not a dark ops console.** The mood is a calm, trustworthy instrument: lots of whitespace, soft surfaces, and a disciplined status-color language that only lights up when something needs attention. Data-dense but never cluttered.

### Color palette
| Role | Name | Hex |
| --- | --- | --- |
| Canvas / app background | Stratus | `#F6F8FB` |
| Card / surface | White | `#FFFFFF` |
| Elevated / sidebar surface | Frost | `#FBFCFE` |
| Border / hairline | Mist | `#E6EBF2` |
| Ink / primary text | Troposphere | `#0F1B2D` |
| Muted text / captions | Haze | `#64748B` |
| Primary accent (brand, links, active) | Azimuth Blue | `#1D6FE0` |
| **Status — healthy / normal** | Clear-sky Green | `#15A66E` |
| **Status — genuine weather event** | Squall Indigo | `#6366F1` |
| **Status — warning / drift** | Solar Amber | `#F59E0B` |
| **Status — critical fault** | Ember Red | `#E5484D` |

**Data-visualization series** (used only inside charts, mapped to physical parameters):
temperature = coral `#F97316` · pressure = cyan `#06B6D4` · humidity = violet `#8B5CF6` · dew point = pink `#EC4899` · **self-healed / imputed line** = green `#15A66E` (dashed) · ground-truth reference = grey `#94A3B8` (dotted).

### Typography
- **Display + large numbers:** `Space Grotesk` — headings, metric values, station temperatures. Technical, slightly geometric; suits an instrument product. Use with restraint (weights 500–700).
- **Body + UI:** `Inter` — labels, buttons, table text, paragraphs. Weights 400–600, sentence case.
- **Data / mono:** `JetBrains Mono` — telemetry readouts, station IDs (`AWS_ALPHA_MOUNTAIN`), timestamps, the diagnostic report, and any raw values. This mono treatment is part of the identity, not a fallback.

Type scale (desktop): page title 28/34, section title 18/24, card title 15/20, body 14/20, caption 12/16, big metric number 32–40.

### Shape, space, elevation
- Corner radius: **cards 16px**, buttons/inputs **12px**, pills/badges **full**.
- Borders: 1px `#E6EBF2`. Shadows: soft and low (`0 1px 2px rgba(15,27,45,.04), 0 8px 24px rgba(15,27,45,.06)`) — never heavy.
- Spacing on a 4px grid; generous 24–32px gutters between cards; 20–24px card padding.
- Layout max-width ~1440px; 12-column grid in the main content area.

### Signature element — the "status spine"
Every card and list row carries a **slim 3px vertical bar on its left edge**, colored by its current state (green / indigo / amber / red, or neutral `#E6EBF2` when idle). Across the dense dashboard this creates a single, calm, scannable rhythm — you can read the health of the whole network by glancing down the left edges. It encodes real state, so it's structure, not decoration. Pair it with a small matching status pill and, on live cards, a soft 2px "live" pulse dot in Azimuth Blue.

### Components
Stat card, status pill/badge, station card, action button (primary filled azure, secondary tonal, ghost), segmented toggle, dropdown select, slider, icon button, data table with sticky header and zebra-free rows, gauge/radial meter, multi-series line chart, horizontal bar chart, progress meter, empty state, toast.

### Iconography
Thin line icons (1.5px stroke, rounded joins), e.g. Lucide/Feather style. Weather + instrument motifs where meaningful: radar, thermometer, gauge, droplet, wind, satellite, activity/pulse. Keep icons monochrome (ink or muted), color only when carrying status.

### Voice
Plain, active, sentence case. Buttons say what happens ("Start stream", "Export log"). Status is a fact, not a mood. Errors explain what happened and what to do. No exclamation marks in system text.

### Tailwind mapping (for the eventual build)
- Canvas → a custom `stratus`/`bg-slate-50`-like token; cards `bg-white`; borders `border-slate-200` (tuned to `#E6EBF2`).
- Primary `#1D6FE0` → `brand`/`primary`; semantic `green`, `indigo`, `amber`, `red` scales for status.
- Radius: cards `rounded-2xl`, controls `rounded-xl`, pills `rounded-full`.
- Shadows: `shadow-sm` default, `shadow-md` on hover/elevated.
- Fonts: `font-display` (Space Grotesk), `font-sans` (Inter), `font-mono` (JetBrains Mono).

---

### ⭐ Style capsule (paste this into every prompt)

```
Style: clean, modern SaaS analytics console for meteorology — light and airy, not dark.
Cool off-white canvas (#F6F8FB), white cards with 1px #E6EBF2 borders, 16px rounded corners,
soft low shadows, generous whitespace. Deep navy ink (#0F1B2D), muted slate captions (#64748B).
Primary accent azure #1D6FE0. Status colors used sparingly: healthy green #15A66E,
genuine-weather indigo #6366F1, warning amber #F59E0B, critical red #E5484D.
Signature: every card and row has a slim 3px left "status spine" in its state color.
Type: Space Grotesk for headings and large numbers, Inter for UI/body, JetBrains Mono for
telemetry values, station IDs and timestamps. Chart series: temperature coral #F97316,
pressure cyan #06B6D4, humidity violet #8B5CF6, dew point pink #EC4899, self-healed line
green #15A66E dashed, ground-truth grey #94A3B8 dotted. Calm, confident, data-dense but uncluttered.
```

---

## 1. Master prompt — full Control Center in one frame

```
Create a desktop web-app dashboard called "SkyGuard AI — Control Center" for meteorologists
and weather-station network operators. It monitors Automatic Weather Stations in real time for
sensor anomalies (temperature, pressure, humidity), repairs bad readings, and explains its decisions.

[PASTE THE STYLE CAPSULE HERE]

Layout: a fixed left sidebar (280px) plus a scrollable main area with a top status bar.

LEFT SIDEBAR (control rail, on the frost surface):
- Brand lockup: a radar/satellite mark in an azure rounded square + "SkyGuard AI" wordmark and the
  tagline "Real-time anomaly detection for weather stations".
- "Data source" segmented toggle: "Real NOAA history" (selected) / "Synthetic generator".
- "Weather station" dropdown set to "Gamma Metropole (Urban)". Below it a small info panel:
  "Type Urban · Elevation 216 m · Baseline 25.0 °C, 990 hPa, 60% RH" in mono.
- "Stream simulation" controls: a primary "Start stream" button and a secondary "Stop" button side by
  side, a "Playback speed" slider (0.1–2.0 s), and a ghost "Clear buffer" button.
- A small reference card "WMO QC limits" listing: "Max ΔT 3.0 °C/min · Max ΔP 2.0 hPa/min ·
  Max ΔRH 15.0 %/min · Clausius-Clapeyron: T ≥ Td" in mono.
- Footer caption: "Models trained on synthetic data blended with ~46k real NOAA observations."

TOP STATUS BAR (main area header):
- Page title "Control Center" with a live pulse dot and "Live" label.
- Active-stream line in mono: "Gamma Metropole · Urban · 28.61°N, 77.21°E".
- Right side: a global status pill (green "Normal stream").

MAIN AREA, stacked in cards with the status spine on each:

1) "Anomaly injection sandbox" — a caption "Simulate hardware faults or a real storm on the live stream",
   then a row of 6 action buttons, each with an icon, title and sub-label:
   ⚡ Temp spike (+15 °C) · ❄️ Sensor freeze (flatline) · 📈 Calibration drift (+0.25 °C/step) ·
   ⚠️ Physics fault (54 °C & 96% RH) · 📶 Packet loss & dropouts · ⛈️ Thunderstorm (0% false alarm).

2) "Network overview — all stations" — 4 station cards in a row. Each shows station type (small caps),
   station name, a large temperature in Space Grotesk, and a status pill + colored spine:
   Alpha Ridge (Mountain) 11.8 °C — Normal (green);
   Beta Coastline (Coastal) 27.4 °C — Weather event (indigo);
   Gamma Metropole (Urban) 24.9 °C — Normal (green, currently selected: azure ring);
   Delta Dunes (Desert) 41.2 °C — Fault: Physics violation (red). Non-selected cards show a "View" link.

3) A row of 6 compact metric stat cards: Temperature 24.9 °C, Pressure 1012.4 hPa, Humidity 58 %,
   Dew point 15.8 °C, Vapor deficit (VPD) 8.3 hPa, and an "Anomaly state" card showing a green
   "Normal stream" pill. Each metric card has a tiny parameter icon and a faint trend sparkline.

4) A two-column split:
   LEFT (wider): "Real-time sensor telemetry" — three stacked, x-axis-aligned line charts:
     • Temperature (°C): raw coral line with dots, a dashed green "self-healed" line, a dotted grey
       "ground truth" reference, and red X markers on flagged anomalies.
     • Pressure (hPa): cyan line + dashed green imputed line.
     • Humidity (%) with a pink dashed dew-point line.
     A horizontal legend sits above. Soft gridlines, mono axis labels.
   RIGHT (narrower): "Sensor health radar" — a radial gauge reading 92 / 100 "Healthy",
     "Estimated remaining useful life: 318 days", advisory caption, and three labeled progress meters:
     Temperature sensor 94%, Barometer 88%, Hygrometer 91%.

5) "Explainable AI — root cause" — a mono diagnostic report block:
   "Temperature rose 15.3 °C in 60 s — 5.1× the WMO gradient limit (3.0 °C/min). Pressure and humidity
   stable; neighboring stations normal. Classified as an isolated SENSOR SPIKE, not weather.
   Raw value quarantined; stream self-healed via temporal imputation. Confidence 96.4%."
   Below it a caption "Spatial context: isolated to this station — 3 other stations report normal", and a
   horizontal bar chart "Feature attribution": Temperature gradient 42%, Dew-point spread 24%,
   Pressure tendency 20%, Humidity level 14%.

6) "Anomaly audit log" — a full-width table with columns:
   Time · Station · Fault type · Category · Severity · Confidence · Raw → Healed · Explanation,
   with a few rows and a secondary "Export log (CSV)" button top-right. Severity shown as colored pills.

Make it feel polished, breathable, and trustworthy. Emphasize the calm status-spine rhythm and the
contrast between the coral "raw" line breaking and the green "self-healed" line repairing it.
```

---

## 2. Modular section prompts

Generate each as its own frame. Each block is self-contained — copy from `Create…` to the end.

### 2.1 App shell & sidebar (control rail)

```
Create the left sidebar navigation for a meteorology monitoring web app called "SkyGuard AI".

[PASTE THE STYLE CAPSULE HERE]

A fixed 280px-wide vertical sidebar on the frost surface (#FBFCFE) with a 1px right border.
Top: brand lockup — a radar/satellite line-icon inside an azure (#1D6FE0) rounded square, next to
"SkyGuard AI" in Space Grotesk and a small muted tagline "Real-time anomaly detection for weather stations".
Then, as stacked labeled groups with small caption headers:
- "Data source": a segmented toggle with two options — "Real NOAA history" (active, azure) and
  "Synthetic generator".
- "Weather station": a dropdown select showing "Gamma Metropole (Urban)". Below, a soft info panel in
  JetBrains Mono: "Type Urban · Elevation 216 m · Baseline 25.0 °C, 990 hPa, 60% RH".
- "Stream simulation": a primary filled "Start stream" button and a secondary "Stop" button on one row;
  a "Playback speed" slider labeled 0.1–2.0 s set near 0.5 s; a full-width ghost "Clear buffer" button.
- "WMO QC limits": a bordered reference card in mono — "Max ΔT 3.0 °C/min · Max ΔP 2.0 hPa/min ·
  Max ΔRH 15.0 %/min · Clausius-Clapeyron: T ≥ Td".
Footer: a muted caption "Models trained on synthetic data blended with ~46k real NOAA observations."
Keep it calm and well-spaced with clear grouping.
```

### 2.2 Top status bar + live metric stat cards

```
Create a dashboard header bar and a row of metric stat cards for a weather-station monitoring app.

[PASTE THE STYLE CAPSULE HERE]

TOP BAR: on the left, a page title "Control Center" in Space Grotesk with a small pulsing azure "live"
dot and a "Live" label; beneath it, in JetBrains Mono, "Gamma Metropole · Urban · 28.61°N, 77.21°E".
On the right, a green status pill "Normal stream" and a subtle "Last update 2 s ago" mono caption.

BELOW: a row of 6 equal compact stat cards, each with a slim left status spine, a thin parameter icon,
a small caption label, and a large value in Space Grotesk:
- Temperature — 24.9 °C (coral icon), tiny sparkline
- Pressure — 1012.4 hPa (cyan icon)
- Humidity — 58 % (violet icon)
- Dew point — 15.8 °C (pink icon)
- Vapor deficit (VPD) — 8.3 hPa
- Anomaly state — a green "Normal stream" pill instead of a number
Cards are white, 16px radius, 1px #E6EBF2 border, soft shadow, breathable padding.
```

### 2.3 Anomaly injection sandbox

```
Create an "Anomaly injection sandbox" panel for a weather-station monitoring app — a control that lets an
operator inject simulated faults or a real storm into the live data stream to test detection.

[PASTE THE STYLE CAPSULE HERE]

A white card with a title "Anomaly injection sandbox" and caption "Simulate hardware faults, telemetry
errors, or a genuine severe storm on the live stream." Inside, a responsive row of 6 equal action buttons,
each a tappable tile with a thin icon on top, a bold title, and a small mono sub-label:
- ⚡ Temp spike — "+15 °C"
- ❄️ Sensor freeze — "Flatline / stuck ADC"
- 📈 Calibration drift — "+0.25 °C per step"
- ⚠️ Physics fault — "54 °C & 96% RH"
- 📶 Packet loss — "Dropouts & outliers"
- ⛈️ Thunderstorm — "0% false alarm"
Buttons: tonal light-azure surface, 12px radius, hover lift. The first five are "fault" style (neutral),
the Thunderstorm tile is subtly indigo-tinted to signal it's a genuine weather event, not a fault.
```

### 2.4 Network overview (4 station cards)

```
Create a "Network overview" panel showing the live status of 4 automatic weather stations at a glance.

[PASTE THE STYLE CAPSULE HERE]

A section titled "Network overview — all stations" with a row of 4 equal station cards. Each card has the
signature left status spine, a small all-caps station-type label, the station name, a large current
temperature in Space Grotesk, and a status pill:
- MOUNTAIN — "Alpha Ridge" — 11.8 °C — green pill "Normal" — spine green
- COASTAL — "Beta Coastline" — 27.4 °C — indigo pill "Weather event" — spine indigo
- URBAN — "Gamma Metropole" — 24.9 °C — green pill "Normal" — SELECTED (azure ring + faint azure tint)
- DESERT — "Delta Dunes" — 41.2 °C — red pill "Fault · Physics violation" — spine red
Non-selected cards show a small "View" text link bottom-right. Cards are white, breathable, equal height.
This panel answers "one station is anomalous while its neighbors read normal" at a glance.
```

### 2.5 Real-time telemetry charts

```
Create a "Real-time sensor telemetry" panel with three stacked, time-aligned line charts for a weather
monitoring app. The story of the charts is that a raw sensor line breaks and a "self-healed" line repairs it.

[PASTE THE STYLE CAPSULE HERE]

A white card titled "Real-time sensor telemetry" with a horizontal legend at the top. Three charts share
the same x-axis (time / step), stacked vertically with light gridlines and JetBrains Mono axis labels:
1) "Temperature (°C)" — a coral (#F97316) raw line with small dots; a dashed green (#15A66E) "self-healed"
   line; a dotted grey (#94A3B8) "ground truth" reference; and red (#E5484D) X markers on a few flagged
   anomaly points where the coral line spikes away and the green line stays smooth.
2) "Atmospheric pressure (hPa)" — a cyan (#06B6D4) line plus a faint dashed green imputed line.
3) "Relative humidity (%)" — a violet (#8B5CF6) line plus a pink (#EC4899) dash-dot "dew point" line.
Legend items: Ground truth · Raw telemetry · Self-healed · Flagged anomaly · Dew point.
Clean, airy, analytical. Make the contrast between the broken raw line and the smooth healed line obvious.
```

### 2.6 Explainable AI (XAI) panel

```
Create an "Explainable AI — root cause" panel that explains, in plain language, why the system flagged a
reading, for a weather-station monitoring app.

[PASTE THE STYLE CAPSULE HERE]

A white card titled "Explainable AI — root cause". Inside:
- A "Diagnostic report" block styled like a readout, in JetBrains Mono on a very light azure-tinted surface
  with a 3px azure left spine:
  "Temperature rose 15.3 °C in 60 s — 5.1× the WMO gradient limit (3.0 °C/min). Pressure and humidity
  stable; neighboring stations normal. Classified as an isolated SENSOR SPIKE, not weather. Raw value
  quarantined; stream self-healed via temporal imputation. Confidence 96.4%."
- A small caption below: "Spatial context: isolated to this station — 3 other tracked stations report
  normal conditions."
- A horizontal bar chart titled "Feature attribution" with 4 bars (azure→teal gradient), sorted:
  Temperature gradient 42% · Dew-point spread 24% · Pressure tendency 20% · Humidity level 14%.
Calm, legible, confident. The diagnostic reads like an instrument, not a chat message.
```

### 2.7 Predictive sensor health radar

```
Create a "Sensor health radar" panel that shows the predictive maintenance status of a weather station's
sensors, for a monitoring app.

[PASTE THE STYLE CAPSULE HERE]

A narrow white card titled "Sensor health radar". Inside:
- A radial gauge / semicircular meter reading "92 / 100" with the label "Healthy" (green arc). The arc
  uses green above 75, amber 50–75, red below 50.
- A line "Estimated remaining useful life: 318 days" (number in Space Grotesk mono-ish emphasis).
- A muted advisory caption: "All sensors within nominal SNR; no calibration drift detected."
- Three labeled horizontal progress meters:
  Temperature sensor — 94% (green)
  Barometer — 88% (green)
  Hygrometer — 91% (green)
Clean and reassuring; the gauge is the focal point.
```

### 2.8 Anomaly audit log (table)

```
Create an "Anomaly audit log" data table for a weather-station monitoring app, listing flagged events.

[PASTE THE STYLE CAPSULE HERE]

A full-width white card titled "Anomaly audit log" with a secondary "Export log (CSV)" button top-right.
A clean table with a sticky header and these columns:
Time · Station · Fault type · Category · Severity · Confidence · Raw → Healed · Explanation.
Timestamps, station IDs and the Raw → Healed values are in JetBrains Mono. Severity is a colored pill
(Critical = red, High = amber, Medium = indigo). Example rows:
- 14:32:07 · Delta Dunes · PHYSICS_VIOLATION · Thermodynamic · Critical · 98.1% · 54.0 → 34.7 °C ·
  "Enthalpy impossible: 54 °C at 96% RH exceeds saturation."
- 14:30:55 · Gamma Metropole · SPIKE · Sensor · High · 96.4% · 39.8 → 24.9 °C ·
  "ΔT 15.3 °C/min, 5.1× WMO limit; neighbors normal."
- 14:28:12 · Alpha Ridge · FLATLINE · Sensor · Medium · 91.2% · 11.8 → 11.8 °C ·
  "Identical value 8 steps; SNR collapse — stuck ADC."
Also design the empty state: a centered thin radar icon and "No anomalies flagged yet — use the injection
sandbox to test detection." Rows have a subtle left status spine matching severity.
```

---

## 3. States & responsiveness

Generate these as extra frames or fold the notes into the prompts above.

**Empty state (prompt):**
```
Create an empty-state card for the anomaly audit log of a weather monitoring app.
[PASTE THE STYLE CAPSULE HERE]
Centered thin radar/pulse line-icon in muted slate, a title "No anomalies flagged yet", a caption
"Use the injection sandbox above to simulate a fault and see detection in action", and a primary
"Start stream" button. Calm, inviting, plenty of whitespace.
```

**Loading / connecting state (prompt):**
```
Create a "connecting to stream" state for a station card in a weather monitoring app.
[PASTE THE STYLE CAPSULE HERE]
A station card with a shimmer/skeleton placeholder where the temperature and status pill would be, a
neutral grey left spine, and a small mono caption "Awaiting telemetry…". Subtle, non-alarming.
```

**Data-lost / fault emphasis (prompt):**
```
Create a metric stat card in its "signal lost" state for a weather monitoring app.
[PASTE THE STYLE CAPSULE HERE]
A "Temperature" stat card showing "— LOST" instead of a value in muted red, a red left spine, and a small
caption "Packet dropped · self-healing imputation active". Keep it factual, not alarmist.
```

**Responsive / mobile (prompt):**
```
Create the mobile layout (390px wide) of the SkyGuard AI Control Center for a weather monitoring app.
[PASTE THE STYLE CAPSULE HERE]
The sidebar collapses into a top app bar with a menu icon and the brand mark. Content stacks in one column:
status bar, a horizontally scrollable metric strip, the network overview as a vertical list of station rows
(each with its status spine), the telemetry charts full-width and stacked, then the health radar, XAI panel,
and audit log (audit log becomes stacked cards instead of a wide table). Touch-friendly 44px targets.
```

---

## 4. Content & copy library (grounded sample data)

Paste any of these into a prompt so First Draft uses real content instead of placeholders. All values match SkyGuard AI's actual data model.

**Stations (4):**
- `AWS_ALPHA_MOUNTAIN` — "Alpha Ridge (Highland Station)" · Mountain · 2150 m · baseline 12.0 °C, 785 hPa, 45% RH · 34.13°N, −117.85°E
- `AWS_BETA_COASTAL` — "Beta Coastline (Marine Station)" · Coastal · 10 m · baseline 27.0 °C, 1012 hPa, 82% RH · 18.92°N, 72.83°E
- `AWS_GAMMA_URBAN` — "Gamma Metropole (Urban Station)" · Urban · 216 m · baseline 25.0 °C, 990 hPa, 60% RH · 28.61°N, 77.21°E
- `AWS_DELTA_DESERT` — "Delta Dunes (Arid Desert Station)" · Desert · 220 m · baseline 34.0 °C, 995 hPa, 22% RH · 26.92°N, 70.91°E

**Monitored parameters:** Temperature (°C), Atmospheric pressure (hPa), Relative humidity (%). Derived: Dew point Td (°C), Vapor pressure deficit VPD (hPa).

**Status vocabulary:** `Normal stream` (green) · `Genuine weather event` (indigo) · `Fault` (amber/red). Fault types: `SPIKE`, `FLATLINE`, `DRIFT`, `PHYSICS_VIOLATION`, `PACKET_LOSS`, `GENUINE_EXTREME_WEATHER`. Categories: Sensor, Thermodynamic, Telemetry, Weather. Severities: Low, Medium, High, Critical.

**Injection sandbox actions:** Temp spike (+15 °C) · Sensor freeze (flatline) · Calibration drift (+0.25 °C/step) · Physics fault (54 °C & 96% RH) · Packet loss & dropouts · Thunderstorm (0% false alarm).

**WMO QC limits:** Max ΔT 3.0 °C/min · Max ΔP 2.0 hPa/min · Max ΔRH 15.0 %/min · Clausius-Clapeyron: T ≥ Td.

**Sample diagnostic reports:**
- "Temperature rose 15.3 °C in 60 s — 5.1× the WMO gradient limit (3.0 °C/min). Pressure and humidity stable; neighboring stations normal. Isolated SENSOR SPIKE, not weather. Raw value quarantined; self-healed via temporal imputation. Confidence 96.4%."
- "Reading 54 °C at 96% RH is thermodynamically impossible (exceeds saturation enthalpy). PHYSICS_VIOLATION. Value rejected; imputed 34.7 °C from recent trend."
- "Coordinated pressure drop (−6 hPa/hr) with cooling and moistening across 2 stations — corroborated GENUINE WEATHER EVENT (convective storm). No fault raised."

**Feature attribution set:** Temperature gradient 42% · Dew-point spread 24% · Pressure tendency 20% · Humidity level 14%.

**Health radar:** Overall health 92 / 100 (Healthy) · RUL 318 days · Temperature sensor 94% · Barometer 88% · Hygrometer 91% · Advisory "All sensors within nominal SNR; no calibration drift detected."

**Benchmark stats (optional badges/footer):** Detection precision 99.1% · Recall 91.3% · F1 95.1% · False-alarm rate on storms 0.0% · Mean inference latency 4.9 ms.

---

## 5. From Figma to React + Tailwind + TypeScript

Notes to keep the design build-ready:

- **Tokenize first.** Turn Section 0 into Tailwind theme tokens (colors, radius, shadow, font families) before building components, so status colors and the spine are single sources of truth.
- **Component inventory** (suggested): `AppShell`, `Sidebar`, `StatusBar`, `StatCard`, `StatusPill`, `StationCard`, `InjectionButton`, `TelemetryChart`, `HealthGauge`, `ProgressMeter`, `DiagnosticReport`, `AttributionBars`, `AuditTable`, `EmptyState`, `StatusSpine`. Most are driven by a single `status: 'normal' | 'weather' | 'warning' | 'critical' | 'idle'` prop that sets the spine + pill color.
- **Charts:** Recharts or Visx map cleanly to the multi-series line charts and the horizontal attribution bars; a lightweight custom SVG arc works for the health gauge.
- **Live data:** the current backend streams over `ws://…/ws/telemetry?station_id=…`; model the frontend around a `useTelemetryStream(stationId)` hook feeding the charts and cards.
- **Typography:** load Space Grotesk, Inter, and JetBrains Mono (e.g., via Fontsource) and wire them to `font-display`, `font-sans`, `font-mono`.
- **Accessibility floor:** visible keyboard focus rings (azure), status never conveyed by color alone (always pair the spine with a label/pill), and respect `prefers-reduced-motion` for the live pulse.
