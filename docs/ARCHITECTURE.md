# SkyGuard AI: Technical Architecture & System Design Document

## 1. System Overview & Problem Formulation
Automatic Weather Stations (AWS) stream three continuous atmospheric parameters:
1. **Temperature ($T$) in °C**
2. **Atmospheric Pressure ($P$) in hPa**
3. **Relative Humidity ($RH$) in %**

The core mission of **SkyGuard AI** is to distinguish between genuine, severe meteorological phenomena (e.g. convective storms, cold front passages) and true sensor/telemetry anomalies (spikes, flatlines, calibration drift, packet loss, and unphysical thermodynamic states) in real-time with **zero false alarms on extreme weather**.

---

## 2. Multi-Tier System Architecture

```
                                 [ AWS Sensor Stream: T, P, RH, Time ]
                                                   │
                                                   ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ Tier 1: Edge Guard (Ultra-Low Memory C++ & MicroPython Filter)                                    │
│ - WMO Physical Range Validation & Gradient Checks (Max ΔT/min, ΔP/min, ΔRH/min)                  │
│ - Instantaneous Sensor Flatline (ADC Freeze) Detector                                            │
│ - Magnus-Tetens Dew Point Boundary Check (T ≥ Td)                                                │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                   │
                                                   ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ Tier 2: Real-Time AI Core Ensemble                                                               │
│                                                                                                  │
│  [ Physics Engine ]             [ Temporal Autoencoder ]          [ Isolation Forest ]            │
│  - Magnus-Tetens Vapor Press    - PyTorch Trajectory Residuals    - Multivariate Density Scoring │
│  - Vapor Pressure Deficit (VPD) - 15-step Temporal Memory         - Gradient & Psychrometric     │
│  - Enthalpy Boundary Checks     - Sequence MSE Loss                Feature Space                 │
│                                                                                                  │
│  [ Streaming Statistical Engine ]                                                                │
│  - Adaptive EWMA Rolling Baseline (diurnal tracking)                                             │
│  - Decaying CUSUM Change-Point Detector (progressive calibration drift)                          │
│                                                                                                  │
│                            ═══> Ensemble Meta-Scorer <═══                                        │
│                     (Confidence Score 0–100%, Severity: LOW/MED/HIGH/CRIT)                       │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                   │
                         ┌─────────────────────────┴─────────────────────────┐
                         ▼                                                   ▼
┌───────────────────────────────────────────────────┐ ┌────────────────────────────────────────────┐
│ Tier 3: Explainable AI & Root-Cause Diagnostics   │ │ Tier 4: Self-Healing Imputation Engine     │
│ - Live: fast additive attribution heuristic       │ │ - Multivariate Temporal Moving Average     │
│ - Offline: genuine SHAP (benchmark/run_shap_*.py) │ │                                              │
│ - Multi-Class Fault Classifier (Spike, Flatline,  │ │ - Psychrometric Clamping Constraints       │
│   Drift, Physics Violation, Convective Storm)     │ │ - Uninterrupted Data Stream for Downstream │
│ - Natural Language Diagnostic Generator           │ │   Numerical Weather Prediction Models      │
└───────────────────────────────────────────────────┘ └────────────────────────────────────────────┘
                                                   │
                                                   ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ Tier 5: Sensor Health & Maintenance Advisory (heuristic, rule-based)                             │
│ - Rolling Hardware-Fault Rate & CUSUM Calibration-Drift Monitoring                               │
│ - Sensor Health Index (0–100%) mapped to a coarse days-to-service band                           │
│ - Automated Calibration & Maintenance Advisories                                                 │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Mathematical & Physical Formulations

### 3.1 Psychrometric Vapor Pressure & Dew Point (Magnus-Tetens Formula)
Saturation Vapor Pressure $e_s(T)$ (hPa):
$$e_s(T) = a \cdot \exp\left(\frac{b \cdot T}{c + T}\right)$$
where for $T \ge 0^\circ\text{C}$: $a = 6.112\text{ hPa}$, $b = 17.67$, $c = 243.5^\circ\text{C}$.  
For $T < 0^\circ\text{C}$ (over ice): $b = 22.5$, $c = 273.0^\circ\text{C}$.

Actual Vapor Pressure $e(T, RH)$ (hPa):
$$e(T, RH) = \frac{RH}{100} \cdot e_s(T)$$

Dew Point Temperature $T_d$ (°C):
$$\gamma(T, RH) = \ln\left(\frac{RH}{100}\right) + \frac{b \cdot T}{c + T}$$
$$T_d = \frac{c \cdot \gamma}{b - \gamma}$$

Vapor Pressure Deficit ($VPD$ in hPa):
$$VPD = e_s(T) - e(T, RH) = e_s(T) \cdot \left(1 - \frac{RH}{100}\right)$$

### 3.2 Decaying CUSUM Formulation for Sensor Drift
To distinguish progressive transducer degradation from diurnal variations:
$$S_n^+ = \max\left(0, \lambda \cdot S_{n-1}^+ + Z_n - k\right)$$
$$S_n^- = \max\left(0, \lambda \cdot S_{n-1}^- - Z_n - k\right)$$
where $Z_n = \frac{x_n - \mu_{\text{EWMA}}}{\sigma_{\text{EWMA}}}$, $k = 0.6$ (slack), $h = 3.5$ (threshold), and $\lambda = 0.95$ (exponential decay).

---

## 4. Multi-Class Root Cause Diagnostic Taxonomy

| Fault Code | Primary Indicator | Typical Physical Root Cause |
| :--- | :--- | :--- |
| `NORMAL` | All parameters within diurnal bounds | Healthy operational condition |
| `GENUINE_EXTREME_WEATHER` | Rapid synchronized cooling + $RH \to 100\%$ + pressure jump | Thunderstorm gust front, microburst, cold front |
| `SENSOR_SPIKE` | Sudden $\Delta T > 3^\circ\text{C}/\text{min}$ with zero $RH/P$ response | Electrostatic transient, power supply ripple |
| `SENSOR_FLATLINE` | Identical float repeating for $\ge 5$ steps | ADC buffer freeze, firmware deadlock, icing |
| `CALIBRATION_DRIFT` | CUSUM accumulation $> 3.5$ over time | Sensor aging, salt crusting, radiation shield dirt |
| `PHYSICAL_INCONSISTENCY` | $T < T_d - 0.5^\circ\text{C}$ or implied $T_d > 36^\circ\text{C}$ (exceeds Earth's ~35°C record dew point) | Transducer failure, corrupted calibration curves |
| `COMMUNICATION_DROPOUT`| Missing/null telemetry frames or random noise | Telemetry packet loss, weak cellular/LoRa signal |

---

## 5. Presentation Layer — Operator Interfaces

SkyGuard ships two front-ends over the same processing core. Neither re-implements any detection
logic; both consume the processed packet emitted by `pipeline.process_reading()`.

- **React Operator Dashboard (`frontend/`)** — the flagship, production-style console. React 19 +
  Vite + TypeScript, styled with Tailwind v4 design tokens. Streams live telemetry over the
  backend WebSocket and leads every event with the platform's core question: *sensor fault or
  genuine weather?*
- **Streamlit Control Center (`app.py`)** — a standalone testing/demo sandbox with 1-click anomaly
  injection and a Real-NOAA / synthetic toggle, useful for driving the detector during development.

### 5.1 Dashboard data flow

```
  WS /ws/telemetry  ─▶  StreamProvider          ─▶  pure adapters         ─▶  dumb components
  (processed_packet     (single live-state           (adapters.ts:              (verdict.tsx et al:
   JSON per reading)     source; rolling per-          ProcessedPacket            take plain props,
                         station buffers; REST         → UI-ready shapes)         render only)
                         backfill on mount)
```

Three concerns are kept strictly separated:

1. **One live-state source.** `StreamProvider` owns the WebSocket connection(s), the rolling
   per-station buffers, and the online/offline flag. Every component reads a single `useStream()`
   hook rather than opening its own socket.
2. **Pure adapters.** `src/lib/adapters.ts` transforms a raw `ProcessedPacket` into the exact shape
   each component needs (verdict, root-cause readout, neighbour strip, decision pipeline, heal
   provenance). Each transform has a *live* builder (from a packet) and an *offline* builder (from a
   mock row); the page chooses which to call. The transforms are side-effect-free.
3. **Dumb components.** The verdict / neighbour / pipeline / heal components take plain data props
   and render — they never fetch, so the same component renders identically whether its data came
   from a live packet or the offline fallback.

### 5.2 What the operator sees per event

Every anomaly is presented as a *decision*, not a raw score:

- **Verdict** — SENSOR FAULT / GENUINE WEATHER / NORMAL, with a one-line reason and a three-test
  evidence grid (Physics / Spatial / Rate).
- **Root-cause readout** — the classifier's `fault_type` (humanized) and its engineering
  `fault_category` from §4, shown with the **classifier's own confidence** for that fault class.
  This value is deliberately *distinct* from the ensemble detection confidence (Tier 2): the ensemble
  answers *"how sure are we this is anomalous?"*, the classifier answers *"how sure are we it is
  **this specific** fault?"*. Both are shown side by side so neither is mistaken for the other.
- **Neighbour-consistency strip** — the subject station against its network peers, making spatial
  corroboration (weather) vs. isolation (fault) legible at a glance.
- **Self-healing provenance** — raw → imputed value, with the original quarantined, not discarded.
- **Network map** — an isolated-fault halo vs. a coordinated-weather arc over the station mesh.

### 5.3 Honest-confidence display

Detection confidence is rendered with a **± agreement band** — computed on the client as the spread
across the four ensemble component scores (tight when they concur, wider when, e.g., physics fires
but the others stay low) — and is **capped just below 100%**. This is a *presentation-layer* choice
only: the ensemble mathematics in `models/ensemble.py` are untouched. The rationale is calibration
honesty — a detector that renders a literal "100.0% confident" invites misplaced trust that no
finite-evidence statistical detector has earned. First load shows skeleton placeholders rather than
flashing zeros, and when the backend is unreachable the dashboard falls back to built-in demo data
behind a clearly labelled **"Demo mode"** badge rather than presenting fabricated numbers as live.
Network-level tiles (e.g. fleet health) are **aggregated on the client** from the live per-station
packets already held in the StreamProvider buffers, not fetched as a separate server-computed metric.
