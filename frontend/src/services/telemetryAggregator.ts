import { v4 as uuidv4 } from "uuid";
import { TelemetryBatchSchema } from "../schemas/telemetry";
import type { ValidatedTelemetryBatch } from "../schemas/telemetry";

export class TelemetryAggregator {
  private session_id: string;
  private batch_start_time: number;
  
  // State accumulators
  private keystrokes: number = 0;
  private backspaces: number = 0;
  private currentPauseStart: number = Date.now();
  private longest_pause_ms: number = 0;
  
  private mouse_distance_px: number = 0;
  private clicks: number = 0;
  private mousePath: { x: number; y: number }[] = [];
  
  private idleStart: number = Date.now();
  private total_idle_time_ms: number = 0;
  private tab_hidden: boolean = false;
  
  private lastMouseX: number = 0;
  private lastMouseY: number = 0;
  private user_baseline: Record<string, number> | null = null;

  constructor(session_id: string, user_baseline?: Record<string, number> | null) {
    this.session_id = session_id;
    this.batch_start_time = Date.now();
    this.user_baseline = user_baseline || null;
  }

  // Record a keydown event
  public trackKeydown(key: string) {
    this.keystrokes++;
    if (key === "Backspace") {
      this.backspaces++;
    }
    
    // Calculate pause duration
    const now = Date.now();
    const pauseDuration = now - this.currentPauseStart;
    if (pauseDuration > this.longest_pause_ms) {
      this.longest_pause_ms = pauseDuration;
    }
    this.currentPauseStart = now;
    this.resetIdle();
  }

  // Record mouse movement
  public trackMouseMove(x: number, y: number) {
    if (this.lastMouseX !== 0 && this.lastMouseY !== 0) {
      const dx = x - this.lastMouseX;
      const dy = y - this.lastMouseY;
      this.mouse_distance_px += Math.sqrt(dx * dx + dy * dy);
    }
    this.lastMouseX = x;
    this.lastMouseY = y;
    this.mousePath.push({ x, y });
    this.resetIdle();
  }

  // Record clicks
  public trackClick() {
    this.clicks++;
    this.resetIdle();
  }
  
  // Track visibility
  public trackVisibility(isHidden: boolean) {
    this.tab_hidden = isHidden;
  }

  // Calculate variances based on mouse path
  private calculateVariances() {
    if (this.mousePath.length < 2) return { variance_x: 0, variance_y: 0 };
    
    const sumX = this.mousePath.reduce((acc, point) => acc + point.x, 0);
    const sumY = this.mousePath.reduce((acc, point) => acc + point.y, 0);
    const meanX = sumX / this.mousePath.length;
    const meanY = sumY / this.mousePath.length;

    const squareDiffsX = this.mousePath.map(point => Math.pow(point.x - meanX, 2));
    const squareDiffsY = this.mousePath.map(point => Math.pow(point.y - meanY, 2));

    const avgSquareDiffX = squareDiffsX.reduce((acc, val) => acc + val, 0) / this.mousePath.length;
    const avgSquareDiffY = squareDiffsY.reduce((acc, val) => acc + val, 0) / this.mousePath.length;

    return { variance_x: avgSquareDiffX, variance_y: avgSquareDiffY };
  }

  private resetIdle() {
    this.total_idle_time_ms += (Date.now() - this.idleStart);
    this.idleStart = Date.now();
  }

  // Extract batch and reset accumulators
  public flushBatch(): ValidatedTelemetryBatch | null {
    // End idle tracking for the current batch
    const now = Date.now();
    this.total_idle_time_ms += (now - this.idleStart);
    
    const { variance_x, variance_y } = this.calculateVariances();

    const rawBatch = {
      batch_id: uuidv4(),
      session_id: this.session_id,
      timestamp_start: this.batch_start_time,
      timestamp_end: now,
      keyboard: {
        keystrokes: this.keystrokes,
        backspaces: this.backspaces,
        longest_pause_ms: this.longest_pause_ms,
      },
      mouse: {
        distance_px: parseFloat(this.mouse_distance_px.toFixed(2)),
        clicks: this.clicks,
        variance_x: parseFloat(variance_x.toFixed(2)),
        variance_y: parseFloat(variance_y.toFixed(2)),
      },
      session: {
        idle_time_ms: this.total_idle_time_ms,
        tab_hidden: this.tab_hidden,
        ...(this.user_baseline ? { user_baseline: this.user_baseline } : {})
      }
    };

    // Reset accumulators
    this.batch_start_time = now;
    this.keystrokes = 0;
    this.backspaces = 0;
    this.longest_pause_ms = 0;
    this.currentPauseStart = now;
    this.mouse_distance_px = 0;
    this.clicks = 0;
    this.mousePath = [];
    this.idleStart = now;
    this.total_idle_time_ms = 0;
    
    try {
      return TelemetryBatchSchema.parse(rawBatch);
    } catch (e) {
      console.error("[Telemetry] Validation Failed", e);
      return null;
    }
  }
}
