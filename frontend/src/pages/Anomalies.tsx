import { useState } from "react";
import { Search, Download, X, StickyNote } from "lucide-react";
import { Card, KpiCard, StatusPill, StatusSpine } from "../components/primitives";
import { VerdictPanel, DecisionStepper, NeighborStrip, HealProvenanceBlock, VerdictTag } from "../components/verdict";
import {
  anomalyKpis as mockAnomalyKpis,
  anomalyRows as mockAnomalyRows,
  stations as mockStations,
  severityStatus,
  ensembleWeights,
  attribution as mockAttribution,
  type AnomalyRow,
} from "../components/data";
import { useStream } from "../lib/StreamProvider";
import {
  packetToAnomalyRow,
  toAnomalyKpis,
  toAttribution,
  toVerdict,
  verdictFromRow,
  toPipeline,
  pipelineFromRow,
  toNeighborStrip,
  neighborCaption,
  toHealProvenance,
  healProvenanceFromRow,
  toDetectorVotes,
  rowWasHealed,
} from "../lib/adapters";
import type { NeighborTile } from "../lib/adapters";
import type { ProcessedPacket } from "../lib/types";

const stateStatus: Record<string, string> = {
  Open: "text-[var(--color-status-critical)]",
  Acknowledged: "text-[var(--color-status-warning)]",
  Resolved: "text-[var(--color-status-normal)]",
};

// Each table entry carries its source packet (when live) so the drawer can show
// the real, per-anomaly feature attribution rather than a static illustration.
type Entry = { id: string; row: AnomalyRow; packet: ProcessedPacket | null };
type Triage = AnomalyRow["state"];

const severityFilters = ["All", "Critical", "High", "Medium", "Info"] as const;
type SeverityFilter = (typeof severityFilters)[number];

const verdictFilters = ["All", "Sensor fault", "Genuine weather"] as const;
type VerdictFilter = (typeof verdictFilters)[number];

function csvCell(v: string): string {
  return /[",\n]/.test(v) ? `"${v.replace(/"/g, '""')}"` : v;
}

function exportCsv(entries: Entry[]) {
  const header = ["Time", "Station", "Fault type", "Verdict", "Category", "Severity", "Confidence", "Raw", "Healed", "State"];
  const body = entries.map((e) => [
    e.row.time, e.row.station, e.row.type,
    e.row.verdict === "weather" ? "Genuine weather" : "Sensor fault",
    e.row.category, e.row.severity, e.row.confidence, e.row.raw, e.row.healed, e.row.state,
  ]);
  const csv = [header, ...body].map((r) => r.map(csvCell).join(",")).join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `skyguard-anomalies-${new Date().toISOString().slice(0, 19).replace(/[:T]/g, "-")}.csv`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

// Offline neighbor strip: highlight the row's own station as the subject and
// show the others as normal. For a genuine-weather row, one neighbour also
// shows the event (it's corroborated); for a fault, neighbours stay normal.
function mockNeighborsForRow(row: AnomalyRow): { tiles: NeighborTile[]; caption: string } {
  const isWeather = row.verdict === "weather";
  const ordered = [...mockStations].sort((a, b) => {
    const aSub = a.name === row.station;
    const bSub = b.name === row.station;
    return aSub === bSub ? 0 : aSub ? -1 : 1;
  });
  let corroborated = false;
  const tiles: NeighborTile[] = ordered.map((s): NeighborTile => {
    const isSubject = s.name === row.station;
    if (isSubject) {
      return { id: s.id, name: s.name, value: `${s.temp} °C`, status: isWeather ? "weather" : "critical", isSubject: true, ok: false };
    }
    if (isWeather && !corroborated) {
      corroborated = true;
      return { id: s.id, name: s.name, value: `${s.temp} °C`, status: "weather", isSubject: false, ok: false };
    }
    return { id: s.id, name: s.name, value: `${s.temp} °C`, status: "normal", isSubject: false, ok: true };
  });
  const normalCount = tiles.filter((t) => !t.isSubject && t.ok).length;
  const caption = isWeather
    ? "Coordinated with a neighbouring station — a shared, physically-consistent shift, so it reads as genuine weather."
    : `Isolated to ${row.station} — ${normalCount} neighbour${normalCount === 1 ? "" : "s"} reading normal, so it's a sensor fault, not weather.`;
  return { tiles, caption };
}

function Drawer({
  entry,
  latestByStation,
  onClose,
  onTriage,
}: {
  entry: Entry;
  latestByStation: Record<string, ProcessedPacket>;
  onClose: () => void;
  onTriage: (id: string, state: Triage) => void;
}) {
  const { row, packet } = entry;
  const [noteOpen, setNoteOpen] = useState(false);
  const [note, setNote] = useState("");

  const verdict = packet ? toVerdict(packet) : verdictFromRow(row);
  const pipeline = packet ? toPipeline(packet) : pipelineFromRow(row);
  const accent = verdict.kind === "weather" ? "var(--color-status-weather)" : "var(--color-status-critical)";
  const neighbors = packet
    ? { tiles: toNeighborStrip(packet.station_id, latestByStation), caption: neighborCaption(packet) }
    : mockNeighborsForRow(row);
  const heal = packet ? toHealProvenance(packet) : healProvenanceFromRow(row);
  const attribution = packet ? toAttribution(packet) : mockAttribution;
  const votes = packet ? toDetectorVotes(packet) : ensembleWeights.map((w) => ({ label: w.label, value: w.value }));

  return (
    <Card status={severityStatus[row.severity]} className="flex h-fit flex-col p-5">
      <div className="flex items-start justify-between">
        <div>
          <div className="font-mono text-[12px] text-haze">{row.time} · {row.station}</div>
          <div className="mt-0.5 font-mono text-sm font-semibold text-ink">{row.type}</div>
        </div>
        <button onClick={onClose} className="flex h-7 w-7 items-center justify-center rounded-lg text-haze hover:bg-mist/50 hover:text-ink">
          <X size={16} />
        </button>
      </div>

      <div className="mt-4">
        <VerdictPanel verdict={verdict} />
      </div>

      <div className="mt-5 text-[11px] font-semibold uppercase tracking-wider text-haze">Decision pipeline</div>
      <div className="mt-2">
        <DecisionStepper nodes={pipeline} accent={accent} />
      </div>

      <div className="mt-5 text-[11px] font-semibold uppercase tracking-wider text-haze">Neighbor consistency</div>
      <div className="mt-2">
        <NeighborStrip tiles={neighbors.tiles} caption={neighbors.caption} />
      </div>

      <div className="mt-5 text-[11px] font-semibold uppercase tracking-wider text-haze">Self-healing provenance</div>
      <div className="mt-2">
        <HealProvenanceBlock heal={heal} />
      </div>

      <div className="mt-5 text-[11px] font-semibold uppercase tracking-wider text-haze">Diagnostic report</div>
      <div className="relative mt-1.5 overflow-hidden rounded-xl bg-azimuth/[0.05] p-3 font-mono text-[12px] leading-relaxed text-ink">
        <span className="absolute inset-y-0 left-0 w-[3px] bg-azimuth" />
        {row.explain}
      </div>

      <div className="mt-5 text-[11px] font-semibold uppercase tracking-wider text-haze">Feature attribution</div>
      <div className="mt-2 space-y-2">
        {attribution.map((a) => (
          <div key={a.label} className="flex items-center gap-2">
            <span className="w-32 shrink-0 text-xs text-ink">{a.label}</span>
            <div className="h-4 flex-1 overflow-hidden rounded-md bg-mist/60">
              <div className="h-full rounded-md" style={{ width: `${Math.max(a.value, 4)}%`, background: "linear-gradient(90deg,var(--color-azimuth),#14b8c4)" }} />
            </div>
            <span className="w-9 text-right font-mono text-[11px] text-haze">{a.value}%</span>
          </div>
        ))}
      </div>

      <div className="mt-5 text-[11px] font-semibold uppercase tracking-wider text-haze">Detector votes</div>
      <div className="mt-2 space-y-1.5">
        {votes.map((w) => (
          <div key={w.label} className="flex items-center justify-between text-xs">
            <span className="text-ink">{w.label}</span>
            <span className="font-mono text-haze">{w.value.toFixed(2)}</span>
          </div>
        ))}
      </div>

      <div className="mt-5 flex items-center gap-2 text-[11px]">
        <span className="text-haze">Triage state:</span>
        <span className={`font-semibold ${stateStatus[row.state]}`}>{row.state}</span>
      </div>
      <div className="mt-2 flex gap-2">
        <button
          onClick={() => onTriage(entry.id, "Acknowledged")}
          disabled={row.state === "Acknowledged"}
          className="flex-1 rounded-xl bg-azimuth px-3 py-2 text-sm font-semibold text-white shadow-card transition-transform hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:translate-y-0"
        >
          Acknowledge
        </button>
        <button
          onClick={() => onTriage(entry.id, "Resolved")}
          disabled={row.state === "Resolved"}
          className="flex-1 rounded-xl bg-azimuth/10 px-3 py-2 text-sm font-semibold text-azimuth transition-colors hover:bg-azimuth/15 disabled:cursor-not-allowed disabled:opacity-40"
        >
          Resolve
        </button>
        <button
          onClick={() => setNoteOpen((v) => !v)}
          className="flex items-center gap-1.5 rounded-xl px-3 py-2 text-sm font-medium text-haze transition-colors hover:bg-mist/50 hover:text-ink"
        >
          <StickyNote size={15} strokeWidth={1.5} /> Add note
        </button>
      </div>
      {noteOpen && (
        <textarea
          value={note}
          onChange={(e) => setNote(e.target.value)}
          rows={2}
          placeholder="Add an investigation note (session-only)…"
          className="mt-2 w-full resize-none rounded-xl border border-mist bg-white px-3 py-2 text-sm text-ink outline-none placeholder:text-haze focus:border-azimuth/40"
        />
      )}
      {note.trim() !== "" && <div className="mt-1.5 text-[11px] text-haze">Note saved for this session.</div>}
    </Card>
  );
}

export default function Anomalies() {
  const { backendOnline, buffers, latestByStation } = useStream();
  const live = backendOnline;

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [sev, setSev] = useState<SeverityFilter>("All");
  const [verdictF, setVerdictF] = useState<VerdictFilter>("All");
  // Triage is client-side only — the backend exposes no anomaly-state endpoint,
  // so acknowledgements live for the session (keyed by station+timestamp).
  const [triage, setTriage] = useState<Record<string, Triage>>({});

  const kpis = live ? toAnomalyKpis(buffers) : mockAnomalyKpis;

  const baseEntries: Entry[] = live
    ? Object.entries(buffers)
        .flatMap(([sid, buf]) => buf.filter((p) => p.ensemble.is_anomaly).map((p) => ({ sid, p })))
        .sort((a, b) => new Date(b.p.timestamp).getTime() - new Date(a.p.timestamp).getTime())
        .slice(0, 80)
        .map(({ sid, p }) => ({ id: `${sid}|${p.timestamp}`, row: packetToAnomalyRow(p), packet: p }))
    : mockAnomalyRows.map((r, i) => ({ id: `mock-${i}`, row: r, packet: null }));

  const entries: Entry[] = baseEntries.map((e) =>
    triage[e.id] ? { ...e, row: { ...e.row, state: triage[e.id] } } : e,
  );

  const q = query.trim().toLowerCase();
  const verdictWant = verdictF === "All" ? null : verdictF === "Genuine weather" ? "weather" : "fault";
  const filtered = entries.filter(
    (e) =>
      (sev === "All" || e.row.severity === sev) &&
      (verdictWant === null || e.row.verdict === verdictWant) &&
      (q === "" ||
        `${e.row.station} ${e.row.type} ${e.row.category} ${e.row.explain}`.toLowerCase().includes(q)),
  );

  const selected = entries.find((e) => e.id === selectedId) ?? null;
  const onTriage = (id: string, state: Triage) => setTriage((prev) => ({ ...prev, [id]: state }));

  return (
    <div className="flex flex-col gap-5">
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {kpis.map((k) => (
          <KpiCard key={k.label} {...k} />
        ))}
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <div className="flex items-center gap-2 rounded-xl border border-mist bg-white px-3 py-2">
          <Search size={15} className="text-haze" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search anomalies"
            className="w-40 bg-transparent text-sm text-ink outline-none placeholder:text-haze"
          />
        </div>
        <div className="flex flex-wrap gap-1.5">
          {severityFilters.map((f) => (
            <button
              key={f}
              onClick={() => setSev(f)}
              className={`rounded-full px-3 py-1.5 text-xs font-medium transition-colors ${
                sev === f ? "bg-azimuth text-white" : "border border-mist bg-white text-haze hover:text-ink"
              }`}
            >
              {f}
            </button>
          ))}
        </div>
        <span aria-hidden className="h-5 w-px bg-mist" />
        <div className="flex flex-wrap gap-1.5">
          {verdictFilters.map((f) => {
            const active = verdictF === f;
            const color = f === "Sensor fault" ? "var(--color-status-critical)" : f === "Genuine weather" ? "var(--color-status-weather)" : "var(--color-azimuth)";
            return (
              <button
                key={f}
                onClick={() => setVerdictF(f)}
                className="rounded-full border px-3 py-1.5 text-xs font-medium transition-colors"
                style={
                  active
                    ? { background: color, borderColor: color, color: "white" }
                    : { background: "white", borderColor: "var(--color-mist)", color: "var(--color-haze)" }
                }
              >
                {f}
              </button>
            );
          })}
        </div>
        <button
          onClick={() => exportCsv(filtered)}
          disabled={filtered.length === 0}
          className="ml-auto flex items-center gap-1.5 rounded-xl bg-azimuth/10 px-3 py-2 text-sm font-medium text-azimuth transition-colors hover:bg-azimuth/15 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <Download size={15} strokeWidth={1.5} /> Export log (CSV)
        </button>
      </div>

      <div className={`grid grid-cols-1 gap-5 ${selected ? "xl:grid-cols-[1fr_360px]" : ""}`}>
        <Card status="idle" className="p-2">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[940px] text-left text-sm">
              <thead>
                <tr className="border-b border-mist text-[11px] font-semibold uppercase tracking-wider text-haze">
                  <th className="px-4 py-3 font-semibold">Time</th>
                  <th className="px-4 py-3 font-semibold">Station</th>
                  <th className="px-4 py-3 font-semibold">Fault type</th>
                  <th className="px-4 py-3 font-semibold">Verdict</th>
                  <th className="px-4 py-3 font-semibold">Severity</th>
                  <th className="px-4 py-3 font-semibold">Confidence</th>
                  <th className="px-4 py-3 font-semibold">Raw → Healed</th>
                  <th className="px-4 py-3 font-semibold">Status</th>
                </tr>
              </thead>
              <tbody>
                {filtered.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="py-10 text-center text-sm text-haze">
                      {live
                        ? "No anomalies match — all monitored stations nominal this session."
                        : "No anomalies to show."}
                    </td>
                  </tr>
                ) : (
                  filtered.map((e) => {
                    const r = e.row;
                    const st = severityStatus[r.severity];
                    return (
                      <tr
                        key={e.id}
                        onClick={() => setSelectedId(e.id)}
                        className={`cursor-pointer border-b border-mist/70 transition-colors hover:bg-stratus/60 ${
                          selectedId === e.id ? "bg-azimuth/[0.04]" : ""
                        }`}
                      >
                        <td className="relative px-4 py-3">
                          <StatusSpine status={st} />
                          <span className="font-mono text-[13px] text-ink">{r.time}</span>
                        </td>
                        <td className="px-4 py-3 text-ink">{r.station}</td>
                        <td className="px-4 py-3 font-mono text-[11.5px] text-haze">{r.type}</td>
                        <td className="px-4 py-3"><VerdictTag kind={r.verdict} healed={rowWasHealed(r)} /></td>
                        <td className="px-4 py-3"><StatusPill status={st}>{r.severity}</StatusPill></td>
                        <td className="px-4 py-3 font-mono text-[13px] text-ink">{r.confidence}</td>
                        <td className="px-4 py-3 font-mono text-[13px] text-ink"><span className="text-haze">{r.raw}</span> → {r.healed}</td>
                        <td className={`px-4 py-3 text-[13px] font-medium ${stateStatus[r.state]}`}>{r.state}</td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </Card>

        {selected && (
          <Drawer
            entry={selected}
            latestByStation={latestByStation}
            onClose={() => setSelectedId(null)}
            onTriage={onTriage}
            key={selected.id}
          />
        )}
      </div>
    </div>
  );
}
