"""
SkyGuard AI - Explainable AI (XAI) Engine & Natural Language Reasoner
Computes a fast additive feature-attribution heuristic (NOT SHAP -- see
benchmark/run_shap_analysis.py for genuine, offline-computed SHAP values against the
Isolation Forest) and generates human-readable diagnostic explanations. This module
trades explanation fidelity for speed: it must run inside the <10ms per-packet
real-time budget, which a proper SHAP/LIME explainer cannot.
"""

from typing import Dict, Any, List, Optional
import numpy as np


class XAIExplainer:
    def __init__(self):
        self.feature_names = [
            "temperature", "pressure", "humidity",
            "delta_temp", "delta_pres", "delta_hum",
            "vpd", "dew_point_depression"
        ]

    def compute_feature_attributions(
        self,
        raw_reading: Dict[str, Optional[float]],
        physics_res: Dict[str, Any],
        stat_res: Dict[str, Any],
        ae_res: Dict[str, Any],
        if_res: Dict[str, Any],
        ensemble_res: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Computes normalized Shapley / additive feature attribution weights (summing to 1.0)
        showing which meteorological variables and gradients drove the anomaly score.
        """
        temp = raw_reading.get("temperature", 25.0) or 25.0
        pres = raw_reading.get("pressure", 1000.0) or 1000.0
        hum = raw_reading.get("humidity", 60.0) or 60.0

        z_scores = stat_res.get("z_scores", {})
        z_t = abs(z_scores.get("temperature", 0.0))
        z_p = abs(z_scores.get("pressure", 0.0))
        z_rh = abs(z_scores.get("humidity", 0.0))

        ae_t = ae_res.get("recent_temp_err", 0.0)
        ae_p = ae_res.get("recent_pres_err", 0.0)
        ae_h = ae_res.get("recent_hum_err", 0.0)

        # Physics weighting
        violations = physics_res.get("violations", [])
        phys_t = 1.0 if any("Temperature" in v or "ΔT" in v for v in violations) else 0.0
        phys_p = 1.0 if any("Pressure" in v or "ΔP" in v for v in violations) else 0.0
        phys_rh = 1.0 if any("Humidity" in v or "ΔRH" in v or "Dew point" in v for v in violations) else 0.0

        # Raw attribution vector
        w_t = (z_t * 0.4) + (ae_t * 0.3) + (phys_t * 0.8) + 0.05
        w_p = (z_p * 0.4) + (ae_p * 0.3) + (phys_p * 0.8) + 0.05
        w_rh = (z_rh * 0.4) + (ae_h * 0.3) + (phys_rh * 0.8) + 0.05
        w_dt = (z_t * 0.3) + (phys_t * 0.5) + 0.02
        w_dp = (z_p * 0.3) + (phys_p * 0.5) + 0.02
        w_drh = (z_rh * 0.3) + (phys_rh * 0.5) + 0.02
        w_vpd = max(0.01, (physics_res.get("vpd_hpa") or 0.0) / 40.0)
        w_dp_dep = max(0.01, abs(physics_res.get("dew_point_depression_c") or 0.0) / 15.0)

        raw_attributions = {
            "temperature": w_t,
            "pressure": w_p,
            "humidity": w_rh,
            "delta_temp": w_dt,
            "delta_pres": w_dp,
            "delta_hum": w_drh,
            "vpd": w_vpd,
            "dew_point_depression": w_dp_dep
        }

        total_weight = sum(raw_attributions.values())
        normalized_attributions = {
            k: round(v / total_weight, 4) for k, v in raw_attributions.items()
        }

        return normalized_attributions

    def generate_natural_language_explanation(
        self,
        fault_type: str,
        fault_category: str,
        raw_reading: Dict[str, Optional[float]],
        physics_res: Dict[str, Any],
        attributions: Dict[str, float],
        is_anomaly: bool
    ) -> str:
        """
        Generates a human-readable diagnostic report for operators.
        """
        if not is_anomaly or fault_type == "NORMAL":
            return "All atmospheric parameters (Temperature, Pressure, Relative Humidity) conform to physical limits and expected diurnal trajectories."

        temp = raw_reading.get("temperature")
        pres = raw_reading.get("pressure")
        hum = raw_reading.get("humidity")

        # Top 2 contributing features
        sorted_attribs = sorted(attributions.items(), key=lambda x: x[1], reverse=True)
        top_feature, top_val = sorted_attribs[0]
        top_pct = int(top_val * 100)

        violations = physics_res.get("violations", [])
        phys_text = f" Physical rule flagged: '{violations[0]}'." if violations else ""

        if fault_type == "GENUINE_EXTREME_WEATHER":
            return (
                f"✅ GENUINE SEVERE WEATHER EVENT DETECTED ({fault_category}). "
                f"Rapid synchronized shifts across Temperature ({temp}°C), Pressure ({pres} hPa), and Humidity ({hum}%) "
                f"follow physical convective/frontal atmospheric mechanics without violating thermodynamic equilibrium."
            )
        elif fault_type == "SENSOR_SPIKE":
            return (
                f"⚠️ SENSOR SPIKE ANOMALY DETECTED ({fault_category}). "
                f"Primary driver: '{top_feature.replace('_', ' ').title()}' contributing {top_pct}% to the anomaly score.{phys_text} "
                f"Lack of thermodynamic coupling in neighboring sensors confirms transducer transient rather than weather."
            )
        elif fault_type == "SENSOR_FLATLINE":
            return (
                f"❄️ SENSOR FLATLINE / FREEZE DETECTED ({fault_category}). "
                f"Constant invariant float values detected across consecutive sampling steps. Suspected ADC buffer lockup."
            )
        elif fault_type == "CALIBRATION_DRIFT":
            return (
                f"📈 CALIBRATION DRIFT DETECTED ({fault_category}). "
                f"CUSUM statistical tracking indicates progressive systematic bias accumulation in '{top_feature.title()}'. Calibration needed."
            )
        elif fault_type == "PHYSICAL_INCONSISTENCY":
            return (
                f"❌ THERMODYNAMIC INCONSISTENCY ({fault_category}). "
                f"Reading combinations violate atmospheric psychrometric equations.{phys_text} Sensor transducer recalibration required."
            )
        elif fault_type == "COMMUNICATION_DROPOUT":
            return (
                f"📶 TELEMETRY PACKET LOSS ({fault_category}). "
                f"Missing or corrupted transmission frames received over telemetry link. Self-healing imputer activated."
            )

        return f"Anomaly flagged in {top_feature} ({top_pct}% contribution). Fault category: {fault_category}."


xai_explainer = XAIExplainer()
