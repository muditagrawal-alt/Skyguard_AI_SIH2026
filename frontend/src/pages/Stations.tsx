import { useState } from "react";
import { useNavigate } from "react-router";
import { Search, ChevronRight, MoreHorizontal } from "lucide-react";
import { Card, StatusPill, StatusSpine } from "../components/primitives";
import { stationRows as mockStationRows } from "../components/data";
import { useStream } from "../lib/StreamProvider";
import { toStationRow, type StationRow } from "../lib/adapters";

const typeFilters = ["All", "Mountain", "Coastal", "Urban", "Desert"];

export default function Stations() {
  const [type, setType] = useState("All");
  const [query, setQuery] = useState("");
  const navigate = useNavigate();

  const { backendOnline, stations, latestByStation, buffers } = useStream();
  const live = backendOnline;

  const allRows: StationRow[] = live
    ? stations.map((m) => {
        const l = latestByStation[m.station_id] ?? null;
        const count = (buffers[m.station_id] ?? []).filter(
          (p) => p.ensemble.is_anomaly && !p.root_cause.is_genuine_weather,
        ).length;
        return toStationRow(m, l, count);
      })
    : mockStationRows;

  const rows = allRows.filter(
    (r) =>
      (type === "All" || r.type === type) &&
      r.name.toLowerCase().includes(query.toLowerCase()),
  );

  const latests = Object.values(latestByStation);
  const online = latests.length;
  const faults = latests.filter((p) => p.ensemble.is_anomaly && !p.root_cause.is_genuine_weather).length;
  const avgHealth =
    online > 0
      ? Math.round(latests.reduce((s, p) => s + p.sensor_health.overall_health_score, 0) / online)
      : 0;

  const summary = live
    ? [
        { label: "Total", value: stations.length },
        { label: "Online", value: online },
        { label: "With active faults", value: faults },
        { label: "Avg health", value: online > 0 ? `${avgHealth}%` : "—" },
      ]
    : [
        { label: "Total", value: 4 },
        { label: "Online", value: 4 },
        { label: "With active faults", value: 1 },
        { label: "Avg health", value: "89%" },
      ];

  return (
    <div className="flex flex-col gap-5">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {summary.map((s) => (
          <div key={s.label} className="rounded-xl border border-mist bg-white px-4 py-3">
            <div className="text-xs text-haze">{s.label}</div>
            <div className="mt-1 font-display text-xl font-semibold text-ink">{s.value}</div>
          </div>
        ))}
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2 rounded-xl border border-mist bg-white px-3 py-2">
          <Search size={15} className="text-haze" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search stations"
            className="w-44 bg-transparent text-sm text-ink outline-none placeholder:text-haze"
          />
        </div>
        <div className="flex flex-wrap gap-1.5">
          {typeFilters.map((t) => (
            <button
              key={t}
              onClick={() => setType(t)}
              className={`rounded-full px-3 py-1.5 text-xs font-medium transition-colors ${
                type === t ? "bg-azimuth text-white" : "border border-mist bg-white text-haze hover:text-ink"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      <Card status="idle" className="p-2">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[920px] border-collapse text-left text-sm">
            <thead>
              <tr className="border-b border-mist text-[11px] font-semibold uppercase tracking-wider text-haze">
                <th className="px-4 py-3 font-semibold">Station</th>
                <th className="px-4 py-3 font-semibold">Type</th>
                <th className="px-4 py-3 font-semibold">Location</th>
                <th className="px-4 py-3 font-semibold">Status</th>
                <th className="px-4 py-3 font-semibold">Health</th>
                <th className="px-4 py-3 font-semibold">RUL</th>
                <th className="px-4 py-3 font-semibold">Last reading</th>
                <th className="px-4 py-3 font-semibold">Anomalies</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr
                  key={r.id}
                  onClick={() => navigate(`/stations/${r.id}`)}
                  className="group cursor-pointer border-b border-mist/70 transition-colors hover:bg-stratus/60"
                >
                  <td className="relative px-4 py-3">
                    <StatusSpine status={r.status} />
                    <span className="font-medium text-ink">{r.name}</span>
                  </td>
                  <td className="px-4 py-3 text-haze">{r.type}</td>
                  <td className="px-4 py-3 font-mono text-[12px] text-haze">{r.loc}</td>
                  <td className="px-4 py-3"><StatusPill status={r.status}>{r.label}</StatusPill></td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <div className="h-1.5 w-16 overflow-hidden rounded-full bg-mist">
                        <div className="h-full rounded-full" style={{ width: `${r.health}%`, background: r.health >= 85 ? "var(--color-status-normal)" : "var(--color-status-warning)" }} />
                      </div>
                      <span className="font-mono text-xs text-ink">{r.health}%</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 font-mono text-[13px] text-ink">{r.rul}</td>
                  <td className="px-4 py-3 font-mono text-[12px] text-haze">{r.last}</td>
                  <td className="px-4 py-3 font-mono text-[13px] text-ink">{r.anomalies}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-1 text-haze">
                      <ChevronRight size={16} className="opacity-0 transition-opacity group-hover:opacity-100" />
                      <MoreHorizontal size={16} />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
