import { Play, Square, Trash2, ChevronDown } from "lucide-react";
import { Card, StatusPill } from "./primitives";
import type { Status } from "./data";
import { useStream } from "../lib/StreamProvider";
import { packetStatus, packetLabel } from "../lib/adapters";

function lastUpdate(iso: string | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? "—" : d.toLocaleTimeString("en-GB", { hour12: false });
}

export default function ControlStrip() {
  const {
    stations,
    selectedStationId,
    selectedStation,
    selectedLatest,
    dataSource,
    rateHz,
    running,
    connected,
    backendOnline,
    setStation,
    setDataSource,
    setRate,
    start,
    stop,
    clear,
  } = useStream();

  const realAvailable = !!selectedStation?.has_real_data;

  let status: Status = "idle";
  let statusText = "Offline · demo data";
  if (backendOnline) {
    if (!running) {
      status = "idle";
      statusText = "Stream stopped";
    } else if (!connected) {
      status = "warning";
      statusText = "Connecting…";
    } else if (selectedLatest) {
      status = packetStatus(selectedLatest);
      statusText = packetLabel(selectedLatest);
    } else {
      status = "warning";
      statusText = "Waiting for data…";
    }
  }

  return (
    <Card status={status === "idle" ? "normal" : status} className="p-4">
      <div className="flex flex-wrap items-center gap-x-5 gap-y-3">
        <label className="flex flex-col gap-1">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-haze">Station</span>
          <div className="relative">
            <select
              value={selectedStationId}
              onChange={(e) => setStation(e.target.value)}
              className="w-full appearance-none rounded-xl border border-mist bg-white px-3 py-2 pr-9 text-sm font-medium text-ink transition-colors hover:border-azimuth/40 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-azimuth"
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
        </label>

        <div className="flex flex-col gap-1">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-haze">Data source</span>
          <div className="flex rounded-xl border border-mist bg-white p-1">
            {(
              [
                ["real", "Real NOAA history"],
                ["synthetic", "Synthetic generator"],
              ] as const
            ).map(([key, label]) => {
              const disabled = key === "real" && !realAvailable;
              return (
                <button
                  key={key}
                  onClick={() => setDataSource(key)}
                  disabled={disabled}
                  title={disabled ? "No real NOAA history available for this station" : undefined}
                  className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
                    dataSource === key
                      ? "bg-azimuth text-white shadow-card"
                      : disabled
                        ? "cursor-not-allowed text-mist"
                        : "text-haze hover:text-ink"
                  }`}
                >
                  {label}
                </button>
              );
            })}
          </div>
        </div>

        <div className="flex flex-col gap-1">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-haze">Stream</span>
          <div className="flex items-center gap-2">
            <button
              onClick={start}
              disabled={running}
              className="flex items-center gap-1.5 rounded-xl bg-azimuth px-3 py-2 text-sm font-semibold text-white shadow-card transition-transform hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-45 disabled:hover:translate-y-0"
            >
              <Play size={14} strokeWidth={2} /> Start stream
            </button>
            <button
              onClick={stop}
              disabled={!running}
              className="flex items-center gap-1.5 rounded-xl bg-azimuth/10 px-3 py-2 text-sm font-semibold text-azimuth transition-colors hover:bg-azimuth/15 disabled:cursor-not-allowed disabled:opacity-45"
            >
              <Square size={13} strokeWidth={2} /> Stop
            </button>
            <button
              onClick={clear}
              className="flex items-center gap-1.5 rounded-xl px-2.5 py-2 text-sm font-medium text-haze transition-colors hover:bg-mist/50 hover:text-ink"
            >
              <Trash2 size={14} strokeWidth={1.5} /> Clear buffer
            </button>
          </div>
        </div>

        <label className="flex w-44 flex-col gap-1">
          <span className="flex items-center justify-between text-[11px] font-semibold uppercase tracking-wider text-haze">
            Stream rate <span className="font-mono normal-case text-ink">{rateHz.toFixed(1)} /s</span>
          </span>
          <input
            type="range"
            min={0.2}
            max={5}
            step={0.2}
            value={rateHz}
            onChange={(e) => setRate(+e.target.value)}
            className="mt-2 w-full accent-azimuth"
          />
        </label>

        <div className="ml-auto flex flex-col items-end gap-1.5">
          <StatusPill status={status}>{statusText}</StatusPill>
          <span className="font-mono text-xs text-haze">
            {backendOnline && selectedLatest
              ? `Last update ${lastUpdate(selectedLatest.timestamp)}`
              : backendOnline
                ? "Awaiting backend stream"
                : "Backend not connected"}
          </span>
        </div>
      </div>
    </Card>
  );
}
