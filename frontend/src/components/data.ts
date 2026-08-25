export type Status = "normal" | "weather" | "warning" | "critical" | "idle";

export const statusColor: Record<Status, string> = {
  normal: "var(--color-status-normal)",
  weather: "var(--color-status-weather)",
  warning: "var(--color-status-warning)",
  critical: "var(--color-status-critical)",
  idle: "var(--color-mist)",
};

export const statusTint: Record<Status, string> = {
  normal: "rgba(21,166,110,0.10)",
  weather: "rgba(99,102,241,0.10)",
  warning: "rgba(245,158,11,0.12)",
  critical: "rgba(229,72,77,0.10)",
  idle: "rgba(100,116,139,0.08)",
};

export const stations = [
  { id: "AWS_ALPHA_MOUNTAIN", type: "Mountain", name: "Alpha Ridge", temp: 11.8, status: "normal" as Status, label: "Normal" },
  { id: "AWS_BETA_COASTAL", type: "Coastal", name: "Beta Coastline", temp: 27.4, status: "weather" as Status, label: "Weather event" },
  { id: "AWS_GAMMA_URBAN", type: "Urban", name: "Gamma Metropole", temp: 24.9, status: "normal" as Status, label: "Normal", selected: true },
  { id: "AWS_DELTA_DESERT", type: "Desert", name: "Delta Dunes", temp: 41.2, status: "critical" as Status, label: "Fault · Physics violation" },
];

// Time-aligned telemetry. Temperature has a spike anomaly self-healed at steps 11-13.
export const telemetry = Array.from({ length: 24 }, (_, i) => {
  const base = 24.5 + Math.sin(i / 3) * 1.1;
  const spike = i === 11 ? 12.4 : i === 12 ? 14.9 : i === 13 ? 8.2 : 0;
  const raw = +(base + spike + (i % 2 ? 0.2 : -0.15)).toFixed(1);
  const healed = +(base + (i % 2 ? 0.15 : -0.1)).toFixed(1);
  const flagged = spike > 0 ? raw : null;
  const pressure = +(1012 + Math.cos(i / 4) * 1.6).toFixed(1);
  const pressureHealed = i >= 18 && i <= 20 ? +(1012 + Math.cos(i / 4) * 1.6 - 0.4).toFixed(1) : null;
  const humidity = +(58 + Math.sin(i / 2.5) * 4).toFixed(0);
  const dew = +(15.8 + Math.sin(i / 2.5) * 1.4).toFixed(1);
  return {
    t: `${String(6 + Math.floor(i / 2)).padStart(2, "0")}:${i % 2 ? "30" : "00"}`,
    raw,
    truth: healed,
    healed,
    flagged,
    pressure,
    pressureHealed,
    humidity,
    dew,
  };
});

export const metrics = [
  { key: "temp", label: "Temperature", value: "24.9", unit: "°C", color: "var(--color-series-temp)", status: "normal" as Status, spark: [24.2, 24.5, 24.8, 24.6, 24.9, 25.0, 24.9] },
  { key: "pressure", label: "Pressure", value: "1012.4", unit: "hPa", color: "var(--color-series-pressure)", status: "normal" as Status, spark: [1011, 1012, 1013, 1012, 1012, 1013, 1012] },
  { key: "humidity", label: "Humidity", value: "58", unit: "%", color: "var(--color-series-humidity)", status: "normal" as Status, spark: [55, 57, 60, 58, 56, 59, 58] },
  { key: "dew", label: "Dew point", value: "15.8", unit: "°C", color: "var(--color-series-dew)", status: "normal" as Status, spark: [15.2, 15.5, 16.1, 15.8, 15.6, 16.0, 15.8] },
  { key: "vpd", label: "Vapor deficit (VPD)", value: "8.3", unit: "hPa", color: "var(--color-haze)", status: "normal" as Status, spark: [7.9, 8.1, 8.5, 8.3, 8.2, 8.4, 8.3] },
];

export const attribution = [
  { label: "Temperature gradient", value: 42 },
  { label: "Dew-point spread", value: 24 },
  { label: "Pressure tendency", value: 20 },
  { label: "Humidity level", value: 14 },
];

export const healthMeters = [
  { label: "Temperature sensor", value: 94 },
  { label: "Barometer", value: 88 },
  { label: "Hygrometer", value: 91 },
];

export const auditRows = [
  { time: "14:32:07", station: "Delta Dunes", type: "PHYSICS_VIOLATION", category: "Thermodynamic", severity: "Critical" as const, confidence: "98.1%", raw: "54.0", healed: "34.7 °C", explain: "Enthalpy impossible: 54 °C at 96% RH exceeds saturation." },
  { time: "14:30:55", station: "Gamma Metropole", type: "SPIKE", category: "Sensor", severity: "High" as const, confidence: "96.4%", raw: "39.8", healed: "24.9 °C", explain: "ΔT 15.3 °C/min, 5.1× WMO limit; neighbors normal." },
  { time: "14:28:12", station: "Alpha Ridge", type: "FLATLINE", category: "Sensor", severity: "Medium" as const, confidence: "91.2%", raw: "11.8", healed: "11.8 °C", explain: "Identical value 8 steps; SNR collapse — stuck ADC." },
  { time: "14:24:41", station: "Beta Coastline", type: "GENUINE_EXTREME_WEATHER", category: "Weather", severity: "Medium" as const, confidence: "94.7%", raw: "1006.0", healed: "1006.0 hPa", explain: "Coordinated −6 hPa/hr drop across 2 stations; no fault." },
];

export const severityStatus: Record<string, Status> = {
  Critical: "critical",
  High: "warning",
  Medium: "weather",
  Info: "idle",
  Low: "idle",
};

// ── Overview ──────────────────────────────────────────────
export const overviewKpis = [
  { label: "Stations online", value: "4 / 4", status: "normal" as Status, delta: "All reporting" },
  { label: "Active anomalies", value: "2", status: "critical" as Status, delta: "1 critical" },
  { label: "Avg network health", value: "89%", status: "normal" as Status, delta: "+1% vs yesterday" },
  { label: "Detections today", value: "37", status: "idle" as Status, delta: "+8 vs avg" },
  { label: "Mean latency", value: "4.9 ms", status: "normal" as Status, delta: "target < 5 ms" },
];

export const networkHealth24h = Array.from({ length: 24 }, (_, i) => ({
  t: `${String(i).padStart(2, "0")}h`,
  health: +(90 + Math.sin(i / 3.5) * 2.4 + (i > 14 ? -1.2 : 0)).toFixed(1),
}));

export type LiveAlertRow = {
  time: string;
  station: string;
  fault: string;
  severity: "Critical" | "High" | "Medium" | "Info";
  verdict: "fault" | "weather";
  healed: boolean;
};

export const liveAlerts: LiveAlertRow[] = [
  { time: "14:32", station: "Delta Dunes", fault: "Physics violation", severity: "Critical", verdict: "fault", healed: true },
  { time: "14:30", station: "Gamma Metropole", fault: "Spike", severity: "High", verdict: "fault", healed: true },
  { time: "14:28", station: "Alpha Ridge", fault: "Flatline", severity: "Medium", verdict: "fault", healed: false },
  { time: "14:24", station: "Beta Coastline", fault: "Weather event", severity: "Info", verdict: "weather", healed: false },
];

// Overview "fault vs weather · last 24h" signature band. faults + weather sums
// to 37 — matching the "Detections today" KPI. 0 false alarms mirrors the
// Analytics storm false-alarm rate.
export const faultWeatherBand = { faults: 31, weather: 6, falseAlarms: 0 };

export const detectionsByType = [
  { label: "Spike", value: 12 },
  { label: "Physics", value: 9 },
  { label: "Flatline", value: 7 },
  { label: "Drift", value: 5 },
  { label: "Packet loss", value: 4 },
];

// ── Stations table ────────────────────────────────────────
export const stationRows = [
  { id: "AWS_ALPHA_MOUNTAIN", name: "Alpha Ridge", type: "Mountain", loc: "34.13°N, −117.85°E", status: "normal" as Status, label: "Normal", health: 96, rul: "342 d", last: "11.8 °C · 2s", anomalies: 1 },
  { id: "AWS_BETA_COASTAL", name: "Beta Coastline", type: "Coastal", loc: "18.92°N, 72.83°E", status: "weather" as Status, label: "Weather event", health: 90, rul: "281 d", last: "27.4 °C · 3s", anomalies: 0 },
  { id: "AWS_GAMMA_URBAN", name: "Gamma Metropole", type: "Urban", loc: "28.61°N, 77.21°E", status: "normal" as Status, label: "Normal", health: 92, rul: "318 d", last: "24.9 °C · 2s", anomalies: 1 },
  { id: "AWS_DELTA_DESERT", name: "Delta Dunes", type: "Desert", loc: "26.92°N, 70.91°E", status: "critical" as Status, label: "Fault · Physics violation", health: 78, rul: "214 d", last: "41.2 °C · 5s", anomalies: 4 },
];

// ── Anomalies ─────────────────────────────────────────────
export const anomalyKpis = [
  { label: "Critical", value: "3", status: "critical" as Status },
  { label: "High", value: "8", status: "warning" as Status },
  { label: "Medium", value: "12", status: "weather" as Status },
  { label: "Resolved · 24h", value: "19", status: "normal" as Status },
];

export type AnomalyRow = {
  time: string;
  station: string;
  type: string;
  category: string;
  severity: "Critical" | "High" | "Medium" | "Info";
  confidence: string;
  raw: string;
  healed: string;
  state: "Open" | "Acknowledged" | "Resolved";
  verdict: "fault" | "weather";
  explain: string;
};

export const anomalyRows: AnomalyRow[] = [
  { time: "14:32:07", station: "Delta Dunes", type: "PHYSICS_VIOLATION", category: "Thermodynamic", severity: "Critical", confidence: "98.1%", raw: "54.0", healed: "34.7 °C", state: "Open", verdict: "fault", explain: "Reading 54 °C at 96% RH is thermodynamically impossible (exceeds saturation enthalpy). PHYSICS_VIOLATION. Value rejected; imputed 34.7 °C from recent trend." },
  { time: "14:30:55", station: "Gamma Metropole", type: "SPIKE", category: "Sensor", severity: "High", confidence: "96.4%", raw: "39.8", healed: "24.9 °C", state: "Open", verdict: "fault", explain: "Temperature rose 15.3 °C in 60 s — 5.1× the WMO gradient limit. Neighbors normal. Isolated SENSOR SPIKE; self-healed via temporal imputation." },
  { time: "14:28:12", station: "Alpha Ridge", type: "FLATLINE", category: "Sensor", severity: "Medium", confidence: "91.2%", raw: "11.8", healed: "11.8 °C", state: "Acknowledged", verdict: "fault", explain: "Identical value 8 steps; SNR collapse — stuck ADC. Flagged for inspection." },
  { time: "14:24:41", station: "Beta Coastline", type: "GENUINE_EXTREME_WEATHER", category: "Weather", severity: "Info", confidence: "94.7%", raw: "1006.0", healed: "1006.0 hPa", state: "Resolved", verdict: "weather", explain: "Coordinated −6 hPa/hr pressure drop across 2 stations — corroborated GENUINE WEATHER EVENT (convective storm). No fault raised." },
];

export const ensembleWeights = [
  { label: "Physics", value: 0.45, color: "var(--color-azimuth)" },
  { label: "Isolation Forest", value: 0.2, color: "#14b8c4" },
  { label: "Statistical", value: 0.2, color: "var(--color-series-humidity)" },
  { label: "Autoencoder", value: 0.15, color: "var(--color-series-dew)" },
];

// ── Maintenance ───────────────────────────────────────────
export const maintenanceKpis = [
  { label: "Sensors at risk", value: "1", status: "warning" as Status },
  { label: "Avg RUL", value: "289 d", status: "idle" as Status },
  { label: "Drift alerts", value: "2", status: "warning" as Status },
  { label: "Calibrations due", value: "1", status: "idle" as Status },
];

export const rulLeaderboard = [
  { station: "Delta Dunes", sensor: "Hygrometer", days: 168, status: "warning" as Status },
  { station: "Delta Dunes", sensor: "Barometer", days: 214, status: "warning" as Status },
  { station: "Beta Coastline", sensor: "Barometer", days: 258, status: "normal" as Status },
  { station: "Gamma Metropole", sensor: "Barometer", days: 296, status: "normal" as Status },
  { station: "Alpha Ridge", sensor: "Temperature", days: 342, status: "normal" as Status },
];

export const healthMatrix = [
  { station: "Alpha Ridge", temp: 94, baro: 90, hygro: 92 },
  { station: "Beta Coastline", temp: 91, baro: 88, hygro: 93 },
  { station: "Gamma Metropole", temp: 94, baro: 88, hygro: 91 },
  { station: "Delta Dunes", temp: 82, baro: 79, hygro: 74 },
];

export const driftTrend = Array.from({ length: 30 }, (_, i) => ({
  d: `D${i + 1}`,
  delta: +(0.02 * i + Math.sin(i / 5) * 0.05).toFixed(3),
  snr: +(42 - i * 0.18 + Math.sin(i / 4) * 0.6).toFixed(1),
}));

export const serviceSchedule = [
  { station: "Delta Dunes", sensor: "Hygrometer", action: "Recalibrate", due: "in 6 days", status: "warning" as Status },
  { station: "Beta Coastline", sensor: "Barometer", action: "Inspect", due: "in 21 days", status: "idle" as Status },
  { station: "Delta Dunes", sensor: "Barometer", action: "Inspect", due: "in 28 days", status: "idle" as Status },
];

// ── Analytics ─────────────────────────────────────────────
export const analyticsKpis = [
  { label: "Precision", value: "99.1%", status: "normal" as Status },
  { label: "Recall", value: "91.3%", status: "normal" as Status },
  { label: "F1 score", value: "95.1%", status: "normal" as Status },
  { label: "False-alarm on storms", value: "0.0%", status: "normal" as Status },
  { label: "Mean latency", value: "4.9 ms", status: "normal" as Status },
];

export const recallByType = [
  { label: "Physics violation", value: 100 },
  { label: "Flatline", value: 90.0 },
  { label: "Drift", value: 85.8 },
  { label: "Packet loss", value: 85.0 },
  { label: "Spike", value: 80.6 },
];

export const confusionMatrix = [
  { label: "Normal → Normal", value: 8214, good: true },
  { label: "Normal → Anomaly", value: 74, good: false },
  { label: "Anomaly → Normal", value: 39, good: false },
  { label: "Anomaly → Anomaly", value: 412, good: true },
];

export const benchmark = [
  { metric: "Precision", synthetic: 99.1, real: 91.2 },
  { metric: "Recall", synthetic: 91.3, real: 88.8 },
  { metric: "F1", synthetic: 95.1, real: 90.0 },
];

export const latencyHistogram = Array.from({ length: 12 }, (_, i) => {
  const ms = 2.5 + i * 0.5;
  const peak = Math.exp(-((ms - 4.9) ** 2) / 1.2);
  return { ms: ms.toFixed(1), count: Math.round(peak * 320 + 8) };
});

// ── Map ───────────────────────────────────────────────────
export const mapPins = [
  { id: "AWS_ALPHA_MOUNTAIN", name: "Alpha Ridge", type: "Mountain", temp: "11.8 °C", status: "normal" as Status, label: "Normal", x: 16, y: 34 },
  { id: "AWS_BETA_COASTAL", name: "Beta Coastline", type: "Coastal", temp: "27.4 °C", status: "weather" as Status, label: "Weather event", x: 71, y: 72 },
  { id: "AWS_GAMMA_URBAN", name: "Gamma Metropole", type: "Urban", temp: "24.9 °C", status: "normal" as Status, label: "Normal", x: 74, y: 46 },
  { id: "AWS_DELTA_DESERT", name: "Delta Dunes", type: "Desert", temp: "41.2 °C", status: "critical" as Status, label: "Fault", x: 67, y: 52 },
];

// ── Settings ──────────────────────────────────────────────
export const edgeDevices = [
  { id: "EDGE-ALPHA-01", fw: "1.4.2", ram: "3.1 KB", sync: "12 s ago", state: "Online", status: "normal" as Status },
  { id: "EDGE-BETA-02", fw: "1.4.2", ram: "3.0 KB", sync: "31 s ago", state: "Online", status: "normal" as Status },
  { id: "EDGE-GAMMA-03", fw: "1.4.2", ram: "3.1 KB", sync: "9 s ago", state: "Online", status: "normal" as Status },
  { id: "EDGE-DELTA-04", fw: "1.4.1", ram: "3.0 KB", sync: "4 m ago", state: "Update available", status: "warning" as Status },
];
