# SkyGuard AI: Operational Use Cases & Scenarios

This document explains five real-world meteorological operations and how SkyGuard AI protects data integrity.

---

## Use Case 1: Severe Convective Thunderstorm vs. Sensor Spike

### Scenario:
A high-impact convective thunderstorm arrives at an airport AWS (`AWS_GAMMA_URBAN`). Within 3 minutes:
- Temperature drops rapidly by $-7.5^\circ\text{C}$ (rain-cooled downdraft).
- Relative Humidity surges from $55\%$ to $97\%$ (precipitation saturation).
- Barometric Pressure spikes by $+2.5\text{ hPa}$ (gust front pressure nose) before dropping.

### Traditional Quality Control Failure:
Traditional threshold-based QC flags this rapid rate of change as an anomaly and rejects the data, blinding air traffic controllers and numerical weather forecast models during severe weather.

### SkyGuard AI Solution:
1. **Multivariate Physics Engine**: Confirms that $T \ge T_d$ (no thermodynamic boundary broken).
2. **Coupled Response Validation**: Confirms that cooling is accompanied by humidity surge and barometric gust nose.
3. **Classification & Action**: Classifies stream as `GENUINE_EXTREME_WEATHER` with **0% False Alarm**, transmits true readings, and triggers a Severe Storm Advisory.

---

## Use Case 2: ADC Freezing / Icing Over at High-Altitude Mountain Station

### Scenario:
At `AWS_ALPHA_MOUNTAIN` (Elevation: 2,150 m), sub-zero moisture causes the mechanical temperature transducer or the analog-to-digital converter (ADC) buffer to freeze, outputting the exact same value `12.400000°C` for 3 hours.

### SkyGuard AI Solution:
1. **Flatline Detector**: Flags invariant float after 5 consecutive identical readings.
2. **XAI Diagnostic**: Outputs *"❄️ SENSOR FLATLINE DETECTED (Sensor Transducer / ADC Lockup). Constant float detected."*
3. **Self-Healing Imputation**: Reconstructs the expected diurnal solar trajectory based on solar phase and historical trends.
4. **Maintenance Tracker**: Updates sensor health index to `DEGRADED`, decrementing Remaining Useful Life (RUL) and recommending field inspection.

---

## Use Case 3: Progressive Calibration Drift on Coastal Marine Station

### Scenario:
At `AWS_BETA_COASTAL`, salt spray and humidity film slowly contaminate the capacitive hygrometer, causing relative humidity readings to drift upward by $+0.3\%$/hour over several days.

### SkyGuard AI Solution:
1. **Decaying CUSUM Engine**: Accumulates the continuous one-sided positive residual against the adaptive rolling baseline.
2. **Drift Detection**: Triggers `CALIBRATION_DRIFT` alert once CUSUM exceeds threshold.
3. **Self-Healing Engine**: Subtracts cumulative drift to supply bias-corrected humidity readings to numerical forecasting models.

---

## Use Case 4: Power Supply Noise & Electrical Transient Spikes

### Scenario:
A solar inverter switching transient introduces high-voltage noise, causing an instantaneous spike of $+16.0^\circ\text{C}$ on temperature for a single timestep with no change in pressure or humidity.

### SkyGuard AI Solution:
1. **WMO Gradient Filter & Isolation Forest**: Trips the rate-of-change limit ($>3^\circ\text{C}/\text{min}$) and identifies high multivariate isolation score.
2. **XAI Attribution**: Flags temperature as contributing 82% of the anomaly score.
3. **Self-Healing Action**: Replaces the spike with the smooth temporal moving-average value ($24.8^\circ\text{C}$), completely insulating downstream weather forecasting pipelines from erroneous data.

---

## Use Case 5: Telemetry Packet Loss & Corrupted Transmissions

### Scenario:
A remote desert station (`AWS_DELTA_DESERT`) loses cellular packets during a dust storm, resulting in `None` / `NaN` readings and corrupted bits.

### SkyGuard AI Solution:
1. **Telemetry Detector**: Flags `COMMUNICATION_DROPOUT`.
2. **Autoregressive Imputer**: Automatically fills missing timestamps with physics-constrained estimates until telemetry is restored.
