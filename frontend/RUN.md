# Running the SkyGuard dashboard

This frontend (the Figma-built React dashboard) is now wired to the SkyGuard
FastAPI backend. Start the backend first, then the frontend — the dev server
proxies API and WebSocket traffic to the backend, so the browser talks to a
single origin (no CORS setup needed).

## Prerequisites

- **Python 3.10+** with `pip` (for the backend)
- **Node.js 20.19+ (or 22+)** and **pnpm** (for the frontend)

## 1. Start the backend

From the backend project root `D:\Skyguard_AI_SIH2026`:

```bash
pip install -r requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

Leave this running. It serves:

- `GET  /api/stations` — station metadata
- `GET  /api/stations/{id}/latest` and `/buffer` — latest reading / history
- `POST /api/stations/{id}/inject` and `/api/stations/{id}/clear`
- `WS   /ws/stream/{id}?source=synthetic|real&rate_hz=…` — live telemetry

## 2. Start the frontend

From this folder (`Build UI`):

```bash
pnpm install
pnpm dev
```

Open **http://localhost:5173**. The dev server proxies `/api` and `/ws` to the
backend at `http://localhost:8000`.

### Pointing at a backend on another host/port

The proxy target is overridable — no code change needed:

```bash
# Windows PowerShell
$env:BACKEND_ORIGIN="http://192.168.1.20:8000"; pnpm dev

# macOS / Linux
BACKEND_ORIGIN=http://192.168.1.20:8000 pnpm dev
```

Change the frontend's own port with `PORT` (default `8443`).

## What "connected" looks like

- The **sidebar status chip** and the **top-bar source pill** turn live: green
  "System healthy" / "Real NOAA" or "Synthetic" once packets arrive; the bell
  shows a live count of active faults.
- **Live Monitor** streams charts in real time. Use the control strip to
  Start / Stop / Clear the stream, switch station, change the rate, and inject
  faults (Temp spike, Sensor freeze, Calibration drift, Physics fault, Packet
  loss, Thunderstorm).
- **Overview / Stations / Map / Anomalies / Maintenance** all read the same live
  buffers. On Anomalies you can search, filter by severity, export the log to
  CSV, and triage (Acknowledge / Resolve / Reopen — session-local).
- **Settings → Data source** switches the whole stream between the synthetic
  generator and recorded NOAA history. The "Real NOAA" option is disabled unless
  a station reports `has_real_data`.

## Notes

- **Offline fallback:** if the backend isn't reachable, the dashboard keeps
  working on built-in demo data and the status chip reads "Demo mode." It
  reconnects automatically once the backend is up.
- **Analytics** shows the offline model-evaluation snapshot (precision/recall,
  confusion matrix, benchmark, latency) — those are held-out test results, not
  the live stream, and are intentionally static.
- **Settings** detection fields (QC limits, ensemble weights, thresholds) are
  session-only; the backend exposes no settings-write endpoint, so "Save" does
  not persist server-side.
