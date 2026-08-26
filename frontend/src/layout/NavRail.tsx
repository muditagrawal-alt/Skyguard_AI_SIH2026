import { NavLink } from "react-router";
import {
  LayoutGrid,
  Activity,
  RadioTower,
  TriangleAlert,
  Wrench,
  ChartLine,
  Map as MapIcon,
  Settings as SettingsIcon,
  Radar,
} from "lucide-react";
import { useStream } from "../lib/StreamProvider";

const items = [
  { to: "/overview", label: "Overview", icon: LayoutGrid },
  { to: "/live", label: "Live Monitor", icon: Activity },
  { to: "/stations", label: "Stations", icon: RadioTower },
  { to: "/anomalies", label: "Anomalies", icon: TriangleAlert },
  { to: "/maintenance", label: "Maintenance", icon: Wrench },
  { to: "/analytics", label: "Analytics", icon: ChartLine },
  { to: "/map", label: "Map", icon: MapIcon },
  { to: "/settings", label: "Settings", icon: SettingsIcon },
];

function systemStatus(
  backendOnline: boolean,
  connected: boolean,
  latests: { ensemble: { is_anomaly: boolean; severity: string }; root_cause: { is_genuine_weather: boolean } }[],
): { color: string; text: string } {
  if (!backendOnline) return { color: "var(--color-haze)", text: "Demo mode" };
  const faults = latests.filter((p) => p.ensemble.is_anomaly && !p.root_cause.is_genuine_weather);
  if (faults.some((p) => p.ensemble.severity === "CRITICAL"))
    return { color: "var(--color-status-critical)", text: "Faults detected" };
  if (faults.length > 0) return { color: "var(--color-status-warning)", text: "Anomalies active" };
  if (!connected) return { color: "var(--color-status-warning)", text: "Connecting…" };
  return { color: "var(--color-status-normal)", text: "System healthy" };
}

export default function NavRail() {
  const { backendOnline, connected, latestByStation } = useStream();
  const sys = systemStatus(backendOnline, connected, Object.values(latestByStation));

  return (
    <aside className="flex w-[248px] shrink-0 flex-col border-r border-mist bg-frost px-4 py-5">
      <div className="flex items-center gap-2.5 px-2">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-azimuth text-white shadow-card">
          <Radar size={19} strokeWidth={1.5} />
        </div>
        <span className="font-display text-[17px] font-semibold text-ink">SkyGuard AI</span>
      </div>

      <nav className="mt-7 flex flex-col gap-1">
        {items.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors ${
                isActive
                  ? "bg-azimuth/[0.08] text-azimuth"
                  : "text-haze hover:bg-mist/50 hover:text-ink"
              }`
            }
          >
            {({ isActive }: { isActive: boolean }) => (
              <>
                {isActive && (
                  <span className="absolute left-0 top-1.5 bottom-1.5 w-[3px] rounded-full bg-azimuth" />
                )}
                <Icon size={17} strokeWidth={1.5} />
                {label}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="mt-auto space-y-3 pt-4">
        <div
          className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium"
          style={{ background: `color-mix(in srgb, ${sys.color} 12%, transparent)`, color: sys.color }}
        >
          <span className="h-1.5 w-1.5 rounded-full" style={{ background: sys.color }} />
          {sys.text}
        </div>
        <div className="flex items-center gap-2.5 rounded-xl border border-mist bg-white px-3 py-2">
          <Radar size={15} strokeWidth={1.5} className="shrink-0 text-azimuth" />
          <div className="text-[11px] leading-tight">
            <div className="font-semibold text-ink">Smart India Hackathon 2026</div>
            <div className="font-mono text-haze">Problem Statement 26073</div>
          </div>
        </div>
      </div>
    </aside>
  );
}
