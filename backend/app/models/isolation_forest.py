"""
SkyGuard AI - Multivariate Isolation Forest Outlier Detector
Evaluates multi-dimensional feature space (T, P, RH, rate-of-change, VPD, dew point depression)
using unsupervised Isolation Forest density scoring.
"""

import csv
from pathlib import Path

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from typing import Dict, Any, List, Optional

from backend.app.core.physics import physics_engine
from backend.app.core.data_split import training_rows

REAL_DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "real_stations" / "processed"


class MultivariateOutlierDetector:
    def __init__(self):
        self.scaler = StandardScaler()
        self.model = IsolationForest(
            n_estimators=100,
            contamination=0.03,
            random_state=42,
            # n_jobs=1, not -1: every call here scores a single reading, so there's
            # no batch to parallelize -- multi-threading only adds thread-pool
            # overhead with no benefit, and removes any doubt about it as a source
            # of run-to-run nondeterminism alongside the autoencoder's (see
            # autoencoder.py's torch.set_num_threads(1) for the confirmed case).
            n_jobs=1
        )
        self.is_fitted = False
        self._pretrain_baseline()

    def _load_real_features(self) -> Optional[np.ndarray]:
        """
        Builds the same 8-column feature space from real NOAA ISD-Lite observations
        (see data/real_stations/), if the processed CSVs are present. Per-station
        chronological consecutive-row diffs approximate d_temp/d_pres/d_hum; VPD and
        dew-point-depression are computed with the project's own physics engine so
        real rows are scored on identical features to synthetic ones. Returns None
        if no processed real data is available (fresh clone, fetch script not run).
        """
        if not REAL_DATA_DIR.is_dir():
            return None

        rows = []
        for csv_path in sorted(REAL_DATA_DIR.glob("*.csv")):
            with open(csv_path, newline="") as f:
                reader = csv.DictReader(f)
                # Train only on rows outside the benchmark's evaluation window --
                # see backend/app/core/data_split.py for why.
                station_rows = training_rows(list(reader))

            prev_t, prev_p, prev_h = None, None, None
            skipped = 0
            for r in station_rows:
                # A single malformed row (non-numeric field, missing column, stray
                # blank line) must NOT crash backend import: this loader runs at
                # module load time while constructing the singleton detector, so an
                # unguarded float() here would take down the whole API on startup
                # over one bad line in a data file. Skip the bad row and continue;
                # the model simply trains on the rows that parse cleanly.
                try:
                    t = float(r["temperature_c"])
                    pres = float(r["pressure_hpa"])
                    h = float(r["humidity_pct"])
                except (KeyError, ValueError, TypeError):
                    skipped += 1
                    continue
                d_t = abs(t - prev_t) if prev_t is not None else 0.0
                d_p = abs(pres - prev_p) if prev_p is not None else 0.0
                d_h = abs(h - prev_h) if prev_h is not None else 0.0
                vpd = physics_engine.vapor_pressure_deficit(t, h)
                td = physics_engine.dew_point(t, h)
                dp_dep = max(0.0, t - td)
                rows.append([t, pres, h, d_t, d_p, d_h, vpd, dp_dep])
                prev_t, prev_p, prev_h = t, pres, h
            if skipped:
                print(f"[isolation_forest] {csv_path.name}: skipped {skipped} malformed row(s) during feature load")

        return np.array(rows, dtype=np.float64) if rows else None

    def _pretrain_baseline(self):
        """
        Fits the isolation tree estimators on synthetic diurnal baseline data blended
        with real NOAA ISD-Lite observations (when available) so the model recognizes
        both the synthetic generator's station-level pressure convention and real
        stations' sea-level-pressure convention as normal background variation --
        see data/real_stations/STATION_SOURCES.md for why these two ranges differ.
        """
        np.random.seed(42)
        n_samples = 3000

        # Simulate normal multi-station conditions
        temps = np.random.uniform(5.0, 40.0, n_samples)
        pressures = np.random.uniform(800.0, 1025.0, n_samples)
        humidities = np.clip(100.0 - (temps * 1.8) + np.random.normal(0, 10, n_samples), 10.0, 95.0)

        # Gradients
        d_temp = np.random.normal(0, 0.1, n_samples)
        d_pres = np.random.normal(0, 0.15, n_samples)
        d_hum = np.random.normal(0, 0.3, n_samples)

        # Psychrometrics
        vpd = np.clip((40.0 - temps) * (1.0 - (humidities / 100.0)), 0.0, 50.0)
        dp_depression = np.clip((100.0 - humidities) / 5.0, 0.0, 30.0)

        X_synthetic = np.column_stack([
            temps, pressures, humidities,
            d_temp, d_pres, d_hum,
            vpd, dp_depression
        ])

        X_real = self._load_real_features()
        if X_real is not None:
            X_baseline = np.vstack([X_synthetic, X_real])
            self.real_data_samples = len(X_real)
        else:
            X_baseline = X_synthetic
            self.real_data_samples = 0

        X_scaled = self.scaler.fit_transform(X_baseline)
        self.model.fit(X_scaled)
        self.is_fitted = True

    def score_observation(
        self,
        temp_c: float,
        pressure_hpa: float,
        humidity_pct: float,
        d_temp: float = 0.0,
        d_pres: float = 0.0,
        d_hum: float = 0.0,
        vpd: float = 0.0,
        dew_point_depression: float = 0.0
    ) -> Dict[str, Any]:
        """
        Calculates multivariate anomaly score on a single observation.
        Returns outlier probability in range [0.0, 1.0].
        """
        # Defense-in-depth against a partial/dropped packet. StandardScaler.transform
        # on an array containing None raises (object-dtype TypeError on numpy<2, or
        # "Input contains NaN" on numpy>=2), which previously surfaced as an HTTP 500
        # on any batch containing a reading missing pressure or humidity. The pipeline
        # already guards this path (see core/pipeline.py), but a direct caller must not
        # be able to crash the detector: a reading we cannot fully feature-ize is
        # treated as missing telemetry, mirroring the pipeline's packet-loss result.
        if any(v is None for v in (
            temp_c, pressure_hpa, humidity_pct,
            d_temp, d_pres, d_hum, vpd, dew_point_depression
        )):
            return {
                "isolation_score": -0.5,
                "isolation_anomaly_prob": 0.95,
                "is_multivariate_outlier": True
            }

        features = np.array([[
            temp_c, pressure_hpa, humidity_pct,
            d_temp, d_pres, d_hum,
            vpd, dew_point_depression
        ]])

        features_scaled = self.scaler.transform(features)
        
        # Decision function: positive means normal, negative means abnormal
        raw_score = float(self.model.decision_function(features_scaled)[0])
        
        # Smooth monotonic logistic mapping of the decision function to [0, 1].
        # Replaces a 3-branch piecewise mapping that had a hard DISCONTINUITY at
        # raw_score = 0: a reading at raw=+0.001 scored 0.30, while raw=-0.001 --
        # a numerically indistinguishable neighbour -- jumped straight to 0.50,
        # above the ensemble's 0.35 anomaly cutoff. Since IsolationForest's
        # decision_function crosses zero at the `contamination` quantile (3%) of
        # the TRAINING distribution, real readings sit near that boundary
        # constantly, so that cliff converted ordinary boundary noise into
        # confident anomaly calls. A logistic is continuous, monotonically
        # decreasing in raw_score, and keeps the same "0 means maximally
        # uncertain" centre without the cliff on either side of it.
        # Steepness and offset are chosen so the curve passes through the ensemble's
        # own 0.35 anomaly cutoff exactly at raw_score = 0 -- preserving this
        # detector's established decision boundary (`is_anomaly = raw_score < 0`,
        # the contamination quantile) rather than silently shifting it, while the
        # steepness keeps clearly-normal readings (raw ~ +0.12 in the measured real
        # data) down near 0.03 instead of loitering just under the cutoff.
        # offset = ln(1/0.35 - 1) = 0.619 puts prob(raw=0) = 0.35.
        anomaly_prob = 1.0 / (1.0 + np.exp(25.0 * raw_score + 0.619))

        is_anomaly = raw_score < 0.0

        return {
            "isolation_score": round(raw_score, 4),
            "isolation_anomaly_prob": round(float(anomaly_prob), 4),
            "is_multivariate_outlier": is_anomaly
        }


multivariate_detector = MultivariateOutlierDetector()
