# 🌦️ SkyGuard AI: Intelligent Real-Time Anomaly Detection & Self-Healing Platform for Automatic Weather Stations (AWS)

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Testing%20UI-Streamlit-FF4B4B.svg)](https://streamlit.io/)
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
   - **Temporal Sequence Autoencoder** (Neural trajectory residuals via PyTorch)
   - **Multivariate Isolation Forest** (Non-parametric density outlier scoring)
   - **Adaptive EWMA & Decaying CUSUM** (Streaming statistical filters for drift & Z-scores)
3. **0% False Alarm Rate on Severe Convective Weather**: Successfully distinguishes genuine extreme weather (e.g. thunderstorm gust front: rapid cooling + humidity surge to $98\%$ + pressure jump) from true sensor faults.
4. **Explainable AI (XAI) & Root Cause Classifier**: Computes **SHAP feature attributions** and outputs human-readable diagnostic explanations for meteorologists.
5. **Real-Time Self-Healing Imputation**: Reconstructs corrupted or missing readings dynamically so downstream forecasting pipelines experience zero data downtime.
6. **Predictive Sensor Maintenance Radar**: Tracks Signal-to-Noise Ratio (SNR), cumulative drift, and estimates Remaining Useful Life (RUL in days).
7. **Ultra-Lightweight Edge AI (`skyguard_edge.h` & `skyguard_edge.py`)**: Zero-dynamic-memory C++ header ready for direct deployment on **ESP32**, **ARM Cortex-M**, and **MicroPython** (< 3.2 KB RAM, < 0.05 ms latency).
8. **Interactive Control Center UI**: Built with Streamlit & Plotly, featuring a dynamic **Anomaly Injection Sandbox** (1-click triggers for Spikes, Flatlines, Drift, Physics Faults, Packet Loss, and Thunderstorms).

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
│   │   │   ├── explainer.py         # SHAP feature attributions & natural language reasoning
│   │   │   └── root_cause.py        # Multi-class fault classification matrix
│   │   └── maintenance/
│   │       └── health_tracker.py    # Sensor drift, SNR, health score & RUL estimation
│   └── tests/                       # Complete automated pytest test suite
│       ├── conftest.py
│       ├── test_physics.py
│       ├── test_detection.py
│       └── test_self_healing.py
├── edge/
│   ├── skyguard_edge.h              # Portable C/C++ single-header library for ESP32/MCU
│   └── skyguard_edge.py             # MicroPython portable edge module
├── benchmark/
│   ├── run_benchmark.py             # Quantitative evaluation suite (F1, Precision, Latency)
│   └── evaluation_report.md         # Generated benchmark evaluation results
├── docs/
│   ├── ARCHITECTURE.md              # Mathematical formulations & system design
│   ├── USE_CASES.md                 # Real-world operational scenarios
│   └── ESP32_DEPLOYMENT.md          # Guide for flashing onto microcontrollers
├── app.py                           # Interactive Streamlit Testing & Control Center UI
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

### 2. Launch the Interactive Control Center UI (1-Click Demo)
```bash
python run_demo.py
# or
streamlit run app.py
```
Open **`http://localhost:8501`** in your browser to interact with live streaming telemetry, trigger anomalies in the sandbox, view XAI diagnostic reports, and observe the self-healing green imputed curves in real-time!

### 3. Launch the FastAPI Backend (REST & WebSocket Server)
```bash
uvicorn backend.app.main:app --reload --port 8000
```
- Interactive API Docs (Swagger UI): `http://127.0.0.1:8000/docs`
- Real-time WebSocket Endpoint: `ws://127.0.0.1:8000/ws/telemetry?station_id=AWS_ALPHA_MOUNTAIN`

---

## 🧪 Running Automated Tests & Benchmark Evaluation

### Run Unit Test Suite
```bash
pytest backend/tests/
```

### Run Quantitative Evaluation Benchmark
```bash
python benchmark/run_benchmark.py
```

### Benchmark Results Summary:
| Metric | Measured Value | Benchmark Target | Status |
| :--- | :--- | :--- | :--- |
| **Detection Precision** | **95.5%** | > 90.0% | ✅ PASS |
| **Detection Recall** | **82.5%** | > 80.0% | ✅ PASS |
| **Overall F1-Score** | **88.5%** | > 85.0% | ✅ PASS |
| **False Alarm Rate on Storms** | **0.0%** | < 2.0% | ✅ PASS |
| **Mean Inference Latency** | **4.95 ms** | < 10.0 ms | ✅ PASS |
| **Self-Healing Imputation MAE**| **1.13 °C** | < 2.0 °C | ✅ PASS |

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
- [Operational Use Cases & Scenarios](docs/USE_CASES.md)
- [ESP32 & Microcontroller Flashing Guide](docs/ESP32_DEPLOYMENT.md)
- [Benchmark Evaluation Report](benchmark/evaluation_report.md)