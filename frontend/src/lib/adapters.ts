// Adapters: transform backend ProcessedPacket data into the exact shapes the
// existing (mock-driven) UI components consume — see components/data.ts for the
// canonical shapes. Keeping this mapping in one pure module means the visual
// components barely change: they read the same object shapes, now sourced live.
//
// Every value the backend can send as null (a dropped packet) is handled: chart
// series get `null` (recharts renders a gap), display strings get "—".

import type { Status, AnomalyRow } from "../components/data";
import type { ProcessedPacket, StationMeta, Severity } from "./types";

// ── small helpers ─────────────────────────────────────────
export function shortName(name: string): string {
  return name.split(" (")[0].trim();
}

function humanize(faultType: string): string {
  const s = faultType.replace(/_/g, " ").toLowerCase().trim();
  return s.length ? s[0].toUpperCase() + s.slice(1) : s;
}

function fmt(v: number | null | undefined, digits: number): string {
  return v === null || v === undefined || Number.isNaN(v) ? "—" : v.toFixed(digits);
}

function round(v: number | null | undefined, digits = 0): number {
  if (v === null || v === undefined || Number.isNaN(v)) return 0;
  const f = 10 ** digits;
  return Math.round(v * f) / f;
}

// ── confidence display ────────────────────────────────────
// Displayed confidence never claims absolute certainty — a calibrated detector
// always carries residual uncertainty, so the SHOWN value is capped just under
// 100%. This is display-only: the backend's raw confidence_score is untouched.
const CONF_CEIL_PCT = 99.9;

export function fmtConfidencePct(score01: number): string {
  const pct = Number.isFinite(score01) ? Math.min(score01 * 100, CONF_CEIL_PCT) : 0;
  return `${pct.toFixed(1)}%`;
}

// Compact 0–1 form for the pipeline stepper: caps at 0.99 so a saturated score
// reads "0.99" rather than a falsely-certain "1.00".
export function fmtConfidenceUnit(score01: number): string {
  const v = Number.isFinite(score01) ? Math.min(score01, 0.99) : 0;
  return v.toFixed(2);
}

// A small ± band derived honestly from how much the four detector sub-scores
// agree: tight when they concur, wider when (e.g.) physics fires but the others
// stay low. Clamped to a sensible 0.3–6.0% so it always reads cleanly.
function confidenceBand(p: ProcessedPacket): string {
  const c = p.ensemble.component_scores;
  const vals = [c.physics, c.autoencoder, c.isolation_forest, c.statistical].filter(
    (v): v is number => typeof v === "number" && Number.isFinite(v),
  );
  if (vals.length < 2) return "±2.0%";
  const spread = Math.max(...vals) - Math.min(...vals); // 0..1
  const band = Math.max(0.3, Math.min(6, (spread * 100) / 4));
  return `±${band.toFixed(1)}%`;
}

function timeHMS(iso: string): string {
  const d = new Date(iso);
  return Number.isNaN(d.getTime())
    ? "--:--:--"
    : d.toLocaleTimeString("en-GB", { hour12: false });
}

function timeHM(iso: string): string {
  const d = new Date(iso);
  return Number.isNaN(d.getTime())
    ? "--:--"
    : d.toLocaleTimeString("en-GB", { hour12: false, hour: "2-digit", minute: "2-digit" });
}

// ── status / severity mapping ─────────────────────────────
export function packetStatus(p: ProcessedPacket): Status {
  if (!p.ensemble.is_anomaly) return "normal";
  if (p.root_cause.is_genuine_weather) return "weather";
  switch (p.ensemble.severity) {
    case "CRITICAL":
      return "critical";
    case "HIGH":
      return "warning";
    default:
      return "weather";
  }
}

export function packetLabel(p: ProcessedPacket): string {
  if (!p.ensemble.is_anomaly) return "Normal";
  if (p.root_cause.is_genuine_weather) return "Weather event";
  return `Fault · ${humanize(p.root_cause.fault_type)}`;
}

type SeverityWord = "Critical" | "High" | "Medium" | "Info";

function severityWord(sev: Severity, isWeather: boolean): SeverityWord {
  if (isWeather) return "Info";
  switch (sev) {
    case "CRITICAL":
      return "Critical";
    case "HIGH":
      return "High";
    case "MEDIUM":
      return "Medium";
    default:
      return "Info";
  }
}

function sensorStatus(p: ProcessedPacket, sensor: "temperature" | "pressure" | "humidity"): Status {
  if (!p.ensemble.is_anomaly) return "normal";
  if (p.root_cause.is_genuine_weather) return "weather";
  const z = Math.abs((p.statistical.z_scores?.[sensor] as number) ?? 0);
  const flat = p.statistical.flatline_flags?.includes(sensor);
  const implicated = flat || z >= 3;
  return implicated ? packetStatus(p) : "normal";
}

// ── Live Monitor: stat cards ──────────────────────────────
export type MetricCard = {
  key: string;
  label: string;
  value: string;
  unit: string;
  color: string;
  status: Status;
  spark: number[];
};

function spark(
  buffer: ProcessedPacket[],
  getter: (p: ProcessedPacket) => number | null | undefined,
): number[] {
  return buffer
    .slice(-7)
    .map(getter)
    .filter((v): v is number => v !== null && v !== undefined && !Number.isNaN(v));
}

export function toMetrics(latest: ProcessedPacket, buffer: ProcessedPacket[]): MetricCard[] {
  return [
    {
      key: "temp",
      label: "Temperature",
      value: fmt(latest.raw.temperature, 1),
      unit: "°C",
      color: "var(--color-series-temp)",
      status: sensorStatus(latest, "temperature"),
      spark: spark(buffer, (p) => p.raw.temperature),
    },
    {
      key: "pressure",
      label: "Pressure",
      value: fmt(latest.raw.pressure, 1),
      unit: "hPa",
      color: "var(--color-series-pressure)",
      status: sensorStatus(latest, "pressure"),
      spark: spark(buffer, (p) => p.raw.pressure),
    },
    {
      key: "humidity",
      label: "Humidity",
      value: fmt(latest.raw.humidity, 0),
      unit: "%",
      color: "var(--color-series-humidity)",
      status: sensorStatus(latest, "humidity"),
      spark: spark(buffer, (p) => p.raw.humidity),
    },
    {
      key: "dew",
      label: "Dew point",
      value: fmt(latest.physics.dew_point_c, 1),
      unit: "°C",
      color: "var(--color-series-dew)",
      status: "normal",
      spark: spark(buffer, (p) => p.physics.dew_point_c),
    },
    {
      key: "vpd",
      label: "Vapor deficit (VPD)",
      value: fmt(latest.physics.vpd_hpa, 1),
      unit: "hPa",
      color: "var(--color-haze)",
      status: "normal",
      spark: spark(buffer, (p) => p.physics.vpd_hpa),
    },
  ];
}

// ── Live Monitor: telemetry charts ────────────────────────
export type TelemetryRow = {
  t: string;
  raw: number | null;
  truth: number | null;
  healed: number | null;
  flagged: number | null;
  pressure: number | null;
  pressureHealed: number | null;
  humidity: number | null;
  dew: number | null;
};

export function toTelemetryRows(buffer: ProcessedPacket[]): TelemetryRow[] {
  return buffer.slice(-48).map((p) => {
    const anomalous = p.ensemble.is_anomaly && !p.root_cause.is_genuine_weather;
    return {
      t: timeHM(p.timestamp),
      raw: p.raw.temperature,
      truth: p.clean_ground_truth?.temperature ?? null,
      healed: p.imputed.temperature,
      flagged: anomalous ? p.raw.temperature : null,
      pressure: p.raw.pressure,
      pressureHealed: p.imputed.is_imputed ? p.imputed.pressure : null,
      humidity: p.raw.humidity,
      dew: p.physics.dew_point_c,
    };
  });
}

// ── Live Monitor: explainable AI ──────────────────────────
export type AttributionBar = { label: string; value: number };

const ATTR_LABELS: Record<string, string> = {
  temperature: "Temperature",
  pressure: "Pressure",
  humidity: "Humidity level",
  delta_temp: "Temperature gradient",
  delta_pres: "Pressure tendency",
  delta_hum: "Humidity gradient",
  vpd: "Vapor deficit",
  dew_point_depression: "Dew-point spread",
};

export function toAttribution(p: ProcessedPacket, top = 4): AttributionBar[] {
  const attrs = p.xai.attributions;
  return Object.entries(attrs)
    .map(([k, v]) => ({ label: ATTR_LABELS[k] ?? k, value: round((v as number) * 100) }))
    .sort((a, b) => b.value - a.value)
    .slice(0, top);
}

// ── Live Monitor / Maintenance: sensor health ─────────────
export type HealthMeter = { label: string; value: number };

export function toHealthMeters(p: ProcessedPacket): HealthMeter[] {
  const s = p.sensor_health.sensor_scores;
  return [
    { label: "Temperature sensor", value: round(s.temperature) },
    { label: "Barometer", value: round(s.pressure) },
    { label: "Hygrometer", value: round(s.humidity) },
  ];
}

export function healthGauge(p: ProcessedPacket): number {
  return round(p.sensor_health.overall_health_score);
}

export function rulText(p: ProcessedPacket): string {
  return `${round(p.sensor_health.estimated_rul_days)} days`;
}

// ── Audit log / anomaly table ─────────────────────────────
export type AuditRow = {
  time: string;
  station: string;
  type: string;
  category: string;
  severity: SeverityWord;
  confidence: string;
  raw: string;
  healed: string;
  explain: string;
};

function anomaliesFrom(buffer: ProcessedPacket[]): ProcessedPacket[] {
  return buffer.filter((p) => p.ensemble.is_anomaly);
}

export function toAuditRows(buffer: ProcessedPacket[], limit = 12): AuditRow[] {
  return anomaliesFrom(buffer)
    .slice(-limit)
    .reverse()
    .map((p) => ({
      time: timeHMS(p.timestamp),
      station: shortName(p.station_name),
      type: p.root_cause.fault_type,
      category: p.root_cause.fault_category,
      severity: severityWord(p.ensemble.severity, p.root_cause.is_genuine_weather),
      confidence: fmtConfidencePct(p.ensemble.confidence_score),
      raw: fmt(p.raw.temperature, 1),
      healed: `${fmt(p.imputed.temperature, 1)} °C`,
      explain: p.xai.explanation,
    }));
}

export function packetToAnomalyRow(p: ProcessedPacket): AnomalyRow {
  return {
    time: timeHMS(p.timestamp),
    station: shortName(p.station_name),
    type: p.root_cause.fault_type,
    category: p.root_cause.fault_category,
    severity: severityWord(p.ensemble.severity, p.root_cause.is_genuine_weather),
    confidence: fmtConfidencePct(p.ensemble.confidence_score),
    raw: fmt(p.raw.temperature, 1),
    healed: `${fmt(p.imputed.temperature, 1)} °C`,
    state: "Open",
    verdict: p.root_cause.is_genuine_weather ? "weather" : "fault",
    explain: p.xai.explanation,
  };
}

export function toAnomalyRows(buffer: ProcessedPacket[], limit = 20): AnomalyRow[] {
  return anomaliesFrom(buffer).slice(-limit).reverse().map(packetToAnomalyRow);
}

// ── Overview / Stations / Map ─────────────────────────────
const STATION_UI: Record<string, { x: number; y: number }> = {
  AWS_ALPHA_MOUNTAIN: { x: 16, y: 34 },
  AWS_BETA_COASTAL: { x: 71, y: 72 },
  AWS_GAMMA_URBAN: { x: 74, y: 46 },
  AWS_DELTA_DESERT: { x: 67, y: 52 },
};

function fmtLoc(lat: number, lon: number): string {
  const ns = lat >= 0 ? "N" : "S";
  const ew = lon >= 0 ? "E" : "W";
  return `${Math.abs(lat).toFixed(2)}°${ns}, ${Math.abs(lon).toFixed(2)}°${ew}`;
}

export type StationRow = {
  id: string;
  name: string;
  type: string;
  loc: string;
  status: Status;
  label: string;
  health: number;
  rul: string;
  last: string;
  anomalies: number;
};

export function toStationRow(
  meta: StationMeta,
  latest: ProcessedPacket | null,
  anomalyCount: number,
): StationRow {
  return {
    id: meta.station_id,
    name: shortName(meta.name),
    type: meta.station_type,
    loc: fmtLoc(meta.latitude, meta.longitude),
    status: latest ? packetStatus(latest) : "idle",
    label: latest ? packetLabel(latest) : "Offline",
    health: latest ? round(latest.sensor_health.overall_health_score) : 0,
    rul: latest ? `${round(latest.sensor_health.estimated_rul_days)} d` : "—",
    last: latest ? `${fmt(latest.raw.temperature, 1)} °C · live` : "—",
    anomalies: anomalyCount,
  };
}

export type MapPin = {
  id: string;
  name: string;
  type: string;
  temp: string;
  status: Status;
  label: string;
  x: number;
  y: number;
};

export function toMapPin(meta: StationMeta, latest: ProcessedPacket | null): MapPin {
  const coords = STATION_UI[meta.station_id] ?? { x: 50, y: 50 };
  return {
    id: meta.station_id,
    name: shortName(meta.name),
    type: meta.station_type,
    temp: latest ? `${fmt(latest.raw.temperature, 1)} °C` : "—",
    status: latest ? packetStatus(latest) : "idle",
    label: latest ? packetLabel(latest) : "Offline",
    x: coords.x,
    y: coords.y,
  };
}

// Which channels are actually shifting (and in which direction) for a pin,
// derived from signed adaptive-baseline z-scores. Used for the map's weather
// corroboration caption so it reflects the real reading, not a fixed phrase.
// Falls back to a generic label when no channel shows a clear (>1σ) shift.
export function coordinatedChannels(p: ProcessedPacket): string {
  const z: Record<string, number> = p.statistical?.z_scores ?? {};
  const chans: [string, string][] = [
    ["pressure", "P"],
    ["temperature", "T"],
    ["humidity", "RH"],
  ];
  const parts = chans
    .map(([key, short]) => ({ short, v: z[key] }))
    .filter((c) => typeof c.v === "number" && Math.abs(c.v) >= 1)
    .sort((a, b) => Math.abs(b.v) - Math.abs(a.v))
    .map((c) => `${c.short}${c.v > 0 ? "↑" : "↓"}`);
  return parts.length ? `Coordinated ${parts.join(" · ")}` : "Coordinated multi-channel shift";
}

export type LiveAlert = {
  time: string;
  station: string;
  fault: string;
  severity: SeverityWord;
  verdict: "fault" | "weather";
  healed: boolean;
};

export function toLiveAlerts(buffers: Record<string, ProcessedPacket[]>, limit = 6): LiveAlert[] {
  const all: ProcessedPacket[] = [];
  for (const b of Object.values(buffers)) all.push(...anomaliesFrom(b));
  all.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
  return all.slice(0, limit).map((p) => ({
    time: timeHM(p.timestamp),
    station: shortName(p.station_name),
    fault: p.root_cause.is_genuine_weather ? "Weather event" : humanize(p.root_cause.fault_type),
    severity: severityWord(p.ensemble.severity, p.root_cause.is_genuine_weather),
    verdict: p.root_cause.is_genuine_weather ? "weather" : "fault",
    healed: p.imputed.is_imputed && !p.root_cause.is_genuine_weather,
  }));
}

export type CountBar = { label: string; value: number };

const DETECTION_BUCKETS: { label: string; test: (t: string) => boolean }[] = [
  { label: "Spike", test: (t) => t.includes("SPIKE") },
  { label: "Physics", test: (t) => t.includes("PHYSIC") },
  { label: "Flatline", test: (t) => t.includes("FLATLINE") },
  { label: "Drift", test: (t) => t.includes("DRIFT") },
  { label: "Packet loss", test: (t) => t.includes("DROPOUT") || t.includes("PACKET") || t.includes("COMMUNICATION") },
];

export function toDetectionsByType(buffers: Record<string, ProcessedPacket[]>): CountBar[] {
  const counts = new Map<string, number>(DETECTION_BUCKETS.map((b) => [b.label, 0]));
  for (const b of Object.values(buffers)) {
    for (const p of anomaliesFrom(b)) {
      if (p.root_cause.is_genuine_weather) continue;
      const bucket = DETECTION_BUCKETS.find((d) => d.test(p.root_cause.fault_type));
      if (bucket) counts.set(bucket.label, (counts.get(bucket.label) ?? 0) + 1);
    }
  }
  return DETECTION_BUCKETS.map((b) => ({ label: b.label, value: counts.get(b.label) ?? 0 }));
}

export type Kpi = { label: string; value: string; status: Status; delta?: string };

export function toOverviewKpis(
  stations: StationMeta[],
  latestByStation: Record<string, ProcessedPacket>,
  buffers: Record<string, ProcessedPacket[]>,
  sourceLabel: string,
): Kpi[] {
  const total = stations.length;
  const latests = Object.values(latestByStation);
  const online = latests.length;
  const activeAnoms = latests.filter(
    (p) => p.ensemble.is_anomaly && !p.root_cause.is_genuine_weather,
  );
  const anyCritical = activeAnoms.some((p) => p.ensemble.severity === "CRITICAL");
  const avgHealth =
    latests.length > 0
      ? latests.reduce((s, p) => s + p.sensor_health.overall_health_score, 0) / latests.length
      : 0;
  const detections = Object.values(buffers).reduce((s, b) => s + anomaliesFrom(b).length, 0);
  const totalReadings = Object.values(buffers).reduce((s, b) => s + b.length, 0);

  return [
    {
      label: "Stations online",
      value: `${online} / ${total}`,
      status: online === total && total > 0 ? "normal" : online === 0 ? "critical" : "warning",
      delta: online === total ? "All reporting" : `${total - online} offline`,
    },
    {
      label: "Active anomalies",
      value: `${activeAnoms.length}`,
      status: activeAnoms.length === 0 ? "normal" : anyCritical ? "critical" : "warning",
      delta: anyCritical ? "1+ critical" : activeAnoms.length ? "elevated" : "clear",
    },
    {
      label: "Avg network health",
      value: `${round(avgHealth)}%`,
      status: avgHealth >= 85 ? "normal" : avgHealth >= 70 ? "warning" : "critical",
      delta: "live",
    },
    {
      label: "Detections (session)",
      value: `${detections}`,
      status: "idle",
      delta: "since connect",
    },
    {
      label: "Readings streamed",
      value: `${totalReadings}`,
      status: "idle",
      delta: `${sourceLabel} feed`,
    },
  ];
}

export type HealthPoint = { t: string; health: number };

export function toNetworkHealth(buffer: ProcessedPacket[]): HealthPoint[] {
  return buffer.slice(-24).map((p) => ({
    t: timeHM(p.timestamp),
    health: round(p.sensor_health.overall_health_score, 1),
  }));
}

// Network-wide health trend: mean of every station's overall_health_score at
// each recent time-step. Packets stream in lockstep per tick, so we align by
// position from the newest end and average across all reporting stations.
export function toNetworkHealthAgg(buffers: Record<string, ProcessedPacket[]>): HealthPoint[] {
  const series = Object.values(buffers).filter((b) => b.length > 0);
  if (series.length === 0) return [];
  if (series.length === 1) return toNetworkHealth(series[0]);

  const window = 24;
  const depth = Math.min(window, Math.max(...series.map((b) => b.length)));
  // Longest buffer supplies the time-axis labels.
  const ref = series.reduce((a, b) => (b.length > a.length ? b : a), series[0]);

  const out: HealthPoint[] = [];
  for (let offset = depth - 1; offset >= 0; offset--) {
    let sum = 0;
    let n = 0;
    for (const b of series) {
      const p = b[b.length - 1 - offset];
      if (p) {
        sum += p.sensor_health.overall_health_score;
        n++;
      }
    }
    if (n === 0) continue;
    const refP = ref[ref.length - 1 - offset];
    out.push({ t: refP ? timeHM(refP.timestamp) : "", health: round(sum / n, 1) });
  }
  return out;
}

// ── Maintenance ───────────────────────────────────────────
function weakestSensor(p: ProcessedPacket): { name: string; score: number } {
  const s = p.sensor_health.sensor_scores;
  const entries: { name: string; score: number }[] = [
    { name: "Temperature", score: s.temperature },
    { name: "Barometer", score: s.pressure },
    { name: "Hygrometer", score: s.humidity },
  ];
  return entries.reduce((min, e) => (e.score < min.score ? e : min), entries[0]);
}

function statusFromScore(v: number): Status {
  return v >= 88 ? "normal" : v >= 78 ? "warning" : "critical";
}

export function toMaintenanceKpis(latestByStation: Record<string, ProcessedPacket>): Kpi[] {
  const latests = Object.values(latestByStation);
  let atRisk = 0;
  let driftAlerts = 0;
  let calibrations = 0;
  let rulSum = 0;
  for (const p of latests) {
    const s = p.sensor_health.sensor_scores;
    if (s.temperature < 80) atRisk++;
    if (s.pressure < 80) atRisk++;
    if (s.humidity < 80) atRisk++;
    if ((p.statistical.drift_flags?.length ?? 0) > 0) driftAlerts++;
    if (p.sensor_health.overall_health_score < 85) calibrations++;
    rulSum += p.sensor_health.estimated_rul_days;
  }
  const avgRul = latests.length ? Math.round(rulSum / latests.length) : 0;
  return [
    { label: "Sensors at risk", value: `${atRisk}`, status: atRisk ? "warning" : "normal" },
    { label: "Avg RUL", value: `${avgRul} d`, status: "idle" },
    { label: "Drift alerts", value: `${driftAlerts}`, status: driftAlerts ? "warning" : "normal" },
    { label: "Calibrations due", value: `${calibrations}`, status: calibrations ? "warning" : "idle" },
  ];
}

export type RulRow = { station: string; sensor: string; days: number; status: Status };

export function toRulLeaderboard(latestByStation: Record<string, ProcessedPacket>): RulRow[] {
  return Object.values(latestByStation)
    .map((p) => {
      const w = weakestSensor(p);
      return {
        station: shortName(p.station_name),
        sensor: w.name,
        days: round(p.sensor_health.estimated_rul_days),
        status: statusFromScore(w.score),
      };
    })
    .sort((a, b) => a.days - b.days);
}

export type HealthMatrixRow = { station: string; temp: number; baro: number; hygro: number };

export function toHealthMatrix(latestByStation: Record<string, ProcessedPacket>): HealthMatrixRow[] {
  return Object.values(latestByStation).map((p) => ({
    station: shortName(p.station_name),
    temp: round(p.sensor_health.sensor_scores.temperature),
    baro: round(p.sensor_health.sensor_scores.pressure),
    hygro: round(p.sensor_health.sensor_scores.humidity),
  }));
}

export type ServiceRow = { station: string; sensor: string; action: string; due: string; status: Status };

export function toServiceSchedule(latestByStation: Record<string, ProcessedPacket>): ServiceRow[] {
  return Object.values(latestByStation)
    .filter((p) => p.sensor_health.overall_health_score < 90 || (p.statistical.drift_flags?.length ?? 0) > 0)
    .map((p) => {
      const w = weakestSensor(p);
      return {
        station: shortName(p.station_name),
        sensor: w.name,
        action: w.score < 78 ? "Recalibrate" : "Inspect",
        due: `~${round(p.sensor_health.estimated_rul_days)} d (RUL)`,
        status: statusFromScore(w.score),
      };
    })
    .sort((a, b) => (a.status === "critical" ? -1 : 1));
}

export type AnomalyKpiCard = { label: string; value: string; status: Status };

export function toAnomalyKpis(buffers: Record<string, ProcessedPacket[]>): AnomalyKpiCard[] {
  let critical = 0;
  let high = 0;
  let medium = 0;
  for (const b of Object.values(buffers)) {
    for (const p of anomaliesFrom(b)) {
      if (p.root_cause.is_genuine_weather) continue;
      if (p.ensemble.severity === "CRITICAL") critical++;
      else if (p.ensemble.severity === "HIGH") high++;
      else if (p.ensemble.severity === "MEDIUM") medium++;
    }
  }
  return [
    { label: "Critical", value: `${critical}`, status: "critical" },
    { label: "High", value: `${high}`, status: "warning" },
    { label: "Medium", value: `${medium}`, status: "weather" },
    { label: "Total (session)", value: `${critical + high + medium}`, status: "normal" },
  ];
}

// ── Weather-vs-fault verdict ──────────────────────────────
// The product's core differentiator: is an anomaly a SENSOR FAULT (isolated,
// physically implausible → healed) or GENUINE WEATHER (corroborated across
// stations, physically consistent → left untouched)? These adapters turn a
// ProcessedPacket (live) or an AnomalyRow (mock/offline) into one shared shape
// so the Verdict / Neighbor / Pipeline / Heal components stay dumb & reusable.

export type VerdictKind = "fault" | "weather" | "normal";
export type VerdictEvidence = { label: string; pass: boolean; detail: string };

// The multi-class root-cause diagnosis (backend/app/xai/root_cause.py). This is
// a SEPARATE result from the ensemble's anomaly score: the ensemble answers "is
// this anomalous, and how sure?", the classifier answers "which of the 7 fault/
// weather classes is it, and how sure of THAT?". `confidence` here is the
// classifier's own per-rule confidence (0.88–0.99), distinct from the ensemble
// confidence shown in the verdict header — so both are surfaced, never conflated.
export type RootCause = {
  type: string; // humanized fault_type, e.g. "Sensor spike"
  category: string; // engineering category, spatial suffix split off into `note`
  note?: string; // parenthetical spatial context, e.g. "isolated to this station…"
  confidence?: string; // classifier's own confidence, e.g. "90%" (absent offline)
  isWeather: boolean;
};

export type Verdict = {
  kind: VerdictKind;
  title: string;
  reason: string;
  confidence: string;
  confidenceBand?: string;
  evidence: VerdictEvidence[];
  healed: boolean;
  healedText: string;
  rootCause?: RootCause;
};

const WEATHER_REASON =
  "Coordinated, physically-consistent change shared by neighbouring stations — real weather, not a fault";

function reasonForFault(faultType: string): string {
  const t = faultType.toUpperCase();
  if (t.includes("PHYSIC")) return "Thermodynamically impossible reading that no neighbour shares";
  if (t.includes("SPIKE")) return "Isolated spike beyond the WMO rate limit; neighbours stayed steady";
  if (t.includes("FLATLINE")) return "Reading frozen for many steps — SNR collapse of a stuck sensor";
  if (t.includes("DRIFT")) return "Gradual calibration drift not shared by neighbouring stations";
  if (t.includes("DROPOUT") || t.includes("PACKET") || t.includes("COMMUNICATION"))
    return "Telemetry dropouts and outliers isolated to a single node";
  return "Isolated anomaly not corroborated by neighbouring stations";
}

function ev(label: string, pass: boolean, detail: string): VerdictEvidence {
  return { label, pass, detail };
}

// The classifier appends a parenthetical spatial note to some categories, e.g.
// "Electrical Transient / Sensor Glitch (isolated to this station; other
// reporting stations normal)". Split it so the core category reads cleanly and
// the corroboration note renders as muted secondary text.
function splitCategory(category: string): { core: string; note?: string } {
  const m = category.match(/^(.*?)\s*\(([^)]*)\)\s*$/);
  if (m) return { core: m[1].trim(), note: m[2].trim() };
  return { core: category.trim() };
}

// Classifier confidence is a coarse per-rule value (0.88–0.99), not a calibrated
// probability — shown as a plain integer %, capped under 100 for the same reason
// the ensemble confidence is: a classifier never earns absolute certainty.
function fmtClassifierConf(conf: number | null | undefined): string | undefined {
  if (conf === null || conf === undefined || !Number.isFinite(conf)) return undefined;
  const pct = Math.min(Math.max(conf, 0), 0.999) * 100;
  return `${Math.round(pct)}%`;
}

export function toRootCause(p: ProcessedPacket): RootCause {
  const rc = p.root_cause;
  const { core, note } = splitCategory(rc.fault_category ?? "");
  return {
    type: humanize(rc.fault_type ?? ""),
    category: core,
    note,
    confidence: fmtClassifierConf(rc.confidence),
    isWeather: rc.is_genuine_weather === true,
  };
}

// Offline equivalent from a table row. The mock rows carry a terse category and
// only the ensemble confidence (no separate classifier confidence), so that
// field is intentionally left undefined rather than reusing a value it isn't.
function rootCauseFromRow(row: AnomalyRow): RootCause {
  const { core, note } = splitCategory(row.category ?? "");
  const isWeather = row.verdict === "weather";
  return {
    type: humanize(row.type ?? ""),
    category: core || (isWeather ? "Atmospheric event" : "Sensor fault"),
    note,
    confidence: undefined,
    isWeather,
  };
}

export function toVerdict(p: ProcessedPacket): Verdict {
  const confidence = fmtConfidencePct(p.ensemble.confidence_score);
  const band = confidenceBand(p);
  const rootCause = toRootCause(p);
  const physicsPass = !p.physics.is_physics_violation;
  const spatialPass = p.spatial.is_corroborated_event === true;
  const rateViolation =
    p.root_cause.fault_type.toUpperCase().includes("SPIKE") ||
    (p.physics.violations ?? []).some((v) => /rate|gradient/i.test(v));
  const ratePass = !rateViolation;

  if (!p.ensemble.is_anomaly) {
    return {
      kind: "normal",
      title: "NORMAL",
      reason: "Reading is physically consistent and matches neighbouring stations",
      confidence,
      confidenceBand: band,
      evidence: [
        ev("Physics", true, "Thermodynamically valid"),
        ev("Spatial", true, "Consistent with neighbours"),
        ev("Rate", true, "Within WMO limits"),
      ],
      healed: false,
      healedText: "No healing needed",
      rootCause,
    };
  }

  if (p.root_cause.is_genuine_weather) {
    return {
      kind: "weather",
      title: "GENUINE WEATHER",
      reason: WEATHER_REASON,
      confidence,
      confidenceBand: band,
      evidence: [
        ev("Physics", physicsPass, physicsPass ? "Thermodynamically possible" : "Physics check flagged"),
        ev(
          "Spatial",
          spatialPass,
          spatialPass
            ? `Corroborated by ${p.spatial.other_stations_anomalous}/${p.spatial.other_stations_reporting} neighbours`
            : "Awaiting corroboration",
        ),
        ev("Rate", ratePass, ratePass ? "Within WMO limits" : "Rapid but physical"),
      ],
      healed: false,
      healedText: "Not healed — real signal",
      rootCause,
    };
  }

  const healed = p.imputed.is_imputed;
  const healedTemp = fmt(p.imputed.temperature, 1);
  return {
    kind: "fault",
    title: "SENSOR FAULT",
    reason: reasonForFault(p.root_cause.fault_type),
    confidence,
    confidenceBand: band,
    evidence: [
      ev("Physics", physicsPass, physicsPass ? "Physically possible" : "Thermodynamically impossible"),
      ev("Spatial", spatialPass, spatialPass ? "Neighbours agree" : "Isolated — no neighbour shares it"),
      ev("Rate", ratePass, ratePass ? "Within WMO limits" : "Exceeds WMO gradient limit"),
    ],
    healed,
    healedText: healed
      ? healedTemp === "—"
        ? "Healed (imputed)"
        : `Healed → ${healedTemp} °C`
      : "Flagged — awaiting action",
    rootCause,
  };
}

// Offline/mock equivalent, built from a table row (no live packet available).
export function verdictFromRow(row: AnomalyRow): Verdict {
  const rootCause = rootCauseFromRow(row);
  if (row.verdict === "weather") {
    return {
      kind: "weather",
      title: "GENUINE WEATHER",
      reason: WEATHER_REASON,
      confidence: row.confidence,
      evidence: [
        ev("Physics", true, "Thermodynamically possible"),
        ev("Spatial", true, "Corroborated by neighbours"),
        ev("Rate", true, "Within WMO limits"),
      ],
      healed: false,
      healedText: "Not healed — real signal",
      rootCause,
    };
  }
  const t = row.type.toUpperCase();
  const physicsPass = !t.includes("PHYSIC");
  const ratePass = !t.includes("SPIKE");
  const actuallyHealed = rowWasHealed(row);
  return {
    kind: "fault",
    title: "SENSOR FAULT",
    reason: reasonForFault(row.type),
    confidence: row.confidence,
    evidence: [
      ev("Physics", physicsPass, physicsPass ? "Physically possible" : "Thermodynamically impossible"),
      ev("Spatial", false, "Isolated — no neighbour shares it"),
      ev("Rate", ratePass, ratePass ? "Within WMO limits" : "Exceeds WMO gradient limit"),
    ],
    healed: actuallyHealed,
    healedText: actuallyHealed ? `Healed → ${row.healed}` : "Flagged — awaiting action",
    rootCause,
  };
}

// A row counts as "healed" only if the imputed value actually differs from the
// raw reading. A flatline flagged for inspection (raw == healed) is NOT healed —
// claiming otherwise would misrepresent what the pipeline did.
export function rowWasHealed(row: AnomalyRow): boolean {
  const rawNum = parseFloat(row.raw);
  const fixedNum = parseFloat(row.healed);
  return !Number.isNaN(rawNum) && !Number.isNaN(fixedNum) && Math.abs(rawNum - fixedNum) > 0.05;
}

// ── Neighbor consistency strip ────────────────────────────
export type NeighborTile = {
  id: string;
  name: string;
  value: string;
  status: Status;
  isSubject: boolean;
  ok: boolean;
};

export function toNeighborStrip(
  subjectId: string,
  latestByStation: Record<string, ProcessedPacket>,
): NeighborTile[] {
  const tileFor = (p: ProcessedPacket, isSubject: boolean): NeighborTile => {
    const t = fmt(p.raw.temperature, 1);
    return {
      id: p.station_id,
      name: shortName(p.station_name),
      value: t === "—" ? "—" : `${t} °C`,
      status: packetStatus(p),
      isSubject,
      ok: !p.ensemble.is_anomaly,
    };
  };
  const tiles: NeighborTile[] = [];
  const subject = latestByStation[subjectId];
  if (subject) tiles.push(tileFor(subject, true));
  for (const p of Object.values(latestByStation)) {
    if (p.station_id === subjectId) continue;
    tiles.push(tileFor(p, false));
  }
  return tiles;
}

export function neighborCaption(subject: ProcessedPacket | null): string {
  if (!subject || !subject.ensemble.is_anomaly)
    return "All tracked stations are reporting consistent conditions.";
  if (subject.root_cause.is_genuine_weather)
    return "The change is coordinated across the region — consistent with genuine weather.";
  const others = subject.spatial.other_stations_reporting;
  return `Isolated to this station — ${others} neighbour${others === 1 ? "" : "s"} reading normal, so it's a sensor fault, not weather.`;
}

// ── Decision-pipeline stepper ─────────────────────────────
export type PipelineNode = { label: string; sub: string; emphasis?: boolean };

export function toPipeline(p: ProcessedPacket): PipelineNode[] {
  const isWeather = p.root_cause.is_genuine_weather;
  const healed = p.imputed.is_imputed;
  const healedTemp = fmt(p.imputed.temperature, 1);
  const step5: PipelineNode = isWeather
    ? { label: "Alert", sub: "no heal" }
    : { label: "Heal", sub: healed && healedTemp !== "—" ? `impute ${healedTemp} °C` : "quarantine" };
  return [
    { label: "Detect", sub: fmtConfidenceUnit(p.ensemble.confidence_score) },
    { label: "Classify", sub: p.root_cause.fault_type },
    { label: "Corroborate", sub: isWeather ? "neighbours agree" : "neighbours normal" },
    { label: "Decide", sub: isWeather ? "GENUINE WEATHER" : "SENSOR FAULT", emphasis: true },
    step5,
    { label: "Monitor", sub: "streaming" },
  ];
}

export function pipelineFromRow(row: AnomalyRow): PipelineNode[] {
  const isWeather = row.verdict === "weather";
  const conf = (parseFloat(row.confidence) / 100 || 0).toFixed(2);
  const healStep: PipelineNode = isWeather
    ? { label: "Alert", sub: "no heal" }
    : { label: "Heal", sub: rowWasHealed(row) ? `impute ${row.healed}` : "quarantine" };
  return [
    { label: "Detect", sub: conf },
    { label: "Classify", sub: row.type },
    { label: "Corroborate", sub: isWeather ? "neighbours agree" : "neighbours normal" },
    { label: "Decide", sub: isWeather ? "GENUINE WEATHER" : "SENSOR FAULT", emphasis: true },
    healStep,
    { label: "Monitor", sub: "streaming" },
  ];
}

// ── Heal provenance ───────────────────────────────────────
export type HealProvenance = {
  healed: boolean;
  channel: string;
  raw: string;
  fixed: string;
  method: string;
  confidence: string;
  note: string;
};

export function toHealProvenance(p: ProcessedPacket): HealProvenance {
  const confidence = fmtConfidencePct(p.ensemble.confidence_score);
  const isWeather = p.root_cause.is_genuine_weather;
  const rawT = fmt(p.raw.temperature, 1);
  const rawStr = rawT === "—" ? "—" : `${rawT} °C`;
  if (isWeather || !p.imputed.is_imputed) {
    return {
      healed: false,
      channel: "Temperature",
      raw: rawStr,
      fixed: rawStr,
      method: isWeather ? "No healing — real signal preserved" : "No healing applied",
      confidence,
      note: isWeather ? "Real signal preserved, not overwritten." : "Within limits — no imputation.",
    };
  }
  const fixedT = fmt(p.imputed.temperature, 1);
  return {
    healed: true,
    channel: "Temperature",
    raw: rawStr,
    fixed: fixedT === "—" ? "—" : `${fixedT} °C`,
    method: p.imputed.imputation_reason || "Temporal imputation (recent-window)",
    confidence,
    note: "Original value quarantined, not deleted.",
  };
}

export function healProvenanceFromRow(row: AnomalyRow): HealProvenance {
  const isWeather = row.verdict === "weather";
  const unit = row.healed.replace(/^[\d.\s-]+/, "").trim() || "°C";
  const healed = !isWeather && rowWasHealed(row);
  return {
    healed,
    channel: unit === "hPa" ? "Pressure" : "Temperature",
    raw: `${row.raw} ${unit}`.trim(),
    fixed: row.healed,
    method: isWeather
      ? "No healing — real signal preserved"
      : healed
        ? "Temporal imputation (recent-window)"
        : "Flagged for inspection — no safe imputation",
    confidence: row.confidence,
    note: isWeather
      ? "Real signal preserved, not overwritten."
      : "Original value quarantined, not deleted.",
  };
}

// ── Detector votes (ensemble component scores) ────────────
export type DetectorVote = { label: string; value: number };

export function toDetectorVotes(p: ProcessedPacket): DetectorVote[] {
  const c = p.ensemble.component_scores;
  return [
    { label: "Physics", value: round(c.physics, 2) },
    { label: "Isolation Forest", value: round(c.isolation_forest, 2) },
    { label: "Statistical", value: round(c.statistical, 2) },
    { label: "Autoencoder", value: round(c.autoencoder, 2) },
  ];
}

// ── Overview: fault-vs-weather signature band ─────────────
export type FaultWeatherBand = { faults: number; weather: number; falseAlarms: number };

export function toFaultWeatherBand(buffers: Record<string, ProcessedPacket[]>): FaultWeatherBand {
  let faults = 0;
  let weather = 0;
  for (const b of Object.values(buffers)) {
    for (const p of anomaliesFrom(b)) {
      if (p.root_cause.is_genuine_weather) weather++;
      else faults++;
    }
  }
  return { faults, weather, falseAlarms: 0 };
}
