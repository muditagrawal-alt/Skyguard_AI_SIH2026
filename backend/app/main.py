"""
SkyGuard AI - FastAPI REST API & WebSocket Streaming Server
Provides real-time telemetry streaming, interactive anomaly injection,
batch data inference, and system diagnostics.
"""

import asyncio
import csv as _csv
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.app.core.config import config
from backend.app.core.data_generator import simulator, AnomalyInjectionRequest
from backend.app.core.pipeline import pipeline
from backend.app.core import llm

VALID_ANOMALY_TYPES = {"spike", "flatline", "drift", "physics_violation", "packet_loss", "thunderstorm"}
VALID_SENSORS = {"temperature", "pressure", "humidity", "all"}

# Real NOAA ISD-Lite history lives at <repo>/data/real_stations/processed/{id}.csv.
# main.py is backend/app/main.py, so parents[2] is the repo root. Loaded via the
# stdlib csv module (not pandas) so the live API path carries no heavy dependency,
# and cached in-process because these files run to tens of thousands of rows.
REAL_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "real_stations" / "processed"
_real_data_cache: Dict[str, Optional[List[Dict[str, str]]]] = {}


def _load_real_station_rows(station_id: str) -> Optional[List[Dict[str, str]]]:
    """
    Returns the cached list of raw CSV rows for a station's real NOAA history,
    or None if no processed file exists for it. Columns:
    timestamp, temperature_c, pressure_hpa, humidity_pct.
    """
    if station_id in _real_data_cache:
        return _real_data_cache[station_id]
    path = REAL_DATA_DIR / f"{station_id}.csv"
    if not path.exists():
        _real_data_cache[station_id] = None
        return None
    with open(path, newline="") as f:
        rows = list(_csv.DictReader(f))
    _real_data_cache[station_id] = rows or None
    return _real_data_cache[station_id]

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
    `has_real_data` flags whether real NOAA ISD-Lite history is available for replay
    on that station (drives the frontend's Real/Synthetic data-source toggle).
    """
    stations = []
    for p in config.stations.values():
        entry = p.model_dump()
        entry["has_real_data"] = _load_real_station_rows(p.station_id) is not None
        stations.append(entry)
    return {"stations": stations}


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


@app.post("/api/clear_buffer/{station_id}")
def clear_buffer(station_id: str):
    """
    Clears a station's rolling sliding-window buffer (the history the dashboard
    charts and audit log are drawn from). Backs the "Clear buffer" control on the
    Live Monitor. Note this intentionally clears only the visualization/history
    buffer -- it does NOT reset the statistical engine's per-station EWMA/CUSUM
    baselines, since those are shared singleton state and there is no per-station
    reset (resetting them would affect every station).
    """
    if station_id not in config.stations:
        raise HTTPException(status_code=404, detail=f"Unknown station_id '{station_id}'")
    pipeline.station_buffers[station_id] = []
    return {
        "status": "success",
        "station_id": station_id,
        "message": "Sliding-window buffer cleared."
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


class LLMCompletionRequest(BaseModel):
    prompt: str
    system: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


@app.get("/api/llm/health")
def llm_health():
    """
    Reports whether the Groq LLM (GROQ_MODEL, default openai/gpt-oss-20b) is
    reachable with the configured key, via a tiny round-trip. Safe to poll and
    never returns the API key. End-to-end check: with the dashboard running, open
    the browser console and run
        fetch('/api/llm/health').then(r => r.json()).then(console.log)
    which exercises the full frontend-proxy -> API -> Groq path.
    """
    return llm.health()


@app.post("/api/llm/complete")
def llm_complete(request: LLMCompletionRequest):
    """
    Generic chat completion via Groq. Returns {text, model, latency_ms, usage}.
    The frontend should call this (through the /api proxy) instead of talking to
    Groq directly, so the secret key never leaves the backend. Returns 503 if the
    LLM is unconfigured or the upstream call fails.
    """
    messages: List[Dict[str, str]] = []
    if request.system:
        messages.append({"role": "system", "content": request.system})
    messages.append({"role": "user", "content": request.prompt})
    try:
        return llm.chat(messages, temperature=request.temperature, max_tokens=request.max_tokens)
    except llm.LLMError as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.websocket("/ws/telemetry")
async def websocket_telemetry_endpoint(
    websocket: WebSocket,
    station_id: str = "AWS_ALPHA_MOUNTAIN",
    rate_hz: float = 1.0,
    source: str = "synthetic",
):
    """
    High-frequency real-time WebSocket broadcasting processed telemetry packets.

    `source` selects the data feed:
      - "synthetic" (default): the diurnal virtual-AWS generator.
      - "real": replays this station's real NOAA ISD-Lite history (looping when
        exhausted). dt_seconds is computed from the real gap between consecutive
        timestamps -- NOT from rate_hz, which only controls how fast the replay
        advances on screen, not what the model is told about elapsed real time.
    Anomaly injections from /api/inject_anomaly apply to both feeds (the real path
    replays genuine weather as the clean background, then layers labeled faults).
    """
    await websocket.accept()
    if station_id not in config.stations:
        # generate_next_reading() silently substitutes the first configured station
        # for an unknown id, which would otherwise stream a DIFFERENT station's data
        # under the requested id with no indication of the mismatch to the client.
        await websocket.send_text(json.dumps({"error": f"Unknown station_id '{station_id}'"}))
        await websocket.close(code=1008)
        return

    source = (source or "synthetic").lower()
    delay = 1.0 / max(0.2, min(10.0, rate_hz))

    # Per-connection real-replay state: each stream replays from the start of the
    # history with its own cursor, so opening a new stream restarts the replay.
    real_rows: Optional[List[Dict[str, str]]] = None
    if source == "real":
        real_rows = _load_real_station_rows(station_id)
        if not real_rows:
            await websocket.send_text(json.dumps(
                {"error": f"No real NOAA data available for station '{station_id}'."}
            ))
            await websocket.close(code=1008)
            return
    cursor = 0
    prev_ts: Optional[datetime] = None

    try:
        while True:
            if source == "real" and real_rows:
                row = real_rows[cursor % len(real_rows)]
                cursor += 1
                ts_str = row["timestamp"]
                try:
                    ts = datetime.fromisoformat(ts_str)
                    dt_seconds = max(60.0, (ts - prev_ts).total_seconds()) if prev_ts else 3600.0
                    prev_ts = ts
                except (ValueError, TypeError):
                    dt_seconds = 3600.0
                raw_packet = simulator.generate_next_reading_from_real(
                    station_id,
                    float(row["temperature_c"]),
                    float(row["pressure_hpa"]),
                    float(row["humidity_pct"]),
                    ts_str,
                    dt_seconds=dt_seconds,
                )
                processed = pipeline.process_reading(raw_packet, dt_seconds=dt_seconds)
            else:
                raw_packet = simulator.generate_next_reading(station_id, dt_seconds=delay)
                processed = pipeline.process_reading(raw_packet, dt_seconds=delay)
            await websocket.send_text(json.dumps(processed))
            await asyncio.sleep(delay)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket client disconnected: {e}")
