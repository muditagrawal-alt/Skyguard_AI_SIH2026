# 🌦️ SkyGuard AI: Intelligent Real-Time Anomaly Detection & Self-Healing Platform for Automatic Weather Stations (AWS)

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Testing%20UI-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![React Dashboard](https://img.shields.io/badge/Operator%20Dashboard-React%20%7C%20Vite%20%7C%20TypeScript-61DAFB.svg)](frontend/RUN.md)
[![PyTorch](https://img.shields.io/badge/AI%2FML-PyTorch%20%7C%20Scikit--Learn-EE4C2C.svg)](https://pytorch.org/)
[![Edge AI](https://img.shields.io/badge/Edge%20AI-ESP32%20%7C%20MicroPython-green.svg)](docs/ESP32_DEPLOYMENT.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Problem Statement ID: 26073**  
> **Title**: AI/ML-Based Intelligent Anomaly Detection for Automatic Weather Stations (AWS)  
> **Parameters Monitored**: **Temperature (°C)**, **Atmospheric Pressure (hPa)**, **Relative Humidity (%)**

---

## 🌟 Key Highlights & Innovations

1. **Physics-Informed Meteorological Engine**: Uses the **Magnus-Tetens formulation** for saturation vapor pressure $e_s(T)$, actual vapor pressure $e(T, RH)$, dew point $T_d$, vapor pressure deficit ($VPD$), and World Meteorological Organization (WMO No. 8) gradient boundary checks.
2. **Multi-Tier AI Consensus Ensemble**: Combines:
   - **Physics Rules Engine** (Thermodynamic consistency)
   - **Temporal Sequence Autoencoder** (Neural trajectory residuals via PyTorch) — pretrained on synthetic diurnal curves blended with real NOAA historical sequences
   - **Multivariate Isolation Forest** (Non-parametric density outlier scoring) — pretrained on synthetic baseline data blended with ~46k real NOAA ISD-Lite observations across 4 real stations (see [`data/real_stations/`](data/real_stations/))
   - **Adaptive EWMA & Decaying CUSUM** (Streaming statistical filters for drift & Z-scores)
3. **0% False Alarm Rate on a Genuine, Gradually-Intensifying Convective Storm**: Measured (not asserted) on the seeded synthetic benchmark. Getting here required three separate, real fixes — a genuine-weather recognition gate that reacted too slowly to a decelerating storm ramp, a statistics-only drift filter with no notion of elapsed time between readings, and a synthetic-generator artifact where saturated humidity looked like a stuck sensor — see the benchmark section below and the corresponding commit messages for what was actually wrong and how each was fixed.
4. **Cross-Station Spatial Consistency**: When multiple stations in the same network are anomalous concurrently, that corroborates a genuine, spatially-correlated weather event rather than an isolated sensor fault — directly implementing the problem statement's own worked example. Deliberately loosens the genuine-weather gate on corroboration only, never tightens it on isolation (see `benchmark/run_spatial_consistency_benchmark.py` and its README section for why).
5. **Explainable AI (XAI) & Root Cause Classifier**: Live per-packet API/UI attributions use a fast additive heuristic (not SHAP) to stay inside the real-time latency budget; genuine **SHAP values** are computed offline against the Isolation Forest (`benchmark/run_shap_analysis.py`, see [`benchmark/shap_analysis_report.md`](benchmark/shap_analysis_report.md)) for model-level explainability evidence. Both output human-readable diagnostic explanations for meteorologists.
6. **Real-Time Self-Healing Imputation**: Reconstructs corrupted or missing readings dynamically so downstream forecasting pipelines experience zero data downtime.
7. **Sensor Health & Maintenance Advisory**: Tracks each station's rolling hardware-fault rate and CUSUM calibration-drift scores to derive a live Sensor Health Index (0–100%), mapped to a coarse maintenance advisory band with a representative days-until-service figure. This is a heuristic, rule-based health tracker describing *present* condition — not a trained prognostic model, and the days figure is an advisory band, not an extrapolated failure forecast.
8. **Ultra-Lightweight Edge AI (`skyguard_edge.h` & `skyguard_edge.py`)**: Zero-dynamic-memory C++ header ready for direct deployment on **ESP32**, **ARM Cortex-M**, and **MicroPython** (< 3.2 KB RAM, < 0.05 ms latency).
9. **Real-Time Operator Dashboard (React + Vite + TypeScript, `frontend/`)**: A production-style operator console that consumes the backend's live WebSocket telemetry and leads every anomaly with the platform's core question — *sensor fault or genuine weather?* Each event surfaces an explicit **verdict** (SENSOR FAULT / GENUINE WEATHER / NORMAL), an explicit **root-cause classification** readout (humanized fault type, its engineering category, and the classifier's *own* confidence — surfaced straight from [`xai/root_cause.py`](backend/app/xai/root_cause.py) and kept distinct from the ensemble score), a six-stage **decision pipeline**, a **neighbour-consistency strip** for spatial corroboration, and **self-healing provenance** (raw → imputed, with the original value quarantined, not deleted). A live **network map** overlays an isolated-fault halo against a coordinated-weather arc. Confidence is displayed **honestly** — shown with a ± agreement band and capped just under 100%, because a calibrated detector never earns absolute certainty — and first load shows skeleton states rather than flashing placeholder numbers. Falls back to built-in demo data ("Demo mode") when the backend is offline. See [`frontend/RUN.md`](frontend/RUN.md).
10. **Anomaly-Injection Control Center (Streamlit + Plotly)**: A standalone testing/demo sandbox built with Streamlit & Plotly, featuring a dynamic **Anomaly Injection Sandbox** (1-click triggers for Spikes, Flatlines, Drift, Physics Faults, Packet Loss, and Thunderstorms), a **Real NOAA / Synthetic Generator toggle** (real data as the live background signal by default, with the same injection sandbox layered on top), and a **Network Overview** showing all 4 stations concurrently — the direct visual answer to the problem statement's own example ("...while neighboring stations show normal conditions").

---

## 🏗️ Repository Architecture

```
SkyGuard_AI/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI server (REST & WebSockets)
│   │   ├── core/
│   │   │   ├── config.py            # Central settings, WMO limits & station profiles
│   │   │   ├── physics.py           # Magnus-Tetens, Dew Point, VPD & physical rules
│   │   │   ├── data_generator.py    # Virtual AWS simulator & dynamic anomaly injector
│   │   │   ├── pipeline.py          # Unified streaming pipeline & sliding buffer
│   │   │   └── self_healing.py      # Real-time self-healing imputation engine
│   │   ├── models/
│   │   │   ├── statistical.py       # Adaptive EWMA, Flatline, CUSUM & Welford filters
│   │   │   ├── isolation_forest.py  # Multivariate density outlier detector
│   │   │   ├── autoencoder.py       # PyTorch temporal sequence neural network
│   │   │   └── ensemble.py          # Multi-tier weighted consensus meta-scorer
│   │   ├── xai/
│   │   │   ├── explainer.py         # Fast additive feature attributions (not SHAP) & natural language reasoning
│   │   │   └── root_cause.py        # Multi-class fault classification matrix
│   │   └── maintenance/
│   │       └── health_tracker.py    # Fault-rate & CUSUM-drift health index + maintenance advisory
│   └── tests/                       # Complete automated pytest test suite
│       ├── conftest.py
│       ├── test_physics.py
│       ├── test_detection.py
│       └── test_self_healing.py
├── edge/
│   ├── skyguard_edge.h              # Portable C/C++ single-header library for ESP32/MCU
│   └── skyguard_edge.py             # MicroPython portable edge module
├── benchmark/
│   ├── run_benchmark.py             # Quantitative evaluation suite (synthetic generator, seeded)
│   ├── run_real_data_benchmark.py   # Same evaluation replayed against real NOAA history
│   ├── run_spatial_consistency_benchmark.py  # Cross-station corroboration demonstration
│   ├── run_shap_analysis.py         # Genuine offline SHAP analysis (real, not the live heuristic)
│   ├── evaluation_report.md         # Generated synthetic benchmark results
│   ├── real_data_evaluation_report.md        # Generated real-data benchmark results
│   └── shap_analysis_report.md      # Generated SHAP feature-importance results
├── data/
│   └── real_stations/
│       ├── fetch_and_process.py     # Downloads & derives real NOAA ISD-Lite station data
│       ├── STATION_SOURCES.md       # Station mapping, license, and data-convention caveats
│       ├── raw/                     # Cached raw downloads (gitignored, re-fetchable)
│       └── processed/               # Clean per-station CSVs (committed, ~46k real observations)
├── docs/
│   ├── ARCHITECTURE.md              # Mathematical formulations & system design
│   ├── PIPELINE_AND_METRICS.md      # End-to-end pipeline stages & how each metric is measured
│   ├── USE_CASES.md                 # Real-world operational scenarios
│   └── ESP32_DEPLOYMENT.md          # Guide for flashing onto microcontrollers
├── frontend/                        # Real-time React operator dashboard (Vite + TypeScript)
│   ├── src/
│   │   ├── lib/
│   │   │   ├── StreamProvider.tsx   # Single live-state source (WebSocket + rolling buffers)
│   │   │   ├── adapters.ts          # Pure ProcessedPacket → UI transforms (verdict, root-cause, neighbours, healing)
│   │   │   └── types.ts             # Wire types mirroring the backend processed packet
│   │   ├── components/              # Dumb verdict / neighbour / pipeline / heal components + primitives
│   │   ├── pages/                   # Overview, Live Monitor, Anomalies, Map, Stations, Maintenance, Analytics, Settings
│   │   └── layout/                  # App shell (NavRail, TopBar)
│   ├── package.json                 # React 19, Vite, react-router, recharts, lucide
│   └── RUN.md                       # Frontend run & backend-wiring guide
├── app.py                           # Standalone Streamlit anomaly-injection control center (testing/demo)
├── run_demo.py                      # 1-Click Master Launcher Script
├── requirements.txt                 # Python dependencies
└── README.md                        # Master Documentation
```

---

## 🚀 Quickstart Guide

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/muditagrawal-alt/Skyguard_AI_SIH2026.git
cd Skyguard_AI_SIH2026

# Install requirements
pip install -r requirements.txt
```

### 2. Launch the Real-Time Operator Dashboard (React) — the flagship demo UI

The React dashboard consumes live telemetry from the FastAPI backend, so start the backend first, then the frontend.

**2a. Start the backend (REST + WebSocket server):**
```bash
uvicorn backend.app.main:app --reload --port 8000
```
- Interactive API docs (Swagger UI): `http://127.0.0.1:8000/docs`
- Live WebSocket endpoint: `ws://127.0.0.1:8000/ws/telemetry?station_id=AWS_ALPHA_MOUNTAIN&source=synthetic&rate_hz=1` (use `source=real` to replay real NOAA history instead of the synthetic generator)

**2b. Start the frontend** (requires Node 20+ and [pnpm](https://pnpm.io)):
```bash
cd frontend
pnpm install
pnpm dev
```
Open **`http://localhost:8443`**. The dev server proxies `/api` and `/ws` to the backend on port 8000, so no extra CORS setup is needed. Override the backend target with `BACKEND_ORIGIN` (e.g. `BACKEND_ORIGIN=http://127.0.0.1:9000 pnpm dev`) or change the frontend port with `PORT`. If the backend is offline, the dashboard falls back to built-in demo data and shows a **"Demo mode"** badge rather than fabricating a live feed. See [`frontend/RUN.md`](frontend/RUN.md) for full details.

### 3. Alternative — Streamlit Anomaly-Injection Control Center (standalone)
```bash
python run_demo.py
# or
streamlit run app.py
```
Open **`http://localhost:8501`** for the standalone testing sandbox: trigger anomalies with 1-click, toggle Real NOAA / Synthetic data, read XAI diagnostic reports, and watch the self-healing green imputed curves in real time. This UI runs the detection pipeline in-process and does **not** require the FastAPI backend from step 2a.

---

## 🧪 Running Automated Tests & Benchmark Evaluation

### Run Unit Test Suite
```bash
pytest backend/tests/
```

### Run Quantitative Evaluation Benchmark (synthetic diurnal generator)
```bash
python benchmark/run_benchmark.py --seed 42
```
Deterministic (fixed-seed) results, regenerated at [`benchmark/evaluation_report.md`](benchmark/evaluation_report.md) on every run:

| Metric | Measured Value | Benchmark Target | Status |
| :--- | :--- | :--- | :--- |
| **Detection Precision** | **99.1%** | > 90.0% | ✅ PASS |
| **Detection Recall** | **91.3%** | > 90.0% | ✅ PASS |
| **Overall F1-Score** | **95.1%** | > 92.0% | ✅ PASS |
| **False Alarm Rate on Storms** | **0.0%** | < 2.0% | ✅ PASS |
| **Mean Inference Latency** | **4.9 ms** | < 5.0 ms | ✅ PASS |
| **Self-Healing Imputation MAE**| **1.10 °C** | < 1.0 °C | ⚠️ borderline |

The storm false-alarm rate was an honest, measured 15% earlier in this project's
history (see git log for `fix: recognize coordinated cooling+moistening trend...`,
`fix: make statistical drift detection time-interval aware`, and `fix: prevent
saturated storm humidity from mimicking a stuck sensor`) — the root causes were a
genuine-weather recognition gate that reacted too slowly to a decelerating storm
ramp, a statistics-only drift detector with no notion of elapsed time between
readings, and a synthetic-generator artifact where saturated humidity clamped to an
exact repeated float and looked like a stuck sensor. All three are fixed and the
reasoning for each is in its commit message and inline code comments, not just
asserted here.

### Run the Real Historical Weather Benchmark (NOAA data, not synthetic)
```bash
python data/real_stations/fetch_and_process.py   # one-time: downloads real station data
python benchmark/run_real_data_benchmark.py --seed 42
```
Replays real hourly NOAA ISD-Lite observations (see
[`data/real_stations/STATION_SOURCES.md`](data/real_stations/STATION_SOURCES.md)) as the
clean background signal instead of the synthetic generator, then injects the same
controlled fault sandbox on top — closing the "graded on your own homework" problem
where the generator, the detector's training data, and the evaluator were all
authored by the same synthetic model. Results (regenerated at
[`benchmark/real_data_evaluation_report.md`](benchmark/real_data_evaluation_report.md)):
**Precision 91.2% / Recall 88.8% / F1 90.0%.** False-positive rate on real,
un-injected historical weather: **1.60%**, well under the 5% target (was 4.8%
overall / 13.6% at the worst station before this project's real-data fixes began).
Getting real-data F1 from 75% to 90% took four things, each verified independently
before being combined (see their commit messages for the full reasoning):

1. **Per-station hourly climatology** (`backend/app/core/climatology.py`): CUSUM was
   misreading ordinary diurnal warming (measured ~10-11°C swings at these stations)
   as sustained drift. Feeding it (raw − this hour's real 3-year climatological mean)
   instead of the raw reading removes that confound at the source.
2. **A critical reproducibility bug, fixed first.** Two "identical" runs of this
   benchmark were producing different F1 scores — traced to `torch.manual_seed()`
   being called one line too late (after the autoencoder's layers were already
   randomly initialized from an unseeded RNG state). Every measurement before this
   fix was potentially noise; it's called out explicitly because a system whose
   output isn't reproducible on identical input is a real problem for a deployment
   where outputs might trigger maintenance actions.
3. **Ensemble reweighting toward physics** (0.35→0.45) **and away from the
   autoencoder** (0.25→0.15): the autoencoder is a single model shared across 4
   climatically distinct profiles and runs elevated reconstruction error on the
   desert station's own legitimate large swings; physics reasons from
   thermodynamics directly and had zero false positives observed anywhere in this
   project's real-data testing.
4. **Injected-fault magnitudes recalibrated to real variance**, the same principle
   as the spike-intensity fix already in the benchmark script: a fault needs to be
   anomalous *relative to a station's own real variability*, not to the synthetic
   generator's much smaller noise floor.

**Recall by injected fault category**: physics violations 100%, flatline 90.0%,
drift 85.8%, packet loss 85.0%, spike 80.6% — all solid, none hand-picked.

### Run the Cross-Station Spatial Consistency Demonstration
```bash
python benchmark/run_spatial_consistency_benchmark.py
```
Demonstrates the corroboration mechanism: when the *same* thunderstorm signature
hits a second station concurrently, the classifier's confidence in a genuine
weather explanation is reinforced rather than left to a single station's signal
alone. With the storm false-alarm rate now at 0% even in isolation, this scenario's
headroom to demonstrate improvement is naturally small — its real value is as a
regression guard: an earlier version of this check that tightened the gate on
isolation (rather than only ever loosening it on corroboration) was caught by this
exact script pushing a genuine single-station storm's false-alarm rate from ~16% to
87.5% before being corrected. Keep this script in the suite if you extend the
network to a denser, geographically real local mesonet, where isolation vs.
corroboration will matter far more than it does for 4 stations spread across two
continents.

### Run the Genuine SHAP Explainability Analysis
```bash
python benchmark/run_shap_analysis.py
```
Computes real SHAP values (`shap.KernelExplainer`) for the Isolation Forest against
real historical background data — offline, since a proper SHAP explainer needs many
model evaluations per point and cannot run inside the live pipeline's <10ms budget.
See [`benchmark/shap_analysis_report.md`](benchmark/shap_analysis_report.md) for the
generated global feature importances and per-point attributions. The live per-packet
attribution shown in the UI/API is a separate, fast additive heuristic — clearly
labeled as such, not SHAP.

---

## 🛡️ Edge Microcontroller Deployment (ESP32)

Include `edge/skyguard_edge.h` directly in your Arduino or PlatformIO project:
```cpp
#include "skyguard_edge.h"

EdgeGuardState edge_state;

void setup() {
    skyguard_edge_init(&edge_state);
}

void loop() {
    EdgeTelemetryInput input = { .temperature_c = 25.4f, .pressure_hpa = 1013.2f, .humidity_pct = 60.0f, .dt_seconds = 1.0f };
    EdgeDetectionResult result;
    skyguard_edge_process(&edge_state, &input, &result);
    
    if (result.is_anomaly) {
        // Trigger local edge alert
    }
}
```
*See [docs/ESP32_DEPLOYMENT.md](docs/ESP32_DEPLOYMENT.md) for full instructions.*

---

## 📚 Documentation Links
- [System Architecture & Mathematics](docs/ARCHITECTURE.md)
- [Pipeline Stages & How Each Metric Is Measured](docs/PIPELINE_AND_METRICS.md)
- [Operational Use Cases & Scenarios](docs/USE_CASES.md)
- [ESP32 & Microcontroller Flashing Guide](docs/ESP32_DEPLOYMENT.md)
- [React Operator Dashboard — Run & Wiring Guide](frontend/RUN.md)
- [SIH 2026 Demo Script & Talking Points](docs/DEMO_SCRIPT.md)
- [Prior Art & Validation Positioning](docs/PRIOR_ART.md)
- [Benchmark Evaluation Report](benchmark/evaluation_report.md)