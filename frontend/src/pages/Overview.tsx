import { Link } from "react-router";
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, ResponsiveContainer } from "recharts";
import { Card, KpiCard, StatusPill, StatusSpine, SectionTitle } from "../components/primitives";
import { VerdictTag } from "../components/verdict";
import {
  overviewKpis as mockKpis,
  stations as mockStations,
  networkHealth24h as mockHealth,
  liveAlerts as mockAlerts,
  detectionsByType as mockDetections,
  faultWeatherBand as mockBand,
  severityStatus,
  mapPins as mockPins,
  statusColor,
  type Status,
} from "../components/data";
import { useStream } from "../lib/StreamProvider";
import {
  shortName,
  packetStatus,
  packetLabel,
  toOverviewKpis,
  toNetworkHealthAgg,
  toLiveAlerts,
  toDetectionsByType,
  toFaultWeatherBand,
  toMapPin,
} from "../lib/adapters";

const axisStyle = { fontSize: 10, fontFamily: "var(--font-mono)", fill: "#94a3b8" };

type NetCard = { id: string; type: string; name: string; temp: string; status: Status; label: string };

export default function Overview() {
  const { backendOnline, stations, latestByStation, buffers, dataSource } = useStream();
  const live = backendOnline;
  const sourceLabel = dataSource === "real" ? "Real NOAA" : "Synthetic";

  const kpis = live ? toOverviewKpis(stations, latestByStation, buffers, sourceLabel) : mockKpis;

  const netCards: NetCard[] = live
    ? stations.map((m) => {
        const l = latestByStation[m.station_id] ?? null;
        return {
          id: m.station_id,
          type: m.station_type,
          name: shortName(m.name),
          temp: l && l.raw.temperature != null ? l.raw.temperature.toFixed(1) : "—",
          status: l ? packetStatus(l) : "idle",
          label: l ? packetLabel(l) : "Offline",
        };
      })
    : mockStations.map((s) => ({
        id: s.id,
        type: s.type,
        name: s.name,
        temp: String(s.temp),
        status: s.status,
        label: s.label,
      }));

  const health = live ? toNetworkHealthAgg(buffers) : mockHealth;
  const detections = live ? toDetectionsByType(buffers) : mockDetections;
  const alerts = live ? toLiveAlerts(buffers) : mockAlerts;
  const band = live ? toFaultWeatherBand(buffers) : mockBand;
  const bandTotal = band.faults + band.weather;
  const faultPct = bandTotal > 0 ? (band.faults / bandTotal) * 100 : 0;
  const weatherPct = bandTotal > 0 ? (band.weather / bandTotal) * 100 : 0;
  const bandFigures = [
    { value: band.faults, label: "sensor faults — isolated & healed", color: "var(--color-status-critical)" },
    { value: band.weather, label: "genuine weather events — corroborated, untouched", color: "var(--color-status-weather)" },
    { value: band.falseAlarms, label: "false alarms", color: "var(--color-status-normal)" },
  ];
  const pins = live
    ? stations.map((m) => toMapPin(m, latestByStation[m.station_id] ?? null))
    : mockPins;

  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-5">
        {kpis.map((k) => (
          <KpiCard key={k.label} {...k} />
        ))}
      </div>

      <Card status="idle" className="p-5">
        <SectionTitle
          title="Fault vs weather · last 24h"
          caption="Every anomaly is classified before any healing — sensor faults are isolated and repaired, genuine weather is corroborated and left untouched."
        />
        <div className="mt-4 flex h-2.5 w-full overflow-hidden rounded-full bg-mist">
          <div style={{ width: `${faultPct}%`, background: "var(--color-status-critical)" }} />
          <div style={{ width: `${weatherPct}%`, background: "var(--color-status-weather)" }} />
        </div>
        <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
          {bandFigures.map((f) => (
            <div key={f.label} className="relative overflow-hidden rounded-xl border border-mist bg-white p-3">
              <span aria-hidden className="absolute inset-y-0 left-0 w-[3px]" style={{ background: f.color }} />
              <div className="font-display text-2xl font-semibold leading-none" style={{ color: f.color }}>
                {f.value}
              </div>
              <div className="mt-1 text-xs leading-snug text-haze">{f.label}</div>
            </div>
          ))}
        </div>
      </Card>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <div className="flex flex-col gap-4 xl:col-span-2">
          <Card status="idle" className="p-6">
            <SectionTitle title="Network status" />
            <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
              {netCards.map((s) => (
                <div
                  key={s.id}
                  className="relative overflow-hidden rounded-xl border border-mist bg-white p-4"
                >
                  <StatusSpine status={s.status} />
                  <div className="text-[11px] font-semibold uppercase tracking-wider text-haze">{s.type}</div>
                  <div className="mt-0.5 text-sm font-semibold text-ink">{s.name}</div>
                  <div className="mt-2 flex items-center justify-between">
                    <span className="tnum font-display text-[26px] font-semibold leading-none text-ink">
                      {s.temp}
                      <span className="ml-1 text-xs font-normal text-haze">°C</span>
                    </span>
                    <StatusPill status={s.status}>{s.label}</StatusPill>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-5">
              <div className="mb-1 flex items-center justify-between text-xs font-medium text-haze">
                <span>Network health</span>
                <span className="font-mono text-[11px]">
                  {live ? "network mean · recent" : "demo · 24h"}
                </span>
              </div>
              <ResponsiveContainer width="100%" height={140}>
                <AreaChart data={health} margin={{ top: 8, right: 8, bottom: 0, left: -20 }}>
                  <defs>
                    <linearGradient id="healthFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="var(--color-status-normal)" stopOpacity={0.25} />
                      <stop offset="100%" stopColor="var(--color-status-normal)" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke="#eef2f7" vertical={false} />
                  <XAxis dataKey="t" tick={axisStyle} tickLine={false} axisLine={{ stroke: "#e6ebf2" }} interval={3} />
                  <YAxis tick={axisStyle} tickLine={false} axisLine={false} width={40} domain={["auto", "auto"]} />
                  <Area dataKey="health" stroke="var(--color-status-normal)" strokeWidth={2} fill="url(#healthFill)" isAnimationActive={false} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Card status="idle" className="p-5">
              <div className="text-sm font-semibold text-ink">Detections by fault type</div>
              <ResponsiveContainer width="100%" height={160}>
                <BarChart data={detections} layout="vertical" margin={{ top: 8, right: 12, bottom: 0, left: 8 }}>
                  <XAxis type="number" hide />
                  <YAxis type="category" dataKey="label" tick={{ fontSize: 11, fill: "#64748b" }} tickLine={false} axisLine={false} width={72} />
                  <Bar dataKey="value" radius={[0, 6, 6, 0]} fill="var(--color-azimuth)" barSize={14} isAnimationActive={false} />
                </BarChart>
              </ResponsiveContainer>
            </Card>

            <Card status="idle" className="flex flex-col p-5">
              <div className="flex items-center justify-between">
                <div className="text-sm font-semibold text-ink">Network map</div>
                <Link to="/map" className="text-xs font-medium text-azimuth hover:opacity-70">Open map</Link>
              </div>
              <div className="relative mt-3 flex-1 overflow-hidden rounded-xl bg-stratus" style={{ minHeight: 140 }}>
                {pins.map((p) => (
                  <span
                    key={p.id}
                    className="absolute h-3 w-3 -translate-x-1/2 -translate-y-1/2 rounded-full ring-4"
                    style={{
                      left: `${p.x}%`,
                      top: `${p.y}%`,
                      background: statusColor[p.status],
                      boxShadow: `0 0 0 4px color-mix(in srgb, ${statusColor[p.status]} 20%, transparent)`,
                    }}
                    title={p.name}
                  />
                ))}
              </div>
            </Card>
          </div>
        </div>

        <Card status="idle" className="flex flex-col p-6">
          <SectionTitle
            title="Live alerts"
            right={<Link to="/anomalies" className="text-xs font-medium text-azimuth hover:opacity-70">View all</Link>}
          />
          <div className="mt-4 flex flex-col gap-2">
            {alerts.length === 0 ? (
              <div className="rounded-xl border border-dashed border-mist bg-white px-4 py-8 text-center text-sm text-haze">
                No active alerts — all stations nominal.
              </div>
            ) : (
              alerts.map((a, i) => {
                const st = severityStatus[a.severity];
                return (
                  <div key={i} className="relative overflow-hidden rounded-xl border border-mist bg-white py-2.5 pl-4 pr-3">
                    <StatusSpine status={st} />
                    <div className="flex items-center justify-between gap-2">
                      <div className="min-w-0">
                        <div className="truncate text-sm font-medium text-ink">{a.station}</div>
                        <div className="font-mono text-[11px] text-haze">{a.time} · {a.fault}</div>
                      </div>
                      <div className="flex shrink-0 flex-col items-end gap-1">
                        <VerdictTag kind={a.verdict} healed={a.healed} />
                        <StatusPill status={st}>{a.severity}</StatusPill>
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
