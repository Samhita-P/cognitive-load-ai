export type EventType = "keyboard" | "mouse" | "session";

export interface TelemetryBatch {
  batch_id: string;
  session_id: string;
  timestamp_start: number;
  timestamp_end: number;
  keyboard: {
    keystrokes: number;
    backspaces: number;
    longest_pause_ms: number;
  };
  mouse: {
    distance_px: number;
    clicks: number;
    variance_x: number;
    variance_y: number;
  };
  session: {
    idle_time_ms: number;
    tab_hidden: boolean;
  };
}

export interface CognitiveStatePrediction {
  request_id?: string;
  session_id: string;
  timestamp: number;
  state: "Focused" | "Distracted" | "Fatigued" | "Overloaded" | "Normal" | "Unknown";
  focus_score: number;
  fatigue_score: number;
  confidence: number;
  top_factors: string[];
  model_version: string;
  /** Django DB row id for linking human feedback */
  gateway_prediction_id?: number;
  /** Engineered feature vector from the ML service (for training / feedback) */
  engine_features?: Record<string, number>;
  /** Present when v2_random_forest model is loaded */
  feature_importances?: Record<string, number>;
}

export interface AdaptiveAction {
  session_id: string;
  timestamp: number;
  intervention_type: "DeepWorkMode" | "BreakSuggestion" | "BurnoutWarning";
  priority: number;
  message: string;
}

export interface WebSocketMessage<T> {
  type: "telemetry" | "prediction" | "intervention" | "error";
  payload: T;
}
