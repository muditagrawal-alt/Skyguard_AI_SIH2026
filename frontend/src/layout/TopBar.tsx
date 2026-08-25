import { ChevronDown, Globe, Search, Bell, HelpCircle } from "lucide-react";
import { useStream } from "../lib/StreamProvider";

export default function TopBar({ title }: { title: string }) {
  const { backendOnline, connected, dataSource, latestByStation } = useStream();

  const sourceLabel = !backendOnline
    ? "Demo data"
    : dataSource === "real"
      ? "Real NOAA"
      : "Synthetic";
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
        <button className="hidden items-center gap-1.5 rounded-xl border border-mist bg-white px-3 py-1.5 text-sm font-medium text-ink transition-colors hover:border-azimuth/40 md:flex">
          All stations <ChevronDown size={15} className="text-haze" />
        </button>
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
        <button className="hidden items-center gap-1.5 rounded-xl border border-mist bg-white px-3 py-1.5 text-sm font-medium text-ink transition-colors hover:border-azimuth/40 sm:flex">
          Last 24h <ChevronDown size={15} className="text-haze" />
        </button>

        <div className="mx-1 hidden h-6 w-px bg-mist sm:block" />

        <button className="flex h-9 w-9 items-center justify-center rounded-xl text-haze transition-colors hover:bg-mist/50 hover:text-ink">
          <Search size={17} strokeWidth={1.5} />
        </button>
        <button className="relative flex h-9 w-9 items-center justify-center rounded-xl text-haze transition-colors hover:bg-mist/50 hover:text-ink">
          <Bell size={17} strokeWidth={1.5} />
          {activeFaults > 0 && (
            <span className="absolute right-1.5 top-1.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-[var(--color-status-critical)] px-1 text-[10px] font-semibold text-white">
              {activeFaults}
            </span>
          )}
        </button>
        <button className="flex h-9 w-9 items-center justify-center rounded-xl text-haze transition-colors hover:bg-mist/50 hover:text-ink">
          <HelpCircle size={17} strokeWidth={1.5} />
        </button>
      </div>
    </header>
  );
}
