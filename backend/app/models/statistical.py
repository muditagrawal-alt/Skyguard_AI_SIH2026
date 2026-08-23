"""
SkyGuard AI - Streaming Statistical Filters
Implements Adaptive EWMA Rolling Baseline, Flatline (ADC Stuck) Detector,
and Decaying CUSUM change-point detection tailored for diurnal meteorological streams.
"""

import math
from typing import Dict, Any, List, Optional


class AdaptiveRollingBaseline:
    """
    Tracks local rolling mean and standard deviation with exponential smoothing,
    adapting to natural diurnal heating/cooling cycles while detecting sudden shocks.
    """
    def __init__(self, alpha: float = 0.05, warmup_steps: int = 15):
        self.alpha = alpha
        self.mean = None
        self.var = 1.0
        self.count = 0
        self.warmup_steps = warmup_steps

    def update(self, x: float) -> tuple:
        self.count += 1
        if self.mean is None:
            self.mean = x
            self.var = 1.0
            return self.mean, 1.0, 0.0

        # Update running variance and mean
        diff = x - self.mean
        self.mean += self.alpha * diff
        self.var = max(0.25, (1.0 - self.alpha) * (self.var + self.alpha * (diff ** 2)))
        std_dev = math.sqrt(self.var)

        if self.count < self.warmup_steps or std_dev < 0.2:
            z_score = 0.0
        else:
            z_score = diff / std_dev

        return self.mean, std_dev, z_score


class FlatlineDetector:
    """
    Detects stuck sensor floats (zero variance / identical values repeating).
    """
    def __init__(self, threshold_steps: int = 5):
        self.threshold_steps = threshold_steps
        self.last_value = None
        self.identical_count = 0

    def update(self, x: Optional[float]) -> tuple:
        if x is None:
            return False, 0.0
            
        if self.last_value is not None and abs(x - self.last_value) < 1e-5:
            self.identical_count += 1
        else:
            self.last_value = x
            self.identical_count = 1

        is_flatline = self.identical_count >= self.threshold_steps
        flatline_score = min(1.0, self.identical_count / float(self.threshold_steps)) if is_flatline else 0.0
        return is_flatline, flatline_score


class CUSUMDetector:
    """
    CUSUM filter with memory decay for tracking rapid calibration drift
    relative to adaptive rolling baseline.
    """
    def __init__(self, drift_slack: float = 0.6, threshold: float = 3.5, decay: float = 0.95):
        self.k = drift_slack    # Allowable slack
        self.h = threshold      # Detection threshold
        self.decay = decay      # Exponential decay
        self.s_pos = 0.0
        self.s_neg = 0.0

    def update(self, x: float, target_mean: float, std_dev: float) -> Dict[str, Any]:
        if std_dev < 0.5:
            std_dev = 0.5
            
        z = (x - target_mean) / std_dev
        
        self.s_pos = max(0.0, (self.s_pos * self.decay) + z - self.k)
        self.s_neg = max(0.0, (self.s_neg * self.decay) - z - self.k)

        is_drift_positive = self.s_pos > self.h
        is_drift_negative = self.s_neg > self.h
        
        drift_score = min(1.0, max(self.s_pos, self.s_neg) / self.h)
        is_drift = is_drift_positive or is_drift_negative
        
        return {
            "s_pos": round(self.s_pos, 2),
            "s_neg": round(self.s_neg, 2),
            "is_drift": is_drift,
            "drift_score": round(drift_score, 4)
        }

    def reset(self):
        self.s_pos = 0.0
        self.s_neg = 0.0


class StatisticalEngine:
    def __init__(self):
        self.baselines: Dict[str, Dict[str, AdaptiveRollingBaseline]] = {}
        self.flatline: Dict[str, Dict[str, FlatlineDetector]] = {}
        self.cusum: Dict[str, Dict[str, CUSUMDetector]] = {}

    def _init_station(self, station_id: str):
        if station_id not in self.baselines:
            self.baselines[station_id] = {
                "temperature": AdaptiveRollingBaseline(alpha=0.20),
                "pressure": AdaptiveRollingBaseline(alpha=0.20),
                "humidity": AdaptiveRollingBaseline(alpha=0.20)
            }
            self.flatline[station_id] = {
                "temperature": FlatlineDetector(),
                "pressure": FlatlineDetector(),
                "humidity": FlatlineDetector()
            }
            self.cusum[station_id] = {
                "temperature": CUSUMDetector(),
                "pressure": CUSUMDetector(),
                "humidity": CUSUMDetector()
            }

    def process(self, station_id: str, temp_c: Optional[float], pressure_hpa: Optional[float], humidity_pct: Optional[float]) -> Dict[str, Any]:
        self._init_station(station_id)
        
        readings = {
            "temperature": temp_c,
            "pressure": pressure_hpa,
            "humidity": humidity_pct
        }

        z_scores = {}
        cusum_scores = {}
        flatline_flags = []
        flatline_scores = []
        drift_flags = []

        for sensor, val in readings.items():
            if val is None:
                continue

            # Update Flatline Detector
            is_flat, f_score = self.flatline[station_id][sensor].update(val)
            flatline_scores.append(f_score)
            if is_flat:
                flatline_flags.append(f"{sensor.capitalize()} sensor flatline / invariant float detected")

            # Update Adaptive Baseline
            mean, std, z = self.baselines[station_id][sensor].update(val)
            z_scores[sensor] = z

            # Update CUSUM
            c_res = self.cusum[station_id][sensor].update(val, mean, std)
            cusum_scores[sensor] = c_res["drift_score"]
            if c_res["is_drift"]:
                drift_flags.append(f"{sensor.capitalize()} persistent drift detected (CUSUM score: {c_res['drift_score']:.2f})")

        max_abs_z = max([abs(z) for z in z_scores.values()]) if z_scores else 0.0
        norm_z_score = min(1.0, max_abs_z / 4.0)
        max_cusum = max(cusum_scores.values()) if cusum_scores else 0.0
        max_flatline = max(flatline_scores) if flatline_scores else 0.0

        # Unified statistical anomaly score
        stat_anomaly_score = max(norm_z_score, max_cusum, max_flatline)

        return {
            "z_scores": {k: round(v, 2) for k, v in z_scores.items()},
            "cusum_scores": {k: round(v, 3) for k, v in cusum_scores.items()},
            "is_flatline": len(flatline_flags) > 0,
            "flatline_flags": flatline_flags,
            "stat_anomaly_score": round(stat_anomaly_score, 4),
            "drift_flags": drift_flags
        }


statistical_engine = StatisticalEngine()
