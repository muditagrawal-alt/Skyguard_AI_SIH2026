"""
Unit Tests for Anomaly Detection Pipeline and Machine Learning Ensemble
"""

import pytest
from backend.app.core.data_generator import VirtualAWSNetworkSimulator, AnomalyInjectionRequest
from backend.app.core.pipeline import SkyGuardPipeline


def test_pipeline_normal_stream():
    sim = VirtualAWSNetworkSimulator()
    pipe = SkyGuardPipeline()
    station_id = "AWS_ALPHA_MOUNTAIN"

    # Step 15 clean steps
    for _ in range(15):
        raw = sim.generate_next_reading(station_id, dt_seconds=1.0)
        res = pipe.process_reading(raw, dt_seconds=1.0)

    # Clean normal reading should not be anomalous
    raw = sim.generate_next_reading(station_id, dt_seconds=1.0)
    res = pipe.process_reading(raw, dt_seconds=1.0)

    assert res["ensemble"]["is_anomaly"] is False
    assert res["root_cause"]["fault_type"] == "NORMAL"
    assert res["imputed"]["is_imputed"] is False


def test_pipeline_spike_detection():
    sim = VirtualAWSNetworkSimulator()
    pipe = SkyGuardPipeline()
    station_id = "AWS_ALPHA_MOUNTAIN"

    for _ in range(10):
        raw = sim.generate_next_reading(station_id, dt_seconds=1.0)
        pipe.process_reading(raw, dt_seconds=1.0)

    # Inject spike
    sim.inject_anomaly(AnomalyInjectionRequest(station_id=station_id, anomaly_type="spike", sensor="temperature", intensity=1.5, duration_steps=1))
    raw = sim.generate_next_reading(station_id, dt_seconds=1.0)
    res = pipe.process_reading(raw, dt_seconds=1.0)

    assert res["ensemble"]["is_anomaly"] is True
    assert res["imputed"]["is_imputed"] is True


def test_pipeline_flatline_detection():
    sim = VirtualAWSNetworkSimulator()
    pipe = SkyGuardPipeline()
    station_id = "AWS_ALPHA_MOUNTAIN"

    for _ in range(10):
        raw = sim.generate_next_reading(station_id, dt_seconds=1.0)
        pipe.process_reading(raw, dt_seconds=1.0)

    sim.inject_anomaly(AnomalyInjectionRequest(station_id=station_id, anomaly_type="flatline", sensor="temperature", intensity=1.0, duration_steps=10))

    flatline_detected = False
    for _ in range(10):
        raw = sim.generate_next_reading(station_id, dt_seconds=1.0)
        res = pipe.process_reading(raw, dt_seconds=1.0)
        if res["root_cause"]["fault_type"] == "SENSOR_FLATLINE":
            flatline_detected = True
            break

    assert flatline_detected is True


def test_pipeline_partial_packet_does_not_crash():
    """
    Regression: a partial packet -- one or more of temperature/pressure/humidity
    present, the rest missing -- must process without raising. Previously the
    pipeline only guarded the Isolation Forest path on `temperature is not None`,
    so a reading with temperature present but pressure or humidity missing reached
    StandardScaler.transform() with an array containing None. That raised (object-
    dtype TypeError on numpy<2, "Input contains NaN" on numpy>=2) and surfaced as
    an HTTP 500 on /api/detect_batch. Any reading missing a core sensor is now
    routed through the same 'missing telemetry' branch the physics engine used.
    """
    sim = VirtualAWSNetworkSimulator()
    pipe = SkyGuardPipeline()
    station_id = "AWS_ALPHA_MOUNTAIN"

    # Warm up with clean, complete readings so a buffer/history exists.
    for _ in range(10):
        raw = sim.generate_next_reading(station_id, dt_seconds=1.0)
        pipe.process_reading(raw, dt_seconds=1.0)

    partial_packets = [
        {"station_id": station_id, "temperature": 25.0, "pressure": None, "humidity": None},
        {"station_id": station_id, "temperature": 25.0, "pressure": 1012.0, "humidity": None},
        {"station_id": station_id, "temperature": 25.0, "pressure": None, "humidity": 60.0},
        {"station_id": station_id, "temperature": None, "pressure": 1012.0, "humidity": 60.0},
    ]
    for pkt in partial_packets:
        res = pipe.process_reading(pkt, dt_seconds=1.0)
        assert "isolation_forest" in res
        assert res["isolation_forest"]["isolation_anomaly_prob"] is not None
        assert isinstance(res["ensemble"]["is_anomaly"], bool)


def test_isolation_forest_handles_none_inputs():
    """
    Regression (defense-in-depth): scoring an observation with any None feature
    must return the safe 'missing telemetry' result instead of raising, even when
    called directly, bypassing the pipeline's guard.
    """
    from backend.app.models.isolation_forest import multivariate_detector

    res = multivariate_detector.score_observation(
        temp_c=25.0, pressure_hpa=None, humidity_pct=None
    )
    assert res["is_multivariate_outlier"] is True
    assert res["isolation_anomaly_prob"] == 0.95

    # A fully-specified observation must still score normally (no false fallback).
    ok = multivariate_detector.score_observation(
        temp_c=25.0, pressure_hpa=1012.0, humidity_pct=60.0
    )
    assert 0.0 <= ok["isolation_anomaly_prob"] <= 1.0
