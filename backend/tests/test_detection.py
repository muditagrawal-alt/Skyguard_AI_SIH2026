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
