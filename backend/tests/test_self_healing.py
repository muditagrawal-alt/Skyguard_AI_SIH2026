"""
Unit Tests for Self-Healing Imputation and Edge AI Module
"""

import pytest
from backend.app.core.self_healing import self_healing_imputer
from edge.skyguard_edge import MicroEdgeGuard


def test_self_healing_clean_reading():
    raw = {"temperature": 24.5, "pressure": 1012.0, "humidity": 65.0}
    res = self_healing_imputer.impute_reading(
        station_id="AWS_BETA_COASTAL",
        current_raw=raw,
        temporal_history=[],
        is_anomaly=False,
        fault_type="NORMAL"
    )
    assert res["is_imputed"] is False
    assert res["temperature"] == 24.5


def test_self_healing_missing_packet():
    raw = {"temperature": None, "pressure": None, "humidity": None}
    history = [
        {"imputed": {"temperature": 25.0, "pressure": 1012.0, "humidity": 60.0}},
        {"imputed": {"temperature": 25.2, "pressure": 1012.1, "humidity": 59.8}},
        {"imputed": {"temperature": 25.4, "pressure": 1012.2, "humidity": 59.5}}
    ]
    res = self_healing_imputer.impute_reading(
        station_id="AWS_BETA_COASTAL",
        current_raw=raw,
        temporal_history=history,
        is_anomaly=True,
        fault_type="COMMUNICATION_DROPOUT"
    )
    assert res["is_imputed"] is True
    assert res["temperature"] is not None
    assert abs(res["temperature"] - 25.3) < 0.5


def test_micro_edge_guard():
    edge = MicroEdgeGuard()
    # Normal reading
    res1 = edge.process(temp_c=25.0, pressure_hpa=1013.0, humidity_pct=60.0)
    assert res1["is_anomaly"] is False

    # Immediate spike
    res2 = edge.process(temp_c=45.0, pressure_hpa=1013.0, humidity_pct=60.0, dt_sec=1.0)
    assert res2["is_anomaly"] is True
    assert res2["type"] == "RATE_SPIKE"
