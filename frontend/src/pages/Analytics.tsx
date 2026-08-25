import { BarChart, Bar, XAxis, YAxis, CartesianGrid, ResponsiveContainer, Legend, Cell } from "recharts";
import { Card, KpiCard, SectionTitle } from "../components/primitives";
import {
  analyticsKpis,
  recallByType,
  confusionMatrix,
  benchmark,
  latencyHistogram,
  ensembleWeights,
} from "../components/data";

export default function Analytics() {
  return (
    <div className="flex flex-col gap-6">
      <div className="rounded-xl border border-mist bg-stratus/50 px-4 py-3 text-xs leading-relaxed text-haze">
        Model evaluation snapshot — precision/recall, confusion matrix, benchmark and latency figures
        come from the offline held-out test run, not the current live stream. See the Live Monitor and
        Anomalies pages for real-time session data.
      </div>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-5">
        {analyticsKpis.map((k) => (
          <KpiCard key={k.label} {...k} delta="target met ✓" />
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <Card status="idle" className="p-6">
          <SectionTitle title="Recall by fault type" />
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={recallByType} layout="vertical" margin={{ top: 8, right: 24, bottom: 0, left: 12 }}>
              <CartesianGrid stroke="#eef2f7" horizontal={false} />
              <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 10, fontFamily: "var(--font-mono)", fill: "#94a3b8" }} tickLine={false} axisLine={false} />
              <YAxis type="category" dataKey="label" tick={{ fontSize: 11, fill: "#64748b" }} tickLine={false} axisLine={false} width={100} />
              <Bar dataKey="value" radius={[0, 6, 6, 0]} fill="var(--color-azimuth)" barSize={16} isAnimationActive={false} />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card status="idle" className="p-6">
          <SectionTitle title="Confusion matrix" caption="Predicted vs actual" />
          <div className="mt-4 grid grid-cols-2 gap-3">
            {confusionMatrix.map((c) => (
              <div
                key={c.label}
                className="rounded-xl p-4"
                style={{
                  background: c.good ? "color-mix(in srgb, var(--color-status-normal) 12%, white)" : "color-mix(in srgb, var(--color-status-critical) 12%, white)",
                }}
              >
                <div className="text-xs text-haze">{c.label}</div>
                <div className="mt-1 font-display text-2xl font-semibold" style={{ color: c.good ? "var(--color-status-normal)" : "var(--color-status-critical)" }}>
                  {c.value.toLocaleString()}
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <Card status="idle" className="p-6">
          <SectionTitle title="Real vs synthetic benchmark" />
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={benchmark} margin={{ top: 12, right: 8, bottom: 0, left: -16 }}>
              <CartesianGrid stroke="#eef2f7" vertical={false} />
              <XAxis dataKey="metric" tick={{ fontSize: 11, fill: "#64748b" }} tickLine={false} axisLine={{ stroke: "#e6ebf2" }} />
              <YAxis domain={[80, 100]} tick={{ fontSize: 10, fontFamily: "var(--font-mono)", fill: "#94a3b8" }} tickLine={false} axisLine={false} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Bar name="Synthetic" dataKey="synthetic" fill="var(--color-azimuth)" radius={[6, 6, 0, 0]} barSize={22} isAnimationActive={false} />
              <Bar name="Real NOAA" dataKey="real" fill="#14b8c4" radius={[6, 6, 0, 0]} barSize={22} isAnimationActive={false} />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card status="idle" className="p-6">
          <SectionTitle title="Inference latency distribution" caption="Dashed line = 5 ms target" />
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={latencyHistogram} margin={{ top: 12, right: 8, bottom: 0, left: -16 }}>
              <CartesianGrid stroke="#eef2f7" vertical={false} />
              <XAxis dataKey="ms" tick={{ fontSize: 10, fontFamily: "var(--font-mono)", fill: "#94a3b8" }} tickLine={false} axisLine={{ stroke: "#e6ebf2" }} interval={1} />
              <YAxis tick={{ fontSize: 10, fontFamily: "var(--font-mono)", fill: "#94a3b8" }} tickLine={false} axisLine={false} width={32} />
              <Bar dataKey="count" radius={[4, 4, 0, 0]} barSize={18} isAnimationActive={false}>
                {latencyHistogram.map((d, i) => (
                  <Cell key={i} fill={d.ms === "4.9" || d.ms === "5.0" ? "var(--color-status-normal)" : "var(--color-series-pressure)"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      <Card status="idle" className="p-6">
        <SectionTitle title="Ensemble consensus" caption="Detector weights sum to 1.00" />
        <div className="mt-4 flex h-10 w-full overflow-hidden rounded-xl">
          {ensembleWeights.map((w) => (
            <div
              key={w.label}
              className="flex items-center justify-center text-[11px] font-medium text-white"
              style={{ width: `${w.value * 100}%`, background: w.color }}
              title={`${w.label} ${w.value}`}
            >
              {w.value >= 0.2 ? `${w.label} ${w.value.toFixed(2)}` : w.value.toFixed(2)}
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
