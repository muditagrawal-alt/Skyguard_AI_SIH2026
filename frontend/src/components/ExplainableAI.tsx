import { useEffect, useRef, useState } from "react";
import { Pause, Play, Pin } from "lucide-react";
import { Card, LiveDot } from "./primitives";
import { VerdictPanel, NeighborStrip } from "./verdict";
import { attribution as mockAttribution } from "./data";
import { useStream } from "../lib/StreamProvider";
import { toAttribution, toVerdict, toNeighborStrip, neighborCaption } from "../lib/adapters";
import type { Verdict, VerdictKind, NeighborTile, AttributionBar } from "../lib/adapters";
import type { Status } from "./data";
import type { ProcessedPacket } from "../lib/types";

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

// The full decision surface derived from one packet. We snapshot this whole
// object (not just the packet) when latching/freezing so a pinned event is a
// true freeze-frame — its neighbours and attribution stay as they were at the
// moment of the event, even as the live stream moves on underneath.
type DecisionView = {
  verdict: Verdict;
  neighbors: NeighborTile[];
  neighborsCaption: string;
  diagnostic: string;
  attribution: AttributionBar[];
};

function buildView(p: ProcessedPacket, latestByStation: Record<string, ProcessedPacket>): DecisionView {
  return {
    verdict: toVerdict(p),
    neighbors: toNeighborStrip(p.station_id, latestByStation),
    neighborsCaption: neighborCaption(p),
    diagnostic: p.xai.explanation,
    attribution: toAttribution(p),
  };
}

const MOCK_VIEW: DecisionView = {
  verdict: MOCK_VERDICT,
  neighbors: MOCK_NEIGHBORS,
  neighborsCaption: MOCK_NEIGHBOR_CAPTION,
  diagnostic: MOCK_DIAGNOSTIC,
  attribution: mockAttribution,
};

type Snapshot = { view: DecisionView; at: string };

function fmtTime(iso: string | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? "—" : d.toLocaleTimeString("en-GB", { hour12: false });
}

const CHIP =
  "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide";
const AZIMUTH_CHIP = {
  color: "var(--color-azimuth)",
  background: "color-mix(in srgb, var(--color-azimuth) 10%, white)",
};

export default function ExplainableAI() {
  const { backendOnline, selectedLatest, latestByStation } = useStream();
  const live = backendOnline && !!selectedLatest;

  // frozen  = manual freeze-frame (highest priority)
  // held    = auto-latched last fault/weather event
  // dismissedHeld = user resumed past the current held event (a fresh event re-surfaces it)
  const [frozen, setFrozen] = useState<Snapshot | null>(null);
  const [held, setHeld] = useState<Snapshot | null>(null);
  const [dismissedHeld, setDismissedHeld] = useState(false);

  const lastPacketRef = useRef<ProcessedPacket | null>(null);
  const prevKindRef = useRef<VerdictKind>("normal");

  // Auto-latch: whenever a new anomalous packet arrives, pin it. The held frame
  // keeps updating to the freshest fault frame while the anomaly persists, then
  // stops (and stays pinned) once readings return to normal — so the final
  // decision remains on screen long enough to read and act on.
  useEffect(() => {
    if (!live || !selectedLatest) return;
    if (selectedLatest === lastPacketRef.current) return; // same packet ref → skip
    lastPacketRef.current = selectedLatest;

    const kind = toVerdict(selectedLatest).kind;
    const wasNormal = prevKindRef.current === "normal";
    prevKindRef.current = kind;

    if (kind !== "normal") {
      setHeld({ view: buildView(selectedLatest, latestByStation), at: fmtTime(selectedLatest.timestamp) });
      // Only force a dismissed panel back open on a genuinely new episode
      // (normal → anomaly), so "Resume live" during an ongoing fault sticks.
      if (wasNormal) setDismissedHeld(false);
    }
  }, [selectedLatest, live, latestByStation]);

  const mode: "frozen" | "held" | "live" =
    frozen ? "frozen" : held && !dismissedHeld ? "held" : "live";

  const view: DecisionView =
    mode === "frozen" && frozen
      ? frozen.view
      : mode === "held" && held
        ? held.view
        : live && selectedLatest
          ? buildView(selectedLatest, latestByStation)
          : MOCK_VIEW;

  const freezeNow = () => {
    if (live && selectedLatest) {
      setFrozen({ view: buildView(selectedLatest, latestByStation), at: fmtTime(selectedLatest.timestamp) });
    }
  };
  const resumeLive = () => {
    setFrozen(null);
    setDismissedHeld(true);
  };

  const subtitle =
    mode === "held"
      ? "Holding the last detected event so you can read it — telemetry keeps streaming underneath."
      : mode === "frozen"
        ? "Frozen for inspection — resume to follow the live stream again."
        : "Is this a sensor fault or genuine weather — and what did we do about it?";

  // Chip/control key off `mode` first; backendOnline only distinguishes the
  // live-vs-demo case. A frozen/held frame is a REAL captured frame, so it must
  // keep its label (and stay resumable) even if the backend drops afterwards —
  // "Demo data" only applies when we're actually showing MOCK_VIEW.
  const chip = mode === "frozen" ? (
    <span className={CHIP} style={AZIMUTH_CHIP}>
      <Pause size={11} strokeWidth={2.5} /> Frozen · {frozen?.at}
    </span>
  ) : mode === "held" ? (
    <span
      className={CHIP}
      style={{
        color: "var(--color-status-warning)",
        background: "color-mix(in srgb, var(--color-status-warning) 12%, white)",
      }}
    >
      <Pin size={11} strokeWidth={2.5} /> Held · {held?.at}
    </span>
  ) : backendOnline ? (
    <span className={CHIP} style={AZIMUTH_CHIP}>
      <LiveDot /> Live
    </span>
  ) : (
    <span className={CHIP} style={{ color: "var(--color-haze)", background: "rgba(100,116,139,0.08)" }}>
      Demo data
    </span>
  );

  const control =
    mode !== "live" ? (
      <button
        onClick={resumeLive}
        className="flex items-center gap-1.5 rounded-xl bg-azimuth px-3 py-1.5 text-xs font-semibold text-white shadow-card transition-transform hover:-translate-y-0.5"
      >
        <Play size={13} strokeWidth={2} /> Resume live
      </button>
    ) : backendOnline ? (
      <button
        onClick={freezeNow}
        className="flex items-center gap-1.5 rounded-xl bg-azimuth/10 px-3 py-1.5 text-xs font-semibold text-azimuth transition-colors hover:bg-azimuth/15"
      >
        <Pause size={13} strokeWidth={2} /> Freeze
      </button>
    ) : null;

  return (
    <Card status={KIND_STATUS[view.verdict.kind]} className="p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="font-display text-[18px] font-semibold leading-6 text-ink">Explainable AI — decision</h2>
          <p className="mt-0.5 text-sm text-haze">{subtitle}</p>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          {chip}
          {control}
        </div>
      </div>

      <div className="mt-4">
        <VerdictPanel verdict={view.verdict} />
      </div>

      <div className="mt-5 text-[11px] font-semibold uppercase tracking-wider text-haze">Neighbor consistency</div>
      <div className="mt-2">
        <NeighborStrip tiles={view.neighbors} caption={view.neighborsCaption} />
      </div>

      <div className="mt-5 text-[11px] font-semibold uppercase tracking-wider text-haze">Diagnostic report</div>
      <div className="relative mt-2 overflow-hidden rounded-xl bg-azimuth/[0.05] p-4 font-mono text-[12.5px] leading-relaxed text-ink">
        <span className="absolute left-0 top-0 bottom-0 w-[3px] bg-azimuth" aria-hidden />
        {view.diagnostic}
      </div>

      <div className="mt-5 text-[11px] font-semibold uppercase tracking-wider text-haze">Feature attribution</div>
      <div className="mt-3 space-y-2.5">
        {view.attribution.map((a) => (
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
