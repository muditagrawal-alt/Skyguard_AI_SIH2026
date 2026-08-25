// Reusable weather-vs-fault decision components. They take plain data props
// (Verdict / NeighborTile[] / PipelineNode[] / HealProvenance from lib/adapters)
// so the SAME components render whether the source is a live ProcessedPacket or
// an offline AnomalyRow — the page picks the builder, these stay dumb.
import { Check, X, ArrowRight } from "lucide-react";
import { statusColor } from "./data";
import type { Verdict, NeighborTile, PipelineNode, HealProvenance } from "../lib/adapters";

const KIND_COLOR: Record<Verdict["kind"], string> = {
  fault: "var(--color-status-critical)",
  weather: "var(--color-status-weather)",
  normal: "var(--color-status-normal)",
};

// ── tiny inline tag (tables, alert feed) ──────────────────
export function VerdictTag({
  kind,
  healed = false,
}: {
  kind: "fault" | "weather";
  healed?: boolean;
}) {
  const isWeather = kind === "weather";
  const color = isWeather ? "var(--color-status-weather)" : "var(--color-status-critical)";
  return (
    <span
      className="inline-flex items-center rounded-md px-2 py-0.5 text-[11px] font-bold uppercase tracking-wide"
      style={{ color, background: `color-mix(in srgb, ${color} 12%, white)` }}
    >
      {isWeather ? "Weather" : healed ? "Fault · healed" : "Fault"}
    </span>
  );
}

// ── ⚖️ Verdict capsule ────────────────────────────────────
export function VerdictPanel({ verdict, className = "" }: { verdict: Verdict; className?: string }) {
  const color = KIND_COLOR[verdict.kind];
  return (
    <div
      className={`relative overflow-hidden rounded-2xl border border-mist bg-white p-4 ${className}`}
      style={{ background: `color-mix(in srgb, ${color} 4%, white)` }}
    >
      <span aria-hidden className="absolute inset-y-0 left-0 w-[3px]" style={{ background: color }} />
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1.5">
        <span
          className="rounded-lg px-2.5 py-1 text-xs font-bold uppercase tracking-wide text-white"
          style={{ background: color }}
        >
          {verdict.title}
        </span>
        <span className="min-w-[160px] flex-1 text-sm leading-snug text-ink">{verdict.reason}</span>
        <span className="font-mono text-sm font-semibold" style={{ color }}>
          {verdict.confidence}
        </span>
      </div>

      <div className="mt-3 grid grid-cols-3 gap-2">
        {verdict.evidence.map((e) => {
          const c = e.pass ? "var(--color-status-normal)" : "var(--color-status-critical)";
          return (
            <div
              key={e.label}
              className="rounded-lg border px-2.5 py-1.5"
              style={{
                borderColor: `color-mix(in srgb, ${c} 35%, transparent)`,
                background: `color-mix(in srgb, ${c} 7%, white)`,
              }}
            >
              <div className="flex items-center gap-1.5" style={{ color: c }}>
                {e.pass ? <Check size={12} strokeWidth={2.5} /> : <X size={12} strokeWidth={2.5} />}
                <span className="text-[11px] font-semibold">{e.label}</span>
              </div>
              <div className="mt-0.5 text-[10px] leading-tight text-haze">{e.detail}</div>
            </div>
          );
        })}
      </div>

      <div className="mt-3">
        <span
          className="inline-block rounded-md px-2 py-1 text-[11px] font-medium"
          style={
            verdict.healed
              ? { background: "color-mix(in srgb, var(--color-status-normal) 12%, white)", color: "var(--color-status-normal)" }
              : { background: "rgba(100,116,139,0.10)", color: "var(--color-haze)" }
          }
        >
          {verdict.healedText}
        </span>
      </div>
    </div>
  );
}

// ── Neighbor consistency strip ────────────────────────────
export function NeighborStrip({ tiles, caption }: { tiles: NeighborTile[]; caption: string }) {
  return (
    <div>
      <div className="grid grid-cols-4 gap-1.5">
        {tiles.map((t) => (
          <div
            key={t.id}
            className="relative overflow-hidden rounded-xl border bg-white px-2 py-2"
            style={{
              borderColor: t.isSubject
                ? "color-mix(in srgb, var(--color-status-critical) 45%, transparent)"
                : "var(--color-mist)",
            }}
          >
            <span aria-hidden className="absolute inset-y-0 left-0 w-[3px]" style={{ background: statusColor[t.status] }} />
            <div className="flex items-center justify-between gap-1">
              <span className="truncate text-[11px] font-medium text-ink">{t.name}</span>
              {!t.isSubject && t.ok && (
                <Check size={11} strokeWidth={2.5} style={{ color: "var(--color-status-normal)" }} />
              )}
            </div>
            <div
              className={`mt-1 font-mono text-[12px] ${t.isSubject ? "font-semibold" : "text-ink"}`}
              style={t.isSubject ? { color: "var(--color-status-critical)" } : undefined}
            >
              {t.value}
            </div>
            <div className="mt-0.5 text-[10px] text-haze">
              {t.isSubject ? "subject" : t.ok ? "normal" : "flagged"}
            </div>
          </div>
        ))}
      </div>
      <p className="mt-2 text-[11px] leading-relaxed text-haze">{caption}</p>
    </div>
  );
}

// ── Decision-pipeline stepper ─────────────────────────────
export function DecisionStepper({
  nodes,
  accent = "var(--color-status-critical)",
}: {
  nodes: PipelineNode[];
  accent?: string;
}) {
  return (
    <div className="flex items-start gap-0.5 overflow-x-auto pb-1">
      {nodes.map((n, i) => (
        <div key={`${n.label}-${i}`} className="flex items-start gap-0.5">
          <div className="flex w-[78px] flex-col items-center text-center">
            <span
              className="flex h-6 w-6 items-center justify-center rounded-full text-white"
              style={{ background: n.emphasis ? accent : "var(--color-azimuth)" }}
            >
              <Check size={12} strokeWidth={2.5} />
            </span>
            <span
              className={`mt-1 text-[11px] font-semibold ${n.emphasis ? "" : "text-ink"}`}
              style={n.emphasis ? { color: accent } : undefined}
            >
              {n.label}
            </span>
            <span className="mt-0.5 max-w-full truncate font-mono text-[9px] leading-tight text-haze" title={n.sub}>
              {n.sub}
            </span>
          </div>
          {i < nodes.length - 1 && <span aria-hidden className="mt-3 h-px w-3 shrink-0 bg-mist" />}
        </div>
      ))}
    </div>
  );
}

// ── Heal-provenance block ─────────────────────────────────
export function HealProvenanceBlock({ heal }: { heal: HealProvenance }) {
  const rawNum = parseFloat(heal.raw);
  const fixedNum = parseFloat(heal.fixed);
  const hasSpark = !Number.isNaN(rawNum) && !Number.isNaN(fixedNum);
  const min = hasSpark ? Math.min(rawNum, fixedNum) : 0;
  const max = hasSpark ? Math.max(rawNum, fixedNum) : 1;
  const y = (v: number) => (max === min ? 12 : 4 + (1 - (v - min) / (max - min)) * 16);
  const fixedColor = heal.healed ? "var(--color-status-normal)" : "var(--color-haze)";

  return (
    <div className="rounded-xl border border-mist bg-white p-3">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-1.5 font-mono text-[12.5px]">
          <span className="text-haze">{heal.channel}</span>
          <span style={{ color: "var(--color-series-temp)" }}>{heal.raw}</span>
          <ArrowRight size={12} className="text-haze" />
          <span style={{ color: fixedColor }}>{heal.fixed}</span>
        </div>
        {hasSpark && (
          <svg width="64" height="24" viewBox="0 0 64 24" aria-hidden>
            <line
              x1="9"
              y1={y(rawNum)}
              x2="55"
              y2={y(fixedNum)}
              stroke="var(--color-mist)"
              strokeWidth="1.5"
              strokeDasharray="3 3"
            />
            <circle cx="9" cy={y(rawNum)} r="3.2" fill="var(--color-series-temp)" />
            <circle cx="55" cy={y(fixedNum)} r="3.2" fill={fixedColor} />
          </svg>
        )}
      </div>
      <div className="mt-2 flex items-center justify-between gap-2 text-[11px]">
        <span className="text-haze">{heal.method}</span>
        <span className="font-mono text-haze">{heal.confidence}</span>
      </div>
      <div className="mt-1 text-[10.5px] text-haze">{heal.note}</div>
    </div>
  );
}
