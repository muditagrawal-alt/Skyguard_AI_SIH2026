import { Thermometer, Gauge, Droplets, Wind, Activity, ShieldCheck } from "lucide-react";
import { Card, StatusPill } from "./primitives";
import { metrics as mockMetrics } from "./data";
import type { Status } from "./data";
import { useStream } from "../lib/StreamProvider";
import { toMetrics, packetStatus, packetLabel } from "../lib/adapters";

const icons: Record<string, typeof Thermometer> = {
  temp: Thermometer,
  pressure: Gauge,
  humidity: Droplets,
  dew: Wind,
  vpd: Activity,
};

function Sparkline({ points, color }: { points: number[]; color: string }) {
  if (!points || points.length === 0) {
    return <div className="h-[22px]" aria-hidden />;
  }
  const pts = points.length === 1 ? [points[0], points[0]] : points;
  const min = Math.min(...pts);
  const max = Math.max(...pts);
  const range = max - min || 1;
  const w = 72;
  const h = 22;
  const d = pts
    .map((p, i) => {
      const x = (i / (pts.length - 1)) * w;
      const y = h - ((p - min) / range) * h;
      return `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
  return (
    <svg width={w} height={h} className="overflow-visible">
      <path d={d} fill="none" stroke={color} strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" opacity={0.7} />
    </svg>
  );
}

export default function StatCards() {
  const { backendOnline, selectedLatest, selectedBuffer } = useStream();

  const live = backendOnline && selectedLatest;
  const metrics = live ? toMetrics(selectedLatest, selectedBuffer) : mockMetrics;

  const anomalyStatus: Status = live ? packetStatus(selectedLatest) : "normal";
  const anomalyLabel = live ? packetLabel(selectedLatest) : "Normal stream";

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 xl:grid-cols-6">
      {metrics.map((m) => {
        const Icon = icons[m.key];
        return (
          <Card key={m.key} status={m.status} className="p-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-haze">{m.label}</span>
              {Icon ? <Icon size={15} strokeWidth={1.5} style={{ color: m.color }} /> : null}
            </div>
            <div className="mt-2 flex items-baseline gap-1">
              <span className="font-display text-[26px] font-semibold leading-none text-ink">{m.value}</span>
              <span className="text-xs text-haze">{m.unit}</span>
            </div>
            <div className="mt-2">
              <Sparkline points={m.spark} color={m.color} />
            </div>
          </Card>
        );
      })}
      <Card status={anomalyStatus === "idle" ? "normal" : anomalyStatus} className="flex flex-col p-4">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-haze">Anomaly state</span>
          <ShieldCheck size={15} strokeWidth={1.5} className="text-[var(--color-status-normal)]" />
        </div>
        <div className="mt-auto pt-4">
          <StatusPill status={anomalyStatus}>{anomalyLabel}</StatusPill>
        </div>
      </Card>
    </div>
  );
}
