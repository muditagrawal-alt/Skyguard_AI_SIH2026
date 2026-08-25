import { Zap, Snowflake, TrendingUp, AlertTriangle, WifiOff, CloudLightning } from "lucide-react";
import { Card, SectionTitle } from "./primitives";
import { useStream } from "../lib/StreamProvider";
import type { AnomalyType } from "../lib/types";

const actions: {
  icon: typeof Zap;
  title: string;
  sub: string;
  type: AnomalyType;
  weather?: boolean;
}[] = [
  { icon: Zap, title: "Temp spike", sub: "+15 °C", type: "spike" },
  { icon: Snowflake, title: "Sensor freeze", sub: "Flatline / stuck ADC", type: "flatline" },
  { icon: TrendingUp, title: "Calibration drift", sub: "+0.25 °C per step", type: "drift" },
  { icon: AlertTriangle, title: "Physics fault", sub: "54 °C & 96% RH", type: "physics_violation" },
  { icon: WifiOff, title: "Packet loss", sub: "Dropouts & outliers", type: "packet_loss" },
  { icon: CloudLightning, title: "Thunderstorm", sub: "0% false alarm", type: "thunderstorm", weather: true },
];

export default function InjectionSandbox() {
  const { inject, backendOnline, notice, selectedStation } = useStream();
  const stationName = selectedStation?.name ?? "the selected station";

  return (
    <Card status="idle" className="p-6">
      <SectionTitle
        title="Anomaly injection sandbox"
        caption={`Simulate hardware faults, telemetry errors, or a genuine severe storm on ${stationName}'s live stream.`}
        right={
          notice ? (
            <span className="rounded-full bg-azimuth/10 px-3 py-1 text-xs font-medium text-azimuth">{notice}</span>
          ) : undefined
        }
      />
      <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        {actions.map((a) => {
          const Icon = a.icon;
          return (
            <button
              key={a.title}
              onClick={() => inject(a.type)}
              disabled={!backendOnline}
              title={!backendOnline ? "Connect the backend to inject anomalies" : `Inject ${a.title} on ${stationName}`}
              className={`group flex flex-col items-start gap-2 rounded-xl border px-3.5 py-3 text-left transition-all hover:-translate-y-0.5 hover:shadow-card focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-azimuth disabled:cursor-not-allowed disabled:opacity-45 disabled:hover:translate-y-0 disabled:hover:shadow-none ${
                a.weather
                  ? "border-[var(--color-status-weather)]/25 bg-[var(--color-status-weather)]/[0.06]"
                  : "border-azimuth/15 bg-azimuth/[0.05]"
              }`}
            >
              <Icon
                size={18}
                strokeWidth={1.5}
                className={a.weather ? "text-[var(--color-status-weather)]" : "text-azimuth"}
              />
              <div>
                <div className="text-[13px] font-semibold text-ink">{a.title}</div>
                <div className="mt-0.5 font-mono text-[11px] text-haze">{a.sub}</div>
              </div>
            </button>
          );
        })}
      </div>
    </Card>
  );
}
