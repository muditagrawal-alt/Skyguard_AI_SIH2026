import ControlStrip from "../components/ControlStrip";
import StatCards from "../components/StatCards";
import TelemetryCharts from "../components/TelemetryCharts";
import HealthRadar from "../components/HealthRadar";
import InjectionSandbox from "../components/InjectionSandbox";
import ExplainableAI from "../components/ExplainableAI";

export default function LiveMonitor() {
  return (
    <div className="flex flex-col gap-6">
      <ControlStrip />
      <StatCards />
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <div className="xl:col-span-2">
          <TelemetryCharts />
        </div>
        <div className="xl:col-span-1">
          <HealthRadar />
        </div>
      </div>
      <InjectionSandbox />
      <ExplainableAI />
    </div>
  );
}
