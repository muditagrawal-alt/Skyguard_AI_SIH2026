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

    def update(self, x: float, target_mean: float, std_dev: float, slack_scale: float = 1.0) -> Dict[str, Any]:
        """
        `slack_scale` raises the effective slack `k` for longer inter-sample gaps
        (see StatisticalEngine.process()). CUSUM's whole design is to accumulate
        evidence from any SUSTAINED same-direction deviation above the slack -- which
        is exactly right for near-independent per-step noise (the synthetic
        generator's ~0.05C/step Gaussian), but real weather is autocorrelated at
        real sampling intervals: an ordinary multi-hour warming trend produces a
        z of ~1-1.5 sustained for many consecutive REAL hours, which is completely
        normal persistence, not drift. Widening the slack means only distinctly
        larger per-step deviations count as evidence at longer intervals; it does
        NOT touch the z-score itself, so a genuinely large single-step anomaly
        (a spike) is still exactly as detectable regardless of interval.
        """
        if std_dev < 0.5:
            std_dev = 0.5

        z = (x - target_mean) / std_dev
        k = self.k * max(1.0, slack_scale)

        self.s_pos = max(0.0, (self.s_pos * self.decay) + z - k)
        self.s_neg = max(0.0, (self.s_neg * self.decay) - z - k)

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

    def process(
        self, station_id: str, temp_c: Optional[float], pressure_hpa: Optional[float],
        humidity_pct: Optional[float], dt_seconds: float = 60.0
    ) -> Dict[str, Any]:
        """
        `dt_seconds`: elapsed time since the previous reading. Every synthetic-path
        caller (tests, benchmark, UI, API) passes dt_seconds=1.0, which is this
        filter's implicit no-scaling reference point (not the diurnal clock's
        separate "1 step = 1 simulated minute" convention -- a different number).

        An earlier version of this scaled the z-score's own std_dev by sqrt(dt),
        which fixed real-data false positives but collapsed calibration-drift and
        spike recall on the same real-data benchmark (drift: ~0% at real hourly
        cadence, since a sqrt(3600)=60x-inflated std_dev buries almost any real
        deviation). The z-score itself is accurate and adaptive already -- it does
        not need dt-scaling. What actually needs it is CUSUM's slack `k`: CUSUM
        accumulates evidence from ANY sustained same-direction deviation above the
        slack, which is correct for the synthetic generator's near-independent
        per-step noise, but real weather is autocorrelated at real sampling
        intervals -- an ordinary multi-hour warming trend produces a middling z
        sustained for many consecutive real hours, which CUSUM's design otherwise
        reads as drift. `cusum_slack_scale` widens the slack (capped, and only
        applied to CUSUM) so ordinary persistence stops accumulating as evidence
        without touching single-step anomaly sensitivity (spike, flatline) at all.
        Capped at 3x rather than following dt linearly/via sqrt: real calibration
        drift still needs to be catchable within a plausible detection window, and
        an unbounded scale-up (60x under a naive sqrt(3600)) makes that impossible.
        """
        self._init_station(station_id)
        cusum_slack_scale = min(3.0, 1.0 + math.log10(max(dt_seconds, 1.0)))

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
            c_res = self.cusum[station_id][sensor].update(val, mean, std, slack_scale=cusum_slack_scale)
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
