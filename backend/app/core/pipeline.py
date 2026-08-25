"""
SkyGuard AI - Unified Streaming Pipeline Orchestrator
Connects Sensor Streams -> Physics Engine -> ML Ensemble -> XAI -> Self-Healing -> Health Tracker.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from backend.app.core.physics import physics_engine
from backend.app.core.climatology import station_climatology
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
    def __init__(self, buffer_size: int = None):
        self.buffer_size = buffer_size if buffer_size is not None else config.sliding_window_size
        self.station_buffers: Dict[str, List[Dict[str, Any]]] = {}

    def _get_buffer(self, station_id: str) -> List[Dict[str, Any]]:
        if station_id not in self.station_buffers:
            self.station_buffers[station_id] = []
        return self.station_buffers[station_id]

    def _get_spatial_context(self, station_id: str, is_anomaly: bool) -> Dict[str, Any]:
        """
        Cross-station spatial consistency check. Directly implements the problem
        statement's own example scenario: "...while neighboring stations show normal
        conditions. The AI system should analyze temporal and spatial consistency,
        identify the reading as a probable sensor anomaly." Looks at the most recent
        processed reading from every OTHER station this pipeline instance is tracking.

        Requires multiple stations to be live in the SAME pipeline instance to produce
        a judgement -- true for the shared `pipeline` singleton used by the FastAPI
        backend and the Streamlit UI (backend/app/main.py, app.py), which track all
        configured stations concurrently. A benchmark harness that only ever feeds one
        station through an isolated SkyGuardPipeline() instance will see
        `other_stations_reporting=0` and this check stays neutral, by design --
        it cannot claim isolation or corroboration it has no data for.
        """
        other_station_ids = [
            sid for sid in self.station_buffers
            if sid != station_id and self.station_buffers[sid]
        ]
        other_reporting = len(other_station_ids)

        if other_reporting == 0:
            return {
                "other_stations_reporting": 0,
                "other_stations_anomalous": 0,
                "is_isolated_event": None,
                "is_corroborated_event": False
            }

        other_anomalous = sum(
            1 for sid in other_station_ids
            if self.station_buffers[sid][-1].get("ensemble", {}).get("is_anomaly", False)
        )

        return {
            "other_stations_reporting": other_reporting,
            "other_stations_anomalous": other_anomalous,
            "is_isolated_event": bool(is_anomaly and other_anomalous == 0),
            "is_corroborated_event": bool(is_anomaly and (other_anomalous / other_reporting) >= 0.34)
        }

    def process_reading(self, raw_packet: Dict[str, Any], dt_seconds: float = 1.0) -> Dict[str, Any]:
        """
        Executes end-to-end processing of a single streaming observation.
        """
        # A packet with no station_id gets its own isolated state under a neutral
        # sentinel -- never a real station's. Defaulting to a named demo station
        # (previously "AWS_ALPHA_MOUNTAIN") silently merged unattributed readings
        # into that station's sliding buffer and EWMA/CUSUM baselines, corrupting
        # the detection state of a real station with foreign data.
        station_id = raw_packet.get("station_id") or "UNSPECIFIED_STATION"
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
        #
        # Real-data replay only: feed the statistical engine a deseasonalized residual
        # (raw - this hour's real historical climatological mean) instead of the raw
        # value. CUSUM accumulates evidence from any sustained deviation from a slowly-
        # adapting mean, which is right for catching genuine drift but was measured to
        # misfire constantly on real hourly data -- real diurnal swings run ~10-11C at
        # these stations and look exactly like a sustained one-directional shift for
        # several consecutive hours every single day. Subtracting "what's normal for
        # this hour" removes that confound; real calibration drift, unlike ordinary
        # diurnal warming, does not follow the diurnal shape, so it stands out in the
        # residual instead of being swamped by it.
        stat_temp, stat_pres, stat_hum = temp, pres, hum
        is_deseasonalized = False
        # Deseasonalization is opt-in per packet via `climatology_key`, NOT gated on
        # a hardcoded data-source name. Any producer -- a real archive replay, a live
        # station feed, a future third-party source -- enables it by naming the
        # climatology its readings should be compared against; producers that set
        # nothing are simply never deseasonalized. This matters because a
        # climatology is only valid for the measurement convention it was built
        # from: the real archives report sea-level pressure (~1013 hPa) while the
        # synthetic generator reports station-level pressure (~785 hPa at altitude)
        # under the SAME station ids, so keying on station id alone would apply one
        # convention's baseline to the other's readings.
        climatology_key = raw_packet.get("climatology_key")
        if climatology_key and station_climatology.has_climatology(climatology_key):
            hour = raw_packet.get("simulated_hour", 12.0)
            if temp is not None:
                exp = station_climatology.expected(climatology_key, hour, "temperature")
                if exp is not None:
                    stat_temp = temp - exp
                    is_deseasonalized = True
            if pres is not None:
                exp = station_climatology.expected(climatology_key, hour, "pressure")
                if exp is not None:
                    stat_pres = pres - exp
                    is_deseasonalized = True
            if hum is not None:
                exp = station_climatology.expected(climatology_key, hour, "humidity")
                if exp is not None:
                    stat_hum = hum - exp
                    is_deseasonalized = True

        stat_res = statistical_engine.process(
            station_id=station_id,
            temp_c=stat_temp,
            pressure_hpa=stat_pres,
            humidity_pct=stat_hum,
            dt_seconds=dt_seconds,
            raw_temp_c=temp,
            raw_pressure_hpa=pres,
            raw_humidity_pct=hum,
            deseasonalized=is_deseasonalized
        )

        # 3. Multivariate Isolation Forest Outlier Scoring
        d_temp = abs(temp - prev_temp) if (temp is not None and prev_temp is not None) else 0.0
        d_pres = abs(pres - prev_pres) if (pres is not None and prev_pres is not None) else 0.0
        d_hum = abs(hum - prev_hum) if (hum is not None and prev_hum is not None) else 0.0
        vpd = physics_res.get("vpd_hpa") or 0.0
        dp_dep = physics_res.get("dew_point_depression_c") or 0.0

        if not is_packet_loss and temp is not None and pres is not None and hum is not None:
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
        #
        # Missing values are filled by last-observation-carried-forward from this
        # station's OWN recent history, never by a fixed "typical" constant. The
        # previous 25.0C / 1000.0 hPa / 60.0% fallbacks silently encoded a
        # temperate-lowland station as the assumed norm: substituting 1000 hPa at
        # a 785 hPa mountain station, or 25C at a station whose real baseline is
        # 34C, injects a fabricated ~200 hPa / ~9C step into the very trajectory
        # the autoencoder is judging for smoothness -- manufacturing an anomaly
        # out of a dropped packet, and doing so worst at exactly the stations
        # least like the hardcoded assumption. LOCF is station-agnostic: it
        # asserts only "we have no new information", which is what a dropped
        # packet actually means.
        sequence_window = []
        last_seen = {"temperature": None, "pressure": None, "humidity": None}
        for r in buffer[-15:]:
            r_raw = r.get("raw", {})
            entry = {}
            for key in ("temperature", "pressure", "humidity"):
                val = r_raw.get(key)
                if val is not None:
                    last_seen[key] = val
                entry[key] = val if val is not None else last_seen[key]
            sequence_window.append(entry)

        current = {"temperature": temp, "pressure": pres, "humidity": hum}
        for key, val in current.items():
            if val is not None:
                last_seen[key] = val
        sequence_window.append({k: (v if v is not None else last_seen[k]) for k, v in current.items()})

        ae_res = temporal_autoencoder.score_sequence(sequence_window)

        # 5. Ensemble Meta-Scoring
        ensemble_res = ensemble_meta_scorer.evaluate(
            physics_res=physics_res,
            ae_res=ae_res,
            if_res=if_res,
            stat_res=stat_res
        )

        # 6. Cross-Station Spatial Consistency Check
        spatial_res = self._get_spatial_context(station_id, ensemble_res["is_anomaly"])

        # 7. Root Cause Diagnostics & Weather vs Fault Discrimination
        raw_dict = {"temperature": temp, "pressure": pres, "humidity": hum}
        root_cause_res = root_cause_classifier.classify_fault(
            raw_reading=raw_dict,
            physics_res=physics_res,
            stat_res=stat_res,
            ae_res=ae_res,
            if_res=if_res,
            ensemble_res=ensemble_res,
            temporal_window=buffer,
            spatial_res=spatial_res
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
            "spatial": spatial_res,
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


def reset_detector_state():
    """
    Resets the module-level singleton detector state that constructing a fresh
    SkyGuardPipeline() does NOT clear: the statistical engine's per-station
    EWMA/CUSUM/flatline state, and the sensor health tracker's per-station history.
    Benchmarks that evaluate independent scenarios/categories must call this between
    runs so warmed-up state from one category cannot leak into the next and silently
    change its scores. (A pipeline's own sliding buffers are per-instance and already
    reset by constructing a new SkyGuardPipeline(); the isolation forest, autoencoder,
    ensemble, and root-cause classifier hold no per-run mutable state after training,
    so they need no reset.)
    """
    statistical_engine.reset()
    sensor_health_tracker.reset()


pipeline = SkyGuardPipeline()
