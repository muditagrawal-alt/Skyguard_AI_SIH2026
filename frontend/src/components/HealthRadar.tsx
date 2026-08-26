import { Card, Skeleton } from "./primitives";
import { healthMeters as mockHealthMeters } from "./data";
import { useStream } from "../lib/StreamProvider";
import { healthGauge, rulText, toHealthMeters } from "../lib/adapters";

function Gauge({ value }: { value: number }) {
  const r = 78;
  const cx = 100;
  const cy = 100;
  // Semicircle from 180° to 0°
  const angle = Math.PI * (1 - value / 100);
  const ex = cx + r * Math.cos(angle);
  const ey = cy - r * Math.sin(angle);
  const color =
    value > 75 ? "var(--color-status-normal)" : value >= 50 ? "var(--color-status-warning)" : "var(--color-status-critical)";
  const label = value > 75 ? "Healthy" : value >= 50 ? "Degrading" : "At risk";
  return (
    <svg viewBox="0 0 200 116" className="w-full max-w-[220px]">
      <path d="M22 100 A78 78 0 0 1 178 100" fill="none" stroke="#eef2f7" strokeWidth={12} strokeLinecap="round" />
      <path
        d={`M22 100 A78 78 0 0 1 ${ex.toFixed(1)} ${ey.toFixed(1)}`}
        fill="none"
        stroke={color}
        strokeWidth={12}
        strokeLinecap="round"
      />
      <text x={cx} y={90} textAnchor="middle" className="font-display" fontSize={30} fontWeight={600} fill="var(--color-ink)" style={{ fontVariantNumeric: "tabular-nums" }}>
        {value}
      </text>
      <text x={cx} y={108} textAnchor="middle" fontSize={11} fontFamily="var(--font-mono)" fill="var(--color-haze)">
        / 100 · {label}
      </text>
    </svg>
  );
}

export default function HealthRadar() {
  const { backendOnline, selectedLatest } = useStream();
  const live = backendOnline && selectedLatest;
  const connecting = backendOnline && !selectedLatest;

  const gauge = live ? healthGauge(selectedLatest) : 92;
  const rul = live ? rulText(selectedLatest) : "318 days";
  const meters = live ? toHealthMeters(selectedLatest) : mockHealthMeters;
  const advisory = live
    ? selectedLatest.sensor_health.advisory || "All sensors within nominal SNR; no calibration drift detected."
    : "All sensors within nominal SNR; no calibration drift detected.";

  return (
    <Card status="normal" className="flex h-full flex-col p-6">
      <h2 className="font-display text-[18px] font-semibold leading-6 text-ink">Sensor health radar</h2>
      <div className="mt-4 flex justify-center">
        {connecting ? (
          <Skeleton className="h-[116px] w-[220px] max-w-full rounded-xl" />
        ) : (
          <Gauge value={gauge} />
        )}
      </div>
      <div className="mt-3 text-center">
        <div className="text-sm text-ink">
          Estimated remaining useful life:{" "}
          {connecting ? (
            <Skeleton className="inline-block h-4 w-16 align-middle" />
          ) : (
            <span className="font-display font-semibold">{rul}</span>
          )}
        </div>
        {connecting ? (
          <div className="mx-auto mt-2 flex max-w-[240px] flex-col items-center gap-1.5">
            <Skeleton className="h-2.5 w-full" />
            <Skeleton className="h-2.5 w-2/3" />
          </div>
        ) : (
          <p className="mt-1.5 text-xs leading-relaxed text-haze">{advisory}</p>
        )}
      </div>
      <div className="mt-5 space-y-3.5">
        {meters.map((m) => {
          const barColor =
            m.value > 75
              ? "var(--color-status-normal)"
              : m.value >= 50
                ? "var(--color-status-warning)"
                : "var(--color-status-critical)";
          return (
            <div key={m.label}>
              <div className="mb-1 flex items-center justify-between text-xs">
                <span className="text-ink">{m.label}</span>
                {connecting ? (
                  <Skeleton className="inline-block h-3 w-9 align-middle" />
                ) : (
                  <span className="font-mono text-haze">{m.value}%</span>
                )}
              </div>
              <div className="h-1.5 w-full overflow-hidden rounded-full bg-mist">
                {!connecting && (
                  <div className="h-full rounded-full" style={{ width: `${m.value}%`, background: barColor }} />
                )}
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
