import type { ReactNode } from "react";
import { type Status, statusColor } from "./data";

export function StatusSpine({ status }: { status: Status }) {
  return (
    <span
      aria-hidden
      className="absolute left-0 top-0 bottom-0 w-[3px] rounded-l-2xl"
      style={{ background: statusColor[status] }}
    />
  );
}

export function Card({
  status = "idle",
  className = "",
  children,
  selected = false,
}: {
  status?: Status;
  className?: string;
  children: ReactNode;
  selected?: boolean;
}) {
  return (
    <div
      className={`relative overflow-hidden rounded-2xl border border-mist bg-white shadow-card ${
        selected ? "ring-2 ring-azimuth ring-offset-1 ring-offset-stratus" : ""
      } ${className}`}
    >
      <StatusSpine status={status} />
      {children}
    </div>
  );
}

export function StatusPill({ status, children }: { status: Status; children: ReactNode }) {
  const dotClass =
    status === "normal"
      ? "bg-[var(--color-status-normal)]"
      : status === "weather"
        ? "bg-[var(--color-status-weather)]"
        : status === "warning"
          ? "bg-[var(--color-status-warning)]"
          : status === "critical"
            ? "bg-[var(--color-status-critical)]"
            : "bg-haze";
  const textColor = statusColor[status];
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium"
      style={{
        color: status === "idle" ? "var(--color-haze)" : textColor,
        background:
          status === "idle"
            ? "rgba(100,116,139,0.08)"
            : `color-mix(in srgb, ${textColor} 12%, white)`,
      }}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${dotClass}`} />
      {children}
    </span>
  );
}

export function LiveDot() {
  return (
    <span className="relative inline-flex h-2 w-2 items-center justify-center text-azimuth">
      <span className="live-dot absolute inset-0 rounded-full" />
      <span className="relative h-2 w-2 rounded-full bg-azimuth" />
    </span>
  );
}

export function KpiCard({
  label,
  value,
  status = "idle",
  delta,
  icon,
}: {
  label: string;
  value: string;
  status?: Status;
  delta?: string;
  icon?: ReactNode;
}) {
  return (
    <Card status={status} className="p-4">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-haze">{label}</span>
        {icon}
      </div>
      <div className="mt-2 font-display text-[28px] font-semibold leading-none text-ink">{value}</div>
      {delta ? <div className="mt-2 text-xs text-haze">{delta}</div> : null}
    </Card>
  );
}

export function SectionTitle({ title, caption, right }: { title: string; caption?: string; right?: ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-4">
      <div>
        <h2 className="font-display text-[18px] font-semibold leading-6 text-ink">{title}</h2>
        {caption ? <p className="mt-0.5 text-sm text-haze">{caption}</p> : null}
      </div>
      {right}
    </div>
  );
}
