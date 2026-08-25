import { useEffect, useState } from "react";
import { Link, useParams } from "react-router";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer, Legend } from "recharts";
import { ChevronLeft } from "lucide-react";
import { Card, StatusPill, StatusSpine, SectionTitle } from "../components/primitives";
import HealthRadar from "../components/HealthRadar";
import {
  telemetry as mockTelemetry,
  anomalyRows as mockAnomalies,
  severityStatus,
  type Status,
} from "../components/data";
import { useStream } from "../lib/StreamProvider";
import {
  packetStatus,
  packetLabel,
  toMetrics,
  toTelemetryRows,
  toAuditRows,
} from "../lib/adapters";

const tabs = ["Overview", "Telemetry", "Health", "Anomalies", "Config"];
const axisStyle = { fontSize: 10, fontFamily: "var(--font-mono)", fill: "#94a3b8" };

const MOCK_METRICS = [
  { key: "temp", label: "Temperature", value: "24.9", unit: "°C" },
  { key: "pressure", label: "Pressure", value: "1012.4", unit: "hPa" },
  { key: "humidity", label: "Humidity", value: "58", unit: "%" },
  { key: "dew", label: "Dew point", value: "15.8", unit: "°C" },
  { key: "vpd", label: "VPD", value: "8.3", unit: "hPa" },
];

function fmtLoc(lat: number, lon: number): string {
  const ns = lat >= 0 ? "N" : "S";
  const ew = lon >= 0 ? "E" : "W";
  return `${Math.abs(lat).toFixed(2)}°${ns}, ${Math.abs(lon).toFixed(2)}°${ew}`;
}

export default function StationDetail() {
  const { id } = useParams();
  const [tab, setTab] = useState("Overview");
  const { stations, latestByStation, buffers, backendOnline, setStation } = useStream();

  // Point the shared stream at this station so the embedded HealthRadar and all
  // derived views reflect the station the user is looking at.
  useEffect(() => {
    if (id) setStation(id);
  }, [id, setStation]);

  const meta = stations.find((s) => s.station_id === id) ?? stations[0];
  const latest = id ? (latestByStation[id] ?? null) : null;
  const buffer = id ? (buffers[id] ?? []) : [];
  const live = backendOnline && latest;

  const headerStatus: Status = latest ? packetStatus(latest) : backendOnline ? "idle" : "normal";
  const headerLabel = latest ? packetLabel(latest) : backendOnline ? "Awaiting data" : "Demo data";

  const metrics = live ? toMetrics(latest, buffer) : MOCK_METRICS;
  const telemetry = live && buffer.length > 0 ? toTelemetryRows(buffer) : mockTelemetry;
  const recent = live ? toAuditRows(buffer, 3) : mockAnomalies.slice(0, 3);

  return (
    <div className="flex flex-col gap-5">
      <Link to="/stations" className="flex w-fit items-center gap-1 text-sm font-medium text-azimuth hover:opacity-70">
        <ChevronLeft size={16} /> Stations
      </Link>

      <Card status={headerStatus === "idle" ? "normal" : headerStatus} className="p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2.5">
              <h2 className="font-display text-[22px] font-semibold text-ink">{meta.name}</h2>
              <span className="rounded-full bg-stratus px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-haze">{meta.station_type}</span>
              <StatusPill status={headerStatus}>{headerLabel}</StatusPill>
            </div>
            <p className="mt-1.5 font-mono text-[12px] text-haze">
              {meta.station_id} · {fmtLoc(meta.latitude, meta.longitude)} · Elevation {meta.elevation_m} m · Baseline {meta.base_temp_c} °C, {meta.base_pressure_hpa} hPa, {meta.base_humidity_pct}% RH
            </p>
          </div>
          <div className="flex gap-2">
            <Link to="/live" className="rounded-xl bg-azimuth px-3.5 py-2 text-sm font-semibold text-white shadow-card transition-transform hover:-translate-y-0.5">View live</Link>
          </div>
        </div>
      </Card>

      <div className="flex gap-1 border-b border-mist">
        {tabs.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`relative px-3.5 py-2.5 text-sm font-medium transition-colors ${
              tab === t ? "text-azimuth" : "text-haze hover:text-ink"
            }`}
          >
            {t}
            {tab === t && <span className="absolute inset-x-2 -bottom-px h-0.5 rounded-full bg-azimuth" />}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 xl:grid-cols-5">
        {metrics.map((m) => (
          <Card key={m.key} status="normal" className="p-4">
            <div className="text-xs text-haze">{m.label}</div>
            <div className="mt-2 font-display text-[24px] font-semibold leading-none text-ink">
              {m.value}<span className="ml-1 text-xs font-normal text-haze">{m.unit}</span>
            </div>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <Card status="idle" className="p-6 xl:col-span-2">
          <SectionTitle title={live ? "Recent telemetry" : "24h telemetry"} />
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={telemetry} margin={{ top: 12, right: 8, bottom: 0, left: -16 }}>
              <CartesianGrid stroke="#eef2f7" vertical={false} />
              <XAxis dataKey="t" tick={axisStyle} tickLine={false} axisLine={{ stroke: "#e6ebf2" }} interval={3} />
              <YAxis tick={axisStyle} tickLine={false} axisLine={false} width={40} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Line name="Temperature" dataKey="healed" stroke="var(--color-series-temp)" strokeWidth={2} dot={false} isAnimationActive={false} />
              <Line name="Pressure" dataKey="pressure" stroke="var(--color-series-pressure)" strokeWidth={2} dot={false} isAnimationActive={false} />
              <Line name="Humidity" dataKey="humidity" stroke="var(--color-series-humidity)" strokeWidth={2} dot={false} isAnimationActive={false} />
            </LineChart>
          </ResponsiveContainer>
        </Card>
        <HealthRadar />
      </div>

      <Card status="idle" className="p-6">
        <SectionTitle title="Recent anomalies at this station" />
        <div className="mt-4 overflow-x-auto">
          <table className="w-full min-w-[560px] text-left text-sm">
            <thead>
              <tr className="border-b border-mist text-[11px] font-semibold uppercase tracking-wider text-haze">
                <th className="py-2.5 pr-4 font-semibold">Time</th>
                <th className="py-2.5 pr-4 font-semibold">Fault type</th>
                <th className="py-2.5 pr-4 font-semibold">Severity</th>
                <th className="py-2.5 font-semibold">Confidence</th>
              </tr>
            </thead>
            <tbody>
              {recent.length === 0 ? (
                <tr>
                  <td colSpan={4} className="py-8 text-center text-sm text-haze">
                    No anomalies recorded at this station yet.
                  </td>
                </tr>
              ) : (
                recent.map((r, i) => (
                  <tr key={i} className="border-b border-mist/70">
                    <td className="relative py-3 pr-4">
                      <StatusSpine status={severityStatus[r.severity]} />
                      <span className="font-mono text-[13px] text-ink">{r.time}</span>
                    </td>
                    <td className="py-3 pr-4 font-mono text-[12px] text-haze">{r.type}</td>
                    <td className="py-3 pr-4"><StatusPill status={severityStatus[r.severity]}>{r.severity}</StatusPill></td>
                    <td className="py-3 font-mono text-[13px] text-ink">{r.confidence}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
