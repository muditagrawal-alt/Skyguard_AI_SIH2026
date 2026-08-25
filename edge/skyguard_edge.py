"""
SkyGuard AI - MicroPython Edge Guard Module
Designed for low-power microcontrollers (ESP32, Raspberry Pi Pico, STM32).
Zero external dependencies, O(1) RAM allocation, sub-millisecond execution.
"""

import math


class MicroEdgeGuard:
    def __init__(self):
        self.prev_temp = None
        self.prev_pres = None
        self.prev_hum = None
        self.flatline_count = 0
        self.last_temp = None
        
        # Welford stats
        self.count = 0
        self.mean_t = 25.0
        self.m2_t = 0.0

    def compute_dew_point(self, temp_c: float, humidity_pct: float) -> float:
        if humidity_pct <= 0.0:
            return -99.0
        rh = min(1.0, max(0.01, humidity_pct / 100.0))
        b = 17.67 if temp_c >= 0.0 else 22.5
        c = 243.5 if temp_c >= 0.0 else 273.0
        gamma = math.log(rh) + (b * temp_c) / (c + temp_c)
        if abs(b - gamma) < 1e-5:
            return temp_c
        return (c * gamma) / (b - gamma)

    def process(self, temp_c: float, pressure_hpa: float, humidity_pct: float, dt_sec: float = 1.0) -> dict:
        # 1. Bounds check -- kept in lock-step with the central WMO envelope in
        # backend/app/core/config.py (temp -95..65 C, pressure 300..1085 hPa,
        # humidity 0..100 %). These are the OUTER physical limits of any Earth
        # surface station, not a typical operating range: the old -40..60 C /
        # 700..1100 hPa gate silently rejected legitimate polar and high-altitude
        # readings that the corrected central config now accepts, so an edge node
        # would have flagged as broken exactly what the server treats as valid.
        if temp_c < -95.0 or temp_c > 65.0 or pressure_hpa < 300.0 or pressure_hpa > 1085.0 or humidity_pct < 0.0 or humidity_pct > 100.0:
            return {"is_anomaly": True, "confidence": 1.0, "type": "OUT_OF_BOUNDS"}

        # 2. Dew point check (record dew point on Earth is ~35C, Dhahran 2003)
        td = self.compute_dew_point(temp_c, humidity_pct)
        if td > temp_c + 0.5 or td > 36.0:
            return {"is_anomaly": True, "confidence": 0.95, "type": "PHYSICS_VIOLATION", "td": td}

        # 3. Rate of change (Spike). Includes humidity: prev_hum was recorded every
        # step (see below) but never checked, so a physically impossible RH jump --
        # e.g. 20% -> 95% between consecutive readings -- passed this tier silently.
        # The 15 %/min limit mirrors config.py's humidity max_step_1min.
        if self.prev_temp is not None:
            time_factor = max(0.05, dt_sec / 60.0)
            if (abs(temp_c - self.prev_temp) > (3.0 * time_factor)
                    or abs(pressure_hpa - self.prev_pres) > (2.0 * time_factor)
                    or abs(humidity_pct - self.prev_hum) > (15.0 * time_factor)):
                return {"is_anomaly": True, "confidence": 0.85, "type": "RATE_SPIKE"}

        # 4. Flatline
        if self.last_temp == temp_c:
            self.flatline_count += 1
            if self.flatline_count >= 5:
                return {"is_anomaly": True, "confidence": 0.90, "type": "FLATLINE"}
        else:
            self.last_temp = temp_c
            self.flatline_count = 1

        # 5. Online Welford Z-Score drift check (mirrors skyguard_edge.h's Welford
        # update -- this Python module previously declared mean_t/m2_t but never
        # used them, so it silently had no drift-detection tier at all while the
        # C header did. Both are lifetime (unwindowed) statistics by design: this
        # is a minimal, O(1)-memory edge tier meant to catch a sensor's calibration
        # wandering off its long-run baseline, not to track short-term diurnal
        # variation the way the central pipeline's adaptive EWMA baseline does.
        self.count += 1
        delta = temp_c - self.mean_t
        self.mean_t += delta / self.count
        delta2 = temp_c - self.mean_t
        self.m2_t += delta * delta2

        variance = (self.m2_t / self.count) if self.count > 1 else 1.0
        std_dev = max(0.1, variance ** 0.5)
        z = abs(temp_c - self.mean_t) / std_dev

        if self.count > 10 and z > 3.8:
            return {"is_anomaly": True, "confidence": 0.75, "type": "DRIFT", "td": td, "z_score": z}

        self.prev_temp = temp_c
        self.prev_pres = pressure_hpa
        self.prev_hum = humidity_pct

        return {"is_anomaly": False, "confidence": 0.0, "type": "NORMAL", "td": td}
