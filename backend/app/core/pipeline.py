"""
SkyGuard AI - Unified Streaming Pipeline Orchestrator
Connects Sensor Streams -> Physics Engine -> ML Ensemble -> XAI -> Self-Healing -> Health Tracker.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from backend.app.core.physics import physics_engine
from backend.app.models.statistical import statistical_engine
from backend.app.models.isolation_forest import multivariate_detector
from backend.app.models.autoencoder import temporal_autoencoder
from backend.app.models.ensemble import ensemble_meta_scorer
from backend.app.xai.root_cause import root_cause_classifier
from backend.app.xai.explainer import xai_explainer
from backend.app.core.self_healing import self_healing_imputer
from backend.app.maintenance.health_tracker import sensor_health_tracker
from backend.app.core.config import config


class SkyGuardPipeline:
    def __init__(self, buffer_size: int = 60):
        self.buffer_size = buffer_size
        self.station_buffers: Dict[str, List[Dict[str, Any]]] = {}

    def _get_buffer(self, station_id: str) -> List[Dict[str, Any]]:
        if station_id not in self.station_buffers:
            self.station_buffers[station_id] = []
        return self.station_buffers[station_id]

    def process_reading(self, raw_packet: Dict[str, Any], dt_seconds: float = 1.0) -> Dict[str, Any]:
        """
        Executes end-to-end processing of a single streaming observation.
        """
        station_id = raw_packet.get("station_id", "AWS_ALPHA_MOUNTAIN")
        buffer = self._get_buffer(station_id)

        temp = raw_packet.get("temperature")
        pres = raw_packet.get("pressure")
        hum = raw_packet.get("humidity")
        timestamp = raw_packet.get("timestamp", datetime.now(timezone.utc).isoformat())
        is_packet_loss = raw_packet.get("is_packet_loss", False)

        # Get previous valid readings from buffer for gradient calculations
        prev_temp, prev_pres, prev_hum = None, None, None
        if buffer:
            last_entry = buffer[-1]
            prev_raw = last_entry.get("raw", {})
            prev_temp = prev_raw.get("temperature")
            prev_pres = prev_raw.get("pressure")
            prev_hum = prev_raw.get("humidity")

        # 1. Physics Engine Check
        if not is_packet_loss and temp is not None and pres is not None and hum is not None:
            physics_res = physics_engine.verify_physical_consistency(
                temp_c=temp,
                pressure_hpa=pres,
                humidity_pct=hum,
                prev_temp_c=prev_temp,
                prev_pressure_hpa=prev_pres,
                prev_humidity_pct=prev_hum,
                dt_seconds=dt_seconds
            )
        else:
            physics_res = {
                "dew_point_c": None,
                "sat_vapor_pressure_hpa": None,
                "actual_vapor_pressure_hpa": None,
                "vpd_hpa": None,
                "dew_point_depression_c": None,
                "is_physics_violation": True,
                "physics_anomaly_score": 1.0,
                "violations": ["Missing telemetry packet"]
            }

        # 2. Streaming Statistical Filter Check
        # Pass None through untouched during packet loss: StatisticalEngine.process()
        # already skips updating its EWMA/CUSUM baselines for None sensors. Substituting
        # generic defaults here would otherwise corrupt station-specific baselines (e.g.
        # a ~785 hPa mountain station or ~34C desert station) with a fake 25C/1000hPa/60%
        # reading every time a packet drops.
        stat_res = statistical_engine.process(
            station_id=station_id,
            temp_c=temp,
            pressure_hpa=pres,
            humidity_pct=hum
        )

        # 3. Multivariate Isolation Forest Outlier Scoring
        d_temp = abs(temp - prev_temp) if (temp is not None and prev_temp is not None) else 0.0
        d_pres = abs(pres - prev_pres) if (pres is not None and prev_pres is not None) else 0.0
        d_hum = abs(hum - prev_hum) if (hum is not None and prev_hum is not None) else 0.0
        vpd = physics_res.get("vpd_hpa") or 0.0
        dp_dep = physics_res.get("dew_point_depression_c") or 0.0

        if not is_packet_loss and temp is not None:
            if_res = multivariate_detector.score_observation(
                temp_c=temp,
                pressure_hpa=pres,
                humidity_pct=hum,
                d_temp=d_temp,
                d_pres=d_pres,
                d_hum=d_hum,
                vpd=vpd,
                dew_point_depression=dp_dep
            )
        else:
            if_res = {
                "isolation_score": -0.5,
                "isolation_anomaly_prob": 0.95,
                "is_multivariate_outlier": True
            }

        # 4. Temporal Sequence Autoencoder Scoring
        sequence_window = [
            {"temperature": r.get("raw", {}).get("temperature", 25.0),
             "pressure": r.get("raw", {}).get("pressure", 1000.0),
             "humidity": r.get("raw", {}).get("humidity", 60.0)}
            for r in buffer[-15:]
        ]
        sequence_window.append({
            "temperature": temp if temp is not None else 25.0,
            "pressure": pres if pres is not None else 1000.0,
            "humidity": hum if hum is not None else 60.0
        })

        ae_res = temporal_autoencoder.score_sequence(sequence_window)

        # 5. Ensemble Meta-Scoring
        ensemble_res = ensemble_meta_scorer.evaluate(
            physics_res=physics_res,
            ae_res=ae_res,
            if_res=if_res,
            stat_res=stat_res
        )

        # 6. Root Cause Diagnostics & Weather vs Fault Discrimination
        raw_dict = {"temperature": temp, "pressure": pres, "humidity": hum}
        root_cause_res = root_cause_classifier.classify_fault(
            raw_reading=raw_dict,
            physics_res=physics_res,
            stat_res=stat_res,
            ae_res=ae_res,
            if_res=if_res,
            ensemble_res=ensemble_res,
            temporal_window=buffer
        )

        # 7. XAI Feature Attributions & Natural Language Explanation
        attributions = xai_explainer.compute_feature_attributions(
            raw_reading=raw_dict,
            physics_res=physics_res,
            stat_res=stat_res,
            ae_res=ae_res,
            if_res=if_res,
            ensemble_res=ensemble_res
        )

        explanation = xai_explainer.generate_natural_language_explanation(
            fault_type=root_cause_res["fault_type"],
            fault_category=root_cause_res["fault_category"],
            raw_reading=raw_dict,
            physics_res=physics_res,
            attributions=attributions,
            is_anomaly=ensemble_res["is_anomaly"]
        )

        # 8. Self-Healing Imputation
        imputed_res = self_healing_imputer.impute_reading(
            station_id=station_id,
            current_raw=raw_dict,
            temporal_history=buffer,
            is_anomaly=ensemble_res["is_anomaly"] and not root_cause_res["is_genuine_weather"],
            fault_type=root_cause_res["fault_type"]
        )

        # 9. Sensor Health Radar & Maintenance
        health_res = sensor_health_tracker.update(
            station_id=station_id,
            is_anomaly=ensemble_res["is_anomaly"],
            fault_type=root_cause_res["fault_type"],
            stat_res=stat_res,
            physics_res=physics_res
        )

        # 10. Assemble Final Telemetry Result
        processed_packet = {
            "station_id": station_id,
            "station_name": raw_packet.get("station_name", station_id),
            "station_type": raw_packet.get("station_type", "Standard"),
            "timestamp": timestamp,
            "simulated_hour": raw_packet.get("simulated_hour", 12.0),
            "raw": raw_dict,
            "clean_ground_truth": raw_packet.get("clean_ground_truth", raw_dict),
            "physics": physics_res,
            "statistical": stat_res,
            "isolation_forest": if_res,
            "autoencoder": ae_res,
            "ensemble": ensemble_res,
            "root_cause": root_cause_res,
            "xai": {
                "attributions": attributions,
                "explanation": explanation
            },
            "imputed": imputed_res,
            "sensor_health": health_res,
            "injected_anomalies": raw_packet.get("injected_anomalies", [])
        }

        # Update rolling buffer
        buffer.append(processed_packet)
        if len(buffer) > self.buffer_size:
            buffer.pop(0)

        return processed_packet


pipeline = SkyGuardPipeline()
