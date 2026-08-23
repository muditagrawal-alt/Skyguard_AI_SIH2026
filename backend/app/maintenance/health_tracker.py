"""
SkyGuard AI - Predictive Sensor Maintenance & Health Radar Engine
Tracks sensor Signal-to-Noise Ratio (SNR), drift accumulation, glitch frequencies,
and calculates Sensor Health Index (0-100%) and Remaining Useful Life (RUL) advisory.
"""

from typing import Dict, Any, List, Optional
import numpy as np


class SensorHealthState:
    def __init__(self, station_id: str):
        self.station_id = station_id
        self.total_observations = 0
        self.anomaly_count = 0
        self.flatline_count = 0
        self.drift_accumulated = {"temperature": 0.0, "pressure": 0.0, "humidity": 0.0}
        self.recent_anomalies: List[bool] = []
        self.window_size = 100

        # Current Health Metrics
        self.overall_health_score = 100.0  # 0 to 100%
        self.sensor_scores = {
            "temperature": 100.0,
            "pressure": 100.0,
            "humidity": 100.0
        }
        self.estimated_rul_days = 365.0  # Days until calibration/replacement required


class SensorHealthTracker:
    def __init__(self):
        self.station_states: Dict[str, SensorHealthState] = {}

    def _get_state(self, station_id: str) -> SensorHealthState:
        if station_id not in self.station_states:
            self.station_states[station_id] = SensorHealthState(station_id)
        return self.station_states[station_id]

    def update(
        self,
        station_id: str,
        is_anomaly: bool,
        fault_type: str,
        stat_res: Dict[str, Any],
        physics_res: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Updates sensor health statistics based on streaming observations.
        """
        state = self._get_state(station_id)
        state.total_observations += 1

        # Track rolling anomalies (excluding genuine weather events)
        is_hardware_fault = is_anomaly and fault_type not in ("NORMAL", "GENUINE_EXTREME_WEATHER")
        state.recent_anomalies.append(is_hardware_fault)
        if len(state.recent_anomalies) > state.window_size:
            state.recent_anomalies.pop(0)

        if is_hardware_fault:
            state.anomaly_count += 1
            if fault_type == "SENSOR_FLATLINE":
                state.flatline_count += 1

        # Calculate Rolling Fault Rate
        fault_rate = sum(state.recent_anomalies) / max(1, len(state.recent_anomalies))

        # CUSUM drift scores
        cusum_scores = stat_res.get("cusum_scores", {})
        drift_t = cusum_scores.get("temperature", 0.0)
        drift_p = cusum_scores.get("pressure", 0.0)
        drift_rh = cusum_scores.get("humidity", 0.0)

        # Health degradation penalties
        penalty_t = min(50.0, (fault_rate * 60.0) + (drift_t * 30.0))
        penalty_p = min(50.0, (fault_rate * 60.0) + (drift_p * 30.0))
        penalty_rh = min(50.0, (fault_rate * 60.0) + (drift_rh * 30.0))

        score_t = max(10.0, 100.0 - penalty_t)
        score_p = max(10.0, 100.0 - penalty_p)
        score_rh = max(10.0, 100.0 - penalty_rh)

        state.sensor_scores = {
            "temperature": round(score_t, 1),
            "pressure": round(score_p, 1),
            "humidity": round(score_rh, 1)
        }

        state.overall_health_score = round((score_t + score_p + score_rh) / 3.0, 1)

        # Estimate RUL (Remaining Useful Life in days)
        # 100% health -> 365 days; 50% health -> 45 days; <30% health -> Immediate maintenance
        if state.overall_health_score > 90:
            rul_days = 365
            maintenance_status = "OPTIMAL"
            advisory = "Sensor operating within optimal specifications."
        elif state.overall_health_score > 75:
            rul_days = 180
            maintenance_status = "GOOD"
            advisory = "Routine scheduled maintenance recommended within 6 months."
        elif state.overall_health_score > 50:
            rul_days = 45
            maintenance_status = "DEGRADED"
            advisory = "Calibration drift or intermittent glitches detected. Dispatch technician."
        else:
            rul_days = 7
            maintenance_status = "CRITICAL"
            advisory = "Severe transducer degradation or flatline detected. Immediate sensor replacement required."

        state.estimated_rul_days = rul_days

        return {
            "overall_health_score": state.overall_health_score,
            "sensor_scores": state.sensor_scores,
            "maintenance_status": maintenance_status,
            "advisory": advisory,
            "estimated_rul_days": rul_days,
            "fault_rate_pct": round(fault_rate * 100.0, 1),
            "total_observations": state.total_observations
        }


sensor_health_tracker = SensorHealthTracker()
