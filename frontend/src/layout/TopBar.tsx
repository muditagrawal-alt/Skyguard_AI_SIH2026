import { ChevronDown, Globe, Bell } from "lucide-react";
import { Link } from "react-router";
import { useStream } from "../lib/StreamProvider";

export default function TopBar({ title }: { title: string }) {
  const { backendOnline, connected, dataSource, latestByStation, stations, selectedStationId, setStation } =
    useStream();

  const sourceLabel = !backendOnline ? "Demo data" : dataSource === "real" ? "Real NOAA" : "Synthetic";
  const sourceOnline = backendOnline && connected;

  // Live "notification" count = stations whose latest reading is an active
  // (non-weather) fault right now.
  const activeFaults = Object.values(latestByStation).filter(
    (p) => p.ensemble.is_anomaly && !p.root_cause.is_genuine_weather,
  ).length;

  return (
    <header className="flex h-16 shrink-0 items-center justify-between gap-4 border-b border-mist bg-white px-7">
      <h1 className="font-display text-[22px] font-semibold text-ink">{title}</h1>

      <div className="flex items-center gap-2">
        {/* Global station picker — stays in sync with the Live Monitor controls */}
        <div className="relative hidden md:block">
          <select
            aria-label="Active station"
            value={selectedStationId}
            onChange={(e) => setStation(e.target.value)}
            className="appearance-none rounded-xl border border-mist bg-white py-1.5 pl-3 pr-9 text-sm font-medium text-ink transition-colors hover:border-azimuth/40 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-azimuth"
          >
            {stations.map((s) => (
              <option key={s.station_id} value={s.station_id}>
                {s.name}
              </option>
            ))}
          </select>
          <ChevronDown
            size={15}
            className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-haze"
          />
        </div>

        <span
          className="hidden items-center gap-1.5 rounded-xl bg-stratus px-3 py-1.5 text-xs font-medium text-haze lg:flex"
          title={sourceOnline ? "Backend connected" : "Backend offline — showing demo data"}
        >
          <Globe
            size={13}
            strokeWidth={1.5}
            style={{ color: sourceOnline ? "var(--color-status-normal)" : "var(--color-haze)" }}
          />
          {sourceLabel}
        </span>

        <div className="mx-1 hidden h-6 w-px bg-mist sm:block" />

        <Link
          to="/anomalies"
          aria-label={activeFaults > 0 ? `${activeFaults} active faults — view anomalies` : "View anomalies"}
          title="View anomalies"
          className="relative flex h-9 w-9 items-center justify-center rounded-xl text-haze transition-colors hover:bg-mist/50 hover:text-ink"
        >
          <Bell size={17} strokeWidth={1.5} />
          {activeFaults > 0 && (
            <span className="absolute right-1.5 top-1.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-[var(--color-status-critical)] px-1 text-[10px] font-semibold text-white">
              {activeFaults}
            </span>
          )}
        </Link>
      </div>
    </header>
  );
}
