import { LineChart, Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer } from "recharts";
import { Card, KpiCard, StatusPill, SectionTitle } from "../components/primitives";
import {
  maintenanceKpis as mockMaintenanceKpis,
  rulLeaderboard as mockRulLeaderboard,
  healthMatrix as mockHealthMatrix,
  driftTrend,
  serviceSchedule as mockServiceSchedule,
  statusColor,
} from "../components/data";
import { useStream } from "../lib/StreamProvider";
import {
  toMaintenanceKpis,
  toRulLeaderboard,
  toHealthMatrix,
  toServiceSchedule,
} from "../lib/adapters";

const axisStyle = { fontSize: 10, fontFamily: "var(--font-mono)", fill: "#94a3b8" };

function healthColor(v: number) {
  return v >= 88 ? "var(--color-status-normal)" : v >= 78 ? "var(--color-status-warning)" : "var(--color-status-critical)";
}

export default function Maintenance() {
  const { backendOnline, latestByStation } = useStream();
  // Maintenance views summarise the *current* health of each station's sensors,
  // so they read the latest packet per station. The 30-day drift / SNR trends
  // have no per-session equivalent, so they stay on the illustrative mock data.
  const hasData = backendOnline && Object.keys(latestByStation).length > 0;

  const maintenanceKpis = hasData ? toMaintenanceKpis(latestByStation) : mockMaintenanceKpis;
  const rulLeaderboard = hasData ? toRulLeaderboard(latestByStation) : mockRulLeaderboard;
  const healthMatrix = hasData ? toHealthMatrix(latestByStation) : mockHealthMatrix;
  const serviceSchedule = hasData ? toServiceSchedule(latestByStation) : mockServiceSchedule;

  // Guard against an empty leaderboard (Math.max() → -Infinity) and zero-day rows.
  const maxDays = Math.max(1, ...rulLeaderboard.map((r) => r.days));
  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {maintenanceKpis.map((k) => (
          <KpiCard key={k.label} {...k} />
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <Card status="idle" className="p-6">
          <SectionTitle title="Remaining useful life — leaderboard" caption="Shortest first" />
          <div className="mt-4 space-y-3">
            {rulLeaderboard.map((r) => (
              <div key={r.station + r.sensor} className="flex items-center gap-3">
                <div className="w-44 shrink-0 text-sm">
                  <span className="text-ink">{r.station}</span>
                  <span className="text-haze"> · {r.sensor}</span>
                </div>
                <div className="h-5 flex-1 overflow-hidden rounded-md bg-mist/60">
                  <div className="h-full rounded-md" style={{ width: `${(r.days / maxDays) * 100}%`, background: statusColor[r.status] }} />
                </div>
                <span className="w-12 text-right font-mono text-[13px] text-ink">{r.days} d</span>
              </div>
            ))}
          </div>
        </Card>

        <Card status="idle" className="p-6">
          <SectionTitle title="Sensor health matrix" />
          <div className="mt-4 overflow-x-auto">
            <table className="w-full min-w-[420px] text-left text-sm">
              <thead>
                <tr className="text-[11px] font-semibold uppercase tracking-wider text-haze">
                  <th className="py-2 pr-4 font-semibold">Station</th>
                  <th className="py-2 px-2 text-center font-semibold">Temperature</th>
                  <th className="py-2 px-2 text-center font-semibold">Barometer</th>
                  <th className="py-2 px-2 text-center font-semibold">Hygrometer</th>
                </tr>
              </thead>
              <tbody>
                {healthMatrix.map((m) => (
                  <tr key={m.station}>
                    <td className="py-1.5 pr-4 text-ink">{m.station}</td>
                    {[m.temp, m.baro, m.hygro].map((v, i) => (
                      <td key={i} className="px-1.5 py-1.5">
                        <div
                          className="flex h-9 items-center justify-center rounded-lg font-mono text-[13px] font-medium"
                          style={{ background: `color-mix(in srgb, ${healthColor(v)} 16%, white)`, color: healthColor(v) }}
                        >
                          {v}%
                        </div>
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <Card status="warning" className="p-6">
          <SectionTitle title="Cumulative drift (°C)" caption="Delta Dunes · 30 days" />
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={driftTrend} margin={{ top: 10, right: 8, bottom: 0, left: -18 }}>
              <CartesianGrid stroke="#eef2f7" vertical={false} />
              <XAxis dataKey="d" tick={axisStyle} tickLine={false} axisLine={{ stroke: "#e6ebf2" }} interval={5} />
              <YAxis tick={axisStyle} tickLine={false} axisLine={false} width={40} />
              <Line dataKey="delta" stroke="var(--color-status-warning)" strokeWidth={2} dot={false} isAnimationActive={false} />
            </LineChart>
          </ResponsiveContainer>
        </Card>
        <Card status="idle" className="p-6">
          <SectionTitle title="Signal-to-noise ratio (dB)" caption="30 days" />
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={driftTrend} margin={{ top: 10, right: 8, bottom: 0, left: -18 }}>
              <CartesianGrid stroke="#eef2f7" vertical={false} />
              <XAxis dataKey="d" tick={axisStyle} tickLine={false} axisLine={{ stroke: "#e6ebf2" }} interval={5} />
              <YAxis tick={axisStyle} tickLine={false} axisLine={false} width={40} />
              <Line dataKey="snr" stroke="var(--color-series-pressure)" strokeWidth={2} dot={false} isAnimationActive={false} />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      </div>

      <Card status="idle" className="p-6">
        <SectionTitle title="Service schedule" />
        <div className="mt-4 overflow-x-auto">
          <table className="w-full min-w-[520px] text-left text-sm">
            <thead>
              <tr className="border-b border-mist text-[11px] font-semibold uppercase tracking-wider text-haze">
                <th className="py-2.5 pr-4 font-semibold">Station</th>
                <th className="py-2.5 pr-4 font-semibold">Sensor</th>
                <th className="py-2.5 pr-4 font-semibold">Recommended action</th>
                <th className="py-2.5 font-semibold">Due</th>
              </tr>
            </thead>
            <tbody>
              {serviceSchedule.length === 0 ? (
                <tr>
                  <td colSpan={4} className="py-8 text-center text-sm text-haze">
                    All sensors within healthy limits — no service actions recommended.
                  </td>
                </tr>
              ) : (
                serviceSchedule.map((s, i) => (
                  <tr key={i} className="border-b border-mist/70">
                    <td className="py-3 pr-4 text-ink">{s.station}</td>
                    <td className="py-3 pr-4 text-haze">{s.sensor}</td>
                    <td className="py-3 pr-4"><StatusPill status={s.status}>{s.action}</StatusPill></td>
                    <td className="py-3 font-mono text-[13px] text-ink">{s.due}</td>
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
