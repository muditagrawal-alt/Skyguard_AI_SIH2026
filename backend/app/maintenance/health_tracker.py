"""
SkyGuard AI - Sensor Health & Maintenance Advisory Engine
Tracks rolling hardware-fault rate and CUSUM calibration-drift scores, derives a
Sensor Health Index (0-100%), and maps it to a coarse maintenance advisory band.

This is a heuristic, rule-based health tracker -- NOT a trained prognostic model.
The reported "remaining useful life (RUL)" is a fixed lookup keyed on the current
health band: a maintenance-planning aid describing PRESENT condition, not a failure
date forecast extrapolated from a degradation model. The field name is kept
(`estimated_rul_days`) for API/UI compatibility; interpret it as an advisory band.
"""

from typing import Dict, Any, List, Optional
import numpy as np


class SensorHealthState:
    def __init__(self, station_id: str):
        self.station_id = station_id
        self.total_observations = 0
        self.anomaly_count = 0
        self.flatline_count = 0
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

        # Map the current health band to a coarse maintenance advisory and a
        # representative days-until-service figure. This is a fixed lookup on
        # PRESENT health, not a forecast: it means "a sensor in this condition band
        # is typically serviced within N days", not "this sensor will fail on day N".
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
            "flatline_count": state.flatline_count,
            "total_observations": state.total_observations
        }


    def reset(self):
        """
        Clears all per-station health state. Like the other detectors this is a
        module-level singleton, so a benchmark that builds a fresh SkyGuardPipeline()
        per category would otherwise carry fault-rate/flatline history across
        supposedly independent categories. Call between independent runs.
        """
        self.station_states.clear()


sensor_health_tracker = SensorHealthTracker()
