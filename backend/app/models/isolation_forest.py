"""
SkyGuard AI - Multivariate Isolation Forest Outlier Detector
Evaluates multi-dimensional feature space (T, P, RH, rate-of-change, VPD, dew point depression)
using unsupervised Isolation Forest density scoring.
"""

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from typing import Dict, Any, List, Optional


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

    def _pretrain_baseline(self):
        """
        Generates synthetic clean baseline meteorological data covering standard diurnal variations
        to initialize the isolation tree estimators.
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

        X_baseline = np.column_stack([
            temps, pressures, humidities,
            d_temp, d_pres, d_hum,
            vpd, dp_depression
        ])

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
