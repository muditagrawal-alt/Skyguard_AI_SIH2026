"""
SkyGuard AI - FastAPI REST API & WebSocket Streaming Server
Provides real-time telemetry streaming, interactive anomaly injection,
batch data inference, and system diagnostics.
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.app.core.config import config
from backend.app.core.data_generator import simulator, AnomalyInjectionRequest
from backend.app.core.pipeline import pipeline

app = FastAPI(
    title="SkyGuard AI - Intelligent AWS Anomaly Detection Platform",
    version="1.0.0",
    description="Real-Time Physics-Informed Anomaly Detection, Self-Healing, and Explainable AI for Weather Stations."
)

# Enable CORS for all origins (for Streamlit, Web clients, and IDE previews)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
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
        "stations": [p.dict() for p in config.stations.values()]
    }


@app.post("/api/inject_anomaly")
def inject_anomaly(request: AnomalyInjectionRequest):
    """
    Triggers an anomaly injection on a target weather station.
    """
    res = simulator.inject_anomaly(request)
    if res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res.get("message"))
    return res


@app.get("/api/latest_reading/{station_id}")
def get_latest_reading(station_id: str):
    """
    Generates and returns a single processed time-step reading for a station.
    """
    raw_packet = simulator.generate_next_reading(station_id)
    processed = pipeline.process_reading(raw_packet)
    return processed


@app.get("/api/station_buffer/{station_id}")
def get_station_buffer(station_id: str):
    """
    Returns recent sliding-window buffer history for a station.
    """
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
    """
    results = []
    station_id = request.station_id or "AWS_ALPHA_MOUNTAIN"
    for r in request.readings:
        raw_packet = {
            "station_id": station_id,
            "timestamp": r.get("timestamp"),
            "temperature": r.get("temperature"),
            "pressure": r.get("pressure"),
            "humidity": r.get("humidity"),
            "is_packet_loss": r.get("temperature") is None
        }
        processed = pipeline.process_reading(raw_packet)
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
