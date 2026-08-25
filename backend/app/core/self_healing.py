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

        # Cold-start fallback profile for a station with NO history yet. Only a
        # profile genuinely belonging to THIS station is acceptable: the previous
        # `list(config.stations.values())[0]` fallback silently handed an unknown
        # station the first configured station's baseline, so an unrecognised
        # sea-level station would have been imputed at a 785 hPa mountain
        # baseline -- a ~230 hPa fabricated error presented to downstream
        # forecasting as a healed value. An unknown station now gets None and the
        # imputer declines to invent a level for it (see below).
        #
        # Residual caveat: base_pressure_hpa is the station-LEVEL convention
        # (785 hPa for the mountain profile). In the real-data replay path the same
        # station streams NOAA sea-level pressure (~1013 hPa), so this baseline is
        # in the wrong convention there too -- but the fallback only fires at cold
        # start before ANY clean reading has established history. Once one valid
        # reading exists (always true after benchmark warmup), imputation uses the
        # recent stream value, which is already in the stream's own convention.
        st_prof = config.stations.get(station_id)

        # Temperature Imputation
        if temp is None or is_anomaly:
            if len(valid_imputed_temps) >= 3:
                # 3-step moving average projection
                imputed_temp = float(np.mean(valid_imputed_temps[-3:]))
            elif len(valid_imputed_temps) >= 1:
                imputed_temp = valid_imputed_temps[-1]
            else:
                imputed_temp = st_prof.base_temp_c if st_prof else temp
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
                imputed_pres = st_prof.base_pressure_hpa if st_prof else pres
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
                imputed_hum = st_prof.base_humidity_pct if st_prof else hum
            reasons.append("Reconstructed relative humidity trajectory")
        else:
            imputed_hum = hum

        # No history, no station profile, and no current reading -> nothing
        # defensible to impute. Report the gap honestly instead of fabricating a
        # value that downstream forecasting would treat as observed data.
        if imputed_temp is None or imputed_pres is None or imputed_hum is None:
            return {
                "temperature": imputed_temp,
                "pressure": imputed_pres,
                "humidity": imputed_hum,
                "is_imputed": False,
                "imputation_reason": (
                    "Insufficient history for this station to reconstruct a value; "
                    "gap reported rather than fabricated"
                ),
            }

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
