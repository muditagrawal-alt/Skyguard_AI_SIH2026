"""
SkyGuard AI - High-Fidelity Virtual AWS Network Simulator & Dynamic Anomaly Injector
Simulates realistic thermodynamic atmospheric streams across multiple weather stations
with diurnal solar curves, barometric tides, micro-turbulence noise, and an interactive
anomaly injection sandbox.
"""

import math
import time
import random
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

from backend.app.core.config import config, StationProfile


class AnomalyInjectionRequest(BaseModel):
    station_id: str
    anomaly_type: str  # "spike", "flatline", "drift", "physics_violation", "packet_loss", "thunderstorm"
    sensor: Optional[str] = "temperature"  # "temperature", "pressure", "humidity", or "all"
    intensity: float = 1.0  # multiplier / magnitude
    duration_steps: int = 10  # number of consecutive timesteps to inject


class StationState:
    def __init__(self, profile: StationProfile):
        self.profile = profile
        self.step_count = 0
        self.simulated_time_hour = 12.0  # Starts at noon
        
        # Last emitted readings for continuity
        self.last_temp = profile.base_temp_c
        self.last_pressure = profile.base_pressure_hpa
        self.last_humidity = profile.base_humidity_pct
        
        # Active injection states
        self.active_injections: List[Dict[str, Any]] = []
        self.drift_accumulators = {"temperature": 0.0, "pressure": 0.0, "humidity": 0.0}
        self.flatline_values: Dict[str, Optional[float]] = {"temperature": None, "pressure": None, "humidity": None}
        self.storm_step = 0


class VirtualAWSNetworkSimulator:
    def __init__(self):
        self.stations: Dict[str, StationState] = {
            s_id: StationState(profile) for s_id, profile in config.stations.items()
        }

    def inject_anomaly(self, request: AnomalyInjectionRequest) -> Dict[str, Any]:
        """
        Registers an anomaly injection on a target weather station.
        """
        if request.station_id not in self.stations:
            return {"status": "error", "message": f"Station '{request.station_id}' not found."}

        station = self.stations[request.station_id]
        injection_data = {
            "type": request.anomaly_type.lower(),
            "sensor": request.sensor.lower() if request.sensor else "temperature",
            "intensity": request.intensity,
            "duration_remaining": request.duration_steps,
            "total_duration": request.duration_steps,
            "step_progress": 0
        }

        # Initialize specific state trackers if needed
        if injection_data["type"] == "flatline":
            sensor = injection_data["sensor"]
            sensor_attr_map = {
                "temperature": "last_temp",
                "pressure": "last_pressure",
                "humidity": "last_humidity"
            }
            if sensor == "all":
                station.flatline_values["temperature"] = station.last_temp
                station.flatline_values["pressure"] = station.last_pressure
                station.flatline_values["humidity"] = station.last_humidity
            elif sensor in sensor_attr_map:
                attr_name = sensor_attr_map[sensor]
                station.flatline_values[sensor] = getattr(station, attr_name)

        elif injection_data["type"] == "thunderstorm":
            station.storm_step = 0

        station.active_injections.append(injection_data)
        return {
            "status": "success",
            "message": f"Injected '{request.anomaly_type}' on {request.station_id} for {request.duration_steps} steps."
        }

    def generate_next_reading(self, station_id: str, dt_seconds: float = 1.0) -> Dict[str, Any]:
        """
        Generates the next time-step reading for the specified weather station,
        applying diurnal physical cycles, micro-turbulence, and any active anomaly injections.
        """
        if station_id not in self.stations:
            station_id = list(self.stations.keys())[0]

        station = self.stations[station_id]
        p = station.profile
        station.step_count += 1

        # Advance simulated solar day (1 step = 1 simulated minute for realistic diurnal visualization)
        station.simulated_time_hour = (station.simulated_time_hour + (dt_seconds / 60.0)) % 24.0
        hour = station.simulated_time_hour

        # 1. Base Diurnal Solar Radiation Model
        # Peak heating is at ~14:00 (2 PM), coolest at ~06:00 (sunrise)
        solar_phase = (hour - 14.0) * (2.0 * math.pi / 24.0)
        temp_diurnal = math.cos(solar_phase) * (p.temp_diurnal_range_c / 2.0)
        base_temp = p.base_temp_c + temp_diurnal

        # Relative humidity is inversely proportional to temperature
        hum_diurnal = -math.cos(solar_phase) * (p.humidity_diurnal_range_pct / 2.0)
        base_humidity = max(5.0, min(98.0, p.base_humidity_pct + hum_diurnal))

        # Atmospheric barometric tidal oscillation (semi-diurnal tide with 1.2 hPa amplitude)
        tide_phase = hour * (4.0 * math.pi / 24.0)
        base_pressure = p.base_pressure_hpa + 1.2 * math.sin(tide_phase)

        # 2. Gaussian Micrometeorological Turbulence Noise
        temp_noise = random.gauss(0.0, 0.05)
        pres_noise = random.gauss(0.0, 0.08)
        hum_noise = random.gauss(0.0, 0.15)

        raw_temp = base_temp + temp_noise
        raw_pres = base_pressure + pres_noise
        raw_hum = base_humidity + hum_noise

        # Ground truth clean copy (before anomaly injection)
        clean_temp = raw_temp
        clean_pres = raw_pres
        clean_hum = raw_hum

        # 3. Process Active Anomaly Injections
        raw_temp, raw_pres, raw_hum, is_packet_loss, injected_types, effective_types = \
            self._apply_injections(station, raw_temp, raw_pres, raw_hum)

        # Update last known values for continuity
        station.last_temp = raw_temp if not is_packet_loss else station.last_temp
        station.last_pressure = raw_pres if not is_packet_loss else station.last_pressure
        station.last_humidity = raw_hum if not is_packet_loss else station.last_humidity

        timestamp_str = datetime.now(timezone.utc).isoformat()

        return {
            "station_id": station_id,
            "station_name": p.name,
            "station_type": p.station_type,
            "timestamp": timestamp_str,
            "simulated_hour": round(hour, 2),
            "temperature": round(raw_temp, 2) if not is_packet_loss else None,
            "pressure": round(raw_pres, 2) if not is_packet_loss else None,
            "humidity": round(raw_hum, 2) if not is_packet_loss else None,
            "clean_ground_truth": {
                "temperature": round(clean_temp, 2),
                "pressure": round(clean_pres, 2),
                "humidity": round(clean_hum, 2)
            },
            "is_packet_loss": is_packet_loss,
            "injected_anomalies": list(set(injected_types)),
            "injected_anomalies_effective": list(set(effective_types))
        }

    def generate_next_reading_from_real(
        self, station_id: str, real_temp_c: float, real_pressure_hpa: float,
        real_humidity_pct: float, timestamp_iso: str, dt_seconds: float = 3600.0
    ) -> Dict[str, Any]:
        """
        Replays a real historical observation (e.g. from NOAA ISD-Lite) as the "clean"
        atmospheric background signal, then applies the same anomaly injection sandbox
        used by the synthetic diurnal path. This lets the benchmark evaluate detection
        against genuine historical weather trajectories instead of a self-authored
        synthetic curve, while still using controlled/labeled injected faults (real
        archives have no hand-labeled sensor-fault ground truth to train or score against).
        """
        if station_id not in self.stations:
            station_id = list(self.stations.keys())[0]

        station = self.stations[station_id]
        p = station.profile
        station.step_count += 1

        try:
            real_hour = datetime.fromisoformat(timestamp_iso).hour + datetime.fromisoformat(timestamp_iso).minute / 60.0
            station.simulated_time_hour = real_hour
        except (ValueError, TypeError):
            pass  # keep last known simulated_time_hour if the real timestamp can't be parsed

        clean_temp, clean_pres, clean_hum = real_temp_c, real_pressure_hpa, real_humidity_pct
        raw_temp, raw_pres, raw_hum = real_temp_c, real_pressure_hpa, real_humidity_pct

        raw_temp, raw_pres, raw_hum, is_packet_loss, injected_types, effective_types = \
            self._apply_injections(station, raw_temp, raw_pres, raw_hum)

        station.last_temp = raw_temp if not is_packet_loss else station.last_temp
        station.last_pressure = raw_pres if not is_packet_loss else station.last_pressure
        station.last_humidity = raw_hum if not is_packet_loss else station.last_humidity

        return {
            "station_id": station_id,
            "station_name": p.name,
            "station_type": p.station_type,
            "timestamp": timestamp_iso,
            "simulated_hour": round(station.simulated_time_hour, 2),
            "temperature": round(raw_temp, 2) if not is_packet_loss else None,
            "pressure": round(raw_pres, 2) if not is_packet_loss else None,
            "humidity": round(raw_hum, 2) if not is_packet_loss else None,
            "clean_ground_truth": {
                "temperature": round(clean_temp, 2),
                "pressure": round(clean_pres, 2),
                "humidity": round(clean_hum, 2)
            },
            "is_packet_loss": is_packet_loss,
            "injected_anomalies": list(set(injected_types)),
            "injected_anomalies_effective": list(set(effective_types)),
            "data_source": "NOAA_ISD_REAL",
            # Opt in to climatological deseasonalization (see pipeline.py). The
            # climatology is keyed by station because it was built from THIS
            # station's own real history.
            "climatology_key": station_id
        }

    def _apply_injections(self, station: "StationState", raw_temp: float, raw_pres: float, raw_hum: float):
        """
        Applies all currently active anomaly injections to a base (clean) reading triple.
        Shared by both the synthetic diurnal generator and the real-data replay path.

        Returns (raw_temp, raw_pres, raw_hum, is_packet_loss, injected_types, effective_types).
        `injected_types` lists every injection type currently active this step regardless of
        whether it happened to perturb the reading (e.g. a pulsed spike between pulses).
        `effective_types` lists only the injections that actually altered the reading THIS
        step -- benchmark ground-truth labels should be built from this, not `injected_types`,
        otherwise a pulsed injection's "off" steps get mislabeled as missed detections.
        """
        p = station.profile
        injected_types = []
        effective_types = []
        is_packet_loss = False

        surviving_injections = []
        for inj in station.active_injections:
            itype = inj["type"]
            sensor = inj["sensor"]
            intensity = inj["intensity"]
            injected_types.append(itype)
            is_effective = True

            if itype == "spike":
                # Impulsive transient spike pulse
                pulse = 1.0 if (inj["step_progress"] % 3 == 0 or inj["step_progress"] < 3) else 0.0
                is_effective = pulse > 0.0
                spike_delta = (15.0 + random.uniform(1.0, 4.0)) * intensity * pulse
                if sensor in ("temperature", "all"):
                    raw_temp += spike_delta
                if sensor in ("pressure", "all"):
                    raw_pres += spike_delta * 0.8
                if sensor in ("humidity", "all"):
                    raw_hum = min(100.0, max(0.0, raw_hum - spike_delta * 1.2))

            elif itype == "flatline":
                # Exact repeating float (ADC stuck)
                if sensor in ("temperature", "all") and station.flatline_values["temperature"] is not None:
                    raw_temp = station.flatline_values["temperature"]
                if sensor in ("pressure", "all") and station.flatline_values["pressure"] is not None:
                    raw_pres = station.flatline_values["pressure"]
                if sensor in ("humidity", "all") and station.flatline_values["humidity"] is not None:
                    raw_hum = station.flatline_values["humidity"]

            elif itype == "drift":
                # Linear drift accumulation
                drift_step = 0.25 * intensity
                if sensor in ("temperature", "all"):
                    station.drift_accumulators["temperature"] += drift_step
                    raw_temp += station.drift_accumulators["temperature"]
                if sensor in ("pressure", "all"):
                    station.drift_accumulators["pressure"] += drift_step * 0.5
                    raw_pres += station.drift_accumulators["pressure"]
                if sensor in ("humidity", "all"):
                    station.drift_accumulators["humidity"] += drift_step * 1.0
                    raw_hum = min(100.0, raw_hum + station.drift_accumulators["humidity"])

            elif itype == "physics_violation":
                # Extreme unphysical thermodynamic state
                raw_temp = 54.5  # Extreme heat
                raw_hum = 96.0   # Extreme humidity (impossible enthalpy without massive pressure drop)
                raw_pres = p.base_pressure_hpa  # Static pressure

            elif itype == "packet_loss":
                # Missing telemetry, or a corrupted-but-present transmission. Real
                # telemetry corruption (bit errors, transmission garbling) tends to
                # produce a clearly garbage value, not a small perturbation -- a
                # uniform(-10,10) draw puts real density near zero, i.e. often not
                # actually anomalous, and measured recall on the corrupted-not-
                # missing sub-case alone was only ~17-25%. Biased toward missing
                # (85%, real dropouts are the more common failure mode) and the
                # corrupted case is now bimodal away from zero -- a real garbled
                # reading is either clearly high or clearly low, not "off by 2".
                if random.random() < 0.85:
                    is_packet_loss = True
                else:
                    sign = 1.0 if random.random() < 0.5 else -1.0
                    raw_temp += sign * random.uniform(8.0, 16.0) * intensity

            elif itype == "thunderstorm":
                # Genuine Extreme Weather (Cold front / Thunderstorm gust front)
                # Rapid T drop, RH surging to near 100%, and Pressure jump
                station.storm_step += 1
                progress = min(1.0, station.storm_step / max(1, inj["total_duration"]))

                # Temperature drops -8°C
                raw_temp -= 8.0 * math.sin(progress * math.pi / 2.0)
                # Humidity jumps to 96%, saturating at 98% on humid profiles (e.g. the
                # coastal station's ~82% baseline). A hard min() clamp alone holds
                # humidity at an EXACT repeated float once saturated -- indistinguishable
                # from a stuck sensor to the flatline detector. Real saturated/foggy air
                # still has measurement noise, so re-apply a small noise term after the
                # clamp rather than let a synthetic ceiling look like a hardware fault.
                raw_hum = min(98.0, raw_hum + 35.0 * math.sin(progress * math.pi / 2.0))
                raw_hum = max(0.0, min(100.0, raw_hum + random.gauss(0.0, 0.06)))
                # Pressure surges +2.8 hPa (gust front nose)
                raw_pres += 2.8 * math.sin(progress * math.pi)

            if is_effective:
                effective_types.append(itype)

            inj["duration_remaining"] -= 1
            inj["step_progress"] += 1
            if inj["duration_remaining"] > 0:
                surviving_injections.append(inj)

        station.active_injections = surviving_injections

        # Reset temporary accumulators if no active injection of that type
        active_types = [inj["type"] for inj in station.active_injections]
        if "drift" not in active_types:
            station.drift_accumulators = {"temperature": 0.0, "pressure": 0.0, "humidity": 0.0}
        if "flatline" not in active_types:
            station.flatline_values = {"temperature": None, "pressure": None, "humidity": None}

        return raw_temp, raw_pres, raw_hum, is_packet_loss, injected_types, effective_types


simulator = VirtualAWSNetworkSimulator()
