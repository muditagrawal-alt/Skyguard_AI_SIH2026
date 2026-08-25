"""
SkyGuard AI - FastAPI REST API & WebSocket Streaming Server
Provides real-time telemetry streaming, interactive anomaly injection,
batch data inference, and system diagnostics.
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.app.core.config import config
from backend.app.core.data_generator import simulator, AnomalyInjectionRequest
from backend.app.core.pipeline import pipeline

VALID_ANOMALY_TYPES = {"spike", "flatline", "drift", "physics_violation", "packet_loss", "thunderstorm"}
VALID_SENSORS = {"temperature", "pressure", "humidity", "all"}

# Tracks wall-clock time of the last /api/latest_reading call per station, so the
# pipeline's rate-of-change and drift checks (both scaled by actual elapsed time,
# see physics.py and statistical.py) get a real dt_seconds instead of always
# assuming 1.0 -- a REST client polling this endpoint every few minutes would
# otherwise have every normal reading compared as if only 1 second had passed,
# producing spurious "rapid change" flags on completely ordinary polling gaps.
_last_poll_time: Dict[str, float] = {}

app = FastAPI(
    title="SkyGuard AI - Intelligent AWS Anomaly Detection Platform",
    version="1.0.0",
    description="Real-Time Physics-Informed Anomaly Detection, Self-Healing, and Explainable AI for Weather Stations."
)

# CORS for browser clients (Streamlit, web dashboards, IDE previews). This API is
# stateless and token/cookie-free, so credentials are disabled: the wildcard origin
# `allow_origins=["*"]` combined with `allow_credentials=True` is both a security
# anti-pattern and rejected by browsers outright (the spec forbids a wildcard origin
# on credentialed requests). If per-user auth is ever added, replace the wildcard
# with an explicit origin allow-list and re-enable credentials together.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class BatchInferenceRequest(BaseModel):
    station_id: Optional[str] = "AWS_ALPHA_MOUNTAIN"
    readings: List[Dict[str, Any]]


@app.get("/")
def get_root():
    return {
        "system": "SkyGuard AI",
        "status": "ONLINE",
        "stations_count": len(config.stations),
        "docs_url": "/docs"
    }


@app.get("/api/stations")
def get_stations():
    """
    Returns all configured Automatic Weather Stations and their geographical/climatic metadata.
    """
    return {
        "stations": [p.model_dump() for p in config.stations.values()]
    }


@app.post("/api/inject_anomaly")
def inject_anomaly(request: AnomalyInjectionRequest):
    """
    Triggers an anomaly injection on a target weather station.
    """
    if request.anomaly_type.lower() not in VALID_ANOMALY_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown anomaly_type '{request.anomaly_type}'. Must be one of: {sorted(VALID_ANOMALY_TYPES)}"
        )
    if request.sensor is not None and request.sensor.lower() not in VALID_SENSORS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown sensor '{request.sensor}'. Must be one of: {sorted(VALID_SENSORS)}"
        )
    res = simulator.inject_anomaly(request)
    if res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res.get("message"))
    return res


@app.get("/api/latest_reading/{station_id}")
def get_latest_reading(station_id: str):
    """
    Generates and returns a single processed time-step reading for a station.
    Elapsed real time since this station's last call is used as dt_seconds, so
    polling this endpoint slowly doesn't get compared as if only 1 second passed.
    """
    if station_id not in config.stations:
        raise HTTPException(status_code=404, detail=f"Unknown station_id '{station_id}'")

    now = time.monotonic()
    dt_seconds = max(1.0, now - _last_poll_time[station_id]) if station_id in _last_poll_time else 1.0
    _last_poll_time[station_id] = now

    raw_packet = simulator.generate_next_reading(station_id, dt_seconds=dt_seconds)
    processed = pipeline.process_reading(raw_packet, dt_seconds=dt_seconds)
    return processed


@app.get("/api/station_buffer/{station_id}")
def get_station_buffer(station_id: str):
    """
    Returns recent sliding-window buffer history for a station.
    """
    if station_id not in config.stations:
        raise HTTPException(status_code=404, detail=f"Unknown station_id '{station_id}'")
    buffer = pipeline._get_buffer(station_id)
    return {
        "station_id": station_id,
        "count": len(buffer),
        "history": buffer
    }


@app.post("/api/detect_batch")
def detect_batch(request: BatchInferenceRequest):
    """
    Runs batch anomaly detection across an array of historical observations.
    dt_seconds between consecutive readings is computed from their timestamps
    (ISO 8601) when present, so real, unevenly-spaced historical data -- e.g.
    hourly station records -- is scored against physically correct rate-of-change
    and drift expectations instead of always assuming a 1-second gap.
    """
    results = []
    station_id = request.station_id or "AWS_ALPHA_MOUNTAIN"
    prev_ts: Optional[datetime] = None
    for r in request.readings:
        ts_raw = r.get("timestamp")
        dt_seconds = 1.0
        if ts_raw:
            try:
                ts = datetime.fromisoformat(str(ts_raw).replace("Z", "+00:00"))
                if prev_ts is not None:
                    dt_seconds = max(1.0, (ts - prev_ts).total_seconds())
                prev_ts = ts
            except (ValueError, TypeError):
                pass  # Unparseable timestamp: fall back to the 1-second default for this reading

        raw_packet = {
            "station_id": station_id,
            "timestamp": ts_raw,
            "temperature": r.get("temperature"),
            "pressure": r.get("pressure"),
            "humidity": r.get("humidity"),
            "is_packet_loss": r.get("temperature") is None
        }
        processed = pipeline.process_reading(raw_packet, dt_seconds=dt_seconds)
        results.append(processed)

    return {
        "total_processed": len(results),
        "results": results
    }


@app.websocket("/ws/telemetry")
async def websocket_telemetry_endpoint(websocket: WebSocket, station_id: str = "AWS_ALPHA_MOUNTAIN", rate_hz: float = 1.0):
    """
    High-frequency real-time WebSocket broadcasting processed telemetry packets.
    """
    await websocket.accept()
    if station_id not in config.stations:
        # generate_next_reading() silently substitutes the first configured station
        # for an unknown id, which would otherwise stream a DIFFERENT station's data
        # under the requested id with no indication of the mismatch to the client.
        await websocket.send_text(json.dumps({"error": f"Unknown station_id '{station_id}'"}))
        await websocket.close(code=1008)
        return
    delay = 1.0 / max(0.2, min(10.0, rate_hz))

    try:
        while True:
            raw_packet = simulator.generate_next_reading(station_id, dt_seconds=delay)
            processed = pipeline.process_reading(raw_packet, dt_seconds=delay)
            await websocket.send_text(json.dumps(processed))
            await asyncio.sleep(delay)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket client disconnected: {e}")
