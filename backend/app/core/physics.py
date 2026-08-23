"""
SkyGuard AI - Meteorological & Psychrometric Physics Engine
Implements Magnus-Tetens formulation, Dew Point computation, Vapor Pressure Deficit (VPD),
and World Meteorological Organization (WMO) physical boundary verification.
"""

import math
from typing import Dict, Any, Tuple, Optional
from backend.app.core.config import config


class PhysicsEngine:
    def __init__(self):
        self.a = config.magnus_a_hpa
        self.b = config.magnus_b
        self.c = config.magnus_c
        self.ice_b = config.magnus_ice_b
        self.ice_c = config.magnus_ice_c

    def saturation_vapor_pressure(self, temp_c: float) -> float:
        """
        Calculates Saturation Vapor Pressure e_s (hPa) using the Magnus-Tetens formula.
        Switches between liquid water and ice formulations based on temperature.
        """
        if temp_c >= 0.0:
            b, c = self.b, self.c
        else:
            b, c = self.ice_b, self.ice_c
        
        exponent = (b * temp_c) / (c + temp_c)
        return self.a * math.exp(exponent)

    def actual_vapor_pressure(self, temp_c: float, humidity_pct: float) -> float:
        """
        Calculates Actual Vapor Pressure e (hPa) from temperature and relative humidity.
        """
        e_s = self.saturation_vapor_pressure(temp_c)
        rh_clamped = max(0.0, min(100.0, humidity_pct))
        return (rh_clamped / 100.0) * e_s

    def dew_point(self, temp_c: float, humidity_pct: float) -> float:
        """
        Calculates Dew Point Temperature T_d (°C) using the inverse Magnus relationship.
        """
        if humidity_pct <= 0.0:
            return -99.9  # Arbitrarily low dry limit
        
        if temp_c >= 0.0:
            b, c = self.b, self.c
        else:
            b, c = self.ice_b, self.ice_c

        rh_fraction = max(0.001, min(1.0, humidity_pct / 100.0))
        gamma = math.log(rh_fraction) + (b * temp_c) / (c + temp_c)
        
        # Avoid division by zero if gamma reaches b
        if abs(b - gamma) < 1e-6:
            return temp_c
            
        td = (c * gamma) / (b - gamma)
        return td

    def vapor_pressure_deficit(self, temp_c: float, humidity_pct: float) -> float:
        """
        Calculates Vapor Pressure Deficit VPD (hPa) = e_s(T) - e(T, RH).
        High VPD indicates dry atmospheric evaporative demand; near-zero indicates saturation.
        """
        e_s = self.saturation_vapor_pressure(temp_c)
        e = self.actual_vapor_pressure(temp_c, humidity_pct)
        return max(0.0, e_s - e)

    def verify_physical_consistency(
        self,
        temp_c: float,
        pressure_hpa: float,
        humidity_pct: float,
        prev_temp_c: Optional[float] = None,
        prev_pressure_hpa: Optional[float] = None,
        prev_humidity_pct: Optional[float] = None,
        dt_seconds: float = 1.0
    ) -> Dict[str, Any]:
        """
        Runs comprehensive physical consistency checks across all parameters:
        1. Range boundaries (WMO absolute physical limits)
        2. Psychrometric laws (Dew point vs. Temperature, VPD)
        3. Gradient/Rate-of-Change limits (WMO max step per unit time)
        4. Thermodynamic coupling (Enthalpy / Wet-bulb impossible conditions)
        """
        violations = []
        scores = []  # Sub-scores from 0.0 (clean) to 1.0 (severe violation)

        # 1. Compute psychrometric properties
        e_s = self.saturation_vapor_pressure(temp_c)
        e = self.actual_vapor_pressure(temp_c, humidity_pct)
        td = self.dew_point(temp_c, humidity_pct)
        vpd = self.vapor_pressure_deficit(temp_c, humidity_pct)
        dew_point_depression = temp_c - td

        # 2. Boundary Checks
        t_limits = config.limits["temperature"]
        p_limits = config.limits["pressure"]
        rh_limits = config.limits["humidity"]

        if temp_c < t_limits.min_val or temp_c > t_limits.max_val:
            violations.append(f"Temperature {temp_c:.1f}°C out of WMO bounds [{t_limits.min_val}, {t_limits.max_val}]")
            scores.append(1.0)
        
        if pressure_hpa < p_limits.min_val or pressure_hpa > p_limits.max_val:
            violations.append(f"Pressure {pressure_hpa:.1f} hPa out of WMO bounds [{p_limits.min_val}, {p_limits.max_val}]")
            scores.append(1.0)

        if humidity_pct < rh_limits.min_val or humidity_pct > 102.0:
            violations.append(f"Humidity {humidity_pct:.1f}% out of physical bounds [0%, 100%]")
            scores.append(1.0)

        # 3. Psychrometric Dew Point Violation (T_d cannot exceed T by more than standard measurement tolerance)
        if dew_point_depression < -0.5:
            violations.append(f"Thermodynamic violation: Dew point ({td:.1f}°C) exceeds ambient temperature ({temp_c:.1f}°C)")
            scores.append(min(1.0, abs(dew_point_depression) / 3.0))

        # 4. Extreme Wet-Bulb / Enthalpy Inconsistency
        # E.g. T > 48°C with RH > 85% is physically impossible on Earth surface without massive barometric anomaly
        if temp_c > 45.0 and humidity_pct > 80.0:
            violations.append(f"Thermodynamic enthalpy violation: Unphysical combination of high temp ({temp_c:.1f}°C) and high humidity ({humidity_pct:.1f}%)")
            scores.append(0.95)

        # 5. Gradient & Rate-of-Change Checks (if previous reading available)
        rate_violations = []
        if prev_temp_c is not None and prev_pressure_hpa is not None and prev_humidity_pct is not None:
            # Scale allowable step to elapsed time with instrument noise floor
            time_factor = max(0.05, dt_seconds / 60.0)
            
            d_temp = abs(temp_c - prev_temp_c)
            d_pres = abs(pressure_hpa - prev_pressure_hpa)
            d_hum = abs(humidity_pct - prev_humidity_pct)

            # Enforce physical gradient limits plus instrument precision noise tolerance
            max_d_temp = max(0.6, t_limits.max_step_1min * time_factor)
            max_d_pres = max(0.8, p_limits.max_step_1min * time_factor)
            max_d_hum = max(3.0, rh_limits.max_step_1min * time_factor)

            if d_temp > max_d_temp:
                rate_violations.append(f"Rapid ΔT ({d_temp:.2f}°C in {dt_seconds:.1f}s exceeds limit {max_d_temp:.2f}°C)")
                scores.append(min(1.0, d_temp / (max_d_temp * 2.0)))

            if d_pres > max_d_pres:
                rate_violations.append(f"Rapid ΔP ({d_pres:.2f} hPa in {dt_seconds:.1f}s exceeds limit {max_d_pres:.2f} hPa)")
                scores.append(min(1.0, d_pres / (max_d_pres * 2.0)))

            if d_hum > max_d_hum:
                rate_violations.append(f"Rapid ΔRH ({d_hum:.2f}% in {dt_seconds:.1f}s exceeds limit {max_d_hum:.2f}%)")
                scores.append(min(1.0, d_hum / (max_d_hum * 2.0)))

        all_violations = violations + rate_violations
        physics_anomaly_score = max(scores) if scores else 0.0

        return {
            "dew_point_c": round(td, 2),
            "sat_vapor_pressure_hpa": round(e_s, 2),
            "actual_vapor_pressure_hpa": round(e, 2),
            "vpd_hpa": round(vpd, 2),
            "dew_point_depression_c": round(dew_point_depression, 2),
            "is_physics_violation": len(all_violations) > 0,
            "physics_anomaly_score": round(physics_anomaly_score, 4),
            "violations": all_violations
        }


physics_engine = PhysicsEngine()
