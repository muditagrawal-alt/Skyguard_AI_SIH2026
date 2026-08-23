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

REAL_DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "real_stations" / "processed"


class MultivariateOutlierDetector:
    def __init__(self):
        self.scaler = StandardScaler()
        self.model = IsolationForest(
            n_estimators=100,
            contamination=0.03,
            random_state=42,
            n_jobs=-1
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
                station_rows = list(reader)

            prev_t, prev_p, prev_h = None, None, None
            for r in station_rows:
                t, pres, h = float(r["temperature_c"]), float(r["pressure_hpa"]), float(r["humidity_pct"])
                d_t = abs(t - prev_t) if prev_t is not None else 0.0
                d_p = abs(pres - prev_p) if prev_p is not None else 0.0
                d_h = abs(h - prev_h) if prev_h is not None else 0.0
                vpd = physics_engine.vapor_pressure_deficit(t, h)
                td = physics_engine.dew_point(t, h)
                dp_dep = max(0.0, t - td)
                rows.append([t, pres, h, d_t, d_p, d_h, vpd, dp_dep])
                prev_t, prev_p, prev_h = t, pres, h

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
        features = np.array([[
            temp_c, pressure_hpa, humidity_pct,
            d_temp, d_pres, d_hum,
            vpd, dew_point_depression
        ]])

        features_scaled = self.scaler.transform(features)
        
        # Decision function: positive means normal, negative means abnormal
        raw_score = float(self.model.decision_function(features_scaled)[0])
        
        if raw_score >= 0.05:
            anomaly_prob = max(0.0, 0.15 - (raw_score * 0.5))
        elif raw_score >= 0.0:
            anomaly_prob = 0.20 + ((0.05 - raw_score) * 2.0)
        else:
            # Outlier region (raw_score < 0)
            anomaly_prob = min(1.0, 0.50 + abs(raw_score) * 3.5)

        is_anomaly = raw_score < 0.0

        return {
            "isolation_score": round(raw_score, 4),
            "isolation_anomaly_prob": round(float(anomaly_prob), 4),
            "is_multivariate_outlier": is_anomaly
        }


multivariate_detector = MultivariateOutlierDetector()
