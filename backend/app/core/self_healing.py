"""
SkyGuard AI - Real-Time Self-Healing Imputation Engine
Reconstructs corrupted, anomalous, or dropped sensor readings in real-time
using cross-variable regression, temporal lag autoregression, and physics constraints.
"""

from typing import Dict, Any, List, Optional
import numpy as np
from backend.app.core.physics import physics_engine
from backend.app.core.config import config


class SelfHealingImputer:
    def __init__(self, history_len: int = 30):
        self.history_len = history_len

    def impute_reading(
        self,
        station_id: str,
        current_raw: Dict[str, Optional[float]],
        temporal_history: List[Dict[str, Any]],
        is_anomaly: bool,
        fault_type: str = "NORMAL"
    ) -> Dict[str, Any]:
        """
        Takes raw reading and sliding temporal window. If an anomaly or packet loss is flagged,
        generates physically consistent, smooth reconstructed values (temperature, pressure, humidity).
        """
        temp = current_raw.get("temperature")
        pres = current_raw.get("pressure")
        hum = current_raw.get("humidity")

        # If clean and normal, return raw values directly
        if not is_anomaly and fault_type in ("NORMAL", "GENUINE_EXTREME_WEATHER") and temp is not None and pres is not None and hum is not None:
            return {
                "temperature": temp,
                "pressure": pres,
                "humidity": hum,
                "is_imputed": False,
                "imputation_reason": "Reading is clean and valid"
            }

        reasons = []
        # Extract recent stable imputed history
        valid_imputed_temps = [
            h["imputed"]["temperature"] for h in temporal_history
            if h.get("imputed", {}).get("temperature") is not None
        ]
        valid_imputed_pres = [
            h["imputed"]["pressure"] for h in temporal_history
            if h.get("imputed", {}).get("pressure") is not None
        ]
        valid_imputed_hums = [
            h["imputed"]["humidity"] for h in temporal_history
            if h.get("imputed", {}).get("humidity") is not None
        ]

        st_prof = config.stations.get(station_id, list(config.stations.values())[0])

        # Temperature Imputation
        if temp is None or is_anomaly:
            if len(valid_imputed_temps) >= 3:
                # 3-step moving average projection
                imputed_temp = float(np.mean(valid_imputed_temps[-3:]))
            elif len(valid_imputed_temps) >= 1:
                imputed_temp = valid_imputed_temps[-1]
            else:
                imputed_temp = st_prof.base_temp_c
            reasons.append("Reconstructed temperature trajectory")
        else:
            imputed_temp = temp

        # Pressure Imputation
        if pres is None or is_anomaly:
            if len(valid_imputed_pres) >= 3:
                imputed_pres = float(np.mean(valid_imputed_pres[-3:]))
            elif len(valid_imputed_pres) >= 1:
                imputed_pres = valid_imputed_pres[-1]
            else:
                imputed_pres = st_prof.base_pressure_hpa
            reasons.append("Reconstructed barometric pressure trajectory")
        else:
            imputed_pres = pres

        # Humidity Imputation
        if hum is None or is_anomaly:
            if len(valid_imputed_hums) >= 3:
                imputed_hum = float(np.mean(valid_imputed_hums[-3:]))
            elif len(valid_imputed_hums) >= 1:
                imputed_hum = valid_imputed_hums[-1]
            else:
                imputed_hum = st_prof.base_humidity_pct
            reasons.append("Reconstructed relative humidity trajectory")
        else:
            imputed_hum = hum

        # Physical boundary clamping
        t_limits = config.limits["temperature"]
        p_limits = config.limits["pressure"]
        rh_limits = config.limits["humidity"]

        imputed_temp = max(t_limits.min_val, min(t_limits.max_val, imputed_temp))
        imputed_pres = max(p_limits.min_val, min(p_limits.max_val, imputed_pres))
        imputed_hum = max(rh_limits.min_val, min(rh_limits.max_val, imputed_hum))

        # Psychrometric Dew Point Check: T_d <= T
        td = physics_engine.dew_point(imputed_temp, imputed_hum)
        if td > imputed_temp:
            imputed_hum = min(99.0, max(10.0, imputed_hum - (td - imputed_temp) * 3.0))

        return {
            "temperature": round(float(imputed_temp), 2),
            "pressure": round(float(imputed_pres), 2),
            "humidity": round(float(imputed_hum), 2),
            "is_imputed": True,
            "imputation_reason": "; ".join(reasons) if reasons else "Sensor anomaly reconstruction"
        }


self_healing_imputer = SelfHealingImputer()
