import type { ValidatedTelemetryBatch } from "../schemas/telemetry";
import { useCognitiveStore } from "../store/useCognitiveStore";
import type { CognitiveStatePrediction } from "@shared/types";
import { useAuthStore } from "../store/useAuthStore";
import { GATEWAY_WS_URL } from "../config/env";

export class TelemetrySocketManager {
  private socket: WebSocket | null = null;
  private url: string;
  private isConnecting: boolean = false;
  private reconnectAttempts: number = 0;
  private readonly maxReconnectAttempts: number = 5;
  private queue: ValidatedTelemetryBatch[] = [];

  constructor(url: string) {
    this.url = url;
  }

  public connect() {
    if (this.socket?.readyState === WebSocket.OPEN || this.isConnecting) {
      return;
    }

    this.isConnecting = true;
    const token = useAuthStore.getState().token;
    const sep = this.url.includes("?") ? "&" : "?";
    const wsUrl = token ? `${this.url}${sep}token=${encodeURIComponent(token)}` : this.url;
    this.socket = new WebSocket(wsUrl);

    this.socket.onopen = () => {
      console.log("[WebSocket] Connected to Telemetry Gateway");
      this.isConnecting = false;
      this.reconnectAttempts = 0;
      useCognitiveStore.getState().setSocketStatus("connected");
      this.flushQueue();
    };

    this.socket.onclose = (event) => {
      console.log(`[WebSocket] Disconnected: ${event.code}`);
      this.isConnecting = false;
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
          console.warn("[WebSocket] Error from Gateway:", data.message);
        }
      } catch (err) {
        console.error("[WebSocket] Failed to parse message", err);
      }
    };
  }

  public disconnect() {
    if (this.socket) {
      this.socket.close(1000, "Client closed intentionally");
      this.socket = null;
    }
  }

  public sendBatch(batch: ValidatedTelemetryBatch) {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(batch));
    } else {
      console.warn("[WebSocket] Offline. Queuing batch:", batch.batch_id);
      this.queue.push(batch);
      this.connect(); // Try to reconnect if we are offline
    }
  }

  private handleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error("[WebSocket] Max reconnect attempts reached.");
      return;
    }

    this.reconnectAttempts++;
    const timeout = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 10000);
    console.log(`[WebSocket] Reconnecting in ${timeout}ms...`);
    useCognitiveStore.getState().setSocketStatus("reconnecting");
    
    setTimeout(() => {
      this.connect();
    }, timeout);
  }

  private flushQueue() {
    if (this.queue.length > 0 && this.socket?.readyState === WebSocket.OPEN) {
      console.log(`[WebSocket] Flushing queue of ${this.queue.length} batches...`);
      // We can iterate and send all buffered payloads
      while (this.queue.length > 0) {
        const batch = this.queue.shift();
        if (batch) {
          this.socket.send(JSON.stringify(batch));
        }
      }
    }
  }
}

// Singleton instance pointing to our Django Channels endpoint
export const telemetrySocket = new TelemetrySocketManager(GATEWAY_WS_URL);
