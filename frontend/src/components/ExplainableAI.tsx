import { Card } from "./primitives";
import { VerdictPanel, NeighborStrip } from "./verdict";
import { attribution as mockAttribution } from "./data";
import { useStream } from "../lib/StreamProvider";
import { toAttribution, toVerdict, toNeighborStrip, neighborCaption } from "../lib/adapters";
import type { Verdict, NeighborTile } from "../lib/adapters";
import type { Status } from "./data";

const MOCK_DIAGNOSTIC =
  "Temperature rose 15.3 °C in 60 s — 5.1× the WMO gradient limit (3.0 °C/min). Pressure and humidity stable; neighboring stations normal. Classified as an isolated SENSOR SPIKE, not weather. Raw value quarantined; stream self-healed via temporal imputation. Confidence 96.4%.";

const MOCK_VERDICT: Verdict = {
  kind: "fault",
  title: "SENSOR FAULT",
  reason: "Isolated +15 °C spike that no neighbour shares — physically implausible rate",
  confidence: "96.4%",
  evidence: [
    { label: "Physics", pass: true, detail: "Spike is physically possible in isolation" },
    { label: "Spatial", pass: false, detail: "Isolated — no neighbour shares it" },
    { label: "Rate", pass: false, detail: "5.1× the WMO gradient limit" },
  ],
  healed: true,
  healedText: "Healed → 24.9 °C",
};

const MOCK_NEIGHBORS: NeighborTile[] = [
  { id: "AWS_GAMMA_URBAN", name: "Gamma Metropole", value: "39.8 °C", status: "critical", isSubject: true, ok: false },
  { id: "AWS_ALPHA_MOUNTAIN", name: "Alpha Ridge", value: "11.8 °C", status: "normal", isSubject: false, ok: true },
  { id: "AWS_BETA_COASTAL", name: "Beta Coastline", value: "27.4 °C", status: "normal", isSubject: false, ok: true },
  { id: "AWS_DELTA_DESERT", name: "Delta Dunes", value: "41.2 °C", status: "normal", isSubject: false, ok: true },
];
const MOCK_NEIGHBOR_CAPTION =
  "Only Gamma moved — the jump is local, so it's a sensor fault, not weather.";

const KIND_STATUS: Record<Verdict["kind"], Status> = {
  fault: "critical",
  weather: "weather",
  normal: "normal",
};

export default function ExplainableAI() {
  const { backendOnline, selectedLatest, latestByStation } = useStream();
  const live = backendOnline && selectedLatest;

  const verdict = live ? toVerdict(selectedLatest) : MOCK_VERDICT;
  const neighbors = live ? toNeighborStrip(selectedLatest.station_id, latestByStation) : MOCK_NEIGHBORS;
  const neighborsCaption = live ? neighborCaption(selectedLatest) : MOCK_NEIGHBOR_CAPTION;
  const diagnostic = live ? selectedLatest.xai.explanation : MOCK_DIAGNOSTIC;
  const attribution = live ? toAttribution(selectedLatest) : mockAttribution;

  return (
    <Card status={KIND_STATUS[verdict.kind]} className="p-6">
      <h2 className="font-display text-[18px] font-semibold leading-6 text-ink">Explainable AI — decision</h2>
      <p className="mt-0.5 text-sm text-haze">Is this a sensor fault or genuine weather — and what did we do about it?</p>

      <div className="mt-4">
        <VerdictPanel verdict={verdict} />
      </div>

      <div className="mt-5 text-[11px] font-semibold uppercase tracking-wider text-haze">Neighbor consistency</div>
      <div className="mt-2">
        <NeighborStrip tiles={neighbors} caption={neighborsCaption} />
      </div>

      <div className="mt-5 text-[11px] font-semibold uppercase tracking-wider text-haze">Diagnostic report</div>
      <div className="relative mt-2 overflow-hidden rounded-xl bg-azimuth/[0.05] p-4 font-mono text-[12.5px] leading-relaxed text-ink">
        <span className="absolute left-0 top-0 bottom-0 w-[3px] bg-azimuth" aria-hidden />
        {diagnostic}
      </div>

      <div className="mt-5 text-[11px] font-semibold uppercase tracking-wider text-haze">Feature attribution</div>
      <div className="mt-3 space-y-2.5">
        {attribution.map((a) => (
          <div key={a.label} className="flex items-center gap-3">
            <span className="w-40 shrink-0 text-xs text-ink">{a.label}</span>
            <div className="h-6 flex-1 overflow-hidden rounded-lg bg-mist/60">
              <div
                className="flex h-full items-center justify-end rounded-lg pr-2"
                style={{
                  width: `${Math.max(a.value, 6)}%`,
                  background: "linear-gradient(90deg, var(--color-azimuth), #14b8c4)",
                }}
              >
                <span className="font-mono text-[11px] font-medium text-white">{a.value}%</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
