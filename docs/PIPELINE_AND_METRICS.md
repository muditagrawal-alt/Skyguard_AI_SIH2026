# SkyGuard AI — Pipeline Architecture & Model Metrics

**Problem Statement 26073** — AI/ML-Based Intelligent Anomaly Detection for Automatic Weather Stations
Parameters monitored: Temperature (°C), Atmospheric Pressure (hPa), Relative Humidity (%)

All figures in this document are **measured, seeded (`--seed 42`), and reproducible** — two consecutive
runs of any benchmark produce byte-identical KPIs. Regenerate everything with the commands in
[§7 Reproducing these numbers](#7-reproducing-these-numbers).

---

## 1. What the system does

Ingests a stream of AWS readings and, for every single observation, decides three things:

1. **Is this anomalous?** — a 0.0–1.0 confidence score from a four-model ensemble.
2. **If so, why?** — one of seven root causes, critically including whether it is a *genuine
   weather event* rather than a sensor fault. A thunderstorm and a broken thermometer both look
   "anomalous" to a naive detector; conflating them is the single most expensive failure mode for
   an operational met network, and separating them is what most of this pipeline exists to do.
3. **What should the value have been?** — a self-healed replacement so downstream forecasting
   never sees a gap.

---

## 2. Pipeline architecture

A single observation flows through ten stages. Everything is streaming and stateful per station —
there is no batch retraining step in the hot path.

```
   AWS reading  (T, P, RH, timestamp, station_id)
        │
        ▼
  ┌──────────────────────────────────────────────────────────────────┐
  │ 1. PHYSICS ENGINE                    backend/app/core/physics.py │
  │    Magnus-Tetens saturation vapour pressure -> dew point, VPD.   │
  │    WMO range + rate-of-change limits, scaled by real elapsed dt. │
  │    Hard law: dew point can never exceed air temperature.         │
  └──────────────────────────────────────────────────────────────────┘
        │
        ▼
  ┌──────────────────────────────────────────────────────────────────┐
  │ 2. CLIMATOLOGY DESEASONALIZATION  backend/app/core/climatology.py │
  │    (real-data path only) Subtracts this station's real per-hour   │
  │    historical mean, so the statistical stage sees a residual      │
  │    rather than raw diurnal swing.                                 │
  └──────────────────────────────────────────────────────────────────┘
        │
        ▼
  ┌───────────── 4 DETECTION MODELS, scored in parallel ─────────────┐
  │  3. STATISTICAL      Adaptive EWMA z-score + decaying CUSUM +     │
  │                      flatline detector    (models/statistical.py) │
  │  4. ISOLATION FOREST 8-feature multivariate density outlier       │
  │                                     (models/isolation_forest.py)  │
  │  5. AUTOENCODER      15-step trajectory reconstruction residual   │
  │                                         (models/autoencoder.py)   │
  │     ( + the physics score from stage 1 )                          │
  └──────────────────────────────────────────────────────────────────┘
        │
        ▼
  ┌──────────────────────────────────────────────────────────────────┐
  │ 6. ENSEMBLE META-SCORER              models/ensemble.py           │
  │    Weighted consensus -> confidence 0..1 -> severity band.        │
  │    Weights: physics .45 | IF .20 | statistical .20 | AE .15       │
  └──────────────────────────────────────────────────────────────────┘
        │
        ▼
  ┌──────────────────────────────────────────────────────────────────┐
  │ 7. CROSS-STATION SPATIAL CONSISTENCY      core/pipeline.py        │
  │    Are neighbouring stations anomalous at the same moment?        │
  │    Corroboration -> genuine regional weather. Isolation -> local  │
  │    fault. (Loosens the weather gate only; see §6 for why.)        │
  └──────────────────────────────────────────────────────────────────┘
        │
        ▼
  ┌──────────────────────────────────────────────────────────────────┐
  │ 8. ROOT-CAUSE CLASSIFIER                  xai/root_cause.py       │
  │    NORMAL | GENUINE_EXTREME_WEATHER | SENSOR_SPIKE |              │
  │    SENSOR_FLATLINE | CALIBRATION_DRIFT |                          │
  │    PHYSICAL_INCONSISTENCY | COMMUNICATION_DROPOUT                 │
  └──────────────────────────────────────────────────────────────────┘
        │
        ├──────────────────────────┬───────────────────────────┐
        ▼                          ▼                           ▼
  ┌──────────────┐   ┌───────────────────────┐   ┌──────────────────────┐
  │ 9. XAI       │   │ 10. SELF-HEALING      │   │ 10b. SENSOR HEALTH   │
  │ attributions │   │ imputation            │   │ score, RUL, advisory │
  │ + plain-text │   │ (physics-constrained) │   │                      │
  │ explanation  │   │                       │   │                      │
  └──────────────┘   └───────────────────────┘   └──────────────────────┘
```

**Latency:** ~4.9 ms/reading synthetic, ~5.3 ms real (p95 5.4 ms) — comfortably real-time.

---

## 3. The four detection models

| # | Model | Type | What it catches | Why it's in the ensemble |
|---|---|---|---|---|
| 1 | **Physics engine** | Deterministic rules (Magnus-Tetens thermodynamics) | Impossible states: dew point > air temp, out-of-range values, unphysical rate-of-change | Highest precision of any component (99.5% on real data). Reasons from first principles, so it does not inherit any training-set bias. |
| 2 | **Statistical** | Adaptive EWMA z-score + decaying CUSUM + flatline counter | Sudden shocks, sustained calibration drift, stuck ADC | Strongest single detector on synthetic data (86.2% F1); best recall-per-cost. |
| 3 | **Isolation Forest** | Unsupervised density (scikit-learn, 100 trees, 8 features) | Multivariate combinations that are individually plausible but jointly rare | Only component that sees T/P/RH *jointly* with gradients and psychrometrics. |
| 4 | **Autoencoder** | PyTorch MLP, 45→32→16→**6**→16→32→45 | Trajectory shape anomalies over a 15-step window | Catches temporal-shape faults the others miss; weakest component, weighted lowest (0.15). |

**Training data:** Isolation Forest and Autoencoder are trained on synthetic baseline data **blended with
46,096 real NOAA ISD-Lite observations** across 4 real stations, 2021–2023 (see
`data/real_stations/STATION_SOURCES.md`). The physics engine and statistical filters require no training.

---

## 4. Metrics — full pipeline (the headline numbers)

The full pipeline = 4-model ensemble **+** root-cause classification **+** spatial consistency.

| Metric | Synthetic generator | **Real NOAA history** |
|---|---|---|
| Precision | 99.12% | **96.43%** |
| Recall | 92.56% | **88.29%** |
| **F1-Score** | **95.73%** | **92.18%** |
| False alarms | 0.00% *(on genuine storms)* | **0.61%** *(on real un-injected weather)* |
| Mean latency | 4.925 ms | 5.331 ms |
| Observations scored | 610 | 6,000 |

> ### Which number should you quote?
> **The real-data one — 92.18% F1.**
>
> The synthetic figure is measured against data this codebase generates itself, with faults this
> codebase injects, scored by an evaluator in the same repository. It is a useful *regression test*
> but it is graded-on-its-own-homework and is structurally optimistic. The real-data benchmark
> replays genuine historical hourly weather as the background signal and injects the same
> controlled faults on top, so its false-positive rate is measured against real, unmodelled
> atmospheric variability. That is the honest estimate of field performance.
>
> **No train/test leakage.** The first 1,530 rows of every station file are a strict
> evaluation holdout — the isolation forest, the autoencoder, and the hourly climatology are
> all forbidden to train on them (`backend/app/core/data_split.py`, asserted at benchmark
> import time so the two windows cannot drift apart). This was originally violated; fixing it
> moved F1 by +0.1 points, because the two highest-weighted components — physics (0.45) and
> statistical (0.20) — do not train on data at all.

### Per-station (real data)

| Station | Real analog | Accuracy | False positives |
|---|---|---|---|
| `AWS_GAMMA_URBAN` | Safdarjung, Delhi | 98.6% | 0.00% |
| `AWS_DELTA_DESERT` | Jaisalmer | 98.3% | 0.08% |
| `AWS_BETA_COASTAL` | Bombay/Colaba | 98.5% | 0.63% |
| `AWS_ALPHA_MOUNTAIN` | Flagstaff, AZ (KFLG) | 94.8% | 1.98% |

Flagstaff is consistently the hardest — real continental-mountain winter weather has large, fast
frontal swings that most closely resemble sensor faults.

### Recall by fault type (real data)

| Fault type | Detected / injected | Recall |
|---|---|---|
| Thermodynamic violation | 180 / 180 | **100.0%** |
| Sensor flatline | 216 / 240 | 90.0% |
| Calibration drift | 204 / 240 | 85.0% |
| Packet loss | 150 / 180 | 83.3% |
| Sensor spike | 85 / 108 | 78.7% |

---

## 5. Metrics — per model, standalone

Each component measured **alone**, thresholded at the ensemble's own cutoff (0.35), with no
root-cause reasoning. `run_component_analysis.py` produces this table.

**AUC is threshold-free** — it measures how much discriminative signal a score carries regardless of
where the cutoff sits. This is what distinguishes *"this model is weak"* (low AUC → replace the model)
from *"this model is mis-thresholded"* (high AUC, low F1 → recalibrate). That distinction drove most
of the tuning work in this project.

### Synthetic generator (610 observations)

| Component | Precision | Recall | F1 | AUC |
|---|---|---|---|---|
| Statistical | 100.0% | 75.8% | **86.2%** | 90.1% |
| Isolation Forest | 87.7% | 41.9% | 56.7% | 58.3% |
| Physics | 85.8% | 35.7% | 50.4% | 64.0% |
| Autoencoder | 100.0% | 9.3% | 17.0% | 69.4% |
| **Ensemble (all 4)** | 93.9% | 91.0% | **92.4%** | 91.5% |

### Real NOAA history (6,000 observations)

| Component | Precision | Recall | F1 | AUC |
|---|---|---|---|---|
| Physics | **99.5%** | 65.0% | **78.6%** | 82.5% |
| Statistical | 67.5% | 62.8% | 65.0% | 83.7% |
| Isolation Forest | 57.6% | 44.6% | 50.3% | 79.5% |
| Autoencoder | 28.0% | 35.4% | 31.3% | 70.4% |
| **Ensemble (all 4)** | 94.4% | 88.8% | **91.5%** | **97.0%** |

### Reading this table

- **The ensemble massively outperforms every part of it.** Best single component on real data is
  78.6% F1; combined they reach 91.5%, at 97.0% AUC. The four models fail on *different* inputs, which
  is exactly what an ensemble is for.
- **Degradation is not uniform.** Physics gets **better** on real data (50.4% → 78.6% F1) because it
  reasons from thermodynamics rather than learned patterns. Only the learned/statistical components
  lose ground.
- **The autoencoder is the weakest link** on both sources and is weighted accordingly (0.15).

---

## 6. Known limitations — stated plainly

1. **Self-healing imputation MAE is 2.28 °C** against a < 1.0 °C target. The imputer has no notion of
   elapsed time, so during a long outage it holds the last trend instead of tracking where the diurnal
   cycle should be. Error grows with outage length. Fine for short gaps; a diurnal-aware fallback is
   the fix.
2. **Spatial consistency is under-exercised.** The four demo stations are continents apart, so a
   genuine storm at one is *always* isolated relative to the others. The check therefore only
   *loosens* the weather gate on corroboration and never tightens it on isolation — an earlier version
   that tightened on isolation was measured pushing a genuine single-station storm's false-alarm rate
   from ~16% to 87.5%. On a real, dense mesonet this check becomes far more powerful.
3. **Calibration drift (85.0% recall) is the hardest fault class.** Distinguishing slow sensor drift
   from slow genuine weather change using one station's own history is information-theoretically hard;
   neighbouring stations, not a better model, are the real solution.
4. **The C edge header has never been compiled.** `edge/skyguard_edge.h` is behaviourally consistent
   with its Python counterpart, but "ESP32-ready" is unverified without a PlatformIO build.
5. **No CI.** Every check in this document was run manually.

### Data-agnosticism

The pipeline carries no assumptions about *which* station or *what kind* of data it is fed.
Audited and fixed before shipping: hardcoded "typical value" fallbacks (25 °C / 1000 hPa / 60 %)
that corrupted high-altitude and polar stations, physical bounds that were really mid-latitude
lowland ranges (a legitimate −55 °C Antarctic reading was being clamped to −40 °C), a default
station ID that merged unattributed packets into a real station's detection state, an imputer
that fell back to another site's baseline profile, and a data-source name hardcoded into the
deseasonalization gate. Verified end-to-end: an unknown station at −55 °C / 680 hPa now passes
through untouched, while a broken sensor (300 °C, −5 hPa, RH 5000 %) is still caught.

---

## 7. Reproducing these numbers

```bash
# one-time: download real NOAA station data (~30s)
python data/real_stations/fetch_and_process.py

python -m pytest backend/tests/ -q              # 11 unit tests
python benchmark/run_benchmark.py --seed 42     # synthetic KPIs
python benchmark/run_real_data_benchmark.py --seed 42   # real-data KPIs  <-- the honest one
python benchmark/run_component_analysis.py      # the per-model tables in §5
python benchmark/run_spatial_consistency_benchmark.py   # cross-station demo
python benchmark/run_shap_analysis.py           # genuine offline SHAP
```

Generated reports land in `benchmark/*.md`. All are deterministic — re-running produces identical
numbers, which was itself a bug fix during development (`torch.manual_seed()` was being called one
line *after* the model's weights were already randomly initialized, so "seeded" runs silently differed).

---

## 8. Explainability

- **Live, per-packet** (UI + API): a fast additive attribution heuristic, chosen to stay inside the
  <10 ms real-time budget. **This is not SHAP** and is labelled as such everywhere it appears.
- **Offline**: genuine SHAP values (`shap.KernelExplainer`) computed against the Isolation Forest over
  a real-data background set — `benchmark/run_shap_analysis.py` → `benchmark/shap_analysis_report.md`.
- Every flagged anomaly also carries a plain-language diagnostic explanation and is written to an
  exportable audit log (CSV) in the UI.

### How the decision reaches the operator (dashboard surface)

The React operator dashboard (`frontend/`) presents each packet as a fault-vs-weather **verdict**
plus an explicit **root-cause readout**. Two points matter for interpreting what is on screen:

- **Two different confidences, shown separately.** The **ensemble confidence** (this document's
  metrics) answers *"is this anomalous?"*; the **root-cause classifier** carries its own per-rule
  confidence answering *"is it *this specific* fault?"* — e.g. a communication dropout is asserted at
  0.99, a calibration-drift call at 0.88. The dashboard shows both side by side and labels them, so
  the classifier's confidence is never mistaken for the detection score, nor the reverse.
- **Confidence is display-capped just below 100%, with a ± band.** The rendered percentage is capped
  and annotated with a ± agreement band (the spread across the four component scores). This is a
  presentation choice in the UI layer only — `models/ensemble.py` is unchanged and every KPI above
  uses the raw scores. The cap exists because a live detector rendering a literal "100.0%" would
  overstate a certainty that the numbers in §4–§5 do not support.

When the backend is unreachable the dashboard shows built-in demo data behind a labelled "Demo mode"
badge rather than fabricating a live feed — the same honesty principle applied to the interface.
