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
│ Tier 5: Predictive Sensor Maintenance & Health Radar                                             │
│ - Signal-to-Noise Ratio (SNR) and Fault Rate Monitoring                                          │
│ - Sensor Health Score (0–100%) and Remaining Useful Life (RUL in Days)                           │
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
