import { useState } from "react";
import { Card, StatusPill, StatusSpine } from "../components/primitives";
import { mapPins as mockPins, statusColor, type Status } from "../components/data";
import { useStream } from "../lib/StreamProvider";
import { toMapPin } from "../lib/adapters";
import type { ProcessedPacket } from "../lib/types";

const legend: { label: string; status: Status }[] = [
  { label: "Normal", status: "normal" },
  { label: "Weather", status: "weather" },
  { label: "Warning", status: "warning" },
  { label: "Fault", status: "critical" },
];

const MOCK_CALLOUT = {
  status: "weather" as Status,
  text: "2 nearby stations reporting a coordinated pressure drop — corroborated as a genuine regional weather event, not isolated sensor faults.",
};

// Summarise the network's spatial consistency from the latest packet per station:
// a corroborated event points to genuine regional weather, isolated anomalies to
// sensor faults, and a quiet network to consistent conditions everywhere.
function spatialCallout(latests: ProcessedPacket[]): { status: Status; text: string } {
  const corroborated = latests.find((p) => p.ensemble.is_anomaly && p.spatial?.is_corroborated_event);
  if (corroborated) {
    const s = corroborated.spatial;
    return {
      status: "weather",
      text: `${s.other_stations_anomalous} of ${s.other_stations_reporting} nearby stations report coordinated conditions — corroborated as a genuine regional weather event, not isolated sensor faults.`,
    };
  }
  const isolated = latests.find((p) => p.ensemble.is_anomaly && !p.root_cause.is_genuine_weather);
  if (isolated) {
    return {
      status: "warning",
      text: "Active anomalies are isolated to individual stations — neighbours report normal conditions, consistent with sensor faults rather than a regional event.",
    };
  }
  return {
    status: "normal",
    text: "All stations reporting consistent regional conditions — no coordinated anomalies or isolated faults detected.",
  };
}

export default function MapView() {
  const { backendOnline, stations, latestByStation, selectedStationId, setStation } = useStream();
  const live = backendOnline;

  const pins = live
    ? stations.map((m) => toMapPin(m, latestByStation[m.station_id] ?? null))
    : mockPins;

  const [active, setActive] = useState<string | null>(selectedStationId);
  const callout = live ? spatialCallout(Object.values(latestByStation)) : MOCK_CALLOUT;

  // Corroboration overlay geometry. The fault pin gets an "isolated" halo (no
  // neighbour shares its signal); the weather pin gets an arc linking it to the
  // wider network (its shift is coordinated → genuine weather, not a fault).
  const faultPin = pins.find((p) => p.status === "critical") ?? null;
  const weatherPin = pins.find((p) => p.status === "weather") ?? null;
  const avg = (ns: number[]) => (ns.length ? ns.reduce((a, b) => a + b, 0) / ns.length : 0);
  const arcNeighbours = weatherPin ? pins.filter((p) => p.id !== weatherPin.id && p.status !== "critical") : [];
  const arcTarget = weatherPin
    ? arcNeighbours.length
      ? { x: avg(arcNeighbours.map((p) => p.x)), y: avg(arcNeighbours.map((p) => p.y)) }
      : { x: 48, y: 42 }
    : null;
  let arcPath = "";
  let arcLabel = { x: 0, y: 0 };
  if (weatherPin && arcTarget) {
    const wx = weatherPin.x, wy = weatherPin.y, tx = arcTarget.x, ty = arcTarget.y;
    const mx = (wx + tx) / 2, my = (wy + ty) / 2;
    const dx = tx - wx, dy = ty - wy;
    const len = Math.hypot(dx, dy) || 1;
    const bow = 15;
    const cx = mx + (-dy / len) * bow, cy = my + (dx / len) * bow;
    arcPath = `M ${wx} ${wy} Q ${cx} ${cy} ${tx} ${ty}`;
    arcLabel = { x: 0.25 * wx + 0.5 * cx + 0.25 * tx, y: 0.25 * wy + 0.5 * cy + 0.25 * ty };
  }

  const select = (id: string) => {
    setActive(id);
    if (live) setStation(id);
  };

  return (
    <div className="grid grid-cols-1 gap-5 xl:grid-cols-[320px_1fr]">
      <Card status="idle" className="flex flex-col p-5">
        <div className="text-sm font-semibold text-ink">Stations</div>
        <div className="mt-3 flex flex-wrap gap-1.5">
          {legend.map((l) => (
            <span key={l.label} className="flex items-center gap-1.5 rounded-full bg-stratus px-2.5 py-1 text-[11px] font-medium text-haze">
              <span className="h-2 w-2 rounded-full" style={{ background: statusColor[l.status] }} />
              {l.label}
            </span>
          ))}
        </div>
        <div className="mt-4 flex flex-col gap-2">
          {pins.map((p) => (
            <button
              key={p.id}
              onClick={() => select(p.id)}
              className={`relative overflow-hidden rounded-xl border py-2.5 pl-4 pr-3 text-left transition-colors ${
                active === p.id ? "border-azimuth/40 bg-azimuth/[0.04]" : "border-mist bg-white hover:bg-stratus/60"
              }`}
            >
              <StatusSpine status={p.status} />
              <div className="flex items-center justify-between gap-2">
                <div>
                  <div className="text-sm font-medium text-ink">{p.name}</div>
                  <div className="text-[11px] text-haze">{p.type} · {p.temp}</div>
                </div>
                <StatusPill status={p.status}>{p.label}</StatusPill>
              </div>
            </button>
          ))}
        </div>
      </Card>

      <Card status="idle" className="relative overflow-hidden p-0">
        <div
          className="relative h-full min-h-[520px] w-full"
          style={{
            background:
              "radial-gradient(circle at 30% 30%, #eef3fa, #f6f8fb 60%)",
            backgroundColor: "#f6f8fb",
          }}
        >
          {/* faint graticule */}
          <div
            className="absolute inset-0 opacity-40"
            style={{
              backgroundImage:
                "linear-gradient(#e6ebf2 1px, transparent 1px), linear-gradient(90deg, #e6ebf2 1px, transparent 1px)",
              backgroundSize: "56px 56px",
            }}
          />

          {/* weather corroboration arc — links the weather pin to the network */}
          {weatherPin && arcPath && (
            <svg
              className="pointer-events-none absolute inset-0 h-full w-full"
              viewBox="0 0 100 100"
              preserveAspectRatio="none"
              aria-hidden
            >
              <path d={arcPath} fill="none" stroke="var(--color-status-weather)" strokeWidth={8} strokeLinecap="round" opacity={0.1} vectorEffect="non-scaling-stroke" />
              <path className="arc-flow" d={arcPath} fill="none" stroke="var(--color-status-weather)" strokeWidth={1.6} strokeLinecap="round" strokeDasharray="5 5" opacity={0.85} vectorEffect="non-scaling-stroke" />
            </svg>
          )}

          {pins.map((p) => {
            const isActive = active === p.id;
            const isFault = p.status === "critical";
            return (
              <button
                key={p.id}
                onClick={() => select(p.id)}
                className="absolute -translate-x-1/2 -translate-y-1/2"
                style={{ left: `${p.x}%`, top: `${p.y}%` }}
              >
                <span className="relative flex items-center justify-center">
                  {isFault && (
                    <>
                      <span
                        className="live-dot absolute h-6 w-6 rounded-full"
                        style={{ color: statusColor[p.status], opacity: 0.4 }}
                      />
                      <span
                        className="iso-ring pointer-events-none absolute left-1/2 top-1/2 h-11 w-11 rounded-full border-2 border-dashed"
                        style={{ borderColor: statusColor[p.status], opacity: 0.55 }}
                      />
                      <span
                        className="iso-halo pointer-events-none absolute left-1/2 top-1/2 h-11 w-11 rounded-full border-2 border-dashed"
                        style={{ borderColor: statusColor[p.status] }}
                      />
                    </>
                  )}
                  <span
                    className="relative h-3.5 w-3.5 rounded-full ring-4"
                    style={{
                      background: statusColor[p.status],
                      boxShadow: `0 0 0 4px color-mix(in srgb, ${statusColor[p.status]} 22%, transparent)`,
                    }}
                  />
                </span>
                <span
                  className={`absolute left-1/2 top-4 -translate-x-1/2 whitespace-nowrap rounded-md px-1.5 py-0.5 text-[10px] font-medium ${
                    isActive ? "bg-white text-ink shadow-card" : "text-haze"
                  }`}
                >
                  {p.name}
                </span>
              </button>
            );
          })}

          {/* fault: isolated-signal caption */}
          {faultPin && (
            <div
              className="pointer-events-none absolute z-10"
              style={{ left: `${faultPin.x}%`, top: `${faultPin.y}%`, transform: "translate(-50%, calc(-100% - 30px))", maxWidth: 200 }}
            >
              <div className="rounded-xl border bg-white/95 px-2.5 py-1.5 shadow-card backdrop-blur-sm" style={{ borderColor: "color-mix(in srgb, var(--color-status-critical) 40%, transparent)" }}>
                <div className="flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wide" style={{ color: "var(--color-status-critical)" }}>
                  <span className="h-1.5 w-1.5 rounded-full" style={{ background: "var(--color-status-critical)" }} />
                  Isolated
                </div>
                <div className="mt-0.5 text-[10.5px] leading-snug text-haze">No neighbour shares this signal → sensor fault.</div>
              </div>
            </div>
          )}

          {/* weather: coordinated-channels arc label */}
          {weatherPin && arcPath && (
            <div
              className="pointer-events-none absolute z-10"
              style={{ left: `${arcLabel.x}%`, top: `${arcLabel.y}%`, transform: "translate(-50%, -50%)", maxWidth: 210 }}
            >
              <div className="rounded-xl border bg-white/95 px-2.5 py-1.5 shadow-card backdrop-blur-sm" style={{ borderColor: "color-mix(in srgb, var(--color-status-weather) 40%, transparent)" }}>
                <div className="flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wide" style={{ color: "var(--color-status-weather)" }}>
                  <span className="h-1.5 w-1.5 rounded-full" style={{ background: "var(--color-status-weather)" }} />
                  Coordinated P↓ / T↓ / RH↑
                </div>
                <div className="mt-0.5 text-[10.5px] leading-snug text-haze">Physically consistent across channels → genuine weather.</div>
              </div>
            </div>
          )}

          <div className="absolute bottom-5 right-5 max-w-[260px] rounded-2xl border border-mist bg-white p-4 shadow-card">
            <div className="text-[11px] font-semibold uppercase tracking-wider" style={{ color: statusColor[callout.status] }}>Spatial consistency</div>
            <p className="mt-1.5 text-[12px] leading-relaxed text-ink">
              {callout.text}
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
}
