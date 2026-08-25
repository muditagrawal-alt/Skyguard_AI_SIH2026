// Thin REST client for the SkyGuard FastAPI backend. Every call throws on a
// network error or non-2xx response; callers (the StreamProvider) decide how to
// degrade — typically by flagging the backend offline and falling back to the
// mock data in components/data.ts.

import { apiUrl } from "./config";
import type {
  ProcessedPacket,
  StationMeta,
  AnomalyType,
  SensorTarget,
} from "./types";

async function getJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(apiUrl(path), {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    let detail = "";
    try {
      const body = (await res.json()) as { detail?: string };
      detail = body?.detail ? ` — ${body.detail}` : "";
    } catch {
      /* non-JSON error body; ignore */
    }
    throw new Error(`${init?.method ?? "GET"} ${path} failed: ${res.status}${detail}`);
  }
  return (await res.json()) as T;
}

export async function fetchStations(): Promise<StationMeta[]> {
  const data = await getJson<{ stations: StationMeta[] }>("/api/stations");
  return data.stations;
}

export async function fetchLatestReading(stationId: string): Promise<ProcessedPacket> {
  return getJson<ProcessedPacket>(`/api/latest_reading/${encodeURIComponent(stationId)}`);
}

export async function fetchStationBuffer(
  stationId: string,
): Promise<{ station_id: string; count: number; history: ProcessedPacket[] }> {
  return getJson(`/api/station_buffer/${encodeURIComponent(stationId)}`);
}

export type InjectAnomalyBody = {
  station_id: string;
  anomaly_type: AnomalyType;
  sensor?: SensorTarget;
  intensity?: number;
  duration_steps?: number;
};

export async function injectAnomaly(
  body: InjectAnomalyBody,
): Promise<{ status: string; message: string }> {
  return getJson("/api/inject_anomaly", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function clearBuffer(
  stationId: string,
): Promise<{ status: string; station_id: string; message: string }> {
  return getJson(`/api/clear_buffer/${encodeURIComponent(stationId)}`, {
    method: "POST",
  });
}
