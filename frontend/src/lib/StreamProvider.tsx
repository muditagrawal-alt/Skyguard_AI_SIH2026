// StreamProvider: the single source of live telemetry for the whole dashboard.
//
// Responsibilities
//  - Load station metadata from the backend (REST), retrying until it's up.
//  - Open one reconnecting WebSocket per station so every page is live at once
//    (and so the backend's cross-station spatial check has neighbours to compare).
//  - Keep a capped rolling buffer + latest packet per station.
//  - Expose controls: start / stop / clear, station selection, data source
//    (synthetic vs real NOAA), playback rate, and anomaly injection.
//  - Degrade gracefully: when the backend is unreachable, `backendOnline` is
//    false and components fall back to the mock data in components/data.ts.

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import {
  clearBuffer as apiClearBuffer,
  fetchStationBuffer,
  fetchStations,
  injectAnomaly,
} from "./api";
import { TelemetryStream, type StreamStatus } from "./ws";
import type {
  AnomalyType,
  DataSource,
  ProcessedPacket,
  SensorTarget,
  StationMeta,
} from "./types";

const BUFFER_CAP = 120;
const STATIONS_RETRY_MS = 4000;
const DEFAULT_STATION = "AWS_GAMMA_URBAN";

// Offline fallback so the station switcher / network views still list the four
// stations (mirrors backend/app/core/config.py). has_real_data is unknown when
// offline, so it's reported false.
const FALLBACK_STATIONS: StationMeta[] = [
  { station_id: "AWS_ALPHA_MOUNTAIN", name: "Alpha Ridge (Highland Station)", station_type: "Mountain", latitude: 34.125, longitude: -117.85, elevation_m: 2150, base_temp_c: 12, temp_diurnal_range_c: 16, base_pressure_hpa: 785, base_humidity_pct: 45, humidity_diurnal_range_pct: 30, has_real_data: false },
  { station_id: "AWS_BETA_COASTAL", name: "Beta Coastline (Marine Station)", station_type: "Coastal", latitude: 18.922, longitude: 72.834, elevation_m: 10, base_temp_c: 27, temp_diurnal_range_c: 7, base_pressure_hpa: 1012, base_humidity_pct: 82, humidity_diurnal_range_pct: 15, has_real_data: false },
  { station_id: "AWS_GAMMA_URBAN", name: "Gamma Metropole (Urban Station)", station_type: "Urban", latitude: 28.613, longitude: 77.209, elevation_m: 216, base_temp_c: 25, temp_diurnal_range_c: 14, base_pressure_hpa: 990, base_humidity_pct: 60, humidity_diurnal_range_pct: 28, has_real_data: false },
  { station_id: "AWS_DELTA_DESERT", name: "Delta Dunes (Arid Desert Station)", station_type: "Desert", latitude: 26.915, longitude: 70.908, elevation_m: 220, base_temp_c: 34, temp_diurnal_range_c: 22, base_pressure_hpa: 995, base_humidity_pct: 22, humidity_diurnal_range_pct: 16, has_real_data: false },
];

type Store = {
  buffers: Record<string, ProcessedPacket[]>;
  latestByStation: Record<string, ProcessedPacket>;
};

export type StreamContextValue = {
  // metadata + connection
  stations: StationMeta[];
  backendOnline: boolean;
  connected: boolean;
  notice: string | null;
  // controls state
  running: boolean;
  dataSource: DataSource;
  rateHz: number;
  selectedStationId: string;
  // data
  buffers: Record<string, ProcessedPacket[]>;
  latestByStation: Record<string, ProcessedPacket>;
  selectedBuffer: ProcessedPacket[];
  selectedLatest: ProcessedPacket | null;
  // derived convenience
  selectedStation: StationMeta | null;
  anyRealDataAvailable: boolean;
  // actions
  start: () => void;
  stop: () => void;
  clear: () => void;
  setStation: (id: string) => void;
  setDataSource: (src: DataSource) => void;
  setRate: (hz: number) => void;
  inject: (type: AnomalyType, sensor?: SensorTarget) => void;
};

const StreamContext = createContext<StreamContextValue | null>(null);

export function StreamProvider({ children }: { children: ReactNode }) {
  const [stations, setStations] = useState<StationMeta[]>(FALLBACK_STATIONS);
  const [backendOnline, setBackendOnline] = useState(false);
  const [connected, setConnected] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  const [running, setRunning] = useState(true);
  const [dataSource, setDataSourceState] = useState<DataSource>("synthetic");
  const [rateHz, setRateHzState] = useState(1);
  const [selectedStationId, setSelectedStationId] = useState(DEFAULT_STATION);

  const [store, setStore] = useState<Store>({ buffers: {}, latestByStation: {} });

  const streamsRef = useRef<Map<string, TelemetryStream>>(new Map());
  const statusRef = useRef<Map<string, StreamStatus>>(new Map());

  const ingest = useCallback((id: string, pkt: ProcessedPacket) => {
    setStore((prev) => {
      const existing = prev.buffers[id];
      const buf = existing ? existing.slice() : [];
      buf.push(pkt);
      if (buf.length > BUFFER_CAP) buf.splice(0, buf.length - BUFFER_CAP);
      return {
        buffers: { ...prev.buffers, [id]: buf },
        latestByStation: { ...prev.latestByStation, [id]: pkt },
      };
    });
  }, []);

  const recomputeConnected = useCallback(() => {
    let open = false;
    statusRef.current.forEach((s) => {
      if (s === "open") open = true;
    });
    setConnected(open);
  }, []);

  // 1. Load station metadata, retrying until the backend answers.
  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | null = null;
    const load = async () => {
      try {
        const s = await fetchStations();
        if (cancelled) return;
        if (s.length > 0) setStations(s);
        setBackendOnline(true);
        setNotice(null);
      } catch {
        if (cancelled) return;
        setBackendOnline(false);
        timer = setTimeout(load, STATIONS_RETRY_MS);
      }
    };
    load();
    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
    };
  }, []);

  // 2. Best-effort prefill from the server's existing buffers so charts have
  //    history immediately on connect (only seeds stations with no data yet).
  useEffect(() => {
    if (!backendOnline || stations.length === 0) return;
    let cancelled = false;
    (async () => {
      const seededBuffers: Record<string, ProcessedPacket[]> = {};
      const seededLatest: Record<string, ProcessedPacket> = {};
      await Promise.all(
        stations.map(async (s) => {
          try {
            const { history } = await fetchStationBuffer(s.station_id);
            if (history && history.length > 0) {
              seededBuffers[s.station_id] = history.slice(-BUFFER_CAP);
              seededLatest[s.station_id] = history[history.length - 1];
            }
          } catch {
            /* ignore per-station prefill failures */
          }
        }),
      );
      if (cancelled) return;
      setStore((prev) => {
        const buffers = { ...prev.buffers };
        const latestByStation = { ...prev.latestByStation };
        for (const id of Object.keys(seededBuffers)) {
          if (!buffers[id] || buffers[id].length === 0) {
            buffers[id] = seededBuffers[id];
            latestByStation[id] = seededLatest[id];
          }
        }
        return { buffers, latestByStation };
      });
    })();
    return () => {
      cancelled = true;
    };
  }, [backendOnline, stations]);

  // 3. Manage one WebSocket per station. Rebuilds when the feed config changes.
  useEffect(() => {
    streamsRef.current.forEach((s) => s.close());
    streamsRef.current.clear();
    statusRef.current.clear();
    setConnected(false);

    if (!running || !backendOnline || stations.length === 0) return;

    for (const meta of stations) {
      const id = meta.station_id;
      const stream = new TelemetryStream({
        stationId: id,
        rateHz,
        source: dataSource,
        onMessage: (pkt) => ingest(id, pkt),
        onStatus: (st) => {
          statusRef.current.set(id, st);
          recomputeConnected();
        },
        onError: (msg) => setNotice(msg),
      });
      streamsRef.current.set(id, stream);
    }

    return () => {
      streamsRef.current.forEach((s) => s.close());
      streamsRef.current.clear();
      statusRef.current.clear();
    };
  }, [running, backendOnline, dataSource, rateHz, stations, ingest, recomputeConnected]);

  // ── actions ─────────────────────────────────────────────
  const start = useCallback(() => setRunning(true), []);
  const stop = useCallback(() => setRunning(false), []);

  const setStation = useCallback((id: string) => setSelectedStationId(id), []);

  const setDataSource = useCallback((src: DataSource) => {
    setDataSourceState(src);
    setNotice(src === "real" ? "Switched to real NOAA replay" : "Switched to synthetic feed");
  }, []);

  const setRate = useCallback((hz: number) => {
    const clamped = Math.max(0.2, Math.min(10, hz));
    setRateHzState(clamped);
  }, []);

  const clear = useCallback(() => {
    const id = selectedStationId;
    setStore((prev) => {
      const buffers = { ...prev.buffers };
      const latestByStation = { ...prev.latestByStation };
      delete buffers[id];
      delete latestByStation[id];
      return { buffers, latestByStation };
    });
    apiClearBuffer(id).catch(() => {
      /* offline: local clear already applied */
    });
  }, [selectedStationId]);

  const inject = useCallback(
    (type: AnomalyType, sensor?: SensorTarget) => {
      injectAnomaly({ station_id: selectedStationId, anomaly_type: type, sensor })
        .then((res) => setNotice(res.message))
        .catch((e: unknown) => setNotice(e instanceof Error ? e.message : "Injection failed"));
    },
    [selectedStationId],
  );

  const value = useMemo<StreamContextValue>(() => {
    const selectedStation = stations.find((s) => s.station_id === selectedStationId) ?? null;
    return {
      stations,
      backendOnline,
      connected,
      notice,
      running,
      dataSource,
      rateHz,
      selectedStationId,
      buffers: store.buffers,
      latestByStation: store.latestByStation,
      selectedBuffer: store.buffers[selectedStationId] ?? [],
      selectedLatest: store.latestByStation[selectedStationId] ?? null,
      selectedStation,
      anyRealDataAvailable: stations.some((s) => s.has_real_data),
      start,
      stop,
      clear,
      setStation,
      setDataSource,
      setRate,
      inject,
    };
  }, [
    stations,
    backendOnline,
    connected,
    notice,
    running,
    dataSource,
    rateHz,
    selectedStationId,
    store,
    start,
    stop,
    clear,
    setStation,
    setDataSource,
    setRate,
    inject,
  ]);

  return <StreamContext.Provider value={value}>{children}</StreamContext.Provider>;
}

export function useStream(): StreamContextValue {
  const ctx = useContext(StreamContext);
  if (!ctx) throw new Error("useStream must be used within a StreamProvider");
  return ctx;
}
