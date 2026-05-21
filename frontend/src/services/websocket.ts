import type { ValidatedTelemetryBatch } from "../schemas/telemetry";
import { useCognitiveStore } from "../store/useCognitiveStore";
import type { CognitiveStatePrediction } from "@shared/types";
import { useAuthStore } from "../store/useAuthStore";
import { GATEWAY_WS_URL, apiUrl } from "../config/env";

export class TelemetrySocketManager {
  private socket: WebSocket | null = null;
  private url: string;
  private isConnecting = false;
  private reconnectAttempts = 0;
  private readonly maxReconnectAttempts = 5;
  private queue: ValidatedTelemetryBatch[] = [];

  constructor(url: string) {
    this.url = url;
  }

  private async ensureToken(): Promise<string | null> {
    let token = useAuthStore.getState().token;

    if (token) {
      return token;
    }

    try {
      console.log("[WebSocket] No token found. Requesting demo token...");

      const res = await fetch(apiUrl("/auth/demo-login/"), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!res.ok) {
        throw new Error(`Demo login failed: ${res.status}`);
      }

      const data = await res.json();

      if (!data.access) {
        throw new Error("No access token returned");
      }

      useAuthStore.getState().setToken(data.access);

      return data.access;
    } catch (error) {
      console.error("[WebSocket] Failed to get demo token:", error);
      return null;
    }
  }

  public async connect() {
    if (this.socket?.readyState === WebSocket.OPEN || this.isConnecting) {
      return;
    }

    this.isConnecting = true;

    const token = await this.ensureToken();

    if (!token) {
      this.isConnecting = false;
      this.handleReconnect();
      return;
    }

    let ticket: string | null = null;

    try {
      const res = await fetch(apiUrl("/auth/ws-ticket/"), {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      if (!res.ok) {
        throw new Error(`Ticket fetch failed: ${res.status}`);
      }

      const data = await res.json();
      ticket = data.ticket;

      if (!ticket) {
        throw new Error("No websocket ticket returned");
      }
    } catch (error) {
      console.error("[WebSocket] Ticket fetch failed:", error);
      this.isConnecting = false;
      this.handleReconnect();
      return;
    }

    const sep = this.url.includes("?") ? "&" : "?";
    const wsUrl = `${this.url}${sep}ticket=${encodeURIComponent(ticket)}`;

    this.socket = new WebSocket(wsUrl);

    this.socket.onopen = () => {
      console.log("[WebSocket] Connected");
      this.isConnecting = false;
      this.reconnectAttempts = 0;
      useCognitiveStore.getState().setSocketStatus("connected");
      this.flushQueue();
    };

    this.socket.onclose = (event) => {
      console.log(`[WebSocket] Disconnected: ${event.code}`);
      this.isConnecting = false;
      this.socket = null;
      useCognitiveStore.getState().setSocketStatus("disconnected");
      this.handleReconnect();
    };

    this.socket.onerror = (error) => {
      console.error("[WebSocket] Error:", error);
      this.socket?.close();
    };

    this.socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.type === "prediction") {
          const prediction = data.payload as CognitiveStatePrediction;
          useCognitiveStore.getState().addPrediction(prediction);
        } else if (data.type === "error") {
          console.warn("[WebSocket] Gateway error:", data.message);
        }
      } catch (err) {
        console.error("[WebSocket] Failed to parse message:", err);
      }
    };
  }

  public disconnect() {
    if (this.socket) {
      this.socket.close(1000, "Client disconnect");
      this.socket = null;
    }
  }

  public sendBatch(batch: ValidatedTelemetryBatch) {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(batch));
    } else {
      console.warn("[WebSocket] Offline. Queuing:", batch.batch_id);
      this.queue.push(batch);
      this.connect();
    }
  }

  private handleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error("[WebSocket] Max reconnect attempts reached");
      return;
    }

    this.reconnectAttempts++;

    const timeout = Math.min(
      1000 * Math.pow(2, this.reconnectAttempts),
      10000
    );

    console.log(`[WebSocket] Reconnecting in ${timeout}ms...`);

    useCognitiveStore.getState().setSocketStatus("reconnecting");

    setTimeout(() => {
      this.connect();
    }, timeout);
  }

  private flushQueue() {
    if (
      this.queue.length > 0 &&
      this.socket?.readyState === WebSocket.OPEN
    ) {
      console.log(`[WebSocket] Flushing ${this.queue.length} queued batches`);

      while (this.queue.length > 0) {
        const batch = this.queue.shift();

        if (batch) {
          this.socket.send(JSON.stringify(batch));
        }
      }
    }
  }
}

export const telemetrySocket = new TelemetrySocketManager(GATEWAY_WS_URL);