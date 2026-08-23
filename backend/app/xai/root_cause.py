"""
SkyGuard AI - Multi-Class Root Cause Fault Diagnostic Classifier
Distinguishes between genuine severe weather events and various hardware/sensor/telemetry faults.
"""

from typing import Dict, Any, List, Optional


class RootCauseClassifier:
    def classify_fault(
        self,
        raw_reading: Dict[str, Optional[float]],
        physics_res: Dict[str, Any],
        stat_res: Dict[str, Any],
        ae_res: Dict[str, Any],
        if_res: Dict[str, Any],
        ensemble_res: Dict[str, Any],
        temporal_window: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Classifies anomaly into a specific root-cause category:
        1. NORMAL
        2. GENUINE_EXTREME_WEATHER
        3. SENSOR_SPIKE
        4. SENSOR_FLATLINE
        5. CALIBRATION_DRIFT
        6. PHYSICAL_INCONSISTENCY
        7. COMMUNICATION_DROPOUT
        """
        is_anomaly = ensemble_res.get("is_anomaly", False)
        temp = raw_reading.get("temperature")
        pres = raw_reading.get("pressure")
        hum = raw_reading.get("humidity")

        # 1. Check for Missing / Packet Loss
        if temp is None or pres is None or hum is None:
            return {
                "fault_type": "COMMUNICATION_DROPOUT",
                "fault_category": "Telemetry & Communication",
                "confidence": 0.99,
                "is_genuine_weather": False
            }

        # 2. Check for Sensor Flatlining (Stuck ADC)
        if stat_res.get("is_flatline", False):
            return {
                "fault_type": "SENSOR_FLATLINE",
                "fault_category": "Sensor Transducer / ADC Lockup",
                "confidence": 0.98,
                "is_genuine_weather": False
            }

        if len(temporal_window) >= 5:
            last_5_temps = [r.get("raw", {}).get("temperature") for r in temporal_window[-5:]]
            last_5_press = [r.get("raw", {}).get("pressure") for r in temporal_window[-5:]]
            last_5_hums = [r.get("raw", {}).get("humidity") for r in temporal_window[-5:]]

            if all(t == temp and t is not None for t in last_5_temps) and len(set(last_5_temps)) == 1:
                return {
                    "fault_type": "SENSOR_FLATLINE",
                    "fault_category": "Sensor Transducer / ADC Lockup",
                    "confidence": 0.96,
                    "is_genuine_weather": False
                }
            if all(p == pres and p is not None for p in last_5_press) and len(set(last_5_press)) == 1:
                return {
                    "fault_type": "SENSOR_FLATLINE",
                    "fault_category": "Barometer ADC Lockup",
                    "confidence": 0.96,
                    "is_genuine_weather": False
                }
            if all(h == hum and h is not None for h in last_5_hums) and len(set(last_5_hums)) == 1:
                return {
                    "fault_type": "SENSOR_FLATLINE",
                    "fault_category": "Hygrometer ADC Lockup",
                    "confidence": 0.96,
                    "is_genuine_weather": False
                }

        # 3. Check for Genuine Extreme Weather vs Sensor Spike / Fault
        if is_anomaly:
            violations = physics_res.get("violations", [])
            hard_violations = [v for v in violations if "Rapid" not in v]

            # 4. Check for Hard Physical Inconsistency
            if len(hard_violations) > 0:
                return {
                    "fault_type": "PHYSICAL_INCONSISTENCY",
                    "fault_category": "Thermodynamic Law Violation",
                    "confidence": 0.95,
                    "is_genuine_weather": False
                }

            # Inspect recent trajectory for convective meteorological event
            recent_drops = False
            if len(temporal_window) >= 1:
                recent_temps = [r.get("raw", {}).get("temperature") for r in temporal_window[-10:] if r.get("raw", {}).get("temperature") is not None]
                recent_hums = [r.get("raw", {}).get("humidity") for r in temporal_window[-10:] if r.get("raw", {}).get("humidity") is not None]
                if len(recent_temps) >= 1:
                    if temp is not None and recent_temps[0] is not None and (temp - recent_temps[0]) < -0.5:
                        recent_drops = True
                if len(recent_hums) >= 1:
                    if hum is not None and hum > 75.0:
                        recent_drops = True

            # Convective Thunderstorm / Cold Front signature:
            # - No thermodynamic bounds broken (T >= Td)
            # - Saturated / high humidity (> 75%) with recent cooling or rain downdraft
            is_convective_storm = len(hard_violations) == 0 and (recent_drops or (hum is not None and hum > 78.0))

            if is_convective_storm:
                return {
                    "fault_type": "GENUINE_EXTREME_WEATHER",
                    "fault_category": "Atmospheric Convective Storm / Cold Front",
                    "confidence": 0.95,
                    "is_genuine_weather": True
                }

            # 5. Check for Calibration Drift
            if len(stat_res.get("drift_flags", [])) > 0:
                return {
                    "fault_type": "CALIBRATION_DRIFT",
                    "fault_category": "Sensor Aging & Calibration Drift",
                    "confidence": 0.88,
                    "is_genuine_weather": False
                }

            # 6. Default to Sensor Spike / Electrical Glitch
            return {
                "fault_type": "SENSOR_SPIKE",
                "fault_category": "Electrical Transient / Sensor Glitch",
                "confidence": 0.90,
                "is_genuine_weather": False
            }

        # If not anomalous
        return {
            "fault_type": "NORMAL",
            "fault_category": "Normal Atmospheric State",
            "confidence": 0.99,
            "is_genuine_weather": True
        }


root_cause_classifier = RootCauseClassifier()
