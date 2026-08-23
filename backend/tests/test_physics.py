"""
Unit Tests for Meteorological and Psychrometric Physics Engine
"""

import pytest
import math
from backend.app.core.physics import physics_engine


def test_saturation_vapor_pressure():
    # At 0°C, e_s should be ~6.112 hPa
    es_0 = physics_engine.saturation_vapor_pressure(0.0)
    assert abs(es_0 - 6.112) < 0.05

    # At 20°C, e_s is ~23.38 hPa
    es_20 = physics_engine.saturation_vapor_pressure(20.0)
    assert abs(es_20 - 23.38) < 0.5

    # At 40°C (hot surface conditions), e_s is ~73.8 hPa
    es_40 = physics_engine.saturation_vapor_pressure(40.0)
    assert abs(es_40 - 73.8) < 1.0


def test_dew_point_calculation():
    # At 100% RH, T_d must equal T
    td_sat = physics_engine.dew_point(temp_c=25.0, humidity_pct=100.0)
    assert abs(td_sat - 25.0) < 0.1

    # At 20°C and 50% RH, T_d is ~9.3°C
    td_50 = physics_engine.dew_point(temp_c=20.0, humidity_pct=50.0)
    assert abs(td_50 - 9.3) < 0.5


def test_vapor_pressure_deficit():
    # At 100% RH, VPD must be 0.0
    vpd_sat = physics_engine.vapor_pressure_deficit(temp_c=30.0, humidity_pct=100.0)
    assert abs(vpd_sat - 0.0) < 0.01

    # At 30°C and 40% RH, VPD must be positive
    vpd_dry = physics_engine.vapor_pressure_deficit(temp_c=30.0, humidity_pct=40.0)
    assert vpd_dry > 20.0


def test_physical_consistency_valid():
    res = physics_engine.verify_physical_consistency(
        temp_c=25.0,
        pressure_hpa=1013.0,
        humidity_pct=60.0,
        prev_temp_c=24.9,
        prev_pressure_hpa=1013.1,
        prev_humidity_pct=60.2,
        dt_seconds=1.0
    )
    assert res["is_physics_violation"] is False
    assert res["physics_anomaly_score"] == 0.0
    assert len(res["violations"]) == 0


def test_physical_consistency_impossible_dewpoint():
    # Anomaly: Humidity 115% or impossible enthalpy
    res = physics_engine.verify_physical_consistency(
        temp_c=52.0,
        pressure_hpa=1013.0,
        humidity_pct=95.0
    )
    assert res["is_physics_violation"] is True
    assert res["physics_anomaly_score"] > 0.8
