import { useState } from "react";
import { Card, StatusPill } from "../components/primitives";
import { ensembleWeights, edgeDevices } from "../components/data";
import { useStream } from "../lib/StreamProvider";

const tabs = ["Detection", "Alerts", "Stations", "Edge devices"];

const sources: { key: "real" | "synthetic"; label: string }[] = [
  { key: "real", label: "Real NOAA history" },
  { key: "synthetic", label: "Synthetic generator" },
];

function FieldRow({ label, value, unit }: { label: string; value: string; unit: string }) {
  return (
    <label className="flex items-center justify-between gap-4 py-2">
      <span className="text-sm text-ink">{label}</span>
      <span className="flex items-center gap-2">
        <input
          defaultValue={value}
          className="w-20 rounded-lg border border-mist bg-white px-2.5 py-1.5 text-right font-mono text-[13px] text-ink outline-none focus:border-azimuth"
        />
        <span className="w-16 font-mono text-xs text-haze">{unit}</span>
      </span>
    </label>
  );
}

export default function Settings() {
  const [tab, setTab] = useState("Detection");
  const [weights, setWeights] = useState(ensembleWeights.map((w) => w.value));
  const total = weights.reduce((a, b) => a + b, 0);
  const [note, setNote] = useState("");

  // The data-source toggle is a real control: it switches the shared live stream
  // between recorded NOAA history and the synthetic fault generator for all
  // stations. The other fields (QC limits, weights, thresholds) are session-only
  // — the backend exposes no settings-write endpoint.
  const { dataSource, setDataSource, anyRealDataAvailable } = useStream();

  const resetDefaults = () => {
    setWeights(ensembleWeights.map((w) => w.value));
    setNote("Reset to default detection settings.");
  };
  const saveChanges = () =>
    setNote("Detection settings applied to this session — no server-side persistence endpoint.");

  return (
    <div className="flex flex-col gap-5 pb-24">
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

      {tab === "Edge devices" ? (
        <Card status="idle" className="p-2">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[560px] text-left text-sm">
              <thead>
                <tr className="border-b border-mist text-[11px] font-semibold uppercase tracking-wider text-haze">
                  <th className="px-4 py-3 font-semibold">Device</th>
                  <th className="px-4 py-3 font-semibold">Firmware</th>
                  <th className="px-4 py-3 font-semibold">RAM</th>
                  <th className="px-4 py-3 font-semibold">Last sync</th>
                  <th className="px-4 py-3 font-semibold">State</th>
                </tr>
              </thead>
              <tbody>
                {edgeDevices.map((d) => (
                  <tr key={d.id} className="border-b border-mist/70">
                    <td className="px-4 py-3 font-mono text-[13px] text-ink">{d.id}</td>
                    <td className="px-4 py-3 font-mono text-[12px] text-haze">{d.fw}</td>
                    <td className="px-4 py-3 font-mono text-[12px] text-haze">{d.ram}</td>
                    <td className="px-4 py-3 font-mono text-[12px] text-haze">{d.sync}</td>
                    <td className="px-4 py-3"><StatusPill status={d.status}>{d.state}</StatusPill></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
          <Card status="idle" className="p-6">
            <div className="text-sm font-semibold text-ink">WMO quality-control limits</div>
            <div className="mt-3 divide-y divide-mist">
              <FieldRow label="Max ΔT" value="3.0" unit="°C/min" />
              <FieldRow label="Max ΔP" value="2.0" unit="hPa/min" />
              <FieldRow label="Max ΔRH" value="15.0" unit="%/min" />
            </div>
            <p className="mt-3 rounded-lg bg-stratus px-3 py-2 font-mono text-[11px] text-haze">
              Clausius-Clapeyron: T ≥ Td (enforced)
            </p>
          </Card>

          <Card status="idle" className="p-6">
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold text-ink">Ensemble weights</span>
              <span className={`font-mono text-xs font-medium ${Math.abs(total - 1) < 0.001 ? "text-[var(--color-status-normal)]" : "text-[var(--color-status-warning)]"}`}>
                Total {total.toFixed(2)} {Math.abs(total - 1) < 0.001 ? "✓" : "⚠"}
              </span>
            </div>
            <div className="mt-4 space-y-3.5">
              {ensembleWeights.map((w, i) => (
                <div key={w.label}>
                  <div className="mb-1 flex items-center justify-between text-xs">
                    <span className="text-ink">{w.label}</span>
                    <span className="font-mono text-haze">{weights[i].toFixed(2)}</span>
                  </div>
                  <input
                    type="range"
                    min={0}
                    max={1}
                    step={0.05}
                    value={weights[i]}
                    onChange={(e) => setWeights((prev) => prev.map((v, j) => (j === i ? +e.target.value : v)))}
                    className="w-full accent-azimuth"
                  />
                </div>
              ))}
            </div>
          </Card>

          <Card status="idle" className="p-6">
            <div className="text-sm font-semibold text-ink">Severity thresholds</div>
            <div className="mt-3 divide-y divide-mist">
              <FieldRow label="Low" value="0.35" unit="score" />
              <FieldRow label="Medium" value="0.60" unit="score" />
              <FieldRow label="High" value="0.80" unit="score" />
              <FieldRow label="Critical" value="0.90" unit="score" />
            </div>
            <div className="mt-4 h-2 w-full rounded-full" style={{ background: "linear-gradient(90deg, var(--color-status-normal), var(--color-status-weather), var(--color-status-warning), var(--color-status-critical))" }} />
          </Card>

          <Card status="idle" className="p-6">
            <div className="text-sm font-semibold text-ink">Data source</div>
            <div className="mt-3 flex rounded-xl border border-mist bg-white p-1">
              {sources.map((s) => {
                const activeSrc = dataSource === s.key;
                const disabled = s.key === "real" && !anyRealDataAvailable;
                return (
                  <button
                    key={s.key}
                    onClick={() => setDataSource(s.key)}
                    disabled={disabled}
                    title={disabled ? "No station has recorded NOAA history available" : undefined}
                    className={`flex-1 rounded-lg px-3 py-2 text-xs font-medium transition-colors ${
                      activeSrc ? "bg-azimuth text-white shadow-card" : "text-haze hover:text-ink"
                    } ${disabled ? "cursor-not-allowed opacity-40" : ""}`}
                  >
                    {s.label}
                  </button>
                );
              })}
            </div>
            <p className="mt-3 text-xs leading-relaxed text-haze">
              Switches the live stream between recorded NOAA history and the synthetic fault
              generator. Applies immediately to every station.
              {!anyRealDataAvailable && " Real history is unavailable in this deployment."}
            </p>
          </Card>
        </div>
      )}

      <div className="fixed bottom-0 right-0 flex w-full items-center justify-end gap-3 border-t border-mist bg-white/90 px-7 py-3 backdrop-blur lg:w-[calc(100%-248px)]">
        {note && <span className="mr-auto text-xs text-haze">{note}</span>}
        <button
          onClick={resetDefaults}
          className="rounded-xl px-4 py-2 text-sm font-medium text-haze transition-colors hover:bg-mist/50 hover:text-ink"
        >
          Reset to defaults
        </button>
        <button
          onClick={saveChanges}
          className="rounded-xl bg-azimuth px-4 py-2 text-sm font-semibold text-white shadow-card transition-transform hover:-translate-y-0.5"
        >
          Save changes
        </button>
      </div>
    </div>
  );
}
