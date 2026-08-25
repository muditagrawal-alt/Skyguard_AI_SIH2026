// Reconnecting WebSocket for one station's telemetry feed.
//
// The backend streams processed packets over /ws/telemetry?station_id=..&rate_hz=..&source=..
// One TelemetryStream owns exactly one socket for one station; the StreamProvider
// runs up to four (one per station) so every page is live at once. Changing the
// data source, rate, or station means tearing a stream down and creating a new one
// (those are query params baked into the URL at connect time).
//
// Reconnect: on an unexpected close we retry with exponential backoff (capped),
// so a backend that is briefly down — or started after the dashboard — reconnects
// on its own without a page reload. close() cancels retries permanently.

import { wsUrl } from "./config";
import type { ProcessedPacket, DataSource } from "./types";

export type StreamStatus = "connecting" | "open" | "closed" | "error";

export type TelemetryStreamOptions = {
  stationId: string;
  rateHz: number;
  source: DataSource;
  onMessage: (packet: ProcessedPacket) => void;
  onStatus?: (status: StreamStatus) => void;
  onError?: (message: string) => void;
};

const MAX_BACKOFF_MS = 8000;
const BASE_BACKOFF_MS = 500;

export class TelemetryStream {
  private ws: WebSocket | null = null;
  private closedByUser = false;
  private attempt = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private readonly opts: TelemetryStreamOptions;

  constructor(opts: TelemetryStreamOptions) {
    this.opts = opts;
    this.connect();
  }

  private setStatus(status: StreamStatus) {
    this.opts.onStatus?.(status);
  }

  private connect() {
    if (this.closedByUser) return;
    this.setStatus("connecting");

    const url = wsUrl("/ws/telemetry", {
      station_id: this.opts.stationId,
      rate_hz: this.opts.rateHz,
      source: this.opts.source,
    });

    let socket: WebSocket;
    try {
      socket = new WebSocket(url);
    } catch {
      this.scheduleReconnect();
      return;
    }
    this.ws = socket;

    socket.onopen = () => {
      this.attempt = 0;
      this.setStatus("open");
    };

    socket.onmessage = (event: MessageEvent<string>) => {
      try {
        const parsed = JSON.parse(event.data) as ProcessedPacket | { error: string };
        if (parsed && typeof parsed === "object" && "error" in parsed) {
          this.opts.onError?.(String((parsed as { error: string }).error));
          return;
        }
        this.opts.onMessage(parsed as ProcessedPacket);
      } catch {
        /* ignore malformed frame */
      }
    };

    socket.onerror = () => {
      this.setStatus("error");
    };

    socket.onclose = () => {
      this.ws = null;
      if (this.closedByUser) {
        this.setStatus("closed");
        return;
      }
      this.scheduleReconnect();
    };
  }

  private scheduleReconnect() {
    if (this.closedByUser) return;
    this.setStatus("closed");
    const delay = Math.min(MAX_BACKOFF_MS, BASE_BACKOFF_MS * 2 ** this.attempt);
    this.attempt += 1;
    this.reconnectTimer = setTimeout(() => this.connect(), delay);
  }

  /** Permanently close this stream and cancel any pending reconnect. */
  close() {
    this.closedByUser = true;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      try {
        this.ws.close();
      } catch {
        /* already closing */
      }
      this.ws = null;
    }
  }
}
