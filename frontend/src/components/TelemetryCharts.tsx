import {
  ComposedChart,
  Line,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  ResponsiveContainer,
} from "recharts";
import { Card } from "./primitives";
import { telemetry as mockTelemetry } from "./data";
import { useStream } from "../lib/StreamProvider";
import { toTelemetryRows } from "../lib/adapters";

const axisStyle = { fontSize: 10, fontFamily: "var(--font-mono)", fill: "#94a3b8" };

const legend = [
  { label: "Ground truth", color: "#94a3b8", dash: true },
  { label: "Raw telemetry", color: "var(--color-series-temp)" },
  { label: "Self-healed", color: "var(--color-series-healed)", dash: true },
  { label: "Flagged anomaly", color: "var(--color-status-critical)", marker: true },
  { label: "Dew point", color: "var(--color-series-dew)", dash: true },
];

function ChartFrame({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="mb-1 font-mono text-[11px] font-medium text-haze">{title}</div>
      <ResponsiveContainer width="100%" height={130}>
        {children as React.ReactElement}
      </ResponsiveContainer>
    </div>
  );
}

export default function TelemetryCharts() {
  const { backendOnline, selectedBuffer } = useStream();
  const rows = backendOnline && selectedBuffer.length > 0 ? toTelemetryRows(selectedBuffer) : mockTelemetry;
  const telemetry = rows;

  return (
    <Card status="warning" className="p-6">
      <h2 className="font-display text-[18px] font-semibold leading-6 text-ink">Real-time sensor telemetry</h2>

      <div className="mt-3 flex flex-wrap gap-x-5 gap-y-2">
        {legend.map((l) => (
          <div key={l.label} className="flex items-center gap-1.5 text-xs text-haze">
            {l.marker ? (
              <span className="font-mono text-sm leading-none" style={{ color: l.color }}>
                ✕
              </span>
            ) : (
              <span
                className="inline-block h-0 w-5 border-t-2"
                style={{ borderColor: l.color, borderStyle: l.dash ? "dashed" : "solid" }}
              />
            )}
            {l.label}
          </div>
        ))}
      </div>

      <div className="mt-4 space-y-4">
        <ChartFrame title="Temperature (°C)">
          <ComposedChart data={telemetry} margin={{ top: 6, right: 8, bottom: 0, left: -18 }}>
            <CartesianGrid stroke="#eef2f7" vertical={false} />
            <XAxis dataKey="t" tick={axisStyle} tickLine={false} axisLine={{ stroke: "#e6ebf2" }} interval={3} />
            <YAxis tick={axisStyle} tickLine={false} axisLine={false} width={40} domain={["auto", "auto"]} />
            <Line dataKey="truth" stroke="#94a3b8" strokeWidth={1} strokeDasharray="2 3" dot={false} isAnimationActive={false} />
            <Line dataKey="raw" stroke="var(--color-series-temp)" strokeWidth={2} dot={{ r: 2, fill: "var(--color-series-temp)" }} isAnimationActive={false} />
            <Line dataKey="healed" stroke="var(--color-series-healed)" strokeWidth={2} strokeDasharray="5 4" dot={false} isAnimationActive={false} />
            <Scatter dataKey="flagged" fill="var(--color-status-critical)" shape="cross" isAnimationActive={false} />
          </ComposedChart>
        </ChartFrame>

        <ChartFrame title="Atmospheric pressure (hPa)">
          <ComposedChart data={telemetry} margin={{ top: 6, right: 8, bottom: 0, left: -18 }}>
            <CartesianGrid stroke="#eef2f7" vertical={false} />
            <XAxis dataKey="t" tick={axisStyle} tickLine={false} axisLine={{ stroke: "#e6ebf2" }} interval={3} />
            <YAxis tick={axisStyle} tickLine={false} axisLine={false} width={40} domain={["auto", "auto"]} />
            <Line dataKey="pressure" stroke="var(--color-series-pressure)" strokeWidth={2} dot={false} isAnimationActive={false} />
            <Line dataKey="pressureHealed" stroke="var(--color-series-healed)" strokeWidth={2} strokeDasharray="5 4" dot={false} connectNulls isAnimationActive={false} />
          </ComposedChart>
        </ChartFrame>

        <ChartFrame title="Relative humidity (%)">
          <ComposedChart data={telemetry} margin={{ top: 6, right: 8, bottom: 0, left: -18 }}>
            <CartesianGrid stroke="#eef2f7" vertical={false} />
            <XAxis dataKey="t" tick={axisStyle} tickLine={false} axisLine={{ stroke: "#e6ebf2" }} interval={3} />
            <YAxis tick={axisStyle} tickLine={false} axisLine={false} width={40} domain={["auto", "auto"]} />
            <Line dataKey="humidity" stroke="var(--color-series-humidity)" strokeWidth={2} dot={false} isAnimationActive={false} />
            <Line dataKey="dew" stroke="var(--color-series-dew)" strokeWidth={2} strokeDasharray="6 3 2 3" dot={false} isAnimationActive={false} />
          </ComposedChart>
        </ChartFrame>
      </div>
    </Card>
  );
}
