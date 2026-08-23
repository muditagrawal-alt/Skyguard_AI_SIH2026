"""
SkyGuard AI - Per-Station Hourly Climatology
Computes an hour-of-day expected value (climatological mean) per station and sensor
from real NOAA ISD-Lite history, so the statistical drift engine can be fed a
deseasonalized residual instead of the raw reading.

Why this exists: CUSUM (backend/app/models/statistical.py) accumulates evidence from
any SUSTAINED deviation from a slowly-adapting mean -- correct for catching a sensor
whose calibration has genuinely shifted, but real diurnal temperature swings are
large (measured: ~10-11C from midnight to mid-morning at the Delhi and desert
stations) and LOOK exactly like a sustained one-directional shift for several
consecutive real hours every single day. Feeding CUSUM the residual after
subtracting "what hour is it, and what does this station's real history say is
normal for that hour" removes the dominant confound, so a genuine multi-day
calibration drift -- which does NOT follow the diurnal shape, unlike ordinary
warming/cooling -- stands out instead of being swamped by it.

Only used for the real-data replay path (data_source == "NOAA_ISD_REAL" in
pipeline.py), gated explicitly rather than auto-detected, so the synthetic
generator's already-tuned behavior is untouched.
"""

import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

REAL_DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "real_stations" / "processed"
SENSORS = ("temperature_c", "pressure_hpa", "humidity_pct")


class StationClimatology:
    def __init__(self):
        # station_id -> sensor -> hour(0-23) -> mean
        self._hourly_mean: Dict[str, Dict[str, Dict[int, float]]] = {}
        self._load()

    def _load(self):
        if not REAL_DATA_DIR.is_dir():
            return
        for csv_path in sorted(REAL_DATA_DIR.glob("*.csv")):
            station_id = csv_path.stem
            sums = {s: defaultdict(float) for s in SENSORS}
            counts = {s: defaultdict(int) for s in SENSORS}

            with open(csv_path, newline="") as f:
                for row in csv.DictReader(f):
                    try:
                        hour = datetime.fromisoformat(row["timestamp"]).hour
                    except (ValueError, KeyError):
                        continue
                    for sensor in SENSORS:
                        val = row.get(sensor)
                        if val is None or val == "":
                            continue
                        sums[sensor][hour] += float(val)
                        counts[sensor][hour] += 1

            self._hourly_mean[station_id] = {
                sensor: {
                    hour: sums[sensor][hour] / counts[sensor][hour]
                    for hour in counts[sensor] if counts[sensor][hour] > 0
                }
                for sensor in SENSORS
            }

    def has_climatology(self, station_id: str) -> bool:
        return station_id in self._hourly_mean and len(self._hourly_mean[station_id]["temperature_c"]) > 0

    def expected(self, station_id: str, hour: float, sensor: str) -> Optional[float]:
        """
        sensor: "temperature", "pressure", or "humidity" (pipeline.py's naming;
        translated to this module's *_c/_hpa/_pct CSV column names internally).
        `hour` may be fractional (e.g. 13.5); linearly interpolated between the
        two nearest integer-hour buckets so the residual doesn't step-jump at
        each hour boundary.
        """
        col = {"temperature": "temperature_c", "pressure": "pressure_hpa", "humidity": "humidity_pct"}.get(sensor)
        if col is None or station_id not in self._hourly_mean:
            return None
        table = self._hourly_mean[station_id][col]
        if not table:
            return None

        h0 = int(hour) % 24
        h1 = (h0 + 1) % 24
        frac = hour - int(hour)
        v0 = table.get(h0)
        v1 = table.get(h1)
        if v0 is None and v1 is None:
            return None
        if v0 is None:
            return v1
        if v1 is None:
            return v0
        return v0 + (v1 - v0) * frac


station_climatology = StationClimatology()
